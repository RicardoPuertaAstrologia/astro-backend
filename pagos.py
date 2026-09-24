# ============================================================
# PAGOS — Wompi + TRM + entrega protegida de los textos
# Ricardo Puerta · Astrología
#
# Este archivo NO contiene ninguna llave. Todas las llaves se leen
# de las variables de entorno del servidor (Render → Environment).
# ============================================================

import os
import json
import time
import hmac
import hashlib
import secrets
import urllib.request
import urllib.error
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
PRECIO_USD = float(os.environ.get("PRECIO_INFORME_USD", "24.99"))

WOMPI_PUBLIC_KEY = os.environ.get("WOMPI_PUBLIC_KEY", "")
WOMPI_INTEGRITY_SECRET = os.environ.get("WOMPI_INTEGRITY_SECRET", "")
WOMPI_EVENTS_SECRET = os.environ.get("WOMPI_EVENTS_SECRET", "")
WOMPI_AMBIENTE = os.environ.get("WOMPI_AMBIENTE", "pruebas").strip().lower()

# Clave con la que el servidor firma los permisos de lectura.
# Si no está definida, se genera una al arrancar (los permisos dejan
# de servir cuando Render reinicia; por eso conviene definirla).
SECRETO_TOKENS = os.environ.get("SECRETO_TOKENS") or secrets.token_hex(32)

# URL de la API de Wompi. Si algún día Wompi cambia estas direcciones,
# se corrige con la variable WOMPI_API_URL sin tocar el código.
WOMPI_API = os.environ.get("WOMPI_API_URL") or (
    "https://production.wompi.co/v1"
    if WOMPI_AMBIENTE.startswith("prod")
    else "https://sandbox.wompi.co/v1"
)

TRM_URL = ("https://www.datos.gov.co/resource/32sa-8pi3.json"
           "?$limit=1&$order=vigenciadesde%20DESC")

HORAS_DE_PERMISO = 6  # cuánto dura el permiso de lectura tras pagar


# ------------------------------------------------------------
# TRM DEL DÍA (Superintendencia Financiera, vía Datos Abiertos)
# ------------------------------------------------------------
_trm_cache = {"valor": None, "fecha": None, "consultado": 0.0}


def _pedir_json(url, timeout=12, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def obtener_trm():
    """TRM de hoy. Se consulta una vez y se guarda por 6 horas.
    Si la consulta falla, se usa la última que haya funcionado."""
    ahora = time.time()
    if _trm_cache["valor"] and (ahora - _trm_cache["consultado"] < 6 * 3600):
        return _trm_cache["valor"], _trm_cache["fecha"]

    try:
        datos = _pedir_json(TRM_URL)
        if datos:
            valor = float(datos[0]["valor"])
            fecha = str(datos[0].get("vigenciadesde", ""))[:10]
            _trm_cache.update({"valor": valor, "fecha": fecha, "consultado": ahora})
            return valor, fecha
    except Exception as e:
        print("TRM: no se pudo consultar:", e)

    if _trm_cache["valor"]:
        return _trm_cache["valor"], _trm_cache["fecha"]
    raise HTTPException(status_code=503,
                        detail="No se pudo obtener la TRM del día. Intenta de nuevo en unos minutos.")


def precio_del_dia():
    trm, fecha_trm = obtener_trm()
    cop = round(PRECIO_USD * trm)          # pesos enteros
    return {
        "usd": PRECIO_USD,
        "cop": cop,
        "cop_en_centavos": cop * 100,       # Wompi cobra en centavos
        "trm": trm,
        "trm_fecha": fecha_trm,
        "moneda": "COP",
    }


@router.get("/precio")
def endpoint_precio():
    """Precio del informe, en dólares y en pesos con la TRM de hoy."""
    return precio_del_dia()


# ------------------------------------------------------------
# PERMISOS DE LECTURA (firmados por el servidor)
# ------------------------------------------------------------
def crear_permiso(referencia, minutos=HORAS_DE_PERMISO * 60):
    vence = int(time.time()) + minutos * 60
    cuerpo = f"{referencia}.{vence}"
    firma = hmac.new(SECRETO_TOKENS.encode(), cuerpo.encode(), hashlib.sha256).hexdigest()
    return f"{cuerpo}.{firma}"


def permiso_valido(permiso):
    try:
        referencia, vence, firma = str(permiso).split(".")
        cuerpo = f"{referencia}.{vence}"
        esperada = hmac.new(SECRETO_TOKENS.encode(), cuerpo.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, esperada):
            return False
        return int(vence) > int(time.time())
    except Exception:
        return False


# ------------------------------------------------------------
# CREAR EL COBRO
# ------------------------------------------------------------
@router.post("/cobro/crear")
def crear_cobro():
    """Devuelve todo lo que el navegador necesita para abrir el checkout
    de Wompi: referencia única, monto en centavos y firma de integridad.
    La firma se hace acá, en el servidor, porque usa un secreto."""
    if not WOMPI_PUBLIC_KEY or not WOMPI_INTEGRITY_SECRET:
        raise HTTPException(status_code=503,
                            detail="El cobro no está configurado en el servidor.")

    p = precio_del_dia()
    referencia = "RP-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + secrets.token_hex(6)
    monto = p["cop_en_centavos"]
    moneda = "COP"

    cadena = f"{referencia}{monto}{moneda}{WOMPI_INTEGRITY_SECRET}"
    firma = hashlib.sha256(cadena.encode("utf-8")).hexdigest()

    return {
        "referencia": referencia,
        "monto_en_centavos": monto,
        "moneda": moneda,
        "firma_integridad": firma,
        "llave_publica": WOMPI_PUBLIC_KEY,
        "ambiente": WOMPI_AMBIENTE,
        "precio": p,
    }


# ------------------------------------------------------------
# VERIFICAR EL PAGO
# ------------------------------------------------------------
def consultar_transaccion(id_transaccion):
    url = f"{WOMPI_API}/transactions/{id_transaccion}"
    try:
        respuesta = _pedir_json(url, headers={"Accept": "application/json"})
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=404, detail=f"Wompi no reconoce esa transacción ({e.code}).")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"No se pudo consultar a Wompi: {e}")
    return respuesta.get("data", {})


@router.get("/cobro/verificar")
def verificar_cobro(id: str, referencia: str = ""):
    """El navegador vuelve de Wompi con el id de la transacción.
    Acá se le pregunta a Wompi si ese pago existe y está aprobado."""
    datos = consultar_transaccion(id)
    estado = datos.get("status")
    ref = datos.get("reference", "")
    monto = datos.get("amount_in_cents", 0)

    if referencia and ref and referencia != ref:
        raise HTTPException(status_code=400, detail="La referencia no corresponde a ese pago.")

    if estado != "APPROVED":
        return {"aprobado": False, "estado": estado, "referencia": ref}

    # El monto debe ser al menos el precio del día menos un margen por
    # si la TRM cambió entre que se creó el cobro y se pagó.
    esperado = precio_del_dia()["cop_en_centavos"]
    if monto < esperado * 0.90:
        raise HTTPException(status_code=400, detail="El monto pagado no corresponde al precio.")

    return {
        "aprobado": True,
        "estado": estado,
        "referencia": ref,
        "permiso": crear_permiso(ref),
        "horas": HORAS_DE_PERMISO,
    }


# ------------------------------------------------------------
# AVISO DE WOMPI (webhook)
# ------------------------------------------------------------
@router.post("/wompi/evento")
async def evento_wompi(request: Request):
    """Wompi avisa acá cada vez que una transacción cambia de estado.
    Se valida la firma para asegurarse de que el aviso es de Wompi."""
    cuerpo = await request.json()

    firma = (cuerpo.get("signature") or {})
    propiedades = firma.get("properties") or []
    checksum_recibido = firma.get("checksum") or request.headers.get("X-Event-Checksum", "")
    timestamp = cuerpo.get("timestamp", "")
    datos = cuerpo.get("data", {})

    cadena = ""
    for prop in propiedades:
        valor = datos
        for parte in str(prop).split("."):
            valor = (valor or {}).get(parte) if isinstance(valor, dict) else None
        cadena += "" if valor is None else str(valor)
    cadena += str(timestamp) + WOMPI_EVENTS_SECRET

    calculado = hashlib.sha256(cadena.encode("utf-8")).hexdigest()
    if not WOMPI_EVENTS_SECRET or not hmac.compare_digest(calculado.lower(),
                                                          str(checksum_recibido).lower()):
        raise HTTPException(status_code=401, detail="Firma del evento inválida.")

    transaccion = (datos.get("transaction") or {})
    print("Wompi evento:", cuerpo.get("event"),
          transaccion.get("reference"), transaccion.get("status"))

    # Aquí, en la Fase B, se dispara el envío del PDF por correo.
    return {"recibido": True}


# ------------------------------------------------------------
# PROTECCIÓN DE LOS TEXTOS
# ------------------------------------------------------------
# Mientras PROTEGER_TEXTOS no valga "si", el backend entrega los textos
# como siempre. Así nada se rompe mientras construimos. Cuando la
# tienda esté lista, se pone "si" en Render y los textos completos solo
# salen con un permiso de pago válido.
PROTEGER_TEXTOS = os.environ.get("PROTEGER_TEXTOS", "no").strip().lower() == "si"


def exigir_permiso(permiso):
    """Lo llama el backend antes de entregar los textos completos."""
    if not PROTEGER_TEXTOS:
        return True
    if permiso_valido(permiso):
        return True
    raise HTTPException(status_code=402,
                        detail="Este contenido hace parte del informe completo.")


# ------------------------------------------------------------
# ESTADO (para revisar que todo quedó bien configurado)
# ------------------------------------------------------------
@router.get("/cobro/estado")
def estado_cobro():
    """No muestra ninguna llave: solo dice si están puestas."""
    try:
        p = precio_del_dia()
        trm_ok = True
    except Exception:
        p, trm_ok = None, False
    return {
        "ambiente": WOMPI_AMBIENTE,
        "llave_publica_configurada": bool(WOMPI_PUBLIC_KEY),
        "secreto_integridad_configurado": bool(WOMPI_INTEGRITY_SECRET),
        "secreto_eventos_configurado": bool(WOMPI_EVENTS_SECRET),
        "secreto_tokens_configurado": bool(os.environ.get("SECRETO_TOKENS")),
        "textos_protegidos": PROTEGER_TEXTOS,
        "trm_disponible": trm_ok,
        "precio": p,
    }

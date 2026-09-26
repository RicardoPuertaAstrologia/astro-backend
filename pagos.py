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

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional

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

# Códigos de cortesía: para que Ricardo entre sin pagar y para regalar
# accesos. Se escriben en Render, separados por comas:
#     CODIGOS_CORTESIA = MARIA-9XQ2, RICARDO-CASA, PRENSA-4KD7
# Borrar un código de esa lista lo desactiva al instante.
def _leer_codigos():
    crudo = os.environ.get("CODIGOS_CORTESIA", "")
    return {c.strip().upper() for c in crudo.split(",") if c.strip()}


CODIGOS_CORTESIA = _leer_codigos()


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


def textos_protegidos():
    """True cuando la tienda está cerrada con llave."""
    return PROTEGER_TEXTOS


def hay_permiso(permiso):
    """True si viene un permiso de pago válido."""
    return bool(permiso) and permiso_valido(permiso)


def exigir_permiso(permiso):
    """Lo llama el backend antes de entregar los textos completos."""
    if not PROTEGER_TEXTOS:
        return True
    if hay_permiso(permiso):
        return True
    raise HTTPException(status_code=402,
                        detail="Este contenido hace parte del informe completo.")


# ------------------------------------------------------------
# ENTREGA DEL INFORME: PDF + CORREO
# ------------------------------------------------------------
_edades_cache = None


def _cargar_edades():
    global _edades_cache
    if _edades_cache is None:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "edades.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                _edades_cache = json.load(f)
        except Exception as e:
            print("Edades: no se pudo cargar", ruta, e)
            _edades_cache = []
    return _edades_cache


def _edad_de(nacimiento):
    hoy = datetime.now()
    edad = hoy.year - nacimiento["year"]
    if (hoy.month, hoy.day) < (nacimiento["month"], nacimiento["day"]):
        edad -= 1
    return edad


def _edad_zodiacal(nacimiento, lang):
    edades = _cargar_edades()
    if not edades:
        return None
    edad = _edad_de(nacimiento)
    elegida = None
    for e in edades:
        if e["min"] <= edad <= e["max"]:
            elegida = e
            break
    if elegida is None:
        siguientes = [e for e in edades if e["min"] > edad]
        elegida = siguientes[0] if siguientes else edades[-1]
    d = elegida.get(lang) or elegida.get("es")
    rango = (str(elegida["min"]) if elegida["min"] == elegida["max"]
             else f'{elegida["min"]} a {elegida["max"]}')
    if lang == "en" and elegida["min"] != elegida["max"]:
        rango = f'{elegida["min"]} to {elegida["max"]}'
    return {
        "rango": rango + (" años" if lang != "en" else " years"),
        "titulo": d.get("titulo", ""),
        "pasa": d.get("pasa", ""),
        "spoiler": d.get("spoiler", ""),
        "retos": d.get("retos", []),
        "trabajar": d.get("trabajar", ""),
        "edad_actual": edad,
    }


class DatosEntrega(BaseModel):
    id: str
    referencia: str = ""
    correo: str
    lang: str = "es"
    nacimiento: dict
    imagen: Optional[str] = None
    secciones: Optional[list] = None


@router.post("/cobro/entregar")
def entregar_informe(datos: DatosEntrega):
    """Verifica el pago, arma el PDF y lo manda al correo de la persona."""
    transaccion = consultar_transaccion(datos.id)
    if transaccion.get("status") != "APPROVED":
        raise HTTPException(status_code=402, detail="Ese pago no está aprobado.")
    if datos.referencia and transaccion.get("reference") and \
            datos.referencia != transaccion.get("reference"):
        raise HTTPException(status_code=400, detail="La referencia no corresponde a ese pago.")

    lang = "en" if str(datos.lang).lower().startswith("en") else "es"

    # Se calcula todo de nuevo acá, en el servidor.
    import correo as correo_mod
    pdf = _armar_pdf(datos.nacimiento, lang, datos.imagen, datos.secciones)

    enviado, motivo = correo_mod.enviar_informe(
        datos.correo, pdf, (datos.nacimiento.get("name") or ""), lang)

    return {
        "ok": True,
        "correo_enviado": enviado,
        "motivo": "" if enviado else motivo,
        "permiso": crear_permiso(transaccion.get("reference") or datos.referencia),
        "horas": HORAS_DE_PERMISO,
        "tamano_pdf": len(pdf),
    }


class DatosPDF(BaseModel):
    permiso: str
    lang: str = "es"
    nacimiento: dict
    imagen: Optional[str] = None
    secciones: Optional[list] = None


# ------------------------------------------------------------
# EL INFORME RECIÉN ARMADO SE GUARDA UN RATO
# ------------------------------------------------------------
# Al volver de Wompi pasan dos cosas seguidas: el servidor arma el PDF
# para mandarlo por correo, y al ratito la persona le da a "descargar" y
# el servidor lo arma OTRA VEZ, idéntico. En el plan pequeño de Render,
# que da una décima de procesador, esos dos trabajos se pisan y los dos
# van lentos.
#
# Guardando el último rato lo que ya se armó, el segundo pedido es
# instantáneo. Se guardan pocos y por poco tiempo: cada informe pesa algo
# más de medio mega y el servidor tiene 512 MB.
_INFORMES = {}          # huella -> (momento, bytes)
_INFORMES_VIDA = 900    # 15 minutos
_INFORMES_CUANTOS = 4


def _huella_informe(nacimiento_dict, lang, imagen, secciones):
    crudo = json.dumps([nacimiento_dict, lang, secciones], sort_keys=True, default=str)
    if imagen:
        crudo += hashlib.sha256(imagen.encode("utf-8", "ignore")).hexdigest()
    return hashlib.sha256(crudo.encode("utf-8", "ignore")).hexdigest()


def _informe_guardado(huella):
    ahora = time.time()
    for k in [k for k, (t, _) in _INFORMES.items() if ahora - t > _INFORMES_VIDA]:
        _INFORMES.pop(k, None)
    guardado = _INFORMES.get(huella)
    return guardado[1] if guardado else None


def _guardar_informe(huella, datos):
    if len(_INFORMES) >= _INFORMES_CUANTOS:
        mas_viejo = min(_INFORMES, key=lambda k: _INFORMES[k][0])
        _INFORMES.pop(mas_viejo, None)
    _INFORMES[huella] = (time.time(), datos)


def _armar_pdf(nacimiento_dict, lang, imagen, secciones):
    """Arma el PDF completo. Lo usan el correo y la descarga, para que
    la persona reciba exactamente el mismo documento por los dos lados.
    Si ya se armó ese mismo informe hace poco, se devuelve tal cual."""
    huella = _huella_informe(nacimiento_dict, lang, imagen, secciones)
    ya_esta = _informe_guardado(huella)
    if ya_esta is not None:
        print("Informe: se reusa el que se armó hace un momento")
        return ya_esta
    from backend import BirthData, calculate_chart, obtener_interpretaciones_carta
    import informe as informe_mod

    try:
        nacimiento = BirthData(**nacimiento_dict)
        carta = calculate_chart(nacimiento, lang)
        interpretaciones = obtener_interpretaciones_carta(carta["natal_chart"], lang)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular la carta: {e}")

    edad = _edad_zodiacal(nacimiento_dict, lang)

    # El calendario de doce meses que devuelve el servidor es solo el del
    # planeta señalado en pantalla. Para el informe se calculan los siete
    # planetas lentos, uno por uno, y van todos.
    calendario = []
    try:
        lentos = list((carta.get("transits") or {}).get("positions") or {})
        for planeta in lentos:
            datos = dict(nacimiento_dict)
            datos["transit_planet"] = planeta
            otra = calculate_chart(BirthData(**datos), lang)
            eventos = ((otra.get("calendar_12mo") or {}).get("events")) or []
            if eventos:
                calendario.append({"planeta": planeta, "eventos": eventos})
    except Exception as e:
        print("Informe: no se pudo armar el calendario completo:", repr(e))

    try:
        pdf = informe_mod.construir_pdf(carta, interpretaciones, edad,
                                        secciones or [], imagen, lang,
                                        calendario=calendario)
        _guardar_informe(huella, pdf)
        return pdf
    except Exception as e:
        print("Informe: falló el PDF:", repr(e))
        raise HTTPException(status_code=500, detail="No se pudo armar el informe en PDF.")


@router.post("/cobro/pdf")
def descargar_pdf(datos: DatosPDF):
    """Devuelve el MISMO informe que se manda por correo, para que el botón
    de descarga no dependa de lo que el navegador tenga abierto en pantalla."""
    if not permiso_valido(datos.permiso):
        raise HTTPException(status_code=402, detail="Este informe hace parte de la versión de pago.")

    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    pdf = _armar_pdf(datos.nacimiento, lang, datos.imagen, datos.secciones)
    nombre = (datos.nacimiento.get("name") or "informe").strip()
    seguro = "".join(c for c in nombre if c.isalnum() or c in " -_").strip() or "informe"
    base = "Natal chart - " if lang == "en" else "Carta natal - "
    return Response(
        content=bytes(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{base}{seguro}.pdf"'},
    )


class DatosCortesia(BaseModel):
    codigo: str


@router.post("/cortesia")
def cortesia(datos: DatosCortesia):
    """Un código de cortesía abre lo mismo que abre un pago. No hay
    registro de quién lo usó: el control es que los códigos se cambian
    o se borran en Render cuando ya cumplieron su encargo."""
    codigo = (datos.codigo or "").strip().upper()
    if not codigo or codigo not in _leer_codigos():
        raise HTTPException(status_code=404, detail="Ese código no sirve.")
    print(f"Cortesía: se usó el código {codigo}")
    return {
        "ok": True,
        "permiso": crear_permiso(f"cortesia-{codigo}"),
        "horas": HORAS_DE_PERMISO,
    }


class DatosEnvio(BaseModel):
    permiso: str
    correo: str
    lang: str = "es"
    nacimiento: dict
    imagen: Optional[str] = None
    secciones: Optional[list] = None


@router.post("/cobro/enviar")
def enviar_a_un_correo(datos: DatosEnvio):
    """Manda el informe completo al correo que se indique. Sirve para
    regalar una carta ya hecha: Ricardo la calcula y la envía."""
    if not permiso_valido(datos.permiso):
        raise HTTPException(status_code=402, detail="Este informe hace parte de la versión de pago.")
    correo_limpio = (datos.correo or "").strip()
    if "@" not in correo_limpio or "." not in correo_limpio.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Ese correo no parece válido.")

    import correo as correo_mod
    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    pdf = _armar_pdf(datos.nacimiento, lang, datos.imagen, datos.secciones)
    enviado, motivo = correo_mod.enviar_informe(
        correo_limpio, pdf, (datos.nacimiento.get("name") or ""), lang)
    return {"ok": True, "enviado": enviado, "motivo": "" if enviado else motivo}


class DatosGratis(BaseModel):
    lang: str = "es"
    nacimiento: dict
    imagen: Optional[str] = None


@router.post("/informe/gratis")
def informe_gratis(datos: DatosGratis):
    """El PDF de cortesía: la portada, el gráfico, las tablas y la edad
    zodiacal. Lo arma el servidor, no el navegador, por dos razones: para
    que se vea con la portada y la tipografía de la marca, y sobre todo
    para que no pueda colarse nada de lo que se paga. Lo que no se le
    pasa a esta función, no existe en ese PDF."""
    from backend import BirthData, calculate_chart
    import informe as informe_mod

    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    try:
        carta = calculate_chart(BirthData(**datos.nacimiento), lang)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular la carta: {e}")

    edad = _edad_zodiacal(datos.nacimiento, lang)
    try:
        pdf = informe_mod.construir_pdf_gratis(carta, edad, datos.imagen, lang)
    except Exception as e:
        print("Informe gratis: falló el PDF:", repr(e))
        raise HTTPException(status_code=500, detail="No se pudo armar el PDF.")

    nombre = (datos.nacimiento.get("name") or "carta").strip()
    seguro = "".join(c for c in nombre if c.isalnum() or c in " -_").strip() or "carta"
    base = "Natal chart - " if lang == "en" else "Carta natal - "
    return Response(
        content=bytes(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{base}{seguro}.pdf"'},
    )


@router.get("/correo/probar")
def probar_correo(a: str = ""):
    """Envía un correo corto de prueba. Se usa una vez, para comprobar la
    configuración: /correo/probar?a=tucorreo@dominio.com"""
    import correo as correo_mod
    if not a:
        return {"configurado": correo_mod.correo_configurado(),
                "servidor": bool(correo_mod.SERVIDOR),
                "usuario": bool(correo_mod.USUARIO),
                "clave": bool(correo_mod.CLAVE),
                "puerto": correo_mod.PUERTO}
    enviado, motivo = correo_mod.enviar_prueba(a)
    return {"enviado": enviado, "motivo": motivo}


# ------------------------------------------------------------
# ESTADO (para revisar que todo quedó bien configurado)
# ------------------------------------------------------------
def _correo_listo():
    try:
        import correo as correo_mod
        return correo_mod.correo_configurado()
    except Exception:
        return False


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
        "codigos_de_cortesia": len(_leer_codigos()),
        "correo_configurado": _correo_listo(),
        "trm_disponible": trm_ok,
        "precio": p,
    }

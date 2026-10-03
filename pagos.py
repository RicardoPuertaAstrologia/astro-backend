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
PRECIO_MAPA_USD = float(os.environ.get("PRECIO_MAPA_USD", "20.99"))

# Los dos productos que se venden. La sigla es la que abre la
# referencia del pago, y es la que después dice qué compró la persona:
# RP-20261002-a1b2c3 es el informe, RPM-20261002-a1b2c3 es el mapa.
PRODUCTOS = {
    "informe": {"usd": PRECIO_USD, "sigla": "RP"},
    "mapa": {"usd": PRECIO_MAPA_USD, "sigla": "RPM"},
}


def producto_de(referencia):
    """De la referencia se deduce qué se compró o qué se regaló. Como la
    referencia va dentro de la firma del permiso, nadie puede cambiarla."""
    r = str(referencia or "").upper()
    if r.startswith("CORTESIA-MAPA-"):
        return "mapa"
    if r.startswith("CORTESIA-INFORME-"):
        return "informe"
    if r.startswith("CORTESIA-"):
        return "todo"
    return "mapa" if r.startswith("RPM-") else "informe"
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


def precio_del_dia(producto="informe"):
    p = PRODUCTOS.get(producto) or PRODUCTOS["informe"]
    trm, fecha_trm = obtener_trm()
    cop = round(p["usd"] * trm)            # pesos enteros
    return {
        "producto": producto,
        "usd": p["usd"],
        "cop": cop,
        "cop_en_centavos": cop * 100,       # Wompi cobra en centavos
        "trm": trm,
        "trm_fecha": fecha_trm,
        "moneda": "COP",
    }


@router.get("/precio")
def endpoint_precio(producto: str = "informe"):
    """Precio del producto, en dólares y en pesos con la TRM de hoy.
    Se pide así:  /precio          -> el informe
                  /precio?producto=mapa  -> el mapa"""
    return precio_del_dia(producto)


# ------------------------------------------------------------
# PERMISOS DE LECTURA (firmados por el servidor)
# ------------------------------------------------------------
def crear_permiso(referencia, minutos=HORAS_DE_PERMISO * 60):
    vence = int(time.time()) + minutos * 60
    cuerpo = f"{referencia}.{vence}"
    firma = hmac.new(SECRETO_TOKENS.encode(), cuerpo.encode(), hashlib.sha256).hexdigest()
    return f"{cuerpo}.{firma}"


def permiso_valido(permiso, producto="informe"):
    """Además de comprobar la firma y que no esté vencido, mira que el
    permiso sea del producto que se está pidiendo. El producto se saca
    de la referencia, que va dentro de la firma: no se puede falsear."""
    try:
        referencia, vence, firma = str(permiso).split(".")
        cuerpo = f"{referencia}.{vence}"
        esperada = hmac.new(SECRETO_TOKENS.encode(), cuerpo.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, esperada):
            return False
        if int(vence) <= int(time.time()):
            return False
        suyo = producto_de(referencia)
        return suyo == "todo" or suyo == producto
    except Exception:
        return False


# ------------------------------------------------------------
# CREAR EL COBRO
# ------------------------------------------------------------
@router.post("/cobro/crear")
def crear_cobro(producto: str = "informe"):
    """Devuelve todo lo que el navegador necesita para abrir el checkout
    de Wompi: referencia única, monto en centavos y firma de integridad.
    La firma se hace acá, en el servidor, porque usa un secreto."""
    if not WOMPI_PUBLIC_KEY or not WOMPI_INTEGRITY_SECRET:
        raise HTTPException(status_code=503,
                            detail="El cobro no está configurado en el servidor.")

    p = precio_del_dia(producto)
    sigla = (PRODUCTOS.get(producto) or PRODUCTOS["informe"])["sigla"]
    referencia = sigla + "-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + secrets.token_hex(6)
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
        "producto": producto,
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
    esperado = precio_del_dia(producto_de(ref))["cop_en_centavos"]
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


def hay_permiso(permiso, producto="informe"):
    """True si viene un permiso de pago válido para ese producto."""
    return bool(permiso) and permiso_valido(permiso, producto)


def exigir_permiso(permiso, producto="informe"):
    """Lo llama el backend antes de entregar los textos completos."""
    if not PROTEGER_TEXTOS:
        return True
    if hay_permiso(permiso, producto):
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
        headers=cabecera_de_archivo(f"{base}{seguro}.pdf"),
    )


class DatosCortesia(BaseModel):
    codigo: str


@router.post("/cortesia")
def cortesia(datos: DatosCortesia):
    """Un código de cortesía abre lo mismo que abre un pago. No hay
    registro de quién lo usó: el control es que los códigos se cambian
    o se borran en Render cuando ya cumplieron su encargo."""
    codigo = (datos.codigo or "").strip().upper()
    producto = producto_del_codigo(codigo)
    if not producto:
        raise HTTPException(status_code=404, detail="Ese código no sirve.")
    print(f"Cortesía: se usó el código {codigo} ({producto})")
    return {
        "ok": True,
        "permiso": crear_permiso(referencia_de_cortesia(codigo, producto)),
        "horas": HORAS_DE_PERMISO,
        "producto": producto,
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
        headers=cabecera_de_archivo(f"{base}{seguro}.pdf"),
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


# ══════════════════════════════════════════════════════════════════
#  EL ASTROMAPA
# ══════════════════════════════════════════════════════════════════
#
# El segundo producto. Funciona igual que el informe de la carta natal:
# se verifica el pago contra Wompi, el servidor arma el PDF, lo manda al
# correo y entrega un permiso de lectura de seis horas.
#
# Dos cosas que conviene tener claras:
#
#  1. El día juliano se pide a get_julian_day_ut(), que es LA MISMA
#     función que usa la carta natal. Así el mapa y el informe hablan
#     exactamente del mismo instante, con la misma zona horaria y el
#     mismo manejo del horario de verano. Si el mapa calculara la hora
#     por su cuenta, los dos informes podrían desfasarse.
#
#  2. El permiso que se entrega va firmado sobre una referencia que
#     empieza por RPM-, y producto_de() deduce de ahí que es del mapa.
#     Con ese permiso NO se pueden abrir los textos del informe de la
#     carta natal, que vale más.

class DatosMapaEntrega(BaseModel):
    id: str
    referencia: str = ""
    correo: str
    lang: str = "es"
    nacimiento: dict


class DatosMapaPDF(BaseModel):
    permiso: str
    lang: str = "es"
    nacimiento: dict


_MAPAS = {}             # huella -> (momento, bytes)
_MAPAS_VIDA = 900       # 15 minutos, como el informe
_MAPAS_CUANTOS = 4


def _armar_mapa(nacimiento_dict, lang):
    """Arma el PDF del astromapa. Lo usan el correo y la descarga, para que
    la persona reciba exactamente el mismo documento por los dos lados.
    Si ya se armó ese mismo mapa hace poco, se devuelve tal cual."""
    crudo = json.dumps(["mapa", nacimiento_dict, lang], sort_keys=True, default=str)
    huella = hashlib.sha256(crudo.encode("utf-8", "ignore")).hexdigest()

    ahora = time.time()
    for k in [k for k, (t, _) in _MAPAS.items() if ahora - t > _MAPAS_VIDA]:
        _MAPAS.pop(k, None)
    guardado = _MAPAS.get(huella)
    if guardado:
        print("Astromapa: se reusa el que se armó hace un momento")
        return guardado[1]

    from backend import BirthData, get_julian_day_ut
    import mapa_informe

    try:
        nacimiento = BirthData(**nacimiento_dict)
        jd, zona = get_julian_day_ut(nacimiento)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"No se pudo leer la fecha de nacimiento: {e}")

    try:
        pdf = mapa_informe.construir_pdf(nacimiento_dict, jd, zona, lang)
    except Exception as e:
        print("Astromapa: falló el PDF:", repr(e))
        raise HTTPException(status_code=500, detail="No se pudo armar el astromapa en PDF.")

    if len(_MAPAS) >= _MAPAS_CUANTOS:
        _MAPAS.pop(min(_MAPAS, key=lambda k: _MAPAS[k][0]), None)
    _MAPAS[huella] = (time.time(), pdf)
    return pdf


def cabecera_de_archivo(nombre_archivo):
    """La cabecera que le dice al navegador cómo llamar al archivo.

    Las cabeceras HTTP sólo admiten ASCII. Un nombre con tilde —«María
    José Muñoz»— viaja en latin-1 y al navegador le llega mal escrito; y
    uno con letras que ni siquiera caben en latin-1 —turco, polaco,
    griego, chino— hace que la descarga falle con un error 500.

    Por eso se mandan las dos formas, que es lo que dice la norma
    (RFC 6266): `filename` sin tildes, que entiende cualquier programa, y
    `filename*` en UTF-8, que es el que usan todos los navegadores de hoy
    y el que sale bien escrito.
    """
    import unicodedata
    import urllib.parse
    plano = unicodedata.normalize("NFKD", nombre_archivo)
    plano = plano.encode("ascii", "ignore").decode("ascii")
    plano = "".join(c for c in plano if c.isalnum() or c in " -_.").strip()
    # Si el nombre de la persona se fue entero —por ejemplo un nombre en
    # chino, que no tiene equivalente sin tildes— queda «Astromapa - .pdf».
    # Se le quita ese guion suelto. El nombre de verdad va igual, bien
    # escrito, en el filename* de más abajo.
    plano = plano.replace(" - .pdf", ".pdf").strip(" -")
    if not plano or plano.lower().startswith(".pdf"):
        plano = "informe.pdf"
    citado = urllib.parse.quote(nombre_archivo, safe="")
    return {"Content-Disposition":
            "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (plano, citado)}


def _nombre_archivo_mapa(nombre, lang):
    limpio = "".join(c for c in (nombre or "") if c.isalnum() or c in " -_").strip()
    base = "Astromap - " if lang == "en" else "Astromapa - "
    return base + (limpio or ("map" if lang == "en" else "mapa")) + ".pdf"


@router.post("/mapa/entregar")
def entregar_mapa(datos: DatosMapaEntrega):
    """Verifica el pago del mapa, arma el PDF y lo manda al correo."""
    transaccion = consultar_transaccion(datos.id)
    if transaccion.get("status") != "APPROVED":
        raise HTTPException(status_code=402, detail="Ese pago no está aprobado.")
    if datos.referencia and transaccion.get("reference") and \
            datos.referencia != transaccion.get("reference"):
        raise HTTPException(status_code=400, detail="La referencia no corresponde a ese pago.")

    ref = transaccion.get("reference") or datos.referencia
    if producto_de(ref) == "informe":
        raise HTTPException(status_code=400,
                            detail="Ese pago es del informe de la carta natal, no del astromapa.")

    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    import correo as correo_mod
    pdf = _armar_mapa(datos.nacimiento, lang)

    enviado, motivo = correo_mod.enviar_mapa(
        datos.correo, pdf, (datos.nacimiento.get("name") or ""), lang)

    return {
        "ok": True,
        "correo_enviado": enviado,
        "motivo": "" if enviado else motivo,
        "permiso": crear_permiso(ref),
        "horas": HORAS_DE_PERMISO,
        "tamano_pdf": len(pdf),
    }


@router.post("/mapa/pdf")
def descargar_mapa(datos: DatosMapaPDF):
    """Devuelve el MISMO astromapa que se manda por correo."""
    if not permiso_valido(datos.permiso, "mapa"):
        raise HTTPException(status_code=402, detail="El astromapa hace parte de la versión de pago.")

    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    pdf = _armar_mapa(datos.nacimiento, lang)
    archivo = _nombre_archivo_mapa(datos.nacimiento.get("name"), lang)
    return Response(
        content=bytes(pdf),
        media_type="application/pdf",
        headers=cabecera_de_archivo(archivo),
    )


@router.get("/mapa/estado")
def estado_mapa():
    """Dice si el servidor sabe armar el astromapa. Sirve para comprobar
    que los archivos del mapa subieron bien, sin tener que pagar nada."""
    detalle = {}
    try:
        import mapa_informe, mapa_datos, mapa_dibujo, mapa_textos
        detalle["modulos"] = True
        detalle["ciudades"] = len(mapa_datos._ciudades())
        detalle["contornos"] = len(mapa_dibujo.mundo())
        detalle["textos_es"] = len(mapa_textos.largos("es"))
        detalle["textos_en"] = len(mapa_textos.largos("en"))
        detalle["listo"] = (detalle["ciudades"] == 73 and
                            detalle["textos_es"] == 66 and
                            detalle["textos_en"] == 66 and
                            detalle["contornos"] > 200)
    except Exception as e:
        detalle["modulos"] = False
        detalle["listo"] = False
        detalle["error"] = repr(e)
    # El precio se consulta aparte y sin que pueda tumbar la comprobación:
    # si datos.gov.co no contesta, lo que interesa saber —si los archivos
    # del mapa subieron bien— se sigue pudiendo ver.
    try:
        detalle["precio"] = precio_del_dia("mapa")
    except Exception as e:
        detalle["precio"] = {"error": repr(e)}
    return detalle


# ══════════════════════════════════════════════════════════════════
#  CÓDIGOS DE CORTESÍA POR PRODUCTO, Y REGALAR UN ASTROMAPA
# ══════════════════════════════════════════════════════════════════
#
# Antes había una sola clase de código y abría todo. Ahora hay tres, y
# el producto va DENTRO del código, no en la casilla donde se escriba:
#
#   CODIGOS_CORTESIA           abren las dos cosas  (los que ya tienes)
#   CODIGOS_CORTESIA_MAPA      abren sólo el astromapa
#   CODIGOS_CORTESIA_INFORME   abren sólo el informe de la carta natal
#
# Que el producto vaya en el código y no en la casilla tiene una razón:
# si alguien escribe un código del astromapa en la casilla del informe,
# lo justo es abrirle el astromapa y decírselo, no responderle «ese
# código no sirve» y dejarlo perdido sin saber por qué.
#
# Tus códigos de siempre siguen funcionando igual, sin tocar nada.


def _codigos_de(variable):
    crudo = os.environ.get(variable, "")
    return {c.strip().upper() for c in crudo.split(",") if c.strip()}


def producto_del_codigo(codigo):
    """Qué abre un código: 'todo', 'mapa' o 'informe'. None si no existe."""
    c = (codigo or "").strip().upper()
    if not c:
        return None
    if c in _codigos_de("CODIGOS_CORTESIA"):
        return "todo"
    if c in _codigos_de("CODIGOS_CORTESIA_MAPA"):
        return "mapa"
    if c in _codigos_de("CODIGOS_CORTESIA_INFORME"):
        return "informe"
    return None


def referencia_de_cortesia(codigo, producto):
    """La referencia que lleva el permiso. De acá saca producto_de() qué
    abre, y como la referencia va dentro de la firma, no se puede falsear."""
    if producto == "mapa":
        return "CORTESIA-MAPA-" + codigo
    if producto == "informe":
        return "CORTESIA-INFORME-" + codigo
    return "CORTESIA-" + codigo


class DatosEnvioMapa(BaseModel):
    permiso: str
    correo: str
    lang: str = "es"
    nacimiento: dict


@router.post("/mapa/enviar")
def enviar_mapa_a_un_correo(datos: DatosEnvioMapa):
    """Manda el astromapa al correo que se indique. Es el gemelo de
    /cobro/enviar: sirve para regalar un astromapa ya hecho."""
    if not permiso_valido(datos.permiso, "mapa"):
        raise HTTPException(status_code=402,
                            detail="El astromapa hace parte de la versión de pago.")
    correo_limpio = (datos.correo or "").strip()
    if "@" not in correo_limpio or "." not in correo_limpio.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Ese correo no parece válido.")

    import correo as correo_mod
    lang = "en" if str(datos.lang).lower().startswith("en") else "es"
    pdf = _armar_mapa(datos.nacimiento, lang)
    enviado, motivo = correo_mod.enviar_mapa(
        correo_limpio, pdf, (datos.nacimiento.get("name") or ""), lang)
    return {"ok": True, "enviado": enviado, "motivo": "" if enviado else motivo}

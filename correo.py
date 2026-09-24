# ============================================================
# CORREO — envío del informe en PDF
# Ricardo Puerta · Astrología
#
# Los datos del correo se leen de las variables de entorno:
#   CORREO_SERVIDOR   servidor de salida (SMTP) de tu proveedor
#   CORREO_PUERTO     465 (SSL) o 587 (STARTTLS)
#   CORREO_USUARIO    ricardopuerta@ricardopuerta.com
#   CORREO_CLAVE      la contraseña de ese buzón (o clave de aplicación)
#   CORREO_REMITENTE  opcional: "Ricardo Puerta <ricardopuerta@ricardopuerta.com>"
# ============================================================

import os
import ssl
import json
import base64
import smtplib
import urllib.request
import urllib.error
from email.message import EmailMessage

SERVIDOR = os.environ.get("CORREO_SERVIDOR", "")
PUERTO = int(os.environ.get("CORREO_PUERTO", "465") or 465)
USUARIO = os.environ.get("CORREO_USUARIO", "")
CLAVE = os.environ.get("CORREO_CLAVE", "")
REMITENTE = os.environ.get("CORREO_REMITENTE") or (
    f"Ricardo Puerta Isaza <{USUARIO}>" if USUARIO else "")
COPIA_OCULTA = os.environ.get("CORREO_COPIA", "")   # opcional: copia para ti

# Camino alternativo: la API de Brevo por web (puerto 443).
# Se usa cuando el servidor no deja salir por los puertos de correo,
# como pasa en el plan gratuito de Render.
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def correo_configurado():
    return bool(BREVO_API_KEY) or bool(SERVIDOR and USUARIO and CLAVE)


def _remitente_partido():
    """De 'Ricardo Puerta Isaza <correo@dominio>' saca el nombre y el correo."""
    r = (REMITENTE or USUARIO or "").strip()
    if "<" in r and ">" in r:
        nombre = r.split("<")[0].strip().strip('"')
        correo = r.split("<")[1].split(">")[0].strip()
        return nombre or "Ricardo Puerta Isaza", correo
    return "Ricardo Puerta Isaza", r


def _enviar_por_api(destino, asunto, texto, pdf_bytes=None, archivo="informe.pdf"):
    """Envía usando la API de Brevo por HTTPS. No usa puertos de correo."""
    nombre, correo = _remitente_partido()
    cuerpo = {
        "sender": {"name": nombre, "email": correo},
        "to": [{"email": destino}],
        "subject": asunto,
        "textContent": texto,
    }
    if COPIA_OCULTA:
        cuerpo["bcc"] = [{"email": COPIA_OCULTA}]
    if pdf_bytes:
        cuerpo["attachment"] = [{
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
            "name": archivo,
        }]
    datos = json.dumps(cuerpo).encode("utf-8")
    peticion = urllib.request.Request(BREVO_URL, data=datos, headers={
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(peticion, timeout=45) as r:
            r.read()
        return True, ""
    except urllib.error.HTTPError as e:
        detalle = ""
        try:
            detalle = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        return False, f"Brevo respondió {e.code}: {detalle}"
    except Exception as e:
        return False, str(e)


CUERPO_ES = """Hola{nombre}:

Acá está el informe completo de tu carta natal, en PDF.

Adentro encontrarás el gráfico de tu carta, los datos de todos tus
planetas y casas, la lectura completa de tu carta natal, los tránsitos
de los planetas lentos y la edad zodiacal que estás viviendo.

Léelo con calma. No es un texto para pasar rápido: es tu mapa de
navegación.

Si quieres que lo conversemos, puedes agendar una cita conmigo en
https://calendly.com/ricardopuerta

Un abrazo,

Ricardo Puerta Isaza
arquitecto & astrólogo
ricardopuerta.com
"""

CUERPO_EN = """Hello{nombre}:

Here is the complete report of your natal chart, as a PDF.

Inside you will find your chart, the data of every planet and house,
the full reading of your natal chart, the transits of the slow planets
and the zodiacal age you are living now.

Read it slowly. It is not a text to skim: it is your map of navigation.

If you would like to talk it through, you can book a consultation with
me at https://calendly.com/ricardopuerta

Warmly,

Ricardo Puerta Isaza
architect & astrologer
ricardopuerta.com
"""


def enviar_informe(destino, pdf_bytes, nombre="", lang="es"):
    """Envía el PDF al correo de la persona. Devuelve (True, '') o (False, motivo)."""
    if not correo_configurado():
        return False, "El envío de correo no está configurado en el servidor."

    es = (lang != "en")
    saludo = f" {nombre.split()[0]}" if nombre else ""
    archivo_pdf = ("Carta natal - " + (nombre or "informe")).strip() + ".pdf"

    if BREVO_API_KEY:
        return _enviar_por_api(
            destino,
            ("Tu carta natal completa · Ricardo Puerta" if es
             else "Your complete natal chart · Ricardo Puerta"),
            (CUERPO_ES if es else CUERPO_EN).format(nombre=saludo),
            pdf_bytes, archivo_pdf)
    mensaje = EmailMessage()
    mensaje["Subject"] = ("Tu carta natal completa · Ricardo Puerta" if es
                          else "Your complete natal chart · Ricardo Puerta")
    mensaje["From"] = REMITENTE
    mensaje["To"] = destino
    if COPIA_OCULTA:
        mensaje["Bcc"] = COPIA_OCULTA
    mensaje.set_content((CUERPO_ES if es else CUERPO_EN).format(nombre=saludo))

    archivo = ("Carta natal - " + (nombre or "informe")).strip() + ".pdf"
    mensaje.add_attachment(pdf_bytes, maintype="application", subtype="pdf",
                           filename=archivo)

    try:
        contexto = ssl.create_default_context()
        if PUERTO == 465:
            with smtplib.SMTP_SSL(SERVIDOR, PUERTO, context=contexto, timeout=30) as s:
                s.login(USUARIO, CLAVE)
                s.send_message(mensaje)
        else:
            with smtplib.SMTP(SERVIDOR, PUERTO, timeout=30) as s:
                s.ehlo()
                s.starttls(context=contexto)
                s.login(USUARIO, CLAVE)
                s.send_message(mensaje)
        return True, ""
    except Exception as e:
        print("Correo: no se pudo enviar:", repr(e))
        return False, str(e)


def enviar_prueba(destino):
    """Correo corto para comprobar que la configuración sirve."""
    if not correo_configurado():
        return False, "Faltan las variables del correo en el servidor."
    if BREVO_API_KEY:
        return _enviar_por_api(
            destino, "Prueba de envío · carta.ricardopuerta.com",
            "Esto es una prueba. Si te llegó, el servidor ya puede enviar los informes.\n\n"
            "Ricardo Puerta Isaza")
    mensaje = EmailMessage()
    mensaje["Subject"] = "Prueba de envío · carta.ricardopuerta.com"
    mensaje["From"] = REMITENTE
    mensaje["To"] = destino
    mensaje.set_content(
        "Esto es una prueba. Si te llegó, el servidor ya puede enviar los informes.\n\n"
        "Ricardo Puerta Isaza")
    try:
        contexto = ssl.create_default_context()
        if PUERTO == 465:
            with smtplib.SMTP_SSL(SERVIDOR, PUERTO, context=contexto, timeout=30) as s:
                s.login(USUARIO, CLAVE)
                s.send_message(mensaje)
        else:
            with smtplib.SMTP(SERVIDOR, PUERTO, timeout=30) as s:
                s.ehlo()
                s.starttls(context=contexto)
                s.login(USUARIO, CLAVE)
                s.send_message(mensaje)
        return True, ""
    except Exception as e:
        return False, str(e)

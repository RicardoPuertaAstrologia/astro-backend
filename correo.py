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
import smtplib
from email.message import EmailMessage

SERVIDOR = os.environ.get("CORREO_SERVIDOR", "")
PUERTO = int(os.environ.get("CORREO_PUERTO", "465") or 465)
USUARIO = os.environ.get("CORREO_USUARIO", "")
CLAVE = os.environ.get("CORREO_CLAVE", "")
REMITENTE = os.environ.get("CORREO_REMITENTE") or (
    f"Ricardo Puerta Isaza <{USUARIO}>" if USUARIO else "")
COPIA_OCULTA = os.environ.get("CORREO_COPIA", "")   # opcional: copia para ti


def correo_configurado():
    return bool(SERVIDOR and USUARIO and CLAVE)


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

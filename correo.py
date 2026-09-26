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

# El logotipo de la firma. Tiene que estar colgado en una dirección pública,
# porque Brevo no deja incrustar imágenes dentro del correo. Se sube a la
# carpeta "assets" del repositorio del front y Vercel lo sirve solo.
# Si algún día cambia de sitio, se cambia la variable LOGO_CORREO en Render.
LOGO = os.environ.get(
    "LOGO_CORREO", "https://carta.ricardopuerta.com/assets/logo-correo.png")
CITAS = os.environ.get("ENLACE_CITAS", "https://calendly.com/ricardopuerta")
SITIO = os.environ.get("SITIO_WEB", "https://www.ricardopuerta.com")


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


def _enviar_por_api(destino, asunto, texto, pdf_bytes=None, archivo="informe.pdf",
                    html=None):
    """Envía usando la API de Brevo por HTTPS. No usa puertos de correo."""
    nombre, correo = _remitente_partido()
    cuerpo = {
        "sender": {"name": nombre, "email": correo},
        "to": [{"email": destino}],
        "subject": asunto,
        "textContent": texto,
    }
    if html:
        cuerpo["htmlContent"] = html
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


# ============================================================
# EL TEXTO DEL CORREO
# Los párrafos van sueltos en una lista: el mismo texto sirve para la
# versión con diseño (HTML) y para la de texto plano, y así no hay
# manera de que se desincronicen.
# ============================================================

PARRAFOS_ES = [
    "Ante todo, quiero agradecerte por acceder a este informe completo y "
    "detallado de tu **carta astral natal**.",

    "En este archivo en PDF que recibes encontrarás el gráfico de tu carta, "
    "los datos de todos tus planetas y casas, la lectura completa de tu carta "
    "natal, los tránsitos actuales de los planetas lentos y la influencia que "
    "ellos hacen sobre tu carta natal, y la edad zodiacal que estás viviendo.",

    "Léelo con calma. No es un texto para pasar rápido: acá tienes tu mapa de "
    "navegación. Y cada vez que necesites, revísalo y recuerda que desde que "
    "naciste tienes la posibilidad de comprender mejor las herramientas con "
    "las que vienes a esta vida, y potenciar lo que se te facilita y trabajar "
    "con consciencia en lo que se te dificulta. Conocer tu **mapa de "
    "navegación** es **conocerte a ti mismo(a)**.",

    "Si además de este informe que recibes quisieras tener una **cita "
    "presencial o virtual** conmigo para revisar, aclarar y ver muchas más "
    "cosas de tu mapa usando otras técnicas astrológicas adicionales, puedes "
    "programar una cita aquí:",

    "Espero que toda esta información te sea muy útil y que, si quieres además "
    "conocer un poco más a las personas con las que compartes tu vida y "
    "comprenderlos mejor, puedes ver el mapa de ellos, ojalá con su "
    "autorización. Recuerda que **la hora exacta de nacimiento es la clave** "
    "para la precisión de este informe.",
]

PARRAFOS_EN = [
    "First of all, thank you for choosing this complete and detailed report "
    "of your **natal chart**.",

    "In this PDF you will find the graphic of your chart, the data of all your "
    "planets and houses, the full reading of your natal chart, the current "
    "transits of the slow planets and the influence they exert on your natal "
    "chart, and the zodiacal age you are living now.",

    "Read it slowly. It is not a text to skim: here you have your map of "
    "navigation. Come back to it whenever you need to, and remember that ever "
    "since you were born you have had the possibility of better understanding "
    "the tools you came into this life with - to make the most of what comes "
    "easily to you and to work consciously on what does not. To know your "
    "**map of navigation** is to **know yourself**.",

    "If, beyond this report, you would like to have an **in-person or online "
    "consultation** with me, to review, clarify and see much more of your map "
    "using further astrological techniques, you can book a time here:",

    "I hope all of this is truly useful to you. And if you also want to know "
    "the people you share your life with a little better, and understand them "
    "more deeply, you can look at their map too - ideally with their consent. "
    "Remember that **the exact time of birth is the key** to the accuracy of "
    "this report.",
]

TEXTOS = {
    "es": {
        "asunto": "Tu carta natal completa · Ricardo Puerta Isaza",
        "saludo": "Hola{nombre},",
        "parrafos": PARRAFOS_ES,
        "boton": "Agendar una cita",
        "despedida": "Con mucho aprecio,",
        "alt": "Ricardo Puerta Isaza · arquitecto & astrólogo",
        "adjunto": "Tu informe va adjunto a este correo, en PDF.",
    },
    "en": {
        "asunto": "Your complete natal chart · Ricardo Puerta Isaza",
        "saludo": "Hello{nombre},",
        "parrafos": PARRAFOS_EN,
        "boton": "Book a consultation",
        "despedida": "With much appreciation,",
        "alt": "Ricardo Puerta Isaza · architect & astrologer",
        "adjunto": "Your report is attached to this email, as a PDF.",
    },
}


def _negrillas(texto, html=False):
    """Los **asteriscos** se vuelven negrilla en el HTML, y se quitan en el
    texto plano. Así el texto se escribe una sola vez."""
    partes = texto.split("**")
    if not html:
        return "".join(partes)
    salida = []
    for i, p in enumerate(partes):
        p = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        salida.append(f"<strong>{p}</strong>" if i % 2 else p)
    return "".join(salida)


def _texto_plano(t, nombre):
    """La versión sin diseño, para los pocos lectores que no muestran HTML."""
    lineas = [t["saludo"].format(nombre=nombre), ""]
    for i, p in enumerate(t["parrafos"]):
        lineas.append(_negrillas(p))
        if i == 3:
            lineas.append(CITAS)
        lineas.append("")
    lineas += [t["despedida"], "",
               "Ricardo Puerta Isaza",
               t["alt"].split("·")[-1].strip(),
               SITIO.replace("https://", "")]
    return "\n".join(lineas)


def _html(t, nombre):
    """La versión con diseño. Todo va con estilos puestos a mano dentro de
    cada etiqueta y con tablas, que es lo único que entienden bien todos los
    programas de correo, Outlook incluido."""
    cuerpo = []
    for i, p in enumerate(t["parrafos"]):
        cuerpo.append(
            '<p style="margin:0 0 18px;">' + _negrillas(p, html=True) + "</p>")
        if i == 3:
            cuerpo.append(
                '<table role="presentation" cellpadding="0" cellspacing="0" '
                'border="0" style="margin:4px 0 26px;"><tr>'
                '<td align="center" bgcolor="#0b0e12" style="border-radius:28px;">'
                f'<a href="{CITAS}" style="display:inline-block;padding:14px 30px;'
                'font-family:Helvetica,Arial,sans-serif;font-size:15px;'
                'font-weight:bold;color:#c9a961;text-decoration:none;'
                f'border-radius:28px;">{t["boton"]}</a>'
                "</td></tr></table>")
    return f"""<!DOCTYPE html>
<html lang="{'es' if t is TEXTOS['es'] else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t["asunto"]}</title>
</head>
<body style="margin:0;padding:0;background-color:#f7f5f0;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{t["adjunto"]}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background-color:#f7f5f0;">
  <tr><td align="center" style="padding:26px 12px 40px;">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           style="width:100%;max-width:600px;background-color:#ffffff;
                  border:1px solid #e2ded4;">
      <tr><td style="background-color:#0b0e12;height:5px;line-height:5px;
                     font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:36px 34px 6px;font-family:Georgia,'Times New Roman',serif;
                     font-size:16.5px;line-height:1.68;color:#15181d;">
        <p style="margin:0 0 20px;font-size:18px;">{t["saludo"].format(nombre=nombre)}</p>
        {"".join(cuerpo)}
        <p style="margin:26px 0 0;">{t["despedida"]}</p>
      </td></tr>
      <tr><td style="padding:22px 34px 34px;">
        <div style="border-top:1px solid #e2ded4;padding-top:24px;">
          <img src="{LOGO}" width="200" alt="{t["alt"]}"
               style="display:block;width:200px;max-width:62%;height:auto;border:0;">
          <p style="margin:14px 0 0;font-family:Helvetica,Arial,sans-serif;
                    font-size:13px;">
            <a href="{SITIO}" style="color:#96762f;text-decoration:none;
               font-weight:bold;">{SITIO.replace("https://", "")}</a>
          </p>
        </div>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def enviar_informe(destino, pdf_bytes, nombre="", lang="es"):
    """Envía el PDF al correo de la persona. Devuelve (True, '') o (False, motivo)."""
    if not correo_configurado():
        return False, "El envío de correo no está configurado en el servidor."

    es = (lang != "en")
    t = TEXTOS["es" if es else "en"]
    saludo = f" {nombre.split()[0]}" if nombre else ""
    archivo_pdf = (("Natal chart - " if not es else "Carta natal - ")
                   + (nombre or ("report" if not es else "informe"))).strip() + ".pdf"

    plano = _texto_plano(t, saludo)
    conservado = _html(t, saludo)

    if BREVO_API_KEY:
        return _enviar_por_api(destino, t["asunto"], plano,
                               pdf_bytes, archivo_pdf, html=conservado)

    mensaje = EmailMessage()
    mensaje["Subject"] = t["asunto"]
    mensaje["From"] = REMITENTE
    mensaje["To"] = destino
    if COPIA_OCULTA:
        mensaje["Bcc"] = COPIA_OCULTA
    mensaje.set_content(plano)
    mensaje.add_alternative(conservado, subtype="html")

    mensaje.add_attachment(pdf_bytes, maintype="application", subtype="pdf",
                           filename=archivo_pdf)

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

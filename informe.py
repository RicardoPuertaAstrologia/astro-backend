# ============================================================
# INFORME EN PDF — Ricardo Puerta · Astrología
#
# Arma el PDF del informe completo en el servidor:
#   · portada con los datos de nacimiento
#   · el gráfico de la carta (la imagen que manda el navegador)
#   · las tablas de planetas y casas
#   · la lectura de la carta natal (textos del servidor)
#   · la edad zodiacal de la persona
#   · las secciones que el navegador ya tenía calculadas
# ============================================================

import os
import io
import re
import json
import base64
from datetime import datetime

from fpdf import FPDF

_dir = os.path.dirname(os.path.abspath(__file__))

TINTA = (21, 24, 29)
SUAVE = (90, 95, 103)
# Los colores son los mismos de la maqueta del sitio:
#   --tinta #15181d · --tinta-suave #5a5f67 · --linea #e2ded4
#   --oro #c9a961 (sobre fondo oscuro) · --oro-tinta #96762f (sobre papel)
#   --noche #0b0e12 · --papel #f7f5f0
ORO = (150, 118, 47)          # --oro-tinta, el dorado sobre papel
ORO_CLARO = (201, 169, 97)    # --oro, el dorado sobre el fondo oscuro
ORO_OSCURO = ORO              # el mismo dorado de la marca
NOCHE = (11, 14, 18)          # --noche
PAPEL = (247, 245, 240)       # --papel
VERDE = (45, 106, 58)         # --success, lo que se facilita
VERDE_FONDO = (240, 246, 241)
ROJO = (155, 62, 62)          # --error, lo que se dificulta
ROJO_FONDO = (250, 242, 242)

# La dirección a la que lleva el botón del PDF gratis. Si algún día cambia
# el dominio, se cambia aquí y ya.
DIRECCION = os.environ.get("DIRECCION_APP", "https://carta.ricardopuerta.com")

_AQUI = os.path.dirname(os.path.abspath(__file__))


def _buscar(nombre, *carpetas):
    """Busca un archivo en varias carpetas y al lado del código. Así los
    tipos de letra y los logos pueden ir en su carpeta o sueltos en la
    raíz del repositorio: funciona de las dos maneras."""
    for carpeta in list(carpetas) + [""]:
        ruta = os.path.join(_AQUI, carpeta, nombre) if carpeta else os.path.join(_AQUI, nombre)
        if os.path.exists(ruta):
            return ruta
    return os.path.join(_AQUI, nombre)


RUTA_LOGO_BLANCO = _buscar("logo-blanco.png", "assets")
RUTA_LOGO_OSCURO = _buscar("logo-oscuro.png", "assets")


def _registrar_fuentes(pdf):
    """Carga la tipografía de la marca. Si no está, el informe se arma
    igual con las tipografías estándar: nunca se cae por esto."""
    try:
        pdf.add_font("Cormorant", "", _buscar("Cormorant-Regular.ttf", "fuentes"))
        pdf.add_font("Cormorant", "B", _buscar("Cormorant-SemiBold.ttf", "fuentes"))
        pdf.add_font("Inter", "", _buscar("Inter-Regular.ttf", "fuentes"))
        pdf.add_font("Inter", "B", _buscar("Inter-SemiBold.ttf", "fuentes"))
        return True
    except Exception as e:
        print("Informe: sin tipografía de marca, se usan las estándar:", e)
        return False


def _nombre_bonito(nombre):
    """Si la persona escribió su nombre todo en minúsculas, se le ponen
    las mayúsculas. Si ya usó mayúsculas, se respeta como lo escribió."""
    n = (nombre or "").strip()
    if not n:
        return n
    if n == n.lower():
        return " ".join(p[:1].upper() + p[1:] if len(p) > 2 or p.lower() not in
                        ("de", "del", "la", "las", "los", "y", "van", "der")
                        else p for p in n.split())
    return n
LINEA = (226, 222, 212)

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _limpiar(texto):
    """El PDF usa fuentes estándar; se quitan los caracteres que no existen
    en ellas y se cambian por su equivalente."""
    if texto is None:
        return ""
    t = str(texto)
    cambios = {
        "—": "-", "–": "-", "―": "-",
        "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'",
        "…": "...", " ": " ", "​": "",
        "′": "'", "″": '"',
    }
    for a, b in cambios.items():
        t = t.replace(a, b)

    # Los símbolos de planetas y aspectos se QUITAN, no se traducen: en el
    # PDF el nombre siempre va al lado, y traducirlos producía repeticiones
    # como "Jupiter Júpiter" o "Lilith Lilith".
    simbolos = "☉☽☾☿♀♂♃♄♅♆♇⚷☊☋⚸⊕⊗☌☍□△▽⚹✶✳✱"
    t = re.sub(r"\(\s*[" + simbolos + r"]+\s*\)", "", t)   # paréntesis que quedarían vacíos
    for c in simbolos:
        t = t.replace(c, " ")
    t = re.sub(r"<[^>]+>", "", t)          # por si viene algo de HTML
    # Los emojis y demás signos que la fuente no tiene se QUITAN.
    # Antes se cambiaban por "?", y por eso los íconos de las áreas de
    # vida salían como signos de interrogación.
    t = "".join(c for c in t if c in "\n\t" or ord(c) < 256)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip(" \t")


def _es_etiqueta(linea):
    """Una línea corta, toda en mayúsculas, es un rótulo y no un párrafo."""
    t = linea.strip()
    if len(t) > 42 or len(t) < 3:
        return False
    letras = [c for c in t if c.isalpha()]
    return bool(letras) and all(c.isupper() for c in letras)


class InformePDF(FPDF):
    def __init__(self, titulo_pie=""):
        super().__init__(format="Letter", unit="mm")
        self.marca = _registrar_fuentes(self)
        # Con la tipografía de la marca se usa esa; si no está, las de siempre.
        self.display = "Cormorant" if self.marca else "Times"
        self.sans = "Inter" if self.marca else "Helvetica"
        self.paginas_sin_numero = 2
        self.titulo_pie = _limpiar(titulo_pie)
        self.set_auto_page_break(auto=True, margin=22)
        self.set_margins(22, 22, 22)
        self.portada = True

    def footer(self):
        if self.page_no() <= getattr(self, "paginas_sin_numero", 1):
            return
        self.set_y(-16)
        self.set_font(self.sans, "", 7)
        self.set_text_color(*SUAVE)
        self.cell(0, 4, self.titulo_pie, align="L")
        self.cell(0, 4, str(self.page_no() - getattr(self, "paginas_sin_numero", 1)), align="R")

    # --- piezas ---
    def titulo_seccion(self, texto, en_indice=False):
        if en_indice:
            self.indice.append((texto, self.page_no() - self.paginas_sin_numero))
        self.ln(4)
        self.set_font(self.sans, "B", 8)
        self.set_text_color(*ORO)
        self.cell(0, 5, _limpiar(texto).upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINEA)
        y = self.get_y() + 1
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    def subtitulo(self, texto):
        """El nombre de cada pieza: "Sol en Casa 5", "Júpiter", "Pareja y
        vínculos". Grande, en la tipografía de la marca y con aire
        arriba, que es lo que ordena la página."""
        if self.get_y() > self.h - 48:
            self.add_page()
        self.ln(6)
        self.set_font(self.display, "B", 19)
        self.set_text_color(*TINTA)
        self.multi_cell(0, 8, _limpiar(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINEA)
        y = self.get_y() + 1.5
        self.line(self.l_margin, y, self.l_margin + 26, y)
        self.ln(4.5)

    def subrotulo(self, texto):
        """Los rótulos de adentro ("Lo que significa este tránsito",
        "Los aspectos a tus planetas natales"): pequeños, en versalitas
        y en el dorado de la marca. Es el nivel intermedio que le daba
        aire a la lectura en pantalla."""
        if self.get_y() > self.h - 34:
            self.add_page()
        self.ln(3.5)
        self.set_font(self.sans, "B", 7.5)
        self.set_text_color(*ORO)
        self.set_char_spacing(1.1)
        self.multi_cell(0, 4.5, _limpiar(texto).upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_char_spacing(0)
        self.set_text_color(*TINTA)
        self.ln(1.5)

    def etiqueta(self, texto):
        """Las mayúsculas cortas del navegador ("TU CARTA") salen como
        etiqueta pequeña, igual que en el resto del informe."""
        self.ln(1)
        self.set_font(self.sans, "B", 7.5)
        self.set_text_color(*SUAVE)
        self.cell(0, 4.5, _limpiar(texto).upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(0.5)

    def recuadro(self, etiqueta, texto, favorable=True):
        """Los dos recuadros de los aspectos: lo que se facilita en verde,
        lo que se dificulta en rojo. Igual que se ven en pantalla."""
        color = VERDE if favorable else ROJO
        fondo = VERDE_FONDO if favorable else ROJO_FONDO
        ancho = self.w - self.l_margin - self.r_margin

        # Se mide el alto antes de pintar, para no partir el recuadro.
        self.set_font("Times", "", 10)
        lineas = len(self.multi_cell(ancho - 10, 4.8, _limpiar(texto), dry_run=True,
                                     output="LINES", new_x="LMARGIN", new_y="NEXT"))
        alto = 9 + lineas * 4.8 + 4
        if self.get_y() + alto > self.h - 26:
            self.add_page()

        y0 = self.get_y()
        self.set_fill_color(*fondo)
        self.rect(self.l_margin, y0, ancho, alto, style="F")
        self.set_fill_color(*color)
        self.rect(self.l_margin, y0, 1.2, alto, style="F")

        self.set_xy(self.l_margin + 5, y0 + 2.5)
        self.set_font(self.sans, "B", 7)
        self.set_text_color(*color)
        self.cell(ancho - 10, 4, _limpiar(etiqueta).upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_xy(self.l_margin + 5, y0 + 7.5)
        self.set_font("Times", "", 10)
        self.set_text_color(*TINTA)
        self.multi_cell(ancho - 10, 4.8, _limpiar(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_y(y0 + alto + 2)

    def renglon(self, texto):
        """Una línea de lista, apretada: el calendario es una agenda,
        no un texto corrido."""
        if self.get_y() > self.h - 30:
            self.add_page()
        self.set_font("Times", "", 10.5)
        self.set_text_color(*TINTA)
        self.multi_cell(0, 4.6, _limpiar(texto), markdown=True,
                        new_x="LMARGIN", new_y="NEXT")

    def destacado(self, texto):
        """El renglón que nombra un aspecto: en negrilla y en el dorado de
        la marca, para que ordene la lectura de un vistazo."""
        if self.get_y() > self.h - 34:
            self.add_page()
        self.ln(2)
        self.set_font("Times", "B", 11.5)
        self.set_text_color(*ORO_OSCURO)
        self.multi_cell(0, 5.4, _limpiar(texto), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*TINTA)
        self.ln(0.5)

    def pastilla(self, texto, url):
        """Un botón redondeado, dorado sobre fondo oscuro, que se puede
        pulsar dentro del PDF y abre la página de la carta."""
        limpio = _limpiar(texto)
        self.set_font(self.sans, "B", 11)
        ancho = self.get_string_width(limpio) + 24
        alto = 13.5
        if self.get_y() + alto > self.h - self.b_margin:
            self.add_page()
        x, y = self.l_margin, self.get_y()
        self.set_fill_color(*NOCHE)
        self.rect(x, y, ancho, alto, style="F", round_corners=True, corner_radius=6.5)
        self.set_text_color(*ORO_CLARO)
        self.set_xy(x, y)
        self.cell(ancho, alto, limpio, align="C")
        self.link(x, y, ancho, alto, url)
        self.set_xy(self.l_margin, y + alto)
        self.set_text_color(*TINTA)

    def enlace(self, texto, url):
        """La dirección escrita, también pulsable, debajo del botón."""
        limpio = _limpiar(texto)
        self.set_font(self.sans, "B", 9)
        self.set_text_color(*ORO)
        x, y = self.l_margin, self.get_y()
        ancho = self.get_string_width(limpio)
        self.cell(0, 6, limpio, new_x="LMARGIN", new_y="NEXT")
        self.link(x, y, ancho, 6, url)
        self.set_text_color(*TINTA)

    def rotulo_mes(self, texto):
        """El mes, con su raya: es lo que la persona busca al hojear."""
        if self.get_y() > self.h - 32:
            self.add_page()
        self.ln(3)
        self.set_font(self.sans, "B", 9)
        self.set_text_color(*ORO_OSCURO)
        self.cell(0, 5, _limpiar(texto).upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINEA)
        y = self.get_y() + 0.5
        self.line(self.l_margin, y, self.l_margin + 60, y)
        self.ln(3)
        self.set_text_color(*TINTA)

    def parrafo(self, texto, cursiva=False):
        self.set_font("Times", "I" if cursiva else "", 11)
        self.set_text_color(*TINTA)
        limpio = re.sub(r" {2,}", " ", _limpiar(texto))
        # En tus textos el énfasis va entre asteriscos sueltos: *así*.
        # El armador del PDF solo entiende **negrilla** y __cursiva__,
        # así que los asteriscos sueltos se traducen a cursiva.
        limpio = re.sub(r"(?<!\*)\*([^*\n]{1,300})\*(?!\*)", r"__\1__", limpio)
        self.multi_cell(0, 5.4, limpio, markdown=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def linea_dato(self, etiqueta, valor):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*SUAVE)
        self.cell(45, 5.5, _limpiar(etiqueta))
        self.set_text_color(*TINTA)
        self.multi_cell(0, 5.5, _limpiar(valor), new_x="LMARGIN", new_y="NEXT")

    def tabla(self, encabezados, filas, anchos):
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*SUAVE)
        self.set_draw_color(*LINEA)
        for h, w in zip(encabezados, anchos):
            self.cell(w, 6, _limpiar(h).upper(), border="B")
        self.ln(6)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*TINTA)
        for fila in filas:
            if self.get_y() > self.h - 30:
                self.add_page()
            for valor, w in zip(fila, anchos):
                self.cell(w, 5.8, _limpiar(valor), border="B")
            self.ln(5.8)
        self.ln(3)


# ------------------------------------------------------------
# TÍTULOS DE CADA INTERPRETACIÓN
# ------------------------------------------------------------
_PLANETAS = {
    "sol": ("Sol", "Sun"), "luna": ("Luna", "Moon"), "mercurio": ("Mercurio", "Mercury"),
    "venus": ("Venus", "Venus"), "marte": ("Marte", "Mars"), "jupiter": ("Júpiter", "Jupiter"),
    "saturno": ("Saturno", "Saturn"), "urano": ("Urano", "Uranus"),
    "neptuno": ("Neptuno", "Neptune"), "pluton": ("Plutón", "Pluto"),
    "quiron": ("Quirón", "Chiron"), "lilith": ("Lilith", "Lilith"),
    # Los textos de la biblioteca usan los nombres en español; los datos
    # de los tránsitos y el calendario los usan en inglés. Valen los dos.
    "sun": ("Sol", "Sun"), "moon": ("Luna", "Moon"), "mercury": ("Mercurio", "Mercury"),
    "mars": ("Marte", "Mars"), "saturn": ("Saturno", "Saturn"),
    "uranus": ("Urano", "Uranus"), "neptune": ("Neptuno", "Neptune"),
    "pluto": ("Plutón", "Pluto"), "chiron": ("Quirón", "Chiron"),
    "true_node": ("Nodo Norte", "North Node"), "north_node": ("Nodo Norte", "North Node"),
    "south_node": ("Nodo Sur", "South Node"),
    "fortuna": ("Rueda de la Fortuna", "Part of Fortune"),
    "infortunio": ("Parte del Infortunio", "Part of Misfortune"),
    "asc": ("Ascendente", "Ascendant"), "ascendente": ("Ascendente", "Ascendant"),
    "ascendant": ("Ascendente", "Ascendant"),
    "mc": ("Medio Cielo", "Midheaven"), "medio_cielo": ("Medio Cielo", "Midheaven"),
}


def _nombre_planeta(clave, es):
    par = _PLANETAS.get(str(clave).lower())
    if par:
        return par[0] if es else par[1]
    return str(clave).capitalize()


def _signo(nombre, es):
    n = str(nombre).capitalize()
    if es:
        return n
    tabla = {"Aries": "Aries", "Tauro": "Taurus", "Geminis": "Gemini", "Géminis": "Gemini",
             "Cancer": "Cancer", "Cáncer": "Cancer", "Leo": "Leo", "Virgo": "Virgo",
             "Libra": "Libra", "Escorpio": "Scorpio", "Sagitario": "Sagittarius",
             "Capricornio": "Capricorn", "Acuario": "Aquarius", "Piscis": "Pisces"}
    return tabla.get(n, n)


def titulo_de(clave, item, es=True):
    """Arma el título que va encima de cada texto."""
    tipo = item.get("tipo", "")
    casa = item.get("casa")
    signo = item.get("signo")
    planeta = item.get("planeta")
    en = "en" if es else "in"
    casa_p = "Casa" if es else "House"

    if tipo == "ascendente":
        return ("Ascendente en " if es else "Ascendant in ") + _signo(signo, es)
    if tipo == "planeta_en_signo":
        return f"{_nombre_planeta(planeta, es)} {en} {_signo(signo, es)}"
    if tipo == "planeta_en_casa":
        return f"{_nombre_planeta(planeta, es)} {en} {casa_p} {casa}"
    if tipo == "nodo_norte":
        return ("Nodo Norte en " if es else "North Node in ") + _signo(signo, es)
    if tipo == "nodo_sur":
        return ("Nodo Sur en " if es else "South Node in ") + _signo(signo, es)
    if tipo == "nodo_norte_casa":
        return ("Nodo Norte en " if es else "North Node in ") + f"{casa_p} {casa}"
    if tipo == "nodo_sur_casa":
        return ("Nodo Sur en " if es else "South Node in ") + f"{casa_p} {casa}"
    if tipo == "puente_nodal":
        return ("El puente nodal" if es else "The nodal bridge")
    if tipo == "fortuna_signo":
        return ("Rueda de la Fortuna en " if es else "Part of Fortune in ") + _signo(signo, es)
    if tipo == "fortuna_casa":
        return ("Rueda de la Fortuna en " if es else "Part of Fortune in ") + f"{casa_p} {casa}"
    if tipo == "aspecto":
        a = item.get("aspecto", "")
        p1 = _nombre_planeta(item.get("planeta1"), es)
        p2 = _nombre_planeta(item.get("planeta2"), es)
        return f"{p1} {a.lower()} {p2}" if es else f"{p1} {a.lower()} {p2}"
    return str(clave).replace("_", " ").capitalize()


_ORDEN = ["ascendente", "planeta_en_signo", "planeta_en_casa", "nodo_norte", "nodo_sur",
          "nodo_norte_casa", "nodo_sur_casa", "puente_nodal", "fortuna_signo",
          "fortuna_casa", "aspecto"]

_ORDEN_PLANETAS = ["sol", "luna", "mercurio", "venus", "marte", "jupiter", "saturno",
                   "urano", "neptuno", "pluton", "quiron", "lilith"]


ASPECTOS_ES = ["Conjunción", "Sextil", "Cuadratura", "Trígono", "Oposición"]
ASPECTOS_EN = ["Conjunction", "Sextile", "Square", "Trine", "Opposition"]

_CIERRES = re.compile(
    r"^(Spoiler ácido|Otro pecado|Y un tercer|Otro riesgo|Tu camino evolutivo|"
    r"Tu trabajo evolutivo|Cuando alineas|Acidic spoiler|Another typical sin|"
    r"And a third|Another risk|Your evolutionary|When you align)", re.IGNORECASE)


def filtrar_por_aspecto(texto, nombre_aspecto):
    """Cada texto de aspectos trae los cinco casos (conjunción, sextil,
    cuadratura, trígono y oposición). En pantalla se muestra solo el que
    la carta tiene de verdad; acá se hace lo mismo para el PDF.

    Se conserva la introducción, el párrafo del aspecto que aplica y el
    cierre (spoiler ácido, camino evolutivo). Los otros cuatro se quitan."""
    if not texto or not nombre_aspecto:
        return texto

    if nombre_aspecto in ASPECTOS_ES:
        lista = ASPECTOS_ES
    elif nombre_aspecto in ASPECTOS_EN:
        lista = ASPECTOS_EN
    else:
        return texto                      # aspecto desconocido: no se toca
    buscado = nombre_aspecto

    intro, elegido, cierre = [], [], []
    estado = "intro"

    for p in re.split(r"\n\n+", texto):
        limpio = p.strip()
        encabezado = None
        for asp in lista:
            if re.match(r"^\*\*[^*]*\b" + re.escape(asp) + r"\b", limpio, re.IGNORECASE):
                encabezado = asp
                break

        if encabezado:
            if encabezado == buscado:
                estado = "elegido"
                elegido.append(p)
            else:
                estado = "otro"
        elif _CIERRES.match(limpio):
            estado = "cierre"
            cierre.append(p)
        else:
            if estado == "intro":
                intro.append(p)
            elif estado == "elegido":
                elegido.append(p)
            elif estado == "cierre":
                cierre.append(p)
            # si estado == "otro", ese párrafo se descarta

    return "\n\n".join(intro + elegido + cierre)


def ordenar_interpretaciones(interpretaciones, es=True):
    """Convierte el diccionario del backend en una lista ordenada
    de {titulo, texto}, como se lee en pantalla."""
    if isinstance(interpretaciones, list):
        return interpretaciones
    items = []
    for clave, item in (interpretaciones or {}).items():
        tipo = item.get("tipo", "")
        planeta = str(item.get("planeta", "")).lower()
        items.append((
            _ORDEN.index(tipo) if tipo in _ORDEN else 99,
            _ORDEN_PLANETAS.index(planeta) if planeta in _ORDEN_PLANETAS else 99,
            item.get("casa") or 0,
            {"titulo": titulo_de(clave, item, es),
             "texto": (filtrar_por_aspecto(item.get("texto", ""), item.get("aspecto"))
                       if tipo == "aspecto" else item.get("texto", ""))}
        ))
    items.sort(key=lambda x: (x[0], x[1], x[2]))
    return [x[3] for x in items]


def _fecha_larga(bd, lang):
    try:
        fecha = str(bd.get("datetime", ""))[:16]
        d = datetime.strptime(fecha, "%Y-%m-%d %H:%M")
        if lang == "en":
            return f"{MESES_EN[d.month - 1]} {d.day}, {d.year} · {d.strftime('%H:%M')}"
        return f"{d.day} de {MESES_ES[d.month - 1]} de {d.year} · {d.strftime('%H:%M')}"
    except Exception:
        return str(bd.get("datetime", ""))


MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_EN = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"]


def _fecha_evento(texto_fecha, es):
    """De '2026-10-22 09:18 UT' saca (datetime, '22 de octubre de 2026')."""
    from datetime import datetime as _dt
    try:
        f = _dt.strptime(str(texto_fecha)[:10], "%Y-%m-%d")
    except Exception:
        return None, str(texto_fecha)
    if es:
        return f, f"{f.day} de {MESES_ES[f.month - 1]} de {f.year}"
    return f, f"{MESES_EN[f.month - 1]} {f.day}, {f.year}"


def _fecha_transitos(carta, lang):
    """El día para el que se dibujaron los tránsitos, que es el día en que
    se generó el informe."""
    es = (lang != "en")
    crudo = ((carta.get("transits") or {}).get("datetime_utc") or "")[:10]
    from datetime import datetime as _dt
    try:
        f = _dt.strptime(crudo, "%Y-%m-%d")
    except Exception:
        f = _dt.utcnow()
    if es:
        return f"{f.day} de {MESES_ES[f.month - 1]} de {f.year}"
    return f"{MESES_EN[f.month - 1]} {f.day}, {f.year}"


def _ya_paso(fecha):
    from datetime import datetime as _dt
    return fecha.date() < _dt.utcnow().date()


def _cuanto_falta(fecha, es):
    """'dentro de 3 meses', 'este mes', 'dentro de un año'."""
    from datetime import datetime as _dt
    if not fecha:
        return ""
    dias = (fecha.date() - _dt.utcnow().date()).days
    if dias < 0:
        return "ya pasó" if es else "already past"
    if dias < 30:
        return "este mes" if es else "this month"
    meses = round(dias / 30.4)
    if meses <= 1:
        return "dentro de un mes" if es else "in a month"
    if meses >= 12:
        return "dentro de un año" if es else "in a year"
    return (f"dentro de {meses} meses" if es else f"in {meses} months")


def _INDICE_VACIO(es):
    """En la primera pasada todavía no se saben los números de página;
    se escriben los títulos sin número para que el índice ocupe lo mismo."""
    titulos = (["Tu carta natal y los tránsitos de hoy", "Los datos de tu carta",
                "Tu carta natal, leída", "Tránsitos de los planetas lentos",
                "Tus áreas de vida activadas", "Tu calendario · 12 meses",
                "Tu edad zodiacal", "Sobre este informe"] if es else
               ["Your natal chart and today's transits", "Your chart data",
                "Your natal chart, read", "Transits of the slow planets",
                "Your activated life areas", "Your 12-month calendar",
                "Your zodiacal age", "About this report"])
    return [(t, None) for t in titulos]


def construir_pdf_gratis(carta, edad_texto=None, imagen_png=None, lang="es"):
    """El informe de cortesía: la portada, el gráfico, las tablas de la
    carta y la edad zodiacal que la persona está viviendo. Nada de lo
    que se paga entra acá, porque sencillamente no se le pasa."""
    datos, _ = _armar(carta, None, edad_texto, None, imagen_png, lang,
                      calendario=None, indice=None, solo_gratis=True)
    return datos


def construir_pdf(carta, interpretaciones, edad_texto=None, secciones=None,
                  imagen_png=None, lang="es", calendario=None):
    """Se arma dos veces: la primera para saber en qué página queda cada
    sección, la segunda para escribir el índice con esos números."""
    _, paginas = _armar(carta, interpretaciones, edad_texto, secciones,
                        imagen_png, lang, calendario, indice=None)
    datos, _ = _armar(carta, interpretaciones, edad_texto, secciones,
                      imagen_png, lang, calendario, indice=paginas)
    return datos


def _pintar_indice(pdf, es, indice):
    """La segunda página: qué trae el informe y en qué página está cada
    cosa. Los números salen de la primera pasada."""
    pdf.titulo_seccion("Índice" if es else "Contents")
    pdf.ln(3)
    pdf.set_font(pdf.display, "B", 27)
    pdf.set_text_color(*TINTA)
    pdf.cell(0, 13, _limpiar("Lo que vas a encontrar" if es else "What you will find"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font(pdf.sans, "", 9.5)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 5.2, _limpiar(
        "Este informe se lee con calma. No hace falta seguirlo en orden: "
        "puedes entrar por donde te llame."
        if es else
        "This report is meant to be read slowly. You don't have to follow it "
        "in order: start wherever it calls you."),
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    for titulo, pagina in (indice or _INDICE_VACIO(es)):
        y = pdf.get_y()
        if y > pdf.h - 40:
            break
        pdf.set_font(pdf.display, "", 13)
        pdf.set_text_color(*TINTA)
        pdf.cell(0, 8, _limpiar(titulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*LINEA)
        pdf.line(pdf.l_margin, y + 7.6, pdf.w - pdf.r_margin, y + 7.6)
        if pagina:
            pdf.set_xy(pdf.w - pdf.r_margin - 16, y)
            pdf.set_font(pdf.sans, "B", 9)
            pdf.set_text_color(*ORO)
            pdf.cell(16, 8, str(pagina), align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)


def _armar(carta, interpretaciones, edad_texto=None, secciones=None,
           imagen_png=None, lang="es", calendario=None, indice=None,
           solo_gratis=False):
    """carta: lo que devuelve /calculate (birth_data + natal_chart)
       interpretaciones: lista de {titulo, texto} del servidor
       edad_texto: dict con la edad zodiacal de la persona (o None)
       secciones: [{titulo, bloques:[{subtitulo, parrafos:[...]}]}] del navegador
       imagen_png: la carta dibujada, en base64 (data:image/png;base64,...)
       calendario: [{planeta, eventos:[...]}] de los doce meses, uno por
                   cada planeta lento, calculado en el servidor"""
    es = (lang != "en")
    bd = carta.get("birth_data", {}) or {}
    natal = carta.get("natal_chart", {}) or {}
    nombre = bd.get("name") or ("Tu carta natal" if es else "Your natal chart")

    pdf = InformePDF(titulo_pie=f"{_nombre_bonito(nombre)} · Ricardo Puerta Isaza")
    pdf.indice = []
    pdf.add_page()

    # ---------- PORTADA ----------
    # En la portada se coloca cada cosa en su sitio exacto: sin esto, el
    # salto de página automático manda el remate a la hoja siguiente.
    pdf.set_auto_page_break(False)
    ancho_hoja = pdf.w
    alto_bloque = 88

    # El bloque oscuro de arriba, con el logotipo en blanco.
    pdf.set_fill_color(*NOCHE)
    pdf.rect(0, 0, ancho_hoja, alto_bloque, style="F")
    if os.path.exists(RUTA_LOGO_BLANCO):
        try:
            ancho_logo = 46
            pdf.image(RUTA_LOGO_BLANCO, x=(ancho_hoja - ancho_logo) / 2, y=15, w=ancho_logo)
        except Exception as e:
            print("Informe: no se pudo poner el logotipo:", e)
    pdf.set_y(69)
    pdf.set_font(pdf.sans, "", 7.5)
    pdf.set_text_color(*ORO_CLARO)
    pdf.set_char_spacing(2.2)
    pdf.cell(0, 5, "RICARDOPUERTA.COM", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_char_spacing(0)

    # El nombre de la persona, que es de lo que trata todo esto.
    # Cada pieza va en su sitio exacto, medido desde el borde de la hoja:
    # así la portada se ve igual con un nombre corto o largo.
    pdf.set_y(alto_bloque + 22)
    pdf.set_font(pdf.sans, "B", 7.5)
    pdf.set_text_color(*ORO)
    pdf.set_char_spacing(2.4)
    if solo_gratis:
        rotulo_portada = "TU CARTA NATAL" if es else "YOUR NATAL CHART"
    else:
        rotulo_portada = ("INFORME COMPLETO DE TU CARTA NATAL" if es
                          else "COMPLETE REPORT OF YOUR NATAL CHART")
    pdf.cell(0, 5, _limpiar(rotulo_portada), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_char_spacing(0)

    titular = _limpiar(_nombre_bonito(nombre))
    tamano = 56 if len(titular) <= 16 else (44 if len(titular) <= 24 else 32)
    pdf.set_y(alto_bloque + 30)
    pdf.set_font(pdf.display, "B", tamano)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, tamano * 0.40, titular, align="C", new_x="LMARGIN", new_y="NEXT")

    # Una raya corta, dorada, para separar sin ruido.
    y_raya = max(pdf.get_y() + 5, alto_bloque + 54)
    pdf.set_draw_color(*ORO)
    pdf.set_line_width(0.6)
    medio = ancho_hoja / 2
    pdf.line(medio - 17, y_raya, medio + 17, y_raya)
    pdf.set_line_width(0.2)

    pdf.set_y(y_raya + 9)
    pdf.set_font(pdf.display, "", 28)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 12, _limpiar(
        "El mapa de navegación con el que naciste" if es
        else "The map of navigation you were born with"),
        align="C", new_x="LMARGIN", new_y="NEXT")

    # El texto de la portada del sitio, el que explica de qué se trata.
    pdf.ln(8)
    margen = 34
    pdf.set_left_margin(margen)
    pdf.set_right_margin(margen)
    pdf.set_x(margen)
    pdf.set_font(pdf.display, "", 15)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 7.5, _limpiar(
        "La carta natal es la foto del cielo en el momento en el que naces, "
        "es tu mapa de navegación en esta vida. Entiéndela y podrás navegar "
        "con más seguridad y confianza."
        if es else
        "Your natal chart is the photograph of the sky at the moment you are "
        "born: it is your map of navigation in this life. Understand it and "
        "you will navigate with more certainty and confidence."),
        align="C", new_x="LMARGIN", new_y="NEXT")

    # Y tu firma, la de la maqueta, con las dos palabras destacadas.
    pdf.ln(5)
    pdf.set_x(margen)
    pdf.set_font(pdf.display, "", 13)
    pdf.set_text_color(*ORO)
    pdf.multi_cell(0, 6.4, _limpiar(
        "Todo en el **universo** es **vibración**. Si quieres conocer tu "
        "realidad interna y externa, conoce tu carta astral natal y verás "
        "cómo se aclara el camino de vida."
        if es else
        "Everything in the **universe** is **vibration**. If you want to know "
        "your inner and outer reality, know your natal chart and you will see "
        "the path of your life become clear."),
        align="C", markdown=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(22)
    pdf.set_right_margin(22)

    # Los datos de nacimiento, abajo, en su propio bloque.
    pdf.set_y(pdf.h - 46)
    pdf.set_draw_color(*LINEA)
    pdf.line(medio - 30, pdf.get_y(), medio + 30, pdf.get_y())
    pdf.ln(6)
    pdf.set_font(pdf.sans, "B", 7)
    pdf.set_text_color(*ORO)
    pdf.set_char_spacing(2)
    pdf.cell(0, 4.5, _limpiar("DATOS DE NACIMIENTO" if es else "BIRTH DATA"),
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_char_spacing(0)
    pdf.ln(2)
    pdf.set_font(pdf.display, "", 15)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 7, _limpiar(_fecha_larga(bd, lang)), align="C",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(pdf.sans, "", 9)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 5, _limpiar(f"{bd.get('city', '')} · {bd.get('timezone', '')}"),
                   align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(pdf.h - 13)
    pdf.set_font(pdf.sans, "", 7.5)
    pdf.set_text_color(*ORO)
    pdf.cell(0, 4, _limpiar("Ricardo Puerta Isaza · " +
                            ("arquitecto & astrólogo" if es else "architect & astrologer")),
             align="C", new_x="LMARGIN", new_y="NEXT")

    # ---------- ÍNDICE ----------
    pdf.set_auto_page_break(auto=True, margin=22)
    if solo_gratis:
        pdf.paginas_sin_numero = 1      # sin índice, la portada es la única sin número
    else:
        pdf.add_page()
    if not solo_gratis:
        _pintar_indice(pdf, es, indice)

    # ---------- EL GRÁFICO ----------
    if imagen_png:
        try:
            crudo = imagen_png.split(",", 1)[-1]
            datos = io.BytesIO(base64.b64decode(crudo))
            pdf.add_page()
            pdf.portada = False
            pdf.titulo_seccion("Tu carta natal y los tránsitos de hoy" if es
                               else "Your natal chart and today's transits", en_indice=True)
            ancho = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.image(datos, x=pdf.l_margin, w=ancho)

            # Debajo de la rueda: de quién es la carta, con qué datos se
            # calculó, y para qué día son los tránsitos que se dibujaron.
            pdf.ln(4)
            pdf.set_draw_color(*LINEA)
            pdf.line(pdf.l_margin + 30, pdf.get_y(), pdf.w - pdf.r_margin - 30, pdf.get_y())
            pdf.ln(5)
            pdf.set_font(pdf.display, "B", 17)
            pdf.set_text_color(*TINTA)
            pdf.cell(0, 8, _limpiar(_nombre_bonito(nombre)), align="C",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            pdf.set_font(pdf.sans, "", 9)
            pdf.set_text_color(*SUAVE)
            pdf.multi_cell(0, 4.8, _limpiar(_fecha_larga(bd, lang)), align="C",
                           new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(0, 4.8, _limpiar(f"{bd.get('city', '')} · {bd.get('timezone', '')}"),
                           align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.set_font(pdf.sans, "B", 7)
            pdf.set_text_color(*ORO)
            pdf.set_char_spacing(2)
            pdf.cell(0, 4.5, _limpiar("TRÁNSITOS" if es else "TRANSITS"), align="C",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_char_spacing(0)
            pdf.ln(1)
            pdf.set_font(pdf.sans, "", 9)
            pdf.set_text_color(*SUAVE)
            pdf.multi_cell(0, 4.8, _limpiar(
                ("Calculados para el " if es else "Calculated for ")
                + _fecha_transitos(carta, lang)), align="C",
                new_x="LMARGIN", new_y="NEXT")
        except Exception as e:
            print("Informe: no se pudo poner la imagen de la carta:", e)
    pdf.portada = False

    # ---------- TABLAS ----------
    pdf.add_page()
    pdf.titulo_seccion("Los datos de tu carta" if es else "Your chart data", en_indice=True)

    filas = []
    asc = natal.get("asc", {})
    mc = natal.get("mc", {})
    if asc:
        filas.append(["Ascendente" if es else "Ascendant", asc.get("formatted", ""), "I", ""])
    if mc:
        filas.append(["Medio Cielo" if es else "Midheaven", mc.get("formatted", ""), "X", ""])
    nombres = {
        "sun": ("Sol", "Sun"), "moon": ("Luna", "Moon"), "mercury": ("Mercurio", "Mercury"),
        "venus": ("Venus", "Venus"), "mars": ("Marte", "Mars"), "jupiter": ("Júpiter", "Jupiter"),
        "saturn": ("Saturno", "Saturn"), "uranus": ("Urano", "Uranus"),
        "neptune": ("Neptuno", "Neptune"), "pluto": ("Plutón", "Pluto"),
        "chiron": ("Quirón", "Chiron"), "lilith": ("Lilith", "Lilith"),
        "true_node": ("Nodo Norte", "North Node"), "south_node": ("Nodo Sur", "South Node"),
        "fortuna": ("Rueda de la Fortuna", "Part of Fortune"),
        "infortunio": ("Parte del Infortunio", "Part of Misfortune"),
    }
    planetas = dict(natal.get("planets", {}) or {})
    planetas.update(natal.get("extras", {}) or {})
    for clave, (es_n, en_n) in nombres.items():
        p = planetas.get(clave)
        if not p:
            continue
        dig = ""
        if p.get("dignity"):
            dig = p["dignity"].get("es" if es else "en", "")
        filas.append([es_n if es else en_n, p.get("formatted", ""),
                      str(p.get("house", "")), ("R " if p.get("retrograde") else "") + dig])
    pdf.tabla(["Planeta" if es else "Planet",
               "Posición" if es else "Position",
               "Casa" if es else "House",
               "Estado" if es else "Status"],
              filas, [52, 52, 20, 48])

    casas = natal.get("houses", []) or []
    if casas:
        pdf.titulo_seccion("Casas y regentes" if es else "Houses and rulers")
        filas_c = []
        for h in casas:
            regente = h.get("ruler") or ""
            nom = nombres.get(regente, (regente, regente))[0 if es else 1]
            donde = ""
            if h.get("ruler_house"):
                donde = ("Casa " if es else "House ") + str(h["ruler_house"]) + " (" + str(h.get("ruler_sign", "")) + ")"
            filas_c.append([str(h.get("house_number", "")), h.get("formatted", ""), nom, donde])
        pdf.tabla(["Casa" if es else "House",
                   "Cúspide" if es else "Cusp",
                   "Regente" if es else "Ruler",
                   "Dónde está" if es else "Where it is"],
                  filas_c, [20, 45, 45, 62])

    # ---------- LECTURA DE LA CARTA NATAL ----------
    interpretaciones = [] if solo_gratis else ordenar_interpretaciones(interpretaciones, es)
    if interpretaciones:
        pdf.add_page()
        pdf.titulo_seccion("Tu carta natal, leída" if es else "Your natal chart, read", en_indice=True)
        for item in interpretaciones:
            pdf.subtitulo(item.get("titulo", ""))
            for parrafo in str(item.get("texto", "")).split("\n"):
                if parrafo.strip():
                    pdf.parrafo(parrafo.strip())

    # ---------- SECCIONES DEL NAVEGADOR ----------
    for sec in ([] if solo_gratis else (secciones or [])):
        bloques = sec.get("bloques") or []
        if not bloques:
            continue
        pdf.add_page()
        pdf.titulo_seccion(sec.get("titulo", ""), en_indice=True)
        for bloque in bloques:
            if bloque.get("subtitulo"):
                pdf.subtitulo(bloque["subtitulo"])
            for parrafo in (bloque.get("parrafos") or []):
                # La app puede marcar un renglón como destacado, por
                # ejemplo el que nombra el aspecto entre dos planetas.
                if isinstance(parrafo, dict):
                    linea = str(parrafo.get("v", "")).strip()
                    if not linea:
                        continue
                    tipo = parrafo.get("t")
                    if tipo == "aspecto":
                        pdf.destacado(linea)
                    elif tipo == "rotulo":
                        pdf.subrotulo(linea)
                    elif tipo in ("facilita", "dificulta"):
                        if tipo == "facilita":
                            etiqueta = "Lo que se facilita" if es else "What is facilitated"
                        else:
                            etiqueta = "Lo que se dificulta" if es else "What is challenged"
                        etiqueta = parrafo.get("etiqueta") or etiqueta
                        pdf.recuadro(etiqueta, linea, favorable=(tipo == "facilita"))
                    else:
                        pdf.parrafo(linea)
                    continue
                linea = str(parrafo).strip()
                if not linea:
                    continue
                if _es_etiqueta(linea):
                    pdf.etiqueta(linea)
                else:
                    pdf.parrafo(linea)

    # ---------- CALENDARIO DE DOCE MESES ----------
    # Se arma con los datos, no copiando el texto de la pantalla: en
    # pantalla solo se ve el planeta que la persona tenga señalado, y
    # cada evento queda partido en renglones sueltos.
    if calendario and not solo_gratis:
        hay = [c for c in calendario if c.get("eventos")]
        if hay:
            pdf.add_page()
            pdf.titulo_seccion("Tu calendario · 12 meses" if es else "Your 12-month calendar", en_indice=True)
            pdf.parrafo(
                "Las fechas en que cada planeta lento toca, por aspecto exacto, "
                "un punto de tu carta natal durante los próximos doce meses."
                if es else
                "The dates when each slow planet makes an exact aspect to a point "
                "of your natal chart over the next twelve months.")
            for grupo in hay:
                futuros = [e for e in grupo["eventos"]
                           if (lambda f: f is not None and not _ya_paso(f))(
                               _fecha_evento(e.get("date"), es)[0])]
                if not futuros:
                    continue
                grupo = {"planeta": grupo.get("planeta"), "eventos": futuros}
                pdf.subtitulo(_nombre_planeta(grupo.get("planeta"), es))
                mes_actual = None
                for ev in grupo["eventos"]:
                    fecha, _ = _fecha_evento(ev.get("date"), es)
                    if fecha is None or _ya_paso(fecha):
                        continue   # el calendario mira hacia adelante
                    mes = (fecha.year, fecha.month)
                    if mes != mes_actual:
                        mes_actual = mes
                        nombre_mes = (MESES_ES if es else MESES_EN)[fecha.month - 1]
                        falta = _cuanto_falta(fecha, es)
                        rotulo = f"{nombre_mes} {fecha.year}"
                        if falta:
                            rotulo += f" · {falta}"
                        pdf.rotulo_mes(rotulo)
                    aspecto = (ev.get("aspect_es" if es else "aspect_en") or "").lower()
                    natal = _nombre_planeta(ev.get("natal_planet"), es)
                    if es:
                        pdf.renglon(f"**{fecha.day}** · {aspecto} a tu {natal}")
                    else:
                        pdf.renglon(f"**{fecha.day}** · {aspecto} to your {natal}")

    # ---------- EDAD ZODIACAL ----------
    if edad_texto:
        pdf.add_page()
        pdf.titulo_seccion("Tu edad zodiacal" if es else "Your zodiacal age", en_indice=True)
        pdf.subtitulo(f"{edad_texto.get('rango', '')} · {edad_texto.get('titulo', '')}")
        for etiqueta, clave in (("Qué pasa" if es else "What happens", "pasa"),
                                ("El spoiler ácido" if es else "The blunt truth", "spoiler"),
                                ("Los retos" if es else "The challenges", "retos"),
                                ("Qué entender y trabajar" if es else "What to work on", "trabajar")):
            valor = edad_texto.get(clave)
            if not valor:
                continue
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*SUAVE)
            pdf.cell(0, 5, _limpiar(etiqueta).upper(), new_x="LMARGIN", new_y="NEXT")
            if isinstance(valor, list):
                for v in valor:
                    pdf.parrafo("· " + str(v))
            else:
                pdf.parrafo(valor, cursiva=(clave == "spoiler"))

    # ---------- CIERRE ----------
    if solo_gratis:
        pdf.add_page()
        pdf.titulo_seccion("Tu carta completa" if es else "Your complete chart")
        pdf.ln(2)
        pdf.set_font(pdf.display, "B", 25)
        pdf.set_text_color(*TINTA)
        pdf.multi_cell(0, 11, _limpiar(
            "Si quieres conocer tu carta natal completa"
            if es else
            "If you want to know your complete natal chart"),
            new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.parrafo(
            "Lo que tienes en estas páginas es el mapa: dónde estaba cada planeta "
            "el día que naciste, en qué casa, con qué aspectos. El informe completo "
            "es la lectura de ese mapa, escrita por mí, texto por texto."
            if es else
            "What you have in these pages is the map: where each planet stood the "
            "day you were born, in which house, with which aspects. The complete "
            "report is the reading of that map, written by me, text by text.")
        pdf.ln(3)
        for linea in ((
            "**Tu carta natal, leída.** Cada planeta en su signo y su casa, los nodos, "
            "la Fortuna y los aspectos entre tus planetas.",
            "**Los tránsitos de los planetas lentos.** Júpiter, Saturno, Urano, Neptuno, "
            "Plutón, Quirón y Lilith, uno por uno, sobre tu carta.",
            "**Tu calendario de doce meses.** Las fechas en que cada planeta lento toca "
            "un punto de tu carta.",
            "**Tus áreas de vida activadas.** Qué se está moviendo hoy y dónde.",
            "**Las 23 edades zodiacales.** Las que ya viviste y las que vienen.",
        ) if es else (
            "**Your natal chart, read.** Each planet in its sign and house, the nodes, "
            "the Part of Fortune and the aspects between your planets.",
            "**The transits of the slow planets.** Jupiter, Saturn, Uranus, Neptune, "
            "Pluto, Chiron and Lilith, one by one, over your chart.",
            "**Your twelve-month calendar.** The dates when each slow planet touches "
            "a point of your chart.",
            "**Your activated life areas.** What is moving today, and where.",
            "**The 23 zodiacal ages.** The ones you have lived and the ones to come.",
        )):
            pdf.parrafo("· " + linea)
        pdf.ln(5)
        pdf.pastilla(
            "Quiero mi carta natal completa  »" if es else
            "I want my complete natal chart  »",
            DIRECCION)
        pdf.ln(3)
        pdf.enlace("carta.ricardopuerta.com", DIRECCION)
        pdf.ln(6)
        pdf.set_font(pdf.sans, "", 8.5)
        pdf.set_text_color(*SUAVE)
        pdf.multi_cell(0, 4.6, _limpiar(
            "Ricardo Puerta Isaza · arquitecto & astrólogo\n"
            "Cálculos con Swiss Ephemeris, validados contra Solar Fire v9.1.0."
            if es else
            "Ricardo Puerta Isaza · architect & astrologer\n"
            "Calculations with Swiss Ephemeris, validated against Solar Fire v9.1.0."),
            new_x="LMARGIN", new_y="NEXT")
        salida = pdf.output()
        return bytes(salida), pdf.indice

    pdf.add_page()
    pdf.titulo_seccion("Sobre este informe" if es else "About this report", en_indice=True)
    pdf.parrafo(
        "Los textos de este informe los escribí yo, uno por uno. El cálculo se hace "
        "con Swiss Ephemeris y está validado contra Solar Fire v9.1.0, con sistema "
        "de casas Plácidus, zodíaco tropical y posiciones geocéntricas. La "
        "interpretación es mía y espero que te ayude mucho."
        if es else
        "The texts in this report were written by me, one by one. The calculation uses "
        "Swiss Ephemeris and is validated against Solar Fire v9.1.0, with Placidus houses, "
        "the tropical zodiac and geocentric positions. The interpretation is mine, and I "
        "hope it helps you.")
    pdf.ln(4)
    pdf.parrafo("Ricardo Puerta Isaza · " + ("arquitecto & astrólogo" if es else "architect & astrologer"))
    pdf.parrafo("ricardopuerta.com · carta.ricardopuerta.com")

    salida = pdf.output()
    return bytes(salida), pdf.indice

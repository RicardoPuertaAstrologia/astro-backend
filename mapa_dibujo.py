# -*- coding: utf-8 -*-
"""Dibuja los mapas dentro del PDF, con líneas de verdad y no con una foto.

Hay dos mapas distintos y los dos salen de acá:

  · EL MAPA GRANDE, con los catorce cuerpos y sus cuatro líneas. Va una
    sola vez, al comienzo, en una hoja apaisada. Es la lámina completa.

  · EL MAPA DE CADA SEGMENTO, más pequeño, al comienzo de cada capítulo.
    Lleva SÓLO lo de ese segmento: las cuatro líneas del planeta que
    manda, las líneas de los socios que efectivamente cruzan, un punto en
    cada cruce y un punto en cada ciudad activa, con su nombre. Es el que
    responde «¿por dónde me pasa mi éxito profesional?» de un vistazo.

POR QUÉ VECTORIAL Y NO UNA IMAGEN

El borrador se hacía en SVG y se convertía a PNG con cairosvg, que
necesita la librería de sistema libcairo. Dibujado directo sobre el PDF
no hace falta ninguna librería nueva —fpdf2 ya está—, el archivo pesa una
décima parte, y el mapa queda en vectores: se amplía sin pixelarse y se
imprime nítido a cualquier tamaño.

LOS RÓTULOS VAN CON NOMBRE, NO CON GLIFO

Ninguna de las dos tipografías de la marca —Cormorant e Inter— trae los
símbolos de los planetas; lo comprobé sobre los .ttf, y faltan los
catorce en las dos. El informe de la carta natal ya resuelve esto igual:
quita los símbolos y deja siempre el nombre.

LA PROYECCIÓN

Equirectangular: la longitud va directo a la x y la latitud directo a la
y. Es la misma que usa Solar Maps, y la que hace que las líneas del Medio
Cielo salgan rectas y verticales.
"""
import io, json, os

AQUI = os.path.dirname(os.path.abspath(__file__))

LAT_MIN, LAT_MAX = -58.0, 76.0

# ── colores ──
# Las catorce líneas. Los cinco más claros van oscurecidos respecto al
# primer borrador: el oro del Sol, el verde de Mercurio, el rosa de
# Venus, el turquesa de Urano y el ocre de los nodos no alcanzaban 3:1
# contra su funda. Ahora el más flojo es el Sol, con 3,85:1.
COLOR = {
    'sol': (168, 122, 14), 'luna': (91, 127, 153), 'mercurio': (85, 120, 58),
    'venus': (164, 79, 114), 'marte': (184, 51, 42), 'jupiter': (125, 90, 166),
    'saturno': (78, 90, 102), 'urano': (21, 128, 127), 'neptuno': (61, 98, 160),
    'pluton': (125, 74, 46), 'quiron': (122, 108, 72), 'lilith': (93, 74, 107),
    'nodo_n': (138, 108, 51), 'nodo_s': (138, 108, 51),
}
MAR = (148, 179, 200)
TIERRA = (243, 238, 226)
COSTA = (81, 97, 109)
RETICULA = (123, 150, 169)
ROTULO = (73, 88, 95)
FUNDA = (255, 255, 255)
MARCO = (81, 97, 109)
TINTA = (21, 24, 29)
ORO = (150, 118, 47)

CORTO = {
    'sol': 'Sol', 'luna': 'Lun', 'mercurio': 'Mer', 'venus': 'Ven',
    'marte': 'Mar', 'jupiter': 'Júp', 'saturno': 'Sat', 'urano': 'Ura',
    'neptuno': 'Nep', 'pluton': 'Plu', 'quiron': 'Qui', 'lilith': 'Lil',
    'nodo_n': 'N.N', 'nodo_s': 'N.S',
}
CORTO_EN = {
    'sol': 'Sun', 'luna': 'Moon', 'mercurio': 'Mer', 'venus': 'Ven',
    'marte': 'Mars', 'jupiter': 'Jup', 'saturno': 'Sat', 'urano': 'Ura',
    'neptuno': 'Nep', 'pluton': 'Plu', 'quiron': 'Chi', 'lilith': 'Lil',
    'nodo_n': 'N.N', 'nodo_s': 'N.S',
}

ORDEN = ['sol', 'luna', 'mercurio', 'venus', 'marte', 'jupiter', 'saturno',
         'urano', 'neptuno', 'pluton', 'quiron', 'lilith', 'nodo_n', 'nodo_s']

NOMBRE = {
    'sol': 'Sol', 'luna': 'Luna', 'mercurio': 'Mercurio', 'venus': 'Venus',
    'marte': 'Marte', 'jupiter': 'Júpiter', 'saturno': 'Saturno',
    'urano': 'Urano', 'neptuno': 'Neptuno', 'pluton': 'Plutón',
    'quiron': 'Quirón', 'lilith': 'Lilith',
    'nodo_n': 'Nodo Norte', 'nodo_s': 'Nodo Sur',
}
NOMBRE_EN = {
    'sol': 'Sun', 'luna': 'Moon', 'mercurio': 'Mercury', 'venus': 'Venus',
    'marte': 'Mars', 'jupiter': 'Jupiter', 'saturno': 'Saturn',
    'urano': 'Uranus', 'neptuno': 'Neptune', 'pluton': 'Pluto',
    'quiron': 'Chiron', 'lilith': 'Lilith',
    'nodo_n': 'North Node', 'nodo_s': 'South Node',
}

ANG_CORTO = {'es': {'mc': 'MC', 'ic': 'IC', 'asc': 'Asc', 'desc': 'Dsc'},
             'en': {'mc': 'MC', 'ic': 'IC', 'asc': 'Asc', 'desc': 'Dsc'}}

ALTO_FILA = 3.4
# La separación mínima entre dos rótulos de la misma fila. Con 8,6 mm cabe
# el más largo —«Moon MC»— sin tocar al vecino.
SEP = 8.6

_MUNDO = None


def mundo():
    """Los contornos de los continentes, cargados una sola vez."""
    global _MUNDO
    if _MUNDO is None:
        _MUNDO = json.load(io.open(os.path.join(AQUI, 'mapa_mundo.json'),
                                   encoding='utf-8'))
    return _MUNDO


class Lienzo:
    """Convierte longitud y latitud en milímetros sobre la hoja."""

    def __init__(self, x, y, ancho):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = ancho * (LAT_MAX - LAT_MIN) / 360.0

    def px(self, lon):
        return self.x + (lon + 180.0) / 360.0 * self.ancho

    def py(self, lat):
        return self.y + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * self.alto


def _mezclar(color, cuanto):
    """Aclara un color hacia el blanco. cuanto=0 lo deja igual, 1 lo borra."""
    return tuple(int(round(c + (255 - c) * cuanto)) for c in color)


def _recortar(lz, tramo):
    return [(lz.px(lo), lz.py(la)) for lo, la in tramo
            if LAT_MIN - 1 <= la <= LAT_MAX + 1]


def _acomodar(items, sep):
    """Reparte los rótulos en filas para que no se pisen."""
    filas, puestos = [], []
    for x, dato in sorted(items, key=lambda t: t[0]):
        for i, fila in enumerate(filas):
            if x - fila[-1] >= sep:
                fila.append(x)
                puestos.append((x, i, dato))
                break
        else:
            filas.append([x])
            puestos.append((x, len(filas) - 1, dato))
    return puestos, len(filas)


# ══════════════════════════════════════════════════════════ LA BASE
def _base(pdf, lz, reticula=True):
    x0, y0, w, h = lz.x, lz.y, lz.ancho, lz.alto
    pdf.set_fill_color(*MAR)
    pdf.rect(x0, y0, w, h, style='F')
    pdf.set_fill_color(*TIERRA)
    pdf.set_draw_color(*COSTA)
    pdf.set_line_width(0.1)
    for anillo in mundo():
        pts = [(lz.px(lo), lz.py(la)) for lo, la in anillo]
        if len(pts) > 2:
            pdf.polygon(pts, style='DF')
    if reticula:
        pdf.set_draw_color(*RETICULA)
        pdf.set_line_width(0.07)
        pdf.set_dash_pattern(dash=1.0, gap=1.4)
        for lon in range(-150, 180, 30):
            pdf.line(lz.px(lon), y0, lz.px(lon), y0 + h)
        for lat in (-45, -30, -15, 15, 30, 45, 60):
            pdf.line(x0, lz.py(lat), x0 + w, lz.py(lat))
        pdf.set_dash_pattern()
        pdf.set_line_width(0.14)
        pdf.line(x0, lz.py(0), x0 + w, lz.py(0))


# Los tres niveles con los que se pinta una línea. Es lo mismo que hacía la
# maqueta cuando se tocaba una pastilla: la carta entera sigue ahí, pero lo
# del segmento se destaca y el resto se apaga.
FUERTE, SOCIA, FONDO = 2, 1, 0
_ACLARADO = {FUERTE: 0.0, SOCIA: 0.40, FONDO: 0.78}
_GRUESO = {FUERTE: 1.0, SOCIA: 0.62, FONDO: 0.42}


def _trazos_de(cuerpos, lz, lista):
    """Convierte (cuerpo, ángulo, nivel) en caminos listos para pintar."""
    fuera = []
    for cu, ang, nivel in lista:
        d = cuerpos.get(cu)
        if not d:
            continue
        nivel = int(nivel)
        col = _mezclar(COLOR[cu], _ACLARADO[nivel])
        punteada = ang in ('ic', 'desc')
        if ang in ('mc', 'ic'):
            fuera.append(([(lz.px(d[ang]), lz.y),
                           (lz.px(d[ang]), lz.y + lz.alto)], col, punteada, nivel))
        else:
            for tramo in d[ang]:
                pts = _recortar(lz, tramo)
                if len(pts) > 1:
                    fuera.append((pts, col, punteada, nivel))
    # El fondo primero, para que lo destacado quede encima de todo.
    fuera.sort(key=lambda t: t[3])
    return fuera


def _pintar_lineas(pdf, trazos, grueso=0.45, funda=1.15):
    """Dos pasadas: primero TODAS las fundas blancas y después todos los
    colores. Si se hiciera línea por línea, la funda de la siguiente
    taparía el color de la anterior.

    La funda lleva EL MISMO punteado que su línea: si fuera continua, una
    línea punteada se vería como una raya blanca con guiones de color
    encima, y se perdería la diferencia entre el MC y el IC."""
    for pts, _col, punteada, nivel in trazos:
        if nivel != FUERTE:
            continue          # sólo lo destacado lleva funda blanca
        pdf.set_draw_color(*FUNDA)
        pdf.set_line_width(funda)
        if punteada:
            pdf.set_dash_pattern(dash=1.6, gap=1.1)
        pdf.polyline(pts)
        pdf.set_dash_pattern()
    for pts, col, punteada, nivel in trazos:
        pdf.set_draw_color(*col)
        pdf.set_line_width(grueso * _GRUESO[nivel])
        if punteada:
            pdf.set_dash_pattern(dash=1.6, gap=1.1)
        pdf.polyline(pts)
        pdf.set_dash_pattern()


def _latitudes(pdf, lz, cuales=(60, 30, 0, -30), tam=4.6):
    pdf.set_font(pdf.sans, '', tam)
    pdf.set_text_color(*ROTULO)
    for lat in cuales:
        pdf.set_xy(lz.x - 7.4, lz.py(lat) - 1.5)
        pdf.cell(6.6, 3.0, ('%d' % abs(lat)) + ('°' if lat == 0 else
                 ('°N' if lat > 0 else '°S')), align='R')


def _marco(pdf, lz):
    pdf.set_draw_color(*MARCO)
    pdf.set_line_width(0.22)
    pdf.rect(lz.x, lz.y, lz.ancho, lz.alto, style='D')


# ══════════════════════════════════════════════ EL MAPA GRANDE
def _colocar(cuerpos, lz, lista):
    arriba, abajo = [], []
    for cu, ang, nivel in lista:
        d = cuerpos.get(cu)
        # Las líneas de fondo NO llevan rótulo: son las cincuenta y seis de
        # la carta entera, y rotularlas taparía el mapa. Están para ubicar.
        if not d or int(nivel) == FONDO:
            continue
        if ang in ('mc', 'ic'):
            arriba.append((lz.px(d[ang]), (cu, ang)))
        else:
            for tramo in d[ang]:
                pts = [(lo, la) for lo, la in tramo if LAT_MIN <= la <= LAT_MAX]
                if len(pts) > 1:
                    abajo.append((lz.px(min(pts, key=lambda t: t[1])[0]), (cu, ang)))
                    break
    return (_acomodar(arriba, SEP), _acomodar(abajo, SEP))


def medir_rotulos(cuerpos, lz, lista=None):
    """Cuánto miden las dos bandas de rótulos, en milímetros. Se calcula sin
    dibujar nada, para poder centrar el mapa antes de pintarlo."""
    lista = lista or [(cu, a, FUERTE) for cu in ORDEN
                      for a in ('mc', 'ic', 'asc', 'desc')]
    (_a, fa), (_b, fb) = _colocar(cuerpos, lz, lista)
    return (fa + 1) * ALTO_FILA + 1.4, (fb + 1) * ALTO_FILA + 1.4


def _rotulos(pdf, cuerpos, lz, lista, corto, lang):
    (puestos_a, _fa), (puestos_b, _fb) = _colocar(cuerpos, lz, lista)
    ac = ANG_CORTO['en' if lang == 'en' else 'es']

    # Primero TODAS las guías y después TODOS los rótulos: si se hiciera uno
    # por uno, la guía de un rótulo de la tercera fila atravesaría los
    # rótulos de la primera y la segunda, que ya estarían pintados.
    pdf.set_line_width(0.25)
    for x, fila, (cu, _ang) in puestos_a:
        pdf.set_draw_color(*COLOR[cu])
        pdf.line(x, lz.y - 1.4 - (fila + 1) * ALTO_FILA + 0.6, x, lz.y)
    for x, fila, (cu, _ang) in puestos_b:
        pdf.set_draw_color(*COLOR[cu])
        pdf.line(x, lz.y + lz.alto, x,
                 lz.y + lz.alto + 1.4 + (fila + 1) * ALTO_FILA - 0.6)

    # Cada rótulo sobre una plaquita de papel, para que la guía que pasa por
    # detrás no le atraviese las letras.
    pdf.set_font(pdf.sans, '', 5)
    pdf.set_fill_color(255, 255, 255)
    for puestos, encima in ((puestos_a, True), (puestos_b, False)):
        for x, fila, (cu, ang) in puestos:
            y = (lz.y - 1.4 - (fila + 1) * ALTO_FILA) if encima else \
                (lz.y + lz.alto + 1.4 + fila * ALTO_FILA)
            texto = '%s %s' % (corto[cu], ac[ang])
            ancho = pdf.get_string_width(texto) + 1.0
            pdf.rect(x - ancho / 2, y + 0.25, ancho, ALTO_FILA - 0.5, style='F')
            pdf.set_text_color(*COLOR[cu])
            pdf.set_xy(x - SEP / 2, y)
            pdf.cell(SEP, ALTO_FILA, texto, align='C')


def dibujar(pdf, cuerpos, lz, lang='es'):
    """El mapa grande: los catorce cuerpos y sus cuatro líneas."""
    corto = CORTO if lang == 'es' else CORTO_EN
    lista = [(cu, a, FUERTE) for cu in ORDEN for a in ('mc', 'ic', 'asc', 'desc')]
    with pdf.rect_clip(lz.x, lz.y, lz.ancho, lz.alto):
        _base(pdf, lz)
        _pintar_lineas(pdf, _trazos_de(cuerpos, lz, lista))
    _marco(pdf, lz)
    _latitudes(pdf, lz, (60, 45, 30, 15, 0, -15, -30, -45), tam=5)
    _rotulos(pdf, cuerpos, lz, lista, corto, lang)


def leyenda(pdf, x, y, ancho, lang='es'):
    """Los catorce cuerpos con su color, en dos filas de siete."""
    nombres = NOMBRE if lang == 'es' else NOMBRE_EN
    por_fila = 7
    paso = ancho / por_fila
    pdf.set_font(pdf.sans, '', 6)
    for i, cu in enumerate(ORDEN):
        cx = x + (i % por_fila) * paso
        cy = y + (i // por_fila) * 5.2
        pdf.set_draw_color(*COLOR[cu])
        pdf.set_line_width(0.9)
        pdf.line(cx, cy + 1.7, cx + 5.0, cy + 1.7)
        pdf.set_text_color(*ROTULO)
        pdf.set_xy(cx + 6.2, cy)
        pdf.cell(paso - 6.4, 3.5, nombres[cu])
    return 10.4


# ══════════════════════════════════════════ EL MAPA DE UN SEGMENTO
def lineas_del_segmento(cuerpos, seg):
    """Las líneas de un mapa de segmento, cada una con su nivel.

    Igual que en la maqueta: la carta entera se sigue viendo, pero sólo lo
    de este segmento está destacado.

      FUERTE  las cuatro líneas del planeta o planetas que mandan
      SOCIA   las líneas de los socios QUE DE VERDAD CRUZAN, para que el
              cruce se entienda. Las otras del socio no, porque no se
              mencionan en ninguna parte del capítulo
      FONDO   todo lo demás de la carta, muy apagado: ubica, no estorba
    """
    lista = [(cu, a, FUERTE) for cu in seg['principales']
             for a in ('mc', 'ic', 'asc', 'desc')]
    puestas = {(cu, a) for cu, a, _n in lista}
    for cu, a in seg['socias']:
        if (cu, a) not in puestas:
            lista.append((cu, a, SOCIA))
            puestas.add((cu, a))
    for cu in ORDEN:
        for a in ('mc', 'ic', 'asc', 'desc'):
            if (cu, a) not in puestas:
                lista.append((cu, a, FONDO))
    return lista


def _punto_cruce(pdf, x, y):
    """Un rombo oscuro con borde blanco: se ve sobre el mar, sobre la tierra
    y encima de cualquier línea."""
    r = 1.15
    rombo = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(0.75)
    pdf.polygon(rombo, style='DF')
    pdf.set_fill_color(*TINTA)
    pdf.polygon(rombo, style='F')


def _punto_ciudad(pdf, x, y):
    pdf.set_fill_color(255, 255, 255)
    pdf.circle(x=x - 1.05, y=y - 1.05, radius=1.05, style='F')
    pdf.set_fill_color(*ORO)
    pdf.circle(x=x - 0.62, y=y - 0.62, radius=0.62, style='F')


def dibujar_segmento(pdf, cuerpos, lz, seg, lang='es'):
    """El mapa de un capítulo: sólo sus líneas, sus cruces y sus ciudades."""
    corto = CORTO if lang == 'es' else CORTO_EN

    lista = lineas_del_segmento(cuerpos, seg)

    with pdf.rect_clip(lz.x, lz.y, lz.ancho, lz.alto):
        _base(pdf, lz)
        _pintar_lineas(pdf, _trazos_de(cuerpos, lz, lista),
                       grueso=0.5, funda=1.25)
        for p in seg['cruces']:
            _punto_cruce(pdf, lz.px(p['lon']), lz.py(p['lat']))
        for fila in seg['ciudades']:
            c = fila['c']
            _punto_ciudad(pdf, lz.px(c['lo']), lz.py(c['la']))

    _marco(pdf, lz)
    _latitudes(pdf, lz)
    _rotulos(pdf, cuerpos, lz, lista, corto, lang)
    _nombres_ciudades(pdf, lz, seg, lang)


def _nombres_ciudades(pdf, lz, seg, lang):
    """El nombre de cada ciudad al lado de su punto, esquivando a los demás.

    Se ponen de arriba abajo y cada uno busca el primer sitio libre: a la
    derecha del punto, a la izquierda, o un poco más abajo. Si no cabe en
    ninguno, se deja sin nombre: el punto sigue ahí y la ciudad está en la
    lista de abajo, así que no se pierde nada y el mapa no se ensucia."""
    pdf.set_font(pdf.sans, 'B', 5)
    ocupado = []

    def libre(x1, y1, x2, y2):
        for a, b, c, d in ocupado:
            if x1 < c and a < x2 and y1 < d and b < y2:
                return False
        # dentro del marco, que si no el rótulo se sale de la lámina
        return (x1 >= lz.x + 0.5 and x2 <= lz.x + lz.ancho - 0.5
                and y1 >= lz.y + 0.5 and y2 <= lz.y + lz.alto - 0.5)

    filas = sorted(seg['ciudades'], key=lambda f: f['c']['la'], reverse=True)
    for fila in filas:
        c = fila['c']
        nombre = c['en'] if lang == 'en' else c['n']
        x, y = lz.px(c['lo']), lz.py(c['la'])
        w = pdf.get_string_width(nombre) + 0.8
        for dx, dy, al in ((1.9, -1.5, 'L'), (-1.9 - w, -1.5, 'L'),
                           (1.9, 0.9, 'L'), (-1.9 - w, 0.9, 'L'),
                           (-w / 2, -5.0, 'L'), (-w / 2, 2.6, 'L')):
            caja = (x + dx - 0.4, y + dy - 0.2, x + dx + w + 0.4, y + dy + 3.2)
            if libre(*caja):
                ocupado.append(caja)
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(caja[0], caja[1], caja[2] - caja[0], caja[3] - caja[1],
                         style='F')
                pdf.set_text_color(*TINTA)
                pdf.set_xy(x + dx, y + dy)
                pdf.cell(w, 3.0, nombre, align=al)
                break


def leyenda_segmento(pdf, x, y, ancho, seg, lang='es'):
    """Debajo del mapa del segmento: qué significa cada cosa que se ve."""
    nombres = NOMBRE if lang == 'es' else NOMBRE_EN
    es = (lang != 'en')
    pdf.set_font(pdf.sans, '', 5.6)
    cx, cy = x, y

    def trozo(dibuja, texto, ancho_texto):
        nonlocal cx, cy
        if cx + ancho_texto + 7.5 > x + ancho:
            cx, cy = x, cy + 4.6
        dibuja(cx, cy + 1.6)
        pdf.set_text_color(*ROTULO)
        pdf.set_xy(cx + 6.4, cy - 0.3)
        pdf.cell(ancho_texto, 3.4, texto)
        cx += ancho_texto + 8.4

    for cu in seg['principales']:
        def pinta(px, py, cu=cu):
            pdf.set_draw_color(*COLOR[cu])
            pdf.set_line_width(0.9)
            pdf.line(px, py, px + 5.0, py)
        t = nombres[cu]
        trozo(pinta, t, pdf.get_string_width(t) + 0.5)

    vistos = []
    for cu, _ang in seg['socias']:
        if cu in vistos:
            continue
        vistos.append(cu)

        def pinta(px, py, cu=cu):
            pdf.set_draw_color(*_mezclar(COLOR[cu], 0.42))
            pdf.set_line_width(0.6)
            pdf.line(px, py, px + 5.0, py)
        t = nombres[cu]
        trozo(pinta, t, pdf.get_string_width(t) + 0.5)

    if seg['cruces']:
        t = 'cruce' if es else 'crossing'
        trozo(lambda px, py: _punto_cruce(pdf, px + 2.5, py), t,
              pdf.get_string_width(t) + 0.5)
    if seg['ciudades']:
        t = 'ciudad activa' if es else 'active city'
        trozo(lambda px, py: _punto_ciudad(pdf, px + 2.5, py), t,
              pdf.get_string_width(t) + 0.5)

    return cy - y + 5.0

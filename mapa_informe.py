# -*- coding: utf-8 -*-
"""
EL INFORME DEL MAPA EN PDF — Ricardo Puerta · Astrología

Arma «Tu mapa natal en el mapa mundial» con las mismas piezas del informe
de la carta natal: misma clase, mismos colores, misma portada, mismos
títulos y rótulos. Lo propio de este informe son el mapa, los ocho
segmentos, las ciudades y la nota de cierre.

Se llama con los datos de nacimiento y el día juliano que ya calculó el
servidor —el mismo que usa la carta natal, para que los dos informes
hablen del mismo instante— y devuelve los bytes del PDF.
"""
import os, re

from fpdf import FPDF

import mapa_datos as MD
import mapa_dibujo as MDI
import mapa_textos as TX

AQUI = os.path.dirname(os.path.abspath(__file__))

# ── los mismos colores de informe.py ──
TINTA = (21, 24, 29)          # --tinta  #15181d
SUAVE = (90, 95, 103)         # --tinta-suave #5a5f67
ORO = (150, 118, 47)          # --oro-tinta, el dorado sobre papel
ORO_CLARO = (201, 169, 97)    # --oro, el dorado sobre fondo oscuro
NOCHE = (11, 14, 18)          # --noche
PAPEL = (247, 245, 240)       # --papel
LINEA = (226, 222, 212)       # --linea
AZUL = (74, 143, 184)         # --azul-hondo

ORDEN_ANG = TX.ORDEN_ANG


def _buscar(nombre, *carpetas):
    """Busca un archivo en varias carpetas y al lado del código. Es la misma
    función de informe.py, para que las tipografías y el logotipo se
    encuentren exactamente igual que en el informe de la carta natal: no hay
    que volver a subirlos, ya están."""
    for carpeta in list(carpetas) + [""]:
        ruta = os.path.join(AQUI, carpeta, nombre) if carpeta else os.path.join(AQUI, nombre)
        if os.path.exists(ruta):
            return ruta
    return os.path.join(AQUI, nombre)


class MapaPDF(FPDF):
    """La misma clase del informe de la carta natal, con las mismas medidas."""

    def __init__(self, titulo_pie=''):
        super().__init__(format='Letter', unit='mm')
        self.marca = self._fuentes()
        self.display = 'Cormorant' if self.marca else 'Times'
        self.sans = 'Inter' if self.marca else 'Helvetica'
        self.paginas_sin_numero = 2
        self.titulo_pie = self.limpiar(titulo_pie)
        self.set_auto_page_break(auto=True, margin=22)
        self.set_margins(22, 22, 22)
        self.indice = []

    def _fuentes(self):
        try:
            self.add_font('Cormorant', '', _buscar('Cormorant-Regular.ttf', 'fuentes'))
            self.add_font('Cormorant', 'B', _buscar('Cormorant-SemiBold.ttf', 'fuentes'))
            self.add_font('Inter', '', _buscar('Inter-Regular.ttf', 'fuentes'))
            self.add_font('Inter', 'B', _buscar('Inter-SemiBold.ttf', 'fuentes'))
            return True
        except Exception as e:
            print('Mapa: sin tipografía de marca:', e)
            return False

    def limpiar(self, texto):
        """Las comillas y las rayas tipográficas se cambian por las simples.

        Si por lo que sea no cargaron las tipografías de la marca, se cae a
        Times y Helvetica, que sólo tienen los primeros 256 caracteres: en
        ese caso se quita todo lo demás, para que no salga basura."""
        if texto is None:
            return ''
        t = str(texto)
        for a, b in {'—': '-', '–': '-', '―': '-', '“': '"', '”': '"', '„': '"',
                     '‘': "'", '’': "'", '…': '...', '′': "'", '″': '"',
                     ' ': ' ', '​': ''}.items():
            t = t.replace(a, b)
        for c in '☉☽☾☿♀♂♃♄♅♆♇⚷☊☋⚸⊕⊗':
            t = t.replace(c, ' ')
        if not self.marca:
            t = ''.join(c for c in t if c in '\n\t' or ord(c) < 256)
        return re.sub(r'[ \t]{2,}', ' ', t)

    def footer(self):
        if self.page_no() <= self.paginas_sin_numero:
            return
        self.set_y(-16)
        self.set_font(self.sans, '', 7)
        self.set_text_color(*SUAVE)
        self.cell(0, 4, self.titulo_pie, align='L')
        self.cell(0, 4, str(self.page_no() - self.paginas_sin_numero), align='R')

    # ── las piezas, iguales a las del informe de la carta natal ──
    def titulo_seccion(self, texto, en_indice=False):
        if en_indice:
            self.indice.append((texto, self.page_no() - self.paginas_sin_numero))
        self.ln(4)
        self.set_font(self.sans, 'B', 8)
        self.set_text_color(*ORO)
        self.cell(0, 5, self.limpiar(texto).upper(), new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*LINEA)
        y = self.get_y() + 1
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    def subtitulo(self, texto):
        if self.get_y() > self.h - 48:
            self.add_page()
        self.ln(6)
        self.set_font(self.display, 'B', 19)
        self.set_text_color(*TINTA)
        self.multi_cell(0, 8, self.limpiar(texto), new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*LINEA)
        y = self.get_y() + 1.5
        self.line(self.l_margin, y, self.l_margin + 26, y)
        self.ln(4.5)

    def subrotulo(self, texto):
        if self.get_y() > self.h - 34:
            self.add_page()
        self.ln(3.5)
        self.set_font(self.sans, 'B', 7.5)
        self.set_text_color(*ORO)
        self.set_char_spacing(1.1)
        self.multi_cell(0, 4.5, self.limpiar(texto).upper(), new_x='LMARGIN', new_y='NEXT')
        self.set_char_spacing(0)
        self.set_text_color(*TINTA)
        self.ln(1.5)

    def parrafo(self, texto, cursiva=False):
        self.set_font('Times', 'I' if cursiva else '', 11)
        self.set_text_color(*TINTA)
        limpio = self.limpiar(texto)
        limpio = re.sub(r'(?<!\*)\*([^*\n]{1,300})\*(?!\*)', r'__\1__', limpio)
        self.multi_cell(0, 5.4, limpio, markdown=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def destacado(self, texto):
        if self.get_y() > self.h - 34:
            self.add_page()
        self.ln(2)
        self.set_font('Times', 'B', 11.5)
        self.set_text_color(*ORO)
        self.multi_cell(0, 5.4, self.limpiar(texto), new_x='LMARGIN', new_y='NEXT')
        self.set_text_color(*TINTA)
        self.ln(0.5)

    def pastilla(self, texto, url):
        limpio = self.limpiar(texto)
        self.set_font(self.sans, 'B', 11)
        ancho = self.get_string_width(limpio) + 24
        alto = 13.5
        if self.get_y() + alto > self.h - self.b_margin:
            self.add_page()
        x, y = self.l_margin, self.get_y()
        self.set_fill_color(*NOCHE)
        self.rect(x, y, ancho, alto, style='F', round_corners=True, corner_radius=6.5)
        self.set_text_color(*ORO_CLARO)
        self.set_xy(x, y)
        self.cell(ancho, alto, limpio, align='C')
        self.link(x, y, ancho, alto, url)
        self.set_xy(self.l_margin, y + alto)
        self.set_text_color(*TINTA)

    def enlace(self, texto, url):
        limpio = self.limpiar(texto)
        self.set_font(self.sans, 'B', 9)
        self.set_text_color(*ORO)
        x, y = self.l_margin, self.get_y()
        ancho = self.get_string_width(limpio)
        self.cell(0, 6, limpio, new_x='LMARGIN', new_y='NEXT')
        self.link(x, y, ancho, 6, url)
        self.set_text_color(*TINTA)


# ══════════════════════════════════════════════════════════ LA FICHA
def _ficha(nac, zona, lang):
    """Las dos líneas de datos de nacimiento que van en la portada."""
    meses = TX.MESES['en' if lang == 'en' else 'es']
    try:
        mes = meses[int(nac.get('month', 1)) - 1]
    except Exception:
        mes = str(nac.get('month', ''))
    dia, anio = nac.get('day', ''), nac.get('year', '')
    hora = '%02d:%02d' % (int(nac.get('hour', 0)), int(nac.get('minute', 0)))
    if lang == 'en':
        primera = '%s %s, %s, %s' % (mes, dia, anio, hora)
    else:
        primera = '%s de %s de %s, %s' % (dia, mes, anio, hora)

    ciudad = (nac.get('city_name') or '').strip()
    # De «Africa/Johannesburg (UTC+2.0)» se saca «UTC+2».
    m = re.search(r'UTC([+-]?\d+(?:\.\d+)?)', str(zona or ''))
    desfase = ''
    if m:
        v = float(m.group(1))
        desfase = 'UTC%+g' % v if v == int(v) else 'UTC%+.1f' % v
    segunda = ' · '.join([p for p in (ciudad, desfase) if p])
    return primera, segunda


# ══════════════════════════════════════════════════════════ PORTADA
def portada(pdf, nombre, ficha, lang):
    F = TX.FIJO[lang]
    pdf.add_page()
    pdf.set_auto_page_break(False)
    W = pdf.w
    alto = 88

    pdf.set_fill_color(*NOCHE)
    pdf.rect(0, 0, W, alto, style='F')
    logo = _buscar('logo-blanco.png', 'assets', 'img')
    if os.path.exists(logo):
        pdf.image(logo, x=(W - 46) / 2, y=15, w=46)
    pdf.set_y(69)
    pdf.set_font(pdf.sans, '', 7.5)
    pdf.set_text_color(*ORO_CLARO)
    pdf.set_char_spacing(2.2)
    pdf.cell(0, 5, 'RICARDOPUERTA.COM', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_char_spacing(0)

    pdf.set_y(alto + 22)
    pdf.set_font(pdf.sans, 'B', 7.5)
    pdf.set_text_color(*ORO)
    pdf.set_char_spacing(2.4)
    pdf.cell(0, 5, F['rotulo_portada'], align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_char_spacing(0)

    titular = pdf.limpiar(nombre) or ' '
    tam = 56 if len(titular) <= 16 else (44 if len(titular) <= 24 else 32)
    pdf.set_y(alto + 30)
    pdf.set_font(pdf.display, 'B', tam)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, tam * 0.40, titular, align='C', new_x='LMARGIN', new_y='NEXT')

    y = max(pdf.get_y() + 5, alto + 54)
    pdf.set_draw_color(*ORO)
    pdf.set_line_width(0.6)
    medio = W / 2
    pdf.line(medio - 17, y, medio + 17, y)
    pdf.set_line_width(0.2)

    pdf.set_y(y + 9)
    pdf.set_font(pdf.display, '', 28)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 12, pdf.limpiar(F['titular_portada']),
                   align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(8)
    m = 34
    pdf.set_left_margin(m); pdf.set_right_margin(m); pdf.set_x(m)
    pdf.set_font(pdf.display, '', 15)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 7.5, pdf.limpiar(F['entrada_portada']),
                   align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_x(m)
    pdf.set_font(pdf.display, '', 13)
    pdf.set_text_color(*ORO)
    pdf.multi_cell(0, 6.4, pdf.limpiar(F['cita_portada']),
                   align='C', markdown=True, new_x='LMARGIN', new_y='NEXT')

    pdf.set_left_margin(22); pdf.set_right_margin(22)

    pdf.set_y(pdf.h - 46)
    pdf.set_draw_color(*LINEA)
    pdf.line(medio - 30, pdf.get_y(), medio + 30, pdf.get_y())
    pdf.ln(6)
    pdf.set_font(pdf.sans, 'B', 7)
    pdf.set_text_color(*ORO)
    pdf.set_char_spacing(2)
    pdf.cell(0, 4.5, F['datos_nacimiento'], align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_char_spacing(0)
    pdf.ln(2)
    pdf.set_font(pdf.display, '', 15)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 7, pdf.limpiar(ficha[0]), align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font(pdf.sans, '', 9)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 5, pdf.limpiar(ficha[1]), align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.set_y(pdf.h - 13)
    pdf.set_font(pdf.sans, '', 7.5)
    pdf.set_text_color(*ORO)
    pdf.cell(0, 4, pdf.limpiar(F['firma']), align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_auto_page_break(auto=True, margin=22)


def pintar_indice(pdf, indice, lang):
    F = TX.FIJO[lang]
    pdf.titulo_seccion(F['indice'])
    pdf.ln(3)
    pdf.set_font(pdf.display, 'B', 27)
    pdf.set_text_color(*TINTA)
    pdf.cell(0, 13, pdf.limpiar(F['indice_titulo']), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)
    pdf.set_font(pdf.sans, '', 9.5)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 5.2, pdf.limpiar(F['indice_entrada']), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(6)
    for titulo, pagina in indice:
        y = pdf.get_y()
        if y > pdf.h - 40:
            break
        pdf.set_font(pdf.display, '', 13)
        pdf.set_text_color(*TINTA)
        pdf.cell(0, 8, pdf.limpiar(titulo), new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(*LINEA)
        pdf.line(pdf.l_margin, y + 7.6, pdf.w - pdf.r_margin, y + 7.6)
        if pagina:
            pdf.set_xy(pdf.w - pdf.r_margin - 16, y)
            pdf.set_font(pdf.sans, 'B', 9)
            pdf.set_text_color(*ORO)
            pdf.cell(16, 8, str(pagina), align='R', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1.5)


# ══════════════════════════════════════════════════════ CÓMO SE LEE
def como_se_lee(pdf, lang):
    F = TX.FIJO[lang]
    A = TX.ANG[lang]
    pdf.add_page()
    pdf.titulo_seccion(F['como_rotulo'], en_indice=True)
    pdf.set_font(pdf.display, 'B', 27)
    pdf.set_text_color(*TINTA)
    pdf.cell(0, 13, pdf.limpiar(F['como_titulo']), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)
    pdf.parrafo(F['como_1'])
    pdf.parrafo(F['como_2'])
    for a in ORDEN_ANG:
        nombre, tema, tecnico = A[a]
        pdf.subrotulo('%s · %s' % (nombre, tecnico))
        pdf.set_font('Times', 'B', 11)
        pdf.set_text_color(*TINTA)
        pdf.cell(0, 5.4, pdf.limpiar(tema), new_x='LMARGIN', new_y='NEXT')
        pdf.parrafo(F['como_' + a])
    pdf.subrotulo(F['rectas_rotulo'])
    pdf.parrafo(F['rectas'])
    pdf.subrotulo(F['radio_rotulo'])
    pdf.parrafo(F['radio'])


# ══════════════════════════════════════════════════════════ EL MAPA
def el_mapa(pdf, cuerpos, lang):
    F = TX.FIJO[lang]
    pdf.add_page(orientation='L')
    pdf.set_auto_page_break(False)
    pdf.titulo_seccion(F['mapa_rotulo'], en_indice=True)
    pdf.set_font(pdf.display, 'B', 24)
    pdf.set_text_color(*TINTA)
    pdf.cell(0, 11, pdf.limpiar(F['mapa_titulo']), new_x='LMARGIN', new_y='NEXT')

    # El mapa se centra en lo que queda de hoja, dejando sitio para la
    # banda de rótulos de arriba, la de abajo y la leyenda. Se dibuja dos
    # veces: la primera sólo para medir cuántas filas de rótulos hacen
    # falta, y la segunda ya en su sitio definitivo.
    izquierda = pdf.l_margin + 8
    ancho = pdf.w - pdf.l_margin - pdf.r_margin - 8
    lz = MDI.Lienzo(x=izquierda, y=0, ancho=ancho)

    arriba_libre = pdf.get_y() + 3
    # El pie de página va a 16 mm del borde; la nota del mapa se queda por
    # encima de él, con holgura, para que no se monten.
    abajo_libre = pdf.h - 27
    hueco = abajo_libre - arriba_libre

    # las bandas: se miden sin dibujar nada
    pdf.set_auto_page_break(False)
    alto_a, alto_b = MDI.medir_rotulos(cuerpos, lz)
    sobra = hueco - (alto_a + lz.alto + alto_b + 12)
    lz.y = arriba_libre + alto_a + max(0.0, sobra) / 2.0

    MDI.dibujar(pdf, cuerpos, lz, lang)
    MDI.leyenda(pdf, izquierda, lz.y + lz.alto + alto_b + 3, ancho, lang)

    pdf.set_y(pdf.h - 25)
    pdf.set_font(pdf.sans, '', 7.5)
    pdf.set_text_color(*SUAVE)
    pdf.cell(0, 4, pdf.limpiar(F['mapa_pie']), align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_auto_page_break(auto=True, margin=22)


# ═══════════════════════════════════════════════════ LOS SEGMENTOS
def _lon(v, lang):
    return '%.1f° %s' % (abs(v), ('E' if v >= 0 else 'W') if lang == 'en'
                         else ('E' if v >= 0 else 'O'))


def _lat(v, lang):
    return '%.0f° %s' % (abs(v), 'N' if v >= 0 else 'S')


def _latitudes_del_cruce(cruces, a, b, lang):
    """«Se cruzan a 62° N y a 58° N». Es lo que ata el texto con el rombo
    del mapa: un cruce es una latitud, y ahí está marcado."""
    F = TX.FIJO[lang]
    par = sorted({round(p['lat'], 0) for p in cruces
                  if {p['a'], p['b']} == {a, b}}, reverse=True)
    if not par:
        return ''
    partes = [_lat(v, lang) for v in par[:4]]
    if len(partes) == 1:
        lista = partes[0]
    else:
        lista = ', '.join(partes[:-1]) + ' %s %s' % (F['y'], partes[-1])
    return '%s %s' % (F['se_cruzan_en'], lista)


def _sitio_para(pdf, milimetros):
    """Pasa de hoja si lo que viene no cabe entero.

    Un rótulo de sección solo al pie de una página, con su contenido en la
    siguiente, se lee como un error. Se pide sitio para el rótulo MÁS lo
    primero que va debajo."""
    if pdf.get_y() > pdf.h - pdf.b_margin - milimetros:
        pdf.add_page()


def _mapa_del_segmento(pdf, cuerpos, seg, lang):
    """El mapa que abre cada capítulo: sólo las líneas de ese segmento."""
    F = TX.FIJO[lang]
    izquierda = pdf.l_margin + 8
    ancho = pdf.w - pdf.l_margin - pdf.r_margin - 8
    lz = MDI.Lienzo(x=izquierda, y=0, ancho=ancho)

    alto_a, alto_b = MDI.medir_rotulos(cuerpos, lz,
                                       MDI.lineas_del_segmento(cuerpos, seg))

    lz.y = pdf.get_y() + alto_a + 1
    pdf.set_auto_page_break(False)
    MDI.dibujar_segmento(pdf, cuerpos, lz, seg, lang)
    alto_ley = MDI.leyenda_segmento(pdf, izquierda, lz.y + lz.alto + alto_b + 2,
                                    ancho, seg, lang)
    pdf.set_y(lz.y + lz.alto + alto_b + 2 + alto_ley)
    pdf.set_font(pdf.sans, '', 6.4)
    pdf.set_text_color(*SUAVE)
    pdf.set_x(izquierda)
    pdf.multi_cell(ancho, 3.4, pdf.limpiar(F['mapa_seg_pie']),
                   new_x='LMARGIN', new_y='NEXT')
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.ln(3)


def _donde_se_activa(pdf, seg, lang):
    """Las ciudades de este segmento, con lo que tienen activo."""
    F = TX.FIJO[lang]
    A = TX.ANG[lang]
    NOM = TX.NOM[lang]

    _sitio_para(pdf, 74)
    pdf.subrotulo(F['donde_activa'])
    if not seg['ciudades']:
        pdf.parrafo(F['donde_activa_vacio'])
        return
    pdf.set_font(pdf.sans, '', 8.5)
    pdf.set_text_color(*SUAVE)
    pdf.multi_cell(0, 4.4, pdf.limpiar(F['donde_activa_intro']),
                   new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    for fila in seg['ciudades']:
        c, propias, otras = fila['c'], fila['propias'], fila['otras']
        alto = 11 + (min(len(propias), 4) + min(len(otras), 2)) * 4.8
        if pdf.get_y() + alto > pdf.h - 26:
            pdf.add_page()
        pdf.ln(2.2)
        pdf.set_font(pdf.display, 'B', 14)
        pdf.set_text_color(*TINTA)
        pdf.cell(0, 6.6, pdf.limpiar(c['en'] if lang == 'en' else c['n']),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(*LINEA)
        y = pdf.get_y() + 0.5
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(2.2)

        def renglon(cu, a, km, propio):
            nombre, tema, _tec = A[a]
            pdf.set_font('Times', '' if propio else 'I', 10.5)
            pdf.set_text_color(*(TINTA if propio else SUAVE))
            pdf.cell(92, 4.8, pdf.limpiar('%s · %s' % (
                NOM[cu], nombre[0].lower() + nombre[1:])))
            pdf.set_font(pdf.sans, '', 7.5)
            pdf.set_text_color(*SUAVE)
            pdf.cell(48, 4.8, pdf.limpiar(tema))
            pdf.cell(0, 4.8, '%d km' % round(km), align='R',
                     new_x='LMARGIN', new_y='NEXT')

        for cu, a, km in propias[:4]:
            renglon(cu, a, km, True)
        if otras:
            pdf.set_font(pdf.sans, '', 7)
            pdf.set_text_color(*ORO)
            pdf.cell(0, 4.2, pdf.limpiar(F['tambien_aqui']).upper(),
                     new_x='LMARGIN', new_y='NEXT')
            for cu, a, km in otras[:2]:
                renglon(cu, a, km, False)


def segmentos(pdf, datos, lang):
    F = TX.FIJO[lang]
    T = TX.largos(lang)
    A = TX.ANG[lang]
    NOM = TX.NOM[lang]
    por_clave = {s['clave']: s for s in datos['segmentos']}

    for clave in TX.ORDEN_SEG:
        seg = por_clave[clave]
        titulo = TX.SEG[lang][clave]
        pdf.add_page()
        pdf.titulo_seccion(titulo, en_indice=True)
        pdf.set_font(pdf.display, 'B', 26)
        pdf.set_text_color(*TINTA)
        pdf.multi_cell(0, 11.5, pdf.limpiar(titulo), new_x='LMARGIN', new_y='NEXT')
        pdf.set_font(pdf.sans, '', 8)
        pdf.set_text_color(*SUAVE)
        pdf.set_char_spacing(1.4)
        pdf.cell(0, 5.5, pdf.limpiar(TX.CUERPO_SEG[lang][clave]).upper(),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.set_char_spacing(0)
        pdf.ln(2)

        # El mapa del segmento va ARRIBA DEL TODO, antes de cualquier texto:
        # es lo primero que la persona quiere ver cuando abre el capítulo.
        _mapa_del_segmento(pdf, datos['cuerpos'], seg, lang)

        for p in T['segmento.' + clave].split('\n\n'):
            pdf.parrafo(p)

        _sitio_para(pdf, 72)
        pdf.subrotulo(F['cuatro_lineas'])
        for pr in seg['principales']:
            for a in ORDEN_ANG:
                k = 'linea.%s.%s' % (pr, a)
                if k not in T:
                    continue
                nombre, tema, tecnico = A[a]
                d = datos['cuerpos'][pr]
                donde = _lon(d[a], lang) if a in ('mc', 'ic') else F['curva']
                if pdf.get_y() > pdf.h - 54:
                    pdf.add_page()
                pdf.destacado('%s · %s' % (NOM[pr], nombre[0].lower() + nombre[1:]))
                pdf.set_font(pdf.sans, '', 8)
                pdf.set_text_color(*SUAVE)
                pdf.cell(0, 4.6, pdf.limpiar('%s · %s · %s' % (tema, tecnico, donde)),
                         new_x='LMARGIN', new_y='NEXT')
                pdf.ln(1)
                pdf.parrafo(T[k])

        # OJO: las parejas vienen como "venus|jupiter" y la clave del texto
        # es "cruce.venus.jupiter". Hay que cambiar la barra por un punto.
        hay = [p for p in seg['parejas'] if ('cruce.' + p.replace('|', '.')) in T]
        if hay:
            _sitio_para(pdf, 66)
            pdf.subrotulo(F['los_cruces'])
            for p in hay:
                a, b = p.split('|')
                if pdf.get_y() > pdf.h - 48:
                    pdf.add_page()
                pdf.destacado('%s %s %s' % (NOM[a], F['con'], NOM[b]))
                # Las latitudes donde ocurre, para poder encontrar el rombo
                # en el mapa de arriba. Un cruce es una latitud: los dos
                # cuerpos quedan angulares a la vez justo ahí.
                donde = _latitudes_del_cruce(seg['cruces'], a, b, lang)
                if donde:
                    pdf.set_font(pdf.sans, '', 8)
                    pdf.set_text_color(*SUAVE)
                    pdf.cell(0, 4.6, pdf.limpiar(donde),
                             new_x='LMARGIN', new_y='NEXT')
                    pdf.ln(1)
                pdf.parrafo(T['cruce.%s.%s' % (a, b)])

        _donde_se_activa(pdf, seg, lang)


# ═══════════════════════════════════════════════════════ CIUDADES
def ciudades(pdf, datos, lang):
    F = TX.FIJO[lang]
    A = TX.ANG[lang]
    NOM = TX.NOM[lang]
    pdf.add_page()
    pdf.titulo_seccion(F['ciudades_rotulo'], en_indice=True)
    pdf.set_font(pdf.display, 'B', 30)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 13, pdf.limpiar(F['ciudades_titulo']),
                   new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)
    pdf.parrafo(F['ciudades_entrada'])

    if not datos['ciudades']:
        pdf.parrafo(F['ciudades_vacio'])
        return

    for fila in datos['ciudades']:
        c, act = fila['c'], fila['activo']
        alto = 14 + min(len(act), 7) * 5
        if pdf.get_y() + alto > pdf.h - 26:
            pdf.add_page()
        pdf.ln(2.5)
        pdf.set_font(pdf.display, 'B', 15)
        pdf.set_text_color(*TINTA)
        pdf.cell(0, 7, pdf.limpiar(c['en'] if lang == 'en' else c['n']),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(*LINEA)
        y = pdf.get_y() + 0.6
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(2.4)
        for cu, a, km in act[:7]:
            nombre, tema, _tec = A[a]
            pdf.set_font('Times', '', 10.5)
            pdf.set_text_color(*TINTA)
            pdf.cell(96, 5, pdf.limpiar('%s · %s' % (NOM[cu],
                                                     nombre[0].lower() + nombre[1:])))
            pdf.set_font(pdf.sans, '', 8)
            pdf.set_text_color(*SUAVE)
            pdf.cell(44, 5, pdf.limpiar(tema))
            pdf.cell(0, 5, '%d km' % round(km), align='R',
                     new_x='LMARGIN', new_y='NEXT')


# ═══════════════════════════════════════════════════════ LA NOTA
def nota(pdf, lang):
    F = TX.FIJO[lang]
    T = TX.largos(lang)
    pdf.add_page()
    pdf.titulo_seccion(F['cierre_rotulo'], en_indice=True)
    pdf.set_font(pdf.display, 'B', 30)
    pdf.set_text_color(*TINTA)
    pdf.multi_cell(0, 13, pdf.limpiar(T['nota.estado.titulo']),
                   new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)
    for p in T['nota.estado'].split('\n\n'):
        pdf.parrafo(p)
    pdf.ln(4)
    pdf.pastilla(F['cita_boton'], F['cita_url'])
    pdf.ln(3)
    pdf.enlace(F['cita_enlace'], F['cita_url'])


# ═══════════════════════════════════════════════════════════ ENTRADA
def construir_pdf(nacimiento, jd, zona='', lang='es'):
    """Arma el informe completo y devuelve los bytes del PDF."""
    lang = 'en' if str(lang).lower().startswith('en') else 'es'
    datos = MD.datos_de(jd)

    nombre = (nacimiento.get('name') or '').strip()
    ficha = _ficha(nacimiento, zona, lang)
    pie = ' · '.join([p for p in (nombre, 'Ricardo Puerta Isaza') if p])

    pdf = MapaPDF(titulo_pie=pie)
    portada(pdf, nombre, ficha, lang)
    pdf.add_page()                      # se reserva la hoja del índice
    pagina_indice = pdf.page
    como_se_lee(pdf, lang)
    el_mapa(pdf, datos['cuerpos'], lang)
    segmentos(pdf, datos, lang)
    nota(pdf, lang)

    pdf.page = pagina_indice
    pdf.set_y(22)
    pdf.set_auto_page_break(False)
    pintar_indice(pdf, pdf.indice, lang)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.page = pdf.pages_count

    return bytes(pdf.output())

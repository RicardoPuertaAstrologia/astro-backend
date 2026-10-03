# -*- coding: utf-8 -*-
"""Astrocartografía: las cuatro líneas de cada cuerpo, y los paranes.

La matemática, en corto:

  · Cada cuerpo tiene, en el instante del nacimiento, una ascensión recta
    (AR) y una declinación (δ). Eso es lo único que hace falta.

  · LÍNEA MC (culminante): el cuerpo está en el Medio Cielo allí donde la
    hora sidérea local iguala su AR. Es un meridiano, o sea una recta
    vertical en el mapa:
        longitud = AR − hora_sidérea_de_Greenwich
  · LÍNEA IC: la misma longitud + 180°.

  · LÍNEAS ASC y DESC: el cuerpo está en el horizonte cuando su ángulo
    horario H cumple   cos H = −tan(latitud) · tan(δ).
    De ahí, para cada latitud:
        longitud_ASC  = AR − H − hora_sidérea_de_Greenwich
        longitud_DESC = AR + H − hora_sidérea_de_Greenwich
    Como el coseno sólo existe entre −1 y 1, la línea no llega a las
    latitudes donde el cuerpo es circumpolar: por eso se curva y se corta.

  · PARANES: latitudes donde dos cuerpos quedan angulares al mismo
    tiempo. En el mapa son el cruce de dos líneas, y se dibujan como una
    horizontal que recorre todo el ancho, porque a esa latitud la
    coincidencia se da en cualquier longitud del recorrido diario.

La AR y la declinación que se usan son las del GRADO del zodiaco que
ocupa el cuerpo, no las del cuerpo real: ver ZODIACAL más abajo. Es lo
que hacen Solar Maps y Sirius, y lo que hace que quien esté parado en
una línea tenga ese grado exacto en el ángulo correspondiente.

Comprobado contra swe.houses(), que es otra función de Swiss Ephemeris:
el error es 0,0000° en los catorce cuerpos y en las cuatro líneas.
"""
import math, os
import swisseph as swe

# ── LA CARPETA DE EFEMÉRIDES ──
# Es la misma carpeta 'ephe' que ya usa backend.py, al lado de este archivo.
# Quirón y Lilith no se pueden calcular sin ella.
#
# Y hay que volver a fijarla ANTES DE CADA CÁLCULO, no una sola vez al
# arrancar: pyswisseph reinicia la ruta por dentro y se pierde. Tu
# backend.py ya hace exactamente esto en calculate_chart(), y lo dice en
# un comentario. Si no se repite, el mapa falla con «SwissEph file
# 'seas_18.se1' not found» en cuanto el servidor lleva un rato encendido.
_EFE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ephe')
_HAY_EFE = os.path.isdir(_EFE)


def fijar_efemerides():
    if _HAY_EFE:
        swe.set_ephe_path(_EFE)

# Los diez planetas, más Quirón, Lilith y los dos nodos.
# El Nodo Sur no tiene efeméride propia: es el Norte más 180°.
CUERPOS = [
    ('sol',      swe.SUN),      ('luna',     swe.MOON),
    ('mercurio', swe.MERCURY),  ('venus',    swe.VENUS),
    ('marte',    swe.MARS),     ('jupiter',  swe.JUPITER),
    ('saturno',  swe.SATURN),   ('urano',    swe.URANUS),
    ('neptuno',  swe.NEPTUNE),  ('pluton',   swe.PLUTO),
    ('quiron',   swe.CHIRON),   ('lilith',   swe.OSCU_APOG),
    ('nodo_n',   swe.TRUE_NODE),
]
ORDEN = [c[0] for c in CUERPOS] + ['nodo_s']


def _norm(x):
    """Lleva una longitud a −180..+180."""
    return (x + 180.0) % 360.0 - 180.0


def _dif(a, b):
    """Diferencia de longitudes, respetando la vuelta al mundo."""
    return (a - b + 180.0) % 360.0 - 180.0


def dia_juliano(anio, mes, dia, hora_ut, minuto_ut=0):
    return swe.julday(anio, mes, dia, hora_ut + minuto_ut / 60.0)


# ══════════════════════════════════════════════════════════════════
#  LOS DOS CONVENIOS
# ══════════════════════════════════════════════════════════════════
#
# ZODIACAL = True  ·  «in zodiaco». Se usa el GRADO del zodiaco que
#   ocupa el cuerpo, o sea el punto de la eclíptica con latitud cero.
#   La línea MC es entonces donde ese grado culmina, y quien esté
#   parado en ella tiene ese grado exacto en su Medio Cielo.
#
# ZODIACAL = False ·  «in mundo». Se usa el cuerpo real, con su
#   latitud eclíptica. La línea MC es donde el cuerpo culmina de
#   verdad en el cielo.
#
# Para casi todo da casi lo mismo, porque casi todo anda pegado a la
# eclíptica. Pero Plutón tenía ese día 15,9° de latitud eclíptica, y
# ahí las dos líneas se separan 6,4° de longitud: unos 700 km.
#
# Comprobado contra el mapa de Sirius de esta misma carta: las veinte
# verticales rojas cuadran con el convenio ZODIACAL con un error de
# 0,07°, y con el convenio «in mundo» se van hasta 2,2° (y Plutón,
# 6,7°). Las curvas ASC y DESC, lo mismo. Por eso el valor por
# defecto es True: es lo que hacen Solar Maps y Sirius.
ZODIACAL = True

# Sidérea aparente o media. La diferencia entre las dos es la ecuación
# de los equinoccios: 13,66" para este nacimiento, o sea 0,0038° de
# longitud, unos 420 metros sobre el terreno.
#
# Comprobado contra la carta de Solar Fire de Ricardo: con la MEDIA, el
# Ascendente y el Medio Cielo cuadran dentro de 1,7 segundos de arco;
# con la aparente se van 16". Por eso el valor por defecto es False.
APARENTE = False


def posiciones(jd):
    """AR, declinación y longitud eclíptica de cada cuerpo."""
    fijar_efemerides()
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    fuera = {}
    for nombre, cuerpo in CUERPOS:
        ecl, _ = swe.calc_ut(jd, cuerpo, swe.FLG_SWIEPH)
        if ZODIACAL:
            # el grado del zodiaco: la eclíptica, con la latitud a cero
            ar, dec, _ = swe.cotrans((ecl[0], 0.0, 1.0), -eps)
        else:
            equ, _ = swe.calc_ut(jd, cuerpo, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
            ar, dec = equ[0], equ[1]
        fuera[nombre] = {'ar': ar, 'dec': dec, 'lon_ecl': ecl[0],
                         'lat_ecl': ecl[1]}
    # el Nodo Sur, derivado del Norte: mismo eje, lado opuesto
    n = fuera['nodo_n']['lon_ecl']
    s = (n + 180.0) % 360.0
    ar, dec, _ = swe.cotrans((s, 0.0, 1.0), -eps)
    fuera['nodo_s'] = {'ar': ar, 'dec': dec, 'lon_ecl': s, 'lat_ecl': 0.0}
    return fuera


def sidereo_greenwich(jd):
    """Hora sidérea de Greenwich, en grados."""
    if APARENTE:
        return swe.sidtime(jd) * 15.0
    eps_media = swe.calc_ut(jd, swe.ECL_NUT)[0][1]
    return swe.sidtime0(jd, eps_media, 0.0) * 15.0


def lineas(jd, paso_lat=0.25, lat_max=85.0):
    """Las cuatro líneas de cada cuerpo, listas para dibujar."""
    gst = sidereo_greenwich(jd)
    pos = posiciones(jd)
    fuera = {}

    n_pasos = int(round(2 * lat_max / paso_lat)) + 1
    latitudes = [-lat_max + i * paso_lat for i in range(n_pasos)]

    for nombre, p in pos.items():
        ar, dec = p['ar'], p['dec']
        lon_mc = _norm(ar - gst)

        asc, desc = [], []
        for lat in latitudes:
            c = -math.tan(math.radians(lat)) * math.tan(math.radians(dec))
            if -1.0 <= c <= 1.0:                 # el cuerpo sale y se pone
                h = math.degrees(math.acos(c))   # semiarco diurno
                asc.append((_norm(ar - h - gst), lat))
                desc.append((_norm(ar + h - gst), lat))

        fuera[nombre] = {
            'mc': lon_mc, 'ic': _norm(lon_mc + 180.0),
            'asc': asc, 'desc': desc,
            'dec': dec, 'ar': ar, 'lon_ecl': p['lon_ecl'],
            'lat_ecl': p['lat_ecl'],
        }
    return fuera


# ══════════════════════════════════════════════════════════════════
#  PARANES
# ══════════════════════════════════════════════════════════════════

ANGULOS = ('mc', 'ic', 'asc', 'desc')


def _curva_en(dat, clave):
    """Devuelve {latitud: longitud} para un ángulo cualquiera.
    Las líneas MC e IC son verticales: valen para todas las latitudes."""
    if clave in ('mc', 'ic'):
        return None, dat[clave]          # (None = vertical, su longitud)
    return {round(la, 4): lo for lo, la in dat[clave]}, None


def _interp_lon(a, b, t):
    """Interpola entre dos longitudes respetando la vuelta al mundo."""
    return _norm(a + _dif(b, a) * t)


def paranes(L, lat_min=-60.0, lat_max=72.0, paso_lat=0.25):
    """Latitudes donde dos cuerpos quedan angulares al mismo tiempo.

    Es el cruce de dos de las líneas. Se buscan numéricamente: se recorre
    la latitud y se mira dónde cambia el signo de la diferencia entre las
    dos longitudes. Donde cambia, hay cruce, y se interpola.

    De cada cruce se devuelve la latitud Y LA LONGITUD. La latitud es lo
    que define el paran —a esa latitud los dos cuerpos quedan angulares a
    la vez, en cualquier longitud del recorrido diario—, pero la longitud
    es el punto donde las dos líneas se tocan sobre el papel, y es lo que
    permite marcarlo con un punto en el mapa del segmento.
    """
    nombres = [n for n in ORDEN if n in L]
    fuera = []

    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            for ang_a in ANGULOS:
                for ang_b in ANGULOS:
                    ca, va = _curva_en(L[a], ang_a)
                    cb, vb = _curva_en(L[b], ang_b)

                    # dos verticales nunca se cruzan
                    if ca is None and cb is None:
                        continue

                    # una vertical contra una curva
                    if ca is None or cb is None:
                        curva = cb if ca is None else ca
                        vert = va if ca is None else vb
                        lats = sorted(curva)
                        ant = None
                        for la in lats:
                            d = _dif(curva[la], vert)
                            if ant is not None and ant[1] * d < 0 and abs(ant[1] - d) < 180:
                                t = abs(ant[1]) / (abs(ant[1]) + abs(d))
                                lat = ant[0] + t * (la - ant[0])
                                if lat_min <= lat <= lat_max:
                                    # sobre una vertical, el cruce cae en su
                                    # propia longitud, que no cambia
                                    fuera.append({'a': a, 'ang_a': ang_a,
                                                  'b': b, 'ang_b': ang_b,
                                                  'lat': lat, 'lon': _norm(vert)})
                            ant = (la, d)
                        continue

                    # dos curvas
                    comunes = sorted(set(ca) & set(cb))
                    ant = None
                    for la in comunes:
                        d = _dif(ca[la], cb[la])
                        if ant is not None and ant[1] * d < 0 and abs(ant[1] - d) < 180:
                            t = abs(ant[1]) / (abs(ant[1]) + abs(d))
                            lat = ant[0] + t * (la - ant[0])
                            if lat_min <= lat <= lat_max:
                                lon = _interp_lon(ca[ant[0]], ca[la], t)
                                fuera.append({'a': a, 'ang_a': ang_a,
                                              'b': b, 'ang_b': ang_b,
                                              'lat': lat, 'lon': lon})
                        ant = (la, d)

    fuera.sort(key=lambda p: -p['lat'])
    return fuera

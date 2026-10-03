# -*- coding: utf-8 -*-
"""Los datos del mapa de una persona: líneas, cruces y ciudades.

Es lo que antes se calculaba a mano y se guardaba en un JSON. Acá se
calcula en el momento, a partir del día juliano del nacimiento, y no se
guarda en ninguna parte: igual que la carta natal, se calcula, se usa y
se descarta.

«Venus con Júpiter» se interpreta como PARAN: la latitud donde los dos
quedan angulares al mismo tiempo. Es lo único que significa combinar dos
planetas en un mapa de lugares.
"""
import io, json, math, os

from mapa_lineas import lineas, paranes

AQUI = os.path.dirname(os.path.abspath(__file__))

LAT_MIN, LAT_MAX = -58.0, 76.0
ORDEN_ANG = ['asc', 'mc', 'desc', 'ic']

# El radio en el que se considera que una línea está activa sobre un
# lugar. No hay un número único y cada escuela usa el suyo; 300 km es una
# medida prudente, y es la que se explica en el informe.
ORBE_KM = 300.0
KM_POR_GRADO = 111.32

# Cada segmento: clave, los planetas PRINCIPALES —de los que se cuentan
# las cuatro líneas— y los SOCIOS, con los que se buscan cruces. Cuando
# hay más de un principal, los cruces se buscan además entre ellos
# mismos: es el caso de Retos y riesgos, donde los tres mandan por igual.
SEGMENTOS = [
    ('amor',        ['venus'],   ['jupiter']),
    ('vocacion',    ['jupiter'], ['sol', 'venus']),
    ('familia',     ['luna'],    ['jupiter', 'venus']),
    ('imaginacion', ['neptuno'], ['luna', 'pluton']),
    ('emocion',     ['urano'],   ['pluton', 'saturno', 'marte',
                                  'sol', 'luna', 'mercurio']),
    ('educacion',   ['mercurio'], ['jupiter', 'pluton', 'saturno']),
    ('enfoque',     ['saturno'], ['sol', 'luna', 'mercurio']),
    ('retos',       ['marte', 'saturno', 'pluton'], []),
]


def parejas_de(principales, socios):
    """Los cruces de un segmento: cada principal con cada socio, y —si hay
    más de un principal— los principales entre ellos."""
    pares = set()
    for p in principales:
        for s in socios:
            pares.add(tuple(sorted([p, s])))
    for i, a in enumerate(principales):
        for b in principales[i + 1:]:
            pares.add(tuple(sorted([a, b])))
    return sorted(pares)


def _partir(puntos):
    """Corta una curva donde salta de un borde del mapa al otro."""
    tramos, act = [], []
    for i, (lo, la) in enumerate(puntos):
        if act and abs(lo - puntos[i - 1][0]) > 180.0:
            tramos.append(act)
            act = []
        act.append((lo, la))
    if act:
        tramos.append(act)
    return [t for t in tramos if len(t) > 1]


def _ciudades():
    return json.load(io.open(os.path.join(AQUI, 'mapa_ciudades.json'),
                             encoding='utf-8'))


def activo_en(cuerpos, la, lo, orbe=ORBE_KM, cuales=None):
    """Qué cuerpos y qué ángulos están activos sobre un punto, y a cuántos
    kilómetros. Para las verticales la distancia es la diferencia de
    longitud, encogida por el coseno de la latitud; para las curvas, la
    distancia al segmento más cercano."""
    fuera = []
    cos_la = math.cos(math.radians(la))
    for cu, d in cuerpos.items():
        if cuales is not None and cu not in cuales:
            continue
        for a in ORDEN_ANG:
            if a in ('mc', 'ic'):
                dlon = abs(((lo - d[a] + 180) % 360) - 180)
                km = dlon * KM_POR_GRADO * cos_la
            else:
                km = 1e9
                for tramo in d[a]:
                    for i in range(len(tramo) - 1):
                        (lo1, la1), (lo2, la2) = tramo[i], tramo[i + 1]
                        dx = (((lo2 - lo1 + 180) % 360) - 180) * cos_la
                        dy = la2 - la1
                        ax = (((lo1 - lo + 180) % 360) - 180) * cos_la
                        ay = la1 - la
                        ll = dx * dx + dy * dy
                        u = max(0.0, min(1.0, -(ax * dx + ay * dy) / ll)) if ll else 0.0
                        px, py = ax + u * dx, ay + u * dy
                        km = min(km, math.hypot(px, py) * KM_POR_GRADO)
            if km <= orbe:
                fuera.append((cu, a, km))
    fuera.sort(key=lambda t: t[2])
    return fuera


def datos_de(jd):
    """Todo lo que el informe necesita saber del mapa de esta persona."""
    L = lineas(jd, paso_lat=0.5, lat_max=LAT_MAX + 6)
    P = paranes(L, LAT_MIN + 3, LAT_MAX - 3)

    cuerpos = {}
    for n, d in L.items():
        curvas = {}
        for cl in ('asc', 'desc'):
            pts = [(lo, la) for lo, la in d[cl] if LAT_MIN - 2 <= la <= LAT_MAX + 2]
            curvas[cl] = _partir(pts) if len(pts) > 1 else []
        cuerpos[n] = {
            'mc': d['mc'], 'ic': d['ic'],
            'asc': curvas['asc'], 'desc': curvas['desc'],
            'lon_ecl': d['lon_ecl'],
        }

    par = {}
    for p in P:
        clave = '|'.join(sorted([p['a'], p['b']]))
        par.setdefault(clave, []).append(p)

    todas_ciudades = _ciudades()

    segs = []
    for clave, principales, socios in SEGMENTOS:
        parejas = ['|'.join(p) for p in parejas_de(principales, socios)]

        # Los cruces de este segmento, con su punto sobre el mapa.
        cruces = []
        for k in parejas:
            for p in par.get(k, []):
                if LAT_MIN <= p['lat'] <= LAT_MAX:
                    cruces.append(p)
        cruces.sort(key=lambda p: -p['lat'])

        # Sobre el mapa del segmento sólo se dibujan las líneas que hacen
        # falta: las cuatro del planeta o planetas que mandan, y de los
        # socios SÓLO las que efectivamente cruzan. Dibujar las cuatro de
        # cada socio llenaría el mapa de líneas que no se mencionan en
        # ninguna parte: Emoción e Inestabilidad tiene seis socios, o sea
        # veintiocho líneas, y no se entendería nada.
        socias = set()
        for p in cruces:
            for cu, ang in ((p['a'], p['ang_a']), (p['b'], p['ang_b'])):
                if cu not in principales:
                    socias.add((cu, ang))

        # Las ciudades del segmento: aquellas donde está activa una línea
        # de un planeta que manda. Si además hay un socio activo ahí, se
        # anota aparte, porque eso es lo que enriquece el lugar.
        ciudades = []
        for c in todas_ciudades:
            propias = activo_en(cuerpos, c['la'], c['lo'], cuales=set(principales))
            if not propias:
                continue
            otras = activo_en(cuerpos, c['la'], c['lo'], cuales=set(socios)) if socios else []
            ciudades.append({'c': c, 'propias': propias, 'otras': otras})
        ciudades.sort(key=lambda f: f['propias'][0][2])

        segs.append({'clave': clave, 'principales': principales,
                     'socios': socios, 'parejas': parejas,
                     'cruces': cruces, 'socias': sorted(socias),
                     'ciudades': ciudades,
                     'n_paranes': len(cruces)})

    return {'cuerpos': cuerpos, 'paranes': par, 'segmentos': segs,
            'lat_min': LAT_MIN, 'lat_max': LAT_MAX}

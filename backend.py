"""
Backend de cálculos astrológicos profesionales — v3.0

Motor: Swiss Ephemeris (pyswisseph) — validado contra Solar Fire v9.1.0
Sistema casas: Plácidus
Zodíaco: Tropical
Marco: Geocéntrico

Funcionalidades v3.0:
- Tránsitos de los 5 lentos (Júpiter, Saturno, Urano, Neptuno, Plutón)
- Aspectos entre planetas natales (carta completa)
- Dignidades planetarias y regentes de casas
- Fechas exactas de tránsitos (búsqueda iterativa)
- Calendario 12 meses
- Manejo correcto de LMT y zonas horarias modernas
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from timezonefinder import TimezoneFinder
import json
app = FastAPI(title="Uranus Transits API", version="4.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Path a las efemérides Swiss Ephemeris.
# Si existe la carpeta 'ephe' relativa al backend, usarla (necesaria para Quirón y otros asteroides).
# Si no existe, usar Moshier built-in (solo soporta planetas principales).
import os as _os
_ephe_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'ephe')
if _os.path.isdir(_ephe_dir):
    swe.set_ephe_path(_ephe_dir)
else:
    swe.set_ephe_path(None)

tf = TimezoneFinder()
# ============================================================
# CARGAR INTERPRETACIONES (biblioteca bilingüe — 403 textos por idioma)
# ============================================================
_data_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'data')

IDIOMAS_DISPONIBLES = ['es', 'en']
IDIOMA_POR_DEFECTO = 'es'

_ARCHIVOS_INTERPRETACIONES = {
    'es': 'interpretaciones_completas_ES.json',
    'en': 'interpretaciones_completas_EN.json',
}

def _cargar_biblioteca(lang, filename):
    path = _os.path.join(_data_dir, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ [{lang}] {len(data)} interpretaciones cargadas desde {path}")
        return data
    except FileNotFoundError:
        print(f"⚠ [{lang}] Archivo no encontrado: {path}")
    except Exception as e:
        print(f"⚠ [{lang}] Error cargando interpretaciones: {e}")
    return {}

INTERPRETACIONES_POR_IDIOMA = {
    lang: _cargar_biblioteca(lang, fname)
    for lang, fname in _ARCHIVOS_INTERPRETACIONES.items()
}

# Compatibilidad hacia atrás: el nombre antiguo apunta al español
INTERPRETACIONES = INTERPRETACIONES_POR_IDIOMA.get(IDIOMA_POR_DEFECTO, {})


def normalizar_idioma(lang):
    l = (lang or IDIOMA_POR_DEFECTO).lower().strip()[:2]
    return l if l in IDIOMAS_DISPONIBLES else IDIOMA_POR_DEFECTO


def obtener_texto(clave, lang):
    """Devuelve (texto, idioma_real). Si falta la clave en el idioma pedido,
    cae al español. Si tampoco existe allí, devuelve (None, lang)."""
    lang = normalizar_idioma(lang)
    texto = INTERPRETACIONES_POR_IDIOMA.get(lang, {}).get(clave)
    if texto is not None:
        return texto, lang
    if lang != IDIOMA_POR_DEFECTO:
        texto = INTERPRETACIONES_POR_IDIOMA.get(IDIOMA_POR_DEFECTO, {}).get(clave)
        if texto is not None:
            return texto, IDIOMA_POR_DEFECTO
    return None, lang
    
# Mapas de normalización
PLANET_KEY_MAP = {
    'sun': 'sol', 'sol': 'sol',
    'moon': 'luna', 'luna': 'luna',
    'mercury': 'mercurio', 'mercurio': 'mercurio',
    'venus': 'venus',
    'mars': 'marte', 'marte': 'marte',
    'jupiter': 'jupiter', 'júpiter': 'jupiter',
    'saturn': 'saturno', 'saturno': 'saturno',
    'uranus': 'urano', 'urano': 'urano',
    'neptune': 'neptuno', 'neptuno': 'neptuno',
    'pluto': 'pluton', 'plutón': 'pluton', 'pluton': 'pluton',
    'chiron': 'quiron', 'quirón': 'quiron', 'quiron': 'quiron'
}

SIGN_KEY_MAP = {
    'aries': 'aries',
    'taurus': 'tauro', 'tauro': 'tauro',
    'gemini': 'geminis', 'géminis': 'geminis', 'geminis': 'geminis',
    'cancer': 'cancer', 'cáncer': 'cancer',
    'leo': 'leo',
    'virgo': 'virgo',
    'libra': 'libra',
    'scorpio': 'escorpio', 'escorpio': 'escorpio',
    'sagittarius': 'sagitario', 'sagitario': 'sagitario',
    'capricorn': 'capricornio', 'capricornio': 'capricornio',
    'aquarius': 'acuario', 'acuario': 'acuario',
    'pisces': 'piscis', 'piscis': 'piscis'
}

ORDEN_PLANETAS = ['sol', 'luna', 'mercurio', 'venus', 'marte', 'jupiter', 'saturno', 'urano', 'neptuno', 'pluton', 'quiron']

SIGNOS_OPUESTOS = {
    'aries': 'libra', 'tauro': 'escorpio', 'geminis': 'sagitario',
    'cancer': 'capricornio', 'leo': 'acuario', 'virgo': 'piscis',
    'libra': 'aries', 'escorpio': 'tauro', 'sagitario': 'geminis',
    'capricornio': 'cancer', 'acuario': 'leo', 'piscis': 'virgo'
}

def normalizar_planeta(p):
    return PLANET_KEY_MAP.get(str(p).lower().strip(), None)

def normalizar_signo(s):
    return SIGN_KEY_MAP.get(str(s).lower().strip(), None)

def obtener_interpretaciones_carta(natal_chart_data, lang=IDIOMA_POR_DEFECTO):
    """
    Recibe el resultado de /calculate (campo 'natal_chart') y devuelve
    todas las interpretaciones aplicables en el idioma pedido.
    """
    lang = normalizar_idioma(lang)
    resultado = {}

    def agregar(clave, meta):
        if clave in resultado:
            return
        texto, idioma_real = obtener_texto(clave, lang)
        if texto is None:
            return
        meta['texto'] = texto
        meta['idioma'] = idioma_real
        resultado[clave] = meta

    # Ascendente en signo (primero, para que anteceda a los planetas)
    asc_data = natal_chart_data.get('asc', {})
    if asc_data:
        signo_asc = normalizar_signo(asc_data.get('sign'))
        if signo_asc:
            agregar(f"ascendente_{signo_asc}", {'tipo': 'ascendente', 'signo': signo_asc})

    # Planetas en signos y casas
    for planeta_en, datos in natal_chart_data.get('planets', {}).items():
        p = normalizar_planeta(planeta_en)
        if not p:
            continue
        signo = normalizar_signo(datos.get('sign'))
        casa = datos.get('house')
        if signo:
            agregar(f"{p}_{signo}", {'tipo': 'planeta_en_signo', 'planeta': p, 'signo': signo})
        if casa and 1 <= casa <= 12:
            agregar(f"{p}_casa_{casa}", {'tipo': 'planeta_en_casa', 'planeta': p, 'casa': casa})

    extras = natal_chart_data.get('extras', {})

    # Quirón
    if 'chiron' in extras:
        signo = normalizar_signo(extras['chiron'].get('sign'))
        casa = extras['chiron'].get('house')
        if signo:
            agregar(f"quiron_{signo}", {'tipo': 'planeta_en_signo', 'planeta': 'quiron', 'signo': signo})
        if casa and 1 <= casa <= 12:
            agregar(f"quiron_casa_{casa}", {'tipo': 'planeta_en_casa', 'planeta': 'quiron', 'casa': casa})

    # Nodos lunares en signos (Sur = opuesto automático del Norte)
    if 'true_node' in extras:
        signo_norte = normalizar_signo(extras['true_node'].get('sign'))
        casa_norte = extras['true_node'].get('house')
        if signo_norte:
            agregar(f"nodo_norte_{signo_norte}", {'tipo': 'nodo_norte', 'signo': signo_norte})
            signo_sur = SIGNOS_OPUESTOS.get(signo_norte)
            if signo_sur:
                agregar(f"nodo_sur_{signo_sur}", {'tipo': 'nodo_sur', 'signo': signo_sur})
        # Nodo Norte en casa
        if casa_norte and 1 <= casa_norte <= 12:
            agregar(f"nodo_norte_casa_{casa_norte}", {'tipo': 'nodo_norte_casa', 'casa': casa_norte})
    
    # Nodo Sur en casa (material nuevo — fase 11)
    if 'south_node' in extras:
        casa_sur = extras['south_node'].get('house')
        if casa_sur and 1 <= casa_sur <= 12:
            agregar(f"nodo_sur_casa_{casa_sur}", {'tipo': 'nodo_sur_casa', 'casa': casa_sur})

    
    # PUENTE DE SÍNTESIS: cruza el signo del Nodo Norte con la casa donde cae.
    # Va aquí, al final del eje nodal, para que se lea como síntesis después de
    # los textos de nodos en signos y en casas. Un solo puente cubre todo el eje,
    # porque el Nodo Sur queda determinado por el Norte.
    if 'true_node' in extras:
        signo_nn = normalizar_signo(extras['true_node'].get('sign'))
        casa_nn = extras['true_node'].get('house')
        if signo_nn and casa_nn and 1 <= casa_nn <= 12:
            casa_sur_eje = casa_nn + 6 if casa_nn <= 6 else casa_nn - 6
            agregar(f"puente_nn_{signo_nn}_casa_{casa_nn}", {
                'tipo': 'puente_nodal',
                'signo_norte': signo_nn,
                'casa_norte': casa_nn,
                'signo_sur': SIGNOS_OPUESTOS.get(signo_nn),
                'casa_sur': casa_sur_eje
            })
            
    # Parte de la Fortuna
    if 'fortuna' in extras:
        signo = normalizar_signo(extras['fortuna'].get('sign'))
        casa = extras['fortuna'].get('house')
        if signo:
            agregar(f"fortuna_{signo}", {'tipo': 'fortuna_signo', 'signo': signo})
        if casa and 1 <= casa <= 12:
            agregar(f"fortuna_casa_{casa}", {'tipo': 'fortuna_casa', 'casa': casa})

    # Aspectos natales
    for asp in natal_chart_data.get('aspects', []):
        p1 = normalizar_planeta(asp.get('planet1'))
        p2 = normalizar_planeta(asp.get('planet2'))
        if not p1 or not p2 or p1 == p2:
            continue
        if ORDEN_PLANETAS.index(p1) > ORDEN_PLANETAS.index(p2):
            p1, p2 = p2, p1
        nombre_asp = asp.get('aspect', {}).get('name_en' if lang == 'en' else 'name_es')
        agregar(f"aspectos_{p1}_{p2}", {
            'tipo': 'aspecto', 'planeta1': p1, 'planeta2': p2, 'aspecto': nombre_asp
        })

    return resultado
# ============================================================
# CONSTANTS
# ============================================================
SIGNS_ES = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo','Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']
SIGNS_EN = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

PLANETS = {
    'sun': swe.SUN, 'moon': swe.MOON, 'mercury': swe.MERCURY,
    'venus': swe.VENUS, 'mars': swe.MARS, 'jupiter': swe.JUPITER,
    'saturn': swe.SATURN, 'uranus': swe.URANUS,
    'neptune': swe.NEPTUNE, 'pluto': swe.PLUTO
}

# Puntos adicionales: cuerpos celestes y puntos sensibles
# Quirón es un asteroide real con efemérides; los Nodos y Lilith son puntos calculados
ADDITIONAL_BODIES = {
    'chiron': swe.CHIRON,        # Asteroide #2060
    'true_node': swe.TRUE_NODE,  # Nodo Norte verdadero (oscilante)
    'lilith': swe.OSCU_APOG,     # Lilith Verdadera (apogeo lunar oscilante)
}

# Puntos que generan aspectos como cualquier planeta (Quirón y Nodos sí)
# Lilith y Partes Árabes solo se posicionan, no generan aspectos
ASPECT_FORMING_POINTS = ['chiron', 'true_node', 'south_node']

# Slow planets used for transits
TRANSIT_PLANETS = ['jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

ASPECT_TYPES = [
    {'name_es':'Conjunción', 'name_en':'Conjunction', 'angle':0,   'orb_natal':8.0, 'orb_transit':2.0, 'glyph':'☌', 'nature':'major'},
    {'name_es':'Sextil',     'name_en':'Sextile',     'angle':60,  'orb_natal':4.0, 'orb_transit':1.5, 'glyph':'⚹', 'nature':'major'},
    {'name_es':'Cuadratura', 'name_en':'Square',      'angle':90,  'orb_natal':7.0, 'orb_transit':2.0, 'glyph':'□', 'nature':'major'},
    {'name_es':'Trígono',    'name_en':'Trine',       'angle':120, 'orb_natal':7.0, 'orb_transit':2.0, 'glyph':'△', 'nature':'major'},
    {'name_es':'Oposición',  'name_en':'Opposition',  'angle':180, 'orb_natal':8.0, 'orb_transit':2.0, 'glyph':'☍', 'nature':'major'},
]

# DIGNIDADES PLANETARIAS (sistema clásico)
# Cada planeta: regente (rulership), exaltación, exilio (detrimento), caída (fall)
DIGNITIES = {
    'sun':     {'rules': [4],         'exalted': [0],         'detriment': [10],        'fall': [6]},   # Leo, Aries, Acuario, Libra
    'moon':    {'rules': [3],         'exalted': [1],         'detriment': [9],         'fall': [7]},   # Cáncer, Tauro, Capricornio, Escorpio
    'mercury': {'rules': [2, 5],      'exalted': [5],         'detriment': [8, 11],     'fall': [11]},  # Géminis/Virgo, Virgo, Sagitario/Piscis, Piscis
    'venus':   {'rules': [1, 6],      'exalted': [11],        'detriment': [7, 0],      'fall': [5]},   # Tauro/Libra, Piscis, Escorpio/Aries, Virgo
    'mars':    {'rules': [0, 7],      'exalted': [9],         'detriment': [6, 1],      'fall': [3]},   # Aries/Escorpio, Capricornio, Libra/Tauro, Cáncer
    'jupiter': {'rules': [8, 11],     'exalted': [3],         'detriment': [2, 5],      'fall': [9]},   # Sagitario/Piscis, Cáncer, Géminis/Virgo, Capricornio
    'saturn':  {'rules': [9, 10],     'exalted': [6],         'detriment': [3, 4],      'fall': [0]},   # Capricornio/Acuario, Libra, Cáncer/Leo, Aries
    'uranus':  {'rules': [10],        'exalted': [7],         'detriment': [4],         'fall': [1]},   # Acuario, Escorpio, Leo, Tauro (regencias modernas)
    'neptune': {'rules': [11],        'exalted': [3],         'detriment': [5],         'fall': [9]},   # Piscis, Cáncer, Virgo, Capricornio
    'pluto':   {'rules': [7],         'exalted': [0],         'detriment': [1],         'fall': [6]},   # Escorpio, Aries, Tauro, Libra
}

# REGENTES TRADICIONALES DE CADA SIGNO (para regente de casa)
# Sistema mixto: planetas tradicionales para consistencia con literatura clásica
SIGN_RULERS = {
    0:  'mars',    # Aries
    1:  'venus',   # Tauro
    2:  'mercury', # Géminis
    3:  'moon',    # Cáncer
    4:  'sun',     # Leo
    5:  'mercury', # Virgo
    6:  'venus',   # Libra
    7:  'pluto',   # Escorpio (moderno) — tradicional sería marte
    8:  'jupiter', # Sagitario
    9:  'saturn',  # Capricornio
    10: 'uranus',  # Acuario (moderno) — tradicional sería saturno
    11: 'neptune', # Piscis (moderno) — tradicional sería júpiter
}


# ============================================================
# MODELS
# ============================================================
class BirthData(BaseModel):
    name: Optional[str] = ""
    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city_name: Optional[str] = ""
    use_lmt: bool = False
    transit_planet: Optional[str] = "uranus"  # Cual planeta priorizar para análisis


# ============================================================
# TIME
# ============================================================
def get_julian_day_ut(birth: BirthData):
    lmt_offset_hours = birth.longitude / 15.0
    if birth.use_lmt:
        ut_hour = birth.hour + birth.minute/60 - lmt_offset_hours
        jd = swe.julday(birth.year, birth.month, birth.day, ut_hour)
        h = int(abs(lmt_offset_hours))
        m = int((abs(lmt_offset_hours) - h) * 60)
        sign = '+' if lmt_offset_hours >= 0 else '-'
        return jd, f"LMT (UT{sign}{h}h{m:02d}m)"

    tz_name = tf.timezone_at(lat=birth.latitude, lng=birth.longitude)
    if not tz_name:
        ut_hour = birth.hour + birth.minute/60 - lmt_offset_hours
        jd = swe.julday(birth.year, birth.month, birth.day, ut_hour)
        return jd, "LMT fallback"

    try:
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(datetime(birth.year, birth.month, birth.day, birth.hour, birth.minute, 0))
        utc_dt = local_dt.astimezone(pytz.UTC)
        ut_hour = utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)
        offset_h = local_dt.utcoffset().total_seconds() / 3600
        return jd, f"{tz_name} (UTC{offset_h:+.1f})"
    except Exception:
        ut_hour = birth.hour + birth.minute/60 - lmt_offset_hours
        jd = swe.julday(birth.year, birth.month, birth.day, ut_hour)
        return jd, "LMT (fallback for pre-standardization date)"


# ============================================================
# FORMATTING
# ============================================================
def format_position(longitude, lang='es'):
    signs = SIGNS_ES if lang == 'es' else SIGNS_EN
    longitude = longitude % 360
    sign_idx = int(longitude // 30)
    deg_in_sign = longitude % 30
    deg = int(deg_in_sign)
    minutes_full = (deg_in_sign - deg) * 60
    min_int = int(minutes_full)
    sec = int(round((minutes_full - min_int) * 60))
    if sec == 60:
        sec = 0
        min_int += 1
        if min_int == 60:
            min_int = 0
            deg += 1
    return {
        'longitude': longitude,
        'sign': signs[sign_idx],
        'sign_index': sign_idx,
        'degree': deg,
        'minute': min_int,
        'second': sec,
        'formatted': f"{deg}° {signs[sign_idx]} {min_int:02d}'{sec:02d}\""
    }


# ============================================================
# CORE CALCULATIONS
# ============================================================
def calc_planet(jd, planet_id):
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    result, _ = swe.calc_ut(jd, planet_id, flags)
    return {
        'longitude': result[0],
        'latitude': result[1],
        'distance': result[2],
        'speed': result[3],
        'retrograde': result[3] < 0
    }


def calc_houses_placidus(jd, lat, lon):
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    return {
        'cusps': list(cusps),
        'asc': ascmc[0],
        'mc': ascmc[1],
        'armc': ascmc[2],
        'vertex': ascmc[3]
    }


def get_house_for_longitude(longitude, cusps):
    longitude = longitude % 360
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= longitude < end:
                return i + 1
        else:
            if longitude >= start or longitude < end:
                return i + 1
    return 1


# ============================================================
# DIURNAL/NOCTURNAL CHART & ARABIC PARTS
# ============================================================
def is_diurnal_chart(sun_lon, asc_lon, mc_lon):
    """
    Determina si una carta es diurna (Sol sobre el horizonte) o nocturna.
    Usa el método clásico: el Sol está sobre el horizonte si está entre
    el Descendente (ASC + 180) y el Ascendente, recorrido en orden antihorario,
    pasando por el Medio Cielo (MC).

    Equivalente más simple: el Sol está en casas 7-12 (sobre el horizonte) = diurno
    en casas 1-6 (bajo el horizonte) = nocturno
    """
    # Diferencia angular entre Sol y ASC, normalizada 0-360
    diff = (sun_lon - asc_lon) % 360
    # Si el Sol está entre 180° y 360° del ASC (en sentido antihorario), está sobre el horizonte
    # Es decir: cae en casas 7, 8, 9, 10, 11, 12
    return diff >= 180


def calc_part_of_fortune(asc_lon, sun_lon, moon_lon, is_diurnal):
    """
    Parte de la Fortuna (Pars Fortunae)
    Diurna: ASC + Luna - Sol
    Nocturna: ASC + Sol - Luna
    """
    if is_diurnal:
        return (asc_lon + moon_lon - sun_lon) % 360
    else:
        return (asc_lon + sun_lon - moon_lon) % 360


def calc_part_of_misfortune(asc_lon, mars_lon, saturn_lon):
    """
    Parte del Infortunio
    Fórmula clásica: ASC + Marte - Saturno

    A diferencia de la Fortuna, esta parte NO tiene fórmula diurna/nocturna
    invertida — la fórmula es la misma siempre.
    Glifo tradicional: cruz templaria (✠)
    """
    return (asc_lon + mars_lon - saturn_lon) % 360


# ============================================================
# DIGNITIES
# ============================================================
def get_dignity(planet, sign_idx):
    """Retorna la dignidad del planeta en el signo."""
    if planet not in DIGNITIES:
        return None
    d = DIGNITIES[planet]
    if sign_idx in d['rules']:
        return {'es': 'domicilio', 'en': 'rulership', 'symbol': '+5'}
    if sign_idx in d['exalted']:
        return {'es': 'exaltación', 'en': 'exaltation', 'symbol': '+4'}
    if sign_idx in d['fall']:
        return {'es': 'caída', 'en': 'fall', 'symbol': '-4'}
    if sign_idx in d['detriment']:
        return {'es': 'exilio', 'en': 'detriment', 'symbol': '-5'}
    return None


def get_house_ruler(cusp_longitude):
    """Retorna el regente del signo en la cúspide de la casa."""
    sign_idx = int(cusp_longitude / 30) % 12
    return SIGN_RULERS[sign_idx]


# ============================================================
# ASPECTS
# ============================================================
def detect_aspect_natal(lon1, lon2):
    """Detecta aspecto entre dos puntos natales (orbes amplios)."""
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff
    for asp in ASPECT_TYPES:
        orb = abs(diff - asp['angle'])
        if orb <= asp['orb_natal']:
            return {
                'name_es': asp['name_es'], 'name_en': asp['name_en'],
                'angle': asp['angle'], 'glyph': asp['glyph'],
                'orb': orb, 'exact_diff': diff
            }
    return None


def detect_aspect_transit(transit_lon, natal_lon):
    """Detecta aspecto en tránsito (orbe estricto)."""
    diff = abs(transit_lon - natal_lon)
    if diff > 180:
        diff = 360 - diff
    for asp in ASPECT_TYPES:
        orb = abs(diff - asp['angle'])
        if orb <= asp['orb_transit']:
            return {
                'name_es': asp['name_es'], 'name_en': asp['name_en'],
                'angle': asp['angle'], 'glyph': asp['glyph'],
                'orb': orb, 'exact_diff': diff
            }
    return None


def calculate_natal_aspects(planets):
    """Calcula todos los aspectos entre planetas natales (incluyendo ASC, MC)."""
    # Pares que son matemáticamente triviales (siempre forman el mismo aspecto):
    # ASC-DC: oposición exacta (DC = ASC + 180°)
    # MC-IC: oposición exacta (IC = MC + 180°)
    # Nodo N - Nodo S: oposición exacta (siempre a 180°)
    TRIVIAL_PAIRS = {
        frozenset(['true_node', 'south_node']),
        frozenset(['mean_node', 'south_node']),
    }

    aspects = []
    keys = list(planets.keys())
    for i, p1 in enumerate(keys):
        for p2 in keys[i+1:]:
            # Saltar pares matemáticamente triviales
            if frozenset([p1, p2]) in TRIVIAL_PAIRS:
                continue
            lon1 = planets[p1]['longitude']
            lon2 = planets[p2]['longitude']
            asp = detect_aspect_natal(lon1, lon2)
            if asp:
                aspects.append({
                    'planet1': p1, 'planet2': p2,
                    'lon1': lon1, 'lon2': lon2,
                    'aspect': asp
                })
    return aspects


# ============================================================
# EXACT TRANSIT DATES (búsqueda iterativa)
# ============================================================
def find_exact_aspect_dates(planet_id, natal_lon, target_angle, jd_start, jd_end, max_iter=100):
    """
    Encuentra las fechas (JD) en que un planeta hace exactamente el aspecto
    `target_angle` con la longitud natal `natal_lon`, dentro del rango [jd_start, jd_end].

    Algoritmo:
    1. Muestrear cada N días la diferencia angular signed = (transit - natal - target_angle) mod 360
    2. Detectar cambios de signo en esa diferencia → cruces exactos
    3. Refinar con bisección
    """
    def angular_residual(jd):
        """Retorna diferencia signed entre el aspecto observado y el target_angle (-180 a 180)."""
        pos = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        diff = (pos[0] - natal_lon - target_angle) % 360
        if diff > 180:
            diff -= 360
        return diff

    # Para conjunción (0°) y oposición (180°) hay 1 aspecto exacto en cada sentido.
    # Para otros aspectos (60°, 90°, 120°), también hay solo 1 cruce por cada lado.
    # Lo crítico: muestreamos densamente porque planetas lentos pueden retrogradar.

    # Sample every 5 days
    sample_step = 5.0
    samples = []
    jd = jd_start
    while jd <= jd_end:
        samples.append((jd, angular_residual(jd)))
        jd += sample_step
    samples.append((jd_end, angular_residual(jd_end)))

    crossings = []
    for i in range(len(samples) - 1):
        jd_a, val_a = samples[i]
        jd_b, val_b = samples[i+1]
        # Cambio de signo (cruce de 0)
        # Pero excluir saltos grandes (alrededor de ±180 boundary)
        if val_a * val_b < 0 and abs(val_a - val_b) < 180:
            # Bisección para encontrar el cero
            lo, hi = jd_a, jd_b
            for _ in range(60):
                mid = (lo + hi) / 2
                val_mid = angular_residual(mid)
                if val_mid * val_a < 0:
                    hi = mid
                    val_b = val_mid
                else:
                    lo = mid
                    val_a = val_mid
                if abs(hi - lo) < 1e-6:
                    break
            crossings.append((lo + hi) / 2)

    return crossings


def jd_to_iso_date(jd):
    """Convierte Julian Day UT a string ISO date."""
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    return f"{y:04d}-{m:02d}-{d:02d} {hour:02d}:{minute:02d} UT"


# ============================================================
# 12-MONTH TRANSIT CALENDAR
# ============================================================
def calculate_transit_calendar(natal_planets, jd_start, jd_end):
    """
    Calcula todos los aspectos exactos de los planetas lentos
    a planetas natales en el rango [jd_start, jd_end].
    Retorna lista ordenada por fecha.
    """
    events = []
    natal_keys = list(natal_planets.keys())

    for transit_p in TRANSIT_PLANETS:
        planet_id = PLANETS[transit_p]
        for natal_p in natal_keys:
            natal_lon = natal_planets[natal_p]['longitude']
            for asp in ASPECT_TYPES:
                # Probar el aspecto en ambos lados (target_angle y -target_angle)
                # Para ángulos no 0 ni 180, hay dos posibles "encuentros"
                targets = [asp['angle']] if asp['angle'] in (0, 180) else [asp['angle'], -asp['angle']]
                for tgt in targets:
                    dates_jd = find_exact_aspect_dates(planet_id, natal_lon, tgt, jd_start, jd_end)
                    for jd_exact in dates_jd:
                        events.append({
                            'jd': jd_exact,
                            'date': jd_to_iso_date(jd_exact),
                            'transit_planet': transit_p,
                            'natal_planet': natal_p,
                            'aspect_es': asp['name_es'],
                            'aspect_en': asp['name_en'],
                            'aspect_glyph': asp['glyph'],
                            'aspect_angle': asp['angle']
                        })

    events.sort(key=lambda x: x['jd'])
    # Deduplicar eventos muy cercanos (< 0.5 días) — pueden surgir por retrogradación
    deduped = []
    for ev in events:
        if deduped and abs(ev['jd'] - deduped[-1]['jd']) < 0.5 \
                and ev['transit_planet'] == deduped[-1]['transit_planet'] \
                and ev['natal_planet'] == deduped[-1]['natal_planet'] \
                and ev['aspect_angle'] == deduped[-1]['aspect_angle']:
            continue
        deduped.append(ev)
    return deduped


# ============================================================
# MAIN ENDPOINT
# ============================================================
@app.get("/")
def root():
    return {
        "service": "Astro Transits API",
        "version": "4.0",
        "engine": "Swiss Ephemeris (pyswisseph 2.10) — Moshier ephemeris",
        "house_system": "Placidus",
        "zodiac": "Tropical",
        "frame": "Geocentric",
        "transit_planets": TRANSIT_PLANETS,
        "additional_points": ["chiron", "true_node", "south_node", "lilith", "fortuna", "infortunio"],
        "validated_against": "Solar Fire v9.1.0 (≤ 1' arc precision)"
    }


@app.post("/calculate")
def calculate_chart(birth: BirthData):
    try:
        # Asegurar que el path de efemérides esté configurado en cada llamada
        # (necesario porque pyswisseph puede resetear el path internamente)
        if _os.path.isdir(_ephe_dir):
            swe.set_ephe_path(_ephe_dir)

        jd_birth, tz_label = get_julian_day_ut(birth)

        # 1. Posiciones natales
        natal_planets = {}
        for name, pid in PLANETS.items():
            natal_planets[name] = calc_planet(jd_birth, pid)

        # 2. Casas
        houses = calc_houses_placidus(jd_birth, birth.latitude, birth.longitude)

        # 3. Asignar casa a planetas y dignidades
        for name in natal_planets:
            p = natal_planets[name]
            p['house'] = get_house_for_longitude(p['longitude'], houses['cusps'])
            sign_idx = int(p['longitude'] / 30) % 12
            p['dignity'] = get_dignity(name, sign_idx)

        # 3b. Calcular puntos adicionales: Quirón, Nodos, Lilith
        natal_extra = {}
        for name, body_id in ADDITIONAL_BODIES.items():
            data = calc_planet(jd_birth, body_id)
            data['house'] = get_house_for_longitude(data['longitude'], houses['cusps'])
            data['dignity'] = None  # No usamos dignidades para estos puntos
            natal_extra[name] = data

        # 3c. Nodo Sur = Nodo Norte + 180°
        south_node_lon = (natal_extra['true_node']['longitude'] + 180) % 360
        natal_extra['south_node'] = {
            'longitude': south_node_lon,
            'latitude': -natal_extra['true_node']['latitude'],
            'distance': natal_extra['true_node']['distance'],
            'speed': natal_extra['true_node']['speed'],
            'retrograde': natal_extra['true_node']['retrograde'],
            'house': get_house_for_longitude(south_node_lon, houses['cusps']),
            'dignity': None
        }

        # 3d. Determinar carta diurna o nocturna
        sun_lon = natal_planets['sun']['longitude']
        moon_lon = natal_planets['moon']['longitude']
        diurnal = is_diurnal_chart(sun_lon, houses['asc'], houses['mc'])

        # 3e. Calcular Partes Árabes
        # Fortuna: usa Sol y Luna con fórmula diurna/nocturna
        # Infortunio: ASC + Marte - Saturno (fórmula única, sin variante diurna/nocturna)
        mars_lon = natal_planets['mars']['longitude']
        saturn_lon = natal_planets['saturn']['longitude']
        fortuna_lon = calc_part_of_fortune(houses['asc'], sun_lon, moon_lon, diurnal)
        infortunio_lon = calc_part_of_misfortune(houses['asc'], mars_lon, saturn_lon)

        natal_extra['fortuna'] = {
            'longitude': fortuna_lon,
            'latitude': 0, 'distance': 0, 'speed': 0, 'retrograde': False,
            'house': get_house_for_longitude(fortuna_lon, houses['cusps']),
            'dignity': None
        }
        natal_extra['infortunio'] = {
            'longitude': infortunio_lon,
            'latitude': 0, 'distance': 0, 'speed': 0, 'retrograde': False,
            'house': get_house_for_longitude(infortunio_lon, houses['cusps']),
            'dignity': None
        }

        # 4. Agregar ASC, MC, y los puntos que generan aspectos al diccionario para aspectos natales
        natal_full = dict(natal_planets)
        natal_full['asc'] = {'longitude': houses['asc']}
        natal_full['mc'] = {'longitude': houses['mc']}
        # Solo añadir puntos que generan aspectos
        for ap in ASPECT_FORMING_POINTS:
            if ap in natal_extra:
                natal_full[ap] = {'longitude': natal_extra[ap]['longitude']}

        # 5. Aspectos entre planetas natales
        natal_aspects = calculate_natal_aspects(natal_full)

        # 6. Posiciones actuales de los 5 lentos
        now_utc = datetime.utcnow()
        jd_now = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                            now_utc.hour + now_utc.minute/60 + now_utc.second/3600)

        transits_now = {}
        for tp in TRANSIT_PLANETS:
            data = calc_planet(jd_now, PLANETS[tp])
            data['house_in_natal'] = get_house_for_longitude(data['longitude'], houses['cusps'])

            # Dual reading: el signo donde está el tránsito puede regir otra casa natal.
            # Buscar qué casa(s) natal(es) tienen su cúspide en ese signo
            transit_sign_idx = int(data['longitude'] / 30) % 12
            ruled_houses = []
            for h_idx, cusp_lon in enumerate(houses['cusps']):
                cusp_sign = int(cusp_lon / 30) % 12
                if cusp_sign == transit_sign_idx:
                    ruled_houses.append(h_idx + 1)
            data['sign_rules_houses'] = ruled_houses
            data['sign_index'] = transit_sign_idx

            transits_now[tp] = data

        # 7. Aspectos de cada tránsito a planetas natales (incluye ASC, MC)
        transit_aspects = {}
        for tp, tp_data in transits_now.items():
            asps = []
            for natal_name, natal_data in natal_full.items():
                asp = detect_aspect_transit(tp_data['longitude'], natal_data['longitude'])
                if asp:
                    asps.append({
                        'natal_planet': natal_name,
                        'natal_longitude': natal_data['longitude'],
                        'aspect': asp
                    })
            asps.sort(key=lambda x: x['aspect']['orb'])
            transit_aspects[tp] = asps

        # 8. Calendario 12 meses para el planeta seleccionado (transit_planet)
        # Solo para el planeta priorizado, no todos (sería pesado)
        focus_planet = birth.transit_planet if birth.transit_planet in TRANSIT_PLANETS else 'uranus'
        jd_start = jd_now
        jd_end = jd_now + 365  # 12 meses
        focus_planet_id = PLANETS[focus_planet]

        focus_calendar = []
        for natal_name in natal_full:
            natal_lon = natal_full[natal_name]['longitude']
            for asp in ASPECT_TYPES:
                targets = [asp['angle']] if asp['angle'] in (0, 180) else [asp['angle'], -asp['angle']]
                for tgt in targets:
                    dates_jd = find_exact_aspect_dates(focus_planet_id, natal_lon, tgt, jd_start, jd_end)
                    for jd_exact in dates_jd:
                        focus_calendar.append({
                            'jd': jd_exact,
                            'date': jd_to_iso_date(jd_exact),
                            'natal_planet': natal_name,
                            'aspect_es': asp['name_es'],
                            'aspect_en': asp['name_en'],
                            'aspect_glyph': asp['glyph'],
                            'aspect_angle': asp['angle']
                        })

        focus_calendar.sort(key=lambda x: x['jd'])
        # Dedup
        deduped_cal = []
        for ev in focus_calendar:
            if deduped_cal and abs(ev['jd'] - deduped_cal[-1]['jd']) < 0.5 \
                    and ev['natal_planet'] == deduped_cal[-1]['natal_planet'] \
                    and ev['aspect_angle'] == deduped_cal[-1]['aspect_angle']:
                continue
            deduped_cal.append(ev)

        # 9. Format response
        natal_planets_formatted = {}
        for name, data in natal_planets.items():
            pos = format_position(data['longitude'])
            natal_planets_formatted[name] = {
                **pos,
                'retrograde': data['retrograde'],
                'speed': data['speed'],
                'house': data['house'],
                'dignity': data['dignity']
            }

        cusps_formatted = []
        for i, c in enumerate(houses['cusps']):
            pos = format_position(c)
            ruler = get_house_ruler(c)
            ruler_data = natal_planets[ruler] if ruler in natal_planets else None
            cusps_formatted.append({
                **pos,
                'house_number': i + 1,
                'ruler': ruler,
                'ruler_house': ruler_data['house'] if ruler_data else None,
                'ruler_sign': format_position(ruler_data['longitude'])['sign'] if ruler_data else None
            })

        transits_formatted = {}
        for tp, data in transits_now.items():
            transits_formatted[tp] = {
                **format_position(data['longitude']),
                'retrograde': data['retrograde'],
                'house_in_natal': data['house_in_natal'],
                'sign_rules_houses': data.get('sign_rules_houses', []),
                'sign_index': data.get('sign_index', 0)
            }

        # Format extra points (Quirón, Nodos, Lilith, Partes Árabes)
        extras_formatted = {}
        for name, data in natal_extra.items():
            pos = format_position(data['longitude'])
            extras_formatted[name] = {
                **pos,
                'retrograde': data.get('retrograde', False),
                'house': data['house'],
                'dignity': data.get('dignity'),
                'forms_aspects': name in ASPECT_FORMING_POINTS
            }

        return {
            'birth_data': {
                'name': birth.name,
                'datetime': f"{birth.year}-{birth.month:02d}-{birth.day:02d} {birth.hour:02d}:{birth.minute:02d}",
                'latitude': birth.latitude,
                'longitude': birth.longitude,
                'city': birth.city_name,
                'timezone': tz_label,
                'use_lmt': birth.use_lmt,
                'julian_day_ut': jd_birth,
                'is_diurnal': diurnal
            },
            'natal_chart': {
                'planets': natal_planets_formatted,
                'extras': extras_formatted,
                'asc': format_position(houses['asc']),
                'mc': format_position(houses['mc']),
                'houses': cusps_formatted,
                'aspects': natal_aspects
            },
            'transits': {
                'datetime_utc': now_utc.isoformat() + 'Z',
                'positions': transits_formatted,
                'aspects': transit_aspects,
                'focus_planet': focus_planet
            },
            'calendar_12mo': {
                'focus_planet': focus_planet,
                'events': deduped_cal
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

# ============================================================
# ENDPOINTS DE INTERPRETACIONES
# ============================================================
@app.get("/interpretation/{clave}")
def get_interpretation(clave: str, lang: str = IDIOMA_POR_DEFECTO):
    """Obtener una interpretación por clave (ej: sol_libra, luna_casa_7, aspectos_sol_luna).
    Parámetro opcional ?lang=es|en"""
    texto, idioma_real = obtener_texto(clave, lang)
    if texto is None:
        raise HTTPException(status_code=404, detail=f"Interpretación no encontrada: {clave}")
    return {"clave": clave, "idioma": idioma_real, "texto": texto}


@app.get("/interpretations/info")
def interpretations_info(lang: str = IDIOMA_POR_DEFECTO):
    """Estadísticas de la biblioteca interpretativa. Parámetro opcional ?lang=es|en"""
    import re
    lang = normalizar_idioma(lang)
    claves = list(INTERPRETACIONES_POR_IDIOMA.get(lang, {}).keys())
    return {
        "idioma": lang,
        "idiomas_disponibles": IDIOMAS_DISPONIBLES,
        "conteo_por_idioma": {k: len(v) for k, v in INTERPRETACIONES_POR_IDIOMA.items()},
        "total": len(claves),
        "planetas_en_casas": len([k for k in claves if re.search(r'^(sol|luna|mercurio|venus|marte|jupiter|saturno|urano|neptuno|pluton|quiron)_casa_\d+$', k)]),
        "planetas_en_signos": len([k for k in claves if re.match(r'^(sol|luna|mercurio|venus|marte|jupiter|saturno|urano|neptuno|pluton|quiron)_(aries|tauro|geminis|cancer|leo|virgo|libra|escorpio|sagitario|capricornio|acuario|piscis)$', k)]),
        "ascendentes": len([k for k in claves if k.startswith('ascendente_')]),
        "nodos_signos": len([k for k in claves if re.match(r'^nodo_(norte|sur)_(?!casa_)', k)]),
        "nodos_casas": len([k for k in claves if re.match(r'^nodo_(norte|sur)_casa_\d+$', k)]),
        "puentes_nodales": len([k for k in claves if k.startswith('puente_nn_')]),
        "fortuna": len([k for k in claves if k.startswith('fortuna_')]),
        "aspectos": len([k for k in claves if k.startswith('aspectos_')])
    }


@app.post("/interpret-chart")
def interpret_chart(birth: BirthData, lang: str = IDIOMA_POR_DEFECTO):
    """Calcula la carta natal y devuelve todas las interpretaciones aplicables.
    Parámetro opcional ?lang=es|en"""
    chart_data = calculate_chart(birth)
    lang = normalizar_idioma(lang)
    interpretaciones = obtener_interpretaciones_carta(chart_data['natal_chart'], lang)

    return {
        "birth_data": chart_data['birth_data'],
        "natal_chart": chart_data['natal_chart'],
        "idioma": lang,
        "interpretaciones": {
            "total": len(interpretaciones),
            "textos": interpretaciones
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)

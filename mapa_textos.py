# -*- coding: utf-8 -*-
"""Los textos del informe del mapa, en español y en inglés.

Los 65 textos largos —las ocho entradas de segmento, las treinta y seis
líneas, los veinte cruces y la nota de cierre— están en los dos archivos
.json, que son los mismos que se revisaron y aprobaron.

Acá sólo van los rótulos cortos: los nombres de los segmentos, de los
ángulos y de los planetas, y las frases fijas del informe.
"""
import io, json, os

AQUI = os.path.dirname(os.path.abspath(__file__))

_LARGOS = {}


def largos(lang):
    """Los 65 textos. Se cargan una sola vez y quedan en memoria."""
    lang = 'en' if str(lang).lower().startswith('en') else 'es'
    if lang not in _LARGOS:
        _LARGOS[lang] = json.load(io.open(
            os.path.join(AQUI, 'mapa_textos_%s.json' % lang), encoding='utf-8'))
    return _LARGOS[lang]


# ── el orden en que van los segmentos en el informe ──
ORDEN_SEG = ['amor', 'vocacion', 'familia', 'imaginacion', 'emocion',
             'educacion', 'enfoque', 'retos']
ORDEN_ANG = ['asc', 'mc', 'desc', 'ic']

SEG = {
    'es': {'amor': 'Amor y Romance', 'vocacion': 'Vocación y Oportunidades',
           'familia': 'Amistad y Familia', 'imaginacion': 'Imaginación e Inspiración',
           'emocion': 'Emoción e Inestabilidad', 'educacion': 'Educación y Comunicación',
           'enfoque': 'Responsabilidad y Enfoque', 'retos': 'Retos y Riesgos'},
    'en': {'amor': 'Love and Romance', 'vocacion': 'Career and Opportunity',
           'familia': 'Friendship and Family', 'imaginacion': 'Imagination and Inspiration',
           'emocion': 'Emotion and Instability', 'educacion': 'Education and Communication',
           'enfoque': 'Responsibility and Focus', 'retos': 'Challenges and Risks'},
}

# nombre llano · tema · nombre técnico
ANG = {
    'es': {
        'asc':  ('Donde se te nota', 'Tu personalidad', 'Ascendente'),
        'mc':   ('Donde te lo reconocen', 'Tu éxito', 'Medio Cielo'),
        'desc': ('Donde te llega por otros', 'Tus relaciones con otras personas',
                 'Descendente'),
        'ic':   ('Donde lo vives puertas adentro', 'La familia, el hogar, las bases',
                 'Bajo Cielo'),
    },
    'en': {
        'asc':  ('Where people notice you', 'Your personality', 'Ascendant'),
        'mc':   ('Where you get recognized', 'Your success', 'Midheaven'),
        'desc': ('Where it comes through others', 'Your relationships with other people',
                 'Descendant'),
        'ic':   ('Where you live it behind closed doors', 'Family, home and foundations',
                 'Imum Coeli'),
    },
}

NOM = {
    'es': {'sol': 'Sol', 'luna': 'Luna', 'mercurio': 'Mercurio', 'venus': 'Venus',
           'marte': 'Marte', 'jupiter': 'Júpiter', 'saturno': 'Saturno',
           'urano': 'Urano', 'neptuno': 'Neptuno', 'pluton': 'Plutón',
           'quiron': 'Quirón', 'lilith': 'Lilith',
           'nodo_n': 'Nodo Norte', 'nodo_s': 'Nodo Sur'},
    'en': {'sol': 'Sun', 'luna': 'Moon', 'mercurio': 'Mercury', 'venus': 'Venus',
           'marte': 'Mars', 'jupiter': 'Jupiter', 'saturno': 'Saturn',
           'urano': 'Uranus', 'neptuno': 'Neptune', 'pluton': 'Pluto',
           'quiron': 'Chiron', 'lilith': 'Lilith',
           'nodo_n': 'North Node', 'nodo_s': 'South Node'},
}

# Qué planeta manda en cada segmento, para el rótulo bajo el título.
CUERPO_SEG = {
    'es': {'amor': 'Venus', 'vocacion': 'Júpiter', 'familia': 'Luna',
           'imaginacion': 'Neptuno', 'emocion': 'Urano', 'educacion': 'Mercurio',
           'enfoque': 'Saturno', 'retos': 'Marte, Saturno y Plutón'},
    'en': {'amor': 'Venus', 'vocacion': 'Jupiter', 'familia': 'Moon',
           'imaginacion': 'Neptune', 'emocion': 'Uranus', 'educacion': 'Mercury',
           'enfoque': 'Saturn', 'retos': 'Mars, Saturn and Pluto'},
}

MESES = {
    'es': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
           'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July',
           'August', 'September', 'October', 'November', 'December'],
}

# ── las frases fijas del informe ──
FIJO = {
 'es': {
  'rotulo_portada': 'TU MAPA NATAL EN EL MAPA MUNDIAL',
  'titular_portada': 'Dónde, en la Tierra, se te activa cada planeta',
  'entrada_portada': 'En el instante en el que naces, la posición de cada planeta '
      'se hace visible, trasladando dicha posición zodiacal a una posición sobre '
      'la Tierra en una de las cuatro esquinas del cielo.',
  'cita_portada': 'Todo en el **universo** es **vibración**. Si quieres conocer tu '
      'realidad interna y externa, conoce tu carta astral natal y verás cómo se '
      'aclara el camino de vida.',
  'datos_nacimiento': 'DATOS DE NACIMIENTO',
  'firma': 'Ricardo Puerta Isaza · arquitecto & astrólogo',

  'indice': 'Índice',
  'indice_titulo': 'Lo que vas a encontrar',
  'indice_entrada': 'Este mapa se lee con calma. No hace falta seguirlo en orden: '
      'puedes entrar por el segmento que te llame, o por tu ciudad.',

  'como_rotulo': 'Cómo se lee',
  'como_titulo': 'Las cuatro esquinas del cielo',
  'como_1': 'Cada planeta de tu carta deja cuatro rastros sobre la Tierra. Son los '
      'lugares donde, en el instante exacto de tu nacimiento, ese planeta estaba en '
      'una de las cuatro esquinas del cielo: saliendo por el oriente, en lo más '
      'alto, ocultándose por el occidente, o en el punto más bajo, bajo tus pies.',
  'como_2': 'No es una metáfora. Si hubieras nacido en un punto exacto de la línea '
      'de Venus del Medio Cielo, Venus estaría en el grado exacto de tu Medio '
      'Cielo. La línea es el conjunto de todos esos puntos.',
  'como_asc': 'El planeta asomaba por el oriente. Es lo que se te ve: cómo te '
      'presentas, qué proyectas, qué notan los demás en ti sin que tengas que decirlo.',
  'como_mc': 'El planeta estaba en lo más alto del cielo. Es lo que te reconocen: '
      'la carrera, el oficio, la reputación, aquello por lo que te ven.',
  'como_desc': 'El planeta se ocultaba por el occidente. Es lo que te llega a través '
      'de otros: la pareja, los socios, los aliados, los adversarios.',
  'como_ic': 'El planeta estaba en el punto más bajo, bajo tus pies. Es lo que vives '
      'puertas adentro: la casa, la familia, las raíces, el linaje y lo que viene de atrás.',
  'rectas_rotulo': 'Las dos rectas y las dos curvas',
  'rectas': 'Las líneas del Medio Cielo y del Bajo Cielo salen rectas y verticales: '
      'son meridianos, la misma hora en todo el mundo. Las del Ascendente y el '
      'Descendente salen curvas, porque el horizonte depende de la latitud y al '
      'aplanar la Tierra sobre un papel esa curva aparece. No es un adorno del '
      'dibujo: es la forma que tiene.',
  'radio_rotulo': 'El radio',
  'radio': 'Una línea no es un hilo: es una franja. En este informe se considera '
      'activo todo lo que esté a 300 km o menos de la línea, a lado y lado. No hay '
      'un número único y cada escuela usa el suyo; 300 km es una medida prudente.',

  'mapa_rotulo': 'Tu mapa',
  'mapa_titulo': 'Las catorce líneas, sobre el mundo',
  'mapa_pie': 'Continua: Medio Cielo y Ascendente · punteada: Bajo Cielo y '
      'Descendente. Proyección equirectangular, la misma de Solar Maps.',

  'cuatro_lineas': 'Las cuatro líneas',
  'los_cruces': 'Los cruces',
  'curva': 'curva',
  'con': 'con',

  'ciudades_rotulo': 'Tus ciudades',
  'ciudades_titulo': 'Qué tienes activo en cada lugar',
  'ciudades_entrada': 'Setenta y tres ciudades, con lo que tienes activo en cada una '
      'a 300 km o menos. Si tu ciudad no está, la distancia se mide igual: lo que '
      'cuenta es la distancia a la línea, no el nombre del lugar.',
  'ciudades_vacio': 'En ninguna de las setenta y tres ciudades de la lista tienes una '
      'línea a 300 km o menos. No es un error ni una carta rara: tus líneas pasan por '
      'otros lugares, y el mapa de la página anterior te muestra por dónde.',

  'cierre_rotulo': 'Para cerrar',
  'cita_boton': 'Pedir una cita',
  'cita_url': 'https://ricardopuerta.com/consulta.html',
  'cita_enlace': 'ricardopuerta.com/consulta.html',

  'donde_activa': 'Dónde se te activa',
  'donde_activa_intro': 'Las ciudades de la lista donde tienes una de estas '
      'líneas a 300 km o menos. Si tu ciudad no está, la distancia se mide '
      'igual: lo que cuenta es la distancia a la línea, no el nombre del lugar.',
  'donde_activa_vacio': 'Ninguna de las setenta y tres ciudades de la lista '
      'te queda a 300 km o menos de estas líneas. No es un error ni una carta '
      'rara: estas líneas tuyas pasan por otras zonas, y el mapa de arriba te '
      'muestra por dónde.',
  'tambien_aqui': 'y además, acá mismo',
  'se_cruzan_en': 'Se cruzan a',
  'y': 'y',
  'mapa_seg_pie': 'Continua: Medio Cielo y Ascendente · punteada: Bajo Cielo y '
      'Descendente. Las líneas más finas son las de los planetas con los que '
      'se cruza.',
  'pdf_nombre': 'Astromapa - ',
 },
 'en': {
  'rotulo_portada': 'YOUR BIRTH CHART ON THE WORLD MAP',
  'titular_portada': 'Where on Earth each of your planets comes alive',
  'entrada_portada': 'At the moment you are born, the position of each planet becomes '
      'visible, carrying that zodiacal position across to a position on Earth at one '
      'of the four corners of the sky.',
  'cita_portada': 'Everything in the **universe** is **vibration**. If you want to '
      'know your inner and outer reality, get to know your natal chart and you will '
      'see your path in life come clear.',
  'datos_nacimiento': 'BIRTH DATA',
  'firma': 'Ricardo Puerta Isaza · architect & astrologer',

  'indice': 'Contents',
  'indice_titulo': "What you'll find here",
  'indice_entrada': 'This map is meant to be read slowly. You do not have to follow '
      'it in order: start with whichever segment calls you, or with your own city.',

  'como_rotulo': 'How to read it',
  'como_titulo': 'The four corners of the sky',
  'como_1': 'Every planet in your chart leaves four tracks across the Earth. They are '
      'the places where, at the exact moment of your birth, that planet stood at one '
      'of the four corners of the sky: rising in the east, at the very top, setting '
      'in the west, or at the lowest point, beneath your feet.',
  'como_2': 'This is not a metaphor. Had you been born at an exact point on the Venus '
      'Midheaven line, Venus would sit at the exact degree of your Midheaven. The '
      'line is the set of all those points.',
  'como_asc': 'The planet was rising in the east. It is what shows: how you come '
      'across, what you project, what others notice in you without your saying it.',
  'como_mc': 'The planet stood at the very top of the sky. It is what you get '
      'recognized for: the career, the craft, the reputation, what people see you by.',
  'como_desc': 'The planet was setting in the west. It is what reaches you through '
      'other people: the partner, the associates, the allies, the adversaries.',
  'como_ic': 'The planet was at its lowest point, beneath your feet. It is what you '
      'live behind closed doors: home, family, roots, lineage and what comes from before.',
  'rectas_rotulo': 'The two straight lines and the two curves',
  'rectas': 'The Midheaven and Imum Coeli lines come out straight and vertical: they '
      'are meridians, the same hour the world over. The Ascendant and Descendant '
      'lines come out curved, because the horizon depends on latitude, and flattening '
      'the Earth onto paper is what makes that curve appear. It is not a flourish of '
      'the drawing: it is the shape the thing has.',
  'radio_rotulo': 'The radius',
  'radio': 'A line is not a thread: it is a band. In this report anything within 300 '
      'km of the line, on either side, counts as active. There is no single number '
      'and every school uses its own; 300 km is a conservative measure.',

  'mapa_rotulo': 'Your map',
  'mapa_titulo': 'The fourteen lines, across the world',
  'mapa_pie': 'Solid: Midheaven and Ascendant · dashed: Imum Coeli and Descendant. '
      'Equirectangular projection, the same one Solar Maps uses.',

  'cuatro_lineas': 'The four lines',
  'los_cruces': 'The crossings',
  'curva': 'curve',
  'con': 'with',

  'ciudades_rotulo': 'Your cities',
  'ciudades_titulo': "What's active for you in each place",
  'ciudades_entrada': 'Seventy-three cities, with what you have active in each one '
      'within 300 km. If your city is not here, the distance is measured the same '
      'way: what counts is the distance to the line, not the name of the place.',
  'ciudades_vacio': 'In none of the seventy-three cities on the list do you have a '
      'line within 300 km. This is not an error, nor an odd chart: your lines run '
      'through other places, and the map on the previous page shows you where.',

  'cierre_rotulo': 'To close',
  'cita_boton': 'Book a consultation',
  'cita_url': 'https://ricardopuerta.com/en/consultation.html',
  'cita_enlace': 'ricardopuerta.com/en/consultation.html',

  'donde_activa': "Where it's active for you",
  'donde_activa_intro': 'The cities on the list where one of these lines runs '
      'within 300 km of you. If your city is not here, the distance is measured '
      'the same way: what counts is the distance to the line, not the name of '
      'the place.',
  'donde_activa_vacio': 'None of the seventy-three cities on the list falls '
      'within 300 km of these lines. This is not an error, nor an odd chart: '
      'these lines of yours run through other regions, and the map above shows '
      'you where.',
  'tambien_aqui': 'and also, right here',
  'se_cruzan_en': 'They cross at',
  'y': 'and',
  'mapa_seg_pie': 'Solid: Midheaven and Ascendant · dashed: Imum Coeli and '
      'Descendant. The thinner lines belong to the planets it crosses with.',
  'pdf_nombre': 'Astromap - ',
 },
}


def fijo(lang, clave):
    return FIJO['en' if str(lang).lower().startswith('en') else 'es'][clave]

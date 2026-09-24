// ============================================================
// LAS EDADES ZODIACALES
// Los años en los que a todos nos pasa lo mismo.
// Textos: Ricardo Puerta Isaza
// ============================================================

// 'gratis'   = la persona solo lee la edad que está viviendo hoy.
// 'completo' = puede abrir las 23 edades (versión del informe pagado).
const EDADES_MODO = 'gratis';

const EDADES_ZODIACALES = [
  {
    "min": 7,
    "max": 8,
    "es": {
      "titulo": "SE ACABÓ EL PARAÍSO",
      "pasa": "Hasta aquí te cuidaron. Desde aquí te evalúan. Es la primera vez que el mundo te pone un límite que no puso tu mamá: la maestra, la nota, la fila, el turno. También es la primera vez que entiendes que hay consecuencias, y que no todas son justas.",
      "spoiler": "A los siete años dejas de ser el dueño del Olimpo y pasas a ser uno más de la clase. Nadie te avisa. Simplemente un día ya no te aplauden por existir.",
      "retos": [
        "La timidez, o su contrario: volverse el que molesta para que lo vean.",
        "El miedo a equivocarse delante de otros.",
        "Los primeros «no» que no se pueden negociar llorando."
      ],
      "trabajar": "Aquí se aprende que el límite no es un castigo: es la forma del mundo. Si un niño aprende eso con cariño, de adulto trabaja sin sentirse perseguido. Si lo aprende con humillación, de adulto le teme a toda autoridad. Si estás leyendo esto y ya eres grande, mira qué te pasa hoy cuando alguien te corrige. Ahí sigue viviendo el niño de siete."
    },
    "en": {
      "titulo": "PARADISE IS OVER",
      "pasa": "Until now you were cared for. From here on you are assessed. It is the first time the world sets a limit your mother did not set: the teacher, the grade, the line, your turn. It is also the first time you understand that there are consequences, and that not all of them are fair.",
      "spoiler": "At seven you stop being the owner of Olympus and become one more child in the classroom. Nobody warns you. One day they simply stop applauding you for existing.",
      "retos": [
        "Shyness, or its opposite: becoming the one who acts up to be seen.",
        "The fear of being wrong in front of others.",
        "The first “no” that crying cannot negotiate."
      ],
      "trabajar": "Here you learn that a limit is not a punishment: it is the shape of the world. A child who learns that with affection works as an adult without feeling persecuted. A child who learns it through humiliation fears every authority later on. If you are grown up as you read this, notice what happens to you today when someone corrects you. That seven-year-old still lives there."
    }
  },
  {
    "min": 9,
    "max": 10,
    "es": {
      "titulo": "LA VIDA ESTÁ AFUERA",
      "pasa": "Por primera vez lo de afuera pesa más que lo de adentro. Los amigos valen más que los hermanos, la opinión del curso vale más que la de la casa, y empiezas a mirarte en el espejo para ver qué opinan los demás de ti.",
      "spoiler": "A esta edad descubres que puedes culpar a otro de lo que te pasa. Y descubres que se siente rico. Muchos adultos nunca dejan de hacerlo.",
      "retos": [
        "Compararse: el cuerpo, la ropa, la casa, los papás.",
        "Formar grupo excluyendo a alguien, o quedar afuera del grupo.",
        "Guardar rencor por primera vez, y no soltarlo."
      ],
      "trabajar": "Es la edad en la que se aprende a pertenecer sin desaparecer. Vale la pena mirar de dónde viene tu manera de buscar aprobación: casi siempre se armó aquí. Y vale la pena revisar a quién no has perdonado desde que eras niño."
    },
    "en": {
      "titulo": "LIFE IS OUTSIDE",
      "pasa": "For the first time what is outside weighs more than what is inside. Friends matter more than siblings, the opinion of the class matters more than the one at home, and you start looking in the mirror to see what others think of you.",
      "spoiler": "At this age you discover you can blame someone else for what happens to you. And you discover it feels good. Many adults never stop doing it.",
      "retos": [
        "Comparing: the body, the clothes, the house, the parents.",
        "Forming a group by leaving someone out, or being the one left out.",
        "Holding a grudge for the first time, and not letting it go."
      ],
      "trabajar": "This is the age when you learn to belong without disappearing. It is worth looking at where your way of seeking approval comes from: it was almost always built here. And it is worth reviewing who you have not forgiven since you were a child."
    }
  },
  {
    "min": 12,
    "max": 12,
    "es": {
      "titulo": "TE CRECE EL MUNDO",
      "pasa": "Todo se agranda: el cuerpo, las ganas, el atrevimiento, el territorio. Te sientes capaz de cualquier cosa y quieres estar donde están los grandes. Es una edad de suerte y de energía.",
      "spoiler": "Te sientes invencible justo cuando menos criterio tienes. Esa mezcla explica casi todas las cicatrices que tienes en las rodillas y algunas de las otras.",
      "retos": [
        "Excederse: en confianza, en comida, en riesgo, en palabras.",
        "Admirar a la persona equivocada.",
        "Creer que los adultos no entienden nada."
      ],
      "trabajar": "Aquí aparece por primera vez la pregunta de toda la vida: ¿hasta dónde puedo crecer sin romperme? Crecer sirve, pero sin frenos se vuelve daño. Si hoy eres adulto, este es el mismo impulso con el que dices que sí a más cosas de las que puedes sostener."
    },
    "en": {
      "titulo": "YOUR WORLD GROWS",
      "pasa": "Everything expands: the body, the appetite, the daring, the territory. You feel capable of anything and you want to be where the older ones are. It is an age of luck and energy.",
      "spoiler": "You feel invincible exactly when you have the least judgement. That mix explains almost every scar on your knees, and a few of the others.",
      "retos": [
        "Overdoing it: in confidence, in food, in risk, in words.",
        "Admiring the wrong person.",
        "Believing adults understand nothing."
      ],
      "trabajar": "Here the question of a lifetime appears for the first time: how far can I grow without breaking? Growth is good, but with no brakes it turns into damage. If you are an adult today, this is the same impulse that makes you say yes to more than you can carry."
    }
  },
  {
    "min": 14,
    "max": 14,
    "es": {
      "titulo": "EL PESO",
      "pasa": "El cuerpo cambia y la exigencia llega toda junta: rendir, encajar, gustar, decidir qué vas a estudiar. Es la edad en la que muchos descubren que la vida pesa.",
      "spoiler": "A los catorce años no te está pasando nada raro: te está pasando lo que le pasa a todo el mundo. Lo raro es que nadie te lo explique y que todos finjan que es una etapa feliz.",
      "retos": [
        "La inseguridad y la comparación permanente.",
        "La primera tristeza de verdad, la que no se quita con un helado.",
        "Los amigos que te llevan a lo que tú no eres."
      ],
      "trabajar": "Esta edad no se supera: se atraviesa. Lo que se trabaja aquí es la confianza propia, y se trabaja despacio. A los padres les toca estar, no salvar. Y si eres tú quien lo está recordando, mira qué frase sobre ti te creíste a los catorce. Probablemente todavía te la repites."
    },
    "en": {
      "titulo": "THE WEIGHT",
      "pasa": "The body changes and every demand arrives at once: perform, fit in, be liked, decide what to study. It is the age when many discover that life is heavy.",
      "spoiler": "At fourteen nothing strange is happening to you: what is happening happens to everyone. What is strange is that nobody explains it and everyone pretends it is a happy stage.",
      "retos": [
        "Insecurity and constant comparison.",
        "The first real sadness, the kind ice cream does not fix.",
        "Friends who pull you toward what you are not."
      ],
      "trabajar": "This age is not overcome: it is crossed. What is worked on here is self-confidence, and it is worked on slowly. Parents are meant to be there, not to rescue. And if you are the one remembering it, look at which sentence about yourself you believed at fourteen. You probably still repeat it."
    }
  },
  {
    "min": 15,
    "max": 16,
    "es": {
      "titulo": "EL DESPERTAR",
      "pasa": "Se enciende todo: el primer amor, el deseo, los celos, los secretos. El cuerpo cambia y con él cambia la manera de mirar y de ser mirado. En nuestra cultura, además, es la edad en la que a la niña la presentan en sociedad, justo cuando menos preparada está para lo que esa sociedad le va a proponer.",
      "spoiler": "A los quince uno cree que el primer amor va a durar toda la vida y que la buena suerte también. Ninguna de las dos cosas dura. Lo que sí dura es lo que uno decide sobre sí mismo en esos meses.",
      "retos": [
        "Una intensidad emocional que no cabe en el cuerpo y sale como rabia, llanto o silencio.",
        "El primer secreto grande, el que no se le cuenta a la mamá.",
        "Un embarazo que llega quince años antes de tiempo.",
        "Confundir ser deseado con ser querido."
      ],
      "trabajar": "Se trabaja el manejo del deseo: sentirlo sin que te domine. Es la primera vez que la pasión y los celos entran en escena, y la manera como se viven aquí deja huella en todas las relaciones que vienen. A los padres les toca hablar claro y sin sermón: a esta edad el silencio no protege, expone."
    },
    "en": {
      "titulo": "THE AWAKENING",
      "pasa": "Everything switches on: first love, desire, jealousy, secrets. The body changes and with it the way you look and are looked at. In our culture this is also the age when a girl is presented to society, exactly when she is least prepared for what that society will propose to her.",
      "spoiler": "At fifteen you believe the first love will last a lifetime, and that the good luck will too. Neither one lasts. What does last is what you decide about yourself during those months.",
      "retos": [
        "An emotional intensity that does not fit in the body and comes out as anger, tears or silence.",
        "The first big secret, the one you do not tell your mother.",
        "A pregnancy that arrives fifteen years too early.",
        "Mistaking being desired for being loved."
      ],
      "trabajar": "What is worked on here is handling desire: feeling it without being ruled by it. It is the first time passion and jealousy walk on stage, and the way they are lived here marks every relationship that follows. Parents have to speak plainly and without preaching: at this age silence does not protect, it exposes."
    }
  },
  {
    "min": 18,
    "max": 19,
    "es": {
      "titulo": "EMPIEZA TU HISTORIA",
      "pasa": "Se abre un capítulo nuevo y esta vez lo escribes tú: la carrera, el trabajo, el amor con peso, salir de la casa. Es un comienzo real, no un ensayo.",
      "spoiler": "A los dieciocho tomas, con la información de un niño, decisiones que te van a durar veinte años. Así es para todos. No hay manera de hacerlo bien; hay manera de corregirlo después.",
      "retos": [
        "Elegir carrera por complacer, por moda o por miedo.",
        "Enamorarse del papel que uno quiere representar, no de la persona.",
        "Confundir libertad con no tener que responder por nada."
      ],
      "trabajar": "Se trabaja el rumbo: para dónde vas y por qué. No tiene que quedar perfecto, tiene que ser tuyo. Lo que se elige por complacer a otro se paga más adelante, con intereses, y el cobro llega puntual a los treinta."
    },
    "en": {
      "titulo": "YOUR STORY BEGINS",
      "pasa": "A new chapter opens and this time you write it: the degree, the job, love with weight, leaving home. It is a real beginning, not a rehearsal.",
      "spoiler": "At eighteen you make, with a child's information, decisions that will last twenty years. It is the same for everyone. There is no way to do it right; there is a way to correct it later.",
      "retos": [
        "Choosing a career to please someone, by fashion, or out of fear.",
        "Falling in love with the role you want to play, not with the person.",
        "Mistaking freedom for not having to answer for anything."
      ],
      "trabajar": "What is worked on here is direction: where you are going and why. It does not have to be perfect, it has to be yours. Whatever is chosen to please someone else is paid for later, with interest, and the bill arrives punctually at thirty."
    }
  },
  {
    "min": 21,
    "max": 22,
    "es": {
      "titulo": "DOS FUERZAS AL TIEMPO",
      "pasa": "Una parte tuya quiere hacerse cargo, ser serio, cumplir. La otra quiere mandar todo al diablo e irse lejos. Las dos tienen razón y las dos hablan al mismo tiempo.",
      "spoiler": "A esta edad crees que el problema es tu familia, tu ciudad o tu carrera. Casi siempre el problema es que todavía no sabes quién eres sin ellos.",
      "retos": [
        "Empezar algo grande y abandonarlo apenas se pone difícil.",
        "Pelearse con la casa para poder irse.",
        "Un primer fracaso que se siente como el fin del mundo."
      ],
      "trabajar": "Se trabaja el equilibrio entre compromiso y libertad. No hay que elegir uno de los dos: hay que aprender a sostener los dos. Quien a esta edad solo cumple, se apaga; quien solo se suelta, no construye nada."
    },
    "en": {
      "titulo": "TWO FORCES AT ONCE",
      "pasa": "One part of you wants to take charge, be serious, deliver. The other wants to throw it all away and leave. Both are right and both speak at the same time.",
      "spoiler": "At this age you believe the problem is your family, your city or your career. Almost always the problem is that you do not yet know who you are without them.",
      "retos": [
        "Starting something big and dropping it the moment it gets hard.",
        "Fighting with home in order to leave it.",
        "A first failure that feels like the end of the world."
      ],
      "trabajar": "What is worked on here is the balance between commitment and freedom. You do not have to choose one: you have to learn to hold both. Whoever only complies at this age goes dim; whoever only lets go builds nothing."
    }
  },
  {
    "min": 24,
    "max": 24,
    "es": {
      "titulo": "LA PUERTA SE ABRE",
      "pasa": "Vuelve la confianza y con ella las oportunidades: el grado, el primer trabajo bueno, el viaje, la persona. Es una edad generosa y de expansión.",
      "spoiler": "Todo te sale bien y crees que es por tu talento. Es, sobre todo, porque tienes veinticuatro años y el mundo todavía te está dando crédito.",
      "retos": [
        "Confiarse y dejar de prepararse.",
        "Gastar la energía en muchos frentes y no terminar ninguno.",
        "Decir que sí a todo por miedo a perderse algo."
      ],
      "trabajar": "Se trabaja el criterio: elegir. Esta es la edad para sembrar lo que quieres cosechar a los treinta. Lo que hoy parece una oportunidad más, puede ser el oficio de tu vida, si lo sostienes."
    },
    "en": {
      "titulo": "THE DOOR OPENS",
      "pasa": "Confidence returns and opportunities come with it: the degree, the first good job, the trip, the person. It is a generous age, an age of expansion.",
      "spoiler": "Everything works out and you think it is your talent. It is mostly because you are twenty-four and the world is still giving you credit.",
      "retos": [
        "Getting comfortable and stopping your preparation.",
        "Spending energy on many fronts and finishing none.",
        "Saying yes to everything for fear of missing out."
      ],
      "trabajar": "What is worked on here is judgement: choosing. This is the age to sow what you want to harvest at thirty. What looks today like one more opportunity can be your life's work, if you sustain it."
    }
  },
  {
    "min": 27,
    "max": 28,
    "es": {
      "titulo": "SE MUEVE EL PISO EMOCIONAL",
      "pasa": "Lo que sentías ya no lo sientes igual. Cambia lo que necesitas de una pareja, de tu familia, de tu casa. Muchos se casan o son padres o madres por esta época, y muchos entienden por fin a los suyos.",
      "spoiler": "Tus papás tenían razón en algunas cosas. Duele reconocerlo a los veintisiete, pero es justo cuando pasa.",
      "retos": [
        "Relaciones que se acaban sin pelea, solo porque ya no funcionan.",
        "La sensación de estar atrasado frente a los demás.",
        "Volverse padre o madre sin haber terminado de ser hijo, o empezar un matrimonio."
      ],
      "trabajar": "Se trabaja lo emocional: qué necesitas de verdad y qué estás pidiendo por costumbre. Este es el calentamiento de lo que viene. Se requiere madurar. Lo que no mires ahora, te lo van a mostrar el año entrante, y sin anestesia."
    },
    "en": {
      "titulo": "THE EMOTIONAL GROUND SHIFTS",
      "pasa": "What you used to feel you no longer feel the same way. What you need from a partner, from your family, from your home changes. Many marry or become parents around this time, and many finally understand their own.",
      "spoiler": "Your parents were right about some things. It hurts to admit at twenty-seven, and that is exactly when it happens.",
      "retos": [
        "Relationships that end with no fight, simply because they no longer work.",
        "The feeling of being behind everyone else.",
        "Becoming a parent before you finished being a child."
      ],
      "trabajar": "What is worked on here is the emotional side: what you truly need and what you are asking for out of habit. This is the warm-up for what comes next. Whatever you do not look at now will be shown to you next year, and without anaesthesia."
    }
  },
  {
    "min": 29,
    "max": 30,
    "es": {
      "titulo": "LA CUENTA DE COBRO",
      "pasa": "Es la edad más conocida de todas y la más temida. La vida revisa lo que construiste en tus primeros treinta años y se queda solo con lo que es tuyo de verdad. Lo demás se cae: trabajos, parejas, ciudades, amistades, ideas sobre ti mismo.",
      "spoiler": "No se cae lo que estaba mal hecho. Se cae lo que no era tuyo, aunque funcionara perfecto.",
      "retos": [
        "Separaciones, renuncias, mudanzas, y todo en el mismo año.",
        "El miedo a empezar de nuevo cuando ya «se supone» que uno llegó.",
        "La comparación con los que aparentemente ya lo lograron."
      ],
      "trabajar": "Se trabaja la adultez: responder por lo tuyo sin culpar a nadie. Esta edad no es un castigo, es un inventario, es madurez y responsabilidad. Lo que fortalezcas o estructures aquí te va a sostener a ti los próximos treinta años. Y lo que se cayó, no lo persigas: no era tuyo."
    },
    "en": {
      "titulo": "THE BILL ARRIVES",
      "pasa": "It is the best known age of all and the most feared. Life reviews what you built in your first thirty years and keeps only what is truly yours. The rest falls: jobs, partners, cities, friendships, ideas about yourself. Growing up is required.",
      "spoiler": "What falls is not what was badly done. What falls is what was not yours, even if it worked perfectly.",
      "retos": [
        "Separations, resignations, moves, all in the same year.",
        "The fear of starting over when you were “supposed” to have arrived.",
        "Comparing yourself with those who apparently already made it."
      ],
      "trabajar": "What is worked on here is adulthood: answering for what is yours without blaming anyone. This age is not a punishment, it is an inventory; it is maturity and responsibility. Whatever you strengthen and structure here will hold you up for the next thirty years. And do not chase what fell: it was not yours."
    }
  },
  {
    "min": 33,
    "max": 33,
    "es": {
      "titulo": "LA VUELTA AL PUNTO DE PARTIDA",
      "pasa": "El cielo del día de tu cumpleaños vuelve a ser casi idéntico al del día en que naciste. Es una de las edades más simbólicas que existen: la edad en la que murieron Cristo y Krishna. Algo se cierra y algo se entrega o se abre.",
      "spoiler": "A los treinta y tres uno ya no puede echarle la culpa a la juventud. Lo que hay, uno lo puso ahí.",
      "retos": [
        "Ganas de mandarlo todo al diablo: la casa, la ciudad, el trabajo.",
        "Viejos recuerdos familiares que vuelven sin ser invitados.",
        "La vida privada halando para un lado y la pública para el otro."
      ],
      "trabajar": "Se trabaja devolver, retribuir. A esta edad la vida promueve que entregues algo de lo que recibiste: enseñar, ayudar, sostener a alguien. El que solo acumula en este año se queda vacío en una edad en la que todo estaba a su favor."
    },
    "en": {
      "titulo": "BACK TO THE STARTING POINT",
      "pasa": "The sky on your birthday returns to being almost identical to the sky on the day you were born. It is one of the most symbolic ages there is: the age at which Christ and Krishna died. Something closes and something is handed over, or opens.",
      "spoiler": "At thirty-three you can no longer blame your youth. Whatever is there, you put it there.",
      "retos": [
        "The urge to drop everything: the house, the city, the job.",
        "Old family memories that come back uninvited.",
        "Private life pulling one way and public life the other."
      ],
      "trabajar": "What is worked on here is giving back. At this age life promotes handing over some of what you received: teaching, helping, supporting someone. Whoever only accumulates in this year ends up empty in an age when everything was in their favour."
    }
  },
  {
    "min": 36,
    "max": 37,
    "es": {
      "titulo": "SEGUNDO COMIENZO",
      "pasa": "Vuelve a abrirse el camino, pero ahora con oficio. Un cambio de rumbo, un negocio propio, un hijo, una mudanza, una vocación que aparece tarde y con fuerza.",
      "spoiler": "A los treinta y seis ya no puedes decir que estás empezando. Puedes decir que estás empezando otra vez, que es distinto y cuesta más.",
      "retos": [
        "El vértigo de soltar lo estable, por lo que tiene sentido.",
        "Sentir que se acaba el tiempo, y decidir con afán.",
        "La vida familiar y el trabajo halando para lados contrarios."
      ],
      "trabajar": "Se trabaja el rumbo otra vez, pero con experiencia. Aquí se decide si la segunda mitad de la vida va a parecerse a la primera o no. Es una buena edad para arriesgar, siempre que sepas por qué. Es crecimiento y expansión."
    },
    "en": {
      "titulo": "SECOND BEGINNING",
      "pasa": "The road opens again, but now with craft. A change of direction, your own business, a child, a move, a vocation that shows up late and strong.",
      "spoiler": "At thirty-six you can no longer say you are starting. You can say you are starting again, which is different and costs more.",
      "retos": [
        "The vertigo of letting go of the stable for the meaningful.",
        "Feeling that time is running out, and deciding in a rush.",
        "Family life and work pulling in opposite directions."
      ],
      "trabajar": "What is worked on here is direction again, but with experience. This is where it is decided whether the second half of life will look like the first. It is a good age to take a risk, as long as you know why. It is growth and expansion."
    }
  },
  {
    "min": 39,
    "max": 40,
    "es": {
      "titulo": "¿ESTO ERA TODO?",
      "pasa": "Llega la pregunta por el sentido. No es una crisis ruidosa: es un cansancio raro, una sensación de que la vida se volvió obligación y que algo importante se quedó por fuera.",
      "spoiler": "La pregunta no es «¿qué me falta?». La pregunta es «¿para qué estoy haciendo todo esto?». Y no hay respuesta prestada que te sirva.",
      "retos": [
        "La niebla: no saber qué se quiere, solo que así no.",
        "Buscar la salida en algo que promete salvarte, sea lo que sea.",
        "Desilusionarse de las personas que admirabas."
      ],
      "trabajar": "Se trabaja lo interior: la fe, el arte, el silencio, el sentido. Esta edad quiere que le des lugar a lo que no produce nada. Si no se lo das, se lo toma en forma de escape."
    },
    "en": {
      "titulo": "IS THIS ALL?",
      "pasa": "The question of meaning arrives. It is not a loud crisis: it is a strange tiredness, a sense that life turned into obligation and that something important was left out.",
      "spoiler": "The question is not “what am I missing?”. The question is “what am I doing all this for?”. And no borrowed answer will serve you.",
      "retos": [
        "The fog: not knowing what you want, only that not like this.",
        "Looking for a way out in something that promises to save you, whatever it is.",
        "Becoming disillusioned with the people you admired."
      ],
      "trabajar": "What is worked on here is the inner life: faith, art, silence, meaning. This age wants you to make room for what produces nothing. If you do not give it room, it takes it in the form of escape."
    }
  },
  {
    "min": 41,
    "max": 42,
    "es": {
      "titulo": "EL DESPERTAR",
      "pasa": "Es la mitad de la vida, y se siente. Lo que aguantaste por años deja de aguantarse de un día para otro: un matrimonio, un trabajo, una manera de vivir. Por eso a esta edad la gente cambia de todo.",
      "spoiler": "La mitad de la vida y su crisis existe, tiene nombre y le llega a todo el mundo. Lo único que uno elige es si despierta o si lo rompe todo.",
      "retos": [
        "Confundir libertad con destruir lo que costó veinte años construir.",
        "El cuerpo que avisa por primera vez que tiene límite.",
        "La salud de los padres, entra al escenario."
      ],
      "trabajar": "Se trabaja la diferencia entre cambiar y huir. Hay cosas que de verdad hay que soltar y otras que solo hay que mirar distinto. La actitud. Esta edad es una oportunidad enorme: casi todo el que la aprovecha vive mejor los siguientes cuarenta años."
    },
    "en": {
      "titulo": "THE AWAKENING OF MIDLIFE",
      "pasa": "It is the middle of life and it shows. What you put up with for years suddenly stops being bearable: a marriage, a job, a way of living. That is why people change everything at this age.",
      "spoiler": "Midlife and its crisis are real, they have a name, and they come for everyone. The only thing you choose is whether you wake up or break it all.",
      "retos": [
        "Mistaking freedom for destroying what took twenty years to build.",
        "The body, warning for the first time that it has a limit.",
        "Your parents' health, stepping onto the stage."
      ],
      "trabajar": "What is worked on here is the difference between changing and running away. Some things really do have to be released and others only have to be seen differently. Attitude. This age is an enormous opportunity: almost everyone who uses it well lives the next forty years better."
    }
  },
  {
    "min": 44,
    "max": 45,
    "es": {
      "titulo": "LA MEDIDA",
      "pasa": "Después del remezón viene la medición. ¿Sirve lo que construí para la vida que viene? Los hijos se van, los padres envejecen, la carrera llega a un techo o se reinventa.",
      "spoiler": "Engañar a otro es desagradable. Engañarte a ti mismo a los cuarenta y cinco sale carísimo, y lo pagas en los veinte años siguientes.",
      "retos": [
        "Las insatisfacciones viejas que vuelven todas juntas.",
        "Rehacer la pareja, o terminarla de verdad.",
        "El cansancio, que ya no se arregla durmiendo un fin de semana."
      ],
      "trabajar": "Se trabaja la honestidad con uno mismo. Aquí no funciona el discurso que uno se cuenta; funciona mirar lo que hay. Lo que se ajusta a esta edad se disfruta después."
    },
    "en": {
      "titulo": "THE MEASURE",
      "pasa": "After the shake-up comes the measuring. Does what I built serve the life that is coming? The children leave, the parents age, the career hits a ceiling or reinvents itself.",
      "spoiler": "Deceiving someone else is merely unpleasant. Deceiving yourself at forty-five is very expensive, and you pay for it over the following twenty years.",
      "retos": [
        "Old dissatisfactions that all come back at once.",
        "Rebuilding the relationship, or really ending it.",
        "Tiredness that a weekend of sleep no longer fixes."
      ],
      "trabajar": "What is worked on here is honesty with yourself. The story you tell yourself does not work here; looking at what is actually there does. Whatever is adjusted at this age is enjoyed afterwards."
    }
  },
  {
    "min": 49,
    "max": 51,
    "es": {
      "titulo": "LA HERIDA QUE ENSEÑA",
      "pasa": "Vuelve completo, el tema que te ha dolido toda la vida. Pero no vuelve como dolor nuevo: vuelve como conocimiento. Lo que aprendiste sufriéndolo ahora le sirve a otros.",
      "spoiler": "Eso que crees que es tu defecto más grande es, casi siempre, tu oficio. Lo malo es que para saberlo hay que llegar a los cincuenta.",
      "retos": [
        "Quedarse en la queja: la herida vuelta identidad.",
        "Curar a todo el mundo menos a uno mismo.",
        "Sentirse viejo y joven el mismo día, varias veces al día."
      ],
      "trabajar": "Se trabaja la sanación, y sanar aquí es enseñar. Esta edad promueve que pases de vivir tu historia a poder acompañar a otros con ella. Es la edad en la que mucha gente encuentra, por fin, para qué sirvió todo lo que le pasó."
    },
    "en": {
      "titulo": "THE WOUND THAT TEACHES",
      "pasa": "The theme that has hurt you all your life comes back, complete. But it does not come back as new pain: it comes back as knowledge. What you learned by suffering it is now useful to others.",
      "spoiler": "What you believe is your greatest flaw is, almost always, your craft. The bad news is that you have to reach fifty to find out.",
      "retos": [
        "Staying in the complaint: the wound turned into identity.",
        "Healing everyone except yourself.",
        "Feeling old and young on the same day, several times a day."
      ],
      "trabajar": "What is worked on here is healing, and healing here means teaching. This age promotes moving from living your story to being able to accompany someone else with it. It is the age when many people finally find out what everything that happened to them was for."
    }
  },
  {
    "min": 54,
    "max": 56,
    "es": {
      "titulo": "OTRA VEZ EL RUMBO",
      "pasa": "Se vuelve a abrir la pregunta por el camino, pero ahora con toda la vida a favor. Aparecen vocaciones tardías, nuevos grupos, un modo de vivir más propio y menos negociado.",
      "spoiler": "Es la última vez que la vida te pregunta qué quieres hacer con ella ofreciéndote tiempo de verdad. Después pregunta con menos paciencia.",
      "retos": [
        "Creer que ya es tarde, que es la excusa más cómoda del mundo.",
        "Los amigos que se van quedando en el camino.",
        "El cuerpo, que pide otro ritmo y no admite discusión."
      ],
      "trabajar": "Se trabaja soltar lo viejo para que quepa lo nuevo: cargos, rencores, costumbres, gente. Lo que sueltes aquí te devuelve energía, y a esta edad la energía es el mayor patrimonio."
    },
    "en": {
      "titulo": "DIRECTION, ONCE AGAIN",
      "pasa": "The question of the road opens again, but now with a whole life in your favour. Late vocations appear, new circles, a way of living that is more your own and less negotiated.",
      "spoiler": "It is the last time life asks you what you want to do with it while still offering you real time. After this it asks with less patience.",
      "retos": [
        "Believing it is too late, the most comfortable excuse in the world.",
        "Friends who stay behind along the way.",
        "The body, which asks for another rhythm and takes no argument."
      ],
      "trabajar": "What is worked on here is letting go of the old so the new fits: positions, resentments, habits, people. Whatever you release here gives you energy back, and at this age energy is the estate."
    }
  },
  {
    "min": 58,
    "max": 60,
    "es": {
      "titulo": "LA COSECHA",
      "pasa": "La vida vuelve a revisar lo construido, como a los treinta, pero esta vez por dentro. Llega el retiro o su negación, la muerte de los padres, los nietos, y la pregunta de qué sigue.",
      "spoiler": "A los treinta te preguntaron qué habías logrado. A los sesenta te preguntan en quién o en qué te convertiste. La pregunta es bien difícil de contestar.",
      "retos": [
        "La identidad pegada al cargo: sin trabajo, «¿yo quién soy?».",
        "Las obligaciones que hay que delegar y uno no suelta.",
        "Los primeros avisos serios de salud."
      ],
      "trabajar": "Se trabaja ser de nuevo, con otra estructura. No se trata de repetir lo que uno era, sino de vivirlo distinto. Mucha gente te necesita ahora: lo que sabes vale más que nunca y cuesta menos esfuerzo."
    },
    "en": {
      "titulo": "THE HARVEST",
      "pasa": "Life reviews what you built once more, as it did at thirty, but this time from the inside. Retirement arrives or is refused, parents die, grandchildren are born, and the question of what comes next shows up.",
      "spoiler": "At thirty they asked you what you had achieved. At sixty they ask who you became. The second question is harder to answer.",
      "retos": [
        "Identity glued to the job title: with no work, “who am I?”.",
        "Obligations that should be delegated and are not released.",
        "The first serious health warnings."
      ],
      "trabajar": "What is worked on here is being again, under another structure. It is not about repeating who you were, but living it differently. Many people need you now: what you know is worth more than ever and costs you less effort."
    }
  },
  {
    "min": 63,
    "max": 65,
    "es": {
      "titulo": "LA ÚLTIMA REBELDÍA",
      "pasa": "Aparecen las ganas de hacer lo que uno quiera, sin pedir permiso. También aparece el riesgo contrario: acomodarse, ponerse cómodo y dejar de moverse.",
      "spoiler": "A esta edad uno cree que ya se ganó el derecho a tener la razón siempre. Esa es exactamente la trampa.",
      "retos": [
        "El conformismo disfrazado de sabiduría.",
        "Querer dominar a los demás con la experiencia.",
        "Buscar la juventud en otros en vez de en uno mismo."
      ],
      "trabajar": "Se trabaja la libertad sin vanidad. Dedícale tiempo a conocerte más, mas que a complacerte. Y suelta el papel de dueño de la verdad: eso espanta a la gente que más te quiere."
    },
    "en": {
      "titulo": "THE LAST REBELLION",
      "pasa": "The urge to do as you please appears, without asking permission. And so does the opposite risk: settling in, getting comfortable, and stopping.",
      "spoiler": "At this age you believe you earned the right to always be right. That is exactly the trap.",
      "retos": [
        "Conformity disguised as wisdom.",
        "Wanting to rule others with your experience.",
        "Looking for youth in other people instead of in yourself."
      ],
      "trabajar": "What is worked on here is freedom without vanity. Give more time to knowing yourself than to pleasing yourself. And drop the role of owner of the truth: it drives away the people who love you most."
    }
  },
  {
    "min": 66,
    "max": 67,
    "es": {
      "titulo": "UN AÑO TE DA Y EL OTRO TE QUITA",
      "pasa": "Son dos años seguidos y opuestos. En uno todo se abre: reconocimiento, tranquilidad, cosas que se resuelven solas. En el otro todo se traba: el cuerpo, el trabajo, el dinero, los planes. Y luego se invierte.",
      "spoiler": "Es la edad de Job: la vida te levanta un año y te sienta al siguiente, y ninguna de las dos cosas es un premio ni un castigo. Es el mismo péndulo de siempre, solo que ahora se nota más.",
      "retos": [
        "La salud, que pide atención de verdad y no admite aplazamiento.",
        "La jubilación: la propia, o la que otros deciden por uno.",
        "Creerse viejo antes de tiempo y bajar los brazos."
      ],
      "trabajar": "Se trabaja la reconciliación: con el cuerpo, con la familia, con lo que no se logró. Y se trabaja una pregunta que a esta edad ya no se puede evitar: además de mi oficio, ¿cuál es mi vocación? Todavía hay tiempo para responderla haciendo, no solo pensando."
    },
    "en": {
      "titulo": "ONE YEAR GIVES, THE NEXT TAKES",
      "pasa": "Two consecutive, opposite years. In one everything opens: recognition, calm, matters that resolve themselves. In the other everything jams: the body, the work, the money, the plans. And then it reverses.",
      "spoiler": "It is the age of Job: life lifts you one year and sits you down the next, and neither is a prize or a punishment. It is the same pendulum as always, only now it shows more.",
      "retos": [
        "Health, which asks for real attention and allows no postponement.",
        "Retirement: your own, or the one others decide for you.",
        "Believing yourself old before your time and giving up."
      ],
      "trabajar": "What is worked on here is reconciliation: with the body, with the family, with what was not achieved. And a question that can no longer be avoided at this age: beyond my job, what is my vocation? There is still time to answer it by doing, not by thinking."
    }
  },
  {
    "min": 72,
    "max": 74,
    "es": {
      "titulo": "TRANSMITIR",
      "pasa": "Empieza la vejez física y, al mismo tiempo, la mejor edad para entregar lo que uno sabe. Lo que se hizo con la vida ahora se cuenta, se escribe, se enseña.",
      "spoiler": "Lo único que se lleva uno son las cirugías que se hizo en el alma. Las otras se quedan en el espejo.",
      "retos": [
        "La soledad, si no se trabajó antes la independencia.",
        "Volverse el viejo que da consejos que nadie pidió.",
        "Adaptarse al cuerpo sin pelear con él todos los días."
      ],
      "trabajar": "Se trabaja transmitir sin imponer. Aquí la vida promueve que tu experiencia le sirva a alguien más. La forma importa: lo que se entrega con humildad se recibe; lo que se impone se devuelve."
    },
    "en": {
      "titulo": "PASSING IT ON",
      "pasa": "Physical old age begins and, at the same time, the best age for handing over what you know. What was done with a life is now told, written, taught.",
      "spoiler": "The only surgery you take with you is the one you had on your soul. The rest stays in the mirror.",
      "retos": [
        "Loneliness, if independence was not worked on earlier.",
        "Becoming the old person who gives advice nobody asked for.",
        "Adapting to the body without fighting it every day."
      ],
      "trabajar": "What is worked on here is passing things on without imposing them. Life promotes that your experience serve someone else. The form matters: what is handed over humbly is received; what is imposed comes back to you."
    }
  },
  {
    "min": 81,
    "max": 84,
    "es": {
      "titulo": "LA VUELTA COMPLETA",
      "pasa": "El cielo cierra su vuelta entera: vuelve al lugar exacto en el que estaba el día en que naciste. Hay que vivir más de ochenta años para verlo, y casi nadie sabe que existe.",
      "spoiler": "Después de ochenta años de andar poniéndote máscaras, el cielo te devuelve al punto de partida. Resulta que sí eras tú desde el principio.",
      "retos": [
        "Las pérdidas, que ya son muchas.",
        "La tentación de vivir solo de recuerdos.",
        "Depender de otros después de una vida mandando."
      ],
      "trabajar": "Se trabaja la mirada larga sobre la propia vida: ver el dibujo completo, no los pedazos. Es la edad de la paz, si uno se atreve a perdonarse."
    },
    "en": {
      "titulo": "THE FULL CIRCLE",
      "pasa": "The sky closes its whole round: it returns to the exact place where it stood the day you were born. You have to live more than eighty years to see it, and almost nobody knows it exists.",
      "spoiler": "After eighty years of putting on masks, the sky returns you to the starting point. It turns out you were yourself from the beginning.",
      "retos": [
        "The losses, which by now are many.",
        "The temptation to live only on memories.",
        "Depending on others after a lifetime of being in charge."
      ],
      "trabajar": "What is worked on here is the long view of your own life: seeing the whole drawing, not the pieces. It is the age of peace, if you dare to forgive yourself."
    }
  },
  {
    "min": 88,
    "max": 90,
    "es": {
      "titulo": "EL BALANCE",
      "pasa": "La vida hace su último inventario. Lo que quedó en pie queda en pie para siempre: la familia, el oficio, lo que enseñaste, lo que dejaste hecho.",
      "spoiler": "No queda lo que acumulaste. Queda lo que hiciste con lo que te pasó.",
      "retos": [
        "Lo que no se dijo a tiempo y ahora urge decir.",
        "La herencia, que saca lo mejor y lo peor de las familias.",
        "Aceptar el cierre sin amargura."
      ],
      "trabajar": "Se trabaja el cierre: ordenar, agradecer, perdonar y entregar. Esta edad no pide más esfuerzo; pide verdad."
    },
    "en": {
      "titulo": "THE BALANCE",
      "pasa": "Life takes its final inventory. Whatever is still standing stands for good: the family, the craft, what you taught, what you left done.",
      "spoiler": "What you accumulated does not remain. What you did with what happened to you does.",
      "retos": [
        "What was not said in time and now urgently needs saying.",
        "The inheritance, which brings out the best and the worst in families.",
        "Accepting the closing without bitterness."
      ],
      "trabajar": "What is worked on here is closing: putting things in order, giving thanks, forgiving and handing over. This age asks for no more effort; it asks for truth."
    }
  }
];

const EDADES_TEXTOS = {
  es: {
    titulo: "Las edades zodiacales",
    intro: "Hay edades en las que los ciclos del cielo se repiten igual para todo el mundo. No importa tu signo ni tu carta exacta: a los 30 los planetas hacen lo mismo en la carta de todos. Lo que cambia es dónde te toca a ti y qué haces tú con eso.",
    tuEdad: "Tienes",
    anios: "años",
    tuEtapa: "Tu edad ahora",
    entre: "Vienes de %1$s y te acercas a %2$s.",
    antesDe: "Todavía no llegas a la primera edad de la lista: %1$s.",
    despuesDe: "Ya pasaste la última edad de la lista: %1$s.",
    verOtras: "Las demás edades",
    bloqueadas: "Las 23 edades completas van en el informe en PDF de tu carta natal, en la versión de PAGO.",
    hPasa: "Qué pasa",
    hSpoiler: "El spoiler ácido",
    hRetos: "Los retos",
    hTrabajar: "Qué entender y trabajar",
    aviso: "Las edades no son exactas: cada etapa se corre un año antes o un año después según la persona, y a veces dura dos años. Si estás cerca de una edad, léela: ya estás en ella."
  },
  en: {
    titulo: "The zodiacal ages",
    intro: "There are ages when the cycles of the sky repeat the same way for everyone. Your sign and your exact chart do not matter: at thirty the planets do the same thing in everybody's chart. What changes is where it lands for you and what you do with it.",
    tuEdad: "You are",
    anios: "years old",
    tuEtapa: "Your age now",
    entre: "You are coming from %1$s and approaching %2$s.",
    antesDe: "You have not reached the first age on the list yet: %1$s.",
    despuesDe: "You are past the last age on the list: %1$s.",
    verOtras: "The other ages",
    bloqueadas: "All 23 ages are included in the PDF report of your natal chart, in the PAID version.",
    hPasa: "What happens",
    hSpoiler: "The blunt truth",
    hRetos: "The challenges",
    hTrabajar: "What to understand and work on",
    aviso: "The ages are not exact: each stage moves a year earlier or later depending on the person, and sometimes lasts two years. If you are close to an age, read it: you are already in it."
  }
};

// --- Estilos propios de esta sección ---
(function () {
  if (document.getElementById('edades-estilos')) return;
  const s = document.createElement('style');
  s.id = 'edades-estilos';
  s.textContent = `
  .edades-seccion { margin-top: 3rem; }
  .edades-intro { color: var(--ink-faint); font-size: 0.92rem; margin-bottom: 1.5rem; }
  .edad-card { border: 1px solid var(--line); border-radius: 10px; padding: 1.6rem 1.5rem; background: #fff; }
  .edad-tuedad { font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold, #c9a961); font-weight: 700; margin-bottom: 0.5rem; }
  .edad-titulo { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.6rem; line-height: 1.2; margin-bottom: 0.3rem; }
  .edad-rango { font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-faint); margin-bottom: 1.3rem; }
  .edad-bloque { margin-bottom: 1.2rem; }
  .edad-bloque h5 { font-size: 0.7rem; letter-spacing: 0.16em; text-transform: uppercase; color: var(--ink-faint); margin: 0 0 0.45rem; font-weight: 700; }
  .edad-bloque p { margin: 0; line-height: 1.65; }
  .edad-bloque.spoiler p { font-style: italic; border-left: 2px solid var(--gold, #c9a961); padding-left: 0.9rem; }
  .edad-bloque ul { margin: 0; padding-left: 1.1rem; }
  .edad-bloque li { margin-bottom: 0.35rem; line-height: 1.55; }
  .edades-pills { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 1.5rem 0 0.9rem; }
  .edad-pill { font: 600 0.78rem/1 inherit; border: 1px solid var(--line); background: #fff; color: var(--ink, #15181d);
               border-radius: 999px; padding: 0.5rem 0.85rem; cursor: pointer; transition: all .2s; }
  .edad-pill:hover { border-color: var(--accent, #4a8fb8); }
  .edad-pill.activa { background: var(--ink, #15181d); color: #fff; border-color: var(--ink, #15181d); }
  .edad-pill.tuya { border-color: var(--gold, #c9a961); }
  .edad-pill.bloqueada { opacity: 0.45; cursor: default; }
  .edad-pill.bloqueada:hover { border-color: var(--line); }
  .edades-aviso { font-size: 0.78rem; color: var(--ink-faint); margin-top: 1rem; line-height: 1.55; }
  @media print { .edades-pills { display: none; } .edades-seccion { break-inside: auto; } }
  `;
  document.head.appendChild(s);
})();

function edadesCalcularEdad(fechaIso) {
  if (!fechaIso) return null;
  const f = String(fechaIso).slice(0, 10).split('-');
  if (f.length !== 3) return null;
  const nac = new Date(Number(f[0]), Number(f[1]) - 1, Number(f[2]));
  if (isNaN(nac.getTime())) return null;
  const hoy = new Date();
  let edad = hoy.getFullYear() - nac.getFullYear();
  const m = hoy.getMonth() - nac.getMonth();
  if (m < 0 || (m === 0 && hoy.getDate() < nac.getDate())) edad--;
  return edad;
}

function edadesRango(e, lang) {
  const une = (lang === 'en') ? ' to ' : ' a ';
  return e.min === e.max ? (e.min + '') : (e.min + une + e.max);
}

function edadesPintarFicha(cont, indice, lang, edadPersona) {
  const t = EDADES_TEXTOS[lang] || EDADES_TEXTOS.es;
  const e = EDADES_ZODIACALES[indice];
  const d = e[lang] || e.es;
  const suya = edadPersona !== null && edadPersona >= e.min && edadPersona <= e.max;
  const etiqueta = suya
    ? `<div class="edad-tuedad">${t.tuEtapa} · ${edadPersona} ${t.anios}</div>`
    : '';
  cont.innerHTML = `
    ${etiqueta}
    <div class="edad-titulo">${d.titulo}</div>
    <div class="edad-rango">${edadesRango(e, lang)} ${lang === 'es' ? 'años' : 'years'}</div>
    <div class="edad-bloque"><h5>${t.hPasa}</h5><p>${d.pasa}</p></div>
    <div class="edad-bloque spoiler"><h5>${t.hSpoiler}</h5><p>${d.spoiler}</p></div>
    <div class="edad-bloque"><h5>${t.hRetos}</h5><ul>${d.retos.map(r => '<li>' + r + '</li>').join('')}</ul></div>
    <div class="edad-bloque"><h5>${t.hTrabajar}</h5><p>${d.trabajar}</p></div>
  `;
}

function renderEdadesZodiacales(contenedorId, fechaNacimiento, lang) {
  const cont = document.getElementById(contenedorId);
  if (!cont) return;
  lang = (lang === 'en') ? 'en' : 'es';
  const t = EDADES_TEXTOS[lang];
  const edad = edadesCalcularEdad(fechaNacimiento);

  // ¿En cuál edad está la persona?
  let indice = EDADES_ZODIACALES.findIndex(e => edad !== null && edad >= e.min && edad <= e.max);
  let situacion = '';
  if (indice === -1 && edad !== null) {
    const siguiente = EDADES_ZODIACALES.findIndex(e => e.min > edad);
    if (siguiente === 0) {
      situacion = t.antesDe.replace('%1$s', edadesRango(EDADES_ZODIACALES[0], lang));
      indice = 0;
    } else if (siguiente === -1) {
      const ultima = EDADES_ZODIACALES.length - 1;
      situacion = t.despuesDe.replace('%1$s', edadesRango(EDADES_ZODIACALES[ultima], lang));
      indice = ultima;
    } else {
      situacion = t.entre
        .replace('%1$s', edadesRango(EDADES_ZODIACALES[siguiente - 1], lang))
        .replace('%2$s', edadesRango(EDADES_ZODIACALES[siguiente], lang));
      indice = siguiente;
    }
  }
  if (indice === -1) indice = 0;

  const encabezado = (edad !== null)
    ? `<p class="edades-intro"><strong>${t.tuEdad} ${edad} ${t.anios}.</strong> ${situacion} ${t.intro}</p>`
    : `<p class="edades-intro">${t.intro}</p>`;

  // Se abren las 23 edades si el modo está en 'completo' o si la persona
  // ya compró el informe en esta sesión.
  const abierto = (EDADES_MODO === 'completo')
    || (typeof window.compraTienePermiso === 'function' && window.compraTienePermiso());
  const pills = EDADES_ZODIACALES.map((e, i) => {
    const suya = (edad !== null && edad >= e.min && edad <= e.max);
    const propia = (i === indice);
    const clases = 'edad-pill'
      + (propia ? ' activa' : '')
      + (suya ? ' tuya' : '')
      + ((!abierto && !propia) ? ' bloqueada' : '');
    const attr = (abierto || propia) ? ` data-edad="${i}"` : ' disabled';
    return `<button type="button" class="${clases}"${attr}>${edadesRango(e, lang)}</button>`;
  }).join('');

  cont.innerHTML = `
    <div class="edades-seccion">
      <h4 class="section-title">${t.titulo}</h4>
      ${encabezado}
      <div class="edad-card" id="edad-ficha"></div>
      <div class="section-title" style="margin-top:1.6rem">${t.verOtras}</div>
      <div class="edades-pills" id="edades-pills">${pills}</div>
      ${abierto ? '' : `<p class="edades-aviso">${t.bloqueadas}</p>`}
      <p class="edades-aviso">${t.aviso}</p>
    </div>
  `;

  const ficha = cont.querySelector('#edad-ficha');
  edadesPintarFicha(ficha, indice, lang, edad);

  cont.querySelector('#edades-pills').addEventListener('click', function (ev) {
    const b = ev.target.closest('.edad-pill');
    if (!b || b.disabled || !b.dataset.edad) return;
    cont.querySelectorAll('.edad-pill').forEach(x => x.classList.remove('activa'));
    b.classList.add('activa');
    edadesPintarFicha(ficha, Number(b.dataset.edad), lang, edad);
  });
}

window.renderEdadesZodiacales = renderEdadesZodiacales;

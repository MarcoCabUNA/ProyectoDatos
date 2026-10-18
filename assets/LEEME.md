# assets/ — recursos gráficos de Cripta

La Vista busca cada imagen **por nombre**. Ningún id de cripta está escrito en el código (§9): el id del catálogo
*es* el nombre del archivo. Todo en minúsculas, sin tildes ni espacios (los nombres pasan `es_nombre_seguro` de
`../Security/ValidadorAcceso.py`). Este archivo es solo documentación: el juego no lo lee.

## Carpetas

| Carpeta | Contenido | Formato |
|---|---|---|
| `personajes` | El jugador: `jugador_<estado>_<n>.png` | PNG con transparencia |
| `enemigos` | `<id del catálogo>_<estado>_<n>.png` y el genérico `enemigo_...` | PNG con transparencia |
| `objetos` | `<id del catálogo>.png` y el respaldo `objeto.png` | PNG con transparencia |
| `fondos` | Fondos de pantalla completa | JPG |
| `ui` | Puertas e inventario | PNG con transparencia |
| `sonidos` | Efectos y músicas (ver "Sonidos" más abajo) | MP3 |

## Nombres

- **Animación:** `<nombre>_<estado>_<n>.png`, con `n` = 1, 2, 3… sin saltos. Estados: `idle` (reposo), `ataque`,
  `caminar`, `muerte`.
- **Orientación:** `<nombre>_direccion_<norte|sur|este|oeste>.png`. `sur` es el frente (de cara a la cámara) y
  `norte` la espalda. Los índices de dirección del código (N=0, S=1, E=2, O=3) se corresponden con esas palabras.
  Están reservados: la regla de búsqueda de abajo todavía no los usa.
- **Objetos:** `objetos` (por ejemplo `itm_daga_oxidada.png`).

## Cómo se buscan (regla prevista para la Vista)

1. **Un actor** (`ActorDTO.tipo` es el id del catálogo, o `jugador`): `<id>_<estado>_1.png`; si falta ese estado,
   `<id>_idle_1.png`; si el conjunto no existe, lo mismo con `enemigo`; y si nada existe, una figura dibujada.
   Por eso **cualquier enemigo sin sprites propios se dibuja como `enemigo`** (hoy, también `ent_guardian_oseo`).
2. **Un objeto:** `objetos`; si no existe, `objetos` (opcional); si no existe,
   `objetos/objeto.png`.
3. **Fondo de sala:** `fondo_inicial` en la sala de entrada, `fondo_final` en la sala de salida y `fondo_regular` en
   todas las demás (también en cualquier cripta que no conozcamos).
4. **Puertas:** una salida abierta no dibuja nada (los fondos ya traen el marco de las 4 puertas); una cerrada con
   llave usa `ui/puerta_cerrada.png`; la que lleva a la sala de salida, `ui`.
5. La Vista alinea cada fotograma por la base de su contenido (`Surface.get_bounding_rect`), así que no hace falta
   que todos tengan el mismo tamaño de lienzo.

## Efectos activos: sin imágenes, se hacen en código

Los efectos (`EfectoDTO.tipo`) **no usan archivos**. La Vista dibuja, encima de todo, un velo translúcido del color
del efecto sobre la pantalla del juego (`pygame.SRCALPHA`), y además una línea de texto con el nombre del efecto y
su tiempo restante (§10.2 pide mostrar el estado de los efectos; el color solo no dice cuál es ni cuánto dura).
Colores propuestos (ajustables en la Vista; la transparencia debe ser baja para que el juego se siga leyendo):

| Efecto | Velo |
|---|---|
| `veneno` | verde |
| `velocidad` con `valor` positivo (acelera) | azul |
| `velocidad` con `valor` negativo (ralentiza) | violeta |
| `antorcha` | naranja cálido |

Cada velo se crea una sola vez y se reutiliza en cada cuadro. Con varios efectos a la vez, los velos se superponen.

## Sonidos (`sonidos/`, solo con `VistaPygame(sonido=True)`; `main.py` lo activa)

Los 11 archivos son `.mp3` (44,1 kHz estéreo) y el nombre es el que escribe la tabla de `View/Componentes.py`
(`SONIDOS_CORTOS`, `MUSICAS`): si falta uno, ese sonido simplemente calla. Sin dispositivo de audio, el juego sigue en
silencio. Qué suena y cuándo lo decide `View/EventosSonoros.py`; el mezclador solo lo toca `View/Sonidos.py`.
`python tests/medir_sonidos.py` imprime la duración, el silencio inicial y el pico de cada archivo y lo que haría el cargador.

| Archivo | Cuándo suena |
|---|---|
| `Main_Menu` | Música de menú, criptas, nombre y puntajes (empieza en 2 s la primera vez). Bucle a mano antes del silencio del final del archivo (`fin_util_ms`) |
| `Game_Ambient` | Música de la partida y la pausa (a 35 % de su volumen en la pausa); se desvanece al terminar la partida, ya durante la demora del fin |
| `Click` | Al activar un botón (ratón o Enter), al esperar (botón Esperar o tecla Z) y al recoger un objeto que no sea una llave |
| `Main_Room_Sound` | Una vez, al empezar una partida NUEVA (no al cargar). En ese cuadro no suena `Click` |
| `Enemies_Impact_Hit` | Cuando baja la vida de un enemigo (comparando por id con el cuadro anterior) o desaparece uno que tenía vida. Como mucho uno por cuadro |
| `Hero_Impact_Hit` | Cuando baja la vida del protagonista, por golpes, trampas o veneno. Como mucho uno por cuadro |
| `Grab_Key_Sound` | Cuando desaparece del suelo un objeto de clase `llave` (en lugar de `Click`) |
| `Locked_Room_Change` | Cuando una puerta cerrada de la sala pasa a abierta: suena al abrirla, no al cruzarla |
| `Low_Health` | En bucle (canal reservado 0) con vida <= 30 % de la máxima y > 0; se apaga al superar el 40 %, al terminar la partida o al salir de juego y pausa. La pausa lo pausa |
| `Defeat_Music`, `Victory_Music` | Al aparecer la pantalla de derrota o de victoria (canal reservado 1). Al salir de ella se apagan con un fundido corto y entra `Main_Menu` |

Los efectos de la partida (golpes, llave, puerta, `Click` por recoger) no suenan en el primer cuadro de una partida, cuando
el reloj del estado retrocede (retroceso o cargar), cuando cambia la sala ni en las pantallas que no son la partida. La
música, `Low_Health`, los sonidos de fin y el `Click` de los botones sí suenan fuera de la partida.

**Latido visual.** Con sonido, la viñeta rojo oscuro-negro de vida baja (`VINETA_*` en `View/Componentes.py`) late al
ritmo de `Low_Health`: su alfa es proporcional a la envolvente del sonido (máximo por ventana de 20 ms, suavizada) en la
posición de reproducción, que es el tiempo sonado sin contar las pausas, módulo la duración del sonido recortado. Sin
sonido (o sin la envolvente) conserva su pulso fijo de 1,8 s.

El cargador prepara cada sonido corto una sola vez al abrir la ventana (entre 0,5 y 0,7 s en total): le quita el silencio
del inicio (hasta superar el 10 % del pico, menos 5 ms), lo limita a su tope, sube el volumen solo a los que tienen el pico
muy bajo (`Main_Room_Sound`, `Victory_Music`) y les pone fundidos contra los chasquidos.

## Conjuntos que hay hoy

| Conjunto | Estados disponibles |
|---|---|
| `jugador` | idle (3), ataque (1), caminar (3), muerte (3), orientaciones |
| `enemigo` (genérico y respaldo) | idle (1), ataque (4), muerte (4), orientaciones |
| `ent_rata_gigante` | idle (1), ataque (2), orientaciones |

Objetos de `cripta-01`: `itm_antidoto`, `itm_antorcha`, `itm_coraza_cuero`, `itm_daga_oxidada`, `itm_llave_bronce`,
`itm_llave_negra`, `itm_pergamino_retroceso`, `itm_pocion_menor`.

## Pendiente (nada de esto bloquea el juego)

- `CREDITOS.md`: fuente y licencia de cada pack de imágenes.
- `ent_guardian_oseo_*`: el guardián de `cripta-01` usa por ahora el sprite genérico `enemigo`.
- `objetos` (arma, armadura, pocion, antidoto, llave, antorcha, pergamino_retroceso): opcional.
- `ui` (32×32): opcional; puede ser texto.
# assets/ — recursos gráficos de Cripta

La Vista busca cada imagen **por nombre**. Ningún id de cripta está escrito en el código (§9): el id del catálogo
*es* el nombre del archivo. Todo en minúsculas, sin tildes ni espacios (los nombres pasan `es_nombre_seguro` de
`Security/ValidadorAcceso.py`). Este archivo es solo documentación: el juego no lo lee.

## Carpetas

| Carpeta | Contenido | Formato |
|---|---|---|
| `personajes/` | El jugador: `jugador_<estado>_<n>.png` | PNG con transparencia |
| `enemigos/` | `<id del catálogo>_<estado>_<n>.png` y el genérico `enemigo_...` | PNG con transparencia |
| `objetos/` | `<id del catálogo>.png` y el respaldo `objeto.png` | PNG con transparencia |
| `fondos/` | Fondos de pantalla completa | JPG |
| `ui/` | Puertas e inventario | PNG con transparencia |

## Nombres

- **Animación:** `<nombre>_<estado>_<n>.png`, con `n` = 1, 2, 3… sin saltos. Estados: `idle` (reposo), `ataque`,
  `caminar`, `muerte`.
- **Orientación:** `<nombre>_direccion_<norte|sur|este|oeste>.png`. `sur` es el frente (de cara a la cámara) y
  `norte` la espalda. Los índices de dirección del código (N=0, S=1, E=2, O=3) se corresponden con esas palabras.
  Están reservados: la regla de búsqueda de abajo todavía no los usa.
- **Objetos:** `objetos/<id>.png` (por ejemplo `itm_daga_oxidada.png`).

## Cómo se buscan (regla prevista para la Vista)

1. **Un actor** (`ActorDTO.tipo` es el id del catálogo, o `jugador`): `<id>_<estado>_1.png`; si falta ese estado,
   `<id>_idle_1.png`; si el conjunto no existe, lo mismo con `enemigo`; y si nada existe, una figura dibujada.
   Por eso **cualquier enemigo sin sprites propios se dibuja como `enemigo`** (hoy, también `ent_guardian_oseo`).
2. **Un objeto:** `objetos/<id>.png`; si no existe, `objetos/clase_<clase>.png` (opcional); si no existe,
   `objetos/objeto.png`.
3. **Fondo de sala:** `fondo_inicial` en la sala de entrada, `fondo_final` en la sala de salida y `fondo_regular` en
   todas las demás (también en cualquier cripta que no conozcamos).
4. **Puertas:** una salida abierta no dibuja nada (los fondos ya traen el marco de las 4 puertas); una cerrada con
   llave usa `ui/puerta_cerrada.png`; la que lleva a la sala de salida, `ui/puerta_final.png`.
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
- `objetos/clase_<clase>.png` (arma, armadura, pocion, antidoto, llave, antorcha, pergamino_retroceso): opcional.
- `ui/equipado.png` (32×32): opcional; puede ser texto.
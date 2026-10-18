"""
Componentes (Vista): el estilo del juego y los elementos reutilizables (botón, panel translúcido, texto).

TODA la paleta, los tamaños de fuente y las medidas fijas de la interfaz están en la sección ESTILO de este archivo:
es el único lugar donde se ajusta el aspecto. Paleta: oscura, con acentos rojos y dorados, como el arte del juego.

Las funciones dibujan sobre la superficie que reciben; no guardan estado ni llaman al Controlador.
"""
import pygame

# ============================================================================ ESTILO
ANCHO, ALTO = 1376, 768                      # resolución lógica (el tamaño nativo de los fondos)

# Colores (RGB; con una cuarta cifra, RGBA: translúcidos)
NEGRO_TINTA = (14, 10, 14)
VELO_SUAVE = (0, 0, 0, 232)                  # sobre fondo_menu en las pantallas que dibujan su propio título
VELO_FUERTE = (0, 0, 0, 215)                 # sobre la partida (o su sustituto) en la pausa
PANEL = (16, 11, 16, 205)                    # fondo de paneles y botones
PANEL_BORDE = (120, 28, 32)                  # rojo oscuro
ROJO = (190, 36, 42)
ROJO_VIVO = (226, 60, 56)
ORO = (232, 184, 84)
ORO_OSCURO = (150, 112, 48)
TEXTO = (236, 230, 218)
TEXTO_SUAVE = (170, 160, 150)
AVISO = (255, 128, 108)
AVISO_FONDO = (70, 14, 16, 230)
SOMBRA = (8, 6, 8)                           # contorno del texto que va sobre la escena
VIDA_BUENA = (84, 168, 72)
VIDA_BAJA = (200, 52, 48)                    # con menos de la cuarta parte de la vida
VIDA_FONDO = (30, 12, 14)

# Tamaños de fuente (pygame.font.Font(None, tamaño))
TAM_TITULO = 60
TAM_BOTON = 30
TAM_TEXTO = 28
TAM_PIE = 22
TAM_CHICO = 18                               # números dentro de las barras de vida
# La ayuda y los mensajes NO tienen tamaño fijo: Fuentes lo elige al abrir la Vista (elegir_tamano), así no depende de la versión de
# pygame ni de la máquina. Es el mayor tamaño del rango en que la línea más ancha deja HUD_HOLGURA píxeles libres en el panel.
TAM_HUD_MIN, TAM_HUD_MAX = 14, 22
HUD_HOLGURA = 8
# Copia de UIController.ControlesJuego.AYUDA_JUEGO (la Vista no puede importarla; test_vista_hud comprueba que son iguales)
AYUDA_PARA_MEDIR = (
    "WASD / flechas: moverse",
    "Clic en un enemigo (o Espacio): atacar",
    "Clic en un objeto del suelo: recoger",
    "E (o clic en la puerta): abrir una puerta",
    "Z: esperar",
    "Rueda o Tab: recorrer el inventario",
    "U (o doble clic): usar   Q (o clic derecho): equipar",
    "G (o Mayús + clic): soltar   V: cambiar el orden",
    "Retroceso o Ctrl + Z: pergamino de retroceso",
    "Ctrl + S / F5: guardar   Ctrl + L / F9: cargar",
    "Esc: menú",
)
# Los peores mensajes del motor (tiempo de 4 cifras, enemigo #99, daño de 999 y los nombres más largos del paquete offline);
# test_vista_hud comprueba que con ellos se elige el mismo tamaño que con TODAS las plantillas
MENSAJES_PARA_MEDIR = (
    "[t=9999] Guardián óseo #99 ataca a Jugador: 999 de daño",
    "[t=9999] Jugador ataca a Guardián óseo #99: 999 de daño",
    "[t=9999] El veneno hace 999 de daño a Guardián óseo #99",
    "[t=9999] Partida cargada: estás en Pasillo de las urnas",
    "[t=9999] Rata gigante #99 ataca a Jugador: 999 de daño",
    "[t=9999] Jugador ataca a Rata gigante #99: 999 de daño",
    "[t=9999] El veneno hace 999 de daño a Rata gigante #99",
)

# Medidas de las pantallas con botones
BOTON_ALTO = 44
BOTON_ALTO_MENU = 36                         # el menú comparte espacio con el título del fondo
BOTON_ALTO_MINIMO = 30                       # por debajo de esto se pasa a otra columna
BOTON_SEPARACION = 8
BOTON_ANCHO = 420
RADIO = 8
TITULO_Y = 52
AVISO_MAX_LINEAS = 2                         # un aviso más largo se corta con "..." (no debe tapar los botones)
AVISO_INTERLINEA = 28
AVISO_ARRIBA_Y = 44                          # con el aviso arriba (victoria y derrota): su borde superior
AVISO_SEPARACION = 8                         # espacio entre el aviso y la primera línea de ayuda
PIE_BASE_Y = 760                             # las líneas de ayuda se apilan hacia arriba desde aquí
PIE_INTERLINEA = 20

# ---------------------------------------------------------------------------- escena de juego (tamaños y reparto)
# Aquí, y solo aquí, están todas las medidas de la escena: EscenaJuego no tiene números propios.
# Tamaños: el alto del CONTENIDO del sprite (recortado), en píxeles de la resolución lógica.
ALTURA_JUGADOR = 90                          # el protagonista: siempre igual, en todas las escenas
ALTURA_ENEMIGO = 190                         # enemigo con sprites propios (como la rata)
FACTOR_RESPALDO = 0.85                       # enemigo de respaldo (conjunto genérico): este tanto de ALTURA_ENEMIGO
FACTORES_ENEMIGOS = [1.0, 0.85, 0.7, 0.58, 0.48, 0.4, 0.33, 0.27, 0.22, 0.18, 0.15]   # si no caben, todos se achican igual
FACTOR_NOMBRE_CHICO = 0.6                    # con un factor menor, los nombres usan la fuente chica
LADO_OBJETO = 52                             # cuadrado en que cabe el sprite de un objeto del suelo
FICHA = 40                                   # alto del nombre y la barra de vida sobre un actor
FICHA_SEPARACION = (4, 2)                    # hueco entre el sprite y la barra, y entre la barra y el nombre
ALTURA_MINIMA = 8                            # ningún sprite de actor se dibuja más bajo que esto
HALO_MARGEN = (12, 8)                        # cuánto sobresale del sprite el marco del enemigo objetivo
HALO_COLOR = (232, 184, 84, 55)
BARRA_VIDA = (96, 14)
NOMBRE_ANCHO_MAX = 170                       # un nombre más largo se corta con "..."
FACTOR_FICHA_ESTRECHA = 0.5                  # con un factor menor (sala muy llena), la ficha se estrecha hasta...
FICHA_ANCHO_MIN = 70                         # ...este ancho: barra más corta y nombre cortado con "..." (si no, con
                                             # 12 enemigos + 12 objetos alrededor del centro no cabían: la ficha no
                                             # bajaba de 98 px aunque el sprite sí se achicara)

# Dónde pisa el protagonista (los pies, en píxeles) y qué puede ocupar la gente
SUELO = pygame.Rect(280, 170, 816, 450)      # la parte del suelo que comparten los tres fondos de sala
PIES_CENTRO = (688, 430)                     # sin sala anterior, o si no se sabe por dónde entró
PIES_PUERTA = [(688, 300), (688, 600), (1060, 430), (316, 430)]    # delante de la puerta N, S, E y O
JUGADOR_OCUPA = (120, ALTURA_JUGADOR + FICHA)    # lo que el protagonista reserva alrededor de sus pies (ancho, alto)
PASILLOS = [pygame.Rect(618, 170, 140, 50), pygame.Rect(618, 570, 140, 50),    # junto a cada puerta con salida: libre
            pygame.Rect(1046, 360, 50, 140), pygame.Rect(280, 360, 50, 140)]  # (N, S, E, O)

# Reparto de enemigos y objetos (las funciones puras colocar y posicion_del_protagonista de EscenaJuego)
REPARTO_PASO = 12                            # separación de las posiciones candidatas
REPARTO_SEPARACION = 8                       # hueco mínimo entre dos elementos
REPARTO_RADIO_ENEMIGOS = 230                 # a qué distancia del protagonista prefieren estar (píxeles)
REPARTO_RADIO_OBJETOS = 330

# Aura de los objetos del suelo (los enemigos no llevan)
AURA_MARGEN = 8                              # cuánto sobresale del sprite
AURA_COLOR = (255, 214, 120)
AURA_INTENSIDAD = 150                        # 0 (invisible) a 255 (opaca)

# Fondos de sala y marcos de puerta medidos sobre ellos (1376x768)
FONDO_INICIAL, FONDO_REGULAR, FONDO_FINAL = "fondo_inicial", "fondo_regular", "fondo_final"
FONDOS_CONOCIDOS = [FONDO_INICIAL, FONDO_REGULAR, FONDO_FINAL]
# Rectángulo de cada marco de puerta, en el orden N, S, E, O (los índices de DTO/Direcciones.py), por fondo, medido
# sobre ampliaciones con regla (tests/capturar_pantallas.py las dibuja: capturas/medicion_*.png).
MARCOS = [
    [pygame.Rect(625, 46, 132, 92), pygame.Rect(625, 632, 132, 92), pygame.Rect(1150, 318, 90, 134),
     pygame.Rect(138, 318, 90, 134)],
    [pygame.Rect(618, 20, 148, 98), pygame.Rect(618, 650, 148, 100), pygame.Rect(1190, 312, 100, 152),
     pygame.Rect(88, 312, 100, 152)],
    [pygame.Rect(632, 40, 126, 80), pygame.Rect(625, 636, 132, 92), pygame.Rect(1174, 318, 90, 134),
     pygame.Rect(112, 318, 90, 134)],
]
MARCOS_OSCURECIBLES = [True, True, False]    # False: el fondo solo trae la puerta del norte (fondo_final)
FRACCION_ESTRECHA = 0.27                     # lo que se achica el hueco de la puerta hacia dentro de la sala
COLOR_OSCURO = (0, 0, 0, 205)

# Ambientación lúgubre de los fondos de SALA (no de menú, victoria ni derrota). Receta a intensidad 1.0; la ambientación
# final mezcla linealmente el original (0) con la receta (1). AMBIENTE_INTENSIDAD es la única perilla (0 = sin ambientar).
AMBIENTE_INTENSIDAD = 0.5
AMBIENTE_GRIS = 0.25                         # cuánto de la versión en grises se mezcla con la imagen
AMBIENTE_TINTE = (122, 110, 122)             # cada canal se multiplica por esto / 255
AMBIENTE_VINETA = 0.45                       # fuerza de la viñeta radial (0 = sin viñeta; en las esquinas oscurece este tanto)
AMBIENTE_VINETA_TAMANO = (64, 36)            # el degradado se calcula en miniatura y se amplía
PUERTA_CERRADA, PUERTA_FINAL = "puerta_cerrada", "puerta_final"       # nombres de los sprites de ui/
ESCALA_PUERTA = [(PUERTA_CERRADA, 2.5), (PUERTA_FINAL, 1.25)]        # (sprite, escala): miran al norte y se giran

# ---------------------------------------------------------------------------- HUD de la partida (Etapa 7)
# Cada panel es un rectángulo fijo. Los de la izquierda y la derecha de arriba (estadísticas, efectos, inventario) no pisan
# el suelo; MENSAJES y el grupo de abajo a la derecha sí, así que repartir_escena los trata como zonas ocupadas. Los tramos
# y 296-470 de las bandas laterales quedan libres: ahí están las puertas este y oeste y el sitio del protagonista.
HUD_ESTADISTICAS = pygame.Rect(8, 8, 264, 128)
HUD_EFECTOS = pygame.Rect(8, 144, 264, 148)
HUD_MENSAJES = pygame.Rect(8, 470, 350, 290)
HUD_INVENTARIO = pygame.Rect(1104, 8, 264, 284)
HUD_ESPERAR = pygame.Rect(1028, 470, 340, 40)
HUD_AVISO = pygame.Rect(1028, 516, 340, 52)
HUD_AYUDA = pygame.Rect(1028, 574, 340, 186)
HUD_PANELES = [HUD_ESTADISTICAS, HUD_EFECTOS, HUD_MENSAJES, HUD_INVENTARIO, HUD_ESPERAR, HUD_AVISO, HUD_AYUDA]
HUD_RELLENO = 8                              # margen interior de los paneles
HUD_MENSAJES_LINEAS = 20                     # capacidad del panel de mensajes
HUD_MENSAJES_INTERLINEA = 13
HUD_MENSAJES_ARRIBA = 22                     # donde empieza la primera línea (debajo del rótulo)
HUD_AVISO_LINEAS = 3
HUD_AYUDA_INTERLINEA = 15
HUD_EFECTOS_INTERLINEA = 22
HUD_EFECTOS_ARRIBA = 28
HUD_STATS_FILAS = (38, 66, 94)               # y (dentro del panel) de cada fila de números de las estadísticas
HUD_STATS_COLUMNA = 132                      # x (dentro del panel) de la segunda columna
# Inventario: casillas en filas de INV_COLUMNAS; si capacidad_maxima pasa de INV_CASILLAS_MAX, solo se dibujan esas
INV_COLUMNAS = 5
INV_CASILLAS_MAX = 15
INV_LADO = 46
INV_HUECO = 4
INV_SPRITE = 38                              # cuadrado en que cabe el sprite de un objeto dentro de su casilla
INV_ARRIBA = 30                              # y (dentro del panel) de la primera fila de casillas
INV_INTERLINEA = 16                          # líneas de datos del objeto bajo el cursor
# Velos de efectos (RGBA de baja opacidad: el juego se tiene que seguir leyendo)
VELO_VENENO = (60, 200, 70, 36)
VELO_RAPIDO = (60, 110, 255, 36)             # velocidad con valor > 0
VELO_LENTO = (150, 70, 220, 40)              # velocidad con valor < 0
VELO_ANTORCHA = (255, 150, 40, 40)

# ---------------------------------------------------------------------------- animaciones (Etapa 9; solo con VistaPygame(animaciones=True))
# Todo va por el reloj en milisegundos de la Vista (nunca el reloj virtual del juego). Las tablas son listas que dan un valor
# por cada paso de su periodo.
ANIM_IDLE_FPS = 6                            # reposo de los enemigos con varios fotogramas: fotogramas por segundo
ANIM_IDLE_JUGADOR_FPS = 3                    # reposo del protagonista: 3 fotogramas en un ciclo de 1 s
BAMBOLEO = [0, 1, 1, 2, 2, 2, 1, 1, 0, -1, -1, -2, -2, -2, -1, -1]      # píxeles de subida (+) del actor de un solo fotograma
BAMBOLEO_PERIODO_MS = 1600
BAMBOLEO_FASE = 5                            # pasos de la tabla de desfase por cada posición en la lista de enemigos
AURA_INTENSIDAD_ANIMADA = 255                # con animaciones el aura se prepara a tope y su alfa se mueve con la tabla
AURA_RESPIRA = [118, 126, 136, 146, 156, 164, 170, 164, 156, 146, 136, 126]    # alfa del aura en reposo (~el 150 de siempre)
AURA_RESPIRA_PERIODO_MS = 2400
AURA_BRILLA = [212, 224, 236, 246, 255, 246, 236, 224]                          # alfa con el ratón encima
AURA_BRILLA_PERIODO_MS = 1100
AURA_FASE = 3                                # pasos de desfase por cada objeto de la lista
FUNDIDO_SALA_MS = 280                        # al entrar a una sala nueva (sobre la escena, debajo del HUD)
FUNDIDO_PANTALLA_MS = 180                    # al cambiar de pantalla de menú (sobre toda la pantalla)
FUNDIDO_COLOR = (0, 0, 0)
PANTALLAS_CON_FUNDIDO = ["menu", "criptas", "nombre", "victoria", "derrota", "puntajes"]
PARPADEO = [4, 7, 3, 10, 14, 9, 5, 12, 16, 11, 6, 2, 8, 13, 7, 3, 9, 15, 10, 4, 6, 12, 16, 13, 8, 3, 5, 11, 7, 2, 9, 6]
PARPADEO_PERIODO_MS = 2500                   # alfa (0-255) de una capa oscura sobre el fondo de la sala: luz que vacila
PARPADEO_COLOR = (0, 0, 0)
MUERTE_JUGADOR_MS = 600                      # el protagonista cae (fotogramas 'muerte') desde el primer cuadro de la derrota

# Feedback de combate (fase 2): todo se deduce de las diferencias entre un cuadro y el anterior, nunca de los mensajes
MAX_ANIMACIONES = 24                         # las que la Vista recuerda a la vez (si llegan más, se olvidan las más viejas)
NUMERO_MS = 700                              # número flotante de vida: -N rojo, +N verde
NUMERO_SUBE = 36                             # píxeles que sube en ese tiempo
NUMERO_FIJO = 0.55                           # la parte del tiempo en que se ve entero antes de desvanecerse
NUMERO_TAMANO = 40
NUMERO_ROJO = ROJO_VIVO
NUMERO_VERDE = (110, 214, 104)
NUMERO_CONTORNO = (14, 8, 10)
DESTELLO_MS = 160                            # el actor golpeado se aclara
DESTELLO_ALFA = 190
DESTELLO_COLOR = (255, 255, 255)
BORDE_MS = 220                               # el borde de la pantalla se enrojece cuando el protagonista pierde vida
BORDE_ALFA = 210
BORDE_GROSOR = 22
BORDE_COLOR = ROJO_VIVO
VELO_GOLPE_MS = 640                          # velo rojo que parpadea sobre toda la pantalla cuando golpean al protagonista
VELO_GOLPE_ALFA = 70
VELO_GOLPE_PARPADEOS = 3
VINETA_UMBRAL = 0.35                         # fracción de vida por debajo de la cual aparece la viñeta de vida baja
VINETA_ALFA = 235                            # alfa máximo (con la vida en 0)
VINETA_GROSOR = 150
VINETA_PERIODO_MS = 1800                     # un latido lento
VINETA_ROJO = (96, 8, 12)                    # hacia adentro; el filo de la pantalla es negro
VINETA_PISO_LATIDO = 0.35                    # con el sonido de vida baja, lo que queda de la viñeta entre latidos (0 a 1)
VINETA_SUAVIZADO = (1, 2, 3, 2, 1)           # pesos de la envolvente suavizada (ventanas vecinas, en círculo)
MUERTE_ENEMIGO_MS = 450                      # el enemigo muere (fotogramas 'muerte' si los tiene; si no, se encoge y se desvanece)
MUERTE_ENCOGE = 0.55                         # el tamaño que le queda al final, sin fotogramas propios
RECOGIDO_MS = 220                            # el objeto recogido se desvanece subiendo
RECOGIDO_SUBE = 26
PUERTA_DESVANECE_MS = 260                    # la puerta cerrada que se abre se desvanece
PUERTA_CALIDO_MS = 300                       # y la puerta final, además, brilla
PUERTA_CALIDO_ALFA = 190
PUERTA_CALIDO_COLOR = (255, 206, 120)
PUERTA_CALIDO_MARGEN = 16
CURSOR_MANO = True                           # con animaciones, el cursor es una mano sobre lo que se puede pulsar

# Etiqueta con el nombre del objeto bajo el ratón
ETIQUETA_SEPARACION = 6                      # entre el objeto y la etiqueta
ETIQUETA_RELLENO = (20, 12)                  # lo que la etiqueta sobresale del texto (ancho, alto)

# ---------------------------------------------------------------------------- sonidos (Etapa 9B; solo con VistaPygame(sonido=True))
CARPETA_SONIDOS = "sonidos"                  # dentro de assets/; el nombre del archivo es el de la tabla + SONIDO_EXTENSION
SONIDO_EXTENSION = ".mp3"
MEZCLADOR = (44100, -16, 2, 512)             # frecuencia, tamaño (negativo: con signo), canales, buffer
MEZCLADOR_CANALES = 16
MEZCLADOR_RESERVADOS = 2                     # canal 0: Low_Health; canal 1: derrota y victoria
SONIDO_UMBRAL_INICIO = 0.10                  # el sonido empieza donde supera esta parte de su pico
SONIDO_MARGEN_MS = 5                         # lo que se deja antes de ese punto
SONIDO_FUNDIDO_BORDE_MS = 5                  # fundido de entrada (y mínimo de salida) contra los clics
SONIDO_GANANCIA_MAX = 6.0
SONIDO_PICO_OBJETIVO = 0.9
SONIDO_GANANCIA_MIN = 1.5                    # con menos ganancia que esto no se tocan las muestras
SONIDO_VENTANA_MS = 20                       # ventana de la envolvente de Low_Health
# Sonidos cortos: (archivo, tope_ms (0: sin tope), fundido_ms, volumen)
SONIDOS_CORTOS = [
    ("Click", 800, 150, 0.6),
    ("Enemies_Impact_Hit", 1200, 120, 0.9),
    ("Hero_Impact_Hit", 1200, 120, 1.0),
    ("Grab_Key_Sound", 1800, 250, 0.8),
    ("Locked_Room_Change", 3000, 400, 0.8),
    ("Main_Room_Sound", 3000, 400, 0.8),
    ("Low_Health", 0, 10, 0.7),
    ("Defeat_Music", 0, 300, 0.9),
    ("Victory_Music", 0, 300, 0.9),
]
# Músicas largas (en streaming): (archivo, volumen, fin_util_ms, inicio_de_la_primera_vez_ms)
MUSICAS = [
    ("Main_Menu", 0.5, 101000, 2000),
    ("Game_Ambient", 0.35, 89000, 0),
]
# Qué música va con cada pantalla: (pantalla, archivo). Las demás pantallas no tienen música.
MUSICA_POR_PANTALLA = [
    ("menu", "Main_Menu"), ("criptas", "Main_Menu"), ("nombre", "Main_Menu"), ("puntajes", "Main_Menu"),
    ("juego", "Game_Ambient"), ("pausa", "Game_Ambient"),
]
MUSICA_PAUSA = 0.35                          # en la pausa la música baja a esta parte de su volumen
MUSICA_SALIDA_MS = 500                       # fundido de salida al cambiar de tema
MUSICA_ENTRADA_MS = 800                      # fundido de entrada de un tema nuevo (y de cada vuelta del bucle)
MUSICA_BAJADA_MS = 1500                      # antes de fin_util_ms el volumen baja a 0
MUSICA_SIN_NOTICIAS_MS = 2000                # si la música no suena (get_pos < 0) pasado este tiempo, se reinicia
SONIDO_CLICK = "Click"
SONIDO_SALA = "Main_Room_Sound"
SONIDO_LATIDO = "Low_Health"                 # el de vida baja: de él se saca la envolvente del latido
SONIDO_GOLPE_ENEMIGO = "Enemies_Impact_Hit"
SONIDO_GOLPE_HEROE = "Hero_Impact_Hit"
SONIDO_LLAVE = "Grab_Key_Sound"
SONIDO_PUERTA = "Locked_Room_Change"
# Sonidos de fin (canal reservado 1): (pantalla, archivo)
SONIDOS_DE_FIN = [("derrota", "Defeat_Music"), ("victoria", "Victory_Music")]
SONIDO_FIN_FUNDIDO_MS = 300                  # fundido corto al salir de la pantalla de victoria o derrota
VIDA_BAJA_ENTRA = 0.30                       # Low_Health empieza con vida <= 30 % de la máxima (y vida > 0)...
VIDA_BAJA_SALE = 0.40                        # ...y se apaga al superar el 40 % (histéresis)


def elegir_tamano(textos, ancho_util: int, alto_maximo: int, minimo: int = TAM_HUD_MIN, maximo: int = TAM_HUD_MAX,
                  holgura: int = HUD_HOLGURA) -> int:
    """El mayor tamaño de fuente de [minimo, maximo] en que el más ancho de 'textos' deja 'holgura' píxeles libres en 'ancho_util' y
    la línea no es más alta que 'alto_maximo'. Si ni el mínimo cabe, devuelve el mínimo. Pide pygame.font.init()."""
    for tamano in range(maximo, minimo - 1, -1):
        fuente = pygame.font.Font(None, tamano)
        if fuente.get_height() <= alto_maximo and max(fuente.size(texto)[0] for texto in textos) + holgura <= ancho_util:
            return tamano
    return minimo


class Fuentes:
    """Las fuentes del juego. Se crean al abrir la ventana (después de pygame.font.init())."""

    def __init__(self):
        self.titulo = pygame.font.Font(None, TAM_TITULO)
        self.boton = pygame.font.Font(None, TAM_BOTON)
        self.texto = pygame.font.Font(None, TAM_TEXTO)
        self.pie = pygame.font.Font(None, TAM_PIE)
        self.chico = pygame.font.Font(None, TAM_CHICO)
        self.tam_mensajes = elegir_tamano(MENSAJES_PARA_MEDIR, HUD_MENSAJES.width - 2 * HUD_RELLENO, HUD_MENSAJES_INTERLINEA - 1)
        self.tam_ayuda = elegir_tamano(AYUDA_PARA_MEDIR, HUD_AYUDA.width - 2 * HUD_RELLENO, HUD_AYUDA_INTERLINEA)
        self.mensajes = pygame.font.Font(None, self.tam_mensajes)
        self.ayuda_juego = pygame.font.Font(None, self.tam_ayuda)


# ============================================================================ texto
def texto_en(superficie, fuente, texto: str, color, posicion, ancla: str = "center") -> pygame.Rect:
    """Dibuja 'texto' con su 'ancla' (center, midtop, topleft, midbottom, ...) en 'posicion'. Devuelve su rectángulo."""
    imagen = fuente.render(texto, True, color)
    rectangulo = imagen.get_rect(**{ancla: posicion})
    superficie.blit(imagen, rectangulo)
    return rectangulo


def texto_sombreado(superficie, fuente, texto: str, color, posicion, ancla: str = "center") -> pygame.Rect:
    """Como texto_en, con un contorno oscuro para que se lea sobre cualquier fondo (la escena de juego)."""
    imagen = fuente.render(texto, True, color)
    rectangulo = imagen.get_rect(**{ancla: posicion})
    sombra = fuente.render(texto, True, SOMBRA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        superficie.blit(sombra, rectangulo.move(dx, dy))
    superficie.blit(imagen, rectangulo)
    return rectangulo


def recortar_a_ancho(fuente, texto: str, ancho: int) -> str:
    """'texto' tal cual si cabe en 'ancho' píxeles; si no, lo corta y le pone '...'."""
    if fuente.size(texto)[0] <= ancho:
        return texto
    while texto and fuente.size(texto + "...")[0] > ancho:
        texto = texto[:-1]
    return texto + "..."


def ajustar_lineas(fuente, texto: str, ancho: int) -> list[str]:
    """Parte 'texto' en líneas que caben en 'ancho' píxeles, cortando entre palabras."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        prueba = palabra if not actual else f"{actual} {palabra}"
        if actual and fuente.size(prueba)[0] > ancho:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas or [""]


# ============================================================================ paneles y botones
def panel(superficie, rectangulo: pygame.Rect, relleno=PANEL, borde=PANEL_BORDE, grosor: int = 2) -> None:
    """Un rectángulo con esquinas redondeadas; el relleno puede ser translúcido (RGBA)."""
    capa = pygame.Surface(rectangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, relleno, capa.get_rect(), border_radius=RADIO)
    if borde is not None and grosor > 0:
        pygame.draw.rect(capa, borde, capa.get_rect(), width=grosor, border_radius=RADIO)
    superficie.blit(capa, rectangulo)


def barra_de_vida(superficie, fuentes: Fuentes, rectangulo: pygame.Rect, vida: int, vida_max: int) -> None:
    """Una barra proporcional a vida/vida_max con los números dentro. Soporta vida fuera de rango y vida_max <= 0."""
    pygame.draw.rect(superficie, VIDA_FONDO, rectangulo, border_radius=3)
    fraccion = 0.0 if vida_max <= 0 else max(0.0, min(1.0, vida / vida_max))
    relleno = pygame.Rect(rectangulo.left + 1, rectangulo.top + 1, round((rectangulo.width - 2) * fraccion),
                          rectangulo.height - 2)
    if relleno.width > 0:
        pygame.draw.rect(superficie, VIDA_BAJA if fraccion < 0.25 else VIDA_BUENA, relleno, border_radius=3)
    pygame.draw.rect(superficie, PANEL_BORDE, rectangulo, width=1, border_radius=3)
    texto_sombreado(superficie, fuentes.chico, f"{vida}/{vida_max}", TEXTO, rectangulo.center)


def dibujar_boton(superficie, fuentes: Fuentes, rectangulo: pygame.Rect, texto: str, resaltado: bool) -> None:
    """Un botón: normal (panel oscuro, borde rojo) o resaltado (relleno rojo, borde y texto dorados)."""
    if resaltado:
        panel(superficie, rectangulo, (ROJO[0], ROJO[1], ROJO[2], 235), ORO, 3)
        color = ORO
    else:
        panel(superficie, rectangulo)
        color = TEXTO
    texto_en(superficie, fuentes.boton, recortar_a_ancho(fuentes.boton, texto, rectangulo.width - 24), color,
             rectangulo.center)


def distribuir_botones(cantidad: int, area: pygame.Rect, alto: int = BOTON_ALTO, separacion: int = BOTON_SEPARACION,
                       alto_minimo: int = BOTON_ALTO_MINIMO) -> list[pygame.Rect]:
    """Rectángulos de 'cantidad' botones dentro de 'area', alineados arriba. Una columna de botones de 'alto'; si no
    caben, se achican hasta 'alto_minimo'; si aun así no caben, se reparten en más columnas."""
    if cantidad <= 0:
        return []
    columnas = 1
    while True:
        filas = -(-cantidad // columnas)
        alto_que_cabe = (area.height - (filas - 1) * separacion) // filas
        if alto_que_cabe >= alto_minimo or filas == 1:
            break
        columnas += 1
    alto_final = min(alto, max(1, alto_que_cabe))
    ancho = (area.width - (columnas - 1) * separacion) // columnas
    rectangulos = []
    for i in range(cantidad):
        columna, fila = divmod(i, filas)
        rectangulos.append(pygame.Rect(area.left + columna * (ancho + separacion),
                                       area.top + fila * (alto_final + separacion), ancho, alto_final))
    return rectangulos

"""
Pruebas de la DECISIÓN de sonidos (View/EventosSonoros.py), con un motor falso que solo anota las llamadas y un reloj que es
simplemente el número 'ahora' que pasa cada prueba. No abre ventana ni mezclador. Se ejecuta desde cualquier carpeta.
"""
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayudas_pygame  # noqa: E402  (fija los controladores dummy antes de importar la Vista)

from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from View import Componentes as c  # noqa: E402
from View.EventosSonoros import EventosSonoros  # noqa: E402

SIN_VENTANA_NI_AUDIO = ayudas_pygame.pygame is not None
BASE_MENU, BASE_JUEGO = 0.5, 0.35
FIN_JUEGO = 89000
LLAVE = "llave"


class MotorFalso:
    """Anota cada llamada; 'posicion' es lo que contestará posicion_musica_ms()."""

    def __init__(self):
        self.llamadas = []
        self.posicion = 0
        self.envolvente_latido = []
        self.duracion_latido_ms = 0

    def efecto(self, nombre):
        self.llamadas.append(("efecto", nombre))

    def musica(self, nombre, volumen, inicio_ms, entrada_ms):
        self.llamadas.append(("musica", nombre, round(volumen, 4), inicio_ms, entrada_ms))

    def volumen_musica(self, volumen):
        self.llamadas.append(("volumen", round(volumen, 4)))

    def parar_musica(self):
        self.llamadas.append(("parar",))

    def posicion_musica_ms(self):
        return self.posicion

    def latido(self, encender):
        self.llamadas.append(("latido", encender))

    def pausar_latido(self, pausado):
        self.llamadas.append(("pausa_latido", pausado))

    def fin(self, nombre):
        self.llamadas.append(("fin", nombre))

    def parar_fin(self, fundido_ms):
        self.llamadas.append(("parar_fin", fundido_ms))

    def tomar(self):
        """Las llamadas desde la última vez (y las olvida)."""
        hechas, self.llamadas = self.llamadas, []
        return hechas

    def efectos(self):
        return [llamada[1] for llamada in self.tomar() if llamada[0] == "efecto"]

    def latidos(self):
        """Las llamadas de Low_Health (encender, apagar, pausar) desde la última vez."""
        return [llamada for llamada in self.tomar() if llamada[0] in ("latido", "pausa_latido")]


def pantalla(nombre, reloj=0, sala=1, suelo=(), terminado=False, activaciones=0, vida=100, vida_max=100, enemigos=(),
             puertas=(None, None, None, None)):
    """Un PantallaDTO con lo único que mira la decisión. 'suelo' son pares (id, clase); 'enemigos' pares (id, vida); 'puertas' lo
    que dice 'cerrada' de cada salida (None: no hay salida)."""
    estado = None
    if nombre in ("juego", "pausa", "victoria", "derrota"):
        objetos = [SimpleNamespace(id=i, clase=k) for i, k in suelo]
        actores = [SimpleNamespace(id=i, vida=v) for i, v in enemigos]
        salidas = [None if p is None else SimpleNamespace(cerrada=p) for p in puertas]
        estado = SimpleNamespace(sala=SimpleNamespace(id=sala, salidas=salidas), reloj=reloj, objetos_suelo=objetos,
                                 terminado=terminado, enemigos=actores,
                                 jugador=SimpleNamespace(vida=vida, vida_max=vida_max))
    return PantallaDTO(nombre, estado=estado, activaciones=activaciones)


def nuevo():
    motor = MotorFalso()
    return motor, EventosSonoros(motor)


def musicas(llamadas):
    return [llamada for llamada in llamadas if llamada[0] == "musica"]


# ================================================================== Click y la sala
def probar_el_primer_cuadro_no_suena_nada_aunque_haya_cambios():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=500, suelo=[("a", "pocion")], activaciones=7), 0)
    assert motor.efectos() == []


def probar_click_cuando_sube_el_contador_y_una_sola_vez_por_cuadro():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu", activaciones=0), 0)
    motor.tomar()
    ev.actualizar(pantalla("menu", activaciones=1), 33)
    assert motor.efectos() == [c.SONIDO_CLICK]
    ev.actualizar(pantalla("menu", activaciones=1), 66)
    assert motor.efectos() == []                                     # el mismo valor: no es otra activación
    ev.actualizar(pantalla("menu", activaciones=4), 99)
    assert motor.efectos() == [c.SONIDO_CLICK]                       # tres activaciones en un cuadro: un solo Click


def probar_click_suena_en_todas_las_pantallas_con_botones_y_en_la_pausa():
    motor, ev = nuevo()
    valor = 0
    for ahora, nombre in enumerate(["menu", "criptas", "nombre", "pausa", "puntajes", "derrota", "victoria"]):
        ev.actualizar(pantalla(nombre, activaciones=valor), ahora * 33)
        motor.tomar()
        valor += 1
        ev.actualizar(pantalla(nombre, activaciones=valor), ahora * 33 + 16)
        assert motor.efectos() == [c.SONIDO_CLICK], nombre


def probar_si_el_contador_baja_no_suena_y_se_toma_como_nuevo_punto_de_partida():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu", activaciones=9), 0)
    motor.tomar()
    ev.actualizar(pantalla("menu", activaciones=2), 33)             # otro controlador: empieza de nuevo
    assert motor.efectos() == []
    ev.actualizar(pantalla("menu", activaciones=3), 66)
    assert motor.efectos() == [c.SONIDO_CLICK]


def probar_click_al_recoger_un_objeto_pero_no_una_llave():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, suelo=[("p", "pocion"), ("k", LLAVE)]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, suelo=[("k", LLAVE)]), 33)       # desaparece la poción
    assert motor.efectos() == [c.SONIDO_CLICK]
    ev.actualizar(pantalla("juego", reloj=20, suelo=[]), 66)                   # desaparece la llave: no hay Click, hay Grab_Key
    assert motor.efectos() == [c.SONIDO_LLAVE]


def probar_dos_objetos_iguales_en_el_suelo_se_cuentan_por_cantidad():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", suelo=[("p", "pocion"), ("p", "pocion")]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, suelo=[("p", "pocion")]), 33)
    assert motor.efectos() == [c.SONIDO_CLICK]


def probar_no_suena_cuando_el_reloj_retrocede_ni_cuando_cambia_la_sala():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=50, suelo=[("p", "pocion")]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=30, suelo=[]), 33)                   # retroceso: el objeto "desaparece" al volver
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=60, sala=2, suelo=[("x", "pocion")]), 66)
    ev.actualizar(pantalla("juego", reloj=70, sala=3, suelo=[]), 99)           # otra sala: el suelo no se compara
    assert motor.efectos() == []


def probar_en_pantallas_que_no_son_la_partida_no_se_compara_el_suelo_pero_el_click_si_suena():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, suelo=[("p", "pocion")]), 0)
    motor.tomar()
    ev.actualizar(pantalla("pausa", reloj=5, suelo=[], activaciones=0), 33)    # la pausa congela la partida
    assert motor.efectos() == []
    ev.actualizar(pantalla("pausa", reloj=5, suelo=[], activaciones=1), 66)
    assert motor.efectos() == [c.SONIDO_CLICK]
    ev.actualizar(pantalla("menu", activaciones=1), 99)
    ev.actualizar(pantalla("juego", reloj=0, suelo=[]), 132)                   # otra partida: primer cuadro, sin comparar
    assert motor.efectos() == []


def probar_main_room_sound_solo_en_la_partida_nueva():
    motor, ev = nuevo()
    ev.actualizar(pantalla("nombre", activaciones=0), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=0, activaciones=1), 33)    # "Aceptar" también subió el contador en este cuadro
    assert motor.efectos() == [c.SONIDO_SALA]                        # suena la sala y NO el Click
    ev.actualizar(pantalla("juego", reloj=0), 66)
    assert motor.efectos() == []                                     # solo el primer cuadro
    ev.actualizar(pantalla("pausa", reloj=0), 99)
    ev.actualizar(pantalla("juego", reloj=0), 132)
    assert motor.efectos() == []                                     # volver de la pausa no es partida nueva


def probar_main_room_sound_no_suena_al_cargar_una_partida_ni_sin_pasar_por_nombre():
    motor, ev = nuevo()
    ev.actualizar(pantalla("nombre", activaciones=0), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=700, activaciones=1), 33)  # cargada: el reloj ya avanzó; solo suena el Click de "Aceptar"
    assert motor.efectos() == [c.SONIDO_CLICK]
    ev.actualizar(pantalla("menu"), 66)
    ev.actualizar(pantalla("juego", reloj=0), 99)                    # sin pasar por "nombre" (p. ej. cargar desde la pausa)
    assert motor.efectos() == []


def probar_click_vuelve_a_sonar_en_el_cuadro_siguiente_al_de_main_room_sound():
    motor, ev = nuevo()
    ev.actualizar(pantalla("nombre", activaciones=0), 0)
    ev.actualizar(pantalla("juego", reloj=0, activaciones=1), 33)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=100, activaciones=2), 66)   # esperar
    assert motor.efectos() == [c.SONIDO_CLICK]


def probar_main_room_sound_suena_otra_vez_en_la_partida_nueva_siguiente():
    motor, ev = nuevo()
    for vuelta in range(2):
        ev.actualizar(pantalla("nombre"), vuelta * 1000)
        motor.tomar()
        ev.actualizar(pantalla("juego", reloj=0), vuelta * 1000 + 33)
        assert motor.efectos() == [c.SONIDO_SALA], vuelta
        ev.actualizar(pantalla("menu"), vuelta * 1000 + 66)


# ================================================================== música
def probar_la_musica_del_menu_empieza_en_2_segundos_y_no_se_reinicia_entre_pantallas_del_mismo_grupo():
    motor, ev = nuevo()
    for ahora, nombre in enumerate(["menu", "criptas", "nombre", "puntajes", "menu"]):
        ev.actualizar(pantalla(nombre), ahora * 33)
    assert musicas(motor.tomar()) == [("musica", "Main_Menu", BASE_MENU, 2000, c.MUSICA_ENTRADA_MS)]


def probar_la_musica_del_juego_no_se_reinicia_con_la_pausa_y_baja_al_35_por_ciento():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    assert musicas(motor.tomar()) == [("musica", "Game_Ambient", BASE_JUEGO, 0, c.MUSICA_ENTRADA_MS)]
    motor.posicion = 5000
    ev.actualizar(pantalla("pausa"), 33)
    assert motor.tomar() == [("volumen", round(BASE_JUEGO * c.MUSICA_PAUSA, 4))]
    ev.actualizar(pantalla("pausa"), 66)
    assert motor.tomar() == []                                       # el mismo volumen no se vuelve a pedir
    ev.actualizar(pantalla("juego"), 99)
    assert motor.tomar() == [("volumen", BASE_JUEGO)]                # vuelve al volumen de siempre, sin reiniciar


def probar_cambiar_de_grupo_apaga_con_un_fundido_a_mano_y_entra_el_tema_nuevo():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu"), 1000)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=0), 2000)                  # empieza el fundido de salida
    assert musicas(motor.tomar()) == []
    ev.actualizar(pantalla("juego", reloj=0), 2000 + c.MUSICA_SALIDA_MS // 2)
    assert motor.tomar() == [("volumen", round(BASE_MENU / 2, 4))]
    ev.actualizar(pantalla("juego", reloj=0), 2000 + c.MUSICA_SALIDA_MS)
    assert motor.tomar() == [("parar",), ("musica", "Game_Ambient", BASE_JUEGO, 0, c.MUSICA_ENTRADA_MS)]


def probar_si_se_vuelve_al_tema_original_durante_el_fundido_el_tema_actual_termina_de_apagarse_y_vuelve_a_entrar():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu"), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego"), 100)
    ev.actualizar(pantalla("menu"), 100 + c.MUSICA_SALIDA_MS)
    llamadas = motor.tomar()
    assert llamadas[-2:] == [("parar",), ("musica", "Main_Menu", BASE_MENU, 0, c.MUSICA_ENTRADA_MS)]


def probar_main_menu_salta_el_silencio_solo_la_primera_vez():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu"), 0)
    ev.actualizar(pantalla("juego"), 100)
    ev.actualizar(pantalla("juego"), 100 + c.MUSICA_SALIDA_MS)       # ya suena Game_Ambient
    ev.actualizar(pantalla("menu"), 5000)
    ev.actualizar(pantalla("menu"), 5000 + c.MUSICA_SALIDA_MS)       # y otra vez Main_Menu
    nombres = [(llamada[1], llamada[3]) for llamada in musicas(motor.tomar())]
    assert nombres == [("Main_Menu", 2000), ("Game_Ambient", 0), ("Main_Menu", 0)]


def probar_el_bucle_a_mano_baja_el_volumen_y_reinicia_en_fin_util():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    motor.tomar()
    motor.posicion = FIN_JUEGO - c.MUSICA_BAJADA_MS - 1
    ev.actualizar(pantalla("juego"), 100)
    assert motor.tomar() == []                                       # todavía falta más de lo que dura la bajada
    motor.posicion = FIN_JUEGO - c.MUSICA_BAJADA_MS // 3
    ev.actualizar(pantalla("juego"), 133)
    assert motor.tomar() == [("volumen", round(BASE_JUEGO / 3, 4))]  # va bajando hacia 0
    motor.posicion = FIN_JUEGO - 1
    ev.actualizar(pantalla("juego"), 166)
    assert motor.tomar() == [("volumen", round(BASE_JUEGO / c.MUSICA_BAJADA_MS, 4))]
    motor.posicion = FIN_JUEGO
    ev.actualizar(pantalla("juego"), 200)
    assert motor.tomar() == [("musica", "Game_Ambient", BASE_JUEGO, 0, c.MUSICA_ENTRADA_MS)]   # empieza de nuevo desde 0
    motor.posicion = 300
    ev.actualizar(pantalla("juego"), 233)
    assert motor.tomar() == []


def probar_el_bucle_de_main_menu_usa_su_propio_fin_util():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu"), 0)
    motor.tomar()
    motor.posicion = 89000                                           # el fin de Game_Ambient: aquí no pasa nada
    ev.actualizar(pantalla("menu"), 33)
    assert motor.tomar() == []
    motor.posicion = 101000
    ev.actualizar(pantalla("menu"), 66)
    assert motor.tomar() == [("musica", "Main_Menu", BASE_MENU, 0, c.MUSICA_ENTRADA_MS)]


def probar_el_bucle_tambien_se_revisa_durante_la_pausa_con_el_volumen_de_la_pausa():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    ev.actualizar(pantalla("pausa"), 33)
    motor.tomar()
    en_pausa = BASE_JUEGO * c.MUSICA_PAUSA
    motor.posicion = FIN_JUEGO - c.MUSICA_BAJADA_MS // 3
    ev.actualizar(pantalla("pausa"), 66)
    assert motor.tomar() == [("volumen", round(en_pausa / 3, 4))]    # baja hacia 0 aunque se esté en pausa
    motor.posicion = FIN_JUEGO
    ev.actualizar(pantalla("pausa"), 99)
    assert motor.tomar() == [("musica", "Game_Ambient", round(en_pausa, 4), 0, c.MUSICA_ENTRADA_MS)]   # y reinicia, bajito
    motor.posicion = 300
    ev.actualizar(pantalla("juego"), 132)
    assert motor.tomar() == [("volumen", BASE_JUEGO)]                # al continuar vuelve al volumen de siempre


def probar_si_la_musica_no_da_noticias_pasado_un_rato_se_reinicia():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    motor.tomar()
    motor.posicion = -1
    ev.actualizar(pantalla("juego"), c.MUSICA_SIN_NOTICIAS_MS)
    assert musicas(motor.tomar()) == []                              # al principio es normal no tener posición todavía
    ev.actualizar(pantalla("juego"), c.MUSICA_SIN_NOTICIAS_MS + 1)
    assert musicas(motor.tomar()) == [("musica", "Game_Ambient", BASE_JUEGO, 0, c.MUSICA_ENTRADA_MS)]


def probar_al_terminar_la_partida_el_ambiente_se_apaga_y_en_victoria_y_derrota_no_hay_musica():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", terminado=True), 1000)           # sigue la demora del fin: el ambiente se desvanece
    ev.actualizar(pantalla("juego", terminado=True), 1000 + c.MUSICA_SALIDA_MS // 2)
    assert motor.tomar() == [("volumen", round(BASE_JUEGO / 2, 4))]
    ev.actualizar(pantalla("derrota", terminado=True), 1000 + c.MUSICA_SALIDA_MS)
    assert motor.tomar() == [("fin", "Defeat_Music"), ("parar",)]            # el ambiente se apaga; la derrota suena en su canal
    ev.actualizar(pantalla("derrota", terminado=True), 3000)
    assert motor.tomar() == []
    ev.actualizar(pantalla("menu"), 4000)
    assert musicas(motor.tomar()) == [("musica", "Main_Menu", BASE_MENU, 2000, c.MUSICA_ENTRADA_MS)]


def probar_una_pantalla_sin_musica_la_detiene():
    motor, ev = nuevo()
    ev.actualizar(pantalla("menu"), 0)
    motor.tomar()
    ev.actualizar(pantalla("victoria", terminado=True), 100)
    ev.actualizar(pantalla("victoria", terminado=True), 100 + c.MUSICA_SALIDA_MS)
    assert motor.tomar()[-1] == ("parar",)


# ================================================================== golpes
def probar_hero_impact_hit_cuando_baja_la_vida_del_protagonista_y_no_al_curarse():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, vida=80), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, vida=60), 33)
    assert motor.efectos() == [c.SONIDO_GOLPE_HEROE]
    ev.actualizar(pantalla("juego", reloj=20, vida=60), 66)
    assert motor.efectos() == []                                     # la misma vida: nada
    ev.actualizar(pantalla("juego", reloj=30, vida=90), 99)
    assert motor.efectos() == []                                     # curarse no es un golpe


def probar_enemies_impact_hit_por_id_solo_cuando_baja_la_vida_de_un_enemigo():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, enemigos=[("a", 10), ("b", 10)]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, enemigos=[("a", 10), ("b", 7)]), 33)    # solo "b" perdió vida
    assert motor.efectos() == [c.SONIDO_GOLPE_ENEMIGO]
    ev.actualizar(pantalla("juego", reloj=20, enemigos=[("b", 7), ("a", 10)]), 66)    # el orden de la lista no importa
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=30, enemigos=[("a", 12), ("b", 9)]), 99)    # se curaron
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=40, enemigos=[("a", 12), ("b", 9), ("c", 5)]), 132)   # entra uno nuevo
    assert motor.efectos() == []


def probar_un_enemigo_que_desaparece_teniendo_vida_suena_como_golpe_pero_uno_sin_vida_no():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, enemigos=[("a", 3), ("b", 0)]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, enemigos=[("b", 0)]), 33)               # "a" murió: golpe final
    assert motor.efectos() == [c.SONIDO_GOLPE_ENEMIGO]
    ev.actualizar(pantalla("juego", reloj=20, enemigos=[]), 66)                       # "b" ya no tenía vida
    assert motor.efectos() == []


def probar_a_lo_sumo_un_golpe_de_cada_tipo_por_cuadro_y_pueden_sonar_los_dos_a_la_vez():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, vida=50, enemigos=[("a", 10), ("b", 10), ("c", 10)]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, vida=10, enemigos=[("a", 1), ("b", 1), ("c", 1)]), 33)
    assert motor.efectos() == [c.SONIDO_GOLPE_ENEMIGO, c.SONIDO_GOLPE_HEROE]          # uno de cada tipo, no seis


def probar_los_golpes_no_suenan_en_el_primer_cuadro_ni_tras_retroceder_el_reloj_ni_al_cambiar_de_sala():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=50, vida=40, enemigos=[("a", 3)]), 0)       # primer cuadro: sin sonidos
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=30, vida=10, enemigos=[]), 33)              # el reloj retrocedió (retroceso o cargar)
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=40, sala=2, vida=5, enemigos=[("z", 1)]), 66)    # otra sala
    assert motor.efectos() == []
    ev.actualizar(pantalla("pausa", reloj=40, sala=2, vida=1, enemigos=[]), 99)       # la pausa no es partida
    assert motor.efectos() == []


# ================================================================== llave y puerta
def probar_grab_key_sound_cuando_desaparece_una_llave_y_no_el_click_ni_para_otros_objetos():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, suelo=[("k", LLAVE), ("p", "pocion")]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, suelo=[("p", "pocion")]), 33)           # se recogió la llave
    assert motor.efectos() == [c.SONIDO_LLAVE]
    ev.actualizar(pantalla("juego", reloj=20, suelo=[]), 66)                          # se recogió la poción
    assert motor.efectos() == [c.SONIDO_CLICK]


def probar_grab_key_sound_no_depende_del_id_de_la_llave():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, suelo=[("itm_cualquier_cosa_nueva", LLAVE)]), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, suelo=[]), 33)
    assert motor.efectos() == [c.SONIDO_LLAVE]


def probar_locked_room_change_cuando_una_puerta_cerrada_pasa_a_abierta_en_la_misma_sala():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, puertas=(True, None, False, None)), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, puertas=(False, None, False, None)), 33)    # se abrió la del norte
    assert motor.efectos() == [c.SONIDO_PUERTA]
    ev.actualizar(pantalla("juego", reloj=20, puertas=(False, None, False, None)), 66)
    assert motor.efectos() == []
    ev.actualizar(pantalla("juego", reloj=30, puertas=(False, None, True, None)), 99)     # una se cerró sola: no suena
    assert motor.efectos() == []


def probar_locked_room_change_suena_al_abrir_y_no_al_cruzar_la_puerta():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, sala=1, puertas=(True, None, None, None)), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, sala=1, puertas=(False, None, None, None)), 33)
    assert motor.efectos() == [c.SONIDO_PUERTA]                                       # al ABRIR
    ev.actualizar(pantalla("juego", reloj=20, sala=2, puertas=(None, False, None, None)), 66)
    assert motor.efectos() == []                                                      # al cruzar, nada
    ev.actualizar(pantalla("juego", reloj=30, sala=3, puertas=(True, None, None, None)), 99)
    ev.actualizar(pantalla("juego", reloj=40, sala=4, puertas=(False, None, None, None)), 132)
    assert motor.efectos() == []                                                      # otra sala: no se compara


# ================================================================== Low_Health
def probar_low_health_con_histeresis_30_para_entrar_y_40_para_salir():
    motor, ev = nuevo()
    pasos = [(50, []), (31, []), (30, [("latido", True)]), (35, []), (40, []), (41, [("latido", False)]),
             (35, []), (31, []), (30, [("latido", True)]), (1, []), (0, [("latido", False)])]
    for i, (vida, esperado) in enumerate(pasos):
        ev.actualizar(pantalla("juego", reloj=i, vida=vida), i * 33)
        assert motor.latidos() == esperado, (vida, esperado)


def probar_low_health_se_apaga_al_terminar_la_partida_y_al_salir_de_juego_y_pausa():
    for destino in ("menu", "derrota", "puntajes"):
        motor, ev = nuevo()
        ev.actualizar(pantalla("juego", vida=20), 0)
        assert motor.latidos() == [("latido", True)]
        ev.actualizar(pantalla(destino, vida=20), 33)
        assert motor.latidos() == [("latido", False)], destino
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", vida=20), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", vida=20, terminado=True), 33)                    # la demora del fin
    assert motor.latidos() == [("latido", False)]


def probar_low_health_se_pausa_con_la_pausa_y_sigue_al_continuar_sin_encender_otra_vez():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", vida=20), 0)
    motor.tomar()
    ev.actualizar(pantalla("pausa", vida=20), 33)
    assert motor.latidos() == [("pausa_latido", True)]
    ev.actualizar(pantalla("pausa", vida=20), 66)
    assert motor.latidos() == []                                                      # ya está en pausa
    ev.actualizar(pantalla("juego", vida=20), 99)
    assert motor.latidos() == [("pausa_latido", False)]                               # sigue, no vuelve a empezar


def probar_low_health_en_la_pausa_se_apaga_si_la_vida_sube_y_no_empieza_con_vida_alta():
    motor, ev = nuevo()
    ev.actualizar(pantalla("pausa", vida=90), 0)
    assert motor.latidos() == []
    ev.actualizar(pantalla("juego", vida=20), 33)
    ev.actualizar(pantalla("pausa", vida=20), 66)
    motor.tomar()
    ev.actualizar(pantalla("pausa", vida=80), 99)                                     # (p. ej. se cargó otra partida)
    assert motor.latidos() == [("latido", False)]


# ================================================================== el latido visual
def _motor_con_envolvente(valores, duracion_ms=None):
    motor, ev = nuevo()
    motor.envolvente_latido = valores
    motor.duracion_latido_ms = duracion_ms if duracion_ms is not None else len(valores) * c.SONIDO_VENTANA_MS
    return motor, ev


def probar_la_intensidad_del_latido_es_none_si_no_suena_y_sigue_la_envolvente_suavizada_si_suena():
    from View import Animaciones as anim
    valores = [0.0] * 10 + [1.0] + [0.0] * 9                                          # un golpe en la ventana 10 (200 ms)
    motor, ev = _motor_con_envolvente(valores)
    ev.actualizar(pantalla("juego", vida=90), 0)
    assert ev.intensidad_latido(0) is None                                            # vida alta: no suena
    ev.actualizar(pantalla("juego", vida=20), 1000)                                   # empieza a sonar en el instante 1000
    suave = anim.suavizar_envolvente(valores)
    assert abs(ev.intensidad_latido(1000) - suave[0]) < 1e-9
    assert abs(ev.intensidad_latido(1000 + 200) - suave[10]) < 1e-9 and suave[10] == 1.0
    mitad = ev.intensidad_latido(1000 + 210)                                          # entre dos ventanas: interpola
    assert abs(mitad - (suave[10] + suave[11]) / 2) < 1e-9
    assert ev.intensidad_latido(1000 + 200) > ev.intensidad_latido(1000 + 180) > ev.intensidad_latido(1000 + 100) == 0.0
    assert abs(ev.intensidad_latido(1000 + 400 + 200) - suave[10]) < 1e-9             # da la vuelta: el sonido va en bucle


def probar_el_latido_visual_no_avanza_durante_la_pausa_y_sigue_despues_sin_perder_el_sitio():
    valores = [0.0] * 10 + [1.0] + [0.0] * 9
    motor, ev = _motor_con_envolvente(valores)
    ev.actualizar(pantalla("juego", vida=20), 0)
    ev.actualizar(pantalla("juego", vida=20), 100)                                    # lleva 100 ms sonando
    ev.actualizar(pantalla("pausa", vida=20), 100)                                    # pausa
    en_pausa = ev.intensidad_latido(100)
    assert ev.intensidad_latido(5000) == en_pausa and ev.intensidad_latido(60000) == en_pausa    # congelado
    ev.actualizar(pantalla("juego", vida=20), 10000)                                  # continúa 9,9 s después
    assert abs(ev.intensidad_latido(10000) - en_pausa) < 1e-9                         # exactamente donde se quedó
    from View import Animaciones as anim
    suave = anim.suavizar_envolvente(valores)
    assert abs(ev.intensidad_latido(10100) - suave[10]) < 1e-9                        # 100 ms más: 200 ms de sonido en total


def probar_el_latido_visual_usa_la_duracion_real_del_sonido_para_dar_la_vuelta():
    valores = [0.0, 1.0, 0.0, 0.0]
    motor, ev = _motor_con_envolvente(valores, duracion_ms=100)                       # dura 100 ms, no 4 ventanas de 20
    ev.actualizar(pantalla("juego", vida=20), 0)
    from View import Animaciones as anim
    suave = anim.suavizar_envolvente(valores)
    assert abs(ev.intensidad_latido(100 + 20) - suave[1]) < 1e-9


def probar_sin_envolvente_no_hay_intensidad_y_la_vina_usa_su_pulso_fijo():
    motor, ev = _motor_con_envolvente([])
    ev.actualizar(pantalla("juego", vida=20), 0)
    assert ev.intensidad_latido(500) is None


def probar_la_alfa_de_la_vineta_sigue_la_intensidad_o_su_pulso_fijo_si_no_hay():
    from View import Animaciones as anim
    maximo, minimo = anim.alfa_vineta(0.0, 0, 1.0), anim.alfa_vineta(0.0, 0, 0.0)
    assert maximo == c.VINETA_ALFA and minimo == round(c.VINETA_ALFA * c.VINETA_PISO_LATIDO)
    assert anim.alfa_vineta(0.0, 0, 0.5) == round(c.VINETA_ALFA * (c.VINETA_PISO_LATIDO + (1 - c.VINETA_PISO_LATIDO) * 0.5))
    assert anim.alfa_vineta(0.0, 12345, 1.0) == anim.alfa_vineta(0.0, 99, 1.0)        # con intensidad, el instante no importa
    fijo = [anim.alfa_vineta(0.1, ms) for ms in range(0, c.VINETA_PERIODO_MS, 50)]
    assert max(fijo) > min(fijo) and anim.alfa_vineta(0.1, 0) == anim.alfa_vineta(0.1, c.VINETA_PERIODO_MS)   # pulso de 1,8 s
    assert anim.alfa_vineta(0.5, 0, 1.0) == 0                                         # con vida alta no hay viñeta


def probar_suavizar_la_envolvente_mantiene_la_escala_la_longitud_y_da_la_vuelta():
    from View import Animaciones as anim
    assert anim.suavizar_envolvente([]) == [] and anim.suavizar_envolvente([0.0, 0.0]) == [0.0, 0.0]
    suave = anim.suavizar_envolvente([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert len(suave) == 6 and max(suave) == 1.0 and min(suave) >= 0.0
    assert suave[1] > 0 and suave[5] > 0                                              # el vecino de atrás (en círculo) también sube


# ================================================================== derrota y victoria
def probar_defeat_music_al_aparecer_la_derrota_y_victory_music_al_aparecer_la_victoria_una_sola_vez():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", vida=1), 0)
    motor.tomar()
    ev.actualizar(pantalla("derrota", terminado=True), 33)
    assert [x for x in motor.tomar() if x[0] in ("fin", "parar_fin")] == [("fin", "Defeat_Music")]
    ev.actualizar(pantalla("derrota", terminado=True), 66)
    assert [x for x in motor.tomar() if x[0] in ("fin", "parar_fin")] == []           # sigue en la misma pantalla
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    motor.tomar()
    ev.actualizar(pantalla("victoria", terminado=True), 33)
    assert [x for x in motor.tomar() if x[0] in ("fin", "parar_fin")] == [("fin", "Victory_Music")]


def probar_al_salir_de_la_pantalla_de_fin_el_sonido_se_apaga_con_fundido_y_entra_main_menu():
    for destino in ("puntajes", "menu", "criptas"):
        motor, ev = nuevo()
        ev.actualizar(pantalla("juego"), 0)
        ev.actualizar(pantalla("derrota", terminado=True), 33)
        ev.actualizar(pantalla("derrota", terminado=True), 33 + c.MUSICA_SALIDA_MS)     # el ambiente ya se apagó
        motor.tomar()
        ev.actualizar(pantalla(destino), 3000)
        llamadas = motor.tomar()
        assert ("parar_fin", c.SONIDO_FIN_FUNDIDO_MS) in llamadas, destino
        assert ("musica", "Main_Menu", 0.5, 2000, c.MUSICA_ENTRADA_MS) in llamadas, destino
        ev.actualizar(pantalla(destino), 3033)
        assert [x for x in motor.tomar() if x[0] == "parar_fin"] == []                # solo una vez


def probar_jugar_de_nuevo_vuelve_a_sonar_la_derrota_en_la_partida_siguiente():
    motor, ev = nuevo()
    for vuelta in range(2):
        ev.actualizar(pantalla("juego"), vuelta * 1000)
        ev.actualizar(pantalla("derrota", terminado=True), vuelta * 1000 + 33)
        ev.actualizar(pantalla("criptas"), vuelta * 1000 + 66)
    assert [x for x in motor.tomar() if x[0] == "fin"] == [("fin", "Defeat_Music"), ("fin", "Defeat_Music")]


def probar_el_ambiente_se_desvanece_al_terminar_la_partida_ya_desde_la_demora_del_fin():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", terminado=True), 1000)                            # empieza el fundido (la demora del fin)
    ev.actualizar(pantalla("juego", terminado=True), 1000 + c.MUSICA_SALIDA_MS // 2)
    assert motor.tomar() == [("volumen", round(0.35 / 2, 4))]                         # Game_Ambient baja...
    ev.actualizar(pantalla("derrota", terminado=True), 1000 + c.MUSICA_SALIDA_MS)
    assert ("parar",) in motor.tomar()                                                # ...y se apaga antes de la derrota


def probar_el_ultimo_golpe_y_la_derrota_suenan_en_cuadros_distintos_y_el_latido_ya_no_suena():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego", reloj=0, vida=20), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=10, vida=0, terminado=True), 33)           # el golpe que mata
    llamadas = motor.tomar()
    assert ("efecto", c.SONIDO_GOLPE_HEROE) in llamadas and ("latido", False) in llamadas
    ev.actualizar(pantalla("derrota", reloj=10, vida=0, terminado=True), 66)
    assert ("fin", "Defeat_Music") in motor.tomar()


def probar_actualizar_cuesta_menos_de_un_milisegundo_por_cuadro():
    motor, ev = nuevo()
    cuadros = [pantalla("juego", reloj=i, suelo=[("a", "pocion"), ("b", LLAVE)] * 4) for i in range(2000)]
    comienzo = time.perf_counter()
    for i, cuadro in enumerate(cuadros):
        motor.posicion = i * 33
        ev.actualizar(cuadro, i * 33)
        motor.llamadas.clear()
    medio_ms = (time.perf_counter() - comienzo) * 1000 / len(cuadros)
    assert medio_ms < 1.0, medio_ms
    print(f"  actualizar(): {medio_ms * 1000:.1f} microsegundos por cuadro")


if __name__ == "__main__":
    probar_el_primer_cuadro_no_suena_nada_aunque_haya_cambios()
    probar_click_cuando_sube_el_contador_y_una_sola_vez_por_cuadro()
    probar_click_suena_en_todas_las_pantallas_con_botones_y_en_la_pausa()
    probar_si_el_contador_baja_no_suena_y_se_toma_como_nuevo_punto_de_partida()
    probar_click_al_recoger_un_objeto_pero_no_una_llave()
    probar_dos_objetos_iguales_en_el_suelo_se_cuentan_por_cantidad()
    probar_no_suena_cuando_el_reloj_retrocede_ni_cuando_cambia_la_sala()
    probar_en_pantallas_que_no_son_la_partida_no_se_compara_el_suelo_pero_el_click_si_suena()
    probar_main_room_sound_solo_en_la_partida_nueva()
    probar_main_room_sound_no_suena_al_cargar_una_partida_ni_sin_pasar_por_nombre()
    probar_click_vuelve_a_sonar_en_el_cuadro_siguiente_al_de_main_room_sound()
    probar_main_room_sound_suena_otra_vez_en_la_partida_nueva_siguiente()
    probar_la_musica_del_menu_empieza_en_2_segundos_y_no_se_reinicia_entre_pantallas_del_mismo_grupo()
    probar_la_musica_del_juego_no_se_reinicia_con_la_pausa_y_baja_al_35_por_ciento()
    probar_cambiar_de_grupo_apaga_con_un_fundido_a_mano_y_entra_el_tema_nuevo()
    probar_si_se_vuelve_al_tema_original_durante_el_fundido_el_tema_actual_termina_de_apagarse_y_vuelve_a_entrar()
    probar_main_menu_salta_el_silencio_solo_la_primera_vez()
    probar_el_bucle_a_mano_baja_el_volumen_y_reinicia_en_fin_util()
    probar_el_bucle_de_main_menu_usa_su_propio_fin_util()
    probar_el_bucle_tambien_se_revisa_durante_la_pausa_con_el_volumen_de_la_pausa()
    probar_si_la_musica_no_da_noticias_pasado_un_rato_se_reinicia()
    probar_al_terminar_la_partida_el_ambiente_se_apaga_y_en_victoria_y_derrota_no_hay_musica()
    probar_una_pantalla_sin_musica_la_detiene()
    probar_hero_impact_hit_cuando_baja_la_vida_del_protagonista_y_no_al_curarse()
    probar_enemies_impact_hit_por_id_solo_cuando_baja_la_vida_de_un_enemigo()
    probar_un_enemigo_que_desaparece_teniendo_vida_suena_como_golpe_pero_uno_sin_vida_no()
    probar_a_lo_sumo_un_golpe_de_cada_tipo_por_cuadro_y_pueden_sonar_los_dos_a_la_vez()
    probar_los_golpes_no_suenan_en_el_primer_cuadro_ni_tras_retroceder_el_reloj_ni_al_cambiar_de_sala()
    probar_grab_key_sound_cuando_desaparece_una_llave_y_no_el_click_ni_para_otros_objetos()
    probar_grab_key_sound_no_depende_del_id_de_la_llave()
    probar_locked_room_change_cuando_una_puerta_cerrada_pasa_a_abierta_en_la_misma_sala()
    probar_locked_room_change_suena_al_abrir_y_no_al_cruzar_la_puerta()
    probar_low_health_con_histeresis_30_para_entrar_y_40_para_salir()
    probar_low_health_se_apaga_al_terminar_la_partida_y_al_salir_de_juego_y_pausa()
    probar_low_health_se_pausa_con_la_pausa_y_sigue_al_continuar_sin_encender_otra_vez()
    probar_low_health_en_la_pausa_se_apaga_si_la_vida_sube_y_no_empieza_con_vida_alta()
    probar_la_intensidad_del_latido_es_none_si_no_suena_y_sigue_la_envolvente_suavizada_si_suena()
    probar_el_latido_visual_no_avanza_durante_la_pausa_y_sigue_despues_sin_perder_el_sitio()
    probar_el_latido_visual_usa_la_duracion_real_del_sonido_para_dar_la_vuelta()
    probar_sin_envolvente_no_hay_intensidad_y_la_vina_usa_su_pulso_fijo()
    probar_la_alfa_de_la_vineta_sigue_la_intensidad_o_su_pulso_fijo_si_no_hay()
    probar_suavizar_la_envolvente_mantiene_la_escala_la_longitud_y_da_la_vuelta()
    probar_defeat_music_al_aparecer_la_derrota_y_victory_music_al_aparecer_la_victoria_una_sola_vez()
    probar_al_salir_de_la_pantalla_de_fin_el_sonido_se_apaga_con_fundido_y_entra_main_menu()
    probar_jugar_de_nuevo_vuelve_a_sonar_la_derrota_en_la_partida_siguiente()
    probar_el_ambiente_se_desvanece_al_terminar_la_partida_ya_desde_la_demora_del_fin()
    probar_el_ultimo_golpe_y_la_derrota_suenan_en_cuadros_distintos_y_el_latido_ya_no_suena()
    probar_actualizar_cuesta_menos_de_un_milisegundo_por_cuadro()
    print("OK: todas las pruebas de la decisión de sonidos pasaron")

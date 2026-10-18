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

    def tomar(self):
        """Las llamadas desde la última vez (y las olvida)."""
        hechas, self.llamadas = self.llamadas, []
        return hechas

    def efectos(self):
        return [llamada[1] for llamada in self.tomar() if llamada[0] == "efecto"]


def pantalla(nombre, reloj=0, sala=1, suelo=(), terminado=False, activaciones=0):
    """Un PantallaDTO con lo único que mira la decisión. 'suelo' son pares (id, clase)."""
    estado = None
    if nombre in ("juego", "pausa", "victoria", "derrota"):
        objetos = [SimpleNamespace(id=i, clase=k) for i, k in suelo]
        estado = SimpleNamespace(sala=SimpleNamespace(id=sala), reloj=reloj, objetos_suelo=objetos, terminado=terminado)
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
    ev.actualizar(pantalla("juego", reloj=20, suelo=[]), 66)                   # desaparece la llave: aquí no hay Click
    assert motor.efectos() == []


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
    ev.actualizar(pantalla("nombre"), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=0), 33)
    assert motor.efectos() == [c.SONIDO_SALA]
    ev.actualizar(pantalla("juego", reloj=0), 66)
    assert motor.efectos() == []                                     # solo el primer cuadro
    ev.actualizar(pantalla("pausa", reloj=0), 99)
    ev.actualizar(pantalla("juego", reloj=0), 132)
    assert motor.efectos() == []                                     # volver de la pausa no es partida nueva


def probar_main_room_sound_no_suena_al_cargar_una_partida_ni_sin_pasar_por_nombre():
    motor, ev = nuevo()
    ev.actualizar(pantalla("nombre"), 0)
    motor.tomar()
    ev.actualizar(pantalla("juego", reloj=700), 33)                  # cargada: el reloj ya avanzó
    assert motor.efectos() == []
    ev.actualizar(pantalla("menu"), 66)
    ev.actualizar(pantalla("juego", reloj=0), 99)                    # sin pasar por "nombre" (p. ej. cargar desde la pausa)
    assert motor.efectos() == []


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


def probar_en_la_pausa_no_se_revisa_el_bucle_y_al_continuar_se_retoma():
    motor, ev = nuevo()
    ev.actualizar(pantalla("juego"), 0)
    ev.actualizar(pantalla("pausa"), 33)
    motor.tomar()
    motor.posicion = FIN_JUEGO + 5000                                # el tiempo pasó durante la pausa
    ev.actualizar(pantalla("pausa"), 66)
    assert musicas(motor.tomar()) == []                              # en pausa no cuenta
    ev.actualizar(pantalla("juego"), 99)
    assert musicas(motor.tomar()) == [("musica", "Game_Ambient", BASE_JUEGO, 0, c.MUSICA_ENTRADA_MS)]


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
    assert motor.tomar() == [("parar",)]
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
    probar_main_room_sound_suena_otra_vez_en_la_partida_nueva_siguiente()
    probar_la_musica_del_menu_empieza_en_2_segundos_y_no_se_reinicia_entre_pantallas_del_mismo_grupo()
    probar_la_musica_del_juego_no_se_reinicia_con_la_pausa_y_baja_al_35_por_ciento()
    probar_cambiar_de_grupo_apaga_con_un_fundido_a_mano_y_entra_el_tema_nuevo()
    probar_si_se_vuelve_al_tema_original_durante_el_fundido_el_tema_actual_termina_de_apagarse_y_vuelve_a_entrar()
    probar_main_menu_salta_el_silencio_solo_la_primera_vez()
    probar_el_bucle_a_mano_baja_el_volumen_y_reinicia_en_fin_util()
    probar_el_bucle_de_main_menu_usa_su_propio_fin_util()
    probar_en_la_pausa_no_se_revisa_el_bucle_y_al_continuar_se_retoma()
    probar_si_la_musica_no_da_noticias_pasado_un_rato_se_reinicia()
    probar_al_terminar_la_partida_el_ambiente_se_apaga_y_en_victoria_y_derrota_no_hay_musica()
    probar_una_pantalla_sin_musica_la_detiene()
    probar_actualizar_cuesta_menos_de_un_milisegundo_por_cuadro()
    print("OK: todas las pruebas de la decisión de sonidos pasaron")

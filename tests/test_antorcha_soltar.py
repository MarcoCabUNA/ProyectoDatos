"""
Pruebas de la regla "soltar una antorcha apaga la que está encendida", con los controles REALES de ControlesJuego dentro de un
ControladorPygame real y servicios reales (paquete offline, carpetas temporales):

    usar     = doble clic sobre la casilla del inventario (o la tecla U)
    soltar   = la tecla G, o Mayús + clic sobre la casilla
    retroceso = la tecla Retroceso (pergamino de retroceso)

Usar una antorcha la CONSUME (sale del inventario) y deja el efecto "antorcha" activo. La regla solo se nota con una SEGUNDA
antorcha en el inventario: al soltarla, el efecto se cancela. La cripta-01 tiene una sola antorcha; las criptas 02, 03 y 04 tienen
dos o tres. Aquí se pone una segunda en el suelo de la sala inicial y un pergamino, y todo lo demás se hace con los controles.
Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import clic, pygame  # noqa: E402
from test_controlador_pygame import Entorno  # noqa: E402

from DTO.ElementoDTO import ELEMENTO_INVENTARIO, ELEMENTO_OBJETO_SUELO, ElementoDTO  # noqa: E402
from UIController.ControlesJuego import DOBLE_CLIC_MS  # noqa: E402

ANTORCHA, PERGAMINO = "itm_antorcha", "itm_pergamino_retroceso"


def partida_con_dos_antorchas_y_un_pergamino(e):
    """La partida de siempre, con una segunda antorcha y un pergamino en el suelo de la sala inicial; los tres objetos ya están
    en el inventario (recogidos con clic, como en el juego)."""
    e.al_juego()
    contexto = e.c._backend._contexto
    sala = contexto.jugador.Sala_Actual
    contexto.mazmorra.soltar_objeto(sala, ANTORCHA, False)
    contexto.mazmorra.soltar_objeto(sala, PERGAMINO, False)
    e.pulsar(pygame.K_z)                                  # esperar: así los controles ven el suelo ya con los objetos nuevos
    for _ in range(3):
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))))
    estado = e.pantalla().estado
    assert sorted(o.id for o in estado.inventario.objetos) == [ANTORCHA, ANTORCHA, PERGAMINO], estado.inventario.objetos
    assert estado.objetos_suelo == [] and estado.efectos == []


def casilla_de(e, id_objeto):
    objetos = e.pantalla().estado.inventario.objetos
    return [i for i, o in enumerate(objetos) if o.id == id_objeto][0]


def punto_de(e, casilla):
    return e.vista.zona(ElementoDTO(ELEMENTO_INVENTARIO, casilla))


def doble_clic_en(e, id_objeto):
    """Usar con doble clic: dos clics sobre la misma casilla, el segundo antes de DOBLE_CLIC_MS."""
    punto = punto_de(e, casilla_de(e, id_objeto))
    e.c.procesar_evento(clic(punto))
    e.reloj.ahora += DOBLE_CLIC_MS // 2
    e.c.procesar_evento(clic(punto))


def soltar_con_g(e, id_objeto):
    e.c.procesar_evento(clic(punto_de(e, casilla_de(e, id_objeto))))      # un clic simple solo coloca el cursor
    e.pulsar(pygame.K_g)


def soltar_con_mayus_y_clic(e, id_objeto):
    e.mods.valor = pygame.KMOD_SHIFT
    try:
        e.c.procesar_evento(clic(punto_de(e, casilla_de(e, id_objeto))))
    finally:
        e.mods.valor = 0


def ids_del_inventario(e):
    return sorted(o.id for o in e.pantalla().estado.inventario.objetos)


def efectos(e):
    return [x.tipo for x in e.pantalla().estado.efectos]


def usar_una_antorcha(e):
    doble_clic_en(e, ANTORCHA)
    assert efectos(e) == ["antorcha"] and ids_del_inventario(e) == [ANTORCHA, PERGAMINO]


# ================================================================== usar consume; soltar la otra apaga
def probar_usar_una_antorcha_con_doble_clic_la_consume_y_deja_el_efecto_activo():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        doble_clic_en(e, ANTORCHA)
        estado = e.pantalla().estado
        assert [o.id for o in estado.inventario.objetos].count(ANTORCHA) == 1          # una sola: la otra se consumió
        assert efectos(e) == ["antorcha"] and estado.efectos[0].restante > 0


def probar_usar_una_antorcha_con_la_tecla_u_tambien_la_consume():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        e.c.procesar_evento(clic(punto_de(e, casilla_de(e, ANTORCHA))))
        e.pulsar(pygame.K_u)
        assert efectos(e) == ["antorcha"] and ids_del_inventario(e) == [ANTORCHA, PERGAMINO]


def probar_soltar_la_otra_antorcha_con_g_cancela_el_efecto():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        usar_una_antorcha(e)
        soltar_con_g(e, ANTORCHA)
        estado = e.pantalla().estado
        assert estado.efectos == []                                                    # el velo desaparece
        assert ids_del_inventario(e) == [PERGAMINO] and [o.id for o in estado.objetos_suelo] == [ANTORCHA]


def probar_soltar_la_otra_antorcha_con_mayus_y_clic_cancela_el_efecto():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        usar_una_antorcha(e)
        soltar_con_mayus_y_clic(e, ANTORCHA)
        assert efectos(e) == [] and ids_del_inventario(e) == [PERGAMINO]


def probar_soltar_otra_cosa_no_apaga_la_antorcha_encendida():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        usar_una_antorcha(e)
        soltar_con_g(e, PERGAMINO)
        assert efectos(e) == ["antorcha"] and ids_del_inventario(e) == [ANTORCHA]


def probar_soltar_una_antorcha_sin_ninguna_encendida_solo_la_deja_en_el_suelo():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        soltar_con_g(e, ANTORCHA)
        estado = e.pantalla().estado
        assert estado.efectos == [] and [o.id for o in estado.objetos_suelo] == [ANTORCHA]
        assert e.pantalla().aviso is None


# ================================================================== pergamino de retroceso, en los dos sentidos
def probar_usar_la_antorcha_y_retroceder_la_devuelve_y_quita_el_efecto():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        doble_clic_en(e, ANTORCHA)
        assert efectos(e) == ["antorcha"]
        e.pulsar(pygame.K_BACKSPACE)                                                   # el pergamino deshace el uso
        assert efectos(e) == []
        assert ids_del_inventario(e) == [ANTORCHA, ANTORCHA]                           # las dos antorchas, y el pergamino se gastó


def probar_soltar_la_otra_antorcha_y_retroceder_devuelve_el_efecto():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        usar_una_antorcha(e)
        antes = e.pantalla().estado.efectos[0].restante
        soltar_con_g(e, ANTORCHA)
        assert efectos(e) == []
        e.pulsar(pygame.K_BACKSPACE)                                                   # el pergamino deshace el soltar
        estado = e.pantalla().estado
        assert [x.tipo for x in estado.efectos] == ["antorcha"]                        # el efecto vuelve
        assert estado.efectos[0].restante == antes                                     # con el mismo tiempo que le quedaba
        assert ids_del_inventario(e) == [ANTORCHA] and estado.objetos_suelo == []     # y la antorcha de vuelta en el inventario


def probar_el_efecto_que_vuelve_con_el_retroceso_se_apaga_a_su_hora():
    with Entorno() as e:
        partida_con_dos_antorchas_y_un_pergamino(e)
        usar_una_antorcha(e)
        soltar_con_g(e, ANTORCHA)
        e.pulsar(pygame.K_BACKSPACE)
        for _ in range(30):                                                            # la duración de la antorcha es 2000 y esperar cuesta 100
            if not efectos(e):
                break
            e.pulsar(pygame.K_z)
        assert efectos(e) == []                                                        # se apagó sola, una sola vez


if __name__ == "__main__":
    probar_usar_una_antorcha_con_doble_clic_la_consume_y_deja_el_efecto_activo()
    probar_usar_una_antorcha_con_la_tecla_u_tambien_la_consume()
    probar_soltar_la_otra_antorcha_con_g_cancela_el_efecto()
    probar_soltar_la_otra_antorcha_con_mayus_y_clic_cancela_el_efecto()
    probar_soltar_otra_cosa_no_apaga_la_antorcha_encendida()
    probar_soltar_una_antorcha_sin_ninguna_encendida_solo_la_deja_en_el_suelo()
    probar_usar_la_antorcha_y_retroceder_la_devuelve_y_quita_el_efecto()
    probar_soltar_la_otra_antorcha_y_retroceder_devuelve_el_efecto()
    probar_el_efecto_que_vuelve_con_el_retroceso_se_apaga_a_su_hora()
    print("OK: todas las pruebas de soltar la antorcha pasaron")

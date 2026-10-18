"""
Pruebas de lo que el ControladorPygame guarda del ratón en la partida: PantallaDTO.elemento_bajo_el_raton (el elemento
que devolvió vista.elemento_en en el último movimiento), para que la Vista muestre el nombre de un objeto del suelo.
Servicios reales, paquete offline y una vista falsa donde cada prueba coloca las zonas. Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import clic, movimiento, pygame, rueda, tecla  # noqa: E402
from test_controlador_pygame import ABAJO, ENTER, ESC, Entorno  # noqa: E402

from DTO.ElementoDTO import ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO, ElementoDTO  # noqa: E402

OBJETO = ElementoDTO(ELEMENTO_OBJETO_SUELO, 0)
SOBRE_NADA = (1000, 1000)


def probar_el_movimiento_guarda_el_elemento_que_devolvio_la_vista():
    with Entorno() as e:
        e.al_juego()
        assert e.pantalla().elemento_bajo_el_raton is None
        sobre_objeto = e.vista.zona(OBJETO)
        e.c.procesar_evento(movimiento(sobre_objeto))
        assert e.pantalla().elemento_bajo_el_raton == OBJETO
        sobre_enemigo = e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 1))
        e.c.procesar_evento(movimiento(sobre_enemigo))
        assert e.pantalla().elemento_bajo_el_raton == ElementoDTO(ELEMENTO_ENEMIGO, 1)     # el último movimiento manda
        e.c.procesar_evento(movimiento(SOBRE_NADA))
        assert e.pantalla().elemento_bajo_el_raton is None                                  # sin nada debajo: None


def probar_solo_la_pantalla_de_juego_recibe_el_elemento():
    with Entorno() as e:
        sobre_boton = e.boton(0)
        e.c.procesar_evento(movimiento(sobre_boton))                                        # en el menú
        assert e.pantalla().pantalla == "menu" and e.pantalla().elemento_bajo_el_raton is None
        e.al_juego()
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().pantalla == "juego" and e.pantalla().elemento_bajo_el_raton == OBJETO
        e.pulsar(ESC)                                                                        # a la pausa
        assert e.pantalla().pantalla == "pausa" and e.pantalla().elemento_bajo_el_raton is None
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().elemento_bajo_el_raton is None                                  # en la pausa tampoco
        e.pulsar(ESC)                                                                        # de vuelta a la partida
        assert e.pantalla().pantalla == "juego" and e.pantalla().elemento_bajo_el_raton is None   # nada desfasado


def probar_las_otras_pantallas_nunca_llevan_el_elemento():
    with Entorno() as e:
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().elemento_bajo_el_raton is None                                  # menú
        e.pulsar(ENTER)                                                                      # criptas
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().pantalla == "criptas" and e.pantalla().elemento_bajo_el_raton is None
        e.pulsar(ENTER)                                                                      # nombre
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().pantalla == "nombre" and e.pantalla().elemento_bajo_el_raton is None
        e.pulsar(*[pygame.K_BACKSPACE] * 16)
        e.escribir("Ana")
        e.pulsar(ENTER)                                                                      # partida
        e.hasta_el_fin()                                                                     # derrota
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().pantalla == "derrota" and e.pantalla().elemento_bajo_el_raton is None
        e.pulsar(ABAJO, ENTER)                                                               # Ver puntajes
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().pantalla == "puntajes" and e.pantalla().elemento_bajo_el_raton is None


def probar_una_tecla_un_clic_o_la_rueda_lo_borran():
    eventos = [("tecla", lambda e: e.c.procesar_evento(tecla(pygame.K_TAB))),
               ("clic izquierdo", lambda e: e.c.procesar_evento(clic(SOBRE_NADA))),
               ("clic derecho", lambda e: e.c.procesar_evento(clic(SOBRE_NADA, 3))),
               ("rueda", lambda e: e.c.procesar_evento(rueda(1)))]
    for nombre, hacer in eventos:
        with Entorno() as e:
            e.al_juego()
            e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
            assert e.pantalla().elemento_bajo_el_raton == OBJETO, nombre
            hacer(e)
            assert e.pantalla().elemento_bajo_el_raton is None, nombre
            e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
            assert e.pantalla().elemento_bajo_el_raton == OBJETO, nombre                    # y se puede volver a guardar


def probar_cambiar_de_pantalla_lo_borra_aunque_no_haya_sido_una_tecla_de_juego():
    with Entorno() as e:
        e.al_juego()
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        e.pulsar(ESC)                                                                        # pausa
        e.pulsar(ESC)                                                                        # y otra vez a la partida
        assert e.pantalla().elemento_bajo_el_raton is None


def probar_no_cambia_el_resaltado_de_los_botones():
    with Entorno() as e:
        sobre_puntajes = e.boton(3)
        e.c.procesar_evento(movimiento(sobre_puntajes))
        assert e.pantalla().seleccion == 3                                                   # el menú resalta igual
        e.c.procesar_evento(movimiento(SOBRE_NADA))
        assert e.pantalla().seleccion == 3
        e.c.procesar_evento(movimiento(e.boton(0)))                                          # de vuelta a "Comenzar juego"
        e.al_juego()
        assert e.pantalla().seleccion == -1
        sobre_esperar = e.boton(0)
        e.c.procesar_evento(movimiento(sobre_esperar))
        assert e.pantalla().seleccion == 0 and e.pantalla().elemento_bajo_el_raton == ElementoDTO(ELEMENTO_BOTON, 0)
        e.c.procesar_evento(movimiento(e.vista.zona(OBJETO)))
        assert e.pantalla().seleccion == -1                                                  # sin botón debajo: se apaga
        e.pulsar(ESC)
        e.c.procesar_evento(movimiento(e.boton(2)))
        assert e.pantalla().seleccion == 2                                                   # y en la pausa también


def probar_no_agrega_consultas_a_la_vista():
    with Entorno() as e:
        e.al_juego()
        zona = e.vista.zona(OBJETO)
        antes = e.vista.consultas
        e.c.procesar_evento(movimiento(zona))
        assert e.vista.consultas - antes == 1                                                # una por movimiento, como antes
        antes = e.vista.consultas
        e.c.pantalla()
        e.c.pantalla()
        assert e.vista.consultas == antes                                                    # pedir la pantalla no consulta
        e.c.procesar_evento(tecla(pygame.K_TAB))
        e.c.procesar_evento(rueda(1))
        assert e.vista.consultas == antes                                                    # tecla y rueda: ninguna
        e.c.procesar_evento(clic(zona))
        assert e.vista.consultas - antes == 1                                                # el clic: la de siempre


if __name__ == "__main__":
    probar_el_movimiento_guarda_el_elemento_que_devolvio_la_vista()
    probar_solo_la_pantalla_de_juego_recibe_el_elemento()
    probar_las_otras_pantallas_nunca_llevan_el_elemento()
    probar_una_tecla_un_clic_o_la_rueda_lo_borran()
    probar_cambiar_de_pantalla_lo_borra_aunque_no_haya_sido_una_tecla_de_juego()
    probar_no_cambia_el_resaltado_de_los_botones()
    probar_no_agrega_consultas_a_la_vista()
    print("OK: todas las pruebas del elemento bajo el ratón pasaron")

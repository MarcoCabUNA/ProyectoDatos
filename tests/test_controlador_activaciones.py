"""
Pruebas de PantallaDTO.activaciones (ControladorPygame): el contador que la Vista usa para tocar el Click. Sube al activar un
botón (clic o Enter) y al esperar en la partida (clic en Esperar o tecla Z); no sube al navegar, resaltar, mover, atacar ni recoger.
Servicios reales (paquete offline) y carpetas temporales. Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import CTRL, clic, movimiento, pygame, tecla  # noqa: E402
from test_controlador_pygame import (ABAJO, ARRIBA, CARGAR, COMENZAR, CONTINUAR, DERECHA, ENTER, ESC, MODO,  # noqa: E402
                                     PUNTAJES_B, Entorno)

from DTO.ElementoDTO import ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO, ElementoDTO  # noqa: E402
from UIController.ControladorPygame import JUEGO, MENU, PAUSA, PUNTAJES  # noqa: E402


def contador(e):
    return e.pantalla().activaciones


def probar_empieza_en_cero_y_navegar_o_resaltar_con_el_raton_no_lo_sube():
    with Entorno() as e:
        assert contador(e) == 0
        e.pulsar(ABAJO, ABAJO, ARRIBA)
        e.c.procesar_evento(movimiento(e.boton(PUNTAJES_B)))
        e.c.procesar_evento(movimiento((900, 900)))
        e.pulsar(ESC)
        assert contador(e) == 0


def probar_enter_y_clic_activan_botones_en_menu_criptas_y_nombre():
    with Entorno() as e:
        e.pulsar(ENTER)                                    # Comenzar juego -> criptas
        assert contador(e) == 1 and e.pantalla().pantalla == "criptas"
        e.clic_en_boton(0)                                 # la primera cripta -> nombre
        assert contador(e) == 2 and e.pantalla().pantalla == "nombre"
        e.escribir("Ana")
        assert contador(e) == 2                            # escribir no es activar nada
        e.pulsar(ENTER)                                    # Aceptar con Enter
        assert contador(e) == 3 and e.pantalla().pantalla == JUEGO


def probar_enter_y_clic_activan_botones_en_la_pausa():
    with Entorno() as e:
        e.al_juego()
        antes = contador(e)
        e.pulsar(ESC)
        assert e.pantalla().pantalla == PAUSA and contador(e) == antes          # Esc no es un botón
        e.pulsar(ENTER)                                    # Continuar
        assert e.pantalla().pantalla == JUEGO and contador(e) == antes + 1
        e.pulsar(ESC)
        e.clic_en_boton(CONTINUAR)
        assert e.pantalla().pantalla == JUEGO and contador(e) == antes + 2


def probar_cambiar_el_modo_o_el_orden_de_puntajes_con_un_boton_cuenta_pero_las_flechas_no():
    with Entorno() as e:
        e.clic_en_boton(MODO)
        assert contador(e) == 1
        e.clic_en_boton(PUNTAJES_B)
        assert e.pantalla().pantalla == PUNTAJES and contador(e) == 2
        e.pulsar(DERECHA)                                  # cambia el orden, pero es una flecha
        assert contador(e) == 2
        e.pulsar(ENTER)                                    # "Cambiar el orden" con Enter
        assert contador(e) == 3


def probar_esperar_cuenta_con_el_clic_en_el_boton_y_con_la_tecla_z():
    with Entorno() as e:
        e.al_juego()
        antes = contador(e)
        e.clic_en_boton(0)
        assert contador(e) == antes + 1
        e.pulsar(pygame.K_z)
        assert contador(e) == antes + 2


def probar_esperar_rechazado_por_el_backend_no_cuenta():
    with Entorno() as e:
        e.al_juego()
        antes = contador(e)
        original = e.c._juego.procesar_evento

        def rechaza(evento, elemento=None):
            original(evento, elemento)
            e.c._juego.aviso = "No se puede esperar ahora."
            return None

        e.c._juego.procesar_evento = rechaza
        e.pulsar(pygame.K_z)
        e.clic_en_boton(0)
        assert contador(e) == antes


def probar_mover_atacar_recoger_retroceder_y_mover_el_raton_no_cuentan():
    with Entorno() as e:
        e.al_juego()
        antes = contador(e)
        e.c.procesar_evento(movimiento(e.boton(0)))                              # sobre Esperar, sin clic
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))))   # recoger la antorcha del suelo
        e.c.procesar_evento(tecla(pygame.K_z, mod=CTRL))                         # Ctrl + Z es retroceder, no esperar
        e.pulsar(pygame.K_TAB, pygame.K_v)                                       # recorrer el inventario y cambiar su orden
        assert contador(e) == antes
        e.pulsar(ARRIBA)                                                         # mover (a la sala de las ratas)
        e.pulsar(pygame.K_SPACE)                                                 # atacar
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 0))))
        assert contador(e) == antes


def probar_en_la_victoria_y_la_derrota_los_botones_cuentan_y_el_contador_nunca_baja():
    with Entorno() as e:
        e.al_juego()
        valores = [contador(e)]
        e.hasta_el_fin()
        valores.append(contador(e))
        antes = valores[-1]
        e.pulsar(ABAJO, ENTER)                             # "Ver puntajes"
        assert e.pantalla().pantalla == PUNTAJES and contador(e) == antes + 1
        e.pulsar(ESC)                                      # de vuelta al menú
        assert e.pantalla().pantalla == MENU
        valores.append(contador(e))
        e.clic_en_boton(COMENZAR)                          # otra partida: el contador sigue desde donde iba
        valores.append(contador(e))
        assert all(valores[i] <= valores[i + 1] for i in range(len(valores) - 1)), valores
        assert valores[-1] == antes + 2


def probar_cargar_partida_desde_el_menu_cuenta_como_boton():
    with Entorno() as e:
        e.clic_en_boton(CARGAR)
        assert contador(e) == 1 and e.pantalla().pantalla == "nombre"


if __name__ == "__main__":
    probar_empieza_en_cero_y_navegar_o_resaltar_con_el_raton_no_lo_sube()
    probar_enter_y_clic_activan_botones_en_menu_criptas_y_nombre()
    probar_enter_y_clic_activan_botones_en_la_pausa()
    probar_cambiar_el_modo_o_el_orden_de_puntajes_con_un_boton_cuenta_pero_las_flechas_no()
    probar_esperar_cuenta_con_el_clic_en_el_boton_y_con_la_tecla_z()
    probar_esperar_rechazado_por_el_backend_no_cuenta()
    probar_mover_atacar_recoger_retroceder_y_mover_el_raton_no_cuentan()
    probar_en_la_victoria_y_la_derrota_los_botones_cuentan_y_el_contador_nunca_baja()
    probar_cargar_partida_desde_el_menu_cuenta_como_boton()
    print("OK: todas las pruebas de las activaciones del controlador pasaron")

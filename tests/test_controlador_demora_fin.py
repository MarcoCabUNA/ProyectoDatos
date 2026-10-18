"""
Pruebas de la demora del fin (Etapa 9, fase 2B): ControladorPygame(demora_fin_ms=...). Con 0 el controlador es el de siempre; con un
valor mayor, al terminar la partida sigue devolviendo la pantalla de JUEGO (con el estado final) durante esa demora y después pasa
a la victoria o la derrota. El puntaje se guarda al terminar, no después. Se ejecuta desde cualquier carpeta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import CONFIG_OFFLINE  # noqa: E402
from ayudas_pygame import Modificadores, Reloj, VistaFalsa, clic, crear_fabrica, movimiento, pygame, rueda, tecla  # noqa: E402
from test_controlador_pygame import (ABAJO, ARRIBA, DERROTA, ENTER, ESC, JUEGO, VICTORIA, ControlesJuego,  # noqa: E402
                                     ControladorPygame, ElementoDTO, ELEMENTO_ENEMIGO, Entorno,
                                     _BackendDeVictoria, letra)
from UIController.ControladorBackend import CRITERIOS_PUNTAJES  # noqa: E402

DEMORA = 1500


def _con_demora(e, demora=DEMORA):
    """El mismo entorno de pruebas, pero con un controlador que tiene demora y mide con el Reloj falso."""
    e.c = ControladorPygame(e.vista, CONFIG_OFFLINE, crear_fabrica(e.carpeta), e.controles, demora_fin_ms=demora,
                            reloj_ms=e.reloj.leer)


def _hasta_la_accion_letal(e):
    """Entra a la sala de las ratas y espera hasta que el estado queda terminado. Devuelve la pantalla de ese momento."""
    e.pulsar(ARRIBA)
    for _ in range(100):
        p = e.pantalla()
        if p.estado.terminado or p.pantalla != JUEGO:
            return p
        e.pulsar(pygame.K_z)
    raise AssertionError("la partida no terminó")


def probar_con_demora_0_o_sin_ella_el_controlador_pasa_de_inmediato_a_la_derrota():
    for explicita in (False, True):
        with Entorno() as e:
            if explicita:
                _con_demora(e, 0)
            e.al_juego("Marta")
            e.pulsar(ARRIBA)
            vistas = []
            for _ in range(100):
                p = e.pantalla()
                vistas.append(p.pantalla)
                if p.pantalla != JUEGO:
                    break
                e.pulsar(pygame.K_z)
            assert vistas[-1] == DERROTA and vistas.count(JUEGO) == len(vistas) - 1, vistas
            p = e.pantalla()
            assert p.estado.terminado and p.puntaje is not None and p.aviso is None


def _al_juego_con_demora(e, nombre="Marta"):
    _con_demora(e)
    e.al_juego(nombre)


def probar_durante_la_demora_sigue_el_juego_con_el_estado_terminado_y_nada_lo_cambia():
    with Entorno() as e:
        _al_juego_con_demora(e)
        p = _hasta_la_accion_letal(e)
        assert p.pantalla == JUEGO and p.estado.terminado and p.estado.resultado == "derrota", p.pantalla
        assert p.estado.jugador.vida <= 0 and p.puntaje is None
        estado = e.c._juego.estado
        inicio = e.reloj.ahora
        enemigo = e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 0))
        boton = e.boton(0)
        for evento in (tecla(pygame.K_z), tecla(ARRIBA), tecla(ABAJO), tecla(ENTER), tecla(ESC), tecla(pygame.K_w),
                       tecla(pygame.K_s), tecla(pygame.K_SPACE), clic(enemigo), clic(enemigo, 3), clic(boton), rueda(1),
                       rueda(-1), movimiento(enemigo)):
            e.c.procesar_evento(evento)
            q = e.pantalla()
            assert q.pantalla == JUEGO and q.estado is estado and q.estado.reloj == estado.reloj, evento
            assert q.aviso is None and q.puntaje is None, (evento, q.aviso)
        e.reloj.ahora = inicio + DEMORA - 1
        assert e.pantalla().pantalla == JUEGO                                   # a los 1499 ms todavía
        e.reloj.ahora = inicio + DEMORA
        p = e.pantalla()
        assert p.pantalla == DERROTA and p.estado is estado and p.puntaje is not None and p.aviso is None
        assert p.opciones == ["Jugar de nuevo", "Ver puntajes", "Menú principal"] and p.seleccion == 0
        e.pulsar(ARRIBA)                                                        # ahora sí: los botones del fin responden
        assert e.pantalla().seleccion == 2


def probar_el_puntaje_se_guarda_al_terminar_antes_de_que_acabe_la_demora():
    with Entorno() as e:
        _al_juego_con_demora(e, "Marta")
        p = _hasta_la_accion_letal(e)
        assert p.pantalla == JUEGO and p.estado.terminado
        tabla = e.c._backend.tabla_puntajes(CRITERIOS_PUNTAJES[0])              # (todavía en la demora)
        assert [x.nombre for x in tabla] == ["Marta"], tabla
        assert e.c._puntaje is not None and e.c._reporte is not None
        e.reloj.ahora += DEMORA
        assert e.pantalla().puntaje is not None and len(e.c._backend.tabla_puntajes(CRITERIOS_PUNTAJES[0])) == 1   # sigue uno solo


def probar_con_victoria_la_demora_es_la_misma_y_se_registra_una_sola_vez():
    backends = []

    def fabrica(config):
        backends.append(_BackendDeVictoria(config))
        return backends[-1]

    vista, reloj, mods = VistaFalsa(), Reloj(), Modificadores()
    c = ControladorPygame(vista, CONFIG_OFFLINE, fabrica, lambda b, s: ControlesJuego(b, s, reloj.leer, mods.leer),
                          demora_fin_ms=DEMORA, reloj_ms=reloj.leer)
    for codigo in (ENTER, ENTER):
        c.procesar_evento(tecla(codigo))
    for caracter in "Ana":
        c.procesar_evento(letra(caracter))
    c.procesar_evento(tecla(ENTER))
    c.procesar_evento(tecla(pygame.K_z))
    inicio = reloj.ahora
    p = c.pantalla()
    assert p.pantalla == JUEGO and p.estado.terminado and p.estado.resultado == "victoria" and p.puntaje is None
    assert backends[-1].registrados == 1                                        # ya registrado, aunque la pantalla siga siendo JUEGO
    for evento in (tecla(pygame.K_z), tecla(ESC), tecla(ENTER), clic((10, 10))):
        c.procesar_evento(evento)
    reloj.ahora = inicio + DEMORA - 1
    assert c.pantalla().pantalla == JUEGO
    reloj.ahora = inicio + DEMORA
    p = c.pantalla()
    assert p.pantalla == VICTORIA and p.puntaje.nombre == "Ana" and p.aviso is None
    assert backends[-1].registrados == 1                                        # nunca dos


def probar_cerrar_la_ventana_durante_la_demora_termina_sin_excepcion():
    with Entorno() as e:
        _al_juego_con_demora(e)
        assert _hasta_la_accion_letal(e).pantalla == JUEGO
        e.c.procesar_evento(pygame.event.Event(pygame.QUIT))
        assert e.c.activo() is False
        assert e.pantalla().pantalla == JUEGO                                   # y pedir un cuadro más no falla
    with Entorno() as e:                                                        # y dentro del bucle real
        _al_juego_con_demora(e)
        cuadros = {"n": 0}

        def eventos():
            cuadros["n"] += 1
            if cuadros["n"] == 1:
                return []
            p = e.pantalla()
            if p.pantalla == JUEGO and p.estado is not None and p.estado.terminado:
                return [pygame.event.Event(pygame.QUIT)]
            return _siguiente(cuadros["n"])
        e.c.ejecutar(eventos)
        assert e.c.activo() is False and e.vista.cerrada


def _siguiente(n):
    """Los eventos que llevan del menú a la sala de las ratas y esperan; uno por cuadro."""
    pasos = [[tecla(ENTER)], [tecla(ENTER)]] + [[tecla(pygame.K_BACKSPACE)]] * 16 + [[letra(ch)] for ch in "Ana"] + \
            [[tecla(ENTER)], [tecla(ARRIBA)]]
    if n - 2 < len(pasos):
        return pasos[n - 2]
    return [tecla(pygame.K_z)]


if __name__ == "__main__":
    probar_con_demora_0_o_sin_ella_el_controlador_pasa_de_inmediato_a_la_derrota()
    probar_durante_la_demora_sigue_el_juego_con_el_estado_terminado_y_nada_lo_cambia()
    probar_el_puntaje_se_guarda_al_terminar_antes_de_que_acabe_la_demora()
    probar_con_victoria_la_demora_es_la_misma_y_se_registra_una_sola_vez()
    probar_cerrar_la_ventana_durante_la_demora_termina_sin_excepcion()
    print("OK: todas las pruebas de la demora del fin pasaron")

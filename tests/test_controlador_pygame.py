import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import CONFIG_OFFLINE, RAIZ, crear_backend  # noqa: E402
from ayudas_pygame import (CTRL, Modificadores, Reloj, VistaFalsa, clic, crear_fabrica, letra, movimiento,  # noqa: E402
                           pygame, rueda, tecla)

import UIController.ControladorPygame as modulo  # noqa: E402
from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.CriptaDTO import ResumenCriptaDTO  # noqa: E402
from DTO.ElementoDTO import (ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ELEMENTO_INVENTARIO,  # noqa: E402
                             ELEMENTO_OBJETO_SUELO, ElementoDTO)
from DTO.EstadoJuegoDTO import EstadoJuegoDTO  # noqa: E402
from DTO.InventarioDTO import InventarioDTO  # noqa: E402
from DTO.PuntajeDTO import PuntajeDTO  # noqa: E402
from DTO.ReporteDatosDTO import ReporteDatosDTO  # noqa: E402
from DTO.SalaDTO import SalaDTO  # noqa: E402
from UIController.ControladorBackend import LARGO_MAXIMO_NOMBRE, ErrorOperacion  # noqa: E402
from UIController.ControladorPygame import (CRIPTAS, DERROTA, JUEGO, MENU, NOMBRE, PAUSA, PUNTAJES, VICTORIA,  # noqa: E402
                                            ControladorPygame)
from UIController.ControlesJuego import AYUDA_JUEGO, DOBLE_CLIC_MS, ControlesJuego  # noqa: E402

ENTER, ESC = pygame.K_RETURN, pygame.K_ESCAPE
ARRIBA, ABAJO, IZQUIERDA, DERECHA = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
OPCIONES_DEL_MENU = ["Comenzar juego", "Modo: Offline", "Cargar partida", "Puntajes", "Salir"]
OPCIONES_DEL_FIN = ["Jugar de nuevo", "Ver puntajes", "Menú principal"]
(COMENZAR, MODO, CARGAR, PUNTAJES_B, SALIR) = range(5)
(CONTINUAR, GUARDAR, CARGAR_EN_PAUSA, AL_MENU) = range(4)
(JUGAR_DE_NUEVO, VER_PUNTAJES, MENU_PRINCIPAL) = range(3)


class Entorno:
    """Un controlador listo para probar: servicios reales, carpetas temporales, ranura de guardado temporal, y una
    vista falsa donde cada prueba coloca los botones y las cosas a las que quiere hacer clic."""

    def __enter__(self):
        self.carpeta = tempfile.mkdtemp()
        self.guardado = os.path.join(self.carpeta, "saves", "partida.sav")
        self._ruta_original = modulo.RUTA_GUARDADO
        modulo.RUTA_GUARDADO = self.guardado
        self.vista, self.reloj, self.mods = VistaFalsa(), Reloj(), Modificadores()
        self.c = ControladorPygame(self.vista, CONFIG_OFFLINE, crear_fabrica(self.carpeta), self.controles)
        return self

    def __exit__(self, *_):
        modulo.RUTA_GUARDADO = self._ruta_original
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def controles(self, backend, estado):
        return ControlesJuego(backend, estado, self.reloj.leer, self.mods.leer)

    def pulsar(self, *codigos):
        for codigo in codigos:
            self.c.procesar_evento(tecla(codigo))

    def escribir(self, texto):
        for caracter in texto:
            self.c.procesar_evento(letra(caracter))

    def pantalla(self):
        return self.c.pantalla()

    def boton(self, indice):
        """Coloca un botón en la vista y devuelve un punto donde hacerle clic."""
        return self.vista.zona(ElementoDTO(ELEMENTO_BOTON, indice))

    def clic_en_boton(self, indice):
        self.c.procesar_evento(clic(self.boton(indice)))

    def al_juego(self, nombre="Ana"):
        """Menú -> Comenzar -> primera cripta -> nombre -> partida (todo con el teclado)."""
        self.pulsar(ENTER, ENTER)
        self.pulsar(*[pygame.K_BACKSPACE] * LARGO_MAXIMO_NOMBRE)         # el campo trae el último nombre: se borra
        self.escribir(nombre)
        self.pulsar(ENTER)
        assert self.pantalla().pantalla == JUEGO, self.pantalla()

    def hasta_el_fin(self):
        """Entra a la sala de las ratas y espera: pierde siempre en este paquete."""
        self.pulsar(ARRIBA)
        for _ in range(100):
            if self.pantalla().pantalla in (VICTORIA, DERROTA):
                return
            self.pulsar(pygame.K_z)
        raise AssertionError("la partida no terminó")

    def al_menu(self):
        self.pulsar(ESC)
        assert self.pantalla().pantalla == MENU


# ---------------------------------------------------------------- menú, configuración y ratón
def probar_el_menu_inicial_y_su_navegacion_da_la_vuelta():
    with Entorno() as e:
        p = e.pantalla()
        assert p.pantalla == MENU and p.titulo == "CRIPTA" and p.opciones == OPCIONES_DEL_MENU
        assert p.seleccion == 0 and p.aviso is None and p.ayuda
        e.pulsar(ABAJO)
        assert e.pantalla().seleccion == 1
        e.pulsar(ARRIBA, ARRIBA)
        assert e.pantalla().seleccion == 4                 # de la primera, hacia arriba, da la vuelta a la última
        e.pulsar(ABAJO)
        assert e.pantalla().seleccion == 0


def probar_pasar_el_raton_por_un_boton_lo_resalta_y_salir_de_el_conserva_el_resaltado():
    with Entorno() as e:
        sobre_puntajes = e.boton(PUNTAJES_B)
        sobre_nada = (900, 900)
        sobre_enemigo = e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 0))    # algo que no es un botón
        e.c.procesar_evento(movimiento(sobre_puntajes))
        assert e.pantalla().seleccion == PUNTAJES_B
        e.c.procesar_evento(movimiento(sobre_nada))
        e.c.procesar_evento(movimiento(sobre_enemigo))
        assert e.pantalla().seleccion == PUNTAJES_B        # en un menú el resaltado no se pierde
        e.pulsar(ABAJO)                                    # y el teclado sigue desde donde dejó el ratón
        assert e.pantalla().seleccion == SALIR


def probar_mover_el_raton_no_borra_el_aviso_pero_una_tecla_si():
    c = ControladorPygame(VistaFalsa(), CONFIG_OFFLINE, lambda config: _BackendQueFalla())
    c.procesar_evento(tecla(ENTER))                        # Comenzar: no se pueden pedir las criptas
    assert "sin conexión" in c.pantalla().aviso
    c.procesar_evento(movimiento((5, 5)))
    c.procesar_evento(movimiento((9, 9)))
    assert "sin conexión" in c.pantalla().aviso            # el ratón se mueve todo el tiempo: no debe borrarlo
    c.procesar_evento(tecla(ABAJO))
    assert c.pantalla().aviso is None


def probar_un_clic_en_cada_boton_del_menu_hace_lo_mismo_que_enter():
    with Entorno() as e:
        e.clic_en_boton(COMENZAR)
        assert e.pantalla().pantalla == CRIPTAS
        e.pulsar(ESC)
        e.clic_en_boton(MODO)
        assert e.pantalla().opciones[1] == "Modo: Online" and e.pantalla().seleccion == MODO
        e.clic_en_boton(MODO)
        assert e.pantalla().opciones[1] == "Modo: Offline"
        e.clic_en_boton(PUNTAJES_B)
        assert e.pantalla().pantalla == PUNTAJES
        e.pulsar(ESC)
        e.clic_en_boton(CARGAR)
        assert e.pantalla().pantalla == NOMBRE and "cargar" in e.pantalla().titulo
        e.pulsar(ESC)
        assert e.c.activo()
        e.clic_en_boton(SALIR)
        assert e.c.activo() is False


def probar_solo_el_clic_izquierdo_sobre_un_boton_activa_algo():
    with Entorno() as e:
        punto = e.boton(COMENZAR)
        sobre_enemigo = e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 0))
        e.c.procesar_evento(clic(punto, 3))                # clic derecho
        e.c.procesar_evento(clic(punto, 2))                # clic del medio
        e.c.procesar_evento(clic(punto, 4))                # la rueda "vieja" de pygame
        e.c.procesar_evento(clic((900, 900)))              # sobre nada
        e.c.procesar_evento(clic(sobre_enemigo))           # sobre algo que no es un botón
        e.c.procesar_evento(rueda(1))                      # la rueda
        assert e.pantalla().pantalla == MENU and e.pantalla().aviso is None
        e.c.procesar_evento(clic(punto))
        assert e.pantalla().pantalla == CRIPTAS


def probar_el_modo_alterna_y_cada_partida_nueva_usa_la_configuracion_vigente():
    configuraciones = []
    carpeta = tempfile.mkdtemp()

    def fabrica(config):
        configuraciones.append(config)
        return crear_backend(carpeta, config)

    try:
        c = ControladorPygame(VistaFalsa(), ConfiguracionDTO(offline=True, cache_size=40), fabrica)
        c.procesar_evento(tecla(ABAJO))
        assert c.pantalla().opciones[1] == "Modo: Offline"
        c.procesar_evento(tecla(ENTER))
        assert c.pantalla().opciones[1] == "Modo: Online" and c.pantalla().seleccion == 1
        c.procesar_evento(tecla(ENTER))
        assert c.pantalla().opciones[1] == "Modo: Offline"
        c.procesar_evento(tecla(ENTER))                    # a Online otra vez
        assert len(configuraciones) == 1                   # elegir el modo no crea nada ni toca la red
        c.procesar_evento(tecla(ARRIBA))                   # a "Comenzar juego"
        c.procesar_evento(tecla(ENTER))
        assert c.pantalla().pantalla == CRIPTAS
        assert len(configuraciones) == 2 and configuraciones[1].offline is False
        assert configuraciones[1].cache_size == 40         # lo demás de la configuración se conserva
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def probar_cada_partida_nueva_o_carga_crea_un_backend_nuevo():
    creados = []
    carpeta = tempfile.mkdtemp()

    def fabrica(config):
        creados.append(config)
        return crear_backend(carpeta, config)

    try:
        c = ControladorPygame(VistaFalsa(), CONFIG_OFFLINE, fabrica)
        assert len(creados) == 1                           # el inicial, solo para ver puntajes
        c.procesar_evento(tecla(ENTER))                    # Comenzar
        c.procesar_evento(tecla(ESC))
        c.procesar_evento(tecla(ENTER))                    # Comenzar otra vez
        assert len(creados) == 3
        c.procesar_evento(tecla(ESC))
        c.procesar_evento(tecla(ABAJO))
        c.procesar_evento(tecla(ABAJO))
        c.procesar_evento(tecla(ENTER))                    # Cargar partida
        assert len(creados) == 4 and c.pantalla().pantalla == NOMBRE
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def probar_salir_termina_el_bucle_con_el_teclado():
    with Entorno() as e:
        e.pulsar(ARRIBA, ENTER)                            # de "Comenzar" hacia arriba: "Salir"
        assert e.c.activo() is False


def probar_la_x_de_la_ventana_termina_desde_cualquier_pantalla():
    preparaciones = (lambda e: None,
                     lambda e: e.pulsar(ENTER),
                     lambda e: e.pulsar(ENTER, ENTER),
                     lambda e: e.al_juego(),
                     lambda e: (e.al_juego(), e.pulsar(ESC)),
                     lambda e: (e.al_juego(), e.hasta_el_fin()),
                     lambda e: e.pulsar(ABAJO, ABAJO, ABAJO, ENTER))
    for preparar in preparaciones:
        with Entorno() as e:
            preparar(e)
            assert e.c.activo() is True
            e.c.procesar_evento(pygame.event.Event(pygame.QUIT))
            assert e.c.activo() is False


# ---------------------------------------------------------------- criptas y nombre
def probar_comenzar_muestra_las_criptas_con_un_boton_volver():
    with Entorno() as e:
        e.pulsar(ENTER)
        p = e.pantalla()
        del_paquete = json.loads((RAIZ / "paquete" / "criptas.json").read_text(encoding="utf-8"))["criptas"]
        esperadas = [f"{d['nombre']} - {d['salas']} salas, dificultad {d['dificultad']}" for d in del_paquete]
        assert p.pantalla == CRIPTAS and p.opciones == esperadas + ["Volver"] and p.ayuda
        assert p.opciones[0] == "Osario menor - 6 salas, dificultad 1"
        e.pulsar(ESC)
        assert e.pantalla().pantalla == MENU
        e.pulsar(ENTER, *[ABAJO] * len(del_paquete), ENTER)    # "Volver" con el teclado: va después de todas las criptas
        assert e.pantalla().pantalla == MENU
        e.pulsar(ENTER)
        e.clic_en_boton(len(del_paquete))                  # "Volver" con el ratón
        assert e.pantalla().pantalla == MENU


def probar_elegir_una_cripta_con_un_clic_lleva_al_nombre():
    with Entorno() as e:
        e.pulsar(ENTER)
        e.clic_en_boton(0)
        p = e.pantalla()
        assert p.pantalla == NOMBRE and p.opciones == ["Aceptar", "Volver"] and "llamas" in p.titulo


def probar_el_nombre_se_escribe_se_borra_y_tiene_limite():
    with Entorno() as e:
        e.pulsar(ENTER, ENTER)
        assert e.pantalla().texto == ""
        e.escribir("Ana")
        assert e.pantalla().texto == "Ana"
        e.pulsar(pygame.K_BACKSPACE)
        assert e.pantalla().texto == "An"
        e.c.procesar_evento(tecla(pygame.K_LSHIFT))                       # sin carácter: se ignora
        e.c.procesar_evento(tecla(pygame.K_TAB, caracter="\t"))           # no imprimible: se ignora
        assert e.pantalla().texto == "An"
        e.escribir("x" * 40)
        assert len(e.pantalla().texto) == LARGO_MAXIMO_NOMBRE
        for _ in range(60):
            e.pulsar(pygame.K_BACKSPACE)
        assert e.pantalla().texto == ""                                   # borrar de más no falla


def probar_aceptar_con_un_nombre_vacio_avisa_y_con_nombre_comienza_la_partida():
    with Entorno() as e:
        e.pulsar(ENTER, ENTER)
        e.clic_en_boton(0)                                 # Aceptar sin nombre
        p = e.pantalla()
        assert p.pantalla == NOMBRE and "nombre" in p.aviso
        e.escribir("   ")
        e.pulsar(ENTER)
        assert e.pantalla().pantalla == NOMBRE
        e.escribir("Ana")
        e.clic_en_boton(0)                                 # Aceptar con el ratón
        assert e.pantalla().pantalla == JUEGO


def probar_volver_desde_el_nombre_y_el_ultimo_nombre_queda_escrito():
    with Entorno() as e:
        e.al_juego("Luis")
        e.pulsar(ESC, ABAJO, ABAJO, ABAJO, ENTER)                         # pausa -> "Salir al menú"
        assert e.pantalla().pantalla == MENU
        e.pulsar(ENTER, ENTER)
        assert e.pantalla().texto == "Luis"                               # no hay que volver a escribirlo
        e.clic_en_boton(1)                                                # "Volver" con el ratón
        assert e.pantalla().pantalla == MENU
        e.pulsar(ENTER, ENTER, ESC)
        assert e.pantalla().pantalla == MENU


# ---------------------------------------------------------------- la partida
def probar_la_partida_empieza_con_su_boton_esperar_y_sin_nada_resaltado():
    with Entorno() as e:
        e.al_juego()
        p = e.pantalla()
        assert p.pantalla == JUEGO and p.opciones == ["Esperar"] and p.seleccion == -1
        assert p.estado.sala.nombre == "Entrada derruida" and p.ayuda == list(AYUDA_JUEGO)
        assert p.aviso is None and p.objetivo is None and p.titulo == ""


def probar_pasar_el_raton_por_el_boton_esperar_lo_resalta_y_al_salir_se_apaga():
    with Entorno() as e:
        e.al_juego()
        sobre_boton = e.boton(0)
        e.c.procesar_evento(movimiento(sobre_boton))
        assert e.pantalla().seleccion == 0
        e.c.procesar_evento(movimiento((900, 900)))
        assert e.pantalla().seleccion == -1


def probar_clic_en_el_boton_esperar_avanza_el_reloj():
    with Entorno() as e:
        e.al_juego()
        antes = e.pantalla().estado.reloj
        e.clic_en_boton(0)
        assert e.pantalla().estado.reloj > antes


def probar_recoger_del_suelo_y_usar_con_doble_clic_llegan_hasta_el_motor():
    with Entorno() as e:
        e.al_juego()
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))))   # la antorcha del suelo
        estado = e.pantalla().estado
        assert [o.id for o in estado.inventario.objetos] == ["itm_antorcha"] and estado.objetos_suelo == []
        casilla = e.vista.zona(ElementoDTO(ELEMENTO_INVENTARIO, 0))
        e.c.procesar_evento(clic(casilla))                                  # selecciona
        e.reloj.ahora += DOBLE_CLIC_MS // 2
        e.c.procesar_evento(clic(casilla))                                  # doble clic: usa la antorcha
        estado = e.pantalla().estado
        assert [o.id for o in estado.inventario.objetos] == ["itm_antorcha"]     # no se gasta: se apaga al soltarla
        assert [x.tipo for x in estado.efectos] == ["antorcha"]


def probar_un_movimiento_rechazado_y_e_sin_puertas_cerradas_dejan_su_aviso():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(pygame.K_LEFT)                                             # no hay salida al oeste
        assert "No hay salida" in e.pantalla().aviso
        e.pulsar(pygame.K_e)
        assert "No hay puertas cerradas" in e.pantalla().aviso
        e.pulsar(pygame.K_z)
        assert e.pantalla().aviso is None


def probar_atacar_con_un_clic_llega_al_motor_y_prefija_el_objetivo():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(pygame.K_w)                                                # a la sala de las ratas
        p = e.pantalla()
        assert p.estado.sala.id == 2 and p.objetivo == "e-201"              # sin ataque previo: el primero
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_ENEMIGO, 1))))
        p = e.pantalla()
        assert any("Jugador ataca a Rata gigante #2" in m for m in p.estado.mensajes), p.estado.mensajes
        if p.pantalla == JUEGO:                                             # (si las ratas ya mataron al jugador, no hay objetivo)
            assert p.objetivo == "e-202"


def probar_la_rueda_del_raton_con_un_solo_objeto_no_rompe_nada():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(pygame.K_1)                                                # tecla sin significado
        e.c.procesar_evento(rueda(-1))
        e.c.procesar_evento(rueda(1))
        assert e.pantalla().pantalla == JUEGO and e.pantalla().aviso is None


def probar_el_controlador_solo_pregunta_a_la_vista_cuando_hace_falta():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(pygame.K_z, pygame.K_TAB, pygame.K_v)                      # teclado: no necesita saber qué hay bajo el ratón
        e.c.procesar_evento(rueda(1))
        e.c.procesar_evento(clic((0, 0), 4))                                # rueda "vieja"
        e.c.procesar_evento(clic((0, 0), 2))                                # botón del medio
        assert e.vista.consultas == 0
        e.c.procesar_evento(clic((0, 0)))                                   # un clic sí
        e.c.procesar_evento(movimiento((0, 0)))                             # un movimiento también (para el resaltado)
        assert e.vista.consultas == 2


# ---------------------------------------------------------------- guardar y cargar desde la partida y la pausa
def probar_ctrl_s_y_f5_guardan_sin_mover_y_el_aviso_sobrevive_al_movimiento_del_raton():
    with Entorno() as e:
        e.al_juego()
        antes = e.pantalla().estado
        for evento in (tecla(pygame.K_s, CTRL), tecla(pygame.K_F5)):
            if os.path.exists(e.guardado):
                os.remove(e.guardado)
            e.c.procesar_evento(evento)
            p = e.pantalla()
            assert p.pantalla == JUEGO and "guardada" in p.aviso and os.path.exists(e.guardado)
            assert p.estado.sala == antes.sala and p.estado.reloj == antes.reloj   # Ctrl+S NO movió al sur
            e.c.procesar_evento(movimiento((3, 3)))
            assert "guardada" in e.pantalla().aviso


def probar_ctrl_l_y_f9_cargan_la_partida_guardada():
    with Entorno() as e:
        e.al_juego()
        e.c.procesar_evento(tecla(pygame.K_s, CTRL))
        e.pulsar(pygame.K_w)                                                # sigue jugando: a la sala 2
        assert e.pantalla().estado.sala.id == 2
        for evento in (tecla(pygame.K_l, CTRL), tecla(pygame.K_F9)):
            e.c.procesar_evento(evento)
            p = e.pantalla()
            assert p.pantalla == JUEGO and p.estado.sala.id == 1 and p.aviso == "Partida cargada."
            e.pulsar(pygame.K_w)
            assert e.pantalla().estado.sala.id == 2                         # y se puede seguir jugando


def probar_cargar_sin_archivo_desde_la_partida_avisa_y_no_pierde_la_partida():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(pygame.K_w)
        e.c.procesar_evento(tecla(pygame.K_l, CTRL))
        p = e.pantalla()
        assert p.pantalla == JUEGO and "no existe" in p.aviso and p.estado.sala.id == 2


def probar_la_pausa_y_sus_botones_con_teclado_y_con_ratón():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(ESC)
        p = e.pantalla()
        assert p.pantalla == PAUSA and p.opciones == ["Continuar", "Guardar partida", "Cargar partida", "Salir al menú"]
        assert p.seleccion == 0 and p.estado is not None and p.ayuda
        e.pulsar(ESC)
        assert e.pantalla().pantalla == JUEGO
        e.pulsar(ESC)
        e.clic_en_boton(CONTINUAR)
        assert e.pantalla().pantalla == JUEGO
        e.pulsar(ESC, ABAJO, ABAJO, ABAJO, ENTER)                           # "Salir al menú" con el teclado
        assert e.pantalla().pantalla == MENU
        e.pulsar(ENTER, ENTER)
        e.escribir("Ana")
        e.pulsar(ENTER, ESC)
        e.clic_en_boton(AL_MENU)                                            # y con el ratón
        assert e.pantalla().pantalla == MENU


def probar_guardar_y_cargar_desde_los_botones_de_la_pausa():
    with Entorno() as e:
        e.al_juego()
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))))   # recoge la antorcha
        e.pulsar(ESC)
        e.clic_en_boton(GUARDAR)
        p = e.pantalla()
        assert p.pantalla == PAUSA and "guardada" in p.aviso and os.path.exists(e.guardado)
        e.pulsar(ESC, pygame.K_w)                                           # sigue jugando después de guardar
        assert e.pantalla().estado.sala.id == 2
        e.pulsar(ESC)
        e.clic_en_boton(CARGAR_EN_PAUSA)
        p = e.pantalla()
        assert p.pantalla == JUEGO and p.estado.sala.id == 1 and p.aviso == "Partida cargada."
        assert [o.id for o in p.estado.inventario.objetos] == ["itm_antorcha"]


def probar_cargar_sin_archivo_desde_la_pausa_avisa_y_sigue_en_la_pausa():
    with Entorno() as e:
        e.al_juego()
        e.pulsar(ESC, ABAJO, ABAJO, ENTER)
        p = e.pantalla()
        assert p.pantalla == PAUSA and "no existe" in p.aviso
        e.pulsar(ESC)
        assert e.pantalla().pantalla == JUEGO and e.pantalla().estado.sala.id == 1


def probar_cargar_desde_el_menu_con_y_sin_archivo():
    with Entorno() as e:
        e.pulsar(ABAJO, ABAJO, ENTER)
        e.escribir("Ana")
        e.pulsar(ENTER)
        p = e.pantalla()
        assert p.pantalla == NOMBRE and "no existe" in p.aviso and p.texto == "Ana"
        e.pulsar(ESC)
        assert e.pantalla().pantalla == MENU and e.c.activo()
        e.al_juego("Ana")                                                   # ahora sí: una partida real
        e.c.procesar_evento(clic(e.vista.zona(ElementoDTO(ELEMENTO_OBJETO_SUELO, 0))))   # recoge la antorcha
        e.c.procesar_evento(tecla(pygame.K_s, CTRL))                        # y la guarda
        e.pulsar(ESC, ABAJO, ABAJO, ABAJO, ENTER)                           # pausa -> "Salir al menú"
        e.pulsar(ABAJO, ABAJO, ENTER)                                       # Cargar partida (menú)
        p = e.pantalla()
        assert p.pantalla == NOMBRE and "cargar" in p.titulo and p.texto == "Ana"
        e.clic_en_boton(0)                                                  # Aceptar
        p = e.pantalla()
        assert p.pantalla == JUEGO and [o.id for o in p.estado.inventario.objetos] == ["itm_antorcha"]


# ---------------------------------------------------------------- fin: victoria y derrota
def probar_al_perder_se_muestra_la_derrota_con_puntaje_reporte_y_tres_botones():
    with Entorno() as e:
        e.al_juego("Marta")
        e.hasta_el_fin()
        p = e.pantalla()
        assert p.pantalla == DERROTA and p.estado.terminado and p.estado.resultado == "derrota"
        assert p.opciones == OPCIONES_DEL_FIN and p.seleccion == 0 and p.ayuda
        assert p.puntaje is not None and p.puntaje.nombre == "Marta" and p.puntaje.mazmorra == "cripta-01"
        assert p.reporte is not None and p.reporte.offline is True and p.reporte.presupuesto
        assert p.aviso is None
        e.pulsar(ARRIBA, pygame.K_z, pygame.K_w, pygame.K_s)                # las teclas de la partida ya no cuentan
        assert e.pantalla().pantalla == DERROTA and e.pantalla().seleccion == 2


def probar_los_botones_de_la_derrota_jugar_de_nuevo_ver_puntajes_y_menu():
    with Entorno() as e:
        e.al_juego("Zoe")
        e.hasta_el_fin()
        e.clic_en_boton(JUGAR_DE_NUEVO)
        p = e.pantalla()
        assert p.pantalla == CRIPTAS and p.opciones[0].startswith("Osario menor")     # otra partida: elegir cripta
        e.pulsar(ENTER, *[pygame.K_BACKSPACE] * 5)
        e.escribir("Zoe")
        e.pulsar(ENTER)
        e.hasta_el_fin()
        e.clic_en_boton(VER_PUNTAJES)
        p = e.pantalla()
        assert p.pantalla == PUNTAJES and [x.nombre for x in p.puntajes] == ["Zoe", "Zoe"]
        e.pulsar(ESC)
        e.pulsar(ENTER, ENTER, ESC, ESC)
        e.al_juego("Ana")
        e.hasta_el_fin()
        e.clic_en_boton(MENU_PRINCIPAL)
        assert e.pantalla().pantalla == MENU


def probar_los_botones_del_fin_funcionan_tambien_con_el_teclado_y_esc_vuelve_al_menu():
    with Entorno() as e:
        e.al_juego()
        e.hasta_el_fin()
        e.pulsar(ABAJO, ENTER)                                              # "Ver puntajes"
        assert e.pantalla().pantalla == PUNTAJES
        e.pulsar(ESC, ENTER, ENTER)
        e.pulsar(*[pygame.K_BACKSPACE] * 5)
        e.escribir("Ana")
        e.pulsar(ENTER)
        e.hasta_el_fin()
        e.pulsar(ESC)
        assert e.pantalla().pantalla == MENU


class _BackendDeVictoria:
    """Un backend que gana en cuanto se espera, para ver la pantalla de victoria sin depender del azar."""

    def __init__(self, config):
        self.registrados = 0

    def criptas(self):
        return [ResumenCriptaDTO(id="cripta-x", nombre="Cripta de prueba", salas=3, dificultad=1)]

    def iniciar(self, id_cripta, nombre):
        return _estado_de_prueba()

    def esperar(self):
        return _estado_de_prueba(terminado=True, resultado="victoria")

    def finalizar(self):
        self.registrados += 1
        return PuntajeDTO("Ana", "cripta-x", "v1", 3, 0, 250)

    def reporte(self):
        return ReporteDatosDTO(solicitudes_realizadas=4, presupuesto=9, aciertos_cache=10, fallos_cache=2)

    def tabla_puntajes(self, criterio):
        return []


def _estado_de_prueba(**cambios):
    base = dict(sala=SalaDTO(1, "Sala", [None] * 4, "v"), jugador=ActorDTO("jugador", "jugador", "J", 30, 30, 5, 1, 100, 1),
                enemigos=[], objetos_suelo=[], efectos=[], inventario=InventarioDTO([], 0, 0, 10), mensajes=[], reloj=0)
    base.update(cambios)
    return EstadoJuegoDTO(**base)


class _BackendDeDosCriptas:
    """Un backend con dos criptas que recuerda cuál se eligió (el paquete real solo tiene una)."""
    elegidas = []

    def __init__(self, config):
        pass

    def criptas(self):
        return [ResumenCriptaDTO(id="cripta-x", nombre="Primera", salas=3, dificultad=1),
                ResumenCriptaDTO(id="cripta-y", nombre="Segunda", salas=5, dificultad=2)]

    def iniciar(self, id_cripta, nombre):
        _BackendDeDosCriptas.elegidas.append(id_cripta)
        return _estado_de_prueba()


def probar_se_inicia_la_cripta_que_se_eligio_con_el_teclado_o_con_el_raton():
    for como in ("teclado", "raton"):
        _BackendDeDosCriptas.elegidas = []
        vista = VistaFalsa()
        c = ControladorPygame(vista, CONFIG_OFFLINE, _BackendDeDosCriptas)
        c.procesar_evento(tecla(ENTER))                                     # Comenzar
        assert c.pantalla().opciones == ["Primera - 3 salas, dificultad 1", "Segunda - 5 salas, dificultad 2", "Volver"]
        if como == "teclado":
            c.procesar_evento(tecla(ABAJO))
            c.procesar_evento(tecla(ENTER))
        else:
            c.procesar_evento(clic(vista.zona(ElementoDTO(ELEMENTO_BOTON, 1))))
        for caracter in "Ana":
            c.procesar_evento(letra(caracter))
        c.procesar_evento(tecla(ENTER))
        assert _BackendDeDosCriptas.elegidas == ["cripta-y"], (como, _BackendDeDosCriptas.elegidas)


def probar_al_ganar_se_muestra_la_victoria_con_los_mismos_botones_y_un_solo_registro():
    backends = []

    def fabrica(config):
        backends.append(_BackendDeVictoria(config))
        return backends[-1]

    vista, reloj, mods = VistaFalsa(), Reloj(), Modificadores()
    c = ControladorPygame(vista, CONFIG_OFFLINE, fabrica, lambda b, e: ControlesJuego(b, e, reloj.leer, mods.leer))
    for codigo in (ENTER, ENTER):
        c.procesar_evento(tecla(codigo))
    for caracter in "Ana":
        c.procesar_evento(letra(caracter))
    c.procesar_evento(tecla(ENTER))
    assert c.pantalla().pantalla == JUEGO
    c.procesar_evento(tecla(pygame.K_z))
    p = c.pantalla()
    assert p.pantalla == VICTORIA and p.opciones == OPCIONES_DEL_FIN and p.estado.resultado == "victoria"
    assert p.puntaje.nombre == "Ana" and p.reporte.solicitudes_realizadas == 4 and p.aviso is None
    assert backends[-1].registrados == 1
    c.procesar_evento(tecla(ENTER))                                         # "Jugar de nuevo"
    assert c.pantalla().pantalla == CRIPTAS


def probar_si_no_se_puede_guardar_el_puntaje_el_fin_se_muestra_igual_con_un_aviso():
    carpeta = tempfile.mkdtemp()
    try:
        bloqueo = os.path.join(carpeta, "bloqueo")
        with open(bloqueo, "w", encoding="utf-8") as archivo:
            archivo.write("esto es un archivo, no una carpeta")
        with Entorno() as e:
            e.c = ControladorPygame(e.vista, CONFIG_OFFLINE,
                                    crear_fabrica(e.carpeta, ruta_puntajes=os.path.join(bloqueo, "puntajes.jsonl")), e.controles)
            e.al_juego()
            e.hasta_el_fin()
            p = e.pantalla()
            assert p.pantalla == DERROTA and p.puntaje is None and "No se pudo guardar el puntaje" in p.aviso
            assert p.reporte is not None and p.estado.terminado and p.opciones == OPCIONES_DEL_FIN
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------- puntajes
def probar_los_puntajes_se_ordenan_con_flechas_con_enter_y_con_el_boton():
    with Entorno() as e:
        for nombre in ("Zoe", "Ana"):
            e.al_juego(nombre)
            e.hasta_el_fin()
            e.al_menu()
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER)                                # "Puntajes"
        p = e.pantalla()
        assert p.pantalla == PUNTAJES and p.criterio == "enemigos" and p.opciones == ["Cambiar el orden", "Volver"]
        assert [x.nombre for x in p.puntajes] == ["Zoe", "Ana"]
        e.pulsar(DERECHA, DERECHA, DERECHA)
        assert e.pantalla().criterio == "nombre" and [x.nombre for x in e.pantalla().puntajes] == ["Ana", "Zoe"]
        e.pulsar(DERECHA)
        assert e.pantalla().criterio == "enemigos"                          # da la vuelta
        e.pulsar(IZQUIERDA)
        assert e.pantalla().criterio == "nombre"
        e.pulsar(ENTER)                                                     # Enter sobre "Cambiar el orden"
        assert e.pantalla().criterio == "enemigos"
        e.clic_en_boton(0)                                                  # y el botón hace lo mismo
        assert e.pantalla().criterio == "tiempo"


def probar_el_boton_volver_de_los_puntajes_y_esc_regresan_al_menu():
    with Entorno() as e:
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER)
        assert e.pantalla().pantalla == PUNTAJES and e.pantalla().puntajes == []
        e.clic_en_boton(1)
        assert e.pantalla().pantalla == MENU
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER, ESC)
        assert e.pantalla().pantalla == MENU


def probar_al_volver_a_entrar_a_los_puntajes_el_orden_vuelve_al_primero():
    with Entorno() as e:
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER)
        e.pulsar(DERECHA, DERECHA)
        assert e.pantalla().criterio == "acciones"
        e.pulsar(ESC)
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER)
        assert e.pantalla().criterio == "enemigos"


# ---------------------------------------------------------------- errores que no cierran el programa
class _BackendQueFalla:
    def __init__(self, criptas=None, error="Falló 'listar criptas': sin conexión"):
        self._criptas, self._error = criptas, error

    def criptas(self):
        if self._criptas is not None:
            return self._criptas
        raise ErrorOperacion(self._error)


def probar_si_no_se_pueden_pedir_las_criptas_el_aviso_sale_en_el_menu():
    c = ControladorPygame(VistaFalsa(), CONFIG_OFFLINE, lambda config: _BackendQueFalla())
    c.procesar_evento(tecla(ENTER))
    p = c.pantalla()
    assert p.pantalla == MENU and "sin conexión" in p.aviso and c.activo()
    c.procesar_evento(tecla(ABAJO))
    assert c.pantalla().aviso is None                                      # el aviso dura hasta la siguiente acción


def probar_una_lista_de_criptas_vacia_avisa():
    c = ControladorPygame(VistaFalsa(), CONFIG_OFFLINE, lambda config: _BackendQueFalla(criptas=[]))
    c.procesar_evento(tecla(ENTER))
    assert c.pantalla().pantalla == MENU and "ninguna cripta" in c.pantalla().aviso


def probar_los_eventos_que_no_interesan_se_ignoran_en_todas_las_pantallas():
    with Entorno() as e:
        eventos = (pygame.event.Event(pygame.KEYUP, key=ENTER, mod=0), pygame.event.Event(pygame.WINDOWENTER),
                   pygame.event.Event(pygame.ACTIVEEVENT, gain=1, state=1))
        for preparar in (lambda: None, lambda: e.pulsar(ENTER), lambda: e.pulsar(ENTER)):
            preparar()
            antes = e.pantalla()
            for evento in eventos:
                e.c.procesar_evento(evento)
            assert e.pantalla() == antes
        assert e.c.activo()


def probar_cada_pantalla_trae_lo_que_la_vista_necesita():
    with Entorno() as e:
        p = e.pantalla()
        assert p.pantalla == MENU and p.opciones and p.ayuda and p.titulo
        e.pulsar(ENTER)
        p = e.pantalla()
        assert p.pantalla == CRIPTAS and p.opciones and p.ayuda and p.titulo
        e.pulsar(ENTER)
        p = e.pantalla()
        assert p.pantalla == NOMBRE and p.opciones == ["Aceptar", "Volver"] and p.ayuda and p.titulo
        e.escribir("Ana")
        e.pulsar(ENTER)
        p = e.pantalla()
        assert p.pantalla == JUEGO and p.estado is not None and p.opciones and p.ayuda
        e.pulsar(ESC)
        p = e.pantalla()
        assert p.pantalla == PAUSA and p.opciones and p.estado is not None and p.ayuda and p.titulo
        e.pulsar(ESC)
        e.hasta_el_fin()
        p = e.pantalla()
        assert p.pantalla == DERROTA and p.opciones and p.puntaje and p.reporte and p.ayuda and p.estado is not None
        e.al_menu()
        e.pulsar(ABAJO, ABAJO, ABAJO, ENTER)
        p = e.pantalla()
        assert p.pantalla == PUNTAJES and p.opciones and p.puntajes and p.ayuda and p.titulo


# ---------------------------------------------------------------- bucle principal
def probar_el_bucle_abre_dibuja_y_cierra_la_vista():
    with Entorno() as e:
        lotes = [[], [movimiento((5, 5)), tecla(ARRIBA)], [tecla(ENTER)]]    # hacia "Salir" y aceptar

        def fuente():
            return lotes.pop(0) if lotes else [pygame.event.Event(pygame.QUIT)]

        e.c.ejecutar(fuente)
        assert e.vista.abierta and e.vista.cerrada
        assert len(e.vista.cuadros) == 3 and e.vista.cuadros[0].pantalla == MENU
        assert e.vista.cuadros[1].seleccion == 4                           # la Vista vio la selección moverse
        assert e.c.activo() is False


def probar_cerrar_la_ventana_termina_el_bucle():
    with Entorno() as e:
        e.c.ejecutar(lambda: [pygame.event.Event(pygame.QUIT)])
        assert e.vista.cerrada and len(e.vista.cuadros) == 1


def probar_la_vista_se_cierra_aunque_el_bucle_falle():
    with Entorno() as e:
        def fuente():
            raise RuntimeError("falló la lectura de eventos")

        try:
            e.c.ejecutar(fuente)
        except RuntimeError:
            assert e.vista.abierta and e.vista.cerrada
            return
        raise AssertionError("Debió propagar el error")


# ---------------------------------------------------------------- arquitectura
def probar_los_controladores_graficos_respetan_las_capas():
    """La Interfaz solo habla con Servicios (y DTO): ni Datos ni Lógica (§6, §7). Sin dict ni ordenamientos de la biblioteca."""
    for nombre in ("ControladorPygame.py", "ControlesJuego.py"):
        texto = (RAIZ / "UIController" / nombre).read_text(encoding="utf-8")
        for linea in texto.splitlines():
            if linea.startswith(("import ", "from ")):
                assert not linea.startswith(("from Data", "from Logic", "import Data", "import Logic", "from Service", "from Estructuras")), (nombre, linea)
        assert "dict(" not in texto and "sorted(" not in texto and ".sort(" not in texto, nombre
    for nombre in ("PantallaDTO.py", "ElementoDTO.py"):
        texto = (RAIZ / "DTO" / nombre).read_text(encoding="utf-8")
        assert "import pygame" not in texto, nombre                          # los DTO no conocen la biblioteca gráfica


if __name__ == "__main__":
    probar_el_menu_inicial_y_su_navegacion_da_la_vuelta()
    probar_pasar_el_raton_por_un_boton_lo_resalta_y_salir_de_el_conserva_el_resaltado()
    probar_mover_el_raton_no_borra_el_aviso_pero_una_tecla_si()
    probar_un_clic_en_cada_boton_del_menu_hace_lo_mismo_que_enter()
    probar_solo_el_clic_izquierdo_sobre_un_boton_activa_algo()
    probar_el_modo_alterna_y_cada_partida_nueva_usa_la_configuracion_vigente()
    probar_cada_partida_nueva_o_carga_crea_un_backend_nuevo()
    probar_salir_termina_el_bucle_con_el_teclado()
    probar_la_x_de_la_ventana_termina_desde_cualquier_pantalla()
    probar_comenzar_muestra_las_criptas_con_un_boton_volver()
    probar_elegir_una_cripta_con_un_clic_lleva_al_nombre()
    probar_el_nombre_se_escribe_se_borra_y_tiene_limite()
    probar_aceptar_con_un_nombre_vacio_avisa_y_con_nombre_comienza_la_partida()
    probar_volver_desde_el_nombre_y_el_ultimo_nombre_queda_escrito()
    probar_la_partida_empieza_con_su_boton_esperar_y_sin_nada_resaltado()
    probar_pasar_el_raton_por_el_boton_esperar_lo_resalta_y_al_salir_se_apaga()
    probar_clic_en_el_boton_esperar_avanza_el_reloj()
    probar_recoger_del_suelo_y_usar_con_doble_clic_llegan_hasta_el_motor()
    probar_un_movimiento_rechazado_y_e_sin_puertas_cerradas_dejan_su_aviso()
    probar_atacar_con_un_clic_llega_al_motor_y_prefija_el_objetivo()
    probar_la_rueda_del_raton_con_un_solo_objeto_no_rompe_nada()
    probar_el_controlador_solo_pregunta_a_la_vista_cuando_hace_falta()
    probar_ctrl_s_y_f5_guardan_sin_mover_y_el_aviso_sobrevive_al_movimiento_del_raton()
    probar_ctrl_l_y_f9_cargan_la_partida_guardada()
    probar_cargar_sin_archivo_desde_la_partida_avisa_y_no_pierde_la_partida()
    probar_la_pausa_y_sus_botones_con_teclado_y_con_ratón()
    probar_guardar_y_cargar_desde_los_botones_de_la_pausa()
    probar_cargar_sin_archivo_desde_la_pausa_avisa_y_sigue_en_la_pausa()
    probar_cargar_desde_el_menu_con_y_sin_archivo()
    probar_al_perder_se_muestra_la_derrota_con_puntaje_reporte_y_tres_botones()
    probar_los_botones_de_la_derrota_jugar_de_nuevo_ver_puntajes_y_menu()
    probar_los_botones_del_fin_funcionan_tambien_con_el_teclado_y_esc_vuelve_al_menu()
    probar_se_inicia_la_cripta_que_se_eligio_con_el_teclado_o_con_el_raton()
    probar_al_ganar_se_muestra_la_victoria_con_los_mismos_botones_y_un_solo_registro()
    probar_si_no_se_puede_guardar_el_puntaje_el_fin_se_muestra_igual_con_un_aviso()
    probar_los_puntajes_se_ordenan_con_flechas_con_enter_y_con_el_boton()
    probar_el_boton_volver_de_los_puntajes_y_esc_regresan_al_menu()
    probar_al_volver_a_entrar_a_los_puntajes_el_orden_vuelve_al_primero()
    probar_si_no_se_pueden_pedir_las_criptas_el_aviso_sale_en_el_menu()
    probar_una_lista_de_criptas_vacia_avisa()
    probar_los_eventos_que_no_interesan_se_ignoran_en_todas_las_pantallas()
    probar_cada_pantalla_trae_lo_que_la_vista_necesita()
    probar_el_bucle_abre_dibuja_y_cierra_la_vista()
    probar_cerrar_la_ventana_termina_el_bucle()
    probar_la_vista_se_cierra_aunque_el_bucle_falle()
    probar_los_controladores_graficos_respetan_las_capas()
    print("OK: todas las pruebas de ControladorPygame pasaron")
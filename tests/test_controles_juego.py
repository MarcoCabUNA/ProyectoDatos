import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import CTRL, MAYUS, Modificadores, Reloj, clic, movimiento, pygame, rueda, tecla  # noqa: E402

from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ElementoDTO import (ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ELEMENTO_INVENTARIO, ELEMENTO_OBJETO_SUELO,  # noqa: E402
                             ELEMENTO_PUERTA, ElementoDTO)
from DTO.EstadoJuegoDTO import EstadoJuegoDTO  # noqa: E402
from DTO.InventarioDTO import InventarioDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.SalaDTO import SalaDTO, SalidaDTO  # noqa: E402
from UIController.ControladorBackend import ErrorOperacion  # noqa: E402
from UIController.ControlesJuego import (AYUDA_JUEGO, BOTONES, DOBLE_CLIC_MS, PIDE_CARGAR, PIDE_GUARDAR,  # noqa: E402
                                         PIDE_PAUSA, ControlesJuego)

IZQUIERDO, MEDIO, DERECHO = 1, 2, 3


# ---------------------------------------------------------------- DTOs a la medida
def objeto(id_objeto, clase="arma"):
    return ObjetoDTO(id=id_objeto, nombre=id_objeto, clase=clase, peso=1, valor=1)


def enemigo(id_enemigo):
    return ActorDTO(id_enemigo, "enemigo", "Rata", 10, 10, 1, 1, 100, 1)


def inventario(objetos=(), cursor=0, criterio=None):
    return InventarioDTO(list(objetos), cursor, len(objetos), 10, criterio=criterio)


def sala(**salidas):
    """sala(N=SalidaDTO(...), E=...): las direcciones que no se nombran no tienen salida."""
    lista = [None, None, None, None]
    for nombre, salida in salidas.items():
        lista[{"N": N, "S": S, "E": E, "O": O}[nombre]] = salida
    return SalaDTO(1, "Sala", lista, "v")


def estado(enemigos=(), suelo=(), inv=None, terminado=False, resultado=None, reloj=0, salas=None):
    return EstadoJuegoDTO(sala=salas if salas is not None else sala(), jugador=ActorDTO("jugador", "jugador", "J", 30, 30, 5, 1, 100, 1),
                          enemigos=list(enemigos), objetos_suelo=list(suelo), efectos=[],
                          inventario=inv if inv is not None else inventario(), mensajes=[], reloj=reloj,
                          terminado=terminado, resultado=resultado)


class BackendFalso:
    """Anota cada llamada. Las acciones devuelven 'estado_actual' (el que la prueba fije). El cursor del inventario
    se mueve como el del servicio real: de a un paso, sin salirse de los extremos."""

    def __init__(self, estado_inicial):
        self.llamadas = []
        self.estado_actual = estado_inicial
        self.falla_con = None

    def _accion(self, *llamada):
        self.llamadas.append(llamada)
        if self.falla_con is not None:
            raise ErrorOperacion(self.falla_con)
        return self.estado_actual

    def _mover_cursor(self, nombre, paso):
        self.llamadas.append((nombre,))
        inv = self.estado_actual.inventario
        cursor = max(0, min(len(inv.objetos) - 1, inv.cursor + paso))
        self.estado_actual = replace(self.estado_actual, inventario=replace(inv, cursor=cursor))
        return self.estado_actual.inventario

    def mover(self, d): return self._accion("mover", d)
    def abrir(self, d): return self._accion("abrir", d)
    def atacar(self, i): return self._accion("atacar", i)
    def esperar(self): return self._accion("esperar")
    def recoger(self, i): return self._accion("recoger", i)
    def soltar(self, i): return self._accion("soltar", i)
    def equipar(self, i): return self._accion("equipar", i)
    def usar(self, i): return self._accion("usar", i)
    def retroceder(self): return self._accion("retroceder")
    def inventario_siguiente(self): return self._mover_cursor("siguiente", +1)
    def inventario_anterior(self): return self._mover_cursor("anterior", -1)

    def inventario_ordenar(self, criterio):
        self.llamadas.append(("ordenar", criterio))
        self.estado_actual = replace(self.estado_actual, inventario=replace(self.estado_actual.inventario, criterio=criterio))
        return self.estado_actual.inventario


class Escena:
    """Los controles, su backend falso y los relojes, listos para usar."""

    def __init__(self, estado_inicial=None):
        self.backend = BackendFalso(estado_inicial if estado_inicial is not None else estado())
        self.reloj, self.mods = Reloj(), Modificadores()
        self.c = ControlesJuego(self.backend, self.backend.estado_actual, self.reloj.leer, self.mods.leer)

    def tecla(self, codigo, mod=0):
        return self.c.procesar_evento(tecla(codigo, mod))

    def clic(self, tipo, indice, boton=IZQUIERDO):
        return self.c.procesar_evento(clic((0, 0), boton), ElementoDTO(tipo, indice))

    @property
    def llamadas(self):
        return self.backend.llamadas


# ---------------------------------------------------------------- teclado: moverse
def probar_wasd_y_flechas_mueven_en_las_cuatro_direcciones():
    pares = ((pygame.K_UP, N), (pygame.K_w, N), (pygame.K_DOWN, S), (pygame.K_s, S),
             (pygame.K_RIGHT, E), (pygame.K_d, E), (pygame.K_LEFT, O), (pygame.K_a, O))
    for codigo, direccion in pares:
        e = Escena()
        assert e.tecla(codigo) is None
        assert e.llamadas == [("mover", direccion)], (codigo, e.llamadas)


# ---------------------------------------------------------------- teclado: Ctrl no se mezcla con las teclas sueltas
def probar_ctrl_s_guarda_y_no_mueve_al_sur_y_ctrl_l_carga():
    for codigo, esperado in ((pygame.K_s, PIDE_GUARDAR), (pygame.K_l, PIDE_CARGAR)):
        e = Escena()
        assert e.tecla(codigo, CTRL) == esperado
        assert e.llamadas == [], "Ctrl + tecla no debe llamar a ninguna acción (Ctrl+S no es mover al sur)"


def probar_f5_y_f9_guardan_y_cargan():
    e = Escena()
    assert e.tecla(pygame.K_F5) == PIDE_GUARDAR and e.tecla(pygame.K_F9) == PIDE_CARGAR
    assert e.llamadas == []


def probar_z_espera_y_ctrl_z_retrocede_sin_esperar():
    e = Escena()
    assert e.tecla(pygame.K_z) is None
    assert e.llamadas == [("esperar",)]
    e = Escena()
    assert e.tecla(pygame.K_z, CTRL) is None
    assert e.llamadas == [("retroceder",)], "Ctrl+Z retrocede y NO espera"


def probar_retroceso_usa_el_pergamino():
    e = Escena()
    e.tecla(pygame.K_BACKSPACE)
    assert e.llamadas == [("retroceder",)]


def probar_ctrl_con_otra_tecla_no_hace_nada():
    e = Escena(estado([enemigo("e-1")], [objeto("itm_a")], inventario([objeto("itm_x")])))
    for codigo in (pygame.K_w, pygame.K_e, pygame.K_q, pygame.K_u, pygame.K_g, pygame.K_v, pygame.K_SPACE, pygame.K_TAB):
        assert e.tecla(codigo, CTRL) is None
    assert e.llamadas == []


def probar_esc_pide_la_pausa_sin_ser_una_accion():
    e = Escena()
    assert e.tecla(pygame.K_ESCAPE) == PIDE_PAUSA
    assert e.llamadas == []


def probar_teclas_desconocidas_y_otros_eventos_se_ignoran():
    e = Escena(estado([enemigo("e-1")], [objeto("itm_a")]))
    for codigo in (pygame.K_x, pygame.K_1, pygame.K_i, pygame.K_F1, pygame.K_RETURN, pygame.K_o):
        assert e.tecla(codigo) is None
    for evento in (pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE, mod=0), movimiento((5, 5))):
        assert e.c.procesar_evento(evento) is None
    assert e.llamadas == [] and e.c.aviso is None


# ---------------------------------------------------------------- teclado: abrir puertas con E
def probar_e_abre_la_unica_puerta_cerrada_sea_cual_sea_su_direccion():
    cerrada = SalidaDTO(2, cerrada=True, llave="itm_llave")
    abierta = SalidaDTO(3)
    for nombre, direccion in (("N", N), ("S", S), ("E", E), ("O", O)):
        e = Escena(estado(salas=sala(**{nombre: cerrada})))
        e.tecla(pygame.K_e)
        assert e.llamadas == [("abrir", direccion)], nombre
    e = Escena(estado(salas=sala(N=abierta, E=cerrada)))                 # una abierta y una cerrada: abre la cerrada
    e.tecla(pygame.K_e)
    assert e.llamadas == [("abrir", E)]


def probar_e_sin_puertas_cerradas_avisa_y_no_llama():
    for salas in (sala(), sala(N=SalidaDTO(2), S=SalidaDTO(3))):
        e = Escena(estado(salas=salas))
        e.tecla(pygame.K_e)
        assert e.llamadas == [] and "No hay puertas cerradas" in e.c.aviso


def probar_e_con_varias_puertas_cerradas_pide_hacer_clic():
    e = Escena(estado(salas=sala(N=SalidaDTO(2, cerrada=True), E=SalidaDTO(3, cerrada=True))))
    e.tecla(pygame.K_e)
    assert e.llamadas == [] and "varias puertas" in e.c.aviso and "clic" in e.c.aviso


# ---------------------------------------------------------------- teclado: atacar con Espacio (objetivo prefijado)
def probar_espacio_sin_enemigos_avisa():
    e = Escena()
    e.tecla(pygame.K_SPACE)
    assert e.llamadas == [] and "No hay enemigos" in e.c.aviso and e.c.objetivo() is None


def probar_espacio_ataca_al_primero_si_no_hay_objetivo_previo():
    e = Escena(estado([enemigo("e-201"), enemigo("e-202")]))
    assert e.c.objetivo() == "e-201"
    e.tecla(pygame.K_SPACE)
    assert e.llamadas == [("atacar", "e-201")]


def probar_el_objetivo_es_el_ultimo_atacado_mientras_siga_en_la_sala():
    e = Escena(estado([enemigo("e-201"), enemigo("e-202"), enemigo("e-203")]))
    e.clic(ELEMENTO_ENEMIGO, 1)                                           # clic sobre el segundo: lo ataca y lo prefija
    assert e.llamadas == [("atacar", "e-202")] and e.c.objetivo() == "e-202"
    e.tecla(pygame.K_SPACE)
    assert e.llamadas[-1] == ("atacar", "e-202")
    e.backend.estado_actual = estado([enemigo("e-201"), enemigo("e-203")])   # el segundo murió
    e.tecla(pygame.K_SPACE)                                               # ataca a e-202 por última vez (aún estaba en la lista)
    assert e.c.objetivo() == "e-201"                                      # y ahora el objetivo vuelve al primero
    e.tecla(pygame.K_SPACE)
    assert e.llamadas[-1] == ("atacar", "e-201")


# ---------------------------------------------------------------- ratón: atacar, recoger, abrir y esperar
def probar_clic_izquierdo_sobre_un_enemigo_lo_ataca():
    for indice, esperado in ((0, "e-201"), (1, "e-202"), (2, "e-203")):
        e = Escena(estado([enemigo("e-201"), enemigo("e-202"), enemigo("e-203")]))
        e.clic(ELEMENTO_ENEMIGO, indice)
        assert e.llamadas == [("atacar", esperado)]


def probar_clic_izquierdo_sobre_un_objeto_del_suelo_lo_recoge():
    suelo = [objeto("itm_a"), objeto("itm_b")]
    for indice, esperado in ((0, "itm_a"), (1, "itm_b")):
        e = Escena(estado(suelo=suelo))
        e.clic(ELEMENTO_OBJETO_SUELO, indice)
        assert e.llamadas == [("recoger", esperado)]


def probar_clic_izquierdo_sobre_una_puerta_la_abre():
    for direccion in (N, S, E, O):
        e = Escena()
        e.clic(ELEMENTO_PUERTA, direccion)
        assert e.llamadas == [("abrir", direccion)]


def probar_clic_sobre_el_boton_esperar_espera():
    e = Escena()
    e.clic(ELEMENTO_BOTON, 0)
    assert e.llamadas == [("esperar",)] and BOTONES == ("Esperar",) and e.c.botones() == ["Esperar"]
    e.clic(ELEMENTO_BOTON, 1)                                             # un botón que no existe: nada
    assert e.llamadas == [("esperar",)]


def probar_fuera_del_inventario_solo_cuenta_el_clic_izquierdo():
    e = Escena(estado([enemigo("e-1")], [objeto("itm_a")]))
    for tipo in (ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO, ELEMENTO_PUERTA, ELEMENTO_BOTON):
        e.clic(tipo, 0, DERECHO)
    assert e.llamadas == []


def probar_clic_en_ninguna_parte_o_con_otros_botones_no_hace_nada():
    e = Escena(estado([enemigo("e-1")]))
    assert e.c.procesar_evento(clic((0, 0)), None) is None                 # no había nada bajo el ratón
    for boton in (MEDIO, 4, 5):                                           # 4 y 5 son la rueda "vieja" que pygame también emite
        e.c.procesar_evento(clic((0, 0), boton), ElementoDTO(ELEMENTO_ENEMIGO, 0))
    assert e.llamadas == [] and e.c.aviso is None


def probar_la_rueda_vieja_y_el_boton_del_medio_sobre_una_casilla_no_la_seleccionan():
    """pygame emite el botón 4 o 5 ADEMÁS de MOUSEWHEEL: sin el filtro, girar la rueda sobre una casilla la seleccionaría."""
    objetos = [objeto("itm_a"), objeto("itm_b"), objeto("itm_c")]
    e = Escena(estado(inv=inventario(objetos, cursor=0)))
    for boton in (MEDIO, 4, 5):
        e.c.procesar_evento(clic((0, 0), boton), ElementoDTO(ELEMENTO_INVENTARIO, 2))
    assert e.llamadas == [] and e.c.estado.inventario.cursor == 0


def probar_un_elemento_que_ya_no_existe_avisa_sin_llamar_al_backend():
    e = Escena(estado([enemigo("e-1")], [objeto("itm_a")], inventario([objeto("itm_x")])))
    for tipo, indice, trozo in ((ELEMENTO_ENEMIGO, 3, "enemigo"), (ELEMENTO_OBJETO_SUELO, 5, "objeto"),
                                (ELEMENTO_INVENTARIO, 9, "objeto")):
        e.clic(tipo, indice)
        assert "ya no está" in e.c.aviso and trozo in e.c.aviso, (tipo, e.c.aviso)
    assert e.llamadas == []


# ---------------------------------------------------------------- inventario: recorrerlo y cambiar la vista
def probar_la_rueda_recorre_el_inventario():
    objetos = [objeto("itm_a"), objeto("itm_b"), objeto("itm_c")]
    e = Escena(estado(inv=inventario(objetos, cursor=1)))
    e.c.procesar_evento(rueda(-1))                                        # hacia abajo: siguiente
    assert e.llamadas == [("siguiente",)] and e.c.estado.inventario.cursor == 2
    e.c.procesar_evento(rueda(1))                                         # hacia arriba: anterior
    e.c.procesar_evento(rueda(3))
    assert e.llamadas == [("siguiente",), ("anterior",), ("anterior",)] and e.c.estado.inventario.cursor == 0
    e.c.procesar_evento(rueda(0))
    assert len(e.llamadas) == 3


def probar_tab_recorre_hacia_adelante_y_mayus_tab_hacia_atras():
    e = Escena(estado(inv=inventario([objeto("itm_a"), objeto("itm_b")], cursor=0)))
    e.tecla(pygame.K_TAB)
    assert e.llamadas == [("siguiente",)] and e.c.estado.inventario.cursor == 1
    e.tecla(pygame.K_TAB, MAYUS)
    assert e.llamadas == [("siguiente",), ("anterior",)] and e.c.estado.inventario.cursor == 0


def probar_recorrer_el_inventario_no_cambia_el_resto_del_estado():
    base = estado([enemigo("e-1")], [objeto("itm_a")], inventario([objeto("itm_x"), objeto("itm_y")]), reloj=77)
    e = Escena(base)
    e.tecla(pygame.K_TAB)
    assert e.c.estado.sala == base.sala and e.c.estado.enemigos == base.enemigos
    assert e.c.estado.reloj == 77 and e.c.estado.objetos_suelo == base.objetos_suelo


def probar_v_cambia_la_vista_en_orden_y_da_la_vuelta():
    e = Escena(estado(inv=inventario([objeto("itm_a")])))
    for esperado in ("peso", "valor", "nombre", None, "peso"):
        e.tecla(pygame.K_v)
        assert e.llamadas[-1] == ("ordenar", esperado), e.llamadas
        assert e.c.estado.inventario.criterio == esperado


# ---------------------------------------------------------------- inventario: Q, U y G sobre el objeto que se está viendo
def probar_q_u_y_g_actuan_sobre_el_objeto_que_marca_el_cursor():
    objetos = [objeto("itm_a"), objeto("itm_b"), objeto("itm_c")]
    for codigo, accion in ((pygame.K_q, "equipar"), (pygame.K_u, "usar"), (pygame.K_g, "soltar")):
        for cursor in (0, 1, 2):
            e = Escena(estado(inv=inventario(objetos, cursor=cursor)))
            e.tecla(codigo)
            assert e.llamadas == [(accion, objetos[cursor].id)], (codigo, cursor, e.llamadas)


def probar_con_el_inventario_vacio_q_u_y_g_avisan_sin_llamar():
    for codigo in (pygame.K_q, pygame.K_u, pygame.K_g):
        e = Escena(estado(inv=inventario()))
        e.tecla(codigo)
        assert e.llamadas == [] and "vacío" in e.c.aviso


# ---------------------------------------------------------------- inventario con el ratón
def probar_clic_derecho_sobre_una_casilla_equipa_ese_objeto_no_el_del_cursor():
    objetos = [objeto("itm_a"), objeto("itm_b"), objeto("itm_c")]
    e = Escena(estado(inv=inventario(objetos, cursor=0)))
    e.clic(ELEMENTO_INVENTARIO, 2, DERECHO)
    assert e.llamadas == [("equipar", "itm_c")]


def probar_mayus_clic_izquierdo_sobre_una_casilla_la_suelta():
    objetos = [objeto("itm_a"), objeto("itm_b")]
    e = Escena(estado(inv=inventario(objetos, cursor=0)))
    e.mods.valor = MAYUS
    e.clic(ELEMENTO_INVENTARIO, 1)
    assert e.llamadas == [("soltar", "itm_b")]
    e.mods.valor = 0
    e.clic(ELEMENTO_INVENTARIO, 1)                                        # sin Mayús ya no suelta: selecciona
    assert e.llamadas[-1] != ("soltar", "itm_b")


def probar_clic_simple_en_una_casilla_la_selecciona_moviendo_el_cursor_paso_a_paso():
    objetos = [objeto("itm_a"), objeto("itm_b"), objeto("itm_c"), objeto("itm_d")]
    e = Escena(estado(inv=inventario(objetos, cursor=0)))
    e.clic(ELEMENTO_INVENTARIO, 3)
    assert e.llamadas == [("siguiente",)] * 3 and e.c.estado.inventario.cursor == 3
    e.reloj.ahora += DOBLE_CLIC_MS * 10
    e.clic(ELEMENTO_INVENTARIO, 1)
    assert e.llamadas[3:] == [("anterior",)] * 2 and e.c.estado.inventario.cursor == 1
    n = len(e.llamadas)
    e.reloj.ahora += DOBLE_CLIC_MS * 10
    e.clic(ELEMENTO_INVENTARIO, 1)                                        # ya está ahí: no mueve nada
    assert len(e.llamadas) == n


def probar_clic_en_una_casilla_nunca_ejecuta_una_accion_del_jugador():
    e = Escena(estado(inv=inventario([objeto("itm_a"), objeto("itm_b")])))
    e.clic(ELEMENTO_INVENTARIO, 1)
    acciones = [x for x in e.llamadas if x[0] in ("usar", "equipar", "soltar", "recoger", "atacar", "mover", "esperar")]
    assert acciones == []


def probar_doble_clic_sobre_la_misma_casilla_usa_el_objeto():
    objetos = [objeto("itm_a"), objeto("itm_b")]
    e = Escena(estado(inv=inventario(objetos)))
    e.clic(ELEMENTO_INVENTARIO, 1)
    e.reloj.ahora += DOBLE_CLIC_MS                                        # justo en el límite todavía cuenta
    e.clic(ELEMENTO_INVENTARIO, 1)
    assert e.llamadas[-1] == ("usar", "itm_b")
    e.reloj.ahora += 50
    e.clic(ELEMENTO_INVENTARIO, 1)                                        # el doble clic se consumió: este es uno nuevo
    assert e.llamadas.count(("usar", "itm_b")) == 1


def probar_dos_clics_lentos_o_en_casillas_distintas_no_son_doble_clic():
    objetos = [objeto("itm_a"), objeto("itm_b")]
    e = Escena(estado(inv=inventario(objetos)))
    e.clic(ELEMENTO_INVENTARIO, 1)
    e.reloj.ahora += DOBLE_CLIC_MS + 1                                    # demasiado lento
    e.clic(ELEMENTO_INVENTARIO, 1)
    e.clic(ELEMENTO_INVENTARIO, 0)                                        # otra casilla, enseguida
    assert [x for x in e.llamadas if x[0] == "usar"] == []


def probar_una_accion_entre_dos_clics_cancela_el_doble_clic():
    objetos = [objeto("itm_a"), objeto("itm_b")]
    e = Escena(estado(inv=inventario(objetos)))
    e.clic(ELEMENTO_INVENTARIO, 1)
    e.tecla(pygame.K_z)                                                   # esperar: el inventario pudo cambiar
    e.clic(ELEMENTO_INVENTARIO, 1)
    assert [x for x in e.llamadas if x[0] == "usar"] == []


# ---------------------------------------------------------------- avisos y estado
def probar_una_accion_rechazada_deja_el_motivo_como_aviso_y_se_borra_en_la_siguiente_accion():
    e = Escena()
    e.backend.estado_actual = estado(resultado="No hay salida en esa dirección.")
    e.tecla(pygame.K_LEFT)
    assert e.c.aviso == "No hay salida en esa dirección."
    e.backend.estado_actual = estado(reloj=100)
    e.tecla(pygame.K_z)
    assert e.c.aviso is None and e.c.estado.reloj == 100


def probar_el_estado_nuevo_reemplaza_al_anterior():
    e = Escena()
    nuevo = estado(reloj=250)
    e.backend.estado_actual = nuevo
    e.tecla(pygame.K_z)
    assert e.c.estado is nuevo


def probar_un_error_de_operacion_se_convierte_en_aviso_y_no_rompe_nada():
    e = Escena(estado([enemigo("e-1")]))
    e.backend.falla_con = "Sin conexión con el servicio"
    for hacer in (lambda: e.tecla(pygame.K_w), lambda: e.clic(ELEMENTO_ENEMIGO, 0), lambda: e.tecla(pygame.K_z, CTRL)):
        hacer()
        assert e.c.aviso == "Sin conexión con el servicio"


def probar_victoria_o_derrota_no_se_toman_por_un_rechazo():
    e = Escena()
    e.backend.estado_actual = estado(terminado=True, resultado="derrota")
    e.tecla(pygame.K_z)
    assert e.c.estado.terminado and e.c.aviso is None


def probar_con_la_partida_terminada_se_ignora_todo():
    e = Escena(estado([enemigo("e-1")], terminado=True, resultado="victoria"))
    for codigo in (pygame.K_w, pygame.K_z, pygame.K_ESCAPE, pygame.K_SPACE):
        assert e.tecla(codigo) is None
    e.clic(ELEMENTO_ENEMIGO, 0)
    e.c.procesar_evento(rueda(1))
    assert e.llamadas == []


def probar_la_ayuda_es_una_copia_y_menciona_los_controles_del_documento():
    e = Escena()
    ayuda = e.c.ayuda()
    ayuda.append("x")
    assert e.c.ayuda() == list(AYUDA_JUEGO)
    texto = " ".join(AYUDA_JUEGO)
    for control in ("WASD", "Espacio", "E ", "Z:", "Tab", "Rueda", "U ", "Q ", "G ", "V:", "Ctrl + Z", "Ctrl + S", "F5", "F9", "Esc"):
        assert control in texto, control


if __name__ == "__main__":
    probar_wasd_y_flechas_mueven_en_las_cuatro_direcciones()
    probar_ctrl_s_guarda_y_no_mueve_al_sur_y_ctrl_l_carga()
    probar_f5_y_f9_guardan_y_cargan()
    probar_z_espera_y_ctrl_z_retrocede_sin_esperar()
    probar_retroceso_usa_el_pergamino()
    probar_ctrl_con_otra_tecla_no_hace_nada()
    probar_esc_pide_la_pausa_sin_ser_una_accion()
    probar_teclas_desconocidas_y_otros_eventos_se_ignoran()
    probar_e_abre_la_unica_puerta_cerrada_sea_cual_sea_su_direccion()
    probar_e_sin_puertas_cerradas_avisa_y_no_llama()
    probar_e_con_varias_puertas_cerradas_pide_hacer_clic()
    probar_espacio_sin_enemigos_avisa()
    probar_espacio_ataca_al_primero_si_no_hay_objetivo_previo()
    probar_el_objetivo_es_el_ultimo_atacado_mientras_siga_en_la_sala()
    probar_clic_izquierdo_sobre_un_enemigo_lo_ataca()
    probar_clic_izquierdo_sobre_un_objeto_del_suelo_lo_recoge()
    probar_clic_izquierdo_sobre_una_puerta_la_abre()
    probar_clic_sobre_el_boton_esperar_espera()
    probar_fuera_del_inventario_solo_cuenta_el_clic_izquierdo()
    probar_clic_en_ninguna_parte_o_con_otros_botones_no_hace_nada()
    probar_la_rueda_vieja_y_el_boton_del_medio_sobre_una_casilla_no_la_seleccionan()
    probar_un_elemento_que_ya_no_existe_avisa_sin_llamar_al_backend()
    probar_la_rueda_recorre_el_inventario()
    probar_tab_recorre_hacia_adelante_y_mayus_tab_hacia_atras()
    probar_recorrer_el_inventario_no_cambia_el_resto_del_estado()
    probar_v_cambia_la_vista_en_orden_y_da_la_vuelta()
    probar_q_u_y_g_actuan_sobre_el_objeto_que_marca_el_cursor()
    probar_con_el_inventario_vacio_q_u_y_g_avisan_sin_llamar()
    probar_clic_derecho_sobre_una_casilla_equipa_ese_objeto_no_el_del_cursor()
    probar_mayus_clic_izquierdo_sobre_una_casilla_la_suelta()
    probar_clic_simple_en_una_casilla_la_selecciona_moviendo_el_cursor_paso_a_paso()
    probar_clic_en_una_casilla_nunca_ejecuta_una_accion_del_jugador()
    probar_doble_clic_sobre_la_misma_casilla_usa_el_objeto()
    probar_dos_clics_lentos_o_en_casillas_distintas_no_son_doble_clic()
    probar_una_accion_entre_dos_clics_cancela_el_doble_clic()
    probar_una_accion_rechazada_deja_el_motivo_como_aviso_y_se_borra_en_la_siguiente_accion()
    probar_el_estado_nuevo_reemplaza_al_anterior()
    probar_un_error_de_operacion_se_convierte_en_aviso_y_no_rompe_nada()
    probar_victoria_o_derrota_no_se_toman_por_un_rechazo()
    probar_con_la_partida_terminada_se_ignora_todo()
    probar_la_ayuda_es_una_copia_y_menciona_los_controles_del_documento()
    print("OK: todas las pruebas de ControlesJuego pasaron")
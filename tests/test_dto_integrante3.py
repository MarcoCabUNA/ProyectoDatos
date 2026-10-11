import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.AccionDTO import AccionDTO
from DTO.ActorDTO import ActorDTO
from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import E, indice_direccion
from DTO.EfectoDTO import EfectoDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.InventarioDTO import InventarioDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.PuntajeDTO import PuntajeDTO
from DTO.SalaDTO import SalaDTO


def _cripta():
    return CriptaDTO.desde_diccionario({
        "id": "cripta-01", "version": "a3f91c", "salas_total": 20, "paginas": 2,
        "salas_por_pagina": 10, "sala_inicial": 1, "sala_salida": 20,
        "llave_salida": "itm_llave_maestra", "presupuesto_solicitudes": 50,
        "inventario_max": 10,
        "jugador": {"vida_max": 20, "ataque": 5, "defensa": 2, "velocidad": 100}})


def _sala():
    # Sala 4 con una puerta cerrada al Este (índice 2)
    return SalaDTO.desde_diccionario(
        {"id": 4, "nombre": "Sala de ratas",
         "salidas": {"E": {"sala": 5, "cerrada": True, "llave": "itm_llave_hierro"}}},
        version="a3f91c")


def _daga():
    return ObjetoDTO.desde_diccionario(
        {"id": "itm_daga_oxidada", "nombre": "Daga oxidada", "clase": "arma",
         "peso": 2, "valor": 15, "ataque_bonus": 3})


def probar_accion_ida_y_vuelta():
    acciones = [
        AccionDTO("mover", direccion=0),
        AccionDTO("abrir", direccion=2),
        AccionDTO("atacar", objetivo="e-201"),
        AccionDTO("recoger", objeto="itm_daga_oxidada"),
        AccionDTO("esperar"),
        AccionDTO("retroceder"),
    ]
    for accion in acciones:
        assert AccionDTO.desde_linea(accion.a_linea()) == accion
    assert AccionDTO("mover", direccion=0).a_linea() == "mover|0||"
    assert AccionDTO("atacar", objetivo="e-201").a_linea() == "atacar||e-201|"


def probar_accion_linea_invalida():
    try:
        AccionDTO.desde_linea("mover|0")
    except ValueError:
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_accion_inmutable():
    accion = AccionDTO("esperar")
    try:
        accion.tipo = "mover"
    except Exception:
        return
    raise AssertionError("El DTO debería ser inmutable")


def probar_accion_abrir_apunta_a_una_salida_de_la_sala():
    # Cruce con el integrante 2: la dirección 'E' es el índice 2 de SalaDTO.salidas
    sala = _sala()
    accion = AccionDTO("abrir", direccion=indice_direccion("E"))
    assert accion.direccion == E == 2
    assert accion.a_linea() == "abrir|2||"
    assert sala.salidas[accion.direccion].llave == "itm_llave_hierro"


def probar_accion_objetivo_coincide_con_actor():
    # Cruce con el integrante 1: el objetivo de atacar es el id de instancia del actor
    rata = ActorDTO("e-201", "rata_gigante", "Rata gigante #1", 8, 8, 3, 1, 150, 4)
    accion = AccionDTO("atacar", objetivo=rata.id)
    assert AccionDTO.desde_linea(accion.a_linea()).objetivo == "e-201"


def probar_puntaje_ida_y_vuelta():
    puntaje = PuntajeDTO("Ana", "cripta-01", "a3f91c", 42, 5, 1800)
    assert PuntajeDTO.desde_diccionario(puntaje.a_diccionario()) == puntaje


def probar_puntaje_se_arma_desde_la_cripta():
    # Cruce con el integrante 2: mazmorra y version salen de CriptaDTO
    cripta = _cripta()
    puntaje = PuntajeDTO("Ana", cripta.id, cripta.version, 42, 5, 1800)
    assert (puntaje.mazmorra, puntaje.version) == ("cripta-01", "a3f91c")


def probar_inventario_con_objetos_reales():
    daga = _daga()
    pocion = ObjetoDTO.desde_diccionario(
        {"id": "itm_pocion_menor", "nombre": "Poción menor", "clase": "pocion",
         "peso": 1, "valor": 10, "cura": 20, "duracion": 0})
    cripta = _cripta()
    inv = InventarioDTO([daga, pocion], cursor=0, capacidad=2,
                        capacidad_maxima=cripta.inventario_max, arma_equipada=daga.id)
    assert inv.capacidad_maxima == 10
    assert inv.criterio is None and inv.armadura_equipada is None
    assert inv.arma_equipada == inv.objetos[0].id
    assert inv.objetos[1].cura == 20


def probar_estado_juego_integra_todos_los_dto():
    sala = _sala()
    jugador = ActorDTO("jugador", "jugador", "Aventurero", 20, 20, 5, 2, 100, 4)
    rata = ActorDTO("e-201", "rata_gigante", "Rata gigante #1", 8, 8, 3, 1, 150, 4)
    veneno = EfectoDTO("veneno", 300, 2)
    antorcha = EfectoDTO("antorcha", 500)
    inventario = InventarioDTO([], cursor=0, capacidad=0, capacidad_maxima=10)
    estado = EstadoJuegoDTO(
        sala=sala, jugador=jugador, enemigos=[rata], objetos_suelo=[_daga()],
        efectos=[veneno, antorcha], inventario=inventario,
        mensajes=["Entras a la sala.", "Una rata te ataca."], reloj=100)
    assert estado.terminado is False and estado.resultado is None
    assert estado.enemigos[0].id == "e-201"
    assert estado.efectos[1].valor is None
    assert estado.mensajes[-1] == "Una rata te ataca."
    final = EstadoJuegoDTO(sala, jugador, [], [], [], inventario, [], 900,
                           terminado=True, resultado="victoria")
    assert final.terminado and final.resultado == "victoria"
    try:
        estado.reloj = 5
    except Exception:
        return
    raise AssertionError("El DTO debería ser inmutable")


def probar_estado_con_puerta_en_estado_actual():
    # La sala original trae la puerta E cerrada (estado inicial). Servicios puede
    # entregar una copia con la puerta abierta sin modificar el DTO original.
    sala = _sala()
    salidas = list(sala.salidas)
    salidas[E] = replace(sala.salidas[E], cerrada=False)
    sala_viva = replace(sala, salidas=salidas)
    assert sala.salidas[E].cerrada is True
    assert sala_viva.salidas[E].cerrada is False


if __name__ == "__main__":
    probar_accion_ida_y_vuelta()
    probar_accion_linea_invalida()
    probar_accion_inmutable()
    probar_accion_abrir_apunta_a_una_salida_de_la_sala()
    probar_accion_objetivo_coincide_con_actor()
    probar_puntaje_ida_y_vuelta()
    probar_puntaje_se_arma_desde_la_cripta()
    probar_inventario_con_objetos_reales()
    probar_estado_juego_integra_todos_los_dto()
    probar_estado_con_puerta_en_estado_actual()
    print("OK: todas las pruebas de los DTO del integrante 3 pasaron")

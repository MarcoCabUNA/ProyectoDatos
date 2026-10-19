import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from Data.AlmacenPuntajes import AlmacenPuntajes
from DTO.PuntajeDTO import PuntajeDTO
from Service.ServicioPuntajes import ServicioPuntajes
from test_servicios import _correr, _crear


def _servicio(carpeta):
    return ServicioPuntajes(AlmacenPuntajes(os.path.join(carpeta, "saves", "puntajes.jsonl")))


def _fila(nombre, acciones, enemigos, tiempo):
    return PuntajeDTO(nombre, "cripta-01", "v1", acciones, enemigos, tiempo)


def _cuatro_partidas(servicio):
    for fila in (_fila("Ana", 10, 2, 500), _fila("beto", 5, 3, 400),
                 _fila("Carla", 5, 2, 300), _fila("ana", 7, 3, 450)):      # en este orden se jugaron
        servicio.registrar(fila)


def _nombres(filas):
    return [f.nombre for f in filas]


def probar_la_tabla_empieza_vacia(carpeta):
    assert _servicio(carpeta).tabla() == []


def probar_registrar_y_leer(carpeta):
    servicio = _servicio(carpeta)
    servicio.registrar(_fila("Ana", 10, 2, 500))
    assert servicio.tabla() == [_fila("Ana", 10, 2, 500)]


def probar_cada_criterio_ordena_y_los_empates_conservan_el_orden_jugado(carpeta):
    servicio = _servicio(carpeta)
    _cuatro_partidas(servicio)
    assert _nombres(servicio.tabla("enemigos")) == ["beto", "ana", "Ana", "Carla"]    # más derrotados primero
    assert _nombres(servicio.tabla()) == ["beto", "ana", "Ana", "Carla"]              # es el criterio por omisión
    assert _nombres(servicio.tabla("tiempo")) == ["Carla", "beto", "ana", "Ana"]      # menor tiempo primero
    assert _nombres(servicio.tabla("acciones")) == ["beto", "Carla", "ana", "Ana"]    # menos acciones primero
    assert _nombres(servicio.tabla("nombre")) == ["Ana", "ana", "beto", "Carla"]      # sin distinguir mayúsculas


def probar_ordenar_no_altera_lo_guardado(carpeta):
    servicio = _servicio(carpeta)
    _cuatro_partidas(servicio)
    servicio.tabla("tiempo")
    servicio.tabla("nombre")
    jugadas = AlmacenPuntajes(os.path.join(carpeta, "saves", "puntajes.jsonl")).leer()
    assert _nombres(jugadas) == ["Ana", "beto", "Carla", "ana"]


def probar_criterio_invalido(carpeta):
    try:
        _servicio(carpeta).tabla("color")
    except ValueError:
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_registrar_el_puntaje_de_una_partida_real(carpeta):
    partida, acciones, ctx = _crear(carpeta)
    from DTO.AccionDTO import AccionDTO
    acciones.ejecutar(ctx, AccionDTO("esperar"))
    puntaje = partida.puntaje(ctx)
    servicio = _servicio(carpeta)
    servicio.registrar(puntaje)
    assert servicio.tabla() == [puntaje] and puntaje.acciones == 1


if __name__ == "__main__":
    for prueba in (probar_la_tabla_empieza_vacia, probar_registrar_y_leer,
                   probar_cada_criterio_ordena_y_los_empates_conservan_el_orden_jugado,
                   probar_ordenar_no_altera_lo_guardado, probar_criterio_invalido,
                   probar_registrar_el_puntaje_de_una_partida_real):
        _correr(prueba)
    print("OK: todas las pruebas de ServicioPuntajes pasaron")
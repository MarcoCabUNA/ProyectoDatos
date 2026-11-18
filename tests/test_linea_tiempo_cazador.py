"""
Pruebas del cazador con la línea de tiempo (feature 004, T070): FR-419 y FR-114.

La cripta-01 no trae cazadores; FuenteConCazador (tests/ayudas_linea_tiempo.py) pone uno en la sala 4. Cuando el
jugador entra, el cazador lo persigue por el pasillo 4-3-2-1 con la búsqueda compartida de RutasHaciaJugador
(`motor.rutas`, de Marco: aquí solo se usa, no se modifica). El escenario incluye dos pergaminos: el jugador retrocede
en plena persecución. La línea reconstruye en un Motor aparte, cuya búsqueda compartida arranca vacía porque
PartidaGuardada no la guarda; aun así el cazador debe decidir lo mismo que en la partida viva y que desde cero.
"""
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import FuenteConCazador, _correr
from test_linea_tiempo_pergamino import ESPERAR, N, S, _mover, _Partida
from DTO.AccionDTO import AccionDTO
from Logic.BusquedaCostoMinimo import paso_desde_cero
from Logic.PartidaGuardada import PartidaGuardada
from Service.ReconstructorEstado import ReconstructorEstado


def _cazadores(motor) -> list:
    """Los cazadores vivos del motor, de todas las salas."""
    encontrados = []
    for sala in motor.mazmorra.salas:
        if sala is not None:
            for enemigo in sala.enemigos:
                if enemigo.ficha.comportamiento == "cazador" and enemigo.vida > 0:
                    encontrados.append(enemigo)
    return encontrados


def _foto(motor, ctx) -> tuple:
    partida, salas = PartidaGuardada.guardar(motor, ctx.cripta, ctx.resolvedor.version_catalogo(), ctx.semilla)
    return partida.a_diccionario(), [sala.a_diccionario() for sala in salas]


def _referencia_desde_cero(motor) -> list:
    """(id del cazador, paso hacia el jugador calculado desde cero) de cada cazador vivo. No toca `motor.rutas`."""
    return [(c.id, paso_desde_cero(motor.grafo, motor.jugador.Sala_Actual, c.Sala_Actual, c.ficha.rango))
            for c in _cazadores(motor)]


class _PartidaCazada(_Partida):
    """La partida de siempre, que además fotografía el estado completo y la decisión de cada cazador antes de cada acción."""

    def __init__(self, carpeta: str) -> None:
        super().__init__(carpeta, pergaminos=2, k=4, fuente_clase=FuenteConCazador)
        self.fotos: dict = {}
        self.decisiones: dict = {}

    def hacer(self, *acciones: AccionDTO) -> None:
        for accion in acciones:
            k = self.ctx.jugador.acciones + 1
            self.fotos[k] = _foto(self.ctx.motor, self.ctx)
            self.decisiones[k] = _referencia_desde_cero(self.ctx.motor)
            super().hacer(accion)

    def escenario(self) -> None:
        """Entra a la sala 4, el cazador persigue al jugador de vuelta por el pasillo y el jugador retrocede dos veces."""
        self.hacer(_mover(N), _mover(N), _mover(N))              # sala 4: el cazador (y el guardián) se activan
        self.hacer(ESPERAR, _mover(S), _mover(S))                # sala 2, con el cazador detrás
        self.hacer(ESPERAR)
        self.retroceder()                                        # se revierte esa espera en plena persecución
        self.hacer(_mover(S), ESPERAR, ESPERAR)                  # sala 1
        self.retroceder()
        self.hacer(_mover(N), ESPERAR, ESPERAR)


class PruebasCazador(unittest.TestCase):

    def test_cazador_estado_reconstruido_igual_al_vivo_fr419_fr114(self):
        def prueba(carpeta):
            p = _PartidaCazada(carpeta)
            p.escenario()
            self.assertTrue(_cazadores(p.ctx.motor), "el cazador debería seguir vivo")
            salas_del_cazador = {c.Sala_Actual for c in _cazadores(p.ctx.motor)}
            self.assertNotEqual(salas_del_cazador, {4})                  # sí se movió: persiguió al jugador
            p.comprobar_todo(self)                                       # resúmenes: posición, vida y número de cada enemigo
            reconstructor = ReconstructorEstado(p.ctx)
            for k in range(1, p.ctx.jugador.acciones + 1):
                self.assertEqual(_foto(reconstructor.hasta_accion(k), p.ctx), p.fotos[k], f"decisión {k}")
        _correr(prueba)

    def test_cazador_busqueda_compartida_del_motor_aparte_arranca_vacia_fr114(self):
        def prueba(carpeta):
            p = _PartidaCazada(carpeta)
            p.escenario()
            reconstructor = ReconstructorEstado(p.ctx)
            con_cazador = recien_cargados = 0
            for k in range(1, p.ctx.jugador.acciones + 1):
                motor = reconstructor.hasta_accion(k)
                if reconstructor.acciones_reaplicadas == 0:              # el Motor tal como sale del punto de control
                    recien_cargados += 1
                    self.assertFalse(motor.rutas.valida)                 # la búsqueda compartida arranca vacía
                    self.assertEqual(motor.rutas.recalculos, 0)
                reconstruidas = []
                for cazador in _cazadores(motor):
                    paso = motor.rutas.decidir(cazador.Sala_Actual, motor.jugador.Sala_Actual, cazador.ficha.rango)
                    reconstruidas.append((cazador.id, paso))
                    con_cazador += 1
                self.assertEqual(reconstruidas, _referencia_desde_cero(motor), f"desde cero, decisión {k}")
                self.assertEqual(reconstruidas, p.decisiones[k], f"la partida viva, decisión {k}")
            self.assertGreaterEqual(recien_cargados, 3)                   # hubo casos de búsqueda vacía que probar
            self.assertGreater(con_cazador, 5)                            # hubo varias decisiones del cazador que comparar
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

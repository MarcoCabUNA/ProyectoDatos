"""
Pruebas de Logic/LineaTiempo.py (feature 004): la historia de la partida tal como quedó.

Solo Lógica pura: sin Data ni Service. Los puntos de control llevan los DTO de ejemplo del guardado.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_terreno import salidas_con_costos
from TestPartidaGuardadaDTO import partida_de_ejemplo, sala_de_ejemplo
from DTO.AccionDTO import AccionDTO
from Logic.LineaTiempo import LineaTiempo, PuntoControl


def _punto(acciones: int) -> PuntoControl:
    return PuntoControl(acciones, partida_de_ejemplo(), [sala_de_ejemplo()])


def _linea_con(cantidad: int, k: int = 3) -> LineaTiempo:
    """Una línea con `cantidad` acciones (la acción i en el tiempo 100 * i) y el punto 0."""
    linea = LineaTiempo(k)
    linea.agregar_punto(_punto(0))
    for i in range(1, cantidad + 1):
        linea.agregar_accion(100 * i, AccionDTO("esperar"))
    return linea


class PruebasLineaTiempoValidacion(unittest.TestCase):

    def test_linea_valida_instante_fr409(self):
        linea = LineaTiempo(3)
        for malo in (-1, 501, 2.5, "7", None, True):
            with self.assertRaises(ValueError) as error:
                linea.validar_instante(malo, 500)
            self.assertIn("500", str(error.exception))                 # el mensaje trae el rango válido
            self.assertIn("0", str(error.exception))
        linea.validar_instante(0, 500)
        linea.validar_instante(500, 500)                               # igual al reloj actual: se acepta

    def test_linea_valida_accion_fr409(self):
        linea = _linea_con(6)
        for malo in (0, 7, 9, -2, 1.5, "3", None, True):
            with self.assertRaises(ValueError) as error:
                linea.validar_accion(malo)
            self.assertIn("6", str(error.exception))                   # el mensaje trae el rango válido
        linea.validar_accion(1)
        linea.validar_accion(6)
        vacia = LineaTiempo(3)
        with self.assertRaises(ValueError):
            vacia.validar_accion(1)                                    # sin acciones, #1 se rechaza

    def test_linea_k_invalido_fr415(self):
        for malo in (0, -3, 2.5, "5", None):
            with self.assertRaises(ValueError):
                LineaTiempo(malo)
        self.assertEqual(LineaTiempo(1).k, 1)


class PruebasLineaTiempoAcciones(unittest.TestCase):

    def test_linea_agrega_acciones_en_orden_fr413(self):
        linea = LineaTiempo(3)
        acciones = [AccionDTO("mover", direccion=2), AccionDTO("esperar"), AccionDTO("atacar", objetivo="e-1")]
        for i, accion in enumerate(acciones):
            linea.agregar_accion(300 + 50 * i, accion)
        self.assertEqual(len(linea.acciones), 3)
        self.assertEqual([a.tiempo for a in linea.acciones], [300, 350, 400])
        self.assertEqual(linea.acciones[0].accion, acciones[0])        # la acción número k es la posición k (desde 1)
        self.assertEqual(linea.accion(3).accion, acciones[2])

    def test_linea_ubicar_accion_por_tiempo_fr404(self):
        linea = _linea_con(4)                                          # tiempos 100, 200, 300, 400
        self.assertEqual(linea.ubicar_accion_por_tiempo(99), 0)        # antes de la primera: ninguna
        self.assertEqual(linea.ubicar_accion_por_tiempo(100), 1)       # exacto: la propia decisión
        self.assertEqual(linea.ubicar_accion_por_tiempo(250), 2)
        self.assertEqual(linea.ubicar_accion_por_tiempo(9999), 4)
        self.assertEqual(LineaTiempo(3).ubicar_accion_por_tiempo(50), 0)


class PruebasLineaTiempoPuntos(unittest.TestCase):

    def test_linea_necesita_punto_cada_k_fr416(self):
        linea = LineaTiempo(3)
        self.assertTrue(linea.necesita_punto(0))                       # sin puntos: hace falta el punto 0
        linea.agregar_punto(_punto(0))
        for hechas in range(1, 10):
            linea.agregar_accion(100 * hechas, AccionDTO("esperar"))
            if linea.necesita_punto(hechas):
                linea.agregar_punto(_punto(hechas))
        posiciones = [p.acciones_completadas for p in linea.puntos]
        self.assertEqual(posiciones, [0, 3, 6, 9])
        for anterior, siguiente in zip(posiciones, posiciones[1:]):    # nunca más de K entre dos consecutivos
            self.assertLessEqual(siguiente - anterior, 3)

    def test_linea_no_pide_punto_antes_de_k_acciones_fr416(self):
        linea = LineaTiempo(5)
        linea.agregar_punto(_punto(0))
        self.assertFalse(linea.necesita_punto(4))
        self.assertTrue(linea.necesita_punto(5))
        linea.agregar_punto(_punto(5))
        self.assertFalse(linea.necesita_punto(5))                      # ya hay punto en esa posición

    def test_linea_ubicar_punto_fr416(self):
        linea = LineaTiempo(3)
        self.assertIsNone(linea.ubicar_punto(4))                       # sin puntos
        for hechas in (0, 3, 6, 9):
            linea.agregar_punto(_punto(hechas))
        self.assertEqual(linea.ubicar_punto(0).acciones_completadas, 0)
        self.assertEqual(linea.ubicar_punto(2).acciones_completadas, 0)
        self.assertEqual(linea.ubicar_punto(3).acciones_completadas, 3)
        self.assertEqual(linea.ubicar_punto(8).acciones_completadas, 6)
        self.assertEqual(linea.ubicar_punto(500).acciones_completadas, 9)


class PruebasLineaTiempoRegistros(unittest.TestCase):

    def test_linea_registra_carga_y_ficha_una_sola_vez_fr419(self):
        linea = LineaTiempo(3)
        salas = salidas_con_costos(3, [])
        linea.registrar_carga(0, salas[0])
        linea.registrar_carga(2, salas[1])
        linea.registrar_carga(5, salas[0])                             # la sala 1 ya estaba: se ignora
        self.assertEqual([(c.ordinal, c.sala.id) for c in linea.cargas], [(0, 1), (2, 2)])
        rata, trampa = SimpleNamespace(id="ene_rata"), SimpleNamespace(id="trp_pinchos")
        linea.registrar_ficha(rata)
        linea.registrar_ficha(trampa)
        linea.registrar_ficha(SimpleNamespace(id="ene_rata"))          # mismo id: se ignora
        self.assertEqual([f.id for f in linea.fichas], ["ene_rata", "trp_pinchos"])
        self.assertIs(linea.ficha("ene_rata"), rata)
        self.assertIsNone(linea.ficha("no_existe"))


if __name__ == "__main__":
    unittest.main()

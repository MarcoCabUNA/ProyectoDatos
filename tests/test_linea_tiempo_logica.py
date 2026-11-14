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

from ayudas_terreno import mazmorra_con_costos, motor_con, salida, salidas_con_costos
from TestPartidaGuardadaDTO import partida_de_ejemplo, sala_de_ejemplo
from DTO.AccionDTO import AccionDTO
from Logic.Inventario import Inventario
from Logic.LineaTiempo import LineaTiempo, PuntoControl
from Logic.PartidaGuardada import PartidaGuardada


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


# ---------- Recorte con el pergamino (T027, T028): FR-413, FR-416, FR-424 y NFR-403

def _estado_vivo(acciones: int) -> tuple:
    """El estado guardado de un motor de verdad (PartidaGuardada.guardar) con `acciones` acciones hechas."""
    motor, _ = motor_con(mazmorra_con_costos(2, [salida(1, 2, 2, 100)]), 1)
    motor.inventario = Inventario(5)                               # guardar necesita el inventario
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    motor.jugador.acciones = acciones
    return PartidaGuardada.guardar(motor, SimpleNamespace(id="c-prueba", version="1"), "v1", 1)


def _linea_con_puntos(cantidad: int, k: int) -> LineaTiempo:
    """Una línea con `cantidad` acciones y un punto de control cada k (en 0, k, 2k...), como la deja ServicioLineaTiempo."""
    linea = _linea_con(cantidad, k)
    for posicion in range(k, cantidad + 1, k):
        linea.agregar_punto(_punto(posicion))
    return linea


class PruebasRetrocederUna(unittest.TestCase):

    def test_retroceder_una_quita_la_ultima_accion_fr413(self):
        linea = _linea_con_puntos(7, 3)
        linea.retroceder_una(_estado_vivo(6))
        self.assertEqual(len(linea.acciones), 6)
        self.assertEqual(linea.acciones[-1].tiempo, 600)               # quedó la acción 6; la 7 se fue
        self.assertEqual([a.tiempo for a in linea.acciones], [100 * i for i in range(1, 7)])

    def test_retroceder_una_quita_los_puntos_con_mas_acciones_fr413(self):
        linea = _linea_con_puntos(10, 3)                               # puntos en 0, 3, 6, 9
        linea.retroceder_una(_estado_vivo(9))                          # c = 9: el punto de 9 se reemplaza
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0, 3, 6, 9])
        linea.retroceder_una(_estado_vivo(8))                          # c = 8: el de 9 sobra y se agrega el de 8
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0, 3, 6, 8])
        for c in (7, 6, 5):                                            # varios pergaminos seguidos
            linea.retroceder_una(_estado_vivo(c))
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0, 3, 5])
        self.assertEqual(len(linea.acciones), 5)

    def test_retroceder_una_agrega_el_punto_en_c_fr424(self):
        linea = _linea_con_puntos(8, 3)                                # puntos en 0, 3, 6; en c = 7 no hay
        estado = _estado_vivo(7)
        linea.retroceder_una(estado)
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0, 3, 6, 7])
        nuevo = linea.puntos[-1]
        self.assertIs(nuevo.partida, estado[0])                        # es el estado guardado que se le pasó
        self.assertIs(nuevo.salas, estado[1])
        self.assertEqual(nuevo.partida.jugador.acciones, 7)

    def test_retroceder_una_reemplaza_el_punto_en_c_fr424(self):
        linea = _linea_con_puntos(7, 3)                                # puntos en 0, 3, 6; la acción 7 se revierte: c = 6
        viejo = linea.puntos[-1]
        estado = _estado_vivo(6)
        linea.retroceder_una(estado)
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0, 3, 6])   # uno solo en c
        self.assertIsNot(linea.puntos[-1], viejo)
        self.assertIs(linea.puntos[-1].partida, estado[0])             # el nuevo, no el que había

    def test_retroceder_una_no_deja_mas_de_k_entre_puntos_fr416(self):
        for cantidad in range(1, 40):
            linea = _linea_con_puntos(cantidad, 4)
            linea.retroceder_una(_estado_vivo(cantidad - 1))
            posiciones = [p.acciones_completadas for p in linea.puntos]
            for anterior, siguiente in zip(posiciones, posiciones[1:]):
                self.assertTrue(0 < siguiente - anterior <= 4, (cantidad, posiciones))   # estrictamente creciente
            self.assertEqual(posiciones[-1], cantidad - 1)             # el último es el de c
            self.assertLessEqual(len(linea.acciones) - posiciones[-1], 4)

    def test_retroceder_una_no_recorre_la_historia_nfr403(self):
        class _Contada(list):
            """Una lista que cuenta los elementos que se tocan (sacar, agregar, iterar o indexar)."""
            tocados = 0

            def pop(self, *args):
                _Contada.tocados += 1
                return super().pop(*args)

            def append(self, valor):
                _Contada.tocados += 1
                super().append(valor)

            def __iter__(self):
                _Contada.tocados += 1000
                return super().__iter__()

            def __getitem__(self, indice):
                _Contada.tocados += 1
                return super().__getitem__(indice)

        costos = []
        for cantidad in (100, 5000):
            linea = _linea_con_puntos(cantidad, 20)
            linea.acciones, linea.puntos = _Contada(linea.acciones), _Contada(linea.puntos)
            estado = _estado_vivo(cantidad - 1)
            _Contada.tocados = 0
            linea.retroceder_una(estado)
            costos.append(_Contada.tocados)
        self.assertEqual(costos[0], costos[1])                         # no depende del largo de la historia
        self.assertLess(costos[0], 20)

    def test_retroceder_sin_acciones_falla_fr413(self):
        linea = _linea_con(0)
        with self.assertRaises(ValueError):
            linea.retroceder_una(_estado_vivo(0))
        self.assertEqual([p.acciones_completadas for p in linea.puntos], [0])    # no cambió nada


if __name__ == "__main__":
    unittest.main()

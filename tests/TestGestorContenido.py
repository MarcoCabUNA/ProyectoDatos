"""
Pruebas de Data/GestorContenido.py (precarga, enunciado §4.2):
cripta real del paquete y una cripta inventada de 7 x 7 = 49 salas que se recorre completa.
"""
import unittest
from typing import cast

from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from Data.FuenteOffline import FuenteOffline
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from tests.Utilidades import ID_CRIPTA, PAQUETE, FuenteCuadricula, cripta_cuadricula, id_cuadricula

N = 7


class EspiaFuente:
    """Envuelve una fuente y anota cada lote de contenido que se pide."""

    def __init__(self, fuente):
        self.fuente = fuente
        self.lotes = []

    def obtener_contenido(self, id_cripta, ids):
        self.lotes.append(list(ids))
        return self.fuente.obtener_contenido(id_cripta, ids)


def armar_cuadricula(radio=2, falla_en=None):
    fuente = FuenteCuadricula(N, falla_en)
    esqueleto = GestorEsqueleto(fuente)
    esqueleto.cargar(cripta_cuadricula(N))
    return fuente, esqueleto, GestorContenido(fuente, esqueleto, radio)


def recorrido_zigzag():
    camino = []
    for f in range(N):
        fila = [id_cuadricula(f, c, N) for c in range(N)]
        camino += fila if f % 2 == 0 else fila[::-1]
    return camino


def jugar(radio=2):
    """Simula al jugador: precarga al llegar, asegura antes de entrar. Cuenta esperas en puertas."""
    fuente, _, gc = armar_cuadricula(radio)
    camino = recorrido_zigzag()
    gc.precargar_alrededor(camino[0])
    esperas = 0
    for destino in camino[1:]:
        if not gc.contenido_disponible(destino):
            esperas += 1
        gc.asegurar_sala(destino)
        gc.precargar_alrededor(destino)
    return fuente, gc, esperas


class PruebasCriptaReal(unittest.TestCase):

    def setUp(self):
        fuente = FuenteOffline(PAQUETE)
        self.cripta = fuente.obtener_datos_generales(ID_CRIPTA)
        self.esqueleto = GestorEsqueleto(fuente)
        self.esqueleto.cargar(self.cripta)
        self.espia = EspiaFuente(fuente)
        self.gc = GestorContenido(cast(FuenteDatos, self.espia), self.esqueleto)

    def test_un_lote_con_las_6_salas_en_orden_de_cercania(self):
        self.assertEqual(self.gc.precargar_alrededor(self.cripta.sala_inicial), 6)
        self.assertEqual(self.espia.lotes, [[1, 2, 3, 5, 4, 6]])
        sala1 = self.gc.obtener_contenido(1)
        assert sala1 is not None
        self.assertEqual(sala1.objetos, ["itm_antorcha"])

    def test_recorrer_toda_la_cripta_no_pide_nada_mas(self):
        self.gc.precargar_alrededor(1)
        for sala in (1, 2, 5, 2, 3, 4, 6):
            self.assertEqual(self.gc.precargar_alrededor(sala), 0)
            self.assertEqual(self.gc.asegurar_sala(sala).id, sala)
        self.assertEqual(self.gc.lotes_realizados(), 1)

    def test_consultas_antes_de_cargar(self):
        self.assertFalse(self.gc.contenido_disponible(1))
        self.assertIsNone(self.gc.obtener_contenido(1))
        with self.assertRaises(ValueError):
            self.gc.precargar_alrededor(99)


class PruebasCuadricula(unittest.TestCase):

    def test_49_salas_en_5_lotes_sin_esperas_ni_repetidos(self):
        fuente, gc, esperas = jugar()
        self.assertEqual([len(l) for l in fuente.lotes], [10, 10, 10, 10, 9])   # el mínimo posible
        self.assertEqual(esperas, 0)
        pedidas = [x for lote in fuente.lotes for x in lote]
        self.assertEqual(len(pedidas), len(set(pedidas)))
        self.assertTrue(all(gc.contenido_disponible(i) for i in range(1, N * N + 1)))
        self.assertEqual((gc.lotes_realizados(), gc.salas_pedidas()), (5, 49))

    def test_primer_lote_por_cercania(self):
        fuente, _, gc = armar_cuadricula()
        gc.precargar_alrededor(1)
        self.assertEqual(fuente.lotes[0], [1, 8, 2, 15, 9, 3, 22, 16, 10, 4])

    def test_determinista(self):
        self.assertEqual(jugar()[0].lotes, jugar()[0].lotes)

    def test_radio_0_obliga_a_esperar_y_radio_1_ya_no(self):
        self.assertGreater(jugar(radio=0)[2], 0)
        for radio in (1, 2, 3):
            self.assertEqual(jugar(radio=radio)[2], 0)

    def test_no_pide_si_todo_lo_cercano_esta_cargado(self):
        _, _, gc = armar_cuadricula()
        gc.precargar_alrededor(1)
        self.assertEqual(gc.precargar_alrededor(2), 0)


class PruebasFallos(unittest.TestCase):

    def test_precarga_con_presupuesto_agotado_no_cae_y_se_reintenta(self):
        _, _, gc = armar_cuadricula(falla_en=0)
        self.assertEqual(gc.precargar_alrededor(1), 0)
        self.assertFalse(gc.contenido_disponible(1))      # volvió a "no pedida"
        self.assertEqual(gc.precargar_alrededor(1), 10)    # ya hay red: se pide

    def test_asegurar_sala_propaga_el_error_de_red(self):
        _, _, gc = armar_cuadricula(falla_en=0)
        with self.assertRaises(ErrorRed):
            gc.asegurar_sala(25)

    def test_asegurar_sala_la_pide_primero(self):
        fuente, _, gc = armar_cuadricula()
        self.assertEqual(gc.asegurar_sala(25).id, 25)
        self.assertEqual(fuente.lotes[0][0], 25)

    def test_requisitos_al_crear(self):
        fuente = FuenteCuadricula(N)
        with self.assertRaises(ValueError):
            GestorContenido(fuente, GestorEsqueleto(fuente))     # esqueleto sin cargar
        _, esqueleto, _ = armar_cuadricula()
        with self.assertRaises(ValueError):
            GestorContenido(fuente, esqueleto, radio=-1)


if __name__ == "__main__":
    unittest.main()
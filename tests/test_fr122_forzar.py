"""
FR-122 (feature 001, integrante 1) con --forzar: desde la T054 de la 003, ControladorBackend.iniciar pasa por
ServicioResolubilidad. Un error de datos del esqueleto (costo inválido, costos distintos entre las dos caras de una
salida o cierre_automatico inválido) sigue impidiendo iniciar también con --forzar: --forzar solo deja iniciar una
cripta no resoluble o que no se pudo verificar (003 FR-312), no una con datos inválidos.
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ayudas_resolubilidad import FuenteConLlaves, abierta, cara, cripta, puerta, ubic  # noqa: E402

from Data.AlmacenPuntajes import AlmacenPuntajes  # noqa: E402
from Data.ValidacionDatos import ErrorDatos  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.Direcciones import E, O  # noqa: E402
from Service.ServicioBench import ServicioBench  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from Service.ServicioPuntajes import ServicioPuntajes  # noqa: E402
from UIController.ControladorBackend import ControladorBackend, ErrorOperacion  # noqa: E402

ID = "prueba"


def cripta_costo_invalido():
    """La salida 2–3 declara costo 0 en las dos caras."""
    return cripta(3, [abierta(1, E, 2), abierta(2, E, 3, costo=0)], [], sala_salida=3)


def cripta_costos_distintos():
    """La salida 2–3 declara costo 150 en la cara de la sala 2 y 200 en la de la sala 3."""
    return cripta(3, [abierta(1, E, 2), cara(2, E, 3, costo=150), cara(3, O, 2, costo=200)], [], sala_salida=3)


def cripta_cierre_invalido():
    """La puerta 2–3 declara cierre_automatico 0."""
    return cripta(3, [abierta(1, E, 2), puerta(2, E, 3, "S", cierre_automatico=0)], [ubic("S", 2)], sala_salida=3)


CASOS = ((cripta_costo_invalido, "costo"), (cripta_costos_distintos, "costo 150"),
         (cripta_cierre_invalido, "cierre_automatico"))


class PruebasFR122ConForzar(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def backend(self, datos, forzar: bool) -> ControladorBackend:
        config = ConfiguracionDTO(forzar=forzar)
        partida = ServicioPartida(config, fuente=FuenteConLlaves(*datos),
                                  carpeta_cache=os.path.join(self.carpeta, "cache"),
                                  carpeta_logs=os.path.join(self.carpeta, "logs"), almacen_llaves=None)
        puntajes = ServicioPuntajes(AlmacenPuntajes(os.path.join(self.carpeta, "puntajes.jsonl")))
        return ControladorBackend(config, partida, puntajes, ServicioBench([]))

    def test_fr122_datos_invalidos_no_inician_ni_con_forzar(self):
        for armar, texto in CASOS:
            for forzar in (False, True):
                with self.subTest(cripta=armar.__name__, forzar=forzar):
                    backend = self.backend(armar(), forzar)
                    with self.assertRaises(ErrorOperacion) as atrapado:
                        backend.iniciar(ID, "Ana")
                    self.assertIsInstance(atrapado.exception.__cause__, ErrorDatos)
                    self.assertIn(texto, str(atrapado.exception))
                    self.assertFalse(backend.hay_partida())
                    self.assertFalse(os.path.isdir(os.path.join(self.carpeta, "logs")))   # no se creó ningún log


if __name__ == "__main__":
    unittest.main()

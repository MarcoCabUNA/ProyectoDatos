"""
Pruebas de que los resúmenes de `historia` llevan el mapa conocido (feature 002, T118; FR-223, 004 FR-405).

ServicioLineaTiempo pasa `motor.mapa.a_dto()` del motor reconstruido, así que el mapa es el de ese instante.
"""
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.Direcciones import E as ESTE  # noqa: E402
from DTO.MapaConocidoDTO import MapaConocidoDTO  # noqa: E402
from Service.ServicioLineaTiempo import ServicioLineaTiempo  # noqa: E402
from tests.ayudas_ir_a import servicio_partida_cuadricula  # noqa: E402


class PruebasHistoriaConMapa(unittest.TestCase):

    def test_fr223_los_resumenes_por_accion_y_por_instante_llevan_el_mapa_de_ese_momento(self):
        with tempfile.TemporaryDirectory() as carpeta:
            contexto = servicio_partida_cuadricula(carpeta).iniciar_partida("cuadricula", "Ana", semilla=5)
            servicio = ServicioLineaTiempo()
            for _ in range(3):                                                 # Sala 1 → Sala 4
                servicio.ejecutar(contexto, AccionDTO("mover", direccion=ESTE))
            por_accion = servicio.consultar_por_accion(contexto, 2)           # justo antes de la 2.ª: en la Sala 2
            por_instante = servicio.consultar_por_instante(contexto, 100)     # en t = 100 también está en la Sala 2
            for resumen in (por_accion, por_instante):
                self.assertIsInstance(resumen.mapa_conocido, MapaConocidoDTO)
                self.assertEqual([sala.id for sala in resumen.mapa_conocido.salas], [1, 2])
            actual = contexto.motor.mapa.a_dto()
            self.assertEqual([sala.id for sala in actual.salas], [1, 2, 3, 4])    # el vivo sabe más: no se mezcla


if __name__ == "__main__":
    unittest.main()

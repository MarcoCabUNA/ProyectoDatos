"""
Pruebas del campo `checkpoint_cada` de DTO/ConfiguracionDTO.py (feature 004, FR-415).

La bandera `--checkpoint-cada` llega en T050; aquí solo el DTO: el valor por defecto (provisional, se confirma
con --bench en T062) y que el campo es el último y tiene valor por defecto.
"""
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.ConfiguracionDTO import CHECKPOINT_POR_DEFECTO, ConfiguracionDTO


class PruebasConfiguracionCheckpoint(unittest.TestCase):

    def test_configuracion_checkpoint_por_defecto_fr415(self):
        self.assertEqual(ConfiguracionDTO().checkpoint_cada, CHECKPOINT_POR_DEFECTO)
        self.assertEqual(CHECKPOINT_POR_DEFECTO, 20)                       # provisional: se confirma en T062

    def test_configuracion_checkpoint_acepta_otro_valor_fr415(self):
        self.assertEqual(ConfiguracionDTO(checkpoint_cada=5).checkpoint_cada, 5)
        self.assertEqual(ConfiguracionDTO(offline=True, checkpoint_cada=1).checkpoint_cada, 1)

    def test_checkpoint_cada_va_al_final_y_no_cambia_los_otros_campos_fr415(self):
        nombres = [campo.name for campo in dataclasses.fields(ConfiguracionDTO)]
        self.assertEqual(nombres[:5], ["offline", "cache_size", "replay", "bench", "ayuda"])
        self.assertEqual(nombres[5], "checkpoint_cada")


if __name__ == "__main__":
    unittest.main()

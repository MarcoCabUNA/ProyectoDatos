"""
Pruebas de K configurable (feature 004, historia 5, T049): FR-415, FR-416 y FR-418.
"""
import dataclasses
import os
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, jugar, partida_de_prueba
from DTO.ConfiguracionDTO import CHECKPOINT_POR_DEFECTO, ConfiguracionDTO
from Service.ReconstructorEstado import ReconstructorEstado
from Service.ServicioLineaTiempo import ServicioLineaTiempo
from UIController.LectorArgumentos import ErrorArgumentos, leer_argumentos
import main


class PruebasCheckpointCada(unittest.TestCase):

    def test_h5_1_fr418_mismos_resumenes_con_k_1_5_y_50(self):
        """La misma partida (misma semilla y acciones) da los mismos resúmenes sea cual sea K."""
        def prueba(carpeta):
            resultados = {}
            for k in (1, 5, 50):
                _, ctx = partida_de_prueba(os.path.join(carpeta, f"k{k}"), semilla=2026, k=k)
                jugar(ctx, 120)
                self.assertEqual(ctx.linea.k, k)
                servicio = ServicioLineaTiempo()
                reloj, acciones = ctx.motor.reloj, ctx.jugador.acciones
                resultados[k] = (reloj, acciones,
                                 [servicio.consultar_por_instante(ctx, t) for t in range(0, reloj + 1, 7)],
                                 [servicio.consultar_por_accion(ctx, a) for a in range(1, acciones + 1, 5)])
            self.assertGreater(resultados[1][1], 50)                       # la partida fue larga
            self.assertEqual(resultados[1], resultados[5])
            self.assertEqual(resultados[1], resultados[50])
        _correr(prueba)

    def test_h5_2_fr416_ninguna_consulta_reaplica_mas_de_k_acciones(self):
        def prueba(carpeta):
            k = 10
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=k)
            jugar(ctx, 150)
            reconstructor = ReconstructorEstado(ctx)
            mayor = 0
            for a in range(1, ctx.jugador.acciones + 1):
                reconstructor.hasta_accion(a)
                self.assertLessEqual(reconstructor.acciones_reaplicadas, k, f"acción {a}")
                mayor = max(mayor, reconstructor.acciones_reaplicadas)
            for t in range(0, ctx.motor.reloj + 1, 3):
                reconstructor.hasta_instante(t)
                self.assertLessEqual(reconstructor.acciones_reaplicadas, k, f"instante {t}")
                mayor = max(mayor, reconstructor.acciones_reaplicadas)
            self.assertGreater(mayor, 0)                                    # sí hubo que re-simular
        _correr(prueba)

    def test_h5_3_fr415_valores_invalidos(self):
        for valor in ("0", "-2", "abc", "2.5"):
            with self.subTest(valor=valor):
                with self.assertRaises(ErrorArgumentos):
                    leer_argumentos(["--checkpoint-cada", valor])
                self.assertEqual(main.main(["--offline", "--checkpoint-cada", valor]), 2)

    def test_h5_4_fr415_valor_por_defecto(self):
        self.assertEqual(leer_argumentos([]).checkpoint_cada, CHECKPOINT_POR_DEFECTO)
        self.assertEqual(ConfiguracionDTO().checkpoint_cada, CHECKPOINT_POR_DEFECTO)
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)               # sin k: la configuración por defecto
            self.assertEqual(ctx.linea.k, CHECKPOINT_POR_DEFECTO)
        _correr(prueba)
        self.assertEqual(leer_argumentos(["--checkpoint-cada", "7"]).checkpoint_cada, 7)

    def test_fr415_checkpoint_por_defecto_provisional_es_20(self):
        self.assertEqual(CHECKPOINT_POR_DEFECTO, 20)                        # se actualiza en T062 si el bench lo cambia


if __name__ == "__main__":
    unittest.main()

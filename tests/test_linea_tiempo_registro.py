"""
Pruebas del registro de la línea de tiempo (feature 004, T017/T018/T019): FR-401, FR-413, FR-416 y FR-407.

La partida real (paquete offline) alimenta la línea por ServicioLineaTiempo.ejecutar: el punto 0 al empezar,
cada acción aceptada con su tiempo y un punto de control cada K acciones. Las acciones rechazadas no se registran.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, jugar, partida_de_prueba
from DTO.AccionDTO import AccionDTO
from DTO.ConfiguracionDTO import CHECKPOINT_POR_DEFECTO
from Service.ArmadorEstado import ArmadorEstado
from Service.ServicioLineaTiempo import ServicioLineaTiempo


class PruebasRegistroDeLaLinea(unittest.TestCase):

    def test_inicio_toma_el_punto_cero_fr401(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=3)
            linea = ctx.linea
            self.assertIsNotNone(linea)
            self.assertEqual(linea.k, CHECKPOINT_POR_DEFECTO)           # sin --checkpoint-cada: el valor por defecto
            self.assertEqual(len(linea.puntos), 1)
            punto = linea.puntos[0]
            self.assertEqual(punto.acciones_completadas, 0)
            self.assertEqual(punto.partida.reloj, ctx.motor.reloj)       # tomado cuando el jugador ya tiene el control
            self.assertEqual(punto.partida.jugador.acciones, 0)
            self.assertEqual(linea.acciones, [])
            self.assertEqual(len(linea.cargas), 1)                        # la sala inicial, con ordinal 0
            self.assertEqual((linea.cargas[0].ordinal, linea.cargas[0].sala.id), (0, ctx.cripta.sala_inicial))
            _, otra = partida_de_prueba(os.path.join(carpeta, "k"), semilla=3, k=7)
            self.assertEqual(otra.linea.k, 7)                             # el K sale de la configuración
        _correr(prueba)

    def test_accion_aceptada_se_agrega_con_su_tiempo_fr413(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=3)
            servicio = ServicioLineaTiempo()
            estado = ArmadorEstado().armar_estado(ctx)
            libres = [d for d in range(4) if estado.sala.salidas[d] is not None and not estado.sala.salidas[d].cerrada]
            self.assertTrue(libres)
            reloj_antes = ctx.motor.reloj
            accion = AccionDTO("mover", direccion=libres[0])
            servicio.ejecutar(ctx, accion)
            self.assertEqual(ctx.jugador.acciones, 1)
            self.assertEqual(len(ctx.linea.acciones), 1)
            self.assertEqual(ctx.linea.acciones[0].tiempo, reloj_antes)   # el reloj de la decisión, no el de después
            self.assertEqual(ctx.linea.acciones[0].accion, accion)
            servicio.ejecutar(ctx, AccionDTO("esperar"))
            self.assertEqual(len(ctx.linea.acciones), ctx.jugador.acciones)
            self.assertLess(ctx.linea.acciones[0].tiempo, ctx.linea.acciones[1].tiempo)
        _correr(prueba)

    def test_accion_rechazada_no_se_registra_fr407(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=3)
            servicio = ServicioLineaTiempo()
            estado = ArmadorEstado().armar_estado(ctx)
            ciegas = [d for d in range(4) if estado.sala.salidas[d] is None]
            self.assertTrue(ciegas, "la sala inicial debería tener una pared")
            estado = servicio.ejecutar(ctx, AccionDTO("mover", direccion=ciegas[0]))
            self.assertEqual(estado.resultado, "No hay salida en esa dirección.")
            self.assertEqual(ctx.jugador.acciones, 0)
            self.assertEqual(ctx.linea.acciones, [])
            self.assertEqual(len(ctx.linea.puntos), 1)
        _correr(prueba)

    def test_punto_de_control_cada_k_fr416(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=3, k=3)
            jugar(ctx, 20)
            n = ctx.jugador.acciones
            self.assertGreaterEqual(n, 10)
            self.assertEqual(len(ctx.linea.acciones), n)
            posiciones = [p.acciones_completadas for p in ctx.linea.puntos]
            self.assertEqual(posiciones, list(range(0, n + 1, 3)))        # 0, 3, 6, 9...
            for punto in ctx.linea.puntos:                                 # cada punto es el estado de ese momento
                self.assertEqual(punto.partida.jugador.acciones, punto.acciones_completadas)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

"""
Pruebas de Service/ArmadorResumen.py (feature 004, T022/T023): FR-405 y FR-406.

El armador lee un Motor (aquí el vivo, que no modifica) y devuelve el ResumenHistoriaDTO: sin cursor del
inventario ni mensajes, con el reloj que dice FR-405 y con el mapa conocido solo si existe.
"""
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, jugar, partida_de_prueba, resumen_vivo
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO
from Service.ArmadorResumen import ArmadorResumen


def _armar(ctx, instante, es_accion=False, terminada_antes=False, mapa=None):
    return ArmadorResumen.armar(ctx.motor, ctx.esqueleto, instante, es_accion, terminada_antes, mapa)


class PruebasArmadorResumen(unittest.TestCase):

    def test_h1_4_fr404_fr405_contenido_del_resumen(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 40)
            resumen = _armar(ctx, ctx.motor.reloj)
            self.assertIsInstance(resumen, ResumenHistoriaDTO)
            self.assertEqual(resumen, resumen_vivo(ctx))                   # lo mismo que muestra el estado vivo
            self.assertEqual(resumen.sala_id, ctx.jugador.Sala_Actual)
            self.assertEqual(resumen.sala_nombre, ctx.esqueleto.obtener_sala(ctx.jugador.Sala_Actual).nombre)
            self.assertEqual(resumen.jugador.id, "jugador")
            self.assertEqual(resumen.jugador.vida, ctx.jugador.vida)
            ids_enemigos = [e.id for e in ctx.mazmorra.enemigos_vivos(ctx.jugador.Sala_Actual)]
            self.assertEqual([e.id for e in resumen.enemigos], ids_enemigos)  # solo los de esa sala
            self.assertEqual(resumen.inventario, [o.id for o in ctx.inventario.objetos()])
        _correr(prueba)

    def test_h1_10_fr406_sin_cursor_ni_mensajes(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 15)
            resumen = _armar(ctx, ctx.motor.reloj)
            campos = [campo.name for campo in dataclasses.fields(resumen)]
            for prohibido in ("mensajes", "cursor", "inventario_cursor"):
                self.assertNotIn(prohibido, campos)
            self.assertTrue(all(isinstance(i, str) for i in resumen.inventario))   # ids: no hay cursor que mostrar
        _correr(prueba)

    def test_resumen_reloj_es_el_instante_pedido_fr405(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 20)
            resumen = _armar(ctx, ctx.motor.reloj - 7)
            self.assertEqual(resumen.reloj, ctx.motor.reloj - 7)
            self.assertEqual(resumen.instante_pedido, ctx.motor.reloj - 7)
            self.assertFalse(resumen.terminada_antes)
        _correr(prueba)

    def test_resumen_reloj_de_la_decision_k_fr405(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 12)
            resumen = _armar(ctx, 5, es_accion=True)         # `historia #5`: el motor está justo antes de la acción 5
            self.assertEqual(resumen.reloj, ctx.motor.reloj)  # el instante de esa decisión
            self.assertEqual(resumen.instante_pedido, 5)      # lo pedido es la acción k
        _correr(prueba)

    def test_resumen_reloj_del_final_si_la_partida_termino_antes_fr405(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=5)    # con esta semilla la partida se gana en pocas acciones
            estado = jugar(ctx, 700)
            self.assertTrue(estado.terminado)
            final = ctx.motor.reloj
            resumen = _armar(ctx, final + 500, terminada_antes=True)
            self.assertEqual(resumen.reloj, final)             # el reloj del final, no el pedido
            self.assertEqual(resumen.instante_pedido, final + 500)
            self.assertTrue(resumen.terminada_antes)
        _correr(prueba)

    def test_resumen_omite_mapa_conocido_si_no_existe_fr405(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 10)
            self.assertIsNone(_armar(ctx, ctx.motor.reloj).mapa_conocido)
            mapa = [1, 2, 3]                                   # el mapa conocido (spec 002), si el estado lo trae, se copia
            resumen = _armar(ctx, ctx.motor.reloj, mapa=mapa)
            self.assertEqual(resumen.mapa_conocido, [1, 2, 3])
            self.assertIsNot(resumen.mapa_conocido, mapa)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

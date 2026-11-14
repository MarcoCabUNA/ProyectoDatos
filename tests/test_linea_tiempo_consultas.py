"""
Pruebas de las consultas de la línea de tiempo por el servicio (feature 004, T024/T025): FR-401 a FR-409.

`historia <t>` es ServicioLineaTiempo.consultar_por_instante e `historia #k`, consultar_por_accion. Una consulta no
cambia la partida: ni el reloj, ni la cola de eventos, ni el historial de retroceso, ni partida.log.
"""
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, jugar, partida_de_prueba, resumen_vivo
from Logic.PartidaGuardada import PartidaGuardada
from Service.ServicioLineaTiempo import ServicioLineaTiempo


def _foto(ctx) -> tuple:
    partida, salas = PartidaGuardada.guardar(ctx.motor, ctx.cripta, ctx.resolvedor.version_catalogo(), ctx.semilla)
    return partida.a_diccionario(), [sala.a_diccionario() for sala in salas]


def _log(ctx) -> str:
    with open(ctx.bitacora.ruta(), encoding="utf-8") as archivo:
        return archivo.read()


def _sin_pedido(resumen):
    """El resumen sin el campo que dice qué se pidió (t o k), para comparar el contenido."""
    return dataclasses.replace(resumen, instante_pedido=None)


class PruebasConsultas(unittest.TestCase):

    def test_h1_1_apendiceB_caso3_fr409_instante_posterior(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 6)
            reloj, foto = ctx.motor.reloj, _foto(ctx)
            with self.assertRaises(ValueError) as error:
                ServicioLineaTiempo().consultar_por_instante(ctx, reloj + 300)
            self.assertIn(str(reloj), str(error.exception))            # dice el límite
            self.assertEqual(_foto(ctx), foto)                           # la partida sigue igual
        _correr(prueba)

    def test_h1_3_apendiceB_caso4_fr407_fr408_no_altera_la_partida(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 5)
            self.assertEqual(ctx.jugador.acciones, 5)
            servicio = ServicioLineaTiempo()
            antes = (ctx.motor.reloj, ctx.motor.historial.cantidad(), _foto(ctx), _log(ctx),
                     ctx.mensajes.a_array(), len(ctx.motor.cola.eventos))
            servicio.consultar_por_instante(ctx, ctx.linea.accion(3).tiempo + 1)
            servicio.consultar_por_accion(ctx, 3)
            despues = (ctx.motor.reloj, ctx.motor.historial.cantidad(), _foto(ctx), _log(ctx),
                       ctx.mensajes.a_array(), len(ctx.motor.cola.eventos))
            self.assertEqual(antes, despues)
            self.assertEqual(ctx.motor.historial.cantidad(), 5)         # las 5 acciones revertibles siguen ahí
        _correr(prueba)

    def test_h1_5_fr409_accion_fuera_de_rango(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 6)
            servicio = ServicioLineaTiempo()
            for k in (9, 0, -1):
                with self.assertRaises(ValueError) as error:
                    servicio.consultar_por_accion(ctx, k)
                self.assertIn("entre 1 y 6", str(error.exception))
        _correr(prueba)

    def test_h1_6_fr401_fr414_accion_ya_no_revertible(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 20)
            self.assertEqual(ctx.jugador.acciones, 20)
            self.assertLess(ctx.motor.historial.cantidad(), 20)          # el historial de retroceso ya no las guarda todas
            resumen = ServicioLineaTiempo().consultar_por_accion(ctx, 2)
            self.assertEqual(resumen.instante_pedido, 2)
            self.assertEqual(resumen.reloj, ctx.linea.accion(2).tiempo)
        _correr(prueba)

    def test_h1_7_fr409_instante_igual_al_reloj(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 9)
            resumen = ServicioLineaTiempo().consultar_por_instante(ctx, ctx.motor.reloj)
            self.assertEqual(resumen, resumen_vivo(ctx))
        _correr(prueba)

    def test_h1_8_fr419_consulta_repetida(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 30)
            servicio = ServicioLineaTiempo()
            t = ctx.linea.accion(12).tiempo + 40
            self.assertEqual(servicio.consultar_por_instante(ctx, t), servicio.consultar_por_instante(ctx, t))
            self.assertEqual(servicio.consultar_por_accion(ctx, 12), servicio.consultar_por_accion(ctx, 12))
        _correr(prueba)

    def test_h1_9_fr402_historia_t_igual_a_historia_k(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            jugar(ctx, 25)
            servicio = ServicioLineaTiempo()
            for k in (1, 2, 7, 13, 25):
                por_accion = servicio.consultar_por_accion(ctx, k)
                por_instante = servicio.consultar_por_instante(ctx, ctx.linea.accion(k).tiempo)
                self.assertEqual(_sin_pedido(por_instante), _sin_pedido(por_accion), f"decisión {k}")
        _correr(prueba)

    def test_casos_borde_sin_acciones_fr409(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026)
            servicio = ServicioLineaTiempo()
            self.assertEqual(servicio.consultar_por_instante(ctx, 0), resumen_vivo(ctx))
            with self.assertRaises(ValueError):
                servicio.consultar_por_accion(ctx, 1)
        _correr(prueba)

    def test_partida_terminada_sigue_consultable_fr401(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=5)
            estado = jugar(ctx, 700)
            self.assertTrue(estado.terminado)
            servicio = ServicioLineaTiempo()
            final = servicio.consultar_por_instante(ctx, ctx.motor.reloj)
            self.assertEqual(final, resumen_vivo(ctx))
            self.assertEqual(final.reloj, ctx.motor.reloj)
            ultima = servicio.consultar_por_accion(ctx, ctx.jugador.acciones)
            self.assertEqual(ultima.reloj, ctx.linea.accion(ctx.jugador.acciones).tiempo)
        _correr(prueba)

    def test_sc402_resumenes_iguales_al_vivo_en_cada_decision(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=6)
            vivos = {}
            jugar(ctx, 80, al_decidir=lambda _e: vivos.__setitem__(ctx.jugador.acciones + 1, resumen_vivo(ctx)))
            servicio = ServicioLineaTiempo()
            for k in range(1, ctx.jugador.acciones + 1):
                esperado = vivos[k]
                self.assertEqual(servicio.consultar_por_accion(ctx, k), dataclasses.replace(esperado, instante_pedido=k))
                self.assertEqual(servicio.consultar_por_instante(ctx, esperado.reloj), esperado)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

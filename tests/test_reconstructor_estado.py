"""
Pruebas de Service/ReconstructorEstado.py (feature 004, T020/T021): FR-401, FR-402, FR-407 y FR-419.

Se juega una partida real de 200 acciones o más (semilla 2026 con el jugador reforzado: ver FuenteReforzada en
tests/ayudas_linea_tiempo.py). Antes de cada acción se fotografía el estado vivo completo con
PartidaGuardada.guardar; después, el reconstructor debe devolver, para cada decisión, un Motor aparte cuya foto
sea idéntica (incluido el estado del azar). Así la prueba no depende del armador del resumen.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, jugar, partida_de_prueba
from Logic.PartidaGuardada import PartidaGuardada
from Service.ReconstructorEstado import ReconstructorEstado


def _foto(motor, ctx) -> tuple:
    """Todo el estado de un motor como diccionarios comparables (incluye el azar y la cola de eventos)."""
    partida, salas = PartidaGuardada.guardar(motor, ctx.cripta, ctx.resolvedor.version_catalogo(), ctx.semilla)
    return partida.a_diccionario(), [sala.a_diccionario() for sala in salas]


def _solicitudes(fuente) -> int:
    cuenta = fuente.solicitudes_realizadas
    return cuenta() if callable(cuenta) else cuenta


def _numeros_de_data(ctx) -> tuple:
    """Todo lo que cuenta lo que se le pidió a Data."""
    r, g = ctx.resolvedor, ctx.contenido
    return (_solicitudes(ctx.fuente), r.aciertos(), r.fallos(), r.lecturas_disco(),
            r.solicitudes_catalogo(), r.fichas_descargadas(), g.lotes_realizados(), g.salas_pedidas())


def _jugar_y_fotografiar(ctx, intentos: int):
    """Juega y devuelve {numero de decision k: (reloj, foto del estado vivo justo antes de la acción k)}."""
    fotos = {}

    def antes(_estado):
        fotos[ctx.jugador.acciones + 1] = (ctx.motor.reloj, _foto(ctx.motor, ctx))
    jugar(ctx, intentos, al_decidir=antes)
    return fotos


class PruebasReconstructor(unittest.TestCase):

    def test_reconstruir_igual_al_vivo_fr419(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=20)
            fotos = _jugar_y_fotografiar(ctx, 230)
            self.assertGreaterEqual(ctx.jugador.acciones, 200)
            self.assertFalse(ctx.motor.terminado)
            reconstructor = ReconstructorEstado(ctx)
            for k in range(1, ctx.jugador.acciones + 1):
                reloj, foto = fotos[k]
                self.assertEqual(_foto(reconstructor.hasta_accion(k), ctx), foto, f"decisión {k}")
                self.assertEqual(_foto(reconstructor.hasta_instante(reloj), ctx), foto, f"instante {reloj} (decisión {k})")
        _correr(prueba)

    def test_reconstruir_conserva_el_azar_del_punto_fr419(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=10)
            fotos = _jugar_y_fotografiar(ctx, 60)
            reconstructor = ReconstructorEstado(ctx)
            for k in (1, 9, 11, 25, 40):
                reconstruido = reconstructor.hasta_accion(k)
                vivo = fotos[k][1][0]
                self.assertEqual(list(reconstruido.azar.getstate()[1]), vivo["azar_estado"])
                # el siguiente número aleatorio es el mismo: un ataque dará el mismo daño
                from random import Random
                esperado = Random()
                esperado.setstate((vivo["azar_version"], tuple(vivo["azar_estado"]), vivo["azar_gauss"]))
                self.assertEqual(reconstruido.azar.random(), esperado.random())
        _correr(prueba)

    def test_reconstruir_no_toca_log_historial_ni_reloj_fr407(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=5)
            jugar(ctx, 40)
            ruta = ctx.bitacora.ruta()
            with open(ruta, encoding="utf-8") as archivo:
                log = archivo.read()
            antes = (ctx.motor.reloj, ctx.jugador.acciones, ctx.motor.historial.cantidad(), _foto(ctx.motor, ctx),
                     ctx.bitacora.acciones_escritas(), len(ctx.linea.acciones), len(ctx.linea.puntos),
                     len(ctx.linea.cargas), len(ctx.linea.fichas))
            reconstructor = ReconstructorEstado(ctx)
            motor = reconstructor.hasta_accion(17)
            reconstructor.hasta_instante(ctx.motor.reloj // 2)
            self.assertIsNot(motor, ctx.motor)
            self.assertIsNot(motor.mazmorra, ctx.mazmorra)
            despues = (ctx.motor.reloj, ctx.jugador.acciones, ctx.motor.historial.cantidad(), _foto(ctx.motor, ctx),
                       ctx.bitacora.acciones_escritas(), len(ctx.linea.acciones), len(ctx.linea.puntos),
                       len(ctx.linea.cargas), len(ctx.linea.fichas))
            self.assertEqual(antes, despues)
            with open(ruta, encoding="utf-8") as archivo:
                self.assertEqual(archivo.read(), log)
        _correr(prueba)

    def test_reconstruir_no_pide_nada_a_data_fr407(self):
        def prueba(carpeta):
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=5)
            jugar(ctx, 80)
            antes = _numeros_de_data(ctx)
            reconstructor = ReconstructorEstado(ctx)
            for k in (1, 8, 30, ctx.jugador.acciones):
                reconstructor.hasta_accion(k)
            reconstructor.hasta_instante(ctx.motor.reloj)
            self.assertEqual(_numeros_de_data(ctx), antes)
        _correr(prueba)

    def test_reconstruir_cuenta_las_acciones_reaplicadas_fr416(self):
        def prueba(carpeta):
            k_linea = 7
            _, ctx = partida_de_prueba(carpeta, semilla=2026, k=k_linea)
            fotos = _jugar_y_fotografiar(ctx, 60)
            reconstructor = ReconstructorEstado(ctx)
            maximo = 0
            for k in range(1, ctx.jugador.acciones + 1):
                reconstructor.hasta_accion(k)
                self.assertLessEqual(reconstructor.acciones_reaplicadas, k_linea)
                maximo = max(maximo, reconstructor.acciones_reaplicadas)
                reconstructor.hasta_instante(fotos[k][0])
                self.assertLessEqual(reconstructor.acciones_reaplicadas, k_linea)
            self.assertGreater(maximo, 0)                          # sí se re-simuló algo
            reconstructor.hasta_accion(8)                           # justo en un punto: no hay nada que reaplicar
            self.assertEqual(reconstructor.acciones_reaplicadas, 0)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

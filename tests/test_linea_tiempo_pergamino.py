"""
Pruebas de la línea de tiempo con el pergamino de retroceso (feature 004, historia 3: T029, T033; T030, T032, T034).

Un pergamino revierte la última acción del jugador. La línea no guarda marcadores: quita esa acción y toma un
punto de control NUEVO en c (las acciones que quedan) copiando el estado vivo, que reemplaza al que hubiera en c.
Todas las pruebas comparan lo que reconstruye la línea con lo que mostraba la partida viva en ese momento.

La partida es la cripta-01 con el jugador reforzado (tests/ayudas_linea_tiempo.py). Sus salas forman un pasillo
1-2-3-4 (norte = 0 sube, sur = 1 baja): la sala 2 tiene dos ratas y la 4 un guardián.
"""
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import (ID_PERGAMINO, FuenteConRatas, _correr, dar_pergaminos, partida_de_prueba,
                                 resumen_vivo)
from DTO.AccionDTO import AccionDTO
from Service.ReconstructorEstado import ReconstructorEstado
from Service.ServicioLineaTiempo import ServicioLineaTiempo

N, S, E = 0, 1, 2
ANTORCHA = "itm_antorcha"          # lo que ya hay en el suelo de la sala inicial
ESPERAR = AccionDTO("esperar")


def _mover(direccion: int) -> AccionDTO:
    return AccionDTO("mover", direccion=direccion)


class _Partida:
    """Una partida con la línea, que fotografía el estado vivo antes de cada acción (clave = número de la acción)."""

    def __init__(self, carpeta: str, pergaminos: int = 2, suelo: int = 0, k: int | None = None,
                 fuente_clase=None, llave: str | None = None) -> None:
        _, self.ctx = partida_de_prueba(carpeta, semilla=2026, k=k, fuente_clase=fuente_clase)
        if llave is not None:                                         # una llave en el inventario, por fuera de los servicios
            self.ctx.inventario.recoger(self.ctx.resolvedor.ficha(llave))
        for _ in range(suelo):                                       # pergaminos en el suelo de la sala inicial
            self.ctx.mazmorra.sala(self.ctx.jugador.Sala_Actual).objetos.append(ID_PERGAMINO)
        dar_pergaminos(self.ctx, pergaminos)                          # (también vuelve a tomar el punto 0)
        self.servicio = ServicioLineaTiempo()
        self.vivos: dict = {}                                         # k -> resumen del estado vivo justo antes de la acción k

    def hacer(self, *acciones: AccionDTO) -> None:
        for accion in acciones:
            self.vivos[self.ctx.jugador.acciones + 1] = resumen_vivo(self.ctx)
            antes = self.ctx.jugador.acciones
            self.servicio.ejecutar(self.ctx, accion)
            assert self.ctx.jugador.acciones == antes + 1, f"la acción {accion} no se hizo"

    def retroceder(self) -> None:
        """Lee un pergamino: la última acción se revierte."""
        antes = self.ctx.jugador.acciones
        self.servicio.ejecutar(self.ctx, AccionDTO("retroceder"))
        assert self.ctx.jugador.acciones == antes - 1, "el pergamino no revirtió nada"

    def consultar_k(self, k: int):
        return self.servicio.consultar_por_accion(self.ctx, k)

    def consultar_t(self, t: int):
        return self.servicio.consultar_por_instante(self.ctx, t)

    def pergaminos_en_el_inventario(self) -> int:
        return [o.id for o in self.ctx.inventario.objetos()].count(ID_PERGAMINO)

    def suelo_de(self, motor) -> list:
        return list(motor.mazmorra.sala(self.ctx.jugador.Sala_Actual).objetos)

    def suelo_reconstruido(self, t: int) -> list:
        return list(ReconstructorEstado(self.ctx).hasta_instante(t).mazmorra.sala(self.ctx.jugador.Sala_Actual).objetos)

    def comprobar_todo(self, prueba: unittest.TestCase) -> None:
        """Cada decisión vigente y el instante actual coinciden con lo que vivió la partida."""
        for k in range(1, self.ctx.jugador.acciones + 1):
            esperado = self.vivos[k]
            prueba.assertEqual(self.consultar_k(k), dataclasses.replace(esperado, instante_pedido=k), f"decisión {k}")
            prueba.assertEqual(self.consultar_t(esperado.reloj), esperado, f"instante {esperado.reloj} (decisión {k})")
        prueba.assertEqual(self.consultar_t(self.ctx.motor.reloj), resumen_vivo(self.ctx), "el instante actual")


class PruebasPergamino(unittest.TestCase):

    def test_h3_1_apendiceB_caso2_fr413_fr409(self):
        def prueba(carpeta):
            p = _Partida(carpeta)
            p.hacer(_mover(N), _mover(N), _mover(S), _mover(N))
            sala_antes_de_la_5 = p.ctx.jugador.Sala_Actual            # la sala 3
            p.hacer(_mover(S))                                        # la acción 5 lleva a la sala 2
            self.assertEqual(p.ctx.jugador.Sala_Actual, 2)
            p.retroceder()                                            # el pergamino revierte la 5
            with self.assertRaises(ValueError) as error:
                p.consultar_k(5)
            self.assertIn("entre 1 y 4", str(error.exception))        # rechazada por rango
            actual = p.consultar_t(p.ctx.motor.reloj)
            self.assertEqual(actual.sala_id, sala_antes_de_la_5)      # el instante actual muestra la sala de antes...
            self.assertNotEqual(actual.sala_id, 2)                    # ...no la que dejó la acción revertida
            p.comprobar_todo(self)
        _correr(prueba)

    def test_h3_2_fr413_accion_nueva_es_la_cinco(self):
        def prueba(carpeta):
            p = _Partida(carpeta)
            p.hacer(_mover(N), _mover(N), _mover(S), _mover(N), _mover(S))
            p.retroceder()
            justo_antes = resumen_vivo(p.ctx)                         # el estado en que se toma la nueva acción 5
            p.hacer(ESPERAR)
            self.assertEqual(p.ctx.jugador.acciones, 5)
            self.assertEqual(p.consultar_k(5), dataclasses.replace(justo_antes, instante_pedido=5))
            self.assertEqual(p.consultar_k(5).sala_id, 3)
            p.comprobar_todo(self)
        _correr(prueba)

    def test_h3_3_fr409_fr413_limite_es_el_reloj_actual(self):
        def prueba(carpeta):
            p = _Partida(carpeta)
            p.hacer(_mover(N), _mover(N), ESPERAR, ESPERAR)
            reloj_antes = p.ctx.motor.reloj
            p.retroceder()
            reloj_ahora = p.ctx.motor.reloj
            self.assertLess(reloj_ahora, reloj_antes)
            with self.assertRaises(ValueError) as error:
                p.consultar_t(reloj_antes)                            # el reloj de antes del pergamino ya es futuro
            self.assertIn(str(reloj_ahora), str(error.exception))
            self.assertEqual(p.consultar_t(reloj_ahora), resumen_vivo(p.ctx))
        _correr(prueba)

    def test_h3_4_fr413_varios_pergaminos_seguidos(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=3)
            p.hacer(_mover(N), _mover(N), _mover(N), _mover(S), ESPERAR, _mover(S))
            p.retroceder()
            p.retroceder()                                            # revierte la 6 y la 5
            self.assertEqual(p.ctx.jugador.acciones, 4)
            # es el estado de justo antes de la 5, menos los dos pergaminos leídos (eso no se revierte)
            actual = p.consultar_t(p.ctx.motor.reloj)
            self.assertEqual(actual, dataclasses.replace(p.vivos[5], inventario=actual.inventario))
            self.assertEqual(actual.inventario.count(ID_PERGAMINO), 1)
            for k in (5, 6):
                with self.assertRaises(ValueError):
                    p.consultar_k(k)
            p.comprobar_todo(self)
            p.retroceder()                                            # un tercero: queda en la acción 3
            actual = p.consultar_t(p.ctx.motor.reloj)
            self.assertEqual(actual, dataclasses.replace(p.vivos[4], inventario=actual.inventario))
            self.assertEqual(actual.inventario.count(ID_PERGAMINO), 0)
            p.comprobar_todo(self)
        _correr(prueba)

    def test_h3_el_pergamino_usado_no_esta_en_el_estado_actual_fr419(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2)
            p.hacer(_mover(N), ESPERAR, ESPERAR)
            p.retroceder()
            self.assertEqual(p.pergaminos_en_el_inventario(), 1)
            actual = p.consultar_t(p.ctx.motor.reloj)
            self.assertEqual(actual, resumen_vivo(p.ctx))
            self.assertEqual(actual.inventario.count(ID_PERGAMINO), 1)    # el que se leyó ya no está
        _correr(prueba)

    def test_h3_los_estados_pasados_conservan_el_pergamino_fr419(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2)
            p.hacer(_mover(N), ESPERAR, ESPERAR)
            p.retroceder()
            for k in (1, 2):                                          # antes de leerlo, el pergamino sí estaba
                self.assertEqual(p.consultar_k(k).inventario.count(ID_PERGAMINO), 2)
            self.assertEqual(p.consultar_t(p.vivos[2].reloj).inventario.count(ID_PERGAMINO), 2)
            self.assertEqual(p.consultar_t(p.ctx.motor.reloj).inventario.count(ID_PERGAMINO), 1)
        _correr(prueba)

    def test_h3_la_linea_nunca_contiene_retroceder_fr413(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=3)
            p.hacer(_mover(N), ESPERAR, ESPERAR)
            p.retroceder()
            p.hacer(ESPERAR)
            p.servicio.ejecutar(p.ctx, AccionDTO("usar", objeto=ID_PERGAMINO))   # leerlo con «usar» es lo mismo
            self.assertEqual(p.ctx.jugador.acciones, 2)
            self.assertEqual(len(p.ctx.linea.acciones), 2)
            for registrada in p.ctx.linea.acciones:
                self.assertNotEqual(registrada.accion.tipo, "retroceder")
                self.assertFalse(registrada.accion.tipo == "usar" and registrada.accion.objeto == ID_PERGAMINO)
        _correr(prueba)

    def test_pergamino_deja_un_solo_punto_en_c_y_ninguno_despues_fr424(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2, k=3)
            p.hacer(ESPERAR, ESPERAR, ESPERAR, ESPERAR, ESPERAR)              # puntos en 0 y 3
            self.assertEqual([x.acciones_completadas for x in p.ctx.linea.puntos], [0, 3])
            p.retroceder()                                                    # c = 4: punto nuevo en 4
            self.assertEqual([x.acciones_completadas for x in p.ctx.linea.puntos], [0, 3, 4])
            p.retroceder()                                                    # c = 3: reemplaza al que había en 3
            self.assertEqual([x.acciones_completadas for x in p.ctx.linea.puntos], [0, 3])
            nuevo = p.ctx.linea.puntos[-1]
            self.assertEqual(nuevo.partida.reloj, p.ctx.motor.reloj)          # es una copia del estado vivo
            self.assertEqual(nuevo.partida.jugador.acciones, 3)
            self.assertEqual(len(p.ctx.linea.acciones), 3)
        _correr(prueba)

    def test_hallazgo_h1_numeracion_de_enemigos_tras_el_pergamino_fr419(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2, k=4)
            p.hacer(_mover(N))                                        # sala 2, nueva: sus dos ratas se numeran
            p.retroceder()                                            # se revierte; la sala sigue cargada en lo vivo
            p.hacer(_mover(N), _mover(N), _mover(N))                  # sala 2 otra vez, la 3 y la 4 (nueva: el guardián)
            p.hacer(ESPERAR, ESPERAR)
            p.retroceder()
            p.hacer(ESPERAR, _mover(S), _mover(S))
            nombres = [e.nombre for k in p.vivos for e in p.vivos[k].enemigos]
            self.assertTrue(any("Rata gigante #" in nombre for nombre in nombres))   # hay números que comparar
            p.comprobar_todo(self)
        _correr(prueba)

    def test_hallazgo_h1_dos_salas_nuevas_con_el_mismo_enemigo_fr419(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2, k=50, fuente_clase=FuenteConRatas, llave="itm_llave_bronce")
            p.hacer(_mover(N))                                        # sala 2: sus ratas son la #1 y la #2
            p.hacer(AccionDTO("abrir", direccion=E))                  # la puerta de la sala 5
            p.hacer(_mover(E))                                        # sala 5, nueva: su rata es la #3
            self.assertEqual(p.ctx.jugador.Sala_Actual, 5)
            p.retroceder()                                            # se revierte; la sala 5 ya estaba cargada
            p.hacer(_mover(N))                                        # sala 3, nueva: su rata es la #4 (no la #3)
            self.assertEqual(p.ctx.jugador.Sala_Actual, 3)
            numeros = [e.nombre for e in resumen_vivo(p.ctx).enemigos]
            self.assertIn("Rata gigante #4", numeros)                 # el orden REAL de carga: 2, 5, 3
            self.assertNotIn("Rata gigante #3", numeros)              # (la #3 es la de la sala 5)
            p.hacer(ESPERAR)
            p.comprobar_todo(self)
            for k in range(1, p.ctx.jugador.acciones + 1):            # y desde cada punto de partida posible
                motor = ReconstructorEstado(p.ctx).hasta_accion(k)
                if motor.jugador.Sala_Actual == 3:
                    self.assertIn("Rata gigante #4", [e.nombre_visible() for e in motor.mazmorra.enemigos_vivos(3)])
        _correr(prueba)


class PruebasPergaminoEnElSuelo(unittest.TestCase):
    """H3-5 y H3-6 (T033): los pergaminos recogidos o soltados quedan fuera de la reversión."""

    def test_h3_5_fr413_fr419_fr424_pergamino_recogido_en_la_accion_revertida(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=2, suelo=1)                     # 2 en el inventario y 1 en el suelo
            sala = p.ctx.jugador.Sala_Actual
            p.hacer(ESPERAR, ESPERAR, ESPERAR)
            p.hacer(AccionDTO("recoger", objeto=ID_PERGAMINO))               # la acción 4 recoge el del suelo
            self.assertEqual(p.pergaminos_en_el_inventario(), 3)
            p.retroceder()                                                   # lee otro para revertir la 4
            self.assertEqual(p.ctx.jugador.acciones, 3)
            self.assertEqual(p.pergaminos_en_el_inventario(), 2)             # conserva el recogido, sin el consumido
            self.assertEqual(p.suelo_de(p.ctx.motor), [ANTORCHA])            # y el suelo ya no lo tiene
            actual = p.consultar_t(p.ctx.motor.reloj)
            self.assertEqual(actual, resumen_vivo(p.ctx))
            self.assertEqual(actual.inventario.count(ID_PERGAMINO), 2)
            self.assertEqual(p.suelo_reconstruido(p.ctx.motor.reloj), [ANTORCHA])
            self.assertEqual(p.consultar_k(3).inventario.count(ID_PERGAMINO), 2)   # antes de la 4 solo había 2
            p.hacer(ESPERAR)                                                 # se sigue jugando sobre ese estado
            self.assertEqual(p.consultar_t(p.ctx.motor.reloj), resumen_vivo(p.ctx))
            self.assertEqual(p.suelo_reconstruido(p.ctx.motor.reloj), p.suelo_de(p.ctx.motor))
            p.comprobar_todo(self)
        _correr(prueba)

    def test_h3_6_fr413_fr419_fr424_pergamino_soltado_en_la_accion_revertida(self):
        def prueba(carpeta):
            p = _Partida(carpeta, pergaminos=3)
            p.hacer(ESPERAR, ESPERAR, ESPERAR)
            p.hacer(AccionDTO("soltar", objeto=ID_PERGAMINO))                # la acción 4 suelta un pergamino
            self.assertEqual((p.pergaminos_en_el_inventario(), p.suelo_de(p.ctx.motor)), (2, [ANTORCHA, ID_PERGAMINO]))
            p.retroceder()                                                   # otro pergamino revierte esa acción
            self.assertEqual(p.ctx.jugador.acciones, 3)
            self.assertEqual((p.pergaminos_en_el_inventario(), p.suelo_de(p.ctx.motor)), (1, [ANTORCHA, ID_PERGAMINO]))
            self.assertEqual(p.suelo_reconstruido(p.ctx.motor.reloj), [ANTORCHA, ID_PERGAMINO])   # el soltado sigue en el suelo
            self.assertEqual(p.consultar_t(p.ctx.motor.reloj), resumen_vivo(p.ctx))
            p.hacer(AccionDTO("recoger", objeto=ID_PERGAMINO))               # se recoge el que sigue en el suelo
            self.assertEqual((p.pergaminos_en_el_inventario(), p.suelo_de(p.ctx.motor)), (2, [ANTORCHA]))
            self.assertEqual(p.consultar_t(p.ctx.motor.reloj), resumen_vivo(p.ctx))   # el instante actual
            self.assertEqual(p.suelo_reconstruido(p.ctx.motor.reloj), [ANTORCHA])
            p.hacer(ESPERAR, ESPERAR)                                        # y los instantes posteriores
            for k in range(4, p.ctx.jugador.acciones + 2):
                if k <= p.ctx.jugador.acciones:
                    self.assertEqual(p.consultar_k(k).inventario.count(ID_PERGAMINO),
                                     p.vivos[k].inventario.count(ID_PERGAMINO))
            self.assertEqual(p.suelo_reconstruido(p.ctx.motor.reloj), p.suelo_de(p.ctx.motor))
            p.comprobar_todo(self)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

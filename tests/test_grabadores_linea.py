"""
Pruebas de Service/GrabadoresLinea.py (feature 004, T015/T016, FR-419 y Principio VII).

Los grabadores envuelven `contexto.contenido` y `contexto.resolvedor`: registran en la línea lo que la partida
viva YA pidió (el contenido de cada sala con su ordinal y cada ficha, una vez) y delegan todo lo demás.
Las pruebas de delegación y de error usan dobles; las de integración, la partida real con el paquete offline.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import _correr, _crear, jugar
from Data.ValidacionDatos import ErrorDatos
from DTO.AccionDTO import AccionDTO
from Logic.LineaTiempo import LineaTiempo
from Service.ArmadorEstado import ArmadorEstado
from Service.GrabadoresLinea import ContenidoGrabador, ResolvedorGrabador


class _Ficha:
    def __init__(self, id_ficha: str) -> None:
        self.id = id_ficha


class _Sala:
    def __init__(self, id_sala: int) -> None:
        self.id = id_sala


class _ResolvedorDoble:
    """Un resolvedor de mentira que anota cada llamada que recibe."""

    def __init__(self) -> None:
        self.llamadas: list = []
        self.marca = "dato propio"

    def ficha(self, id_ficha: str, contar_acierto: bool = True):
        self.llamadas.append(("ficha", id_ficha, contar_acierto))
        return _Ficha(id_ficha)

    def rechazo(self, id_ficha: str):
        self.llamadas.append(("rechazo", id_ficha))
        return "rechazada"

    def resolver_contenido(self, contenidos: list) -> int:
        self.llamadas.append(("resolver_contenido", contenidos))
        return len(contenidos)

    def version_catalogo(self) -> str:
        return "v-doble"


class _ContenidoDoble:
    def __init__(self) -> None:
        self.llamadas: list = []

    def asegurar_sala(self, id_sala: int):
        self.llamadas.append(("asegurar_sala", id_sala))
        return _Sala(id_sala)

    def salas_pedidas(self) -> int:
        return 42


class _Jugador:
    def __init__(self, acciones: int = 0) -> None:
        self.acciones = acciones


class PruebasGrabadoresConDobles(unittest.TestCase):

    def test_grabadores_registran_la_carga_de_sala_con_su_ordinal_fr419(self):
        linea, jugador = LineaTiempo(3), _Jugador(0)
        contenido = ContenidoGrabador(_ContenidoDoble(), linea, jugador)
        sala_a = contenido.asegurar_sala(1)
        jugador.acciones = 4
        contenido.asegurar_sala(7)
        contenido.asegurar_sala(1)                                      # repetida: no se vuelve a registrar
        self.assertEqual([(c.ordinal, c.sala.id) for c in linea.cargas], [(0, 1), (4, 7)])
        self.assertIs(linea.cargas[0].sala, sala_a)                     # se guarda la referencia que Data entregó

    def test_grabadores_registran_cada_ficha_una_sola_vez_fr419(self):
        linea = LineaTiempo(3)
        resolvedor = ResolvedorGrabador(_ResolvedorDoble(), linea)
        primera = resolvedor.ficha("ene_rata")
        resolvedor.ficha("ene_rata", contar_acierto=False)
        resolvedor.ficha("itm_daga")
        self.assertEqual([f.id for f in linea.fichas], ["ene_rata", "itm_daga"])
        self.assertEqual(primera.id, "ene_rata")

    def test_grabadores_pasan_los_argumentos_tal_cual_fr419(self):
        doble = _ResolvedorDoble()
        ResolvedorGrabador(doble, LineaTiempo(3)).ficha("itm_daga", contar_acierto=False)
        self.assertEqual(doble.llamadas, [("ficha", "itm_daga", False)])     # la caché cuenta igual que sin grabador

    def test_grabadores_delegan_el_resto_al_resolvedor(self):
        resolvedor = ResolvedorGrabador(_ResolvedorDoble(), LineaTiempo(3))
        self.assertEqual(resolvedor.version_catalogo(), "v-doble")
        self.assertEqual(resolvedor.marca, "dato propio")                # también los atributos
        contenido = ContenidoGrabador(_ContenidoDoble(), LineaTiempo(3), _Jugador())
        self.assertEqual(contenido.salas_pedidas(), 42)
        with self.assertRaises(AttributeError):
            resolvedor.no_existe

    def test_grabadores_delegan_rechazo_y_resolver_contenido_fr419(self):
        doble = _ResolvedorDoble()
        linea = LineaTiempo(3)
        resolvedor = ResolvedorGrabador(doble, linea)
        self.assertEqual(resolvedor.rechazo("ene_x"), "rechazada")
        self.assertEqual(resolvedor.resolver_contenido(["a", "b"]), 2)
        self.assertEqual(doble.llamadas, [("rechazo", "ene_x"), ("resolver_contenido", ["a", "b"])])
        self.assertEqual(linea.fichas, [])                               # lo que no es ficha() no registra nada

    def test_grabadores_errordatos_propaga_sin_registrar_nada_fr419(self):
        linea = LineaTiempo(3)

        class _Roto:
            def ficha(self, id_ficha, contar_acierto=True):
                raise ErrorDatos("catalogo", "ficha inválida", id_ficha)

            def asegurar_sala(self, id_sala):
                raise ErrorDatos("contenido", "sala inválida")

        with self.assertRaises(ErrorDatos) as error:
            ResolvedorGrabador(_Roto(), linea).ficha("ene_mala")
        self.assertEqual(error.exception.id_ficha, "ene_mala")           # es el mismo error, sin envolver
        with self.assertRaises(ErrorDatos):
            ContenidoGrabador(_Roto(), linea, _Jugador()).asegurar_sala(3)
        self.assertEqual((linea.fichas, linea.cargas), ([], []))         # no queda ningún registro


def _sin_grabadores(contexto) -> None:
    """Quita lo que iniciar_partida ya instaló (los grabadores y la línea) para dejar el contexto como en la 1.ª entrega."""
    contexto.contenido = contexto.contenido._original
    contexto.resolvedor = contexto.resolvedor._original
    contexto.linea = None


def _instalar(contexto, linea: LineaTiempo) -> None:
    """Instala los grabadores en un contexto SIN grabadores: un solo envoltorio, con la línea de la prueba.

    iniciar_partida ya los instala (T018), así que primero se quitan; si no, quedarían doblemente envueltos."""
    _sin_grabadores(contexto)
    assert not isinstance(contexto.contenido, ContenidoGrabador) and not isinstance(contexto.resolvedor, ResolvedorGrabador)
    contexto.contenido = ContenidoGrabador(contexto.contenido, linea, contexto.jugador)
    contexto.resolvedor = ResolvedorGrabador(contexto.resolvedor, linea)


def _solicitudes(fuente) -> int:
    """Las solicitudes que le han hecho a la fuente (en FuenteJson es un método; en la offline, siempre 0)."""
    cuenta = fuente.solicitudes_realizadas
    return cuenta() if callable(cuenta) else cuenta


def _numeros_de_data(contexto) -> tuple:
    r, g = contexto.resolvedor, contexto.contenido
    return (_solicitudes(contexto.fuente), r.aciertos(), r.fallos(), r.lecturas_disco(),
            r.solicitudes_catalogo(), r.fichas_descargadas(), g.lotes_realizados(), g.salas_pedidas())


class PruebasGrabadoresConLaPartida(unittest.TestCase):

    def test_grabadores_registran_lo_que_la_partida_pidio_fr419(self):
        def prueba(carpeta):
            _, servicio, ctx = _crear(carpeta, semilla=1, reforzar=True)
            linea = LineaTiempo(5)
            _instalar(ctx, linea)
            estado = ArmadorEstado().armar_estado(ctx)
            salidas = [d for d in range(4) if estado.sala.salidas[d] is not None and not estado.sala.salidas[d].cerrada]
            self.assertTrue(salidas)
            destino = estado.sala.salidas[salidas[0]].sala_destino
            servicio.ejecutar(ctx, AccionDTO("mover", direccion=salidas[0]))
            self.assertEqual(ctx.jugador.Sala_Actual, destino)
            self.assertEqual([(c.ordinal, c.sala.id) for c in linea.cargas], [(0, destino)])
            self.assertGreater(len(linea.fichas), 0)                     # las fichas de lo que cargó la sala
            ids = [f.id for f in linea.fichas]
            for i, id_ficha in enumerate(ids):                           # una sola vez cada id
                self.assertNotIn(id_ficha, ids[:i])
        _correr(prueba)

    def test_grabadores_no_piden_nada_nuevo_a_data(self):
        def prueba(carpeta):
            _, _, sin = _crear(os.path.join(carpeta, "sin"), semilla=4, reforzar=True)
            _sin_grabadores(sin)                                         # sin NINGÚN grabador: el contraste es real
            _, _, con = _crear(os.path.join(carpeta, "con"), semilla=4, reforzar=True)
            _instalar(con, LineaTiempo(5))
            jugar(sin, 60)
            jugar(con, 60)
            self.assertGreater(con.jugador.acciones, 10)
            self.assertEqual(sin.jugador.acciones, con.jugador.acciones)  # la misma partida
            self.assertEqual(_numeros_de_data(con), _numeros_de_data(sin))
        _correr(prueba)

    def test_grabadores_no_cambian_lo_que_ve_el_servicio_fr419(self):
        def prueba(carpeta):
            _, _, sin = _crear(os.path.join(carpeta, "sin"), semilla=5, reforzar=True)
            _sin_grabadores(sin)
            _, _, con = _crear(os.path.join(carpeta, "con"), semilla=5, reforzar=True)
            _instalar(con, LineaTiempo(5))
            self.assertEqual(jugar(sin, 50), jugar(con, 50))
            self.assertIs(type(con.contenido), ContenidoGrabador)           # un solo envoltorio
            self.assertNotIsInstance(con.contenido._original, ContenidoGrabador)
            self.assertNotIsInstance(con.resolvedor._original, ResolvedorGrabador)
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

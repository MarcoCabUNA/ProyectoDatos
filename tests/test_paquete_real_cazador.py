"""
Prueba de humo de la feature 001 con el paquete real de la Parte II (T059): FR-107 a FR-111 y FR-114.

Offline, sobre paquete/ (catálogo 4b9e75a42be5), en la cripta-06. La partida empieza en la sala 141; hay un espectro
acechador (rango 2400) en la sala 123 y un sabueso óseo (rango 600) en la sala 41. El jugador hace una lista fija de
acciones (esperar y moverse, ver RECORRIDO): despierta al espectro, sube hasta la sala del sabueso y da una vuelta
con los dos persiguiéndolo. Se comprueba que:
  - la cripta y las fichas reales de los dos cazadores se cargan sin errores de FR-122 (costos y rangos válidos):
    la partida inicia y ninguna acción se rechaza;
  - cada decisión de cada cazador es la de paso_desde_cero en ese mismo instante (FR-114), sobre un esqueleto real
    de 300 salas con costos entre 20 y 300;
  - los dos cazadores deciden con su rango del catálogo (600 y 2400) y avanzan por la ruta más barata pagando el
    costo de cada salida (FR-108, FR-110, FR-111), y atacan cuando comparten sala con el jugador (FR-107);
  - `--replay` del log generado (ServicioReplay, sin vista) pasa por los mismos estados y toma las mismas decisiones.
Con este recorrido nadie llega a esperar por d > rango o por falta de ruta (FR-109): en esta cripta el jugador no
puede alejarse más que su rango de un cazador despierto solo moviéndose y esperando. Si alguna decisión fuera esperar,
también se compara con paso_desde_cero. FR-109 lo prueban H2-1 y H2-2 (casos 1 y 2 del Apéndice B).

    python -m unittest tests.test_paquete_real_cazador -v
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from Logic.BusquedaCostoMinimo import paso_desde_cero  # noqa: E402
from Logic.RutasHaciaJugador import RutasHaciaJugador  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from Service.ServicioReplay import ServicioReplay  # noqa: E402

CRIPTA = "cripta-06"
SEMILLA = 2026
ESPERAR = None
# Salas a las que se mueve el jugador, en orden (ESPERAR es una acción de esperar). Empieza en la 141.
RECORRIDO = [
    ESPERAR,                                          # todavía no hay ningún cazador despierto
    121, 122, 123,                                    # entra a la sala del espectro acechador (rango 2400)
    122, 102, 101, 81, 61, 41,                        # el espectro lo sigue; entra a la sala del sabueso óseo (600)
    42, 41, 61, 81, 82, 62, 61, 81, 101, 121, 141,    # los dos lo persiguen (salidas de 20 a 300)
    ESPERAR,                                          # lo alcanzan en la sala 141 y atacan
]
ESPECTRO = "Espectro acechador #1"
SABUESO = "Sabueso óseo #1"


class DecisionesComparadas:
    """
    Reemplaza RutasHaciaJugador.decidir mientras dura el bloque with: cada decisión de cazador se compara con
    paso_desde_cero en ese mismo instante y se anota como (sala del cazador, sala del jugador, rango, paso).
    """

    def __init__(self):
        self.decisiones = []
        self.distintas = []

    def __enter__(self):
        self._original = RutasHaciaJugador.decidir
        registro = self

        def decidir(rutas, sala_cazador, sala_jugador, rango):
            paso = registro._original(rutas, sala_cazador, sala_jugador, rango)
            esperado = paso_desde_cero(rutas.busqueda.grafo, sala_jugador, sala_cazador, rango)
            registro.decisiones.append((sala_cazador, sala_jugador, rango, paso))
            if paso != esperado:
                registro.distintas.append((sala_cazador, sala_jugador, rango, paso, esperado))
            return paso

        RutasHaciaJugador.decidir = decidir
        return self

    def __exit__(self, *error):
        RutasHaciaJugador.decidir = self._original
        return False


class TestPaqueteRealCazador(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def _partida(self, nombre):
        return ServicioPartida(ConfiguracionDTO(offline=True), fuente=FuenteOffline(str(RAIZ / "paquete")),
                               carpeta_cache=os.path.join(self.carpeta, nombre, "cache"),
                               carpeta_logs=os.path.join(self.carpeta, nombre, "logs"))

    @staticmethod
    def _accion(ctx, sala):
        if sala is ESPERAR:
            return AccionDTO("esperar")
        actual = ctx.jugador.Sala_Actual
        for direccion in range(4):
            salida = ctx.mazmorra.salida(actual, direccion)
            if salida is not None and salida.destino == sala:
                return AccionDTO("mover", direccion=direccion)
        raise AssertionError(f"la sala {actual} no tiene salida a la {sala}")

    def _jugar(self):
        """Juega RECORRIDO. Devuelve (contexto, ruta del log, estados: el inicial y el de cada acción)."""
        partida = self._partida("viva")
        ctx = partida.iniciar_partida(CRIPTA, "Ana", semilla=SEMILLA)   # FR-122: un dato inválido no deja iniciar
        self.assertEqual(ctx.cripta.salas_total, 300)
        acciones = ServicioAccionJugador()
        estados = [partida.estado(ctx)]
        for sala in RECORRIDO:
            self.assertFalse(estados[-1].terminado, f"la partida terminó antes de ir a la sala {sala}")
            estado = acciones.ejecutar(ctx, self._accion(ctx, sala))
            self.assertIsNone(estado.resultado, f"se rechazó la acción hacia la sala {sala}")   # FR-122 al entrar
            if sala is not ESPERAR:
                self.assertEqual(ctx.jugador.Sala_Actual, sala)
            estados.append(estado)
        return ctx, ctx.bitacora.ruta(), estados

    def test_t059_fr107_a_fr111_fr114_cazadores_reales_de_la_cripta_06(self):
        with DecisionesComparadas() as vivas:
            ctx, ruta, estados = self._jugar()

        # FR-114: todas iguales a paso_desde_cero, y son bastantes
        self.assertEqual(vivas.distintas, [], "alguna decisión de cazador difiere de paso_desde_cero")
        self.assertGreaterEqual(len(vivas.decisiones), 20, "los cazadores decidieron muy pocas veces")

        # FR-108, FR-110, FR-111: cada uno con el rango de su ficha; pasos que pagan el costo de la salida
        rangos, costos, avances = [], [], 0
        for sala_cazador, sala_jugador, rango, paso in vivas.decisiones:
            if rango not in rangos:
                rangos.append(rango)
            if paso is not None:
                avances += 1
                self.assertEqual(paso[1], ctx.mazmorra.costo_paso(sala_cazador, paso[0]))
                if paso[1] not in costos:
                    costos.append(paso[1])
        self.assertEqual(rangos, [2400, 600])                 # primero despierta el espectro, después el sabueso
        self.assertGreaterEqual(avances, 20)
        for costo in (20, 100, 150, 200, 300):
            self.assertIn(costo, costos)

        # FR-107: los dos atacan al compartir sala con el jugador
        mensajes = []
        for estado in estados:
            for mensaje in estado.mensajes:
                if mensaje not in mensajes:
                    mensajes.append(mensaje)
        for nombre in (ESPECTRO, SABUESO):
            self.assertTrue(any(f"{nombre} ataca a Jugador" in m for m in mensajes), nombre)
        self.assertLess(estados[-1].jugador.vida, estados[0].jugador.vida)
        self.assertFalse(estados[-1].terminado)

        # --replay del log: mismos estados y mismas decisiones de cazador
        with DecisionesComparadas() as repetidas:
            reproducidos = []
            resultado = ServicioReplay(self._partida("replay")).reproducir(
                ruta, al_avanzar=lambda i, accion, estado: reproducidos.append(estado))
        self.assertEqual(resultado.encabezado.semilla, SEMILLA)
        self.assertEqual(resultado.acciones_reproducidas, len(RECORRIDO))
        self.assertEqual(reproducidos, estados[1:], "--replay pasó por otro estado")
        self.assertEqual(resultado.estado_final, estados[-1])
        self.assertEqual(repetidas.distintas, [])
        self.assertEqual(repetidas.decisiones, vivas.decisiones, "--replay tomó otras decisiones de cazador")


if __name__ == "__main__":
    unittest.main()

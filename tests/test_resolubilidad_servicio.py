"""
Pruebas de la feature 003 en Servicios (integrante 2): ServicioResolubilidad (T035, T036, T039) y los cambios
acordados con el integrante 3 en ServicioPartida (T037), ContextoPartida (T038) y ErroresServicio (T040).

Las criptas se arman a mano con tests/ayudas_resolubilidad.py (Principio VI) y se sirven con FuenteConLlaves, que
cuenta las solicitudes por operación. Todo se escribe en carpetas temporales (caché, logs y guardados).
ServicioResolubilidad se importa dentro de cada prueba: así las pruebas de T037 y T038 corren (y fallan o pasan por
su propio motivo) antes de que exista el módulo de T039.
"""
import dataclasses
import os
import random
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ))

from ayudas_resolubilidad import FuenteConLlaves, abierta, cara, cripta, paquete_temporal, puerta, ubic  # noqa: E402

from Data.AlmacenLlaves import AlmacenLlaves  # noqa: E402
from Data.BitacoraReplayIO import BitacoraReplayIO  # noqa: E402
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from Data.FuenteRed import FuenteRed  # noqa: E402
from Data.ValidacionDatos import ErrorDatos  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.Direcciones import E, N  # noqa: E402
from DTO.ReporteResolubilidadDTO import NO_CONCLUYO, NO_RESOLUBLE, RESOLUBLE  # noqa: E402
from Logic import VerificadorResolubilidad  # noqa: E402
from Service.ContextoPartida import ContextoPartida  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioGuardado import ServicioGuardado  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from Service.ServicioReplay import ServicioReplay  # noqa: E402

ID = "prueba"
SEMILLA = 4242


# ---------------------------------------------------------------- criptas de prueba
def cripta_resoluble():
    """1 → 2 abierta; puerta 2–3 (A) con A en la sala 2; puerta 3–4 (S) con S en la sala 3. Orden: A, S."""
    return cripta(4, [abierta(1, E, 2), puerta(2, E, 3, "A"), puerta(3, E, 4, "S")],
                  [ubic("A", 2), ubic("S", 3)], sala_salida=4)


def cripta_no_resoluble():
    """Apéndice B, caso 4: S está detrás de la única puerta que la pide (puerta 2–3 (S)), un ciclo de un paso."""
    return cripta(3, [abierta(1, E, 2), puerta(2, E, 3, "S")], [ubic("S", 3)], sala_salida=3)


def cripta_enemigo_inexistente():
    """H2-8: B la suelta el enemigo e-9999 (no existe) en la sala 12; B abre la puerta 1–3 y S la puerta 3–2."""
    return cripta(12, [abierta(1, E, 12), puerta(1, N, 3, "B"), puerta(3, N, 2, "S")],
                  [ubic("B", 12, "e-9999"), ubic("S", 3)], sala_salida=2)


def cripta_sala_inexistente():
    """H2-7: la llave A está en la sala 99, que no existe en el esqueleto."""
    return cripta(4, [abierta(1, E, 2), puerta(2, E, 3, "A"), puerta(3, E, 4, "S")],
                  [ubic("A", 99), ubic("S", 3)], sala_salida=4)


def cripta_costos_distintos():
    """H4-5: la salida 3–4 declara costo 150 en la cara de la sala 3 y 200 en la de la sala 4."""
    return cripta(4, [abierta(1, E, 2), puerta(2, E, 3, "S"), cara(3, E, 4, costo=150), cara(4, 3, 3, costo=200)],
                  [ubic("S", 2)], sala_salida=3)


def cripta_cierre_invalido():
    """FR-323 (T055 de la 001): la puerta 2–3 declara cierre_automatico 0."""
    return cripta(3, [abierta(1, E, 2), puerta(2, E, 3, "S", cierre_automatico=0)], [ubic("S", 2)], sala_salida=3)


# ---------------------------------------------------------------- ayudantes
def _resolubilidad():
    """El módulo de T039 (se importa adentro; ver el docstring del archivo)."""
    from Service import ServicioResolubilidad as modulo
    return modulo


class _PartidaEspia(ServicioPartida):
    """ServicioPartida real que anota cuántas veces se llamó iniciar_partida y qué se había pedido hasta entonces."""

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.llamadas_iniciar = 0
        self.contenido_al_iniciar = None
        self.catalogo_al_iniciar = None
        self.azar_al_iniciar = None

    def iniciar_partida(self, *argumentos, **opciones):
        self.llamadas_iniciar += 1
        self.contenido_al_iniciar = self.fuente().pedidos_contenido
        self.catalogo_al_iniciar = self.fuente().pedidos_catalogo
        self.azar_al_iniciar = random.getstate()
        return super().iniciar_partida(*argumentos, **opciones)


def _archivos(carpeta: str, extension: str) -> list[str]:
    """Los archivos con esa extensión en toda la carpeta (logs y guardados que se hayan creado)."""
    encontrados = []
    for raiz, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if nombre.endswith(extension):
                encontrados.append(os.path.join(raiz, nombre))
    return encontrados


class _ConCarpeta(unittest.TestCase):
    """Una carpeta temporal por prueba, y cómo armar el ServicioPartida que escribe solo en ella."""

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def partida(self, fuente, almacen=None, clase=ServicioPartida, config=None):
        return clase(config if config is not None else ConfiguracionDTO(), fuente=fuente,
                     carpeta_cache=os.path.join(self.carpeta, "cache"),
                     carpeta_logs=os.path.join(self.carpeta, "logs"), almacen_llaves=almacen)

    def logs(self) -> list[str]:
        return _archivos(os.path.join(self.carpeta, "logs"), ".log")


# ================================================================ T037: ServicioPartida
class PruebasServicioPartida(_ConCarpeta):

    def test_fr318_offline_sin_almacen_de_llaves(self):
        anterior = os.getcwd()
        os.makedirs(os.path.join(self.carpeta, "paquete"))
        os.chdir(self.carpeta)
        try:
            partida = ServicioPartida(ConfiguracionDTO(offline=True))
            self.assertIsInstance(partida.fuente(), FuenteOffline)
            self.assertIsNone(partida.almacen_llaves())
        finally:
            os.chdir(anterior)

    def test_fr317_red_con_almacen_de_llaves(self):
        partida = ServicioPartida(ConfiguracionDTO(offline=False))      # crear la fuente no hace solicitudes
        self.assertIsInstance(partida.almacen_llaves(), AlmacenLlaves)
        self.assertIsInstance(partida.fuente(), FuenteRed)
        self.assertIs(partida.almacen_llaves(), partida.almacen_llaves())

    def test_fr311_iniciar_partida_con_datos_no_los_vuelve_a_pedir(self):
        fuente = FuenteConLlaves(*cripta_resoluble())
        partida = self.partida(fuente)
        datos = partida.abrir_datos(ID)
        self.assertEqual((fuente.pedidos_generales, fuente.pedidos_esqueleto), (1, 1))
        contexto = partida.iniciar_partida(ID, "Ana", semilla=SEMILLA, datos=datos)
        self.assertEqual((fuente.pedidos_generales, fuente.pedidos_esqueleto), (1, 1))
        self.assertIs(contexto.cripta, datos[0])
        self.assertIs(contexto.esqueleto, datos[2])


# ================================================================ T038: ContextoPartida
class PruebasContextoPartida(_ConCarpeta):

    def test_fr313_contexto_resolubilidad_ultimo_campo_y_none(self):
        nombres = [campo.name for campo in dataclasses.fields(ContextoPartida)]
        self.assertEqual(nombres[-2:], ["linea", "resolubilidad"])
        contexto = self.partida(FuenteConLlaves(*cripta_resoluble())).iniciar_partida(ID, "Ana", semilla=SEMILLA)
        self.assertIsNone(contexto.resolubilidad)


# ================================================================ T035: historia 1
class PruebasIniciarResoluble(_ConCarpeta):

    def test_h1_8_fr301_no_descarga_contenido_ni_consume_azar(self):
        dto, salas, ubicaciones = cripta_resoluble()
        fuente = FuenteConLlaves(dto, salas, ubicaciones)
        partida = self.partida(fuente, clase=_PartidaEspia)
        azar_antes = random.getstate()
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        self.assertEqual(partida.llamadas_iniciar, 1)
        self.assertEqual(partida.contenido_al_iniciar, 0)             # antes de crear el motor: ningún contenido
        self.assertEqual(partida.catalogo_al_iniciar, 0)
        self.assertEqual(partida.azar_al_iniciar, azar_antes)        # ni se tocó el generador

        sin_verificar = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        directo = sin_verificar.iniciar_partida(ID, "Ana", semilla=SEMILLA)
        self.assertEqual(partida.estado(contexto), sin_verificar.estado(directo))
        self.assertEqual(contexto.motor.reloj, directo.motor.reloj)

        repetida = ServicioReplay(self.partida(FuenteConLlaves(dto, salas, ubicaciones)))
        resultado = repetida.reproducir(contexto.bitacora.ruta())
        self.assertEqual(resultado.encabezado.semilla, SEMILLA)
        self.assertEqual(resultado.estado_final, partida.estado(contexto))

    def test_h1_9_fr313_reporte_en_el_contexto_antes_de_la_primera_accion(self):
        dto, salas, ubicaciones = cripta_resoluble()
        partida = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        self.assertEqual(contexto.jugador.acciones, 0)
        self.assertIsNotNone(contexto.resolubilidad)
        self.assertEqual(contexto.resolubilidad.veredicto, RESOLUBLE)
        self.assertEqual(contexto.resolubilidad.orden_llaves, ["A", "S"])
        self.assertEqual(contexto.resolubilidad, VerificadorResolubilidad.verificar(dto, salas, ubicaciones))

    def test_r9_fr301_verificacion_no_registra_en_historial_linea_ni_log(self):
        partida = self.partida(FuenteConLlaves(*cripta_resoluble()))
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        self.assertEqual(contexto.motor.historial.cantidad(), 0)
        self.assertEqual(contexto.linea.acciones, [])
        self.assertEqual(contexto.bitacora.acciones_escritas(), 0)
        leido = BitacoraReplayIO.leer(contexto.bitacora.ruta())       # solo el encabezado
        self.assertEqual(leido.acciones, [])
        self.assertEqual(leido.encabezado.semilla, SEMILLA)
        with open(contexto.bitacora.ruta(), encoding="utf-8") as archivo:
            self.assertTrue(archivo.read().rstrip().endswith("#ACCIONES"))
        self.assertEqual(len(self.logs()), 1)

    def test_h2_8_fr301_fr303_fr321_iniciar_sin_descargar_contenido(self):
        fuente = FuenteConLlaves(*cripta_enemigo_inexistente())
        partida = self.partida(fuente, clase=_PartidaEspia)
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        self.assertEqual(partida.contenido_al_iniciar, 0)
        self.assertEqual(contexto.resolubilidad.veredicto, RESOLUBLE)
        self.assertEqual(contexto.resolubilidad.orden_llaves, ["B", "S"])

    def test_r3_fr317_no_pide_dos_veces_datos_ni_esqueleto(self):
        fuente = FuenteConLlaves(*cripta_resoluble())
        partida = self.partida(fuente)
        _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        self.assertEqual(fuente.pedidos_generales, 1)
        self.assertEqual(fuente.pedidos_esqueleto, 1)               # el esqueleto tiene una sola página
        self.assertEqual(fuente.pedidos_llaves, 1)

    def test_fr315_verificar_e_iniciar_dan_el_mismo_reporte(self):
        modulo = _resolubilidad()
        for armar in (cripta_resoluble, cripta_no_resoluble, cripta_enemigo_inexistente):
            dto, salas, ubicaciones = armar()
            verificado = modulo.ServicioResolubilidad(self.partida(FuenteConLlaves(dto, salas, ubicaciones))) \
                .verificar(ID)
            contexto = modulo.ServicioResolubilidad(self.partida(FuenteConLlaves(dto, salas, ubicaciones))) \
                .iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
            self.assertEqual(verificado, contexto.resolubilidad, armar.__name__)


# ================================================================ T036: historia 4 (y dos de la historia 3)
class PruebasIniciarNoResoluble(_ConCarpeta):

    def _no_inicia(self, fuente, forzar=False):
        """Intenta iniciar y devuelve el ErrorPartidaNoIniciada; comprueba que no se creó nada."""
        modulo = _resolubilidad()
        partida = self.partida(fuente, clase=_PartidaEspia)
        with self.assertRaises(modulo.ErrorPartidaNoIniciada) as atrapado:
            modulo.ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", forzar, SEMILLA)
        self.assertEqual(partida.llamadas_iniciar, 0)                 # sin motor: el reloj no avanzó
        self.assertEqual(self.logs(), [])
        self.assertEqual(_archivos(self.carpeta, ".sav"), [])
        self.assertIsInstance(atrapado.exception, ValueError)
        self.assertNotEqual(str(atrapado.exception).strip(), "")
        return atrapado.exception

    def test_h4_1_apendiceB_caso4_fr311_no_resoluble_no_inicia(self):
        dto, salas, ubicaciones = cripta_no_resoluble()
        error = self._no_inicia(FuenteConLlaves(dto, salas, ubicaciones))
        self.assertEqual(error.reporte.veredicto, NO_RESOLUBLE)
        self.assertEqual(error.reporte, VerificadorResolubilidad.verificar(dto, salas, ubicaciones))
        self.assertEqual([llave.id for llave in error.reporte.llaves_no_obtenibles], ["S"])
        self.assertEqual(len(error.reporte.frontera), 1)
        self.assertEqual(len(error.reporte.ciclos), 1)

    def test_h4_2_fr312_fr313_forzar_inicia_con_advertencia(self):
        dto, salas, ubicaciones = cripta_no_resoluble()
        partida = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
        self.assertEqual(contexto.resolubilidad, VerificadorResolubilidad.verificar(dto, salas, ubicaciones))
        self.assertEqual(contexto.resolubilidad.veredicto, NO_RESOLUBLE)
        self.assertEqual(len(self.logs()), 1)

    def test_h4_3_fr312_forzar_con_resoluble_no_cambia_nada(self):
        modulo = _resolubilidad()
        dto, salas, ubicaciones = cripta_resoluble()
        sin = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        con = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        contexto_sin = modulo.ServicioResolubilidad(sin).iniciar_partida_nueva(ID, "Ana", False, SEMILLA)
        contexto_con = modulo.ServicioResolubilidad(con).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
        self.assertEqual(contexto_sin.resolubilidad, contexto_con.resolubilidad)
        self.assertEqual(sin.estado(contexto_sin), con.estado(contexto_con))
        self.assertEqual(contexto_sin.semilla, contexto_con.semilla)

    def test_h4_4_fr301_fr313_cargar_y_replay_no_verifican(self):
        modulo = _resolubilidad()
        dto, salas, ubicaciones = cripta_no_resoluble()
        partida = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        contexto = modulo.ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
        ServicioAccionJugador().ejecutar(contexto, AccionDTO("esperar"))
        ruta_guardado = os.path.join(self.carpeta, "partida.sav")
        ServicioGuardado(partida).guardar(contexto, ruta_guardado)
        ruta_log = contexto.bitacora.ruta()

        prohibido = AssertionError("cargar y --replay no deben pasar por ServicioResolubilidad")
        with mock.patch.object(modulo.ServicioResolubilidad, "verificar", side_effect=prohibido), \
                mock.patch.object(modulo.ServicioResolubilidad, "iniciar_partida_nueva", side_effect=prohibido):
            fuente_carga = FuenteConLlaves(dto, salas, ubicaciones)
            cargada = ServicioGuardado(self.partida(fuente_carga)).cargar(ruta_guardado, "Ana")
            self.assertEqual(fuente_carga.pedidos_llaves, 0)
            self.assertIsNone(cargada.resolubilidad)
            self.assertEqual(cargada.motor.reloj, contexto.motor.reloj)

            fuente_replay = FuenteConLlaves(dto, salas, ubicaciones)
            resultado = ServicioReplay(self.partida(fuente_replay)).reproducir(ruta_log)
            self.assertEqual(fuente_replay.pedidos_llaves, 0)
            self.assertEqual(resultado.acciones_reproducidas, 1)
            self.assertEqual(resultado.estado_final.reloj, contexto.motor.reloj)

    def test_h4_5_fr323_costos_distintos_no_inicia_ni_con_forzar(self):
        modulo = _resolubilidad()
        for forzar in (False, True):
            partida = self.partida(FuenteConLlaves(*cripta_costos_distintos()), clase=_PartidaEspia)
            with self.assertRaises(ErrorDatos) as atrapado:
                modulo.ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", forzar, SEMILLA)
            texto = str(atrapado.exception)
            self.assertIn("sala 3", texto)
            self.assertIn("sala 4", texto)
            self.assertIn("costo 150", texto)
            self.assertIn("costo 200", texto)
            self.assertEqual(partida.llamadas_iniciar, 0)
            self.assertEqual(self.logs(), [])
            self.assertEqual(_archivos(self.carpeta, ".sav"), [])

    def test_fr323_cierre_automatico_invalido_no_inicia_ni_con_forzar(self):
        modulo = _resolubilidad()
        for forzar in (False, True):
            partida = self.partida(FuenteConLlaves(*cripta_cierre_invalido()), clase=_PartidaEspia)
            with self.assertRaises(ErrorDatos) as atrapado:
                modulo.ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", forzar, SEMILLA)
            texto = str(atrapado.exception)
            self.assertIn("sala 2", texto)
            self.assertIn("salida E", texto)
            self.assertIn("cierre_automatico", texto)
            self.assertEqual(partida.llamadas_iniciar, 0)
            self.assertEqual(self.logs(), [])
            self.assertEqual(_archivos(self.carpeta, ".sav"), [])

    def test_h2_7_fr320_fr321_sala_inexistente_inicia_solo_con_forzar(self):
        error = self._no_inicia(FuenteConLlaves(*cripta_sala_inexistente()))
        reporte = error.reporte
        self.assertEqual(reporte.veredicto, NO_CONCLUYO)
        self.assertIn("llave A", reporte.mensaje)
        self.assertIn("sala 99", reporte.mensaje)
        self.assertEqual((reporte.orden_llaves, reporte.llaves_no_obtenibles, reporte.frontera, reporte.ciclos,
                          reporte.motivo), ([], [], [], [], None))

        partida = self.partida(FuenteConLlaves(*cripta_sala_inexistente()))
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
        self.assertEqual(contexto.resolubilidad, reporte)

    def test_fr320_llaves_no_disponibles_inicia_solo_con_forzar(self):
        for falla, trozo in (("presupuesto", "presupuesto"), ("429", "429"), ("red", "no se pudo conectar")):
            dto, salas, ubicaciones = cripta_resoluble()
            error = self._no_inicia(FuenteConLlaves(dto, salas, ubicaciones, falla_llaves=falla))
            self.assertEqual(error.reporte.veredicto, NO_CONCLUYO, falla)
            self.assertIn(trozo, error.reporte.mensaje)
            self.assertIn("ubicación de llaves", error.reporte.mensaje)
            self.assertEqual(error.reporte.version_cripta, dto.version)

            partida = self.partida(FuenteConLlaves(dto, salas, ubicaciones, falla_llaves=falla))
            contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
            self.assertEqual(contexto.resolubilidad, error.reporte)
            shutil.rmtree(os.path.join(self.carpeta, "logs"), ignore_errors=True)

    def test_fr312_forzar_al_cargar_sin_efecto(self):
        dto, salas, ubicaciones = cripta_no_resoluble()
        partida = self.partida(FuenteConLlaves(dto, salas, ubicaciones))
        contexto = _resolubilidad().ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA)
        ruta = os.path.join(self.carpeta, "partida.sav")
        ServicioGuardado(partida).guardar(contexto, ruta)
        cargadas = []
        for config in (ConfiguracionDTO(), ConfiguracionDTO(forzar=True)):
            servicio = self.partida(FuenteConLlaves(dto, salas, ubicaciones), config=config)
            cargada = ServicioGuardado(servicio).cargar(ruta, "Ana")
            self.assertIsNone(cargada.resolubilidad)
            cargadas.append(servicio.estado(cargada))
        self.assertEqual(cargadas[0], cargadas[1])

    # ---- historia 3: verificar ----
    def test_fr314_verificar_cripta_inexistente_no_concluyo(self):
        modulo = _resolubilidad()
        dto, salas, ubicaciones = cripta_resoluble()
        en_linea = modulo.ServicioResolubilidad(
            self.partida(FuenteConLlaves(dto, salas, ubicaciones, inexistente=True))).verificar(ID)
        self.assertEqual(en_linea.veredicto, NO_CONCLUYO)
        self.assertEqual(en_linea.id_cripta, ID)
        self.assertIn("404", en_linea.mensaje)

        carpeta_paquete = paquete_temporal(os.path.join(self.carpeta, "paquete"), dto, salas, ubicaciones)
        offline = modulo.ServicioResolubilidad(self.partida(FuenteOffline(carpeta_paquete))).verificar("no-existe")
        self.assertEqual(offline.veredicto, NO_CONCLUYO)
        self.assertEqual(offline.id_cripta, "no-existe")
        self.assertIn("falta el archivo", offline.mensaje)
        self.assertIsNone(offline.version_cripta)

    def test_fr323_verificar_costo_invalido_no_concluyo(self):
        reporte = _resolubilidad().ServicioResolubilidad(
            self.partida(FuenteConLlaves(*cripta_costos_distintos()))).verificar(ID)
        self.assertEqual(reporte.veredicto, NO_CONCLUYO)
        self.assertIn("costo 150", reporte.mensaje)
        self.assertEqual((reporte.orden_llaves, reporte.llaves_no_obtenibles, reporte.frontera, reporte.ciclos,
                          reporte.motivo), ([], [], [], [], None))


# ================================================================ T040: ErroresServicio
class PruebasErroresServicio(unittest.TestCase):

    def test_fr311_error_partida_no_iniciada_es_esperado(self):
        from Service.ErroresServicio import ERRORES_ESPERADOS
        self.assertIn(_resolubilidad().ErrorPartidaNoIniciada, ERRORES_ESPERADOS)


if __name__ == "__main__":
    unittest.main()

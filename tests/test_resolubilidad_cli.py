"""
Pruebas de la feature 003 en la línea de comandos (integrante 2): --verificar y --forzar (historia 3, T043 a T046) y el
controlador al iniciar (historia 4, T053).

Las criptas se arman a mano (tests/ayudas_resolubilidad.py, Principio VI). En línea se sirven con FuenteConLlaves,
que reemplaza a FuenteRed dentro de ServicioPartida (mock.patch); con --offline se escribe un paquete temporal en la
carpeta de trabajo. Todo corre en carpetas temporales: nada se escribe en cache/, logs/ ni saves/ del proyecto.
Las pruebas que corren en otro proceso leen la salida como UTF-8.
"""
import contextlib
import dataclasses
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(CARPETA_TESTS))
sys.path.insert(0, str(RAIZ))

from ayudas_resolubilidad import FuenteConLlaves, abierta, cara, cripta, paquete_temporal, puerta, ubic  # noqa: E402

import main  # noqa: E402
from Data.ClienteHttp import ClienteHttp  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ReporteResolubilidadDTO import (NO_CONCLUYO, NO_RESOLUBLE, RESOLUBLE, CicloLlavesDTO,  # noqa: E402
                                         DependienteCicloDTO, LlaveNoObtenibleDTO, PasoCicloDTO, PuertaLlaveDTO,
                                         ReporteResolubilidadDTO)
from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO  # noqa: E402
from Logic import VerificadorResolubilidad  # noqa: E402
from Service.ServicioBench import ServicioBench  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from UIController.ControladorBackend import ControladorBackend, ErrorOperacion  # noqa: E402
from UIController.LectorArgumentos import ErrorArgumentos, leer_argumentos  # noqa: E402

ID = "prueba"
SEMILLA = 777


# ---------------------------------------------------------------- criptas de prueba (sala_salida 9, llave S)
def cripta_resoluble():
    """H1-3: A en 2 (salida 1–2), puerta 1–3 (A), B en 3, puerta 3–4 (B), S en 4; 4–8 abierta y la puerta 8–9 (S)."""
    return cripta(9, [abierta(1, E, 2), puerta(1, S, 3, "A"), puerta(3, E, 4, "B"), abierta(4, S, 8),
                      puerta(8, E, 9, "S")],
                  [ubic("S", 4), ubic("B", 3), ubic("A", 2)])


def cripta_ciclo():
    """H2-2: A en 6 detrás de la puerta 2–6 (B), B en 7 detrás de la 3–7 (A), S en 8 detrás de la 5–8 (A)."""
    return cripta(9, [abierta(1, E, 2), abierta(1, S, 3), abierta(1, O, 5), puerta(2, E, 6, "B"),
                      puerta(3, S, 7, "A"), puerta(5, S, 8, "A"), puerta(8, E, 9, "S")],
                  [ubic("A", 6), ubic("B", 7), ubic("S", 8)])


def cripta_h1_5():
    """Apéndice B, caso 3 (H1-5): A en 2 y B en 3 sin llaves; puertas 5–6 (A) y 6–7 (B); S en 7."""
    return cripta(9, [abierta(1, E, 2), abierta(1, S, 3), abierta(1, O, 5), puerta(5, S, 6, "A"),
                      puerta(6, S, 7, "B"), abierta(7, E, 8), puerta(8, E, 9, "S")],
                  [ubic("S", 7), ubic("B", 3), ubic("A", 2)])


def cripta_sala_inexistente():
    """H2-7: la llave A está en la sala 99, que no existe."""
    return cripta(9, [abierta(1, E, 2), puerta(2, E, 3, "A"), abierta(3, S, 8), puerta(8, E, 9, "S")],
                  [ubic("A", 99), ubic("S", 3)])


def cripta_costo_cero():
    """H3-8: la salida 1–2 declara costo 0 (FR-323, 001 FR-122)."""
    return cripta(9, [abierta(1, E, 2, costo=0), puerta(2, E, 9, "S")], [ubic("S", 2)])


def cripta_cierre_invalido():
    """FR-323 (T055 de la 001): la puerta 2–9 declara cierre_automatico 0."""
    return cripta(9, [abierta(1, E, 2), puerta(2, E, 9, "S", cierre_automatico=0)], [ubic("S", 1)])


CRIPTAS = {"resoluble": cripta_resoluble, "ciclo": cripta_ciclo, "h1_5": cripta_h1_5}


# ---------------------------------------------------------------- ayudantes
@contextlib.contextmanager
def en_carpeta_temporal():
    """El directorio de trabajo es una carpeta vacía (cache/, logs/ y paquete/ nacen ahí)."""
    anterior, carpeta = os.getcwd(), tempfile.mkdtemp()
    os.chdir(carpeta)
    try:
        yield carpeta
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


def correr_main(argumentos: list[str], fuente=None) -> tuple[int, str]:
    """main.main con la salida capturada; con 'fuente', esa fuente reemplaza a FuenteRed (en línea, sin red)."""
    salida = io.StringIO()
    with contextlib.ExitStack() as pila:
        if fuente is not None:
            pila.enter_context(mock.patch("Service.ServicioPartida.FuenteRed", lambda: fuente))
        pila.enter_context(contextlib.redirect_stdout(salida))
        codigo = main.main(argumentos)
    return codigo, salida.getvalue()


def texto_de(reporte: ReporteResolubilidadDTO) -> str:
    """Lo que --verificar debe escribir para ese reporte."""
    from UIController.TextoResolubilidad import lineas_reporte
    return "".join(linea + "\n" for linea in lineas_reporte(reporte))


def lanzar_con_fuente_falsa(nombre: str, argumentos: list[str]) -> int:
    """Lo usa el proceso aparte de SC-303: main.main con la cripta 'nombre' servida por FuenteConLlaves."""
    fuente = FuenteConLlaves(*CRIPTAS[nombre]())
    with mock.patch("Service.ServicioPartida.FuenteRed", lambda: fuente):
        return main.main(argumentos)


_LANZADOR = ("import sys; sys.path[:0] = [sys.argv[1], sys.argv[2]]; import test_resolubilidad_cli as t; "
             "sys.exit(t.lanzar_con_fuente_falsa(sys.argv[3], sys.argv[4:]))")

_SIN_VISTA = ("import sys; sys.path.insert(0, sys.argv[1]); import main; codigo = main.main(sys.argv[2:]); "
              "vista = [m for m in sys.modules if m == 'pygame' or m == 'View' or m.startswith(('pygame.', 'View.'))]; "
              "print('MODULOS_DE_VISTA=' + ','.join(vista)); sys.exit(codigo)")


def en_otro_proceso(comando: list[str], carpeta: str, entorno: dict | None = None) -> tuple[int, str]:
    """Corre 'comando' con este intérprete en otro proceso y lee la salida estándar como UTF-8 (estricto: un byte que
    no es UTF-8 hace fallar la prueba). La salida de errores solo se agrega para el mensaje de la prueba."""
    proceso = subprocess.run([sys.executable, "-B", *comando], cwd=carpeta, capture_output=True,
                             env=entorno if entorno is not None else dict(os.environ))
    return proceso.returncode, proceso.stdout.decode("utf-8") + proceso.stderr.decode("utf-8", errors="replace")


def reporte_de_inicio(carpeta: str, datos) -> ReporteResolubilidadDTO:
    """El reporte que deja iniciar_partida_nueva (con forzar, para que inicie siempre) con esa cripta."""
    from Service.ServicioResolubilidad import ServicioResolubilidad
    partida = ServicioPartida(ConfiguracionDTO(), fuente=FuenteConLlaves(*datos),
                              carpeta_cache=os.path.join(carpeta, "cache_inicio"),
                              carpeta_logs=os.path.join(carpeta, "logs_inicio"), almacen_llaves=None)
    return ServicioResolubilidad(partida).iniciar_partida_nueva(ID, "Ana", True, SEMILLA).resolubilidad


def _medicion_chica() -> list[ResultadoBenchDTO]:
    return [ResultadoBenchDTO("prueba", "medición chica", 1, 0.5, 0.5, "nota")]


class _BenchChico(ServicioBench):
    """ServicioBench con una sola medición chica y fija (para comparar salidas de --bench)."""

    def __init__(self, mediciones=None):
        super().__init__([_medicion_chica])


# ================================================================ T043: argumentos
class PruebasArgumentos(unittest.TestCase):

    def test_fr314_verificar_lee_el_id(self):
        self.assertEqual(leer_argumentos(["--verificar", "cripta-01"]).verificar, "cripta-01")
        self.assertEqual(leer_argumentos(["--verificar=cripta-01", "--offline"]).verificar, "cripta-01")
        self.assertIsNone(leer_argumentos([]).verificar)

    def test_fr314_verificar_sin_valor_o_vacio_codigo_2(self):
        for argumentos in (["--verificar"], ["--verificar", ""], ["--verificar", "   "]):
            with self.assertRaises(ErrorArgumentos):
                leer_argumentos(argumentos)
            self.assertEqual(correr_main(argumentos)[0], 2, argumentos)

    def test_fr314_verificar_con_replay_o_bench_codigo_2(self):
        for argumentos in (["--verificar", "c", "--replay", "x.log"], ["--verificar", "c", "--bench"],
                           ["--bench", "--verificar", "c"]):
            with self.assertRaises(ErrorArgumentos):
                leer_argumentos(argumentos)
            self.assertEqual(correr_main(argumentos)[0], 2, argumentos)

    def test_fr312_forzar_por_defecto_falso_y_no_excluyente(self):
        self.assertFalse(leer_argumentos([]).forzar)
        for argumentos in (["--forzar"], ["--forzar", "--replay", "x.log"], ["--bench", "--forzar"],
                           ["--verificar", "c", "--forzar"], ["--offline", "--forzar"]):
            self.assertTrue(leer_argumentos(argumentos).forzar, argumentos)

    def test_fr314_campos_de_configuracion_detras_de_hasta(self):
        nombres = [campo.name for campo in dataclasses.fields(ConfiguracionDTO)]
        self.assertEqual(nombres[-4:], ["checkpoint_cada", "hasta", "verificar", "forzar"])
        self.assertIsNone(ConfiguracionDTO().verificar)
        self.assertFalse(ConfiguracionDTO().forzar)

    def test_fr314_banderas_de_la_004_sin_cambios(self):
        self.assertEqual(leer_argumentos([]).checkpoint_cada, 20)
        self.assertEqual(leer_argumentos(["--checkpoint-cada", "5"]).checkpoint_cada, 5)
        self.assertEqual(leer_argumentos(["--replay", "x.log", "--hasta", "3"]).hasta, 3)
        for argumentos in (["--hasta", "3"], ["--checkpoint-cada", "0"], ["--replay", "x.log", "--hasta", "-1"]):
            with self.assertRaises(ErrorArgumentos):
                leer_argumentos(argumentos)


# ================================================================ T044: TextoResolubilidad
class PruebasTexto(unittest.TestCase):

    def lineas(self, reporte):
        from UIController.TextoResolubilidad import lineas_reporte
        return lineas_reporte(reporte)

    def test_fr314_texto_resoluble(self):
        reporte = ReporteResolubilidadDTO("cripta-01", RESOLUBLE, "fd58f7743b9e", "itm_llave_negra",
                                          orden_llaves=["itm_llave_bronce", "itm_llave_negra"])
        self.assertEqual(self.lineas(reporte), ["Cripta cripta-01 (versión fd58f7743b9e): RESOLUBLE",
                                                "Orden de obtención de llaves: itm_llave_bronce, itm_llave_negra"])

    def test_fr307_fr309_texto_no_resoluble(self):
        u = UbicacionLlaveDTO
        reporte = ReporteResolubilidadDTO(
            "prueba", NO_RESOLUBLE, "v1", "S",
            llaves_no_obtenibles=[LlaveNoObtenibleDTO("A", [u("A", 6)]), LlaveNoObtenibleDTO("B", [u("B", 7)]),
                                  LlaveNoObtenibleDTO("C", []),
                                  LlaveNoObtenibleDTO("S", [u("S", 8), u("S", 12, "e-1203")])],
            frontera=[PuertaLlaveDTO(2, E, 6, "B"), PuertaLlaveDTO(3, N, 7, None)],
            ciclos=[CicloLlavesDTO(
                pasos=[PasoCicloDTO("A", u("A", 6), PuertaLlaveDTO(2, E, 6, "B")),
                       PasoCicloDTO("B", u("B", 7), PuertaLlaveDTO(3, N, 7, "A"))],
                dependientes=[DependienteCicloDTO("S", u("S", 8), PuertaLlaveDTO(5, N, 8, "A"), "A")])])
        self.assertEqual(self.lineas(reporte), [
            "Cripta prueba (versión v1): NO RESOLUBLE",
            "Llaves no obtenibles:",
            "  - A: sala 6",
            "  - B: sala 7",
            "  - C: sin ubicación",
            "  - S: sala 8; sala 12 (enemigo e-1203)",
            "Frontera bloqueada:",
            "  - puerta 2–6 (desde la sala 2, salida E): requiere B",
            "  - puerta 3–7 (desde la sala 3, salida N): sin llave: no se puede abrir",
            "Ciclos:",
            "  1. A está en la sala 6 → la puerta 2–6 requiere B → B está en la sala 7 → la puerta 3–7 requiere A",
            "     - S (sala 8, puerta 5–8 requiere A) depende de A",
        ])

    def test_fr322_texto_con_motivo(self):
        motivo = VerificadorResolubilidad.motivo_sin_puerta_de_salida(cripta_resoluble()[0])
        reporte = ReporteResolubilidadDTO("prueba", NO_RESOLUBLE, "v1", "S", motivo=motivo)
        self.assertEqual(self.lineas(reporte), ["Cripta prueba (versión v1): NO RESOLUBLE", f"Motivo: {motivo}"])

    def test_fr323_texto_no_concluyo_sin_veredicto(self):
        mensaje = "Falló 'ubicación de llaves de cripta-01': se alcanzó el presupuesto de 9 solicitudes"
        reporte = ReporteResolubilidadDTO("cripta-01", NO_CONCLUYO, "v9", "S", mensaje=mensaje)
        self.assertEqual(self.lineas(reporte), ["Cripta cripta-01: la verificación NO CONCLUYÓ", mensaje])


# ================================================================ T045: escenarios de main
class PruebasVerificarMain(unittest.TestCase):

    def test_h3_1_fr314_fr315_verificar_resoluble_codigo_0(self):
        datos = cripta_resoluble()
        with en_carpeta_temporal() as carpeta:
            codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*datos))
            self.assertEqual(codigo, 0, texto)
            self.assertEqual(texto, texto_de(VerificadorResolubilidad.verificar(*datos)))
            self.assertIn("RESOLUBLE", texto)
            self.assertFalse(os.path.exists(os.path.join(carpeta, "logs")))

    def test_h3_2_fr314_fr315_verificar_no_resoluble_codigo_3(self):
        datos = cripta_ciclo()
        with en_carpeta_temporal() as carpeta:
            codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*datos))
            self.assertEqual(codigo, 3, texto)
            self.assertEqual(texto, texto_de(reporte_de_inicio(carpeta, datos)))
            self.assertIn("NO RESOLUBLE", texto)
            self.assertIn("→", texto)

    def test_h3_3_fr314_fr318_fr306_verificar_offline_igual_que_en_linea(self):
        for nombre, armar in CRIPTAS.items():
            datos = armar()
            with en_carpeta_temporal():
                en_linea = correr_main(["--verificar", ID], FuenteConLlaves(*datos))
            with en_carpeta_temporal() as carpeta:
                paquete_temporal(os.path.join(carpeta, "paquete"), *datos)
                prohibido = AssertionError("con --offline no se crea la fuente de red")
                with mock.patch("Service.ServicioPartida.FuenteRed", side_effect=prohibido), \
                        mock.patch.object(ClienteHttp, "get_json", side_effect=prohibido):
                    offline = correr_main(["--verificar", ID, "--offline"])
            self.assertIn(en_linea[0], (0, 3), en_linea[1])
            self.assertEqual(offline, en_linea, nombre)

    def test_h3_7_fr320_fr314_verificar_sin_llaves_codigo_1(self):
        for falla, trozo in (("presupuesto", "presupuesto"), ("429", "429"), ("red", "no se pudo conectar")):
            with en_carpeta_temporal():
                codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*cripta_resoluble(), falla_llaves=falla))
            self.assertEqual(codigo, 1, texto)
            self.assertIn("la verificación NO CONCLUYÓ", texto)
            self.assertIn(trozo, texto)
            self.assertNotIn("RESOLUBLE", texto)
        dto, salas, _ = cripta_resoluble()
        with en_carpeta_temporal() as carpeta:
            paquete_temporal(os.path.join(carpeta, "paquete"), dto, salas, None)
            codigo, texto = correr_main(["--verificar", ID, "--offline"])
        self.assertEqual(codigo, 1, texto)
        self.assertIn("la verificación NO CONCLUYÓ", texto)
        self.assertIn("falta el archivo", texto)
        self.assertIn("llaves.json", texto)

    def test_h3_8_fr323_fr314_costo_cero_codigo_1(self):
        with en_carpeta_temporal():
            codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*cripta_costo_cero()))
        self.assertEqual(codigo, 1, texto)
        self.assertIn("la verificación NO CONCLUYÓ", texto)
        self.assertIn("salida E de la sala 1", texto)
        self.assertIn("costo 0", texto)
        self.assertNotIn("RESOLUBLE", texto)
        self.assertNotIn("Orden", texto)

    def test_h3_9_fr314_forzar_no_cambia_verificar(self):
        casos = ((cripta_resoluble(), None, 0), (cripta_ciclo(), None, 3), (cripta_resoluble(), "presupuesto", 1))
        for datos, falla, esperado in casos:
            salidas = []
            for extra in ([], ["--forzar"]):
                with en_carpeta_temporal():
                    salidas.append(correr_main(["--verificar", ID, *extra], FuenteConLlaves(*datos, falla_llaves=falla)))
            self.assertEqual(salidas[0], salidas[1])
            self.assertEqual(salidas[0][0], esperado, salidas[0][1])

    def test_h2_7_fr321_fr314_verificar_sala_inexistente_codigo_1(self):
        with en_carpeta_temporal():
            codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*cripta_sala_inexistente()))
        self.assertEqual(codigo, 1, texto)
        self.assertIn("la verificación NO CONCLUYÓ", texto)
        self.assertIn("llave A", texto)
        self.assertIn("sala 99", texto)

    def test_fr323_fr314_cierre_automatico_invalido_codigo_1(self):
        with en_carpeta_temporal():
            codigo, texto = correr_main(["--verificar", ID], FuenteConLlaves(*cripta_cierre_invalido()))
        self.assertEqual(codigo, 1, texto)
        self.assertIn("la verificación NO CONCLUYÓ", texto)
        self.assertIn("salida E de la sala 2", texto)
        self.assertIn("cierre_automatico", texto)
        self.assertNotIn("RESOLUBLE", texto)


# ================================================================ T046: sin escenario propio
class PruebasVerificarSinEscenario(unittest.TestCase):

    def test_fr314_verificar_cripta_inexistente_codigo_1(self):
        for extra in ([], ["--forzar"]):
            with en_carpeta_temporal():
                codigo, texto = correr_main(["--verificar", "no-existe", *extra],
                                            FuenteConLlaves(*cripta_resoluble(), inexistente=True))
            self.assertEqual(codigo, 1, texto)
            self.assertIn("Cripta no-existe: la verificación NO CONCLUYÓ", texto)
            self.assertIn("404", texto)
            with en_carpeta_temporal() as carpeta:
                paquete_temporal(os.path.join(carpeta, "paquete"), *cripta_resoluble())
                codigo, texto = correr_main(["--verificar", "no-existe", "--offline", *extra])
            self.assertEqual(codigo, 1, texto)
            self.assertIn("Cripta no-existe: la verificación NO CONCLUYÓ", texto)
            self.assertIn("falta el archivo", texto)

    def test_fr312_forzar_con_replay_sin_efecto(self):
        log = str(RAIZ / "ejemplos" / "partida_ejemplo.log")
        with en_carpeta_temporal() as carpeta:
            shutil.copytree(str(RAIZ / "paquete"), os.path.join(carpeta, "paquete"))
            sin = correr_main(["--replay", log, "--offline"])
            con = correr_main(["--replay", log, "--offline", "--forzar"])
        self.assertEqual(sin[0], 0, sin[1])
        self.assertEqual(con, sin)

    def test_fr312_forzar_con_bench_sin_efecto(self):
        with en_carpeta_temporal(), mock.patch("UIController.ControladorBackend.ServicioBench", _BenchChico):
            sin = correr_main(["--bench"])
            con = correr_main(["--bench", "--forzar"])
        self.assertEqual(sin[0], 0, sin[1])
        self.assertIn("medición chica", sin[1])
        self.assertEqual(con, sin)

    def test_fr301_bench_no_llama_a_servicio_resolubilidad(self):
        from Service.ServicioResolubilidad import ServicioResolubilidad
        prohibido = AssertionError("--bench no verifica como paso previo a una partida")
        with en_carpeta_temporal(), mock.patch("UIController.ControladorBackend.ServicioBench", _BenchChico), \
                mock.patch.object(ServicioResolubilidad, "verificar", side_effect=prohibido), \
                mock.patch.object(ServicioResolubilidad, "iniciar_partida_nueva", side_effect=prohibido):
            for extra in ([], ["--forzar"]):
                codigo, texto = correr_main(["--bench", *extra])
                self.assertEqual(codigo, 0, texto)

    def test_sc308_verificar_sin_vista(self):
        with en_carpeta_temporal() as carpeta:
            paquete_temporal(os.path.join(carpeta, "paquete"), *cripta_resoluble())
            codigo, texto = en_otro_proceso(["-c", _SIN_VISTA, str(RAIZ), "--verificar", ID, "--offline"], carpeta)
            self.assertEqual(codigo, 0, texto)
            self.assertIn("MODULOS_DE_VISTA=\n", texto.replace("\r\n", "\n"))
            self.assertIn("RESOLUBLE", texto)
            self.assertFalse(os.path.exists(os.path.join(carpeta, "logs")))
            for _, _, nombres in os.walk(carpeta):
                self.assertEqual([n for n in nombres if n.endswith(".log")], [])

    def test_sc308_verificar_offline_sin_solicitudes_de_red(self):
        datos = cripta_ciclo()
        prohibido = AssertionError("--verificar --offline no debe hacer solicitudes de red")
        with en_carpeta_temporal() as carpeta:
            paquete_temporal(os.path.join(carpeta, "paquete"), *datos)
            with mock.patch("Service.ServicioPartida.FuenteRed", side_effect=prohibido), \
                    mock.patch.object(ClienteHttp, "get_json", side_effect=prohibido), \
                    mock.patch.object(socket.socket, "connect", side_effect=prohibido), \
                    mock.patch("socket.create_connection", side_effect=prohibido):
                codigo, texto = correr_main(["--verificar", ID, "--offline"])
        self.assertEqual(codigo, 3, texto)
        self.assertEqual(texto, texto_de(VerificadorResolubilidad.verificar(*datos)))

    def test_sc303_diez_ejecuciones_en_procesos_separados(self):
        codigos_esperados = {"resoluble": 0, "ciclo": 3, "h1_5": 0}
        for nombre, armar in CRIPTAS.items():
            datos = armar()
            esperado = texto_de(VerificadorResolubilidad.verificar(*datos))
            with en_carpeta_temporal() as carpeta:
                en_linea = [en_otro_proceso(["-c", _LANZADOR, str(CARPETA_TESTS), str(RAIZ), nombre,
                                             "--verificar", ID], carpeta) for _ in range(10)]
            with en_carpeta_temporal() as carpeta:
                paquete_temporal(os.path.join(carpeta, "paquete"), *datos)
                offline = [en_otro_proceso([str(RAIZ / "main.py"), "--verificar", ID, "--offline"], carpeta)
                           for _ in range(10)]
            for corridas in (en_linea, offline):
                for codigo, texto in corridas:
                    self.assertEqual(codigo, codigos_esperados[nombre], texto)
                    self.assertEqual(texto.replace("\r\n", "\n"), esperado, nombre)

    def test_fr314_verificar_utf8_sin_pythonioencoding(self):
        entorno = dict(os.environ)
        entorno.pop("PYTHONIOENCODING", None)
        entorno.pop("PYTHONUTF8", None)
        with en_carpeta_temporal() as carpeta:
            paquete_temporal(os.path.join(carpeta, "paquete"), *cripta_ciclo())
            codigo, texto = en_otro_proceso([str(RAIZ / "main.py"), "--verificar", ID, "--offline"], carpeta, entorno)
        self.assertEqual(codigo, 3, texto)
        self.assertIn("→", texto)
        self.assertNotIn("Traceback", texto)


# ================================================================ T053: el controlador al iniciar (historia 4)
class PruebasControlador(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def backend(self, datos, forzar=False) -> ControladorBackend:
        """Un ControladorBackend con servicios reales, la cripta servida por FuenteConLlaves y todo en la carpeta."""
        from Data.AlmacenPuntajes import AlmacenPuntajes
        from Service.ServicioPuntajes import ServicioPuntajes
        config = ConfiguracionDTO(forzar=forzar)
        partida = ServicioPartida(config, fuente=FuenteConLlaves(*datos),
                                  carpeta_cache=os.path.join(self.carpeta, "cache"),
                                  carpeta_logs=os.path.join(self.carpeta, "logs"), almacen_llaves=None)
        puntajes = ServicioPuntajes(AlmacenPuntajes(os.path.join(self.carpeta, "puntajes.jsonl")))
        return ControladorBackend(config, partida, puntajes, ServicioBench([]))

    def logs(self) -> list[str]:
        carpeta = os.path.join(self.carpeta, "logs")
        return os.listdir(carpeta) if os.path.isdir(carpeta) else []

    def test_fr311_controlador_no_inicia_y_guarda_el_reporte(self):
        datos = cripta_ciclo()
        backend = self.backend(datos)
        with self.assertRaises(ErrorOperacion) as atrapado:
            backend.iniciar(ID, "Ana")
        mensaje = str(atrapado.exception)
        self.assertIn("no es resoluble", mensaje)
        self.assertLess(len(mensaje), 200)                            # corto: el reporte va aparte
        self.assertEqual(backend.resolubilidad(), VerificadorResolubilidad.verificar(*datos))
        self.assertFalse(backend.hay_partida())
        self.assertEqual(self.logs(), [])

    def test_fr312_fr313_controlador_inicia_con_forzar(self):
        datos = cripta_ciclo()
        backend = self.backend(datos, forzar=True)
        estado = backend.iniciar(ID, "Ana")
        self.assertTrue(backend.hay_partida())
        self.assertEqual(estado.reloj, 0)
        self.assertEqual(backend.resolubilidad(), VerificadorResolubilidad.verificar(*datos))
        self.assertEqual(backend.resolubilidad().veredicto, NO_RESOLUBLE)

    def test_fr313_controlador_resoluble_muestra_el_orden(self):
        datos = cripta_resoluble()
        for forzar in (False, True):
            backend = self.backend(datos, forzar)
            self.assertIsNone(backend.resolubilidad())                # antes de iniciar no hay reporte
            backend.iniciar(ID, "Ana")
            reporte = backend.resolubilidad()
            self.assertEqual(reporte.veredicto, RESOLUBLE)
            self.assertEqual(reporte.orden_llaves, VerificadorResolubilidad.verificar(*datos).orden_llaves)

    def test_fr301_controlador_resolubilidad_none_al_cargar_y_en_replay(self):
        from Service.ServicioResolubilidad import ServicioResolubilidad
        datos = cripta_ciclo()
        original = self.backend(datos, forzar=True)
        original.iniciar(ID, "Ana")
        original.esperar()
        ruta_guardado = os.path.join(self.carpeta, "partida.sav")
        original.guardar(ruta_guardado)
        ruta_log = original._contexto.bitacora.ruta()                 # las pruebas pueden mirar adentro
        original.cargar(ruta_guardado, "Ana")                        # el mismo controlador: se olvida el reporte
        self.assertIsNone(original.resolubilidad())

        prohibido = AssertionError("cargar y --replay no pasan por ServicioResolubilidad")
        with mock.patch.object(ServicioResolubilidad, "verificar", side_effect=prohibido), \
                mock.patch.object(ServicioResolubilidad, "iniciar_partida_nueva", side_effect=prohibido):
            for forzar in (False, True):
                cargador = self.backend(datos, forzar)
                cargador.cargar(ruta_guardado, "Ana")
                self.assertIsNone(cargador.resolubilidad())
                reproductor = self.backend(datos, forzar)
                resultado = reproductor.reproducir(ruta_log)
                self.assertEqual(resultado.acciones_reproducidas, 1)
                self.assertIsNone(reproductor.resolubilidad())


if __name__ == "__main__":
    unittest.main()

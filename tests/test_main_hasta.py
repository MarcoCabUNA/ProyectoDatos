"""
Pruebas de main.py con --replay ... --hasta (feature 004, historia 2, T040): códigos de salida y salida impresa.

Se juega una partida (paquete offline), se guarda su log y se reproduce desde main.main con la salida capturada.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import main
import test_servicio_replay as replay_ayudas


@contextlib.contextmanager
def en_carpeta_temporal():
    anterior, carpeta = os.getcwd(), tempfile.mkdtemp()
    os.chdir(carpeta)
    shutil.copytree(RAIZ / "paquete", Path(carpeta) / "paquete")                   # --offline lo busca en el directorio de trabajo
    try:
        yield carpeta
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


def correr_main(argumentos):
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        codigo = main.main(argumentos)
    return codigo, salida.getvalue()


class PruebasMainHasta(unittest.TestCase):

    def test_h2_1_fr410_codigo_0(self):
        with en_carpeta_temporal() as carpeta:
            ruta, estados = replay_ayudas._jugar(os.path.join(carpeta, "origen"), 3, pasos=40)
            ultimo = estados[-1]
            codigo, texto = correr_main(["--offline", "--replay", ruta, "--hasta", "0"])
            self.assertEqual(codigo, 0, texto)
            self.assertIn("t=0", texto)                                           # el resumen del instante pedido
            codigo, texto = correr_main(["--offline", "--replay", ruta, "--hasta", str(ultimo.reloj + 500)])
            self.assertEqual(codigo, 0, texto)
            self.assertIn("terminó antes", texto)                                  # FR-412: lo dice con todas sus letras
            self.assertIn(f"t={ultimo.reloj}", texto)                              # y muestra el reloj del final

    def test_h2_3_fr410_codigo_2_hasta_invalido(self):
        for valor in ("abc", "-3", "2.5"):
            with self.subTest(valor=valor):
                codigo, texto = correr_main(["--offline", "--replay", "no_se_lee.log", "--hasta", valor])
                self.assertEqual(codigo, 2)
                self.assertIn("--hasta", texto)
        self.assertEqual(correr_main(["--replay", "no_se_lee.log", "--hasta"])[0], 2)

    def test_h2_3_fr410_codigo_2_hasta_sin_replay(self):
        codigo, texto = correr_main(["--offline", "--hasta", "5"])
        self.assertEqual(codigo, 2)
        self.assertIn("--replay", texto)

    def test_h2_4_fr410_codigo_1_archivo_inexistente(self):
        with en_carpeta_temporal() as carpeta:
            falso = os.path.join(carpeta, "no_existe.log")
            codigo, texto = correr_main(["--offline", "--replay", falso, "--hasta", "10"])
            self.assertEqual(codigo, 1)
            self.assertIn("no_existe.log", texto)                                  # error con contexto, sin caerse

    def test_h2_4_fr410_codigo_1_archivo_ilegible(self):
        with en_carpeta_temporal() as carpeta:
            roto = os.path.join(carpeta, "roto.log")
            with open(roto, "w", encoding="utf-8") as archivo:
                archivo.write("esto no es un log de Cripta\n")
            codigo, texto = correr_main(["--offline", "--replay", roto, "--hasta", "10"])
            self.assertEqual(codigo, 1)
            self.assertIn("roto.log", texto)

    def test_t_fuera_de_rango_es_error_de_operacion_codigo_1_fr409(self):
        """Un t posterior al reloj de una partida que NO terminó no tiene «final» que mostrar: error con el rango."""
        with en_carpeta_temporal() as carpeta:
            ruta, estados = replay_ayudas._jugar(os.path.join(carpeta, "origen"), 3, pasos=1)
            codigo, texto = correr_main(["--offline", "--replay", ruta, "--hasta", "100000"])
            if estados[-1].terminado:
                self.skipTest("la partida de la semilla 3 terminó en una sola acción")
            self.assertEqual(codigo, 1)
            self.assertIn("100000", texto)


if __name__ == "__main__":
    unittest.main()

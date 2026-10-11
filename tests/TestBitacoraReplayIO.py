"""
Pruebas de Data/BitacoraReplayIO.py y DTO/ReplayDTO.py (log de la partida para --replay, enunciado §4.11).
Todo se escribe en carpetas temporales.
"""
import dataclasses
import os
import shutil
import tempfile
import unittest

from Data.BitacoraReplayIO import BitacoraReplayIO, ErrorBitacora, comprobar_compatibilidad
from Data.FuenteOffline import FuenteOffline
from DTO.AccionDTO import AccionDTO
from DTO.ReplayDTO import EncabezadoReplayDTO, PartidaReplayDTO
from tests.Utilidades import ID_CRIPTA, PAQUETE

ENCABEZADO = EncabezadoReplayDTO("cripta-01", "fd58f7743b9e", "be68d322d2f5", 12345)

# Una acción de cada tipo, como las produce el Controlador.
ACCIONES = [
    AccionDTO("mover", direccion=0),
    AccionDTO("atacar", objetivo="e-201"),
    AccionDTO("esperar"),
    AccionDTO("abrir", direccion=3),
    AccionDTO("recoger", objeto="itm_daga_oxidada"),
    AccionDTO("soltar", objeto="itm_daga_oxidada"),
    AccionDTO("usar", objeto="itm_pocion"),
    AccionDTO("equipar", objeto="itm_espada"),
    AccionDTO("retroceder"),
]

TEXTO_ESPERADO = ("#CRIPTA-REPLAY 1\n"
                  "id_cripta=cripta-01\n"
                  "version_cripta=fd58f7743b9e\n"
                  "version_catalogo=be68d322d2f5\n"
                  "semilla=12345\n"
                  "#ACCIONES\n"
                  "mover|0||\n"
                  "atacar||e-201|\n")


class PruebasBitacoraReplayIO(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.temp, "partida.log")

    def tearDown(self):
        shutil.rmtree(self.temp)

    def escribir_a_mano(self, texto: str) -> str:
        with open(self.ruta, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        return self.ruta

    def contenido(self) -> str:
        with open(self.ruta, encoding="utf-8", newline="") as f:
            return f.read()

    def falla_al_leer(self, texto: str, *textos_esperados):
        self.escribir_a_mano(texto)
        with self.assertRaises(ErrorBitacora) as ctx:
            BitacoraReplayIO.leer(self.ruta)
        for esperado in textos_esperados:
            self.assertIn(esperado, str(ctx.exception))

    def nueva(self) -> BitacoraReplayIO:
        b = BitacoraReplayIO(self.ruta)
        b.iniciar(ENCABEZADO)
        return b

    # ------------------------------------------------------------ escribir y leer
    def test_ida_y_vuelta_con_todos_los_tipos(self):
        b = self.nueva()
        for accion in ACCIONES:
            b.anexar(accion)
        self.assertEqual(b.acciones_escritas(), len(ACCIONES))
        partida = BitacoraReplayIO.leer(self.ruta)
        self.assertEqual(partida, PartidaReplayDTO(ENCABEZADO, ACCIONES, ultima_linea_descartada=False))

    def test_formato_exacto_del_archivo(self):
        b = self.nueva()
        b.anexar(ACCIONES[0])
        b.anexar(ACCIONES[1])
        self.assertEqual(self.contenido(), TEXTO_ESPERADO)       # \n también en Windows (newline="")

    def test_sin_acciones(self):
        self.nueva()
        partida = BitacoraReplayIO.leer(self.ruta)
        self.assertEqual((partida.encabezado, partida.acciones), (ENCABEZADO, []))

    def test_solo_anexa(self):
        """Lo ya escrito nunca cambia: cada versión del archivo empieza con la anterior."""
        b = self.nueva()
        anterior = self.contenido()
        for accion in ACCIONES:
            b.anexar(accion)
            actual = self.contenido()
            self.assertTrue(actual.startswith(anterior))
            self.assertEqual(actual[len(anterior):], accion.a_linea() + "\n")
            anterior = actual

    def test_otra_instancia_lee_lo_escrito_sin_cerrar_nada(self):
        b = self.nueva()
        b.anexar(ACCIONES[0])
        self.assertEqual(BitacoraReplayIO.leer(self.ruta).acciones, [ACCIONES[0]])   # ya está en disco
        b.anexar(ACCIONES[1])
        self.assertEqual(BitacoraReplayIO.leer(self.ruta).acciones, ACCIONES[:2])

    def test_semilla_negativa_y_ids_con_tildes(self):
        encabezado = EncabezadoReplayDTO("cripta-ñ", "v=1", "catálogo", -7)
        b = BitacoraReplayIO(self.ruta)
        b.iniciar(encabezado)
        b.anexar(AccionDTO("recoger", objeto="poción"))
        partida = BitacoraReplayIO.leer(self.ruta)
        self.assertEqual((partida.encabezado, partida.acciones), (encabezado, [AccionDTO("recoger", objeto="poción")]))

    def test_crea_la_carpeta(self):
        self.ruta = os.path.join(self.temp, "logs", "2026", "p1.log")
        self.nueva()
        self.assertTrue(os.path.isfile(self.ruta))

    # ------------------------------------------------------------ errores al escribir
    def test_no_sobrescribe_un_log_existente(self):
        b = self.nueva()
        b.anexar(ACCIONES[0])
        antes = self.contenido()
        with self.assertRaises(ErrorBitacora):
            BitacoraReplayIO(self.ruta).iniciar(ENCABEZADO)
        with self.assertRaises(ErrorBitacora):
            b.iniciar(ENCABEZADO)                                 # la misma instancia tampoco
        self.assertEqual(self.contenido(), antes)

    def test_anexar_antes_de_iniciar(self):
        with self.assertRaises(ErrorBitacora):
            BitacoraReplayIO(self.ruta).anexar(ACCIONES[0])
        self.assertFalse(os.path.exists(self.ruta))

    def test_anexar_si_borraron_el_archivo(self):
        b = self.nueva()
        os.remove(self.ruta)
        with self.assertRaises(ErrorBitacora):
            b.anexar(ACCIONES[0])
        self.assertFalse(os.path.exists(self.ruta))               # no crea un log sin encabezado

    def test_no_escribe_acciones_que_se_leerian_distinto(self):
        b = self.nueva()
        antes = self.contenido()
        malas = [AccionDTO("recoger", objeto="a|b"),             # '|' de más
                 AccionDTO("atacar", objetivo=""),                # "" se leería como None
                 AccionDTO("recoger", objeto="a\nb"),             # partiría la línea
                 AccionDTO("recoger", objeto="itm "),             # desde_linea quitaría el espacio final
                 AccionDTO("mover", direccion=True)]              # se escribiría "True"
        for accion in malas:
            with self.assertRaises(ErrorBitacora, msg=repr(accion)):
                b.anexar(accion)
        with self.assertRaises(ErrorBitacora):
            b.anexar("mover|0||")                                 # type: ignore[arg-type]
        self.assertEqual((self.contenido(), b.acciones_escritas()), (antes, 0))

    def test_encabezado_invalido_no_crea_el_archivo(self):
        malos = [EncabezadoReplayDTO("", "v", "c", 1),
                 EncabezadoReplayDTO("c", "v\n", "c", 1),
                 EncabezadoReplayDTO("c", "v", " c", 1),
                 EncabezadoReplayDTO("c", "v", "c", True),
                 EncabezadoReplayDTO("c", "v", "c", "1"),          # type: ignore[arg-type]
                 EncabezadoReplayDTO("c", None, "c", 1)]           # type: ignore[arg-type]
        for encabezado in malos:
            with self.assertRaises(ErrorBitacora, msg=repr(encabezado)):
                BitacoraReplayIO(self.ruta).iniciar(encabezado)
            self.assertFalse(os.path.exists(self.ruta))

    # ------------------------------------------------------------ errores al leer
    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorBitacora) as ctx:
            BitacoraReplayIO.leer(os.path.join(self.temp, "no_existe.log"))
        self.assertIn("no_existe.log", str(ctx.exception))

    def test_no_es_un_log(self):
        self.falla_al_leer("", "no es un log")
        self.falla_al_leer("hola\nmundo\n", "no es un log")
        with open(self.ruta, "wb") as f:
            f.write(b"\xff\xfe\x00binario")
        with self.assertRaises(ErrorBitacora):
            BitacoraReplayIO.leer(self.ruta)

    def test_otra_version_del_formato(self):
        self.falla_al_leer(TEXTO_ESPERADO.replace("#CRIPTA-REPLAY 1", "#CRIPTA-REPLAY 2"), "'2'", "versión 1")

    def test_encabezado_mal_formado(self):
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345\n", ""), "semilla")                 # falta
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla=12a"), "semilla")        # no es entero
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla=+5"), "semilla")
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla="), "línea 5")           # vacío
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla=1\nsemilla=2"), "dos veces")
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla=1\njugador=ana"), "desconocida")
        self.falla_al_leer(TEXTO_ESPERADO.replace("semilla=12345", "semilla 12345"), "línea 5")
        self.falla_al_leer("#CRIPTA-REPLAY 1\nid_cripta=c\n", "incompleto")                          # sin #ACCIONES

    def test_accion_mal_formada_dice_la_linea(self):
        self.falla_al_leer(TEXTO_ESPERADO + "mover|0|\n", "línea 9")              # 3 campos
        self.falla_al_leer(TEXTO_ESPERADO + "mover|norte||\n", "línea 9")         # dirección no numérica
        self.falla_al_leer(TEXTO_ESPERADO + "\nesperar|||\n", "línea 9")          # línea vacía
        self.falla_al_leer(TEXTO_ESPERADO + "mover| 0||\n", "línea 9")            # no es lo que escribe a_linea
        self.falla_al_leer(TEXTO_ESPERADO + " esperar|||\n", "línea 9")

    def test_ultima_linea_a_medio_escribir_se_descarta(self):
        self.escribir_a_mano(TEXTO_ESPERADO + "atacar||e-20")                    # se cortó al escribir "e-201"
        partida = BitacoraReplayIO.leer(self.ruta)
        self.assertEqual(partida.acciones, ACCIONES[:2])
        self.assertTrue(partida.ultima_linea_descartada)

    def test_acepta_finales_de_linea_de_windows(self):
        self.escribir_a_mano(TEXTO_ESPERADO.replace("\n", "\r\n"))
        partida = BitacoraReplayIO.leer(self.ruta)
        self.assertEqual((partida.encabezado, partida.acciones), (ENCABEZADO, ACCIONES[:2]))
        self.assertFalse(partida.ultima_linea_descartada)

    def test_el_orden_de_las_claves_no_importa_y_el_valor_puede_tener_igual(self):
        self.escribir_a_mano("#CRIPTA-REPLAY 1\nsemilla=3\nversion_catalogo=c=1\nid_cripta=x\n"
                             "version_cripta=v\n#ACCIONES\n")
        self.assertEqual(BitacoraReplayIO.leer(self.ruta).encabezado, EncabezadoReplayDTO("x", "v", "c=1", 3))

    # ------------------------------------------------------------ compatibilidad de versiones
    def test_compatibilidad(self):
        self.assertEqual(comprobar_compatibilidad(ENCABEZADO, "fd58f7743b9e", "be68d322d2f5"), [])
        problemas = comprobar_compatibilidad(ENCABEZADO, "otra", "be68d322d2f5")
        self.assertEqual(len(problemas), 1)
        self.assertIn("fd58f7743b9e", problemas[0])
        self.assertIn("otra", problemas[0])
        self.assertEqual(len(comprobar_compatibilidad(ENCABEZADO, "fd58f7743b9e", "otro")), 1)
        self.assertEqual(len(comprobar_compatibilidad(ENCABEZADO, "otra", "otro")), 2)
        self.assertEqual(len(comprobar_compatibilidad(ENCABEZADO, None, None)), 2)    # ante la duda, no

    def test_compatible_con_el_paquete_real(self):
        """Lo que hará Servicios: el encabezado sale de la fuente y se compara contra ella misma."""
        fuente = FuenteOffline(PAQUETE)
        cripta = fuente.obtener_datos_generales(ID_CRIPTA)
        encabezado = EncabezadoReplayDTO(cripta.id, cripta.version, fuente.obtener_version_catalogo(), 99)
        b = BitacoraReplayIO(self.ruta)
        b.iniciar(encabezado)
        leido = BitacoraReplayIO.leer(self.ruta).encabezado
        self.assertEqual(leido, encabezado)
        self.assertEqual(comprobar_compatibilidad(leido, fuente.obtener_version_cripta(ID_CRIPTA),
                                                  fuente.obtener_version_catalogo()), [])

    # ------------------------------------------------------------ DTOs
    def test_dtos_inmutables(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(ENCABEZADO, "semilla", 1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(PartidaReplayDTO(ENCABEZADO, []), "acciones", ACCIONES)

    def test_es_un_valueerror(self):
        with self.assertRaises(ValueError):
            BitacoraReplayIO.leer(os.path.join(self.temp, "nada.log"))


if __name__ == "__main__":
    unittest.main()
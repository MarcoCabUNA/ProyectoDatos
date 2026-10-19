"""
Pruebas de Data/GuardadoBinario.py (guardado binario de la partida, enunciado §4.10).
Todo se escribe en carpetas temporales.
"""
import dataclasses
import json
import os
import shutil
import struct
import tempfile
import unittest

from Data import GuardadoBinario
from Data.GuardadoBinario import (ErrorGuardado, cargar, cargar_sala, cargar_salas, comprobar_compatibilidad,
                                  guardar, ids_salas)
from DTO.PartidaGuardadaDTO import (EnemigoGuardadoDTO, JugadorGuardadoDTO, SalaGuardadaDTO,
                                    TrampaGuardadaDTO)
from tests.TestPartidaGuardadaDTO import partida_de_ejemplo, sala_de_ejemplo

TAMANO_CABECERA = 34
TAMANO_ENTRADA = 12


def salas_de_ejemplo(n: int = 20) -> list[SalaGuardadaDTO]:
    """Salas 1..n variadas: con y sin contenido, puertas cerradas, objetos, trampas y enemigos."""
    salas = []
    for i in range(1, n + 1):
        con_contenido = i % 3 != 0
        salas.append(SalaGuardadaDTO(
            i, con_contenido, [i % 2 == 0, i % 5 == 0, False, i % 7 == 0],
            ["itm_pocion", "itm_daga"][: i % 3] if con_contenido else [],
            [TrampaGuardadaDTO(f"t-{i}", "trp_pinchos", i % 2 == 0)] if i % 4 == 0 else [],
            [EnemigoGuardadoDTO(f"e-{i}{k}", "ene_rata", 3 + k, 100, k + 1, k == 0) for k in range(i % 3)]))
    salas.append(SalaGuardadaDTO(n + 1, False, [True, True, True, True], [], [],
                                 [EnemigoGuardadoDTO("e-errante", "ene_lobo", 9, 120, 1, True)]))  # llegó un errante
    return salas


class PruebasGuardadoBinario(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.temp, "partida.sav")
        self.partida = partida_de_ejemplo()
        self.salas = salas_de_ejemplo()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def bytes_del_archivo(self) -> bytearray:
        with open(self.ruta, "rb") as f:
            return bytearray(f.read())

    def escribir_bytes(self, datos) -> None:
        with open(self.ruta, "wb") as f:
            f.write(bytes(datos))

    def falla_al_cargar(self, *textos):
        for funcion in (lambda: cargar(self.ruta), lambda: cargar_sala(self.ruta, 1),
                        lambda: cargar_salas(self.ruta), lambda: ids_salas(self.ruta)):
            with self.assertRaises(ErrorGuardado) as ctx:
                funcion()
            for texto in textos:
                self.assertIn(texto, str(ctx.exception))

    # ------------------------------------------------------------ ida y vuelta
    def test_ida_y_vuelta_completa(self):
        bytes_escritos = guardar(self.ruta, self.partida, self.salas)
        self.assertEqual(bytes_escritos, os.path.getsize(self.ruta))
        self.assertEqual(cargar(self.ruta), self.partida)
        self.assertEqual(cargar_salas(self.ruta), self.salas)
        for sala in self.salas:
            self.assertEqual(cargar_sala(self.ruta, sala.id), sala)
        self.assertEqual(ids_salas(self.ruta), [s.id for s in self.salas])

    def test_sala_de_ejemplo_y_textos_con_tildes(self):
        partida = dataclasses.replace(self.partida, ruta_log="partidas/señor_ñandú.log", id_cripta="cripta-ñ")
        sala = dataclasses.replace(sala_de_ejemplo(), objetos=["poción", "itm_daga"])
        guardar(self.ruta, partida, [sala])
        self.assertEqual((cargar(self.ruta), cargar_sala(self.ruta, sala.id)), (partida, sala))

    def test_las_salas_pueden_venir_en_cualquier_orden(self):
        desordenadas = [self.salas[i] for i in (5, 0, 20, 3, 1, 2, 4)] + self.salas[6:20]
        guardar(self.ruta, self.partida, desordenadas)
        self.assertEqual(ids_salas(self.ruta), [s.id for s in self.salas])        # salen por id, sin ordenar
        self.assertEqual(cargar_salas(self.ruta), self.salas)

    def test_ids_con_huecos_y_que_no_empiezan_en_1(self):
        salas = [SalaGuardadaDTO(i, True) for i in (7, 8, 12)]
        guardar(self.ruta, self.partida, salas)
        self.assertEqual(ids_salas(self.ruta), [7, 8, 12])
        for no_esta in (0, 6, 9, 11, 13, 1000, -1):
            self.assertIsNone(cargar_sala(self.ruta, no_esta))
        self.assertEqual(cargar_sala(self.ruta, 12), salas[2])

    def test_sin_salas(self):
        guardar(self.ruta, self.partida, [])
        self.assertEqual((ids_salas(self.ruta), cargar_salas(self.ruta)), ([], []))
        self.assertIsNone(cargar_sala(self.ruta, 1))
        self.assertEqual(cargar(self.ruta), self.partida)

    def test_valores_limite(self):
        partida = dataclasses.replace(
            self.partida, semilla=-(2 ** 63), reloj=2 ** 31 - 1, azar_gauss=-0.12345678901234567,
            rastro=[], efectos=[], eventos=[], contadores_tipo=[], ruta_log=None,
            jugador=JugadorGuardadoDTO(0, 1, 0, 0, 1, 0, 0))
        sala = SalaGuardadaDTO(0, False, [True, False, True, True])
        guardar(self.ruta, partida, [sala])
        self.assertEqual((cargar(self.ruta), cargar_salas(self.ruta)), (partida, [sala]))

    # ------------------------------------------------------------ una sola sala
    def test_cargar_una_sala_no_lee_el_resto_del_archivo(self):
        """Se dañan el bloque global y todos los bloques menos uno: esa sala se sigue leyendo bien."""
        guardar(self.ruta, self.partida, self.salas)
        datos = self.bytes_del_archivo()
        offset_indice = struct.unpack_from("<Q", datos, 18)[0]
        objetivo = 9
        offset, largo = struct.unpack_from("<QI", datos, offset_indice + (objetivo - 1) * TAMANO_ENTRADA)
        for i in range(TAMANO_CABECERA, offset_indice):
            if not offset <= i < offset + largo:
                datos[i] = 0xFF
        self.escribir_bytes(datos)
        self.assertEqual(cargar_sala(self.ruta, objetivo), self.salas[objetivo - 1])
        with self.assertRaises(ErrorGuardado):
            cargar(self.ruta)                       # el bloque global sí quedó dañado
        with self.assertRaises(ErrorGuardado):
            cargar_sala(self.ruta, objetivo + 1)

    def test_la_entrada_se_calcula_sin_buscar(self):
        """La entrada de la sala id está en offset_indice + (id - id_minimo) * 12."""
        salas = [SalaGuardadaDTO(i, True) for i in range(5, 15)]
        guardar(self.ruta, self.partida, salas)
        datos = self.bytes_del_archivo()
        _, version, _, _, offset_indice, entradas, id_minimo = struct.unpack_from("<4sHQIQII", datos, 0)
        self.assertEqual((version, entradas, id_minimo), (1, 10, 5))
        self.assertEqual(offset_indice + entradas * TAMANO_ENTRADA, len(datos))      # el índice va al final
        offset, largo = struct.unpack_from("<QI", datos, offset_indice + (11 - 5) * TAMANO_ENTRADA)
        self.assertEqual(struct.unpack_from("<i", datos, offset)[0], 11)          # el bloque empieza con su id

    # ------------------------------------------------------------ errores al guardar
    def test_ids_repetidos_o_invalidos(self):
        for salas in ([SalaGuardadaDTO(1, True), SalaGuardadaDTO(1, False)],
                      [SalaGuardadaDTO(-1, True)],
                      [SalaGuardadaDTO(True, True)],                                       # type: ignore[arg-type]
                      [SalaGuardadaDTO(1, True), SalaGuardadaDTO(5_000_000, True)]):      # índice gigante
            with self.assertRaises(ErrorGuardado, msg=repr([s.id for s in salas])):
                guardar(self.ruta, self.partida, salas)
            self.assertFalse(os.path.exists(self.ruta))

    def test_datos_que_no_se_pueden_guardar(self):
        malos = [dataclasses.replace(self.partida, reloj=2 ** 31),                 # no cabe en 4 bytes
                 dataclasses.replace(self.partida, id_cripta=None),                  # type: ignore[arg-type]
                 dataclasses.replace(self.partida, azar_estado=[2 ** 32] + self.partida.azar_estado[1:]),
                 dataclasses.replace(self.partida, ruta_log="x" * 70_000)]           # texto de más de 65535 bytes
        for partida in malos:
            with self.assertRaises(ErrorGuardado):
                guardar(self.ruta, partida, self.salas)
        with self.assertRaises(ErrorGuardado):
            guardar(self.ruta, self.partida, [SalaGuardadaDTO(1, True, [False, False, False])])   # 3 puertas
        with self.assertRaises(ErrorGuardado):
            guardar(self.ruta, "partida", self.salas)                                # type: ignore[arg-type]
        with self.assertRaises(ErrorGuardado):
            guardar(self.ruta, self.partida, [sala_de_ejemplo().a_diccionario()])   # type: ignore[list-item]
        self.assertFalse(os.path.exists(self.ruta))

    def test_un_guardado_fallido_no_dana_el_anterior(self):
        guardar(self.ruta, self.partida, self.salas)
        antes = self.bytes_del_archivo()
        with self.assertRaises(ErrorGuardado):
            guardar(self.ruta, dataclasses.replace(self.partida, reloj=2 ** 40), self.salas)
        self.assertEqual(self.bytes_del_archivo(), antes)
        self.assertEqual(os.listdir(self.temp), ["partida.sav"])                   # no queda el .tmp

    def test_sobrescribe_y_crea_la_carpeta(self):
        self.ruta = os.path.join(self.temp, "saves", "lenta", "p.sav")
        guardar(self.ruta, self.partida, self.salas)
        otra = dataclasses.replace(self.partida, reloj=999)
        guardar(self.ruta, otra, self.salas[:3])
        self.assertEqual((cargar(self.ruta), ids_salas(self.ruta)), (otra, [1, 2, 3]))

    # ------------------------------------------------------------ errores al cargar
    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorGuardado) as ctx:
            cargar(os.path.join(self.temp, "no_existe.sav"))
        self.assertIn("no_existe.sav", str(ctx.exception))

    def test_no_es_una_partida(self):
        self.escribir_bytes(b"")
        self.falla_al_cargar("no es una partida")
        self.escribir_bytes(b'{"partida": {}}')
        self.falla_al_cargar("no es una partida")

    def test_otra_version_del_formato(self):
        guardar(self.ruta, self.partida, self.salas)
        datos = self.bytes_del_archivo()
        struct.pack_into("<H", datos, 4, 2)
        self.escribir_bytes(datos[:40])          # aunque el resto esté cortado, primero se avisa la versión
        self.falla_al_cargar("versión 2", "versión 1")

    def test_archivo_cortado(self):
        guardar(self.ruta, self.partida, self.salas)
        datos = self.bytes_del_archivo()
        for largo in (8, TAMANO_CABECERA - 1, TAMANO_CABECERA + 10, len(datos) - 1):
            self.escribir_bytes(datos[:largo])
            self.falla_al_cargar()

    def test_bytes_de_mas_al_final(self):
        guardar(self.ruta, self.partida, self.salas)
        self.escribir_bytes(self.bytes_del_archivo() + b"\x00")
        self.falla_al_cargar("dañado")

    def test_bloque_danado(self):
        guardar(self.ruta, self.partida, self.salas)
        datos = self.bytes_del_archivo()
        offset_indice = struct.unpack_from("<Q", datos, 18)[0]
        offset, largo = struct.unpack_from("<QI", datos, offset_indice)        # sala 1
        struct.pack_into("<i", datos, offset, 2)                                # dice ser la sala 2
        self.escribir_bytes(datos)
        with self.assertRaises(ErrorGuardado):
            cargar_sala(self.ruta, 1)
        struct.pack_into("<i", datos, offset, 1)
        struct.pack_into("<B", datos, offset + 5, 0xF0)                         # bits de puertas imposibles
        self.escribir_bytes(datos)
        with self.assertRaises(ErrorGuardado):
            cargar_sala(self.ruta, 1)
        self.assertEqual(cargar_sala(self.ruta, 2), self.salas[1])             # las demás siguen bien

    def test_id_de_sala_invalido(self):
        guardar(self.ruta, self.partida, self.salas)
        for malo in ("1", 1.0, True, None):
            with self.assertRaises(ErrorGuardado):
                cargar_sala(self.ruta, malo)                                    # type: ignore[arg-type]

    # ------------------------------------------------------------ versiones y JSON
    def test_compatibilidad(self):
        p = self.partida
        self.assertEqual(comprobar_compatibilidad(p, p.version_cripta, p.version_catalogo), [])
        self.assertEqual(len(comprobar_compatibilidad(p, "otra", p.version_catalogo)), 1)
        self.assertEqual(len(comprobar_compatibilidad(p, p.version_cripta, "otro")), 1)
        self.assertEqual(len(comprobar_compatibilidad(p, None, None)), 2)

    def test_mas_pequeno_que_el_mismo_estado_en_json(self):
        bytes_binario = guardar(self.ruta, self.partida, self.salas)
        texto = json.dumps({"partida": self.partida.a_diccionario(),
                            "salas": [s.a_diccionario() for s in self.salas]}, separators=(",", ":"))
        self.assertLess(bytes_binario, len(texto.encode("utf-8")))

    def test_es_un_valueerror(self):
        with self.assertRaises(ValueError):
            cargar(os.path.join(self.temp, "nada.sav"))

    def test_constantes_del_formato(self):
        self.assertEqual((GuardadoBinario.MAGIA, GuardadoBinario.VERSION_FORMATO), (b"CRPT", 1))


if __name__ == "__main__":
    unittest.main()
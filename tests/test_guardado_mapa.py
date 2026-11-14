"""
Pruebas del guardado del mapa conocido (feature 002, integrante 2).

- DTO/MapaConocidoDTO.py: constantes, DTO de la vista y DTO guardado (T009).
- DTO/PartidaGuardadaDTO.py: campos `mapa` y `linea` al final, en ese orden (T035, primeras cuatro; T002 de la 004).
- Data/GuardadoBinario.py versión 2: cabecera de 58 bytes, bloque del mapa y bloque de la línea (T038; también son
  las pruebas de T003 y T047 de la 004).
"""
import dataclasses
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.FichaTrampaDTO import FichaTrampaDTO  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.PartidaGuardadaDTO import PartidaGuardadaDTO  # noqa: E402
from tests.ayudas_terreno import ficha_cazador, salida, salidas_con_costos  # noqa: E402
from tests.TestPartidaGuardadaDTO import partida_de_ejemplo, sala_de_ejemplo  # noqa: E402


def mapa_guardado_de_ejemplo(salas: int = 7, variante: int = 0):
    """Un MapaConocidoGuardadoDTO con los tres estados de sala y los tres de cara (S = salas)."""
    from DTO.MapaConocidoDTO import MapaConocidoGuardadoDTO
    estado = [(i + variante) % 3 for i in range(salas)]
    caras = [(i * 7 + variante) % 3 for i in range(4 * salas)]
    return MapaConocidoGuardadoDTO(estado, caras)


def linea_de_ejemplo(k: int = 3, con_mapa: bool = True):
    """
    Una LineaTiempoGuardadaDTO chica que cumple las restricciones del §1 del contrato de la 004: seis acciones,
    puntos en 0, 3 y 6 (cada uno con su mapa si con_mapa), dos cargas y una ficha de cada clase.
    """
    from DTO.LineaTiempoDTO import (AccionGuardadaDTO, LineaTiempoGuardadaDTO, PuntoControlGuardadoDTO,
                                    RegistroCargaGuardadoDTO)
    acciones = [AccionGuardadaDTO(100, "mover", direccion=2), AccionGuardadaDTO(200, "atacar", objetivo="e-201"),
                AccionGuardadaDTO(300, "recoger", objeto="itm_pocion"), AccionGuardadaDTO(400, "esperar"),
                AccionGuardadaDTO(500, "usar", objeto="itm_antorcha"), AccionGuardadaDTO(600, "esperar")]
    puntos = []
    for i, hechas in enumerate([0, 3, 6]):
        mapa = mapa_guardado_de_ejemplo(7, i) if con_mapa else None
        puntos.append(PuntoControlGuardadoDTO(hechas, dataclasses.replace(partida_de_ejemplo(), mapa=mapa),
                                              [sala_de_ejemplo()]))
    salas = salidas_con_costos(2, [salida(1, 2, 2, 100)])
    cargas = [RegistroCargaGuardadoDTO(0, salas[0]), RegistroCargaGuardadoDTO(2, salas[1])]
    fichas = [ficha_cazador(3),
              FichaTrampaDTO.desde_diccionario({"id": "trp_pinchos", "clase": "trampa", "nombre": "Pinchos",
                                                "daño": 4, "rearme": 300}),
              ObjetoDTO.desde_diccionario({"id": "itm_pocion", "clase": "pocion", "nombre": "Poción",
                                           "peso": 1, "valor": 5, "cura": 10})]
    return LineaTiempoGuardadaDTO(k, acciones, puntos, cargas, fichas)


class PruebasMapaConocidoDTO(unittest.TestCase):
    """T009: constantes y DTO de DTO/MapaConocidoDTO.py."""

    def test_fr201_fr208_constantes_del_mapa(self):
        from DTO import MapaConocidoDTO as m
        self.assertEqual((m.DESCONOCIDA, m.AVISTADA, m.EXPLORADA), (0, 1, 2))
        self.assertEqual((m.SIN_OBSERVAR, m.ABIERTA, m.CERRADA), (0, 1, 2))

    def test_fr219_dto_de_vista_inmutables_y_orden_de_campos(self):
        from DTO.MapaConocidoDTO import (MapaConocidoDTO, MapaConocidoGuardadoDTO, SalaConocidaDTO,
                                         SalidaConocidaDTO)
        esperados = [(MapaConocidoDTO, ["salas"]),
                     (SalaConocidaDTO, ["id", "nombre", "salidas"]),
                     (SalidaConocidaDTO, ["costo", "estado_puerta", "destino"]),
                     (MapaConocidoGuardadoDTO, ["estado_salas", "caras"])]
        for clase, campos in esperados:
            with self.subTest(clase=clase.__name__):
                self.assertEqual([c.name for c in dataclasses.fields(clase)], campos)
                self.assertTrue(clase.__dataclass_params__.frozen)
        salida = SalidaConocidaDTO(100, 1, None)
        sala = SalaConocidaDTO(1, "Sala 1", [salida, None, None, None])
        mapa = MapaConocidoDTO([sala])
        guardado = MapaConocidoGuardadoDTO([0, 2], [0] * 8)
        for dto, campo in [(salida, "costo"), (sala, "nombre"), (mapa, "salas"), (guardado, "caras")]:
            with self.subTest(dto=type(dto).__name__):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(dto, campo, None)

    def test_fr221_guardado_a_diccionario_y_vuelta(self):
        from DTO.MapaConocidoDTO import MapaConocidoGuardadoDTO
        dto = MapaConocidoGuardadoDTO([0, 2, 1, 0], [0, 0, 0, 0, 1, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
        d = dto.a_diccionario()
        self.assertEqual(d, {"estado_salas": [0, 2, 1, 0],
                             "caras": [0, 0, 0, 0, 1, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]})
        self.assertEqual(MapaConocidoGuardadoDTO.desde_diccionario(d), dto)
        d["estado_salas"].append(9)                 # a_diccionario también entrega copias
        self.assertEqual(dto.estado_salas, [0, 2, 1, 0])

    def test_fr221_desde_diccionario_copia_las_listas(self):
        from DTO.MapaConocidoDTO import MapaConocidoGuardadoDTO
        d = {"estado_salas": [0, 2], "caras": [0, 1, 0, 0, 0, 0, 0, 0]}
        dto = MapaConocidoGuardadoDTO.desde_diccionario(d)
        d["estado_salas"][1] = 1
        d["caras"].append(2)
        self.assertEqual(dto.estado_salas, [0, 2])
        self.assertEqual(dto.caras, [0, 1, 0, 0, 0, 0, 0, 0])


class PruebasPartidaGuardadaConMapaYLinea(unittest.TestCase):
    """T035 (primeras cuatro): PartidaGuardadaDTO con `mapa` y `linea` (T002 de la 004)."""

    def test_fr221_partida_guardada_mapa_antes_de_linea(self):
        campos = [c.name for c in dataclasses.fields(PartidaGuardadaDTO)]
        self.assertEqual(campos[-2:], ["mapa", "linea"])
        self.assertEqual(campos[:-2], ["id_cripta", "version_cripta", "version_catalogo", "semilla", "reloj",
                                       "siguiente_secuencia", "enemigos_derrotados", "terminado", "victoria",
                                       "salida_abierta", "azar_version", "azar_estado", "azar_gauss", "jugador",
                                       "inventario", "rastro", "contadores_tipo", "efectos", "eventos",
                                       "ruta_log", "acciones_en_log"])     # los demás no cambian de orden
        partida = partida_de_ejemplo()                 # se arma sin nombrar los campos nuevos
        self.assertIsNone(partida.mapa)
        self.assertIsNone(partida.linea)

    def test_fr221_partida_guardada_a_diccionario_y_vuelta_con_mapa(self):
        con_mapa = dataclasses.replace(partida_de_ejemplo(), mapa=mapa_guardado_de_ejemplo())
        sin_mapa = partida_de_ejemplo()
        for partida in (con_mapa, sin_mapa):
            with self.subTest(mapa=partida.mapa is not None):
                d = json.loads(json.dumps(partida.a_diccionario()))       # como si pasara por disco
                self.assertEqual(PartidaGuardadaDTO.desde_diccionario(d), partida)
        self.assertEqual(con_mapa.a_diccionario()["mapa"], con_mapa.mapa.a_diccionario())
        self.assertIsNone(sin_mapa.a_diccionario()["mapa"])
        d = sin_mapa.a_diccionario()
        del d["mapa"]                                  # un diccionario sin la clave "mapa" da None
        self.assertIsNone(PartidaGuardadaDTO.desde_diccionario(d).mapa)

    def test_t002_de_la_004_linea_ida_y_vuelta_por_diccionario(self):
        con_linea = dataclasses.replace(partida_de_ejemplo(), mapa=mapa_guardado_de_ejemplo(),
                                        linea=linea_de_ejemplo())
        sin_linea = partida_de_ejemplo()
        for partida in (con_linea, sin_linea):
            with self.subTest(linea=partida.linea is not None):
                d = json.loads(json.dumps(partida.a_diccionario()))
                self.assertEqual(PartidaGuardadaDTO.desde_diccionario(d), partida)
        self.assertIsNone(sin_linea.a_diccionario()["linea"])
        d = sin_linea.a_diccionario()
        del d["linea"]                                 # un diccionario sin la clave "linea" da None
        self.assertIsNone(PartidaGuardadaDTO.desde_diccionario(d).linea)

    def test_t002_de_la_004_sin_ciclo_de_imports(self):
        for modulo in ("DTO.PartidaGuardadaDTO", "DTO.LineaTiempoDTO"):
            with self.subTest(modulo=modulo):
                proceso = subprocess.run([sys.executable, "-B", "-c", f"import {modulo}"], cwd=RAIZ,
                                         capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.assertEqual(proceso.returncode, 0, proceso.stderr)
        # además, desde_diccionario (que importa LineaTiempoGuardadaDTO adentro) funciona en un proceso nuevo
        codigo = ("from DTO.PartidaGuardadaDTO import PartidaGuardadaDTO\n"
                  "from tests.test_guardado_mapa import linea_de_ejemplo, partida_de_ejemplo\n"
                  "import dataclasses\n"
                  "p = dataclasses.replace(partida_de_ejemplo(), linea=linea_de_ejemplo())\n"
                  "assert PartidaGuardadaDTO.desde_diccionario(p.a_diccionario()) == p\n")
        proceso = subprocess.run([sys.executable, "-B", "-c", codigo], cwd=RAIZ,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(proceso.returncode, 0, proceso.stderr)


# Cabecera de la versión 2 (data-model §6): magia, versión, offset y largo global, offset del índice, entradas,
# id mínimo, offset y largo del mapa, offset y largo de la línea.
CABECERA_V2 = struct.Struct("<4sHQIQIIQIQI")
CABECERA_V1 = struct.Struct("<4sHQIQII")
POS_MAPA = 34           # posición del offset del mapa dentro de la cabecera (después de los 7 campos de la v1)
POS_LINEA = 46          # posición del offset de la línea


class PruebasBinarioVersion2(unittest.TestCase):
    """T038: GuardadoBinario versión 2 (T003 y T047 de la 004)."""

    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.temp, "partida.sav")
        self.salas = [sala_de_ejemplo(), dataclasses.replace(sala_de_ejemplo(), id=4, objetos=["itm_daga"])]

    def tearDown(self):
        shutil.rmtree(self.temp)

    def bytes_del_archivo(self) -> bytearray:
        with open(self.ruta, "rb") as f:
            return bytearray(f.read())

    def escribir_bytes(self, datos) -> None:
        with open(self.ruta, "wb") as f:
            f.write(bytes(datos))

    def cabecera(self) -> tuple:
        return CABECERA_V2.unpack_from(self.bytes_del_archivo(), 0)

    def partida(self, mapa=None, linea=None) -> PartidaGuardadaDTO:
        return dataclasses.replace(partida_de_ejemplo(), mapa=mapa, linea=linea)

    # ------------------------------------------------------------ ida y vuelta
    def test_fr221_binario_v2_ida_y_vuelta_con_mapa(self):
        from Data.GuardadoBinario import cargar, cargar_sala, cargar_salas, guardar
        from DTO.MapaConocidoDTO import MapaConocidoGuardadoDTO
        for mapa in (mapa_guardado_de_ejemplo(7), mapa_guardado_de_ejemplo(1, 2), MapaConocidoGuardadoDTO([], []),
                     MapaConocidoGuardadoDTO([2] * 300, [1, 2, 0, 1] * 300)):
            with self.subTest(salas=len(mapa.estado_salas)):
                partida = self.partida(mapa=mapa)
                bytes_escritos = guardar(self.ruta, partida, self.salas)
                self.assertEqual(bytes_escritos, os.path.getsize(self.ruta))
                self.assertEqual(cargar(self.ruta), partida)
                self.assertEqual(cargar_salas(self.ruta), self.salas)
                self.assertEqual(cargar_sala(self.ruta, 4), self.salas[1])
                largo_mapa = self.cabecera()[8]
                self.assertEqual(largo_mapa, 4 + 2 * len(mapa.estado_salas))     # I cantidad · S + S bytes

    def test_fr221_binario_v2_mapa_none_largo_cero(self):
        from Data.GuardadoBinario import cargar, guardar
        partida = self.partida()
        guardar(self.ruta, partida, self.salas)
        self.assertEqual(self.cabecera()[8], 0)
        self.assertIsNone(cargar(self.ruta).mapa)
        self.assertEqual(cargar(self.ruta), partida)

    def test_t003_de_la_004_binario_v2_ida_y_vuelta_con_linea(self):
        from Data.GuardadoBinario import cargar, cargar_salas, guardar
        for con_mapa in (True, False):
            with self.subTest(puntos_con_mapa=con_mapa):
                linea = linea_de_ejemplo(con_mapa=con_mapa)
                partida = self.partida(mapa=mapa_guardado_de_ejemplo(), linea=linea)
                guardar(self.ruta, partida, self.salas)
                cargada = cargar(self.ruta)
                self.assertEqual(cargada, partida)
                self.assertEqual(cargada.linea, linea)
                for punto in cargada.linea.puntos:                      # cada punto con su mapa (o sin él)
                    self.assertIsNone(punto.partida.linea)
                    self.assertEqual(punto.partida.mapa is not None, con_mapa)
                self.assertEqual(cargar_salas(self.ruta), self.salas)
                self.assertGreater(self.cabecera()[10], 0)
        vacia = self.partida(linea=dataclasses.replace(linea_de_ejemplo(), acciones=[], puntos=[], cargas=[],
                                                       fichas=[]))
        guardar(self.ruta, vacia, self.salas)                           # una línea sin nada también viaja
        self.assertEqual(cargar(self.ruta), vacia)

    def test_t003_de_la_004_binario_v2_linea_none_largo_cero(self):
        from Data.GuardadoBinario import cargar, guardar
        partida = self.partida(mapa=mapa_guardado_de_ejemplo())
        guardar(self.ruta, partida, self.salas)
        self.assertEqual(self.cabecera()[10], 0)
        self.assertIsNone(cargar(self.ruta).linea)
        self.assertEqual(cargar(self.ruta), partida)

    # ------------------------------------------------------------ una sola sala
    def test_t047_de_la_004_cargar_sala_no_lee_mapa_ni_linea(self):
        from Data.GuardadoBinario import ErrorGuardado, cargar, cargar_sala, guardar
        guardar(self.ruta, self.partida(mapa=mapa_guardado_de_ejemplo(), linea=linea_de_ejemplo()), self.salas)
        datos = self.bytes_del_archivo()
        cabecera = CABECERA_V2.unpack_from(datos, 0)
        offset_mapa, largo_mapa, offset_linea, largo_linea = cabecera[7:11]
        self.assertGreater(largo_mapa, 0)
        self.assertGreater(largo_linea, 0)
        for i in range(offset_mapa, offset_mapa + largo_mapa):          # bytes inválidos en los dos bloques
            datos[i] = 0xFF
        for i in range(offset_linea, offset_linea + largo_linea):
            datos[i] = 0xFF
        self.escribir_bytes(datos)
        self.assertEqual(cargar_sala(self.ruta, 4), self.salas[1])
        self.assertEqual(cargar_sala(self.ruta, self.salas[0].id), self.salas[0])
        with self.assertRaises(ErrorGuardado):
            cargar(self.ruta)                                           # cargar sí los lee

    # ------------------------------------------------------------ versión 1
    def archivo_v1(self) -> None:
        """Un archivo con el formato de la versión 1: cabecera de 34 bytes, bloque global, salas e índice."""
        from Data import GuardadoBinario
        global_ = GuardadoBinario._codificar_partida(partida_de_ejemplo())
        bloques = [GuardadoBinario._codificar_sala(s) for s in self.salas]
        ids = [s.id for s in self.salas]
        id_minimo, id_maximo = ids[0], ids[0]
        for i in ids:
            id_minimo, id_maximo = min(id_minimo, i), max(id_maximo, i)
        entradas = [(0, 0)] * (id_maximo - id_minimo + 1)
        posicion = CABECERA_V1.size + len(global_)
        for sala, bloque in zip(self.salas, bloques):
            entradas[sala.id - id_minimo] = (posicion, len(bloque))
            posicion += len(bloque)
        partes = [CABECERA_V1.pack(b"CRPT", 1, CABECERA_V1.size, len(global_), posicion, len(entradas), id_minimo),
                  global_] + bloques + [struct.pack("<QI", o, l) for o, l in entradas]
        self.escribir_bytes(b"".join(partes))

    def test_t047_de_la_004_archivo_v1_rechazado(self):
        from Data.GuardadoBinario import ErrorGuardado, cargar, cargar_sala, cargar_salas, ids_salas
        self.archivo_v1()
        for nombre, funcion in (("cargar", lambda: cargar(self.ruta)),
                                ("cargar_sala", lambda: cargar_sala(self.ruta, 4)),
                                ("cargar_salas", lambda: cargar_salas(self.ruta)),
                                ("ids_salas", lambda: ids_salas(self.ruta))):
            with self.subTest(funcion=nombre):
                with self.assertRaises(ErrorGuardado) as ctx:
                    funcion()
                self.assertIn("versión 1", str(ctx.exception))         # la leída
                self.assertIn("versión 2", str(ctx.exception))         # la esperada

    def test_t047_de_la_004_archivo_v1_deja_intacta_la_partida_actual(self):
        carpeta_tests = os.path.join(RAIZ, "tests")
        if carpeta_tests not in sys.path:
            sys.path.insert(0, carpeta_tests)
        from test_servicios import _crear, _elegir_accion
        from Data.GuardadoBinario import ErrorGuardado
        from Logic.PartidaGuardada import PartidaGuardada
        from Service.ServicioGuardado import ServicioGuardado
        from tests.ayudas_mapa import estados

        servicio, acciones, ctx = _crear(os.path.join(self.temp, "a"), semilla=5, reforzar=True)
        estado = servicio.estado(ctx)
        x = 5
        for _ in range(4):
            if estado.terminado:
                break
            x = (x * 1103515245 + 12345) % 2147483648
            estado = acciones.ejecutar(ctx, _elegir_accion(estado, x))

        def foto():
            motor = ctx.motor
            guardado = PartidaGuardada.guardar(motor, ctx.cripta, ctx.resolvedor.version_catalogo(), ctx.semilla)
            mapa = estados(motor.mapa) if hasattr(motor, "mapa") else None     # motor.mapa llega con T033
            return motor, motor.reloj, guardado, mapa, motor.historial.cantidad()

        antes = foto()
        self.archivo_v1()
        with self.assertRaises(ErrorGuardado) as error:
            ServicioGuardado(servicio).cargar(self.ruta, "Ana")
        self.assertIn("versión 1", str(error.exception))
        despues = foto()
        self.assertIs(despues[0], antes[0])                             # el mismo motor
        self.assertEqual(despues[1:], antes[1:])                        # reloj, estado completo, mapa e historial

    # ------------------------------------------------------------ formato inválido
    def test_t003_de_la_004_linea_con_formato_invalido_es_error_guardado(self):
        from Data.GuardadoBinario import ErrorGuardado, cargar, guardar
        from DTO.LineaTiempoDTO import LineaTiempoGuardadaDTO, PuntoControlGuardadoDTO
        base = linea_de_ejemplo(k=3)
        acciones = list(base.acciones)
        acciones[1], acciones[2] = acciones[2], acciones[1]
        p0, p3, p6 = base.puntos
        malas = [
            ("k menor que 1", dataclasses.replace(base, k=0)),
            ("acciones fuera de orden de tiempo", dataclasses.replace(base, acciones=acciones)),
            ("puntos que no crecen estrictamente", dataclasses.replace(base, puntos=[p0, p3, p3])),
            ("puntos fuera de orden", dataclasses.replace(base, puntos=[p0, p6, p3])),
            ("punto fuera de rango", dataclasses.replace(
                base, puntos=[p0, p3, dataclasses.replace(p6, acciones_completadas=7)])),
            ("más de k acciones entre dos puntos", dataclasses.replace(base, puntos=[p0, p6])),
        ]
        for motivo, linea in malas:
            guardar(self.ruta, self.partida(), self.salas)              # una partida buena ya guardada
            antes = self.bytes_del_archivo()
            with self.subTest(motivo=motivo, momento="al guardar"):
                with self.assertRaises(ErrorGuardado):                  # no se escribe un archivo que no se lee
                    guardar(self.ruta, self.partida(linea=linea), self.salas)
                self.assertEqual(self.bytes_del_archivo(), antes)
            with self.subTest(motivo=motivo, momento="al leer"):
                with mock.patch.object(LineaTiempoGuardadaDTO, "validar", lambda self: None):
                    guardar(self.ruta, self.partida(linea=linea), self.salas)    # escrito saltando la validación
                with self.assertRaises(ErrorGuardado):
                    cargar(self.ruta)
        anidada = PuntoControlGuardadoDTO(0, self.partida(linea=LineaTiempoGuardadaDTO(1)), [])
        with self.subTest(motivo="punto con partida.linea distinto de None"):
            with self.assertRaises(ErrorGuardado):                      # el bloque global de un punto no la lleva
                guardar(self.ruta, self.partida(linea=dataclasses.replace(base, puntos=[anidada])), self.salas)

    def test_fr221_binario_cabecera_de_58_bytes(self):
        from Data import GuardadoBinario
        from Data.GuardadoBinario import guardar
        self.assertEqual(GuardadoBinario._CABECERA.size, 58)
        self.assertEqual(GuardadoBinario._CABECERA.format, CABECERA_V2.format)
        guardar(self.ruta, self.partida(mapa=mapa_guardado_de_ejemplo(), linea=linea_de_ejemplo()), self.salas)
        datos = self.bytes_del_archivo()
        (magia, version, offset_global, largo_global, offset_indice, entradas, id_minimo,
         offset_mapa, largo_mapa, offset_linea, largo_linea) = CABECERA_V2.unpack_from(datos, 0)
        self.assertEqual((magia, version), (b"CRPT", 2))
        self.assertEqual(offset_global, 58)
        self.assertEqual(offset_mapa, offset_global + largo_global)     # global · mapa · línea · salas · índice
        self.assertEqual(offset_linea, offset_mapa + largo_mapa)
        self.assertLessEqual(offset_linea + largo_linea, offset_indice)
        self.assertEqual(offset_indice + entradas * 12, len(datos))     # el índice sigue al final
        self.assertEqual((entradas, id_minimo), (4 - self.salas[0].id + 1, self.salas[0].id))
        self.assertEqual(struct.unpack_from("<Q", datos, POS_MAPA)[0], offset_mapa)
        self.assertEqual(struct.unpack_from("<Q", datos, POS_LINEA)[0], offset_linea)

    def test_fr221_bytes_del_mapa_invalidos_son_error_guardado(self):
        from Data.GuardadoBinario import ErrorGuardado, cargar, cargar_sala, guardar
        mapa = mapa_guardado_de_ejemplo(7)
        guardar(self.ruta, self.partida(mapa=mapa), self.salas)
        original = self.bytes_del_archivo()
        offset_mapa, largo_mapa = struct.unpack_from("<QI", original, POS_MAPA)
        offset_indice = struct.unpack_from("<Q", original, 18)[0]
        s = len(mapa.estado_salas)
        casos = [
            ("estado fuera de {0, 1, 2}", lambda d: d.__setitem__(offset_mapa + 4 + 2, 3)),
            ("par de bits de cara igual a 3", lambda d: d.__setitem__(offset_mapa + 4 + s + 1, 0b00110000)),
            ("cantidad de salas que no coincide con el largo",
             lambda d: struct.pack_into("<I", d, offset_mapa, s + 1)),
            ("largo de la cabecera que no coincide",
             lambda d: struct.pack_into("<I", d, POS_MAPA + 8, largo_mapa - 1)),
            ("offset dentro de la cabecera", lambda d: struct.pack_into("<Q", d, POS_MAPA, 10)),
            ("offset en el índice", lambda d: struct.pack_into("<Q", d, POS_MAPA, offset_indice)),
        ]
        for motivo, danar in casos:
            with self.subTest(motivo=motivo):
                datos = bytearray(original)
                danar(datos)
                self.escribir_bytes(datos)
                with self.assertRaises(ErrorGuardado):
                    cargar(self.ruta)
                self.assertEqual(cargar_sala(self.ruta, 4), self.salas[1])     # cargar_sala no lee el mapa
        from DTO.MapaConocidoDTO import MapaConocidoGuardadoDTO
        for malo in (MapaConocidoGuardadoDTO([0, 3], [0] * 8), MapaConocidoGuardadoDTO([0, 1], [0] * 7),
                     MapaConocidoGuardadoDTO([0, 1], [0] * 7 + [5])):
            with self.subTest(al_guardar=malo):
                with self.assertRaises(ErrorGuardado):                  # tampoco se escribe un mapa que no se lee
                    guardar(self.ruta, self.partida(mapa=malo), self.salas)


if __name__ == "__main__":
    unittest.main()

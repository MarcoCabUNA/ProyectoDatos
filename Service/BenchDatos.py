"""
BenchDatos (Integrante 2): mediciones de la capa de Datos para --bench (§5.3 y Documento de Decisiones).

Todas usan cargas SINTÉTICAS generadas aquí (sin red y sin datos de una cripta específica, §9):

  1. medir_cache             "¿está en caché?" con búsqueda binaria (CacheCatalogo) contra la ALTERNATIVA
                             DESCARTADA, búsqueda lineal en un array. Es la sección que mide directamente
                             la alternativa descartada (§8, punto 5).
  2. medir_fichas_liberadas  recuperar una ficha desde memoria contra desde disco (AlmacenCatalogo).
                             Desde la red sería 1 solicitud por lote de 10: no se cronometra (depende del servidor).
  3. medir_precarga          recorrer una cripta en cuadrícula con GestorContenido: cuántas solicitudes de
                             contenido hace la precarga por lotes contra pedir una sala a la vez, y cuánto
                             tarda la decisión de precarga según el tamaño de la cripta.
  4. medir_guardado          GuardadoBinario contra el MISMO estado en JSON: guardar, cargar todo, cargar 1 sala
                             y tamaño en disco (§4.10).
  5. medir_bitacora          anexar una acción al log (debe costar lo mismo con 100 que con 10 000 acciones)
                             y leer un log completo.

Los archivos temporales van en 'carpeta' (por defecto saves/bench_tmp, que ya está en el .gitignore) y se
borran al terminar, aunque una medición falle. Solo se usa os para eso (sin tempfile ni shutil).

medir() corre todo con los tamaños por defecto. Las pruebas llaman a cada función con tamaños chicos.
"""
import json
import os
import random

from Data.AlmacenCatalogo import AlmacenCatalogo
from Data.BitacoraReplayIO import BitacoraReplayIO
from Data.CacheCatalogo import CacheCatalogo
from Data.FuenteDatos import FuenteDatos
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.GuardadoBinario import cargar, cargar_sala, cargar_salas, guardar
from DTO.AccionDTO import AccionDTO
from DTO.CriptaDTO import CriptaDTO
from DTO.ObjetoDTO import ObjetoDTO
from DTO.PartidaGuardadaDTO import (ContadorTipoDTO, EfectoGuardadoDTO, EnemigoGuardadoDTO,
                                    EventoGuardadoDTO, InventarioGuardadoDTO, JugadorGuardadoDTO,
                                    PartidaGuardadaDTO, SalaGuardadaDTO, TrampaGuardadaDTO)
from DTO.ReplayDTO import EncabezadoReplayDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO, SalidaDTO
from Service.Cronometro import medir as cronometrar

CARPETA_POR_DEFECTO = os.path.join("saves", "bench_tmp")
SEMILLA = 2026          # las cargas sintéticas son siempre las mismas: los resultados se pueden comparar


def medir(carpeta: str = CARPETA_POR_DEFECTO) -> list[ResultadoBenchDTO]:
    """Todas las mediciones de Datos, con los tamaños por defecto."""
    return (medir_cache() + medir_fichas_liberadas(carpeta=carpeta) + medir_precarga()
            + medir_guardado(carpeta=carpeta) + medir_bitacora(carpeta=carpeta))


# ====================================================================== 1. caché
def medir_cache(tamanos=(25, 100, 1000, 10000), consultas: int = 500,
                repeticiones: int = 7) -> list[ResultadoBenchDTO]:
    """Las mismas consultas (la mitad existen) contra la caché real y contra un array con búsqueda lineal."""
    resultados = []
    for n in tamanos:
        ids = [_id_ficha(i) for i in range(n)]          # ya en orden: insertar al final no corre nada
        cache = CacheCatalogo(tope=n)
        for id_ficha in ids:
            cache.insertar(_ficha(id_ficha))
        azar = random.Random(SEMILLA + n)
        pedidas = [ids[azar.randrange(n)] if i % 2 == 0 else _id_ficha(n + azar.randrange(n))
                   for i in range(consultas)]

        def binaria():
            for id_ficha in pedidas:
                cache.contiene(id_ficha)

        def lineal():
            for id_ficha in pedidas:
                _contiene_lineal(ids, id_ficha)

        nota = f"{consultas} consultas (la mitad existen)"
        mejor, mediana = cronometrar(binaria, repeticiones)
        resultados.append(ResultadoBenchDTO("caché", "búsqueda binaria (CacheCatalogo)", n, mejor, mediana, nota))
        mejor, mediana = cronometrar(lineal, repeticiones)
        resultados.append(ResultadoBenchDTO("caché", "búsqueda lineal (descartada)", n, mejor, mediana, nota))
    return resultados


def _contiene_lineal(ids: list[str], buscado: str) -> bool:
    """La alternativa descartada: recorrer el array hasta encontrarlo. O(n)."""
    for id_ficha in ids:
        if id_ficha == buscado:
            return True
    return False


# ====================================================================== 2. fichas liberadas
def medir_fichas_liberadas(cantidad: int = 200, repeticiones: int = 15,
                           carpeta: str = CARPETA_POR_DEFECTO) -> list[ResultadoBenchDTO]:
    """Recuperar 'cantidad' fichas: desde la caché en memoria contra desde la caché en disco."""
    _borrar_carpeta(carpeta)
    try:
        almacen = AlmacenCatalogo("bench", os.path.join(carpeta, "catalogo"))
        almacen.preparar()
        cache = CacheCatalogo(tope=cantidad)
        ids = [_id_ficha(i) for i in range(cantidad)]
        for id_ficha in ids:
            almacen.guardar(_ficha(id_ficha))
            cache.insertar(_ficha(id_ficha))

        def desde_memoria():
            for id_ficha in ids:
                cache.obtener(id_ficha)

        def desde_disco():
            for id_ficha in ids:
                almacen.leer(id_ficha)

        nota = f"{cantidad} fichas; desde la red serían {_lotes_de_10(cantidad)} solicitudes (no se cronometra)"
        mejor_m, mediana_m = cronometrar(desde_memoria, repeticiones)
        mejor_d, mediana_d = cronometrar(desde_disco, repeticiones)
        return [ResultadoBenchDTO("fichas liberadas", "desde memoria", cantidad, mejor_m, mediana_m, nota),
                ResultadoBenchDTO("fichas liberadas", "desde disco (AlmacenCatalogo)", cantidad,
                                  mejor_d, mediana_d, nota)]
    finally:
        _borrar_carpeta(carpeta)


def _lotes_de_10(cantidad: int) -> int:
    return (cantidad + 9) // 10


# ====================================================================== 3. precarga
def medir_precarga(lados=(10, 30, 60), pasos: int = 100, repeticiones: int = 5) -> list[ResultadoBenchDTO]:
    """
    Recorre 'pasos' salas de una cripta de lado x lado salas (en zigzag), como lo haría Servicios:
    precargar_alrededor(sala actual) y asegurar_sala(siguiente). Cuenta las solicitudes de contenido.
    """
    resultados = []
    for lado in lados:
        camino = _zigzag(lado, pasos)

        def nuevo_gestor():
            fuente = _FuenteCuadricula(lado)
            esqueleto = GestorEsqueleto(fuente)
            esqueleto.cargar(fuente.obtener_datos_generales("bench"))
            return GestorContenido(fuente, esqueleto)

        def recorrer(gestor):
            gestor.asegurar_sala(camino[0])
            for i in range(len(camino) - 1):
                gestor.precargar_alrededor(camino[i])
                gestor.asegurar_sala(camino[i + 1])
            return gestor

        contado = recorrer(nuevo_gestor())                 # una vez aparte, para contar solicitudes
        mejor, mediana = cronometrar(recorrer, repeticiones, preparar=nuevo_gestor)
        nota = (f"{len(camino)} salas recorridas: {contado.lotes_realizados()} solicitudes de contenido en "
                f"lotes ({contado.salas_pedidas()} salas pedidas); una sala por solicitud serían {len(camino)}")
        resultados.append(ResultadoBenchDTO("precarga", "lotes de hasta 10 salas (GestorContenido)",
                                            lado * lado, mejor, mediana, nota))
    return resultados


def _zigzag(lado: int, pasos: int) -> list[int]:
    """Ids de sala recorriendo filas de izquierda a derecha y de derecha a izquierda (salas vecinas)."""
    camino = []
    for fila in range(lado):
        columnas = range(lado) if fila % 2 == 0 else range(lado - 1, -1, -1)
        for columna in columnas:
            if len(camino) == pasos:
                return camino
            camino.append(fila * lado + columna + 1)
    return camino


class _FuenteCuadricula(FuenteDatos):
    """FuenteDatos sintética: lado x lado salas conectadas N, S, E, O. Sin red y sin catálogo."""

    def __init__(self, lado: int):
        self._lado = lado

    def listar_criptas(self):
        return []

    def obtener_datos_generales(self, id_cripta: str) -> CriptaDTO:
        n = self._lado * self._lado
        return CriptaDTO(id="bench", version="v", salas_total=n, paginas=1, salas_por_pagina=n,
                         sala_inicial=1, sala_salida=n, llave_salida="itm_llave",
                         presupuesto_solicitudes=10 * n, inventario_max=10, jugador_vida_max=30,
                         jugador_ataque=6, jugador_defensa=2, jugador_velocidad=100)

    def obtener_version_cripta(self, id_cripta: str) -> str:
        return "v"

    def obtener_pagina_salas(self, id_cripta: str, pagina: int, version: str) -> list[SalaDTO]:
        lado = self._lado
        salas = []
        for f in range(lado):
            for c in range(lado):
                salidas: list[SalidaDTO | None] = [None, None, None, None]
                if f > 0:
                    salidas[0] = SalidaDTO((f - 1) * lado + c + 1)
                if f < lado - 1:
                    salidas[1] = SalidaDTO((f + 1) * lado + c + 1)
                if c < lado - 1:
                    salidas[2] = SalidaDTO(f * lado + c + 2)
                if c > 0:
                    salidas[3] = SalidaDTO(f * lado + c)
                id_sala = f * lado + c + 1
                salas.append(SalaDTO(id_sala, f"Sala {id_sala}", salidas, version))
        return salas

    def obtener_contenido(self, id_cripta: str, ids_salas: list[int]) -> list[ContenidoSalaDTO]:
        return [ContenidoSalaDTO(i) for i in ids_salas]

    def obtener_version_catalogo(self) -> str:
        return "v"

    def obtener_catalogo(self, ids: list[str]) -> list:
        return []


# ====================================================================== 4. guardado
def medir_guardado(tamanos=(20, 200, 2000), repeticiones: int = 10,
                   carpeta: str = CARPETA_POR_DEFECTO) -> list[ResultadoBenchDTO]:
    """El mismo estado guardado en binario y en JSON (compacto, sin espacios)."""
    resultados = []
    _borrar_carpeta(carpeta)
    try:
        os.makedirs(carpeta, exist_ok=True)
        for n in tamanos:
            partida, salas = _partida_sintetica(n), _salas_sinteticas(n)
            ruta_bin = os.path.join(carpeta, f"partida_{n}.sav")
            ruta_json = os.path.join(carpeta, f"partida_{n}.json")
            una = (n + 1) // 2

            def guardar_binario():
                guardar(ruta_bin, partida, salas)

            def guardar_json():
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump({"partida": partida.a_diccionario(),
                               "salas": [s.a_diccionario() for s in salas]}, f, separators=(",", ":"))

            def cargar_todo_binario():
                return cargar(ruta_bin), cargar_salas(ruta_bin)

            def cargar_todo_json():
                datos = _leer_json(ruta_json)
                return (PartidaGuardadaDTO.desde_diccionario(datos["partida"]),
                        [SalaGuardadaDTO.desde_diccionario(s) for s in datos["salas"]])

            def cargar_una_binario():
                return cargar_sala(ruta_bin, una)

            def cargar_una_json():
                return SalaGuardadaDTO.desde_diccionario(_leer_json(ruta_json)["salas"][una - 1])

            guardar_binario()
            guardar_json()
            # antes de medir, los dos formatos tienen que devolver exactamente lo mismo
            if cargar_todo_binario() != cargar_todo_json() or cargar_una_binario() != cargar_una_json():
                raise AssertionError("el binario y el JSON no devuelven el mismo estado")
            kb_bin = os.path.getsize(ruta_bin) / 1000
            kb_json = os.path.getsize(ruta_json) / 1000
            tamano = f"archivo: binario {kb_bin:.1f} KB, JSON {kb_json:.1f} KB"
            casos = [("guardar", "binario", guardar_binario), ("guardar", "JSON", guardar_json),
                     ("cargar todo", "binario", cargar_todo_binario), ("cargar todo", "JSON", cargar_todo_json),
                     ("cargar 1 sala", "binario", cargar_una_binario), ("cargar 1 sala", "JSON", cargar_una_json)]
            for operacion, formato, funcion in casos:
                mejor, mediana = cronometrar(funcion, repeticiones)
                resultados.append(ResultadoBenchDTO("guardado", f"{operacion}: {formato}", n, mejor, mediana, tamano))
    finally:
        _borrar_carpeta(carpeta)
    return resultados


def _leer_json(ruta: str) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _partida_sintetica(salas: int) -> PartidaGuardadaDTO:
    azar = random.Random(SEMILLA)
    version, estado, gauss = random.Random(SEMILLA).getstate()
    efectos = [EfectoGuardadoDTO("velocidad", "jugador", 300, 25, 900, 25),
               EfectoGuardadoDTO("antorcha", "jugador", 500, None, 1100)]
    eventos = [EventoGuardadoDTO(700 + i, i, "accion_actor", actor=f"e-{i}") for i in range(min(salas, 50))]
    eventos.append(EventoGuardadoDTO(900, 999, "velocidad", efecto=0))
    return PartidaGuardadaDTO(
        id_cripta="bench", version_cripta="v", version_catalogo="v", semilla=SEMILLA,
        reloj=700, siguiente_secuencia=1000, enemigos_derrotados=3, terminado=False, victoria=False,
        salida_abierta=False, azar_version=version, azar_estado=list(estado), azar_gauss=gauss,
        jugador=JugadorGuardadoDTO(22, 30, 6, 2, 125, 1, 40),
        inventario=InventarioGuardadoDTO(["itm_daga", "itm_pocion", "itm_cota"], 0, 0, 2),
        rastro=[None if azar.random() < 0.5 else azar.randrange(700) for _ in range(salas + 1)],
        contadores_tipo=[ContadorTipoDTO("ene_rata", 4)], efectos=efectos, eventos=eventos,
        ruta_log="logs/partida_001.log", acciones_en_log=40)


def _salas_sinteticas(n: int) -> list[SalaGuardadaDTO]:
    salas = []
    for i in range(1, n + 1):
        con_contenido = i % 3 != 0
        salas.append(SalaGuardadaDTO(
            i, con_contenido, [i % 2 == 0, i % 5 == 0, False, i % 7 == 0],
            ["itm_pocion", "itm_daga"][: i % 3] if con_contenido else [],
            [TrampaGuardadaDTO(f"t-{i}", "trp_pinchos", i % 2 == 0)] if i % 4 == 0 else [],
            [EnemigoGuardadoDTO(f"e-{i}-{k}", "ene_rata", 3 + k, 100, k + 1, k == 0) for k in range(i % 3)]))
    return salas


# ====================================================================== 5. bitácora
def medir_bitacora(tamanos=(100, 1000, 10000), anexos: int = 50, repeticiones: int = 7,
                   carpeta: str = CARPETA_POR_DEFECTO) -> list[ResultadoBenchDTO]:
    """Anexar 1 acción a un log que ya tiene n acciones (debe ser constante) y leer el log completo."""
    resultados = []
    acciones = [AccionDTO("mover", direccion=0), AccionDTO("atacar", objetivo="e-201"), AccionDTO("esperar"),
                AccionDTO("recoger", objeto="itm_daga"), AccionDTO("equipar", objeto="itm_daga")]
    _borrar_carpeta(carpeta)
    try:
        for n in tamanos:
            bitacora = BitacoraReplayIO(BitacoraReplayIO.ruta_libre(carpeta, "bench"))
            bitacora.iniciar(EncabezadoReplayDTO("bench", "v", "v", SEMILLA))
            for i in range(n):
                bitacora.anexar(acciones[i % len(acciones)])
            mejor, mediana = cronometrar(lambda: BitacoraReplayIO.leer(bitacora.ruta()), repeticiones)
            resultados.append(ResultadoBenchDTO("bitácora", "leer el log completo", n, mejor, mediana,
                                                f"log con {n} acciones"))
            mejor, mediana = cronometrar(lambda: bitacora.anexar(acciones[0]), anexos, calentar=False)
            resultados.append(ResultadoBenchDTO("bitácora", "anexar 1 acción", n, mejor, mediana,
                                                f"log que ya tiene {n} acciones; {anexos} repeticiones"))
    finally:
        _borrar_carpeta(carpeta)
    return resultados


# ====================================================================== auxiliares
def _id_ficha(i: int) -> str:
    return f"itm_{i:06d}"


def _ficha(id_ficha: str) -> ObjetoDTO:
    return ObjetoDTO(id=id_ficha, nombre=id_ficha, clase="arma", peso=1, valor=1, ataque_bonus=1)


def _borrar_carpeta(carpeta: str) -> None:
    """Borra la carpeta temporal con todo lo que tenga adentro (solo con os)."""
    if not os.path.isdir(carpeta):
        return
    for raiz, carpetas, archivos in os.walk(carpeta, topdown=False):
        for nombre in archivos:
            os.remove(os.path.join(raiz, nombre))
        for nombre in carpetas:
            os.rmdir(os.path.join(raiz, nombre))
    os.rmdir(carpeta)
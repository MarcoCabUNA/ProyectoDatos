"""
GuardadoBinario (Integrante 2): guarda y carga la partida en un archivo binario de formato propio
(enunciado §4.10). Recibe y entrega DTOs (DTO/PartidaGuardadaDTO.py); nunca conoce Lógica.

Lo que pide §4.10 y cómo se cumple:
  - Formato binario propio            -> struct, little-endian, descrito abajo.
  - Recuperar UNA sala sin leer todo  -> índice de acceso directo: cargar_sala() lee la cabecera,
                                         1 entrada del índice y el bloque de esa sala (3 lecturas).
  - Detectar otra versión del formato -> la cabecera empieza con "CRPT" y VERSION_FORMATO; se
                                         revisan antes de interpretar cualquier otro byte.
  - Comparar contra JSON              -> a_diccionario() de los DTOs (paso 12b-3 y --bench).

Formato del archivo (versión 2, Parte II; feature 002 data-model §6 y T003 de la 004):

    CABECERA (58 bytes, fija)
        4s  "CRPT"
        H   versión del formato (= 2)
        Q   offset del bloque global      I  largo del bloque global
        Q   offset del índice             I  cantidad de entradas del índice
        I   id de sala mínimo (la entrada 0 del índice es esa sala)
        Q   offset del bloque del mapa    I  largo del bloque del mapa   (0 = PartidaGuardadaDTO.mapa es None)
        Q   offset del bloque de la línea I  largo del bloque de la línea (0 = PartidaGuardadaDTO.linea es None)
    BLOQUE GLOBAL       PartidaGuardadaDTO sin mapa ni línea (mismo formato que en la versión 1)
    BLOQUE DEL MAPA     I cantidad de salas S · S bytes de estado · S bytes de caras (las 4 caras de una sala en
                        un byte, 2 bits cada una: bits 0-1 = N, 2-3 = S, 4-5 = E, 6-7 = O)
    BLOQUE DE LA LÍNEA  k · cantidad y acciones · cantidad y puntos de control (cada uno: acciones_completadas,
                        su bloque global, cantidad y sus salas, y el bloque de su mapa con largo I delante) ·
                        cantidad y cargas · cantidad y fichas
    BLOQUES DE SALAS    un SalaGuardadaDTO por sala, uno detrás de otro
    ÍNDICE              una entrada de 12 bytes (Q offset, I largo) por id, desde el id mínimo
                        hasta el máximo; un id que no existe tiene largo 0

    Un archivo de la versión 1 (cabecera de 34 bytes, sin mapa ni línea) se rechaza al leer la versión, antes de
    interpretar el resto; no se migra (004 FR-421).

    El mapa y la línea van en bloques PROPIOS: el bloque global queda igual que en la versión 1 y es el mismo que se
    repite en cada punto de control, y cargar_sala no los lee. El mapa de cada punto usa el mismo
    _codificar_mapa / _leer_mapa que el bloque del mapa. Las fichas del catálogo de la línea se guardan como el
    texto JSON de su a_diccionario (el mismo formato de la caché del catálogo), porque traen campos extra del API
    que no tienen un formato fijo.

    Validación solo de formato: estado de sala y cada par de bits de cara en {0, 1, 2}, largo exacto, offset y
    largo dentro de la zona anterior al índice; la línea, con las restricciones del §1 del contrato de la 004
    (LineaTiempoGuardadaDTO.validar). guardar() también las comprueba, para no reemplazar una partida buena por un
    archivo que después no se puede leer.

    La entrada de la sala 'id' está en  offset_indice + (id - id_minimo) * 12.
    Es el mismo supuesto que GestorEsqueleto: los ids de sala son seguidos (1..N). Así no hay que
    ordenar ni buscar: la posición se calcula (O(1)). Con un índice ordenado y búsqueda binaria
    serían O(log n) lecturas en disco, o leer todo el índice.

    Tipos dentro de los bloques: enteros "i" (4 bytes, con signo; la semilla "q", 8 bytes),
    booleanos "?" (1 byte), textos con largo "H" + UTF-8, opcionales con 1 byte (0 = None),
    listas con cantidad "I" + elementos, las 4 puertas de una sala en 1 byte (un bit por puerta),
    el estado del azar como 625 enteros "I" empaquetados en una sola llamada.

Decisiones:
  - guardar() arma todo en memoria y lo escribe en "<ruta>.tmp", que luego reemplaza al archivo
    con os.replace. Si el programa se cae guardando, la partida anterior queda intacta.
  - Ante cualquier archivo que no cuadra (otra versión, cortado, offsets fuera del archivo, bytes de
    más dentro de un bloque, sala con otro id) se lanza ErrorGuardado: nunca se carga a medias.
  - Las versiones de cripta y catálogo NO las decide este archivo: comprobar_compatibilidad() le
    dice a Servicios si el estado guardado corresponde a lo que hay disponible ahora.
  - Sin dict ni ordenamientos (enunciado §7): el índice es un array que se llena por posición.

Costos (S = salas, R = id máximo - id mínimo + 1, que es S si los ids son seguidos):
    guardar          O(tamaño del estado + R)
    cargar           O(bloque global)
    cargar_sala      O(1) lecturas + O(tamaño de esa sala)
    cargar_salas     O(tamaño del archivo), con una sola lectura
    ids_salas        O(R)

Medición preliminar (Python 3.13; --bench la debe reproducir), mismo estado en binario y en JSON:
    salas   tamaño binario / JSON     cargar todo binario / JSON    cargar 1 sala binario / JSON
      20        4.7 KB / 13.4 KB          0.24 ms / 0.23 ms             0.020 ms / 0.15 ms
     200       18.6 KB / 55.8 KB          1.45 ms / 1.32 ms             0.022 ms / 0.63 ms
    2000      159.5 KB / 484.4 KB        15.0 ms / 14.6 ms              0.022 ms / 7.04 ms
  - El binario ocupa ~3 veces menos.
  - Cargar UNA sala cuesta lo mismo con 20 que con 2000 salas (acceso directo); con JSON hay que
    leer y analizar el archivo completo, así que crece con el tamaño (~300 veces más a 2000 salas).
  - Cargar TODO cuesta casi lo mismo: el lector de json está escrito en C y el nuestro decodifica
    en Python. Para acercarlo se precompilaron los formatos (struct.Struct), los campos fijos se
    leen juntos y cargar_salas lee el archivo de una sola vez.

Uso desde Servicios (Kristel), con los DTOs que arman Marco y Kristel:
    bytes_escritos = guardar("saves/partida1.sav", partida, salas)
    partida = cargar("saves/partida1.sav")
    problemas = comprobar_compatibilidad(partida, cripta.version, resolvedor.version_catalogo())
    salas = cargar_salas("saves/partida1.sav")         # se reconstruyen todas (acuerdo del 11/10)
"""
import json
import os
import struct
from dataclasses import replace

from Data.FuenteJson import FuenteJson
from DTO.LineaTiempoDTO import (AccionGuardadaDTO, LineaTiempoGuardadaDTO, PuntoControlGuardadoDTO,
                                RegistroCargaGuardadoDTO)
from DTO.MapaConocidoDTO import CERRADA, EXPLORADA, MapaConocidoGuardadoDTO
from DTO.PartidaGuardadaDTO import (ContadorTipoDTO, EfectoGuardadoDTO, EnemigoGuardadoDTO,
                                    EventoGuardadoDTO, InventarioGuardadoDTO, JugadorGuardadoDTO,
                                    PartidaGuardadaDTO, SalaGuardadaDTO, TrampaGuardadaDTO)
from DTO.SalaDTO import EnemigoEnSalaDTO, SalaDTO, SalidaDTO, TrampaEnSalaDTO
from Security.ValidadorAcceso import validar_version

MAGIA = b"CRPT"
VERSION_FORMATO = 2
# magia, versión, offset y largo global, offset índice, entradas, id mínimo, offset y largo del mapa,
# offset y largo de la línea (58 bytes)
_CABECERA = struct.Struct("<4sHQIQIIQIQI")
_ENTRADA = struct.Struct("<QI")             # offset y largo de un bloque de sala
_RANGO_MAXIMO = 1_000_000                   # ids de sala más separados que esto no caben en un índice directo

# Formatos precompilados (struct.Struct no vuelve a interpretar el texto del formato en cada dato).
# Los campos fijos que van juntos se leen y escriben con UNA sola llamada (_SALA, _ENEMIGO, _JUGADOR).
_I32 = struct.Struct("<i")
_I64 = struct.Struct("<q")
_U32 = struct.Struct("<I")
_U16 = struct.Struct("<H")
_BOOL = struct.Struct("<?")
_F64 = struct.Struct("<d")
_SALA = struct.Struct("<i?B")               # id, contenido_cargado, bits de las 4 puertas
_ENEMIGO = struct.Struct("<iii?")           # vida, velocidad, numero, activo
_JUGADOR = struct.Struct("<7i")             # vida, vida_max, ataque, defensa, velocidad, sala_actual, acciones


class ErrorGuardado(ValueError):
    """La partida no se pudo guardar o el archivo no se puede cargar. El mensaje dice por qué."""


# ====================================================================== API pública
def guardar(ruta: str, partida: PartidaGuardadaDTO, salas: list[SalaGuardadaDTO]) -> int:
    """Escribe la partida completa (reemplaza la anterior de forma segura). Devuelve los bytes escritos."""
    if not isinstance(partida, PartidaGuardadaDTO):
        raise ErrorGuardado(f"se esperaba un PartidaGuardadaDTO y llegó {type(partida).__name__}")
    for sala in salas:
        if not isinstance(sala, SalaGuardadaDTO):
            raise ErrorGuardado(f"se esperaba un SalaGuardadaDTO y llegó {type(sala).__name__}")
    if partida.mapa is not None and not isinstance(partida.mapa, MapaConocidoGuardadoDTO):
        raise ErrorGuardado(f"se esperaba un MapaConocidoGuardadoDTO y llegó {type(partida.mapa).__name__}")
    if partida.linea is not None and not isinstance(partida.linea, LineaTiempoGuardadaDTO):
        raise ErrorGuardado(f"se esperaba un LineaTiempoGuardadaDTO y llegó {type(partida.linea).__name__}")
    try:
        global_ = _codificar_partida(partida)
        mapa = _codificar_mapa(partida.mapa)
        linea = _codificar_linea(partida.linea)
        bloques = [_codificar_sala(sala) for sala in salas]
    except (struct.error, TypeError, AttributeError, UnicodeEncodeError, OverflowError, ValueError) as error:
        raise ErrorGuardado(f"la partida tiene un dato que no se puede guardar: {error}") from None

    id_minimo, entradas = _armar_indice(salas)
    offset_global = _CABECERA.size
    offset_mapa = offset_global + len(global_)
    offset_linea = offset_mapa + len(mapa)
    posicion = offset_linea + len(linea)
    for i in range(len(salas)):          # cada sala va en su posición del índice, sin ordenar ni buscar
        entradas[salas[i].id - id_minimo] = (posicion, len(bloques[i]))
        posicion += len(bloques[i])
    offset_indice = posicion

    partes = [_CABECERA.pack(MAGIA, VERSION_FORMATO, offset_global, len(global_),
                             offset_indice, len(entradas), id_minimo,
                             offset_mapa, len(mapa), offset_linea, len(linea)),
              global_, mapa, linea]
    partes.extend(bloques)
    for offset, largo in entradas:
        partes.append(_ENTRADA.pack(offset, largo))
    contenido = b"".join(partes)
    _escribir_seguro(ruta, contenido)
    return len(contenido)


def cargar(ruta: str) -> PartidaGuardadaDTO:
    """Todo lo que no es de una sala: el bloque global, el del mapa y el de la línea."""
    with _abrir(ruta) as archivo:
        cabecera = _leer_cabecera(archivo, ruta)
        datos = _leer_en(archivo, ruta, cabecera.offset_global, cabecera.largo_global, "el bloque global")
        datos_mapa = _leer_bloque_opcional(archivo, ruta, cabecera, cabecera.offset_mapa, cabecera.largo_mapa,
                                           "el mapa conocido")
        datos_linea = _leer_bloque_opcional(archivo, ruta, cabecera, cabecera.offset_linea, cabecera.largo_linea,
                                            "la línea de tiempo")
    partida = _decodificar(datos, _leer_partida, ruta, "el bloque global")
    mapa = None if datos_mapa is None else _decodificar(datos_mapa, _leer_mapa, ruta, "el mapa conocido")
    linea = None if datos_linea is None else _decodificar(datos_linea, _leer_linea, ruta, "la línea de tiempo")
    return replace(partida, mapa=mapa, linea=linea)


def cargar_sala(ruta: str, id_sala: int) -> SalaGuardadaDTO | None:
    """Solo esa sala, sin leer el resto del archivo. None si la sala no está guardada."""
    if not isinstance(id_sala, int) or isinstance(id_sala, bool):
        raise ErrorGuardado(f"el id de sala debe ser un entero (llegó {id_sala!r})")
    with _abrir(ruta) as archivo:
        cabecera = _leer_cabecera(archivo, ruta)
        return _cargar_sala_abierta(archivo, ruta, cabecera, id_sala)


def cargar_salas(ruta: str) -> list[SalaGuardadaDTO]:
    """
    Todas las salas guardadas, en orden de id (para reconstruir la mazmorra al cargar).
    Como las necesita todas, lee el archivo de una vez en lugar de hacer un seek por sala.
    """
    with _abrir(ruta) as archivo:
        cabecera = _leer_cabecera(archivo, ruta)
        archivo.seek(0)
        datos = archivo.read()
    entradas = [_ENTRADA.unpack_from(datos, cabecera.offset_indice + i * _ENTRADA.size)
                for i in range(cabecera.entradas)]
    salas = []
    for i in range(len(entradas)):
        offset, largo = entradas[i]
        if largo > 0:
            if offset + largo > cabecera.offset_indice:
                raise ErrorGuardado(f"{ruta!r} está dañado: la sala {cabecera.id_minimo + i} se sale de su zona")
            salas.append(_sala_desde_bytes(datos[offset:offset + largo], ruta, cabecera.id_minimo + i))
    return salas


def ids_salas(ruta: str) -> list[int]:
    """Ids de las salas guardadas, de menor a mayor (sale ordenado por cómo está hecho el índice)."""
    with _abrir(ruta) as archivo:
        cabecera = _leer_cabecera(archivo, ruta)
        entradas = _leer_indice(archivo, ruta, cabecera)
    return [cabecera.id_minimo + i for i in range(len(entradas)) if entradas[i][1] > 0]


def comprobar_compatibilidad(partida: PartidaGuardadaDTO, version_cripta_disponible: str | None,
                             version_catalogo_disponible: str | None) -> list[str]:
    """
    Problemas para continuar esta partida con lo disponible ahora; vacía = se puede cargar.
    Si la cripta o el catálogo cambiaron de versión, el estado guardado apunta a otras salas y fichas.
    """
    problemas: list[str] = []
    if not validar_version(partida.version_cripta, version_cripta_disponible):
        problemas.append(f"la partida es de la versión {partida.version_cripta!r} de {partida.id_cripta!r} "
                         f"y la disponible es {version_cripta_disponible!r}")
    if not validar_version(partida.version_catalogo, version_catalogo_disponible):
        problemas.append(f"la partida usa el catálogo {partida.version_catalogo!r} "
                         f"y el disponible es {version_catalogo_disponible!r}")
    return problemas


# ====================================================================== archivo
class _Cabecera:
    def __init__(self, offset_global: int, largo_global: int, offset_indice: int, entradas: int,
                 id_minimo: int, offset_mapa: int, largo_mapa: int, offset_linea: int, largo_linea: int):
        self.offset_global = offset_global
        self.largo_global = largo_global
        self.offset_indice = offset_indice
        self.entradas = entradas
        self.id_minimo = id_minimo
        self.offset_mapa = offset_mapa
        self.largo_mapa = largo_mapa
        self.offset_linea = offset_linea
        self.largo_linea = largo_linea


def _abrir(ruta: str):
    try:
        return open(ruta, "rb")
    except FileNotFoundError:
        raise ErrorGuardado(f"no existe la partida guardada {ruta!r}") from None
    except OSError as error:
        raise ErrorGuardado(f"no se pudo abrir {ruta!r}: {error}") from None


def _leer_cabecera(archivo, ruta: str) -> _Cabecera:
    datos = archivo.read(_CABECERA.size)
    if len(datos) < 6 or datos[:4] != MAGIA:
        raise ErrorGuardado(f"{ruta!r} no es una partida guardada (no empieza con {MAGIA!r})")
    version = _U16.unpack_from(datos, 4)[0]
    if version < VERSION_FORMATO:           # se revisa ANTES de interpretar el resto
        raise ErrorGuardado(f"{ruta!r} es una partida guardada con un formato viejo (versión {version}) que este "
                            f"programa ya no carga (lee la versión {VERSION_FORMATO}): empieza una partida nueva")
    if version > VERSION_FORMATO:
        raise ErrorGuardado(f"{ruta!r} es una partida guardada con un formato más nuevo (versión {version}) que "
                            f"este programa no sabe leer (lee la versión {VERSION_FORMATO}): actualiza el programa")
    if len(datos) < _CABECERA.size:
        raise ErrorGuardado(f"{ruta!r} está cortado (la cabecera está incompleta)")
    (_, _, offset_global, largo_global, offset_indice, entradas, id_minimo,
     offset_mapa, largo_mapa, offset_linea, largo_linea) = _CABECERA.unpack(datos)
    tamano = os.fstat(archivo.fileno()).st_size
    if (offset_global + largo_global > tamano
            or offset_indice + entradas * _ENTRADA.size != tamano):
        raise ErrorGuardado(f"{ruta!r} está dañado o cortado (los tamaños de la cabecera no cuadran)")
    # El offset y el largo del mapa y de la línea se comprueban al leerlos (cargar): cargar_sala no los usa.
    return _Cabecera(offset_global, largo_global, offset_indice, entradas, id_minimo,
                     offset_mapa, largo_mapa, offset_linea, largo_linea)


def _leer_en(archivo, ruta: str, offset: int, largo: int, que: str) -> bytes:
    archivo.seek(offset)
    datos = archivo.read(largo)
    if len(datos) != largo:
        raise ErrorGuardado(f"{ruta!r} está cortado: falta parte de {que}")
    return datos


def _leer_bloque_opcional(archivo, ruta: str, cabecera: _Cabecera, offset: int, largo: int,
                          que: str) -> bytes | None:
    """Los bytes de un bloque que puede faltar (largo 0 = None), dentro de la zona entre la cabecera y el índice."""
    if largo == 0:
        return None
    if offset < _CABECERA.size or offset + largo > cabecera.offset_indice:
        raise ErrorGuardado(f"{ruta!r} está dañado: {que} se sale de su zona")
    return _leer_en(archivo, ruta, offset, largo, que)


def _leer_indice(archivo, ruta: str, cabecera: _Cabecera) -> list[tuple[int, int]]:
    datos = _leer_en(archivo, ruta, cabecera.offset_indice, cabecera.entradas * _ENTRADA.size, "el índice")
    return [_ENTRADA.unpack_from(datos, i * _ENTRADA.size) for i in range(cabecera.entradas)]


def _cargar_sala_abierta(archivo, ruta: str, cabecera: _Cabecera, id_sala: int) -> SalaGuardadaDTO | None:
    posicion = id_sala - cabecera.id_minimo
    if posicion < 0 or posicion >= cabecera.entradas:
        return None
    datos = _leer_en(archivo, ruta, cabecera.offset_indice + posicion * _ENTRADA.size, _ENTRADA.size,
                     "el índice")
    offset, largo = _ENTRADA.unpack(datos)
    if largo == 0:
        return None
    return _leer_bloque_sala(archivo, ruta, offset, largo, id_sala)


def _leer_bloque_sala(archivo, ruta: str, offset: int, largo: int, id_esperado: int) -> SalaGuardadaDTO:
    return _sala_desde_bytes(_leer_en(archivo, ruta, offset, largo, f"la sala {id_esperado}"), ruta, id_esperado)


def _sala_desde_bytes(datos: bytes, ruta: str, id_esperado: int) -> SalaGuardadaDTO:
    sala = _decodificar(datos, _leer_sala, ruta, f"la sala {id_esperado}")
    if sala.id != id_esperado:
        raise ErrorGuardado(f"{ruta!r} está dañado: el índice de la sala {id_esperado} apunta a la sala {sala.id}")
    return sala


def _decodificar(datos: bytes, funcion, ruta: str, que: str):
    lector = _Lector(datos)
    try:
        resultado = funcion(lector)
    except (struct.error, UnicodeDecodeError, ValueError) as error:
        raise ErrorGuardado(f"{ruta!r} está dañado en {que}: {error}") from None
    if lector.pos != len(datos):
        raise ErrorGuardado(f"{ruta!r} está dañado en {que}: sobran {len(datos) - lector.pos} bytes")
    return resultado


def _armar_indice(salas: list[SalaGuardadaDTO]) -> tuple[int, list[tuple[int, int]]]:
    """Array de entradas vacías, una por id entre el mínimo y el máximo. Rechaza ids repetidos."""
    if not salas:
        return 0, []
    id_minimo = id_maximo = salas[0].id
    for sala in salas:
        if not isinstance(sala.id, int) or isinstance(sala.id, bool) or sala.id < 0:
            raise ErrorGuardado(f"el id de sala debe ser un entero >= 0 (llegó {sala.id!r})")
        if sala.id < id_minimo:
            id_minimo = sala.id
        if sala.id > id_maximo:
            id_maximo = sala.id
    if id_maximo - id_minimo + 1 > _RANGO_MAXIMO:
        raise ErrorGuardado(f"los ids de sala van de {id_minimo} a {id_maximo}: demasiado separados para el índice")
    vistos = [False] * (id_maximo - id_minimo + 1)
    for sala in salas:
        if vistos[sala.id - id_minimo]:
            raise ErrorGuardado(f"la sala {sala.id} viene dos veces")
        vistos[sala.id - id_minimo] = True
    return id_minimo, [(0, 0)] * (id_maximo - id_minimo + 1)


def _escribir_seguro(ruta: str, contenido: bytes) -> None:
    carpeta = os.path.dirname(ruta)
    temporal = ruta + ".tmp"
    try:
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(temporal, "wb") as archivo:
            archivo.write(contenido)
        os.replace(temporal, ruta)          # el archivo anterior se cambia de una vez
    except OSError as error:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise ErrorGuardado(f"no se pudo guardar en {ruta!r}: {error}") from None


# ====================================================================== tipos básicos
class _Escritor:
    def __init__(self):
        self._partes: list[bytes] = []

    def entero(self, valor: int) -> None:
        self._partes.append(_I32.pack(valor))

    def entero_largo(self, valor: int) -> None:
        self._partes.append(_I64.pack(valor))

    def booleano(self, valor: bool) -> None:
        self._partes.append(_BOOL.pack(valor))

    def texto(self, valor: str) -> None:
        if not isinstance(valor, str):
            raise TypeError(f"se esperaba un texto y llegó {valor!r}")
        datos = valor.encode("utf-8")
        self._partes.append(_U16.pack(len(datos)))
        self._partes.append(datos)

    def cantidad(self, valor: int) -> None:
        self._partes.append(_U32.pack(valor))

    def entero_opcional(self, valor: int | None) -> None:
        self.booleano(valor is not None)
        if valor is not None:
            self.entero(valor)

    def texto_opcional(self, valor: str | None) -> None:
        self.booleano(valor is not None)
        if valor is not None:
            self.texto(valor)

    def bytes_crudos(self, datos: bytes) -> None:
        self._partes.append(datos)

    def resultado(self) -> bytes:
        return b"".join(self._partes)


class _Lector:
    def __init__(self, datos: bytes):
        self._datos = datos
        self.pos = 0

    def _tomar(self, formato: struct.Struct):
        valor = formato.unpack_from(self._datos, self.pos)[0]
        self.pos += formato.size
        return valor

    def entero(self) -> int:
        return self._tomar(_I32)

    def entero_largo(self) -> int:
        return self._tomar(_I64)

    def booleano(self) -> bool:
        return self._tomar(_BOOL)

    def texto(self) -> str:
        largo = self._tomar(_U16)
        if self.pos + largo > len(self._datos):
            raise ValueError("un texto se sale del bloque")
        valor = self._datos[self.pos:self.pos + largo].decode("utf-8")
        self.pos += largo
        return valor

    def cantidad(self) -> int:
        return self._tomar(_U32)

    def real(self) -> float:
        return self._tomar(_F64)

    def entero_opcional(self) -> int | None:
        return self.entero() if self.booleano() else None

    def texto_opcional(self) -> str | None:
        return self.texto() if self.booleano() else None

    def grupo(self, formato: struct.Struct) -> tuple:
        valores = formato.unpack_from(self._datos, self.pos)
        self.pos += formato.size
        return valores

    def enteros_sin_signo(self, n: int) -> list[int]:
        formato = f"<{n}I"
        valores = list(struct.unpack_from(formato, self._datos, self.pos))
        self.pos += struct.calcsize(formato)
        return valores

    def bytes_crudos(self, n: int) -> bytes:
        if self.pos + n > len(self._datos):
            raise ValueError(f"faltan {self.pos + n - len(self._datos)} bytes al final del bloque")
        valor = self._datos[self.pos:self.pos + n]
        self.pos += n
        return valor


# ====================================================================== bloque global
def _codificar_partida(p: PartidaGuardadaDTO) -> bytes:
    e = _Escritor()
    e.texto(p.id_cripta)
    e.texto(p.version_cripta)
    e.texto(p.version_catalogo)
    e.entero_largo(p.semilla)
    e.entero(p.reloj)
    e.entero(p.siguiente_secuencia)
    e.entero(p.enemigos_derrotados)
    e.booleano(p.terminado)
    e.booleano(p.victoria)
    e.booleano(p.salida_abierta)
    # azar: random.Random.getstate() -> (versión, 625 enteros de 32 bits, gauss pendiente o None)
    e.entero(p.azar_version)
    e.cantidad(len(p.azar_estado))
    e.bytes_crudos(struct.pack(f"<{len(p.azar_estado)}I", *p.azar_estado))
    e.booleano(p.azar_gauss is not None)
    if p.azar_gauss is not None:
        e.bytes_crudos(_F64.pack(p.azar_gauss))
    # jugador
    j = p.jugador
    e.bytes_crudos(_JUGADOR.pack(j.vida, j.vida_max, j.ataque, j.defensa, j.velocidad, j.sala_actual, j.acciones))
    # inventario
    inv = p.inventario
    e.cantidad(len(inv.objetos))
    for id_objeto in inv.objetos:
        e.texto(id_objeto)
    e.entero_opcional(inv.cursor)
    e.entero_opcional(inv.arma)
    e.entero_opcional(inv.armadura)
    # rastro, contadores, efectos y eventos
    e.cantidad(len(p.rastro))
    for tiempo in p.rastro:
        e.entero_opcional(tiempo)
    e.cantidad(len(p.contadores_tipo))
    for c in p.contadores_tipo:
        e.texto(c.tipo)
        e.entero(c.cantidad)
    e.cantidad(len(p.efectos))
    for ef in p.efectos:
        e.texto(ef.tipo)
        e.texto(ef.actor)
        e.entero(ef.duracion)
        e.entero_opcional(ef.valor)
        e.entero(ef.fin)
        e.entero(ef.cambio_real)
    e.cantidad(len(p.eventos))
    for ev in p.eventos:
        e.entero(ev.tiempo)
        e.entero(ev.secuencia)
        e.texto(ev.tipo)
        e.texto_opcional(ev.actor)
        e.entero_opcional(ev.efecto)
        e.entero_opcional(ev.sala)
        e.texto_opcional(ev.trampa)
        e.entero_opcional(ev.direccion)
    # --replay
    e.texto_opcional(p.ruta_log)
    e.entero(p.acciones_en_log)
    return e.resultado()


def _leer_partida(lector: _Lector) -> PartidaGuardadaDTO:
    id_cripta, version_cripta, version_catalogo = lector.texto(), lector.texto(), lector.texto()
    semilla = lector.entero_largo()
    reloj, siguiente_secuencia, enemigos_derrotados = lector.entero(), lector.entero(), lector.entero()
    terminado, victoria, salida_abierta = lector.booleano(), lector.booleano(), lector.booleano()
    azar_version = lector.entero()
    azar_estado = lector.enteros_sin_signo(lector.cantidad())
    azar_gauss = lector.real() if lector.booleano() else None
    jugador = JugadorGuardadoDTO(*lector.grupo(_JUGADOR))
    objetos = [lector.texto() for _ in range(lector.cantidad())]
    inventario = InventarioGuardadoDTO(objetos, lector.entero_opcional(), lector.entero_opcional(),
                                       lector.entero_opcional())
    rastro = [lector.entero_opcional() for _ in range(lector.cantidad())]
    contadores = [ContadorTipoDTO(lector.texto(), lector.entero()) for _ in range(lector.cantidad())]
    efectos = [EfectoGuardadoDTO(lector.texto(), lector.texto(), lector.entero(), lector.entero_opcional(),
                                 lector.entero(), lector.entero()) for _ in range(lector.cantidad())]
    eventos = [EventoGuardadoDTO(lector.entero(), lector.entero(), lector.texto(), lector.texto_opcional(),
                                 lector.entero_opcional(), lector.entero_opcional(), lector.texto_opcional(),
                                 lector.entero_opcional()) for _ in range(lector.cantidad())]
    ruta_log = lector.texto_opcional()
    acciones_en_log = lector.entero()
    return PartidaGuardadaDTO(
        id_cripta=id_cripta, version_cripta=version_cripta, version_catalogo=version_catalogo,
        semilla=semilla, reloj=reloj, siguiente_secuencia=siguiente_secuencia,
        enemigos_derrotados=enemigos_derrotados, terminado=terminado, victoria=victoria,
        salida_abierta=salida_abierta, azar_version=azar_version, azar_estado=azar_estado,
        azar_gauss=azar_gauss, jugador=jugador, inventario=inventario, rastro=rastro,
        contadores_tipo=contadores, efectos=efectos, eventos=eventos,
        ruta_log=ruta_log, acciones_en_log=acciones_en_log)


# ====================================================================== bloque de una sala
def _codificar_sala(s: SalaGuardadaDTO) -> bytes:
    if len(s.puertas_cerradas) != 4:
        raise TypeError(f"la sala {s.id} debe tener exactamente 4 puertas (N, S, E, O)")
    e = _Escritor()
    bits = 0
    for i in range(4):                       # 1 byte para las 4 puertas: bit i = puerta i cerrada
        if s.puertas_cerradas[i]:
            bits |= 1 << i
    e.bytes_crudos(_SALA.pack(s.id, s.contenido_cargado, bits))
    e.cantidad(len(s.objetos))
    for id_objeto in s.objetos:
        e.texto(id_objeto)
    e.cantidad(len(s.trampas))
    for t in s.trampas:
        e.texto(t.instancia)
        e.texto(t.tipo)
        e.booleano(t.armada)
    e.cantidad(len(s.enemigos))
    for en in s.enemigos:
        e.texto(en.instancia)
        e.texto(en.tipo)
        e.bytes_crudos(_ENEMIGO.pack(en.vida, en.velocidad, en.numero, en.activo))
    return e.resultado()


def _leer_sala(lector: _Lector) -> SalaGuardadaDTO:
    id_sala, contenido_cargado, bits = lector.grupo(_SALA)
    if bits > 0b1111:
        raise ValueError("el byte de las puertas tiene bits de más")
    puertas = [(bits >> i) & 1 == 1 for i in range(4)]
    objetos = [lector.texto() for _ in range(lector.cantidad())]
    trampas = [TrampaGuardadaDTO(lector.texto(), lector.texto(), lector.booleano())
               for _ in range(lector.cantidad())]
    enemigos = [EnemigoGuardadoDTO(lector.texto(), lector.texto(), *lector.grupo(_ENEMIGO))
                for _ in range(lector.cantidad())]
    return SalaGuardadaDTO(id_sala, contenido_cargado, puertas, objetos, trampas, enemigos)


# ====================================================================== bloque del mapa (versión 2)
def _valor_de_mapa(valor, maximo: int, que: str) -> int:
    """El valor si es un entero entre 0 y maximo; si no, ValueError (no se escribe lo que no se puede leer)."""
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < 0 or valor > maximo:
        raise ValueError(f"{que} del mapa conocido debe estar entre 0 y {maximo} (llegó {valor!r})")
    return valor


def _codificar_mapa(mapa: MapaConocidoGuardadoDTO | None) -> bytes:
    """I cantidad de salas S · S bytes de estado · S bytes de caras (2 bits por cara: N, S, E, O). None -> b''."""
    if mapa is None:
        return b""
    salas = len(mapa.estado_salas)
    if len(mapa.caras) != 4 * salas:
        raise ValueError(f"el mapa conocido tiene {salas} salas y {len(mapa.caras)} caras (deberían ser {4 * salas})")
    estado = bytearray(salas)
    caras = bytearray(salas)
    for sala in range(salas):
        estado[sala] = _valor_de_mapa(mapa.estado_salas[sala], EXPLORADA, "el estado de una sala")
        byte = 0
        for direccion in range(4):          # bits 0-1 = N, 2-3 = S, 4-5 = E, 6-7 = O
            byte |= _valor_de_mapa(mapa.caras[sala * 4 + direccion], CERRADA, "una cara") << (2 * direccion)
        caras[sala] = byte
    return _U32.pack(salas) + bytes(estado) + bytes(caras)


def _leer_mapa(lector: _Lector) -> MapaConocidoGuardadoDTO:
    """Inverso de _codificar_mapa. Valida solo formato: estado y cada par de bits en {0, 1, 2}."""
    salas = lector.cantidad()
    estado = list(lector.bytes_crudos(salas))
    bytes_caras = lector.bytes_crudos(salas)
    for sala in range(salas):
        if estado[sala] > EXPLORADA:
            raise ValueError(f"la sala {sala} tiene el estado {estado[sala]}, que no existe")
    caras = [0] * (4 * salas)
    for sala in range(salas):
        byte = bytes_caras[sala]
        for direccion in range(4):
            valor = (byte >> (2 * direccion)) & 0b11
            if valor > CERRADA:
                raise ValueError(f"la cara {direccion} de la sala {sala} tiene el estado {valor}, que no existe")
            caras[sala * 4 + direccion] = valor
    return MapaConocidoGuardadoDTO(estado, caras)


def _escribir_mapa_con_largo(e: _Escritor, mapa: MapaConocidoGuardadoDTO | None) -> None:
    """El bloque del mapa con su largo delante (para los puntos de control); largo 0 = None."""
    bloque = _codificar_mapa(mapa)
    e.cantidad(len(bloque))
    e.bytes_crudos(bloque)


def _leer_mapa_con_largo(lector: _Lector) -> MapaConocidoGuardadoDTO | None:
    largo = lector.cantidad()
    if largo == 0:
        return None
    inicio = lector.pos
    mapa = _leer_mapa(lector)
    if lector.pos - inicio != largo:
        raise ValueError(f"el mapa de un punto de control dice medir {largo} bytes y mide {lector.pos - inicio}")
    return mapa


# ====================================================================== bloque de la línea (versión 2)
def _codificar_linea(linea: LineaTiempoGuardadaDTO | None) -> bytes:
    """
    k · acciones · puntos de control (acciones_completadas, bloque global, salas y mapa) · cargas · fichas.
    None -> b''. Antes de escribir comprueba las restricciones del §1 del contrato de la 004 (ValueError).
    """
    if linea is None:
        return b""
    linea.validar()
    e = _Escritor()
    e.entero(linea.k)
    e.cantidad(len(linea.acciones))
    for accion in linea.acciones:
        e.entero(accion.tiempo)
        e.texto(accion.tipo)
        e.entero_opcional(accion.direccion)
        e.texto_opcional(accion.objetivo)
        e.texto_opcional(accion.objeto)
    e.cantidad(len(linea.puntos))
    for punto in linea.puntos:
        e.entero(punto.acciones_completadas)
        e.bytes_crudos(_codificar_partida(punto.partida))       # el mismo bloque global, sin mapa ni línea
        e.cantidad(len(punto.salas))
        for sala in punto.salas:
            e.bytes_crudos(_codificar_sala(sala))
        _escribir_mapa_con_largo(e, punto.partida.mapa)
    e.cantidad(len(linea.cargas))
    for carga in linea.cargas:
        e.entero(carga.ordinal)
        _escribir_sala_dto(e, carga.sala)
    e.cantidad(len(linea.fichas))
    for ficha in linea.fichas:
        e.texto(json.dumps(ficha.a_diccionario(), ensure_ascii=False, separators=(",", ":")))
    return e.resultado()


def _leer_linea(lector: _Lector) -> LineaTiempoGuardadaDTO:
    """Inverso de _codificar_linea. Una línea que no cumple el §1 del contrato de la 004 es ValueError."""
    k = lector.entero()
    acciones = [AccionGuardadaDTO(lector.entero(), lector.texto(), lector.entero_opcional(),
                                  lector.texto_opcional(), lector.texto_opcional())
                for _ in range(lector.cantidad())]
    puntos = []
    for _ in range(lector.cantidad()):
        acciones_completadas = lector.entero()
        partida = _leer_partida(lector)
        salas = [_leer_sala(lector) for _ in range(lector.cantidad())]
        mapa = _leer_mapa_con_largo(lector)
        puntos.append(PuntoControlGuardadoDTO(acciones_completadas, replace(partida, mapa=mapa), salas))
    cargas = [RegistroCargaGuardadoDTO(lector.entero(), _leer_sala_dto(lector)) for _ in range(lector.cantidad())]
    fichas = [_ficha_desde_texto(lector.texto()) for _ in range(lector.cantidad())]
    linea = LineaTiempoGuardadaDTO(k, acciones, puntos, cargas, fichas)
    linea.validar()
    return linea


def _ficha_desde_texto(texto: str):
    """Una ficha del catálogo desde el JSON de su a_diccionario (el mismo formato de la caché del catálogo)."""
    try:
        return FuenteJson.ficha_desde_diccionario(json.loads(texto))
    except (KeyError, TypeError) as error:
        raise ValueError(f"una ficha de la línea de tiempo está incompleta: {error}") from None


def _escribir_sala_dto(e: _Escritor, sala: SalaDTO) -> None:
    """El contenido inicial de una sala (SalaDTO), para las cargas de la línea."""
    if len(sala.salidas) != 4:
        raise TypeError(f"la sala {sala.id} debe tener exactamente 4 salidas (N, S, E, O)")
    e.entero(sala.id)
    e.texto(sala.nombre)
    e.texto(sala.version)
    e.booleano(sala.contenido_cargado)
    for salida in sala.salidas:
        e.booleano(salida is not None)
        if salida is not None:
            e.entero(salida.sala_destino)
            e.booleano(salida.cerrada)
            e.texto_opcional(salida.llave)
            e.entero_opcional(salida.cierre_automatico)
            e.entero_opcional(salida.costo)
    e.cantidad(len(sala.enemigos))
    for enemigo in sala.enemigos:
        e.texto(enemigo.instancia)
        e.texto(enemigo.tipo)
        e.entero_opcional(enemigo.vida)
    e.cantidad(len(sala.objetos))
    for id_objeto in sala.objetos:
        e.texto(id_objeto)
    e.cantidad(len(sala.trampas))
    for trampa in sala.trampas:
        e.texto(trampa.instancia)
        e.texto(trampa.tipo)


def _leer_sala_dto(lector: _Lector) -> SalaDTO:
    id_sala, nombre, version, contenido_cargado = lector.entero(), lector.texto(), lector.texto(), lector.booleano()
    salidas: list[SalidaDTO | None] = [None, None, None, None]
    for direccion in range(4):
        if lector.booleano():
            salidas[direccion] = SalidaDTO(lector.entero(), lector.booleano(), lector.texto_opcional(),
                                           lector.entero_opcional(), lector.entero_opcional())
    enemigos = [EnemigoEnSalaDTO(lector.texto(), lector.texto(), lector.entero_opcional())
                for _ in range(lector.cantidad())]
    objetos = [lector.texto() for _ in range(lector.cantidad())]
    trampas = [TrampaEnSalaDTO(lector.texto(), lector.texto()) for _ in range(lector.cantidad())]
    return SalaDTO(id_sala, nombre, salidas, version, contenido_cargado, enemigos, objetos, trampas)
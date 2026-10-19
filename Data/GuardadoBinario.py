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

Formato del archivo (versión 1):

    CABECERA (34 bytes, fija)
        4s  "CRPT"
        H   versión del formato
        Q   offset del bloque global      I  largo del bloque global
        Q   offset del índice             I  cantidad de entradas del índice
        I   id de sala mínimo (la entrada 0 del índice es esa sala)
    BLOQUE GLOBAL       PartidaGuardadaDTO
    BLOQUES DE SALAS    un SalaGuardadaDTO por sala, uno detrás de otro
    ÍNDICE              una entrada de 12 bytes (Q offset, I largo) por id, desde el id mínimo
                        hasta el máximo; un id que no existe tiene largo 0

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
import os
import struct

from DTO.PartidaGuardadaDTO import (ContadorTipoDTO, EfectoGuardadoDTO, EnemigoGuardadoDTO,
                                    EventoGuardadoDTO, InventarioGuardadoDTO, JugadorGuardadoDTO,
                                    PartidaGuardadaDTO, SalaGuardadaDTO, TrampaGuardadaDTO)
from Security.ValidadorAcceso import validar_version

MAGIA = b"CRPT"
VERSION_FORMATO = 1
_CABECERA = struct.Struct("<4sHQIQII")      # magia, versión, offset y largo global, offset índice, entradas, id mínimo
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
    try:
        global_ = _codificar_partida(partida)
        bloques = [_codificar_sala(sala) for sala in salas]
    except (struct.error, TypeError, AttributeError, UnicodeEncodeError, OverflowError) as error:
        raise ErrorGuardado(f"la partida tiene un dato que no se puede guardar: {error}") from None

    id_minimo, entradas = _armar_indice(salas)
    offset_global = _CABECERA.size
    posicion = offset_global + len(global_)
    for i in range(len(salas)):          # cada sala va en su posición del índice, sin ordenar ni buscar
        entradas[salas[i].id - id_minimo] = (posicion, len(bloques[i]))
        posicion += len(bloques[i])
    offset_indice = posicion

    partes = [_CABECERA.pack(MAGIA, VERSION_FORMATO, offset_global, len(global_),
                             offset_indice, len(entradas), id_minimo), global_]
    partes.extend(bloques)
    for offset, largo in entradas:
        partes.append(_ENTRADA.pack(offset, largo))
    contenido = b"".join(partes)
    _escribir_seguro(ruta, contenido)
    return len(contenido)


def cargar(ruta: str) -> PartidaGuardadaDTO:
    """El bloque global (todo lo que no es de una sala)."""
    with _abrir(ruta) as archivo:
        cabecera = _leer_cabecera(archivo, ruta)
        datos = _leer_en(archivo, ruta, cabecera.offset_global, cabecera.largo_global, "el bloque global")
    return _decodificar(datos, _leer_partida, ruta, "el bloque global")


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
                 id_minimo: int):
        self.offset_global = offset_global
        self.largo_global = largo_global
        self.offset_indice = offset_indice
        self.entradas = entradas
        self.id_minimo = id_minimo


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
    if version != VERSION_FORMATO:          # se revisa ANTES de interpretar el resto
        raise ErrorGuardado(f"{ruta!r} usa la versión {version} del formato y este programa "
                            f"lee la versión {VERSION_FORMATO}")
    if len(datos) < _CABECERA.size:
        raise ErrorGuardado(f"{ruta!r} está cortado (la cabecera está incompleta)")
    _, _, offset_global, largo_global, offset_indice, entradas, id_minimo = _CABECERA.unpack(datos)
    tamano = os.fstat(archivo.fileno()).st_size
    if (offset_global + largo_global > tamano
            or offset_indice + entradas * _ENTRADA.size != tamano):
        raise ErrorGuardado(f"{ruta!r} está dañado o cortado (los tamaños de la cabecera no cuadran)")
    return _Cabecera(offset_global, largo_global, offset_indice, entradas, id_minimo)


def _leer_en(archivo, ruta: str, offset: int, largo: int, que: str) -> bytes:
    archivo.seek(offset)
    datos = archivo.read(largo)
    if len(datos) != largo:
        raise ErrorGuardado(f"{ruta!r} está cortado: falta parte de {que}")
    return datos


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
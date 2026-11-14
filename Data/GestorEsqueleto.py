"""
GestorEsqueleto (Integrante 2): descarga el esqueleto completo de una cripta y lo
guarda como un grafo.

    - Nodos:   las salas (SalaDTO).
    - Aristas: sus salidas (SalidaDTO.sala_destino), en el array [N, S, E, O] de cada sala.

Estructura: un ARRAY (list) indexado por id de sala. La sala con id 4 está en
self._salas[4], así que obtenerla cuesta O(1). Las posiciones que no corresponden a
ninguna sala quedan en None. Es la estructura que sugiere la Guía (§3.2): una list
usada como almacenamiento contiguo, no un dict como tabla de búsqueda.

Depende de la interfaz FuenteDatos, no de FuenteRed: funciona igual con la red o
con el modo --offline.

Solo valida FORMATO y coherencia de los datos (la única validación permitida en
Datos). Las reglas del juego (puertas, llaves, movimiento) son de la Lógica.
"""
from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from Data.ValidacionDatos import ErrorDatos, es_cierre_valido, es_costo_valido
from DTO.CriptaDTO import CriptaDTO
from DTO.Direcciones import DIRECCIONES
from DTO.SalaDTO import SalaDTO, SalidaDTO


class GestorEsqueleto:

    def __init__(self, fuente: FuenteDatos):
        self._fuente = fuente
        self._cripta: CriptaDTO | None = None
        self._salas: list[SalaDTO | None] = []   # índice = id de sala
        self._cantidad = 0

    # ------------------------------------------------------------ carga
    def cargar(self, cripta: CriptaDTO) -> None:
        """
        Descarga todas las páginas del esqueleto (una solicitud por página) y arma el grafo.
        Si los datos son incoherentes lanza ErrorRed y el gestor queda sin cargar. Si un costo o un
        cierre_automatico es inválido (FR-122) lanza ErrorDatos, que también es un ErrorRed: la partida no inicia.
        """
        if cripta.paginas < 1:
            raise ErrorRed(self._op(cripta), f"la cripta declara {cripta.paginas} páginas")

        # 1) Reunir las salas de todas las páginas, en el orden en que llegan.
        recibidas: list[SalaDTO] = []
        for pagina in range(1, cripta.paginas + 1):
            for sala in self._fuente.obtener_pagina_salas(cripta.id, pagina, cripta.version):
                recibidas.append(sala)

        # 2) Ubicar cada sala en el array según su id y 3) validar el grafo.
        salas = self._indexar(cripta, recibidas)
        self._validar(cripta, salas, len(recibidas))
        self._validar_costos(cripta, salas)

        # Solo se reemplaza el estado cuando todo es válido.
        self._cripta = cripta
        self._salas = salas
        self._cantidad = len(recibidas)

    def esta_cargado(self) -> bool:
        return self._cripta is not None

    # ------------------------------------------------------------ consultas
    def obtener_sala(self, id_sala: int) -> SalaDTO | None:
        """O(1). None si no existe una sala con ese id."""
        if 0 <= id_sala < len(self._salas):
            return self._salas[id_sala]
        return None

    def existe_sala(self, id_sala: int) -> bool:
        return self.obtener_sala(id_sala) is not None

    def vecinos(self, id_sala: int) -> list[int]:
        """
        Ids de las salas a las que se llega directamente desde id_sala, en orden N, S, E, O.
        Incluye las salidas cerradas: para decidir qué precargar importa la cercanía,
        no si la puerta está abierta en este momento. O(1): a lo sumo 4 salidas.
        """
        sala = self._sala_existente(id_sala)
        resultado = []
        for salida in sala.salidas:
            if salida is not None:
                resultado.append(salida.sala_destino)
        return resultado

    def ids_salas(self) -> list[int]:
        """Todos los ids en orden creciente. O(tamaño del array), sin ordenar nada."""
        resultado = []
        for i in range(len(self._salas)):
            if self._salas[i] is not None:
                resultado.append(i)
        return resultado

    def cantidad_salas(self) -> int:
        return self._cantidad

    def cripta(self) -> CriptaDTO | None:
        return self._cripta

    # ------------------------------------------------------------ actualización
    def actualizar_sala(self, sala: SalaDTO) -> None:
        """
        Reemplaza el SalaDTO guardado por uno nuevo de la MISMA sala; por ejemplo, el que
        devuelve sala.con_contenido(...) cuando GestorContenido recibe su contenido. O(1).
        No se aceptan cambios en el esqueleto (nombre o salidas): eso no es contenido.
        """
        actual = self._sala_existente(sala.id)
        if sala.nombre != actual.nombre or sala.salidas != actual.salidas or sala.version != actual.version:
            raise ValueError(f"La sala {sala.id} no coincide con el esqueleto cargado")
        self._salas[sala.id] = sala

    # ------------------------------------------------------------ auxiliares
    def _indexar(self, cripta: CriptaDTO, recibidas: list[SalaDTO]) -> list[SalaDTO | None]:
        op = self._op(cripta)
        if len(recibidas) == 0:
            raise ErrorRed(op, "el esqueleto no trae ninguna sala")
        maximo = 0
        for sala in recibidas:
            if sala.id < 0:
                raise ErrorRed(op, f"id de sala negativo: {sala.id}")
            if sala.id > maximo:
                maximo = sala.id
        salas: list[SalaDTO | None] = [None] * (maximo + 1)
        for sala in recibidas:
            if salas[sala.id] is not None:
                raise ErrorRed(op, f"la sala {sala.id} aparece repetida en el esqueleto")
            salas[sala.id] = sala
        return salas

    @staticmethod
    def _validar(cripta: CriptaDTO, salas: list[SalaDTO | None], cantidad: int) -> None:
        op = GestorEsqueleto._op(cripta)
        if cantidad != cripta.salas_total:
            raise ErrorRed(op, f"la cripta declara {cripta.salas_total} salas y el esqueleto trae {cantidad}")
        for id_especial, nombre in ((cripta.sala_inicial, "sala_inicial"), (cripta.sala_salida, "sala_salida")):
            if not (0 <= id_especial < len(salas)) or salas[id_especial] is None:
                raise ErrorRed(op, f"{nombre} = {id_especial} no existe en el esqueleto")
        for sala in salas:
            if sala is None:
                continue
            for salida in sala.salidas:
                if salida is None:
                    continue
                destino = salida.sala_destino
                # "Cada salida conecta exactamente dos salas" (enunciado §2.1).
                if destino == sala.id:
                    raise ErrorRed(op, f"la sala {sala.id} tiene una salida hacia sí misma")
                if not (0 <= destino < len(salas)) or salas[destino] is None:
                    raise ErrorRed(op, f"la sala {sala.id} tiene una salida a la sala {destino}, que no existe")

    @staticmethod
    def _validar_costos(cripta: CriptaDTO, salas: list[SalaDTO | None]) -> None:
        """
        FR-122 (T002 y T055), con el esqueleto completo y antes de iniciar la partida. Dos pasadas, para que
        el mensaje sea siempre el del primer problema real:
          1. cada costo declarado es un entero >= 1, y cada cierre_automatico que venga también (T055);
          2. si los dos lados de una salida declaran costo, es el mismo (FR-101).
        El otro lado se busca igual que en Lógica (Mazmorra._salida_inversa): la primera salida de la sala
        destino, en orden N, S, E, O, que vuelve a la sala de origen. O(salas): a lo sumo 4 salidas por sala.
        """
        op = GestorEsqueleto._op(cripta)
        for sala in salas:
            if sala is None:
                continue
            for direccion in range(len(sala.salidas)):
                salida = sala.salidas[direccion]
                if salida is None:
                    continue
                if salida.costo is not None and not es_costo_valido(salida.costo):
                    raise ErrorDatos(op, f"la salida {DIRECCIONES[direccion]} de la sala {sala.id} declara "
                                         f"costo {salida.costo!r}: debe ser un entero >= 1")
                if not es_cierre_valido(salida.cierre_automatico):                       # T055
                    raise ErrorDatos(op, f"la salida {DIRECCIONES[direccion]} de la sala {sala.id} declara "
                                         f"cierre_automatico {salida.cierre_automatico!r}: debe ser un entero >= 1")
        for sala in salas:
            if sala is None:
                continue
            for direccion in range(len(sala.salidas)):
                salida = sala.salidas[direccion]
                if salida is None or salida.costo is None:
                    continue
                destino = salas[salida.sala_destino]
                assert destino is not None   # _validar ya comprobó que existe
                direccion_inversa = GestorEsqueleto._direccion_de_vuelta(destino, sala.id)
                if direccion_inversa is None:
                    continue   # salida de un solo sentido: su costo es el que declara
                inversa = destino.salidas[direccion_inversa]
                assert inversa is not None
                if inversa.costo is not None and inversa.costo != salida.costo:
                    raise ErrorDatos(op, f"la salida {DIRECCIONES[direccion]} de la sala {sala.id} declara costo "
                                         f"{salida.costo} y la salida {DIRECCIONES[direccion_inversa]} de la sala "
                                         f"{destino.id} declara costo {inversa.costo}: deben ser iguales")

    @staticmethod
    def _direccion_de_vuelta(sala: SalaDTO, origen: int) -> int | None:
        """Índice de la primera salida de 'sala' (N, S, E, O) que lleva a 'origen', o None."""
        for direccion in range(len(sala.salidas)):
            salida: SalidaDTO | None = sala.salidas[direccion]
            if salida is not None and salida.sala_destino == origen:
                return direccion
        return None

    def _sala_existente(self, id_sala: int) -> SalaDTO:
        sala = self.obtener_sala(id_sala)
        if sala is None:
            raise ValueError(f"No existe la sala {id_sala} en el esqueleto cargado")
        return sala

    @staticmethod
    def _op(cripta: CriptaDTO) -> str:
        return f"esqueleto de {cripta.id}"
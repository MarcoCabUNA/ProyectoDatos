"""
ResolvedorCatalogo (Integrante 2): resolución de referencias del catálogo (enunciado §4.3),
usando la caché en memoria (CacheCatalogo) y la caché en disco (AlmacenCatalogo) de §4.4.

Qué exige el enunciado y cómo se cumple:
  - "Antes de mostrar o simular una entidad, su id de tipo -> resolver_contenido() se llama apenas llega
     debe resolverse a una ficha de catálogo."                 el contenido de las salas (GestorContenido
                                                               lo hace solo), y ficha(id) nunca devuelve None.
  - "Pedir cada id por separado no cumple el presupuesto."  -> los ids que faltan se piden en lotes de
                                                               hasta 10 (un /catalogo cuesta lo mismo con 1 o 10).
  - "Los ids se descubren en orden no controlado, se       -> se quitan repetidos y se buscan primero en
     repiten entre salas y pueden reutilizarse entre          memoria y luego en disco (que se comparte entre
     criptas."                                                 criptas: el catálogo es uno solo).
  - "Un mismo id vigente no debe solicitarse dos veces si  -> solo va a la red un id que no está ni en memoria
     ya está en memoria o en almacenamiento persistente."      ni en disco; todo lo descargado se guarda en disco.

Orden de búsqueda de una ficha:   memoria (O(log n))  ->  disco (1 lectura)  ->  red (1 solicitud por lote)

Lo que sueltan los enemigos (campo 'suelta') también se resuelve: al descargar la ficha de un enemigo,
sus ids de 'suelta' que falten se agregan a la cola y salen en el siguiente lote. Así, cuando el
enemigo muere, el objeto que deja ya se puede mostrar sin ir a la red (COORDINAR de Marco en Enemigo).

Estructuras: Cola compartida (Estructuras/Cola.py) para los ids que faltan, en el orden en que se
descubren (determinista: salas en el orden recibido; en cada sala enemigos, trampas y objetos), y un
array 'vistos' para no repetir ids dentro de una misma resolución (búsqueda lineal: está acotado
por los ids de un lote de salas, unas decenas como mucho).

Cómo lo usa el resto del programa (lo llama Servicios; Lógica no conoce la capa de Datos):
  ficha(id)            -> la función fn_ficha que pide Mazmorra.cargar_contenido. Nunca devuelve None:
                          si no hay forma de obtenerla, lanza ErrorRed.
  marcar_en_uso(id) / liberar_uso(id)  -> fichas en uso de §4.4 (enemigo vivo, objeto en el inventario
                          o en el suelo de la sala actual, trampa de la sala actual).
  sincronizar_usos(ids) -> tras un retroceso (§4.6): la caché no se revierte (no es estado del juego),
                          así que las marcas de uso se rehacen a partir del estado restaurado.
"""
from Data.AlmacenCatalogo import CARPETA_POR_DEFECTO, AlmacenCatalogo
from Data.CacheCatalogo import TOPE_POR_DEFECTO, CacheCatalogo, Ficha
from Data.ClienteHttp import ErrorRed
from Data.FuenteDatos import FuenteDatos
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from Estructuras.Cola import Cola
from Security.ValidadorAcceso import es_nombre_seguro


class ResolvedorCatalogo:

    def __init__(self, fuente: FuenteDatos, cache: CacheCatalogo, almacen: AlmacenCatalogo):
        """Recibe las tres piezas ya armadas (las pruebas usan esto). En el juego se usa crear()."""
        self._fuente = fuente
        self._cache = cache
        self._almacen = almacen
        # Contadores para el reporte final y --bench.
        self._solicitudes_catalogo = 0
        self._fichas_descargadas = 0

    @classmethod
    def crear(cls, fuente: FuenteDatos, tope: int = TOPE_POR_DEFECTO,
              carpeta: str = CARPETA_POR_DEFECTO) -> "ResolvedorCatalogo":
        """
        Arma todo al iniciar el juego: consulta la versión del catálogo (UNA solicitud liviana,
        GET /catalogo/version), prepara el disco con esa versión (descarta lo de versiones viejas)
        y crea la caché en memoria con el tope de --cache-size.
        """
        version = fuente.obtener_version_catalogo()
        if not es_nombre_seguro(version):
            raise ErrorRed("versión del catálogo", f"versión con formato no válido: {version!r}")
        almacen = AlmacenCatalogo(version, carpeta)
        almacen.preparar()
        return cls(fuente, CacheCatalogo(tope), almacen)

    # ------------------------------------------------------------ resolver por adelantado
    def resolver_contenido(self, contenidos: list) -> int:
        """
        Recibe el contenido de varias salas (ContenidoSalaDTO o SalaDTO: los dos tienen enemigos,
        trampas y objetos) y deja disponibles todas las fichas que mencionan. Devuelve cuántas fichas
        tuvo que descargar (0 si ya estaba todo en memoria o en disco).
        """
        ids: list[str] = []
        for sala in contenidos:
            for enemigo in sala.enemigos:
                ids.append(enemigo.tipo)
            for trampa in sala.trampas:
                ids.append(trampa.tipo)
            for id_objeto in sala.objetos:
                ids.append(id_objeto)
        return self.resolver(ids)

    def resolver(self, ids: list[str]) -> int:
        """
        Deja disponibles (en memoria o en disco) las fichas de esos ids y de lo que sueltan los
        enemigos descargados. Pide a la red solo las que faltan, en lotes de hasta 10.
        Devuelve cuántas descargó. Si la red falla, lo ya descargado queda guardado y el error sigue.
        """
        pendientes = Cola()
        vistos: list[str] = []
        for id_ficha in ids:
            self._encolar_si_falta(id_ficha, pendientes, vistos)
        return len(self._descargar(pendientes, vistos))

    # ------------------------------------------------------------ usar una ficha
    def ficha(self, id_ficha: str, contar_acierto: bool = True) -> Ficha:
        """
        La ficha de ese id. NUNCA devuelve None (lo pide Mazmorra.cargar_contenido):
          1. memoria: acierto de caché, O(log n);
          2. disco: fallo de caché + una lectura de disco; queda en memoria;
          3. red: fallo de caché + una solicitud (con lo que suelte, si es enemigo).
        Si la red tampoco puede darla, lanza ErrorRed.
        contar_acierto=False: para Servicios cuando arma el estado de la Vista (objetos del suelo en
        cada turno). Así esas consultas repetidas no inflan los aciertos del reporte; si la ficha no
        está en memoria, el fallo sí cuenta porque implica trabajo real (disco o red).
        """
        en_memoria = self._cache.obtener(id_ficha, contar_acierto)
        if en_memoria is not None:
            return en_memoria
        en_disco = self._almacen.leer(id_ficha)
        if en_disco is not None:
            self._cache.insertar(en_disco)
            return en_disco
        pendientes = Cola()
        vistos: list[str] = []
        self._encolar_si_falta(id_ficha, pendientes, vistos)
        for descargada in self._descargar(pendientes, vistos):
            if descargada.id == id_ficha:
                return descargada
        # obtener_catalogo ya valida que la respuesta traiga todos los ids pedidos.
        raise ErrorRed(f"ficha {id_ficha}", "el catálogo no devolvió la ficha pedida")

    def marcar_en_uso(self, id_ficha: str) -> None:
        """Una instancia más usa la ficha. Si se había liberado de memoria, primero se recupera."""
        if not self._cache.contiene(id_ficha):
            self.ficha(id_ficha)
        self._cache.marcar_en_uso(id_ficha)

    def liberar_uso(self, id_ficha: str) -> None:
        """Una instancia dejó de usar la ficha (una ficha en uso nunca sale de memoria)."""
        self._cache.liberar_uso(id_ficha)

    def sincronizar_usos(self, ids_en_uso: list[str]) -> list[str]:
        """
        Tras un retroceso: deja como "en uso" EXACTAMENTE las fichas de 'ids_en_uso' (un id repetido
        cuenta una vez por instancia: dos ratas vivas = dos usos). Servicios arma la lista con el estado
        ya restaurado: enemigos vivos, inventario, objetos en el suelo y trampas de la sala actual.
          1. todos los usos a 0, sin liberar nada todavía;
          2. se marcan primero las que siguen en memoria (sin costo de disco);
          3. luego las que habían salido de memoria (una lectura de disco cada una);
          4. recién al final se libera lo que sobre del tope.
        Así ninguna ficha que se va a marcar se desaloja en medio. Devuelve los ids liberados.
        """
        self._cache.reiniciar_usos()
        faltantes: list[str] = []
        for id_ficha in ids_en_uso:
            if self._cache.contiene(id_ficha):
                self._cache.marcar_en_uso(id_ficha)
            else:
                faltantes.append(id_ficha)
        for id_ficha in faltantes:
            self.marcar_en_uso(id_ficha)
        return self._cache.ajustar_al_tope()

    # ------------------------------------------------------------ contadores (reporte y --bench)
    def aciertos(self) -> int:
        return self._cache.aciertos()

    def fallos(self) -> int:
        return self._cache.fallos()

    def lecturas_disco(self) -> int:
        return self._almacen.lecturas()

    def solicitudes_catalogo(self) -> int:
        """Solicitudes a /catalogo (no incluye la de la versión)."""
        return self._solicitudes_catalogo

    def fichas_descargadas(self) -> int:
        return self._fichas_descargadas

    def version_catalogo(self) -> str:
        return self._almacen.version()

    # ------------------------------------------------------------ auxiliares
    def _encolar_si_falta(self, id_ficha: str, pendientes: Cola, vistos: list[str]) -> None:
        """Encola el id si no se vio ya en esta resolución y no está en memoria ni en disco."""
        if not es_nombre_seguro(id_ficha):
            raise ErrorRed("resolver catálogo", f"id de ficha con formato no válido: {id_ficha!r}")
        for visto in vistos:
            if visto == id_ficha:
                return
        vistos.append(id_ficha)
        if self._cache.contiene(id_ficha) or self._almacen.contiene(id_ficha):
            return
        pendientes.encolar(id_ficha)

    def _descargar(self, pendientes: Cola, vistos: list[str]) -> list[Ficha]:
        """
        Vacía la cola en lotes de hasta 10, en orden de llegada. Cada ficha recibida se guarda en
        disco (persistente) y en memoria; si es un enemigo, lo que suelta se agrega a la cola.
        """
        descargadas: list[Ficha] = []
        while not pendientes.esta_vacia():
            lote: list[str] = []
            while not pendientes.esta_vacia() and len(lote) < FuenteDatos.MAX_IDS_POR_CATALOGO:
                lote.append(pendientes.desencolar())
            fichas = self._fuente.obtener_catalogo(lote)    # ErrorRed sale de aquí tal cual
            self._solicitudes_catalogo += 1
            for ficha in fichas:
                self._almacen.guardar(ficha)
                self._cache.insertar(ficha)
                self._fichas_descargadas += 1
                descargadas.append(ficha)
                if isinstance(ficha, FichaEnemigoDTO):
                    for id_suelta in ficha.suelta:
                        self._encolar_si_falta(id_suelta, pendientes, vistos)
        return descargadas
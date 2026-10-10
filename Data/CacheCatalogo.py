"""
CacheCatalogo (Integrante 2): fichas del catálogo guardadas en MEMORIA, con tope (enunciado §4.4).

Qué exige el enunciado y cómo se cumple:
  - Tope configurable (--cache-size, 25 por defecto)      -> 'tope' del constructor.
  - Al llegar al tope se libera una ficha, justificando    -> se libera la usada hace más
    cuál                                                      tiempo (LRU), ver abajo.
  - Las fichas EN USO no se pueden liberar                 -> contador de usos por ficha; mientras
                                                              es > 0 la ficha sale de la lista de
                                                              candidatas a liberar.
  - "¿Está en caché?" es muy frecuente y su costo importa  -> búsqueda binaria, O(log n).

Estructuras (solo arrays y listas, por la restricción del curso: no dict, no tabla hash):
  _entradas   ARRAY ORDENADO por id. Cada posición es una _Entrada (ficha + usos + nodo).
              Buscar = búsqueda binaria O(log n). Insertar/quitar = búsqueda + correr
              elementos O(n); es aceptable porque solo pasa en un fallo o al liberar,
              mucho menos seguido que buscar, y n está acotado por el tope.
  _recientes  ListaDoble compartida (Estructuras/ListaDoble.py). Contiene SOLO las fichas que
              se pueden liberar (las que no están en uso), de la más reciente (cabeza) a la
              usada hace más tiempo (cola). Usar una ficha = mover su nodo al frente, O(1).
              Elegir cuál liberar = tomar la cola, O(1), sin recorrer ni saltarse fichas en uso.

Por qué LRU (la usada hace más tiempo): el jugador avanza por salas vecinas, así que las fichas
que acaba de usar (enemigos, objetos y trampas de la zona actual) son las que más probablemente
vuelva a necesitar; las que lleva más tiempo sin usar son de salas que ya quedaron atrás.
FIFO podría liberar una ficha que se está usando constantemente solo por ser antigua.

Caso límite (decisión del equipo, va en el Documento de Decisiones): si TODAS las fichas en
memoria están en uso y llega una nueva, no se puede liberar ninguna; la caché queda por encima del
tope temporalmente y vuelve a él en cuanto alguna deje de estar en uso (liberar_uso). La ficha recién
insertada nunca se libera en esa misma inserción: quien la insertó la va a usar enseguida.

Quién marca el uso (lo llama Servicios, porque Lógica no conoce la capa de Datos):
  marcar_en_uso(id) al aparecer un enemigo vivo, al recoger un objeto, y al entrar a una sala por cada
  objeto en el suelo y cada trampa; liberar_uso(id) cuando muere el enemigo, se suelta/consume el
  objeto o el jugador sale de la sala. Una ficha usada por dos instancias (dos ratas) cuenta 2 usos.

Esta clase es solo la parte EN MEMORIA. La persistencia en disco (paso 10) y la resolución de ids
contra la red (paso 9) se agregan encima: una ficha liberada de memoria debe seguir en disco.
"""
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from Estructuras.ListaDoble import ListaDoble, NodoDoble

Ficha = ObjetoDTO | FichaEnemigoDTO | FichaTrampaDTO

TOPE_POR_DEFECTO = 25


class _Entrada:
    """Una ficha en memoria. 'nodo' es su lugar en _recientes, o None mientras está en uso."""
    __slots__ = ("id", "ficha", "usos", "nodo")

    def __init__(self, ficha: Ficha):
        self.id: str = ficha.id
        self.ficha: Ficha = ficha
        self.usos = 0
        self.nodo: NodoDoble | None = None


class CacheCatalogo:

    def __init__(self, tope: int = TOPE_POR_DEFECTO):
        if tope < 1:
            raise ValueError("El tope de la caché (--cache-size) debe ser al menos 1")
        self._tope = tope
        self._entradas: list[_Entrada] = []   # ordenado por id (búsqueda binaria)
        self._recientes = ListaDoble()          # solo fichas que se pueden liberar
        # Contadores para el reporte final y --bench.
        self._aciertos = 0
        self._fallos = 0
        self._desalojos = 0

    # ------------------------------------------------------------ consultas
    def contiene(self, id_ficha: str) -> bool:
        """¿La ficha está en memoria? O(log n). No cuenta como acierto ni como fallo."""
        return self._buscar(id_ficha)[1]

    def obtener(self, id_ficha: str) -> Ficha | None:
        """
        La ficha si está en memoria (acierto), o None (fallo). O(log n).
        Un acierto la marca como la más reciente, salvo que esté en uso (no se puede liberar
        de todos modos, así que no está en la lista de candidatas).
        """
        posicion, encontrada = self._buscar(id_ficha)
        if not encontrada:
            self._fallos += 1
            return None
        self._aciertos += 1
        entrada = self._entradas[posicion]
        if entrada.nodo is not None:
            self._recientes.mover_al_frente(entrada.nodo)
        return entrada.ficha

    def esta_en_uso(self, id_ficha: str) -> bool:
        posicion, encontrada = self._buscar(id_ficha)
        return encontrada and self._entradas[posicion].usos > 0

    def tamano(self) -> int:
        return len(self._entradas)

    def tope(self) -> int:
        return self._tope

    def aciertos(self) -> int:
        return self._aciertos

    def fallos(self) -> int:
        return self._fallos

    def desalojos(self) -> int:
        return self._desalojos

    def ids_en_memoria(self) -> list[str]:
        """Copia de los ids en memoria, en orden alfabético (el orden del array). O(n)."""
        ids = []
        for entrada in self._entradas:
            ids.append(entrada.id)
        return ids

    # ------------------------------------------------------------ cambios
    def insertar(self, ficha: Ficha) -> list[str]:
        """
        Guarda la ficha en memoria como la más reciente. Si ya estaba, la reemplaza (mismo id).
        Si con eso se pasa del tope, libera las que hagan falta (LRU, nunca las que están en uso
        ni la recién insertada). Devuelve los ids liberados, en el orden en que salieron.
        """
        if not isinstance(ficha.id, str) or not ficha.id:
            raise ValueError("La ficha debe tener un id de texto no vacío")
        posicion, encontrada = self._buscar(ficha.id)
        if encontrada:
            entrada = self._entradas[posicion]
            entrada.ficha = ficha
            if entrada.nodo is not None:
                self._recientes.mover_al_frente(entrada.nodo)
            return []
        entrada = _Entrada(ficha)
        self._insertar_en(posicion, entrada)
        entrada.nodo = self._recientes.agregar_al_frente(entrada)
        return self._ajustar_al_tope(protegida=entrada)

    def marcar_en_uso(self, id_ficha: str) -> None:
        """
        Una instancia más usa esta ficha. Mientras tenga usos no se puede liberar. O(log n).
        La ficha debe estar en memoria (primero se obtiene o se inserta, después se marca).
        """
        entrada = self._entrada_existente(id_ficha)
        if entrada.usos == 0:
            assert entrada.nodo is not None
            self._recientes.eliminar(entrada.nodo)   # deja de ser candidata, O(1)
            entrada.nodo = None
        entrada.usos += 1

    def liberar_uso(self, id_ficha: str) -> list[str]:
        """
        Una instancia dejó de usar la ficha. Si ya nadie la usa, vuelve a ser candidata (como la
        más reciente) y, si la caché estaba por encima del tope, se libera lo que sobre.
        Devuelve los ids liberados de memoria.
        """
        entrada = self._entrada_existente(id_ficha)
        if entrada.usos == 0:
            raise ValueError(f"La ficha {id_ficha!r} no estaba en uso")
        entrada.usos -= 1
        if entrada.usos > 0:
            return []
        entrada.nodo = self._recientes.agregar_al_frente(entrada)
        return self._ajustar_al_tope(protegida=None)

    # ------------------------------------------------------------ desalojo (LRU)
    def _ajustar_al_tope(self, protegida: _Entrada | None) -> list[str]:
        """Libera desde la cola de _recientes mientras haya más fichas que el tope."""
        liberadas: list[str] = []
        while len(self._entradas) > self._tope:
            nodo = self._recientes.cola
            if nodo is None or nodo.dato is protegida:
                break   # todo lo demás está en uso: se queda por encima del tope
            victima: _Entrada = self._recientes.eliminar(nodo)
            victima.nodo = None
            posicion, encontrada = self._buscar(victima.id)
            assert encontrada
            self._quitar_en(posicion)
            self._desalojos += 1
            liberadas.append(victima.id)
        return liberadas

    # ------------------------------------------------------------ array ordenado
    def _buscar(self, id_ficha: str) -> tuple[int, bool]:
        """
        Búsqueda binaria. Devuelve (posición, True) si está, o (posición donde debería
        insertarse para mantener el orden, False) si no está. O(log n).
        """
        inicio = 0
        fin = len(self._entradas) - 1
        while inicio <= fin:
            medio = (inicio + fin) // 2
            actual = self._entradas[medio].id
            if actual == id_ficha:
                return medio, True
            if actual < id_ficha:
                inicio = medio + 1
            else:
                fin = medio - 1
        return inicio, False

    def _insertar_en(self, posicion: int, entrada: _Entrada) -> None:
        """Abre un espacio en 'posicion' corriendo a la derecha los de después. O(n)."""
        self._entradas.append(entrada)   # crece el array en 1 (el valor se sobrescribe si hace falta)
        i = len(self._entradas) - 1
        while i > posicion:
            self._entradas[i] = self._entradas[i - 1]
            i -= 1
        self._entradas[posicion] = entrada

    def _quitar_en(self, posicion: int) -> None:
        """Cierra el espacio de 'posicion' corriendo a la izquierda los de después. O(n)."""
        for i in range(posicion, len(self._entradas) - 1):
            self._entradas[i] = self._entradas[i + 1]
        self._entradas.pop()   # quita la última casilla (ya copiada), O(1)

    def _entrada_existente(self, id_ficha: str) -> _Entrada:
        posicion, encontrada = self._buscar(id_ficha)
        if not encontrada:
            raise ValueError(f"La ficha {id_ficha!r} no está en memoria")
        return self._entradas[posicion]
"""
Inventario (Lógica, Integrante 3): la mochila del jugador.

Usa la ListaDoble compartida (Estructuras/ListaDoble.py) para cumplir §4.5 del enunciado:
    - se recorre hacia adelante y hacia atrás desde una posición actual (el cursor),
    - soltar el objeto bajo el cursor cuesta O(1) esté donde esté,
    - equipar es mover el objeto al frente del orden real, también en O(1),
    - nunca se supera capacidad_maxima (CriptaDTO.inventario_max).

Cada nodo representa una INSTANCIA de objeto y guarda su ObjetoDTO (la ficha, que se comparte
entre instancias iguales, §2.7). Lo equipado se recuerda por nodo y no por id, así es
inequívoco aunque haya dos objetos iguales.

Reglas decididas aquí (a confirmar con el equipo):
    - Un objeto recogido se agrega al FINAL del orden real.
    - El cursor no da la vuelta: en los extremos siguiente()/anterior() devuelven False.
    - Al soltar, el cursor pasa al objeto siguiente; si no hay, al anterior; si no hay, a nada.
    - Al equipar, el cursor sigue al objeto (que queda al frente).
    - Solo se equipan las clases "arma" y "armadura". Equipar otra de la misma clase sustituye a
      la anterior, que permanece en el inventario. Soltar lo equipado lo desequipa.
    - ubicar(id) mueve el cursor a una instancia de ese id, prefiriendo una NO equipada
      (la de repuesto). Es el puente con AccionDTO, que identifica los objetos por id.
    - Si tiene historial (lo asigna el Motor), recoger, soltar y equipar registran cómo
      deshacerse. Los pergaminos de retroceso no se registran (§2.11). Mover el cursor no es
      una acción del jugador, así que tampoco se registra.

Costos (n <= capacidad_maxima, un número pequeño):
    recoger, soltar_actual, equipar_actual, siguiente, anterior    O(1)
    ubicar, tiene_objeto, posicion_cursor, objetos                 O(n)

No conoce a Jugador, Mazmorra ni Motor: solo guarda objetos. Quien orquesta (Servicios)
decide qué hacer con lo que devuelve, por ejemplo poner en el suelo lo que se suelta.
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""

from Estructuras.ListaDoble import ListaDoble
from Logic.Ordenador import Ordenador



def _por_peso(a, b) -> int:
    return Ordenador.comparar(a.peso, b.peso)


def _por_valor(a, b) -> int:
    return Ordenador.comparar(a.valor, b.valor)


def _por_nombre(a, b) -> int:
    return Ordenador.comparar(a.nombre.casefold(), b.nombre.casefold())   # sin distinguir mayúsculas


class Inventario:

    def __init__(self, capacidad_maxima: int):
        if capacidad_maxima < 1:
            raise ValueError("la capacidad máxima del inventario debe ser al menos 1")
        self._capacidad_maxima = capacidad_maxima
        self._lista = ListaDoble()
        self._cursor = None  # nodo que el jugador está viendo (None si está vacío)
        self._nodo_arma = None  # nodo del arma equipada (None si no hay)
        self._nodo_armadura = None  # nodo de la armadura equipada (None si no hay)
        self.historial = None  # HistorialRetroceso del Motor (None = no se registra nada)

    # ---- Estado ----

    def cantidad(self) -> int:
        return self._lista.tamano()

    def capacidad_maxima(self) -> int:
        return self._capacidad_maxima

    def esta_vacio(self) -> bool:
        return self._lista.esta_vacia()

    def esta_lleno(self) -> bool:
        return self._lista.tamano() >= self._capacidad_maxima

    # ---- Cambios ----

    def recoger(self, objeto):
        """Agrega 'objeto' (un ObjetoDTO) al final. Devuelve su nodo, o None si está lleno."""
        if self.esta_lleno():
            return None
        punteros = self._punteros()
        nodo = self._lista.agregar_al_final(objeto)
        self._registrar(objeto, lambda: self._deshacer_recoger(nodo, punteros))
        if self._cursor is None:  # primer objeto: el cursor lo ve
            self._cursor = nodo
        return nodo

    def soltar_actual(self):
        """Quita el objeto bajo el cursor y lo devuelve (None si está vacío).
        También sirve para consumir un objeto: quien llama decide qué hacer con él."""
        nodo = self._cursor
        if nodo is None:
            return None
        punteros = self._punteros()
        anterior = nodo.anterior
        self._registrar(nodo.dato, lambda: self._deshacer_quitar(nodo, anterior, punteros))
        # Primero se decide el nuevo cursor: eliminar() borra los enlaces del nodo.
        self._cursor = nodo.siguiente if nodo.siguiente is not None else nodo.anterior
        if nodo is self._nodo_arma:
            self._nodo_arma = None
        if nodo is self._nodo_armadura:
            self._nodo_armadura = None
        return self._lista.eliminar(nodo)

    def equipar_actual(self) -> bool:
        """Equipa el objeto bajo el cursor y lo mueve al frente. False si no hay objeto o si
        no es un arma ni una armadura (no cambia nada)."""
        nodo = self._cursor
        if nodo is None:
            return False
        clase = nodo.dato.clase
        if clase == "arma" or clase == "armadura":
            punteros = self._punteros()
            anterior = nodo.anterior
            self._registrar(nodo.dato, lambda: self._deshacer_equipar(nodo, anterior, punteros))
        if clase == "arma":
            self._nodo_arma = nodo
        elif clase == "armadura":
            self._nodo_armadura = nodo
        else:
            return False
        self._lista.mover_al_frente(nodo)
        return True

    # ---- Recorrido ----

    def siguiente(self) -> bool:
        """Mueve el cursor un lugar hacia la cola. False si no se pudo (extremo o vacío)."""
        if self._cursor is None or self._cursor.siguiente is None:
            return False
        self._cursor = self._cursor.siguiente
        return True

    def anterior(self) -> bool:
        """Mueve el cursor un lugar hacia la cabeza. False si no se pudo (extremo o vacío)."""
        if self._cursor is None or self._cursor.anterior is None:
            return False
        self._cursor = self._cursor.anterior
        return True

    def ubicar(self, id_objeto: str) -> bool:
        """Mueve el cursor a una instancia con ese id, prefiriendo una no equipada.
        False si no hay ninguna (el cursor no cambia)."""
        nodo = self._buscar(id_objeto, evitar_equipados=True)
        if nodo is None:
            return False
        self._cursor = nodo
        return True

    # ---- Consulta ----

    def objeto_actual(self):
        """El ObjetoDTO bajo el cursor, o None si está vacío."""
        return None if self._cursor is None else self._cursor.dato

    def posicion_cursor(self) -> int:
        """Índice del cursor en el orden real (0 si está vacío)."""
        posicion = 0
        actual = self._lista.cabeza
        while actual is not None and actual is not self._cursor:
            posicion += 1
            actual = actual.siguiente
        return posicion if actual is not None else 0

    def tiene_objeto(self, id_objeto: str) -> bool:
        """True si hay al menos una instancia con ese id. No consume nada (las llaves se conservan)."""
        return self._buscar(id_objeto, evitar_equipados=False) is not None

    def arma_equipada(self):
        return None if self._nodo_arma is None else self._nodo_arma.dato

    def armadura_equipada(self):
        return None if self._nodo_armadura is None else self._nodo_armadura.dato

    def objetos(self) -> list:
        """Copia en un array del orden real. Ordenar la copia no altera el inventario."""
        return self._lista.a_array()

    def vista_ordenada(self, criterio) -> list:
        """Copia ordenada de forma ascendente por 'peso', 'valor' o 'nombre' (None = orden real).
        Los empates conservan el orden real (el ordenamiento es estable). No altera el inventario."""
        if criterio is None:
            return self.objetos()
        if criterio == "peso":
            comparador = _por_peso
        elif criterio == "valor":
            comparador = _por_valor
        elif criterio == "nombre":
            comparador = _por_nombre
        else:
            raise ValueError(f"criterio de orden desconocido: {criterio!r} (se esperaba peso, valor o nombre)")
        return Ordenador.ordenar(self.objetos(), comparador)

    # ---- Interno ----

    def _registrar(self, objeto, deshacer) -> None:
        if self.historial is not None and objeto.clase != "pergamino_retroceso":
            self.historial.registrar_cambio(deshacer)

    def _punteros(self):
        return self._cursor, self._nodo_arma, self._nodo_armadura

    def _restaurar_punteros(self, punteros) -> None:
        cursor, self._nodo_arma, self._nodo_armadura = punteros
        # el cursor pudo apuntar a un pergamino que ya no está (esos cambios no se deshacen)
        self._cursor = cursor if self._lista.contiene(cursor) else self._lista.cabeza

    def _deshacer_recoger(self, nodo, punteros) -> None:
        self._lista.eliminar(nodo)
        self._restaurar_punteros(punteros)

    def _deshacer_quitar(self, nodo, anterior, punteros) -> None:
        # si el vecino era un pergamino que ya no está, el objeto vuelve al frente
        self._lista.insertar_despues(nodo, anterior if self._lista.contiene(anterior) else None)
        self._restaurar_punteros(punteros)

    def _deshacer_equipar(self, nodo, anterior, punteros) -> None:
        self._lista.eliminar(nodo)
        self._deshacer_quitar(nodo, anterior, punteros)

    def _esta_equipado(self, nodo) -> bool:
        return nodo is self._nodo_arma or nodo is self._nodo_armadura

    def _buscar(self, id_objeto: str, evitar_equipados: bool):
        """Primer nodo con ese id desde la cabeza. Con evitar_equipados, un nodo equipado solo se
        devuelve si no hay otro igual sin equipar."""
        respaldo = None
        actual = self._lista.cabeza
        while actual is not None:
            if actual.dato.id == id_objeto:
                if not (evitar_equipados and self._esta_equipado(actual)):
                    return actual
                if respaldo is None:
                    respaldo = actual
            actual = actual.siguiente
        return respaldo
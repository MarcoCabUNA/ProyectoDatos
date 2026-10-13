"""
BenchInventario (Integrante 3): mediciones de inventario, historial, bitácora en pantalla y
ordenamiento para --bench (§5.3 y Documento de Decisiones, secciones 4.5, 4.6, 4.8 y 4.9).

Todas usan cargas SINTÉTICAS generadas aquí (sin red y sin datos de una cripta específica, §9). Cada
medición compara la estructura elegida contra la ALTERNATIVA DESCARTADA haciendo EL MISMO TRABAJO LÓGICO
(las pruebas lo verifican), que es lo que pide §8 punto 5:

  1. medir_estructura    4.5  ListaDoble contra array: quitar y reponer el del medio, mover el último al
                              frente (equipar) y recorrer. El array usa list.pop/insert (memmove en C), que
                              es la versión MÁS rápida posible del array: si la lista gana, gana a pesar de eso.
  2. medir_inventario    4.5  La clase Inventario tal como la usa el juego: recoger, soltar_actual,
                              equipar_actual, ubicar por id, recorrer y vista ordenada. Su alternativa
                              descartada es la del grupo 1 (el array), así que aquí no se repite.
  3. medir_historial     4.6  HistorialRetroceso (guarda cómo invertir cada cambio) contra guardar una
                              copia completa del estado en cada acción (lo que el enunciado prohíbe).
  4. medir_buffer        4.8  BufferCircular contra un array al que se le quita el primero al pasar del
                              límite. Los mensajes SIEMPRE superan la capacidad: si no, el array nunca
                              desplazaría nada y la medición no diría nada.
  5. medir_ordenamiento  4.9  inserción, mezcla y automático con tamaños pequeños, datos casi ordenados,
                              dos tramos ordenados al revés (el límite conocido del Ordenador) y una
                              comparación costosa (casefold sobre texto).

El resultado NO siempre favorece lo elegido (por ejemplo, con pocos objetos el array le gana a la lista
doble). Esas filas se dejan tal cual: el documento debe contar el cruce, no esconderlo.

Los tiempos son totales de una "tanda" (varias operaciones juntas); la columna 'nota' dice cuántas.
Para que los ordenamientos pequeños no midan solo el ruido del reloj, se repiten hasta sumar unos
ELEMENTOS_POR_TANDA elementos por tanda. medir() corre todo con los tamaños por defecto; las pruebas
llaman a cada función con tamaños chicos.
"""
import random

from DTO.ObjetoDTO import ObjetoDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Estructuras.BufferCircular import BufferCircular
from Estructuras.ListaDoble import ListaDoble
from Estructuras.Ordenador import Ordenador
from Logic.HistorialRetroceso import HistorialRetroceso
from Logic.Inventario import Inventario
from Service.Cronometro import medir as cronometrar

SEMILLA = 2026                  # las cargas sintéticas son siempre las mismas: los resultados se pueden comparar
REPETICIONES = 15               # con 15 el mínimo es estable
ELEMENTOS_POR_TANDA = 1024      # los ordenamientos pequeños se repiten hasta sumar esta cantidad de elementos
REPETIR_HASTA_CAPACIDAD = 2000          # el buffer de más capacidad que esto se mide con menos repeticiones
REPETICIONES_CAPACIDAD_GRANDE = 5

_ALGORITMOS = (("inserción", Ordenador.ordenar_por_insercion),
               ("mezcla", Ordenador.ordenar_por_mezcla),
               ("automático", Ordenador.ordenar))


def medir() -> list[ResultadoBenchDTO]:
    """Todas las mediciones del integrante 3, con los tamaños por defecto."""
    return (medir_estructura() + medir_inventario() + medir_historial()
            + medir_buffer() + medir_ordenamiento())


# ====================================================================== 1. estructura del inventario
def medir_estructura(tamanos=(1000, 10000, 100000), operaciones: int = 200,
                     repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """ListaDoble contra array en las tres operaciones que el inventario necesita (§4.5)."""
    resultados = []
    for n in tamanos:
        lista = _lista_de(n)
        array = list(range(n))
        medio = _nodo_en(lista, n // 2)
        nota = f"{operaciones} operaciones por tanda"
        resultados += _comparar(
            "inventario (estructura)", "quitar y reponer el del medio", n, nota, repeticiones,
            ("ListaDoble", lambda: _quitar_y_reponer_lista(lista, medio, operaciones)),
            ("array (descartada)", lambda: _quitar_y_reponer_array(array, n // 2, operaciones)))
        resultados += _comparar(
            "inventario (estructura)", "mover el último al frente", n, nota, repeticiones,
            ("ListaDoble", lambda: _mover_ultimo_lista(lista, operaciones)),
            ("array (descartada)", lambda: _mover_ultimo_array(array, operaciones)))
        resultados += _comparar(
            "inventario (estructura)", "recorrer todo", n, f"1 recorrido de {n} elementos", repeticiones,
            ("ListaDoble", lambda: _recorrer_lista(lista)),
            ("array (descartada)", lambda: _recorrer_array(array)))
    return resultados


def _lista_de(n: int) -> ListaDoble:
    lista = ListaDoble()
    for i in range(n):
        lista.agregar_al_final(i)
    return lista


def _nodo_en(lista: ListaDoble, posicion: int):
    """El nodo (el 'mango') que está en esa posición. Se busca UNA vez, fuera del cronómetro."""
    nodo = lista.cabeza
    for _ in range(posicion):
        nodo = nodo.siguiente
    return nodo


def _quitar_y_reponer_lista(lista: ListaDoble, nodo, operaciones: int) -> None:
    for _ in range(operaciones):
        anterior = nodo.anterior
        lista.eliminar(nodo)
        lista.insertar_despues(nodo, anterior)


def _quitar_y_reponer_array(array: list, posicion: int, operaciones: int) -> None:
    for _ in range(operaciones):
        objeto = array.pop(posicion)
        array.insert(posicion, objeto)


def _mover_ultimo_lista(lista: ListaDoble, operaciones: int) -> None:
    for _ in range(operaciones):
        lista.mover_al_frente(lista.cola)


def _mover_ultimo_array(array: list, operaciones: int) -> None:
    for _ in range(operaciones):
        array.insert(0, array.pop())


def _recorrer_lista(lista: ListaDoble) -> int:
    cuenta = 0
    actual = lista.cabeza
    while actual is not None:
        cuenta += 1
        actual = actual.siguiente
    return cuenta


def _recorrer_array(array: list) -> int:
    cuenta = 0
    for i in range(len(array)):
        _ = array[i]
        cuenta += 1
    return cuenta


# ====================================================================== 2. la clase Inventario
def medir_inventario(capacidades=(10, 100, 1000), operaciones: int = 200,
                     repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Las operaciones de la clase Inventario. El tamaño es la capacidad (llena). 10 es la capacidad típica."""
    resultados = []
    for c in capacidades:
        objetos = _objetos(c)
        inventario = _inventario_lleno(objetos)         # para ubicar, recorrer y vista (nunca se equipa)
        ids = _ids_al_azar(objetos, operaciones)

        def fila(operacion, funcion, nota, preparar=None):
            mejor, mediana = cronometrar(funcion, repeticiones, preparar=preparar)
            resultados.append(ResultadoBenchDTO("inventario (clase)", f"Inventario: {operacion}",
                                                c, mejor, mediana, nota))

        fila("recoger", lambda vacio: _recoger_todos(vacio, objetos),
             f"{c} objetos hasta llenarlo", preparar=lambda: Inventario(c))
        fila("soltar_actual", _soltar_todos,
             f"{c} objetos hasta vaciarlo", preparar=lambda: _inventario_lleno(objetos))
        fila("equipar_actual", lambda lleno: _equipar_rotando(lleno, operaciones),
             f"{operaciones} veces siguiente() + equipar_actual()", preparar=lambda: _inventario_lleno(objetos))
        fila("ubicar por id", lambda: _ubicar_todos(inventario, ids),
             f"{operaciones} búsquedas")
        fila("recorrer ida y vuelta", lambda: _recorrer_ida_y_vuelta(inventario),
             f"{2 * (c - 1)} pasos del cursor")
        fila("vista_ordenada por nombre", lambda: inventario.vista_ordenada("nombre"),
             "1 vista (copia ordenada, no altera el orden real)")
    return resultados


def _objetos(cantidad: int) -> list[ObjetoDTO]:
    """Objetos sintéticos: armas y armaduras alternadas (se pueden equipar), pesos y valores al azar."""
    azar = random.Random(SEMILLA + cantidad)
    objetos = []
    for i in range(cantidad):
        es_arma = i % 2 == 0
        objetos.append(ObjetoDTO(
            id=f"obj_{i:06d}", nombre=_texto(azar.randrange(1000000)),
            clase="arma" if es_arma else "armadura",
            peso=azar.randrange(1, 50), valor=azar.randrange(1, 500),
            ataque_bonus=1 if es_arma else None, defensa_bonus=None if es_arma else 1))
    return objetos


def _inventario_lleno(objetos: list[ObjetoDTO]) -> Inventario:
    inventario = Inventario(len(objetos))
    _recoger_todos(inventario, objetos)
    return inventario


def _ids_al_azar(objetos: list[ObjetoDTO], cantidad: int) -> list[str]:
    azar = random.Random(SEMILLA)
    ids = []
    for _ in range(cantidad):
        ids.append(objetos[azar.randrange(len(objetos))].id)
    return ids


def _recoger_todos(inventario: Inventario, objetos: list[ObjetoDTO]) -> None:
    for objeto in objetos:
        inventario.recoger(objeto)


def _soltar_todos(inventario: Inventario) -> None:
    while not inventario.esta_vacio():
        inventario.soltar_actual()


def _equipar_rotando(inventario: Inventario, operaciones: int) -> None:
    """Avanza un lugar y equipa lo que ve: cada vez trae al frente el segundo objeto."""
    for _ in range(operaciones):
        inventario.siguiente()
        inventario.equipar_actual()


def _ubicar_todos(inventario: Inventario, ids: list[str]) -> None:
    for id_objeto in ids:
        inventario.ubicar(id_objeto)


def _recorrer_ida_y_vuelta(inventario: Inventario) -> None:
    while inventario.siguiente():
        pass
    while inventario.anterior():
        pass


# ====================================================================== 3. historial de retroceso
def medir_historial(tamanos=(1000, 10000, 100000), ciclos: int = 50, cambios: int = 5,
                    repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Una acción de 'cambios' cambios seguida de deshacer, 'ciclos' veces, sobre un estado de n valores."""
    resultados = []
    for n in tamanos:
        estado_h = list(range(n))
        estado_c = list(range(n))
        indices = _indices_de_cambio(n, cambios)
        historial = HistorialRetroceso()
        nota = (f"{ciclos} acciones de {cambios} cambios, cada una seguida de deshacer; "
                "la copia es de valores simples (con objetos reales costaría más)")
        resultados += _comparar(
            "historial", "acción + deshacer", n, nota, repeticiones,
            ("HistorialRetroceso", lambda: _ciclos_con_historial(estado_h, historial, indices, ciclos)),
            ("copia completa (descartada)", lambda: _ciclos_con_copia(estado_c, indices, ciclos)))
    return resultados


def _indices_de_cambio(n: int, cambios: int) -> list[int]:
    """Posiciones repartidas por todo el estado."""
    return [k * n // cambios for k in range(cambios)]


def _poner(estado: list, posicion: int, valor: int) -> None:
    estado[posicion] = valor


def _cambiar_registrando(estado: list, historial: HistorialRetroceso, posicion: int) -> None:
    """Registra ANTES cómo volver y luego cambia. Va en su propia función para que cada lambda guarde
    SU posición y SU valor anterior (en un bucle, todas compartirían la última: error clásico de Python)."""
    anterior = estado[posicion]
    historial.registrar_cambio(lambda: _poner(estado, posicion, anterior))
    estado[posicion] = anterior + 1


def _accion_con_historial(estado: list, historial: HistorialRetroceso, indices: list[int]) -> None:
    """Una acción del jugador: cambia cada posición registrando cómo volver, y cierra el intervalo (como el Motor)."""
    for i in indices:
        _cambiar_registrando(estado, historial, i)
    historial.cerrar_intervalo()


def _accion_con_copia(estado: list, indices: list[int]) -> list:
    """Guarda una copia COMPLETA y luego cambia. Devuelve la copia: 'deshacer' es volver a ella."""
    copia = list(estado)
    for i in indices:
        estado[i] += 1
    return copia


def _ciclos_con_historial(estado: list, historial: HistorialRetroceso, indices: list[int], ciclos: int) -> None:
    for _ in range(ciclos):
        _accion_con_historial(estado, historial, indices)
        historial.deshacer()


def _ciclos_con_copia(estado: list, indices: list[int], ciclos: int) -> list:
    for _ in range(ciclos):
        estado = _accion_con_copia(estado, indices)         # el estado vigente pasa a ser la copia
    return estado


# ====================================================================== 4. bitácora en pantalla
def medir_buffer(capacidades=(20, 200, 2000, 10000),
                 repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Agregar mensajes con el buffer lleno. Siempre hay más mensajes que capacidad (max(2000, 2 * capacidad))."""
    resultados = []
    for c in capacidades:
        textos = [f"mensaje {i}" for i in range(max(2000, 2 * c))]
        nota = f"{len(textos)} mensajes en un buffer de {c} (quedan los últimos {c})"
        reps = repeticiones
        if c > REPETIR_HASTA_CAPACIDAD:
            # el array que desplaza tarda cientos de ms por tanda: la diferencia es de ~100 veces,
            # así que unas pocas repeticiones bastan y el bench no se alarga varios segundos
            reps = min(repeticiones, REPETICIONES_CAPACIDAD_GRANDE)
            nota += f"; {reps} repeticiones"
        resultados += _comparar(
            "bitácora en pantalla", "agregar mensajes", c, nota, reps,
            ("BufferCircular", lambda: _llenar_circular(c, textos)),
            ("array que desplaza (descartada)", lambda: _llenar_desplazando(c, textos)))
    return resultados


def _llenar_circular(capacidad: int, textos: list[str]) -> BufferCircular:
    buffer = BufferCircular(capacidad)
    for texto in textos:
        buffer.agregar(texto)
    return buffer


def _llenar_desplazando(capacidad: int, textos: list[str]) -> list[str]:
    """La alternativa descartada: al pasar del límite se quita el primero y se corren todos los demás."""
    recientes = []
    for texto in textos:
        recientes.append(texto)
        if len(recientes) > capacidad:
            recientes.pop(0)
    return recientes


# ====================================================================== 5. ordenamiento
def medir_ordenamiento(tamanos_desordenados=(8, 16, 24, 32, 64, 128),
                       tamanos_casi_ordenados=(16, 32, 128, 512, 2048),
                       tamanos_dos_tramos=(64, 128, 256, 512, 1024),
                       repeticiones: int = REPETICIONES) -> list[ResultadoBenchDTO]:
    """Inserción, mezcla y automático en cuatro escenarios (los tres algoritmos ordenan LOS MISMOS datos)."""
    resultados = []
    for n in tamanos_desordenados:
        for costoso in (False, True):
            datos = _datos(_desordenados(n), costoso)
            comparador = _comparar_texto if costoso else Ordenador.comparar
            escenario = "desordenados, comparación " + ("costosa" if costoso else "barata")
            resultados += _filas_de_ordenamiento(escenario, n, datos, comparador, ELEMENTOS_POR_TANDA, repeticiones)
    for n in tamanos_casi_ordenados:
        resultados += _filas_de_ordenamiento("casi ordenados (2 % de pares cambiados)", n, _casi_ordenados(n),
                                             Ordenador.comparar, ELEMENTOS_POR_TANDA, repeticiones)
    for n in tamanos_dos_tramos:
        resultados += _filas_de_ordenamiento("dos tramos ordenados al revés", n, _dos_tramos_al_reves(n),
                                             Ordenador.comparar, 0, repeticiones)   # 0: una sola vez por tanda
    return resultados


def _filas_de_ordenamiento(escenario: str, n: int, datos: list, comparador, elementos_por_tanda: int,
                           repeticiones: int) -> list[ResultadoBenchDTO]:
    veces = max(1, elementos_por_tanda // n)
    eligio = Ordenador.elegir_algoritmo(datos, comparador)
    filas = []
    for nombre, algoritmo in _ALGORITMOS:
        mejor, mediana = cronometrar(lambda: _ordenar_varias_veces(algoritmo, datos, comparador, veces),
                                     repeticiones)
        nota = f"{veces} ordenamiento(s) por tanda"
        if nombre == "automático":
            nota += f"; eligió {'inserción' if eligio == 'insercion' else 'mezcla'}"
        filas.append(ResultadoBenchDTO("ordenamiento", f"{nombre}: {escenario}", n, mejor, mediana, nota))
    return filas


def _ordenar_varias_veces(algoritmo, datos: list, comparador, veces: int) -> None:
    for _ in range(veces):
        algoritmo(datos, comparador)


def _desordenados(n: int) -> list[int]:
    azar = random.Random(SEMILLA + n)
    return [azar.randrange(n * 10) for _ in range(n)]


def _casi_ordenados(n: int) -> list[int]:
    """0..n-1 en orden con un 2 % de pares vecinos intercambiados."""
    azar = random.Random(SEMILLA + n)
    datos = list(range(n))
    for _ in range(max(1, n * 2 // 100)):
        i = azar.randrange(n - 1)
        datos[i], datos[i + 1] = datos[i + 1], datos[i]
    return datos


def _dos_tramos_al_reves(n: int) -> list[int]:
    """Dos tramos ya ordenados pero el de los valores altos va primero. Pares vecinos fuera de orden: 1 solo."""
    mitad = n // 2
    return [mitad + i for i in range(n - mitad)] + [i for i in range(mitad)]


def _texto(numero: int) -> str:
    """Texto con mayúsculas y minúsculas mezcladas: casefold tiene trabajo que hacer. Conserva el orden numérico."""
    return f"ObJeTo {numero:06d}"


def _datos(numeros: list[int], costoso: bool) -> list:
    if not costoso:
        return numeros
    return [_texto(numero) for numero in numeros]


def _comparar_texto(a: str, b: str) -> int:
    """El comparador costoso: dos casefold por comparación (el mismo que usa Inventario para ordenar por nombre)."""
    return Ordenador.comparar(a.casefold(), b.casefold())


# ====================================================================== auxiliares
def _comparar(subsistema: str, operacion: str, tamano: int, nota: str, repeticiones: int,
              elegida, descartada) -> list[ResultadoBenchDTO]:
    """elegida y descartada son (nombre, funcion). Devuelve dos filas, la elegida primero."""
    filas = []
    for nombre, funcion in (elegida, descartada):
        mejor, mediana = cronometrar(funcion, repeticiones)
        filas.append(ResultadoBenchDTO(subsistema, f"{nombre}: {operacion}", tamano, mejor, mediana, nota))
    return filas
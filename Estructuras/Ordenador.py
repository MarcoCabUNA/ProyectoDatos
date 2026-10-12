"""
Ordenador (Estructuras, Integrante 3): ordenamiento propio con elección automática (§4.9).

Vive en Estructuras porque lo usan varias capas: Lógica (vistas del inventario y orden de
activación de enemigos), Servicios (tabla de puntajes) y Datos (índices del guardado y listas
del catálogo). Por eso no importa nada de ninguna capa.

Dos algoritmos con características distintas, ambos ESTABLES (los elementos iguales conservan
su orden original):

    insercion   en el sitio, sin memoria extra, muy rápido en listas pequeñas o casi ordenadas
                (cuesta n-1 comparaciones si ya está ordenada), pero cuadrático en el peor caso.
    mezcla      divide y mezcla, O(n log n) garantizado aunque los datos vengan al revés, usa un
                arreglo auxiliar de n elementos. Si dos mitades ya están en orden no las mezcla.

ordenar() elige según propiedades que se pueden medir de los datos:
    1. el tamaño n;
    2. el desorden: proporción de pares vecinos fuera de orden (cuesta n-1 comparaciones).
Regla:
    n <= UMBRAL_PEQUENO                                        -> insercion
    n <= UMBRAL_INSERCION_MAXIMO y desorden <= UMBRAL_DESORDEN -> insercion
    en cualquier otro caso                                     -> mezcla
Como los dos son estables, el resultado es IDÉNTICO sin importar cuál se elija: la elección
solo afecta al tiempo, nunca al orden resultante.

Evidencia (medición preliminar propia; el modo --bench debe reproducirla):
    - Hasta 12 elementos la inserción gana o empata con comparador barato y con uno costoso
      (texto con casefold). Con comparador costoso, desde 16 elementos gana la mezcla.
    - Datos casi ordenados (desorden <= 0.25, n <= 128): la inserción es de 2.5 a 3.8 veces
      más rápida que la mezcla. Con datos aleatorios (desorden ~0.5) gana la mezcla desde
      ~32-48 elementos (barato) y desde ~16 (costoso): hace 3 a 5 veces menos comparaciones.
    - Por encima de 128 se usa siempre mezcla: perder en datos casi ordenados cuesta unas 2.5
      veces (cientos de microsegundos a n=2048), mientras que el peor caso de la inserción es
      16 veces más lento a n=256 y 68 veces a n=1024.
Límite conocido: el desorden se mide con pares vecinos, así que no detecta dos tramos ya
ordenados pero puestos al revés (desorden ~0, pero muchas inversiones). El tope de tamaño acota
ese caso a ~0.25 ms (8 veces más lento que la mezcla a n=128).

Nunca modifica la lista recibida: devuelve una lista nueva (una "vista" ordenada).
El comparador recibe (a, b) y devuelve un entero negativo si a va antes que b, 0 si son
equivalentes y positivo si a va después.
No usa las funciones de ordenamiento integradas de Python (prohibido por el enunciado, §4.9).

Costos (n elementos):
    ordenar_por_insercion   O(n) casi ordenada ... O(n^2) peor caso, memoria O(n) por la copia
    ordenar_por_mezcla      O(n log n) siempre, n-1 comparaciones si ya está ordenada
    proporcion_de_desorden  O(n)
Regla del equipo: no cambiar los nombres de los métodos sin avisar a los demás.
"""


class Ordenador:
    UMBRAL_PEQUENO = 12             # hasta este tamaño siempre se usa inserción
    UMBRAL_INSERCION_MAXIMO = 128   # por encima de este tamaño siempre se usa mezcla
    UMBRAL_DESORDEN = 0.25          # hasta esta proporción de desorden conviene la inserción

    @staticmethod
    def comparar(a, b) -> int:
        """Comparador natural de Python: -1, 0 o 1."""
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    @staticmethod
    def ordenar(lista, comparador) -> list:
        """Devuelve una lista nueva ordenada, eligiendo el algoritmo automáticamente."""
        if Ordenador.elegir_algoritmo(lista, comparador) == "insercion":
            return Ordenador.ordenar_por_insercion(lista, comparador)
        return Ordenador.ordenar_por_mezcla(lista, comparador)

    @staticmethod
    def elegir_algoritmo(lista, comparador) -> str:
        """'insercion' o 'mezcla', según el tamaño y el desorden medido."""
        n = len(lista)
        if n <= Ordenador.UMBRAL_PEQUENO:
            return "insercion"                  # no vale la pena ni medir el desorden
        if n > Ordenador.UMBRAL_INSERCION_MAXIMO:
            return "mezcla"                     # acota el peor caso cuadrático de la inserción
        if Ordenador.proporcion_de_desorden(lista, comparador) <= Ordenador.UMBRAL_DESORDEN:
            return "insercion"
        return "mezcla"

    @staticmethod
    def proporcion_de_desorden(lista, comparador) -> float:
        """Fracción de pares vecinos fuera de orden: 0.0 ya ordenada, 1.0 completamente al revés."""
        if len(lista) < 2:
            return 0.0
        fuera_de_orden = 0
        for i in range(len(lista) - 1):
            if comparador(lista[i], lista[i + 1]) > 0:
                fuera_de_orden += 1
        return fuera_de_orden / (len(lista) - 1)

    @staticmethod
    def ordenar_por_insercion(lista, comparador) -> list:
        resultado = list(lista)
        for i in range(1, len(resultado)):
            actual = resultado[i]
            j = i - 1
            # '> 0' estricto: un elemento igual NO se adelanta, por eso es estable
            while j >= 0 and comparador(resultado[j], actual) > 0:
                resultado[j + 1] = resultado[j]
                j -= 1
            resultado[j + 1] = actual
        return resultado

    @staticmethod
    def ordenar_por_mezcla(lista, comparador) -> list:
        resultado = list(lista)
        if len(resultado) < 2:
            return resultado
        auxiliar = [None] * len(resultado)
        Ordenador._mezclar_tramo(resultado, auxiliar, 0, len(resultado), comparador)
        return resultado

    @staticmethod
    def _mezclar_tramo(datos, auxiliar, inicio, fin, comparador) -> None:
        """Ordena datos[inicio:fin] dividiéndolo en dos mitades y mezclándolas."""
        if fin - inicio < 2:
            return
        medio = (inicio + fin) // 2
        Ordenador._mezclar_tramo(datos, auxiliar, inicio, medio, comparador)
        Ordenador._mezclar_tramo(datos, auxiliar, medio, fin, comparador)
        if comparador(datos[medio - 1], datos[medio]) <= 0:
            return                              # las mitades ya están en orden entre sí
        for k in range(inicio, fin):
            auxiliar[k] = datos[k]
        i, j, k = inicio, medio, inicio
        while i < medio and j < fin:
            # solo pasa primero el de la derecha si es ESTRICTAMENTE menor: estable
            if comparador(auxiliar[j], auxiliar[i]) < 0:
                datos[k] = auxiliar[j]
                j += 1
            else:
                datos[k] = auxiliar[i]
                i += 1
            k += 1
        while i < medio:
            datos[k] = auxiliar[i]
            i += 1
            k += 1
        while j < fin:
            datos[k] = auxiliar[j]
            j += 1
            k += 1

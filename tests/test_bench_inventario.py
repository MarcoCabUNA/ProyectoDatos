import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from Estructuras.ListaDoble import ListaDoble
from Estructuras.Ordenador import Ordenador
from Logic.HistorialRetroceso import HistorialRetroceso
from Logic.Inventario import Inventario
from Service import BenchInventario as B

NOMBRES_ALGORITMOS = ["inserción", "mezcla", "automático"]


# ---------------------------------------------------------------- ayudas
def _revisar(resultados, subsistema, cantidad):
    assert len(resultados) == cantidad, (len(resultados), cantidad)
    for r in resultados:
        assert isinstance(r, ResultadoBenchDTO)
        assert r.subsistema == subsistema, r
        assert 0 <= r.mejor_ms <= r.mediana_ms, r
        assert r.nota != ""


class _ListaEspia(ListaDoble):
    """Cuenta cuántas veces se usa cada operación: así se sabe que SÍ se hizo el trabajo."""

    def __init__(self):
        super().__init__()
        self.quitados = 0
        self.repuestos = 0
        self.movidos = 0

    def eliminar(self, nodo):
        self.quitados += 1
        return super().eliminar(nodo)

    def insertar_despues(self, nodo, anterior):
        self.repuestos += 1
        super().insertar_despues(nodo, anterior)

    def mover_al_frente(self, nodo):
        self.movidos += 1
        super().mover_al_frente(nodo)


class _ArrayEspia(list):
    def __init__(self, *args):
        super().__init__(*args)
        self.quitados = 0
        self.repuestos = 0

    def pop(self, *args):
        self.quitados += 1
        return super().pop(*args)

    def insert(self, posicion, objeto):
        self.repuestos += 1
        super().insert(posicion, objeto)


def _lista_espia(n):
    lista = _ListaEspia()
    for i in range(n):
        lista.agregar_al_final(i)
    return lista


def _esta_ascendente(datos, comparador):
    for i in range(len(datos) - 1):
        if comparador(datos[i], datos[i + 1]) > 0:
            return False
    return True


def _es_permutacion_de_rango(datos):
    n = len(datos)
    vistos = [False] * n
    for x in datos:
        if x < 0 or x >= n or vistos[x]:
            return False
        vistos[x] = True
    return True


# ---------------------------------------------------------------- 1. estructura
def probar_estructura_forma_de_las_filas():
    r = B.medir_estructura(tamanos=(10, 50), operaciones=5, repeticiones=2)
    _revisar(r, "inventario (estructura)", 12)                  # 3 operaciones x 2 casos x 2 tamaños
    assert [x.tamano for x in r] == [10] * 6 + [50] * 6
    operaciones = ["quitar y reponer el del medio", "mover el último al frente", "recorrer todo"]
    for i in range(6):
        operacion = operaciones[i // 2]
        elegida = "ListaDoble" if i % 2 == 0 else "array (descartada)"   # la elegida siempre primero
        assert r[i].caso == f"{elegida}: {operacion}", r[i].caso


def probar_estructura_quitar_y_reponer_hace_el_mismo_trabajo():
    n, operaciones = 11, 7
    lista = _lista_espia(n)
    medio = B._nodo_en(lista, n // 2)
    assert medio.dato == n // 2
    B._quitar_y_reponer_lista(lista, medio, operaciones)
    assert lista.quitados == lista.repuestos == operaciones
    assert lista.a_array() == list(range(n)) and lista.contiene(medio)

    array = _ArrayEspia(range(n))
    B._quitar_y_reponer_array(array, n // 2, operaciones)
    assert array.quitados == array.repuestos == operaciones
    assert list(array) == list(range(n))


def probar_estructura_quitar_y_reponer_funciona_en_los_extremos_del_tamano():
    for n in (2, 3):
        lista = _lista_espia(n)
        B._quitar_y_reponer_lista(lista, B._nodo_en(lista, n // 2), 4)
        assert lista.a_array() == list(range(n))


def probar_estructura_mover_el_ultimo_deja_el_mismo_orden_en_ambas():
    n = 6
    for operaciones in (1, 2, 5, 6, 13):
        lista = _lista_espia(n)
        array = list(range(n))
        B._mover_ultimo_lista(lista, operaciones)
        B._mover_ultimo_array(array, operaciones)
        assert lista.movidos == operaciones
        assert lista.a_array() == array, operaciones
        assert lista.tamano() == n
    una = _lista_espia(n)
    B._mover_ultimo_lista(una, 1)
    assert una.a_array() == [5, 0, 1, 2, 3, 4]                   # el trabajo es real: cambió el orden


def probar_estructura_recorrer_cuenta_todo():
    for n in (1, 2, 50):
        lista = _lista_espia(n)
        assert B._recorrer_lista(lista) == B._recorrer_array(list(range(n))) == n


# ---------------------------------------------------------------- 2. clase Inventario
def probar_inventario_forma_de_las_filas():
    r = B.medir_inventario(capacidades=(5, 12), operaciones=6, repeticiones=2)
    _revisar(r, "inventario (clase)", 12)
    operaciones = ["recoger", "soltar_actual", "equipar_actual", "ubicar por id",
                   "recorrer ida y vuelta", "vista_ordenada por nombre"]
    for i in range(12):
        assert r[i].caso == f"Inventario: {operaciones[i % 6]}", r[i].caso
        assert r[i].tamano == (5 if i < 6 else 12)
    assert "5 objetos" in r[0].nota and "6 búsquedas" in r[3].nota


def probar_inventario_las_cargas_son_validas_y_repetibles():
    objetos = B._objetos(10)
    assert objetos == B._objetos(10)                              # misma semilla, mismos objetos
    ids = [o.id for o in objetos]
    assert len(ids) == 10
    for i in range(10):
        for j in range(i + 1, 10):
            assert ids[i] != ids[j], "los ids deben ser únicos"
    clases = [o.clase for o in objetos]
    assert "arma" in clases and "armadura" in clases              # se pueden equipar los dos tipos
    for o in objetos:
        assert o.peso >= 1 and o.valor >= 1
    assert B._ids_al_azar(objetos, 20) == B._ids_al_azar(objetos, 20)
    for id_objeto in B._ids_al_azar(objetos, 20):
        assert id_objeto in ids


def probar_inventario_recoger_y_soltar_todos():
    objetos = B._objetos(8)
    vacio = Inventario(8)
    B._recoger_todos(vacio, objetos)
    assert vacio.cantidad() == 8 and vacio.esta_lleno()
    assert vacio.objetos() == objetos                             # en el orden en que se recogieron
    B._soltar_todos(vacio)
    assert vacio.esta_vacio() and vacio.cantidad() == 0
    lleno = B._inventario_lleno(objetos)
    assert lleno.esta_lleno() and lleno.objetos() == objetos


def probar_inventario_equipar_rotando_trae_el_segundo_al_frente():
    objetos = B._objetos(6)
    inventario = B._inventario_lleno(objetos)
    B._equipar_rotando(inventario, 1)
    assert inventario.objetos()[0] == objetos[1]                  # el trabajo es real
    assert inventario.arma_equipada() is None and inventario.armadura_equipada() == objetos[1]
    B._equipar_rotando(inventario, 1)                             # ahora trae al frente el viejo primero
    assert inventario.objetos()[0] == objetos[0]
    assert inventario.arma_equipada() == objetos[0]
    assert inventario.cantidad() == 6                             # equipar no quita nada


def probar_inventario_ubicar_deja_el_cursor_en_el_ultimo_buscado():
    objetos = B._objetos(9)
    inventario = B._inventario_lleno(objetos)
    ids = [objetos[7].id, objetos[2].id, objetos[5].id]
    B._ubicar_todos(inventario, ids)
    assert inventario.objeto_actual() == objetos[5]               # sí buscó (si no, seguiría en el primero)
    assert inventario.objetos() == objetos                        # y no alteró el orden real


def probar_inventario_recorrer_ida_y_vuelta_regresa_al_inicio():
    objetos = B._objetos(7)
    inventario = B._inventario_lleno(objetos)
    inventario.siguiente()
    inventario.siguiente()
    B._recorrer_ida_y_vuelta(inventario)
    assert inventario.posicion_cursor() == 0                      # llegó al final y regresó a la cabeza
    assert inventario.objeto_actual() == objetos[0]
    B._recorrer_ida_y_vuelta(inventario)                          # se puede repetir en cada tanda
    assert inventario.posicion_cursor() == 0


# ---------------------------------------------------------------- 3. historial
def probar_historial_forma_de_las_filas():
    r = B.medir_historial(tamanos=(10, 100), ciclos=3, cambios=5, repeticiones=2)
    _revisar(r, "historial", 4)
    assert [x.tamano for x in r] == [10, 10, 100, 100]
    assert r[0].caso == "HistorialRetroceso: acción + deshacer"
    assert r[1].caso == "copia completa (descartada): acción + deshacer"
    assert "3 acciones de 5 cambios" in r[0].nota


def probar_historial_indices_repartidos_y_distintos():
    for n, cambios in ((10, 5), (1000, 5), (100000, 5), (5, 5)):
        indices = B._indices_de_cambio(n, cambios)
        assert len(indices) == cambios
        for i in range(cambios):
            assert 0 <= indices[i] < n
            for j in range(i + 1, cambios):
                assert indices[i] != indices[j]


def probar_historial_la_accion_cambia_y_deshacer_restaura():
    n = 50
    original = list(range(n))
    estado = list(original)
    indices = B._indices_de_cambio(n, 5)
    historial = HistorialRetroceso()
    B._accion_con_historial(estado, historial, indices)
    assert historial.cantidad() == 1
    for i in indices:
        assert estado[i] == original[i] + 1                       # el trabajo es real
    assert estado != original
    assert historial.deshacer() is True
    assert estado == original


def probar_historial_los_ciclos_dejan_el_estado_igual_y_el_historial_vacio():
    original = list(range(40))
    indices = B._indices_de_cambio(40, 5)
    estado = list(original)
    historial = HistorialRetroceso()
    B._ciclos_con_historial(estado, historial, indices, 12)       # más ciclos que el máximo de 5
    assert estado == original and historial.cantidad() == 0


def probar_historial_la_alternativa_hace_el_mismo_trabajo():
    original = list(range(40))
    indices = B._indices_de_cambio(40, 5)
    estado = list(original)
    copia = B._accion_con_copia(estado, indices)
    for i in indices:
        assert estado[i] == original[i] + 1                       # cambió igual que con el historial
    assert copia == original and copia is not estado              # y volver es usar una copia COMPLETA
    assert B._ciclos_con_copia(list(original), indices, 12) == original


# ---------------------------------------------------------------- 4. bitácora en pantalla
def probar_buffer_forma_de_las_filas():
    r = B.medir_buffer(capacidades=(3, 10), repeticiones=2)
    _revisar(r, "bitácora en pantalla", 4)
    assert [x.tamano for x in r] == [3, 3, 10, 10]
    assert r[0].caso == "BufferCircular: agregar mensajes"
    assert r[1].caso == "array que desplaza (descartada): agregar mensajes"


def probar_buffer_siempre_hay_mas_mensajes_que_capacidad():
    """Si no, el array nunca desplazaría nada y la medición no diría nada."""
    capacidades = (3, 10, 1999, 2000, 2001, 5000)
    for fila in B.medir_buffer(capacidades=capacidades, repeticiones=1):
        mensajes = int(fila.nota.split(" ")[0])
        assert mensajes > fila.tamano, fila
        assert mensajes >= 2 * fila.tamano or mensajes >= 2000


def probar_buffer_ambos_dejan_los_ultimos_mensajes():
    for capacidad, cantidad in ((1, 5), (3, 50), (20, 60), (20, 20), (20, 7)):
        textos = [f"mensaje {i}" for i in range(cantidad)]
        circular = B._llenar_circular(capacidad, textos).a_array()
        desplazando = B._llenar_desplazando(capacidad, textos)
        assert circular == desplazando == textos[-capacidad:], (capacidad, cantidad)


def probar_buffer_con_capacidad_grande_usa_menos_repeticiones():
    grande = B.medir_buffer(capacidades=(B.REPETIR_HASTA_CAPACIDAD + 1,), repeticiones=8)
    assert f"{B.REPETICIONES_CAPACIDAD_GRANDE} repeticiones" in grande[0].nota
    chica = B.medir_buffer(capacidades=(20,), repeticiones=8)
    assert "repeticiones" not in chica[0].nota


# ---------------------------------------------------------------- 5. ordenamiento
def probar_ordenamiento_forma_de_las_filas():
    r = B.medir_ordenamiento(tamanos_desordenados=(4, 9), tamanos_casi_ordenados=(10,),
                             tamanos_dos_tramos=(8,), repeticiones=2)
    _revisar(r, "ordenamiento", 18)                               # (2 tamaños x 2 comparadores + 1 + 1) x 3
    for i in range(0, 18, 3):
        assert [r[i + k].caso.split(":")[0] for k in range(3)] == NOMBRES_ALGORITMOS
        assert r[i].tamano == r[i + 1].tamano == r[i + 2].tamano
        assert "eligió" in r[i + 2].nota and "eligió" not in r[i].nota
    assert [x.tamano for x in r[::3]] == [4, 4, 9, 9, 10, 8]
    assert "comparación barata" in r[0].caso and "comparación costosa" in r[3].caso
    assert "casi ordenados" in r[12].caso and "dos tramos" in r[15].caso


def probar_ordenamiento_repite_los_pequenos_hasta_sumar_elementos():
    datos = B._desordenados(8)
    filas = B._filas_de_ordenamiento("x", 8, datos, Ordenador.comparar, 1024, 1)
    assert filas[0].nota.startswith("128 ordenamiento(s)")        # 1024 // 8
    filas = B._filas_de_ordenamiento("x", 2000, B._desordenados(2000), Ordenador.comparar, 1024, 1)
    assert filas[0].nota.startswith("1 ordenamiento(s)")          # nunca menos de uno
    filas = B._filas_de_ordenamiento("x", 8, datos, Ordenador.comparar, 0, 1)
    assert filas[0].nota.startswith("1 ordenamiento(s)")          # 0 = una sola vez


def probar_ordenamiento_ordenar_varias_veces_llama_al_algoritmo_cada_vez():
    llamadas = []

    def algoritmo(datos, comparador):
        llamadas.append(len(datos))
        return datos

    B._ordenar_varias_veces(algoritmo, [3, 1, 2], Ordenador.comparar, 5)
    assert llamadas == [3] * 5


def probar_ordenamiento_las_cargas_son_las_que_dicen_ser():
    for n in (16, 64, 300):
        assert B._desordenados(n) == B._desordenados(n)           # repetibles
        assert B._casi_ordenados(n) == B._casi_ordenados(n)
        casi = B._casi_ordenados(n)
        assert len(casi) == n and _es_permutacion_de_rango(casi)
        desorden = Ordenador.proporcion_de_desorden(casi, Ordenador.comparar)
        assert 0 < desorden <= Ordenador.UMBRAL_DESORDEN, (n, desorden)

        tramos = B._dos_tramos_al_reves(n)
        assert len(tramos) == n and _es_permutacion_de_rango(tramos)
        assert Ordenador.proporcion_de_desorden(tramos, Ordenador.comparar) == 1 / (n - 1)   # solo un par roto

    assert Ordenador.proporcion_de_desorden(B._desordenados(64), Ordenador.comparar) > 0.3  # de verdad desordenados
    assert B._dos_tramos_al_reves(5) == [2, 3, 4, 0, 1]


def probar_ordenamiento_el_texto_costoso_conserva_el_orden_y_tiene_mayusculas():
    assert B._texto(5) < B._texto(10) < B._texto(123456)
    assert B._texto(7) != B._texto(7).casefold()                  # casefold sí tiene trabajo que hacer
    assert B._comparar_texto(B._texto(3), B._texto(30)) < 0
    assert B._comparar_texto(B._texto(30), B._texto(3)) > 0
    assert B._comparar_texto(B._texto(3), B._texto(3)) == 0
    assert B._comparar_texto("Objeto 1", "OBJETO 1") == 0           # casefold: solo difieren en mayúsculas
    assert B._datos([4, 2], costoso=False) == [4, 2]
    assert B._datos([4, 2], costoso=True) == [B._texto(4), B._texto(2)]


def probar_ordenamiento_los_tres_algoritmos_ordenan_lo_mismo():
    escenarios = []
    for n in (8, 30, 200):
        escenarios.append((B._desordenados(n), Ordenador.comparar))
        escenarios.append((B._datos(B._desordenados(n), True), B._comparar_texto))
        escenarios.append((B._casi_ordenados(n), Ordenador.comparar))
        escenarios.append((B._dos_tramos_al_reves(n), Ordenador.comparar))
    assert [nombre for nombre, _ in B._ALGORITMOS] == NOMBRES_ALGORITMOS
    for datos, comparador in escenarios:
        copia = list(datos)
        resultados = [algoritmo(datos, comparador) for _, algoritmo in B._ALGORITMOS]
        assert resultados[0] == resultados[1] == resultados[2]
        assert _esta_ascendente(resultados[0], comparador)
        assert len(resultados[0]) == len(datos)
        assert datos == copia                                     # ninguno altera la carga que se reutiliza


def probar_ordenamiento_el_automatico_anota_lo_que_eligio():
    muy_chico = B._filas_de_ordenamiento("x", 8, B._desordenados(8), Ordenador.comparar, 1024, 1)
    assert muy_chico[2].nota.endswith("eligió inserción")
    n = Ordenador.UMBRAL_INSERCION_MAXIMO + 1
    grande = B._filas_de_ordenamiento("x", n, B._dos_tramos_al_reves(n), Ordenador.comparar, 0, 1)
    assert grande[2].nota.endswith("eligió mezcla")               # pasó el tope de tamaño
    dentro = Ordenador.UMBRAL_INSERCION_MAXIMO
    limite = B._filas_de_ordenamiento("x", dentro, B._dos_tramos_al_reves(dentro), Ordenador.comparar, 0, 1)
    assert limite[2].nota.endswith("eligió inserción")            # el límite conocido: desorden ~0 engaña


# ---------------------------------------------------------------- todo junto
def probar_medir_junta_los_cinco_grupos_en_orden():
    nombres = ["medir_estructura", "medir_inventario", "medir_historial", "medir_buffer", "medir_ordenamiento"]
    originales = [getattr(B, nombre) for nombre in nombres]
    filas = [ResultadoBenchDTO("grupo", f"caso {i}", i, 0.1, 0.2) for i in range(5)]
    try:
        for i in range(5):
            setattr(B, nombres[i], lambda i=i: [filas[i]])
        assert B.medir() == filas                                 # los cinco, y en este orden
    finally:
        for i in range(5):
            setattr(B, nombres[i], originales[i])


def probar_no_usa_lo_prohibido_por_el_enunciado():
    texto = (Path(__file__).resolve().parent.parent / "Service" / "BenchInventario.py").read_text(encoding="utf-8")
    for prohibido in ("sorted(", ".sort(", "heapq", "deque", "OrderedDict"):
        assert prohibido not in texto, prohibido
    assert "random.seed(" not in texto and "random.randint(" not in texto   # nada del generador global


if __name__ == "__main__":
    probar_estructura_forma_de_las_filas()
    probar_estructura_quitar_y_reponer_hace_el_mismo_trabajo()
    probar_estructura_quitar_y_reponer_funciona_en_los_extremos_del_tamano()
    probar_estructura_mover_el_ultimo_deja_el_mismo_orden_en_ambas()
    probar_estructura_recorrer_cuenta_todo()
    probar_inventario_forma_de_las_filas()
    probar_inventario_las_cargas_son_validas_y_repetibles()
    probar_inventario_recoger_y_soltar_todos()
    probar_inventario_equipar_rotando_trae_el_segundo_al_frente()
    probar_inventario_ubicar_deja_el_cursor_en_el_ultimo_buscado()
    probar_inventario_recorrer_ida_y_vuelta_regresa_al_inicio()
    probar_historial_forma_de_las_filas()
    probar_historial_indices_repartidos_y_distintos()
    probar_historial_la_accion_cambia_y_deshacer_restaura()
    probar_historial_los_ciclos_dejan_el_estado_igual_y_el_historial_vacio()
    probar_historial_la_alternativa_hace_el_mismo_trabajo()
    probar_buffer_forma_de_las_filas()
    probar_buffer_siempre_hay_mas_mensajes_que_capacidad()
    probar_buffer_ambos_dejan_los_ultimos_mensajes()
    probar_buffer_con_capacidad_grande_usa_menos_repeticiones()
    probar_ordenamiento_forma_de_las_filas()
    probar_ordenamiento_repite_los_pequenos_hasta_sumar_elementos()
    probar_ordenamiento_ordenar_varias_veces_llama_al_algoritmo_cada_vez()
    probar_ordenamiento_las_cargas_son_las_que_dicen_ser()
    probar_ordenamiento_el_texto_costoso_conserva_el_orden_y_tiene_mayusculas()
    probar_ordenamiento_los_tres_algoritmos_ordenan_lo_mismo()
    probar_ordenamiento_el_automatico_anota_lo_que_eligio()
    probar_medir_junta_los_cinco_grupos_en_orden()
    probar_no_usa_lo_prohibido_por_el_enunciado()
    print("OK: todas las pruebas de BenchInventario pasaron")
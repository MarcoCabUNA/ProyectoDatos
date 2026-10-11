import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.ObjetoDTO import ObjetoDTO
from Logic.Ordenador import Ordenador

ALGORITMOS = [Ordenador.ordenar_por_insercion, Ordenador.ordenar_por_mezcla, Ordenador.ordenar]
TAMANOS = [0, 1, 2, 3, 5, 12, 13, 50, 128, 129, 300]


def _datos(n, semilla, modulo=1000):
    """n números pseudoaleatorios pero siempre iguales para la misma semilla."""
    x = semilla
    resultado = []
    for _ in range(n):
        x = (x * 1103515245 + 12345) % 2147483648
        resultado.append((x >> 8) % modulo)
    return resultado


def _esta_ordenada(lista, comparador=Ordenador.comparar):
    for i in range(len(lista) - 1):
        if comparador(lista[i], lista[i + 1]) > 0:
            return False
    return True


def _mismos_elementos(a, b):
    """Los dos arrays tienen los mismos elementos, repetidos las mismas veces."""
    restantes = list(b)
    for elemento in a:
        if elemento not in restantes:
            return False
        restantes.remove(elemento)
    return len(restantes) == 0


def _contador():
    cuenta = [0]

    def comparador(a, b):
        cuenta[0] += 1
        return Ordenador.comparar(a, b)
    return comparador, cuenta


def _por_clave(a, b):
    return Ordenador.comparar(a[0], b[0])


def probar_comparar():
    assert Ordenador.comparar(1, 2) == -1 and Ordenador.comparar(2, 1) == 1
    assert Ordenador.comparar(3, 3) == 0
    assert Ordenador.comparar("a", "b") == -1 and Ordenador.comparar("b", "b") == 0


def probar_casos_triviales():
    for ordenar in ALGORITMOS:
        assert ordenar([], Ordenador.comparar) == []
        assert ordenar([5], Ordenador.comparar) == [5]
        assert ordenar([2, 1], Ordenador.comparar) == [1, 2]


def probar_ordenan_correctamente():
    for ordenar in ALGORITMOS:
        for n in TAMANOS:
            for semilla in (1, 2, 3):
                for modulo in (1000, 5):             # con 5 valores posibles hay muchos repetidos
                    datos = _datos(n, semilla, modulo)
                    resultado = ordenar(datos, Ordenador.comparar)
                    assert len(resultado) == n
                    assert _esta_ordenada(resultado), (n, semilla, modulo)
                    assert _mismos_elementos(datos, resultado), (n, semilla, modulo)


def probar_patrones_conocidos():
    mitad = list(range(100, 200)) + list(range(100))          # dos tramos ordenados al revés
    patrones = [list(range(200)), list(range(200))[::-1], [7] * 200, mitad]
    for ordenar in ALGORITMOS:
        for datos in patrones:
            resultado = ordenar(datos, Ordenador.comparar)
            assert _esta_ordenada(resultado) and _mismos_elementos(datos, resultado)


def probar_son_estables():
    for ordenar in ALGORITMOS:
        for n in (5, 12, 50, 200):
            pares = [(clave, indice) for indice, clave in enumerate(_datos(n, 9, 4))]
            resultado = ordenar(pares, _por_clave)
            assert _esta_ordenada(resultado, _por_clave)
            for i in range(n - 1):
                if resultado[i][0] == resultado[i + 1][0]:
                    assert resultado[i][1] < resultado[i + 1][1], "empate fuera de su orden original"


def probar_el_resultado_no_depende_del_algoritmo():
    for n in TAMANOS:
        pares = [(clave, indice) for indice, clave in enumerate(_datos(n, 5, 6))]
        por_insercion = Ordenador.ordenar_por_insercion(pares, _por_clave)
        por_mezcla = Ordenador.ordenar_por_mezcla(pares, _por_clave)
        assert por_insercion == por_mezcla == Ordenador.ordenar(pares, _por_clave), n


def probar_no_modifica_la_lista_original():
    for ordenar in ALGORITMOS:
        original = _datos(40, 3)
        copia = list(original)
        resultado = ordenar(original, Ordenador.comparar)
        assert original == copia
        assert resultado is not original


def probar_proporcion_de_desorden():
    cmp = Ordenador.comparar
    assert Ordenador.proporcion_de_desorden([], cmp) == 0.0
    assert Ordenador.proporcion_de_desorden([4], cmp) == 0.0
    assert Ordenador.proporcion_de_desorden([1, 2, 3, 4], cmp) == 0.0
    assert Ordenador.proporcion_de_desorden([4, 3, 2, 1], cmp) == 1.0
    assert abs(Ordenador.proporcion_de_desorden([1, 3, 2, 4], cmp) - 1 / 3) < 1e-9


def probar_eleccion_automatica():
    cmp = Ordenador.comparar
    pequeno = Ordenador.UMBRAL_PEQUENO
    tope = Ordenador.UMBRAL_INSERCION_MAXIMO
    assert Ordenador.elegir_algoritmo(list(range(pequeno))[::-1], cmp) == "insercion"   # pequeño: siempre
    assert Ordenador.elegir_algoritmo(list(range(50))[::-1], cmp) == "mezcla"           # muy desordenado
    casi = list(range(100))
    casi[10], casi[11] = casi[11], casi[10]
    assert Ordenador.elegir_algoritmo(casi, cmp) == "insercion"                          # casi ordenado
    assert Ordenador.elegir_algoritmo(list(range(tope)), cmp) == "insercion"            # justo en el tope
    assert Ordenador.elegir_algoritmo(list(range(tope + 1)), cmp) == "mezcla"           # pasó el tope


def probar_comparaciones_en_los_casos_extremos():
    comparador, cuenta = _contador()
    Ordenador.ordenar_por_insercion(list(range(100)), comparador)
    assert cuenta[0] == 99                              # ya ordenada: n-1 comparaciones
    comparador, cuenta = _contador()
    Ordenador.ordenar_por_mezcla(list(range(100)), comparador)
    assert cuenta[0] == 99                              # ya ordenada: n-1, no mezcla nada
    comparador, cuenta = _contador()
    Ordenador.ordenar_por_insercion(list(range(50))[::-1], comparador)
    assert cuenta[0] == 50 * 49 // 2                    # al revés: el peor caso cuadrático
    comparador, cuenta = _contador()
    Ordenador.ordenar_por_mezcla(_datos(1024, 11), comparador)
    assert cuenta[0] <= 1024 * 10                       # n log2 n: no se vuelve cuadrático


def probar_con_objetos_y_comparador_propio():
    objetos = [ObjetoDTO(id=f"o{i}", nombre=f"Obj{i}", clase="pocion", peso=p, valor=1)
               for i, p in enumerate(_datos(30, 4, 6))]

    def mas_pesado_primero(a, b):
        return Ordenador.comparar(b.peso, a.peso)

    resultado = Ordenador.ordenar(objetos, mas_pesado_primero)
    assert _esta_ordenada(resultado, mas_pesado_primero)
    for i in range(len(resultado) - 1):                 # empates en su orden original (estable)
        if resultado[i].peso == resultado[i + 1].peso:
            assert int(resultado[i].id[1:]) < int(resultado[i + 1].id[1:])


def probar_no_usa_las_funciones_de_ordenamiento_integradas():
    """El enunciado prohíbe las funciones de ordenamiento de Python en §4.9."""
    texto = (Path(__file__).resolve().parent.parent / "Logic" / "Ordenador.py").read_text(encoding="utf-8")
    assert "sorted(" not in texto and ".sort(" not in texto


if __name__ == "__main__":
    probar_comparar()
    probar_casos_triviales()
    probar_ordenan_correctamente()
    probar_patrones_conocidos()
    probar_son_estables()
    probar_el_resultado_no_depende_del_algoritmo()
    probar_no_modifica_la_lista_original()
    probar_proporcion_de_desorden()
    probar_eleccion_automatica()
    probar_comparaciones_en_los_casos_extremos()
    probar_con_objetos_y_comparador_propio()
    probar_no_usa_las_funciones_de_ordenamiento_integradas()
    print("OK: todas las pruebas de Ordenador pasaron")
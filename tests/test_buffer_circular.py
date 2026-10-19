import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Estructuras.BufferCircular import BufferCircular


def probar_vacio():
    b = BufferCircular(5)
    assert b.a_array() == []


def probar_capacidad_invalida():
    try:
        BufferCircular(0)
    except ValueError:
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_antes_de_llenarse_conserva_el_orden():
    b = BufferCircular(5)
    for i in range(3):
        b.agregar(i)
    assert b.a_array() == [0, 1, 2]


def probar_justo_lleno():
    b = BufferCircular(5)
    for i in range(5):
        b.agregar(i)
    assert b.a_array() == [0, 1, 2, 3, 4]


def probar_al_pasar_el_limite_se_pierde_el_mas_antiguo():
    b = BufferCircular(5)
    for i in range(7):
        b.agregar(i)
    assert b.a_array() == [2, 3, 4, 5, 6]


def probar_los_ultimos_veinte_mensajes():
    b = BufferCircular(20)
    for i in range(1000):
        b.agregar(f"mensaje {i}")
    assert len(b.a_array()) == 20
    assert b.a_array() == [f"mensaje {i}" for i in range(980, 1000)]


def probar_capacidad_uno():
    b = BufferCircular(1)
    b.agregar("a")
    b.agregar("b")
    assert b.a_array() == ["b"]


def probar_la_memoria_es_constante():
    b = BufferCircular(20)
    for i in range(5000):
        b.agregar(i)
        assert len(b._datos) == 20                      # el array interno nunca crece


def probar_a_array_es_una_copia():
    b = BufferCircular(3)
    for i in range(3):
        b.agregar(i)
    copia = b.a_array()
    copia.append(99)
    copia[0] = -1
    assert b.a_array() == [0, 1, 2]


def probar_contra_un_modelo_simple():
    """Cada paso se compara con 'los últimos N de un array que crece'."""
    for capacidad in (1, 2, 3, 7, 20):
        b = BufferCircular(capacidad)
        todos = []
        for i in range(100):
            b.agregar(i)
            todos.append(i)
            esperado = todos[-capacidad:]
            assert b.a_array() == esperado, (capacidad, i)


if __name__ == "__main__":
    probar_vacio()
    probar_capacidad_invalida()
    probar_antes_de_llenarse_conserva_el_orden()
    probar_justo_lleno()
    probar_al_pasar_el_limite_se_pierde_el_mas_antiguo()
    probar_los_ultimos_veinte_mensajes()
    probar_capacidad_uno()
    probar_la_memoria_es_constante()
    probar_a_array_es_una_copia()
    probar_contra_un_modelo_simple()
    print("OK: todas las pruebas de BufferCircular pasaron")
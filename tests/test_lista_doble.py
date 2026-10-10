import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Estructuras.ListaDoble import ListaDoble, NodoDoble


def _adelante(lista):
    valores = []
    actual = lista.cabeza
    while actual is not None:
        valores.append(actual.dato)
        actual = actual.siguiente
    return valores


def _atras(lista):
    valores = []
    actual = lista.cola
    while actual is not None:
        valores.append(actual.dato)
        actual = actual.anterior
    return valores


def _verificar_integridad(lista):
    """Recorrer hacia adelante y hacia atrás debe dar lo mismo (invertido) y coincidir con el contador."""
    adelante = _adelante(lista)
    atras = _atras(lista)
    assert adelante == atras[::-1], f"enlaces inconsistentes: {adelante} vs {atras}"
    assert lista.tamano() == len(adelante) == len(lista)
    assert lista.esta_vacia() == (len(adelante) == 0)
    if adelante:
        assert lista.cabeza.anterior is None and lista.cola.siguiente is None
    else:
        assert lista.cabeza is None and lista.cola is None


def _lista_abc():
    lista = ListaDoble()
    na = lista.agregar_al_final("a")
    nb = lista.agregar_al_final("b")
    nc = lista.agregar_al_final("c")
    return lista, na, nb, nc


def probar_lista_vacia():
    lista = ListaDoble()
    assert lista.esta_vacia() and lista.tamano() == 0
    assert lista.cabeza is None and lista.cola is None
    assert lista.a_array() == []
    _verificar_integridad(lista)


def probar_agregar_al_final_conserva_el_orden():
    lista, na, nb, nc = _lista_abc()
    assert lista.a_array() == ["a", "b", "c"]
    assert lista.cabeza is na and lista.cola is nc
    assert nb.anterior is na and nb.siguiente is nc
    _verificar_integridad(lista)


def probar_agregar_al_frente_invierte_el_orden():
    lista = ListaDoble()
    for valor in ["a", "b", "c"]:
        lista.agregar_al_frente(valor)
    assert lista.a_array() == ["c", "b", "a"]
    _verificar_integridad(lista)


def probar_un_solo_elemento():
    lista = ListaDoble()
    nodo = lista.agregar_al_final("x")
    assert lista.cabeza is nodo and lista.cola is nodo
    assert lista.eliminar(nodo) == "x"
    assert lista.esta_vacia()
    _verificar_integridad(lista)


def probar_quitar_cabeza_medio_y_cola():
    lista, na, nb, nc = _lista_abc()
    assert lista.eliminar(nb) == "b"                       # medio
    assert lista.a_array() == ["a", "c"]
    _verificar_integridad(lista)
    assert lista.eliminar(na) == "a"                       # cabeza
    assert lista.a_array() == ["c"] and lista.cabeza is nc
    _verificar_integridad(lista)
    assert lista.eliminar(nc) == "c"                       # cola (y último)
    _verificar_integridad(lista)


def probar_mover_al_frente():
    lista, na, nb, nc = _lista_abc()
    lista.mover_al_frente(nc)                            # desde la cola
    assert lista.a_array() == ["c", "a", "b"]
    _verificar_integridad(lista)
    lista.mover_al_frente(nb)                            # desde la cola otra vez
    assert lista.a_array() == ["b", "c", "a"]
    lista.mover_al_frente(nb)                            # ya está al frente: no cambia nada
    assert lista.a_array() == ["b", "c", "a"]
    lista.mover_al_frente(nc)                            # desde el medio
    assert lista.a_array() == ["c", "b", "a"]
    _verificar_integridad(lista)


def probar_nodos_invalidos_lanzan_error():
    lista, na, nb, nc = _lista_abc()
    lista.eliminar(nb)
    for accion in (lambda: lista.eliminar(nb),                       # ya quitado
                   lambda: lista.mover_al_frente(nb),              # ya quitado
                   lambda: lista.eliminar(NodoDoble("z")),           # nunca estuvo en la lista
                   lambda: lista.eliminar(None),
                   lambda: lista.eliminar(ListaDoble().agregar_al_final("w"))):   # de otra lista
        try:
            accion()
        except ValueError:
            continue
        raise AssertionError("Debió lanzar ValueError")
    assert lista.a_array() == ["a", "c"]                 # la lista no se dañó
    _verificar_integridad(lista)


def probar_enlaces_de_afuera_son_de_solo_lectura():
    lista, na, nb, nc = _lista_abc()
    try:
        lista.cabeza = None
    except AttributeError:
        return
    raise AssertionError("cabeza debería ser de solo lectura")


def probar_a_array_es_una_copia():
    lista, na, nb, nc = _lista_abc()
    copia = lista.a_array()
    copia.append("intruso")
    copia[0] = "otro"
    assert lista.a_array() == ["a", "b", "c"]


def probar_contra_un_modelo_simple():
    """300 operaciones deterministas comparadas, paso a paso, con un array de referencia."""
    lista = ListaDoble()
    nodos = []        # nodos vivos, en el mismo orden que 'modelo'
    modelo = []       # valores esperados, de cabeza a cola
    for i in range(300):
        if len(nodos) < 3 or i % 3 == 0:
            nodos.append(lista.agregar_al_final(i))
            modelo.append(i)
        else:
            idx = (i * 7 + 3) % len(nodos)
            if i % 3 == 1:                               # mover al frente
                lista.mover_al_frente(nodos[idx])
                nodo = nodos.pop(idx)
                valor = modelo.pop(idx)
                nodos.insert(0, nodo)
                modelo.insert(0, valor)
            else:                                        # quitar
                assert lista.eliminar(nodos[idx]) == modelo[idx]
                nodos.pop(idx)
                modelo.pop(idx)
        assert lista.a_array() == modelo
        _verificar_integridad(lista)


if __name__ == "__main__":
    probar_lista_vacia()
    probar_agregar_al_final_conserva_el_orden()
    probar_agregar_al_frente_invierte_el_orden()
    probar_un_solo_elemento()
    probar_quitar_cabeza_medio_y_cola()
    probar_mover_al_frente()
    probar_nodos_invalidos_lanzan_error()
    probar_enlaces_de_afuera_son_de_solo_lectura()
    probar_a_array_es_una_copia()
    probar_contra_un_modelo_simple()
    print("OK: todas las pruebas de ListaDoble pasaron")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.ObjetoDTO import ObjetoDTO
from Logica.Inventario import Inventario


def _objeto(id_objeto, clase="pocion"):
    return ObjetoDTO(id=id_objeto, nombre=id_objeto.upper(), clase=clase, peso=1, valor=1)


def _ids(inventario):
    return [o.id for o in inventario.objetos()]


def _inventario_con(*objetos, capacidad=10):
    inventario = Inventario(capacidad)
    for objeto in objetos:
        inventario.recoger(objeto)
    return inventario


def probar_inventario_vacio():
    inv = Inventario(3)
    assert inv.cantidad() == 0 and inv.esta_vacio() and not inv.esta_lleno()
    assert inv.capacidad_maxima() == 3
    assert inv.objeto_actual() is None and inv.posicion_cursor() == 0
    assert inv.soltar_actual() is None
    assert not inv.equipar_actual() and not inv.siguiente() and not inv.anterior()
    assert not inv.ubicar("x") and not inv.tiene_objeto("x")
    assert inv.arma_equipada() is None and inv.armadura_equipada() is None
    assert inv.objetos() == []


def probar_capacidad_invalida():
    try:
        Inventario(0)
    except ValueError:
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_recoger_agrega_al_final_y_el_cursor_ve_el_primero():
    inv = Inventario(5)
    nodo = inv.recoger(_objeto("a"))
    assert nodo.dato.id == "a"
    inv.recoger(_objeto("b"))
    inv.recoger(_objeto("c"))
    assert _ids(inv) == ["a", "b", "c"]
    assert inv.objeto_actual().id == "a" and inv.posicion_cursor() == 0


def probar_inventario_lleno_rechaza():
    inv = _inventario_con(_objeto("a"), _objeto("b"), capacidad=2)
    assert inv.esta_lleno()
    assert inv.recoger(_objeto("c")) is None
    assert _ids(inv) == ["a", "b"] and inv.cantidad() == 2


def probar_recorrido_en_ambos_sentidos():
    inv = _inventario_con(_objeto("a"), _objeto("b"), _objeto("c"))
    assert inv.siguiente() and inv.objeto_actual().id == "b"
    assert inv.siguiente() and inv.objeto_actual().id == "c"
    assert not inv.siguiente() and inv.objeto_actual().id == "c"        # extremo: no da la vuelta
    assert inv.anterior() and inv.objeto_actual().id == "b"
    assert inv.anterior() and inv.objeto_actual().id == "a"
    assert not inv.anterior() and inv.objeto_actual().id == "a"


def probar_soltar_en_el_medio():
    inv = _inventario_con(_objeto("a"), _objeto("b"), _objeto("c"))
    inv.siguiente()
    assert inv.soltar_actual().id == "b"
    assert _ids(inv) == ["a", "c"] and inv.objeto_actual().id == "c"


def probar_soltar_el_ultimo():
    inv = _inventario_con(_objeto("a"), _objeto("b"), _objeto("c"))
    inv.siguiente()
    inv.siguiente()
    assert inv.soltar_actual().id == "c"
    assert _ids(inv) == ["a", "b"] and inv.objeto_actual().id == "b"    # el cursor retrocede


def probar_soltar_el_primero():
    inv = _inventario_con(_objeto("a"), _objeto("b"), _objeto("c"))
    assert inv.soltar_actual().id == "a"
    assert _ids(inv) == ["b", "c"] and inv.objeto_actual().id == "b"


def probar_soltar_el_unico_y_volver_a_recoger():
    inv = _inventario_con(_objeto("a"))
    assert inv.soltar_actual().id == "a"
    assert inv.esta_vacio() and inv.objeto_actual() is None
    inv.recoger(_objeto("b"))
    assert inv.objeto_actual().id == "b"


def probar_soltar_libera_espacio():
    inv = _inventario_con(_objeto("a"), _objeto("b"), capacidad=2)
    assert inv.recoger(_objeto("c")) is None
    inv.soltar_actual()
    assert inv.recoger(_objeto("c")) is not None


def probar_equipar_arma_la_mueve_al_frente():
    inv = _inventario_con(_objeto("p"), _objeto("w", "arma"), _objeto("r", "armadura"))
    inv.siguiente()
    assert inv.equipar_actual()
    assert _ids(inv) == ["w", "p", "r"]
    assert inv.arma_equipada().id == "w"
    assert inv.objeto_actual().id == "w" and inv.posicion_cursor() == 0   # el cursor sigue al objeto


def probar_arma_y_armadura_se_equipan_por_separado():
    inv = _inventario_con(_objeto("w", "arma"), _objeto("r", "armadura"))
    inv.equipar_actual()
    inv.siguiente()
    inv.equipar_actual()
    assert inv.arma_equipada().id == "w" and inv.armadura_equipada().id == "r"
    assert _ids(inv) == ["r", "w"]


def probar_equipar_lo_no_equipable_no_cambia_nada():
    inv = _inventario_con(_objeto("p"), _objeto("llave", "llave"))
    assert not inv.equipar_actual()
    assert _ids(inv) == ["p", "llave"]
    assert inv.arma_equipada() is None and inv.armadura_equipada() is None


def probar_equipar_otra_arma_sustituye_pero_conserva_la_anterior():
    inv = _inventario_con(_objeto("w1", "arma"), _objeto("w2", "arma"))
    inv.equipar_actual()                       # w1
    inv.siguiente()
    inv.equipar_actual()                       # w2 sustituye a w1
    assert inv.arma_equipada().id == "w2"
    assert inv.tiene_objeto("w1") and _ids(inv) == ["w2", "w1"]


def probar_soltar_lo_equipado_lo_desequipa():
    inv = _inventario_con(_objeto("w", "arma"), _objeto("r", "armadura"))
    inv.equipar_actual()
    inv.soltar_actual()
    assert inv.arma_equipada() is None and inv.armadura_equipada() is None


def probar_ubicar_prefiere_la_instancia_de_repuesto():
    daga1, daga2 = _objeto("daga", "arma"), _objeto("daga", "arma")   # misma ficha, dos instancias
    inv = _inventario_con(daga1, daga2)
    inv.equipar_actual()                                              # daga1 equipada, al frente
    assert inv.ubicar("daga") and inv.posicion_cursor() == 1          # va a la de repuesto
    assert inv.soltar_actual() is daga2
    assert inv.arma_equipada() is daga1 and inv.cantidad() == 1


def probar_ubicar_usa_la_equipada_si_es_la_unica():
    inv = _inventario_con(_objeto("daga", "arma"))
    inv.equipar_actual()
    assert inv.ubicar("daga") and inv.objeto_actual().id == "daga"


def probar_ubicar_inexistente_no_mueve_el_cursor():
    inv = _inventario_con(_objeto("a"), _objeto("b"))
    inv.siguiente()
    assert not inv.ubicar("zzz")
    assert inv.objeto_actual().id == "b"


def probar_tiene_objeto_no_consume():
    inv = _inventario_con(_objeto("llave_bronce", "llave"))
    assert inv.tiene_objeto("llave_bronce") and inv.tiene_objeto("llave_bronce")
    assert inv.cantidad() == 1 and not inv.tiene_objeto("llave_negra")


def probar_objetos_devuelve_una_copia():
    inv = _inventario_con(_objeto("a"), _objeto("b"))
    copia = inv.objetos()
    copia.append(_objeto("intruso"))
    copia.reverse()
    assert _ids(inv) == ["a", "b"]


def probar_contra_un_modelo_simple():
    """400 operaciones deterministas comparadas, paso a paso, con un array de referencia."""
    clases = ["arma", "armadura", "pocion"]
    inv = Inventario(6)
    modelo, idx, arma, armadura, contador = [], 0, None, None, 0
    for i in range(400):
        paso = i % 7
        if paso in (0, 1):                                    # recoger
            nuevo = _objeto(f"o{contador}", clases[contador % 3])
            contador += 1
            resultado = inv.recoger(nuevo)
            if len(modelo) < 6:
                assert resultado is not None
                modelo.append(nuevo)
                idx = 0 if len(modelo) == 1 else idx
            else:
                assert resultado is None
        elif paso == 2:                                       # siguiente
            movio = inv.siguiente()
            assert movio == bool(modelo and idx < len(modelo) - 1)
            idx += 1 if movio else 0
        elif paso == 3:                                       # anterior
            movio = inv.anterior()
            assert movio == bool(modelo and idx > 0)
            idx -= 1 if movio else 0
        elif paso == 4:                                       # soltar
            soltado = inv.soltar_actual()
            if modelo:
                assert soltado is modelo[idx]
                quitado = modelo.pop(idx)
                arma = None if quitado is arma else arma
                armadura = None if quitado is armadura else armadura
                idx = idx if idx < len(modelo) else max(idx - 1, 0)
            else:
                assert soltado is None
        elif paso == 5:                                       # equipar
            ok = inv.equipar_actual()
            if modelo and modelo[idx].clase in ("arma", "armadura"):
                assert ok
                objeto = modelo.pop(idx)
                modelo.insert(0, objeto)
                idx = 0
                if objeto.clase == "arma":
                    arma = objeto
                else:
                    armadura = objeto
            else:
                assert not ok
        elif modelo:                                          # ubicar un objeto elegido de forma determinista
            objetivo = modelo[(i * 5) % len(modelo)]
            assert inv.ubicar(objetivo.id)
            idx = [o.id for o in modelo].index(objetivo.id)
        assert _ids(inv) == [o.id for o in modelo]
        assert inv.cantidad() == len(modelo)
        assert inv.posicion_cursor() == (idx if modelo else 0)
        assert (inv.objeto_actual() is modelo[idx]) if modelo else inv.objeto_actual() is None
        assert inv.arma_equipada() is arma and inv.armadura_equipada() is armadura


if __name__ == "__main__":
    probar_inventario_vacio()
    probar_capacidad_invalida()
    probar_recoger_agrega_al_final_y_el_cursor_ve_el_primero()
    probar_inventario_lleno_rechaza()
    probar_recorrido_en_ambos_sentidos()
    probar_soltar_en_el_medio()
    probar_soltar_el_ultimo()
    probar_soltar_el_primero()
    probar_soltar_el_unico_y_volver_a_recoger()
    probar_soltar_libera_espacio()
    probar_equipar_arma_la_mueve_al_frente()
    probar_arma_y_armadura_se_equipan_por_separado()
    probar_equipar_lo_no_equipable_no_cambia_nada()
    probar_equipar_otra_arma_sustituye_pero_conserva_la_anterior()
    probar_soltar_lo_equipado_lo_desequipa()
    probar_ubicar_prefiere_la_instancia_de_repuesto()
    probar_ubicar_usa_la_equipada_si_es_la_unica()
    probar_ubicar_inexistente_no_mueve_el_cursor()
    probar_tiene_objeto_no_consume()
    probar_objetos_devuelve_una_copia()
    probar_contra_un_modelo_simple()
    print("OK: todas las pruebas de Inventario pasaron")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.ObjetoDTO import ObjetoDTO
from Logic.HistorialRetroceso import HistorialRetroceso
from Logic.Inventario import Inventario


def _objeto(id_objeto, clase="pocion", peso=1, valor=1, nombre=None):
    return ObjetoDTO(id=id_objeto, nombre=nombre or id_objeto.upper(), clase=clase, peso=peso, valor=valor)


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


def probar_vista_ordenada_por_peso_conserva_el_orden_en_los_empates():
    inv = _inventario_con(_objeto("a", peso=5), _objeto("b", peso=2), _objeto("c", peso=5), _objeto("d", peso=2))
    assert [o.id for o in inv.vista_ordenada("peso")] == ["b", "d", "a", "c"]


def probar_vista_ordenada_por_valor():
    inv = _inventario_con(_objeto("a", valor=30), _objeto("b", valor=10), _objeto("c", valor=20))
    assert [o.id for o in inv.vista_ordenada("valor")] == ["b", "c", "a"]


def probar_vista_ordenada_por_nombre_sin_distinguir_mayusculas():
    inv = _inventario_con(_objeto("1", nombre="daga"), _objeto("2", nombre="Antorcha"),
                          _objeto("3", nombre="Bota"), _objeto("4", nombre="armadura"))
    assert [o.nombre for o in inv.vista_ordenada("nombre")] == ["Antorcha", "armadura", "Bota", "daga"]


def probar_vista_sin_criterio_es_el_orden_real():
    inv = _inventario_con(_objeto("b", peso=9), _objeto("a", peso=1))
    assert [o.id for o in inv.vista_ordenada(None)] == ["b", "a"]


def probar_vista_con_criterio_invalido():
    inv = _inventario_con(_objeto("a"))
    try:
        inv.vista_ordenada("color")
    except ValueError:
        return
    raise AssertionError("Debió lanzar ValueError")


def probar_vista_no_altera_el_inventario():
    inv = _inventario_con(_objeto("a", peso=9), _objeto("b", peso=1), _objeto("c", peso=5))
    inv.siguiente()
    inv.vista_ordenada("peso")
    assert _ids(inv) == ["a", "b", "c"] and inv.objeto_actual().id == "b"


def probar_vista_ordenada_con_muchos_objetos():
    pesos = [(i * 37 + 11) % 17 for i in range(40)]
    inv = _inventario_con(*[_objeto(f"o{i:02d}", peso=p) for i, p in enumerate(pesos)], capacidad=40)
    vista = inv.vista_ordenada("peso")
    assert len(vista) == 40
    for i in range(39):
        assert vista[i].peso <= vista[i + 1].peso
        if vista[i].peso == vista[i + 1].peso:
            assert vista[i].id < vista[i + 1].id            # estable: empates en su orden real


# ---------- Retroceso: el inventario registra cómo deshacerse en el historial ----------

def _con_historial(*objetos, capacidad=10, preparar=None):
    inv = _inventario_con(*objetos, capacidad=capacidad)      # el estado base se arma SIN registrar
    if preparar is not None:
        preparar(inv)                                         # (por ejemplo, equipar algo de antemano)
    historial = HistorialRetroceso()
    inv.historial = historial
    return inv, historial


def _estado(inv):
    """Todo lo que debe volver igual: orden real, cursor y lo equipado (por posición del nodo)."""
    arma, armadura = inv.arma_equipada(), inv.armadura_equipada()
    return (_ids(inv), inv.posicion_cursor(), getattr(arma, "id", None), getattr(armadura, "id", None))


def _accion_y_deshacer(inv, historial, accion):
    antes = _estado(inv)
    accion()
    historial.cerrar_intervalo()
    assert historial.deshacer()
    assert _estado(inv) == antes, (antes, _estado(inv))


def probar_deshacer_recoger():
    inv, h = _con_historial(_objeto("a"), _objeto("b"))
    _accion_y_deshacer(inv, h, lambda: inv.recoger(_objeto("c")))
    assert not inv.tiene_objeto("c") and inv.cantidad() == 2


def probar_deshacer_recoger_en_inventario_vacio():
    inv, h = _con_historial()
    _accion_y_deshacer(inv, h, lambda: inv.recoger(_objeto("a")))
    assert inv.esta_vacio() and inv.objeto_actual() is None


def probar_deshacer_soltar_desde_cada_posicion():
    for posicion in range(4):
        inv, h = _con_historial(_objeto("a"), _objeto("b"), _objeto("c"), _objeto("d"))
        for _ in range(posicion):
            inv.siguiente()
        _accion_y_deshacer(inv, h, inv.soltar_actual)


def probar_deshacer_soltar_el_unico():
    inv, h = _con_historial(_objeto("a"))
    _accion_y_deshacer(inv, h, inv.soltar_actual)
    assert inv.objeto_actual().id == "a"


def probar_deshacer_soltar_lo_equipado_restaura_el_equipo():
    inv, h = _con_historial(_objeto("p"), _objeto("w", "arma"), _objeto("r", "armadura"),
                            preparar=lambda i: (i.siguiente(), i.equipar_actual()))   # w equipada al frente
    _accion_y_deshacer(inv, h, inv.soltar_actual)
    assert inv.arma_equipada().id == "w"


def probar_deshacer_equipar():
    inv, h = _con_historial(_objeto("p"), _objeto("w1", "arma"), _objeto("w2", "arma"))
    inv.siguiente()
    _accion_y_deshacer(inv, h, inv.equipar_actual)         # equipa w1: sube al frente
    assert inv.arma_equipada() is None
    inv.equipar_actual()                                   # equipa w1 de verdad...
    h.cerrar_intervalo()                                   # ...como una acción ya terminada
    inv.siguiente()
    inv.siguiente()                                        # cursor en w2
    _accion_y_deshacer(inv, h, inv.equipar_actual)         # w2 sustituye a w1, y se deshace
    assert inv.arma_equipada().id == "w1"


def probar_equipar_lo_no_equipable_se_deshace_sin_cambios():
    inv, h = _con_historial(_objeto("a"))
    _accion_y_deshacer(inv, h, inv.equipar_actual)


def probar_varias_acciones_seguidas_se_deshacen_en_orden():
    inv, h = _con_historial(_objeto("w", "arma"), _objeto("a"))
    fotos = []
    for accion in (lambda: inv.recoger(_objeto("b")), inv.equipar_actual, inv.soltar_actual):
        fotos.append(_estado(inv))
        accion()
        h.cerrar_intervalo()
    for foto in reversed(fotos):
        assert h.deshacer() and _estado(inv) == foto


def probar_los_pergaminos_no_se_registran():
    pergamino = _objeto("itm_pergamino", "pergamino_retroceso")
    inv, h = _con_historial(_objeto("a"), pergamino)
    inv.recoger(_objeto("itm_pergamino2", "pergamino_retroceso"))     # recoger un pergamino
    h.cerrar_intervalo()
    h.deshacer()
    assert inv.tiene_objeto("itm_pergamino2")                         # el retroceso no lo devuelve al suelo
    inv.ubicar("itm_pergamino")
    inv.soltar_actual()                                               # soltar un pergamino
    h.cerrar_intervalo()
    h.deshacer()
    assert not inv.tiene_objeto("itm_pergamino")                      # y tampoco lo trae de vuelta


def probar_deshacer_cuando_el_vecino_era_un_pergamino_que_ya_no_esta():
    pergamino = _objeto("itm_pergamino", "pergamino_retroceso")
    inv, h = _con_historial(pergamino, _objeto("x"))
    inv.siguiente()                                        # cursor en x, cuyo vecino anterior es el pergamino
    inv.soltar_actual()
    h.cerrar_intervalo()
    inv.ubicar("itm_pergamino")
    inv.soltar_actual()                                    # el pergamino se consume: no se registra
    assert h.deshacer()                                    # no debe fallar aunque el vecino ya no esté
    assert _ids(inv) == ["x"] and inv.objeto_actual().id == "x"


def probar_contra_fotos_con_historial():
    """300 operaciones; cada deshacer debe devolver exactamente el estado de antes de esa operación."""
    clases = ["arma", "armadura", "pocion"]
    inv, h = _con_historial(capacidad=6)
    antes, contador = [], 0
    for i in range(300):
        paso = i % 9
        if paso in (0, 1, 4, 5):                           # operaciones que cuentan como acción
            antes.append(_estado(inv))
            if paso in (0, 1):
                inv.recoger(_objeto(f"o{contador}", clases[contador % 3]))
                contador += 1
            elif paso == 4:
                inv.soltar_actual()
            else:
                inv.equipar_actual()
            h.cerrar_intervalo()
            if len(antes) > HistorialRetroceso.MAX_ACCIONES:
                antes.pop(0)
        elif paso == 2:
            inv.siguiente()                                # mover el cursor no es una acción: no se registra
        elif paso == 3:
            inv.anterior()
        elif paso in (6, 7) and antes:                     # deshacer 1 o 2 acciones
            assert h.deshacer()
            assert _estado(inv) == antes.pop(), f"paso {i}"


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
    probar_vista_ordenada_por_peso_conserva_el_orden_en_los_empates()
    probar_vista_ordenada_por_valor()
    probar_vista_ordenada_por_nombre_sin_distinguir_mayusculas()
    probar_vista_sin_criterio_es_el_orden_real()
    probar_vista_con_criterio_invalido()
    probar_vista_no_altera_el_inventario()
    probar_vista_ordenada_con_muchos_objetos()
    probar_deshacer_recoger()
    probar_deshacer_recoger_en_inventario_vacio()
    probar_deshacer_soltar_desde_cada_posicion()
    probar_deshacer_soltar_el_unico()
    probar_deshacer_soltar_lo_equipado_restaura_el_equipo()
    probar_deshacer_equipar()
    probar_equipar_lo_no_equipable_se_deshace_sin_cambios()
    probar_varias_acciones_seguidas_se_deshacen_en_orden()
    probar_los_pergaminos_no_se_registran()
    probar_deshacer_cuando_el_vecino_era_un_pergamino_que_ya_no_esta()
    probar_contra_fotos_con_historial()
    print("OK: todas las pruebas de Inventario pasaron")
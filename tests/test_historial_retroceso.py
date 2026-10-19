import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Logic.HistorialRetroceso import HistorialRetroceso


class Estado:
    """Un estado de juguete para probar el historial."""
    def __init__(self):
        self.a = 0
        self.b = 0
        self.items = []

    def foto(self):
        return (self.a, self.b, list(self.items))


def probar_historial_nuevo_no_puede_deshacer():
    h = HistorialRetroceso()
    assert h.cantidad() == 0 and not h.deshacer()


def probar_deshace_un_atributo():
    h, e = HistorialRetroceso(), Estado()
    h.registrar_atributo(e, "a", e.a)
    e.a = 5
    h.cerrar_intervalo()
    assert h.cantidad() == 1 and h.deshacer() and e.a == 0
    assert h.cantidad() == 0 and not h.deshacer()


def probar_deshace_en_orden_inverso():
    h, e = HistorialRetroceso(), Estado()
    for nuevo in (2, 3):                          # a: 0 -> 2 -> 3, registrando el valor anterior cada vez
        h.registrar_atributo(e, "a", e.a)
        e.a = nuevo
    h.cerrar_intervalo()
    h.deshacer()
    assert e.a == 0                               # al derecho habría quedado en 2


def probar_deshace_cambios_que_no_son_atributos():
    h, e = HistorialRetroceso(), Estado()
    e.items = ["x", "y", "z"]
    h.registrar_cambio(lambda: e.items.pop())               # deshace el append
    e.items.append("w")
    posicion = e.items.index("y")
    h.registrar_cambio(lambda: e.items.insert(posicion, "y"))   # deshace el quitar
    e.items.remove("y")
    h.cerrar_intervalo()
    assert e.items == ["x", "z", "w"]
    h.deshacer()
    assert e.items == ["x", "y", "z"]


def probar_solo_se_deshace_el_ultimo_intervalo():
    h, e = HistorialRetroceso(), Estado()
    for valor in (1, 2):
        h.registrar_atributo(e, "a", e.a)
        e.a = valor
        h.cerrar_intervalo()
    h.deshacer()
    assert e.a == 1
    h.deshacer()
    assert e.a == 0


def probar_maximo_cinco_acciones():
    h, e = HistorialRetroceso(), Estado()
    for valor in range(1, 8):                     # 7 acciones: a pasa de 0 a 7
        h.registrar_atributo(e, "a", e.a)
        e.a = valor
        h.cerrar_intervalo()
    assert h.cantidad() == HistorialRetroceso.MAX_ACCIONES == 5
    for _ in range(5):
        assert h.deshacer()
    assert e.a == 2                               # las dos más antiguas ya no se pueden deshacer
    assert not h.deshacer() and e.a == 2


def probar_cantidad_refleja_los_intervalos():
    h = HistorialRetroceso()
    for esperado in (1, 2, 3, 4, 5, 5, 5):
        h.cerrar_intervalo()
        assert h.cantidad() == esperado
    h.deshacer()
    assert h.cantidad() == 4


def probar_un_intervalo_sin_cambios_cuenta_como_accion():
    h, e = HistorialRetroceso(), Estado()
    h.registrar_atributo(e, "a", e.a)
    e.a = 1
    h.cerrar_intervalo()                          # acción 1
    h.cerrar_intervalo()                          # acción 2: esperar, sin cambios registrados
    assert h.cantidad() == 2
    h.deshacer()
    assert e.a == 1                               # deshacer la acción vacía no toca la anterior
    h.deshacer()
    assert e.a == 0


def probar_no_registra_mientras_deshace():
    h, e = HistorialRetroceso(), Estado()
    h.registrar_atributo(e, "a", e.a)
    e.a = 1
    h.cerrar_intervalo()

    def reversion_que_intenta_registrar():
        h.registrar_atributo(e, "a", 99)          # una operación con su propio punto de registro
        h.registrar_cambio(lambda: setattr(e, "a", 99))
        e.a = 0
    h.registrar_cambio(reversion_que_intenta_registrar)
    h.cerrar_intervalo()

    h.deshacer()                                  # ejecuta la reversión que intenta registrar
    h.cerrar_intervalo()                          # si se hubiera ensuciado, este intervalo traería a=99
    assert h.deshacer() and e.a == 0


def probar_un_error_al_deshacer_no_bloquea_el_historial():
    h, e = HistorialRetroceso(), Estado()

    def falla():
        raise RuntimeError("fallo a propósito")
    h.registrar_cambio(falla)
    h.cerrar_intervalo()
    try:
        h.deshacer()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Debió propagar el error")
    h.registrar_atributo(e, "a", e.a)             # el historial sigue registrando
    e.a = 7
    h.cerrar_intervalo()
    assert h.deshacer() and e.a == 0


def probar_descartar_el_intervalo_abierto():
    h, e = HistorialRetroceso(), Estado()
    h.registrar_atributo(e, "a", e.a)             # preparar la partida (no debe poder deshacerse)
    e.a = 10
    h.descartar_intervalo_abierto()
    h.registrar_atributo(e, "a", e.a)             # primera acción del jugador
    e.a = 11
    h.cerrar_intervalo()
    assert h.deshacer() and e.a == 10             # se vuelve al estado de antes de la acción, no al de antes de preparar


def probar_el_azar_se_restaura():
    h, azar = HistorialRetroceso(), random.Random(5)
    estado = azar.getstate()
    h.registrar_cambio(lambda: azar.setstate(estado))
    primeros = [azar.randint(0, 4) for _ in range(5)]
    h.cerrar_intervalo()
    h.deshacer()
    assert [azar.randint(0, 4) for _ in range(5)] == primeros


def probar_contra_fotos_del_estado():
    """40 acciones con cambios variados; cada deshacer debe dejar exactamente la foto anterior."""
    h, e = HistorialRetroceso(), Estado()
    fotos = [e.foto()]                            # fotos[-1] es siempre el estado actual
    x = 12345

    def azar(m):
        nonlocal x
        x = (x * 1103515245 + 12345) % 2147483648
        return (x >> 8) % m

    for paso in range(40):
        for _ in range(1 + azar(3)):              # varios cambios por acción
            tipo = azar(4)
            if tipo == 0:
                h.registrar_atributo(e, "a", e.a)
                e.a += 1 + azar(5)
            elif tipo == 1:
                h.registrar_atributo(e, "b", e.b)
                e.b -= 1 + azar(5)
            elif tipo == 2:
                h.registrar_cambio(lambda: e.items.pop())
                e.items.append(paso)
            elif e.items:
                posicion = azar(len(e.items))
                valor = e.items[posicion]
                h.registrar_cambio(lambda p=posicion, v=valor: e.items.insert(p, v))
                e.items.pop(posicion)
        h.cerrar_intervalo()
        fotos.append(e.foto())
        if paso % 7 == 6:                         # cada tanto se deshacen 1 a 3 acciones
            for _ in range(1 + azar(3)):
                if h.deshacer():
                    fotos.pop()
                    assert e.foto() == fotos[-1], f"paso {paso}"


if __name__ == "__main__":
    probar_historial_nuevo_no_puede_deshacer()
    probar_deshace_un_atributo()
    probar_deshace_en_orden_inverso()
    probar_deshace_cambios_que_no_son_atributos()
    probar_solo_se_deshace_el_ultimo_intervalo()
    probar_maximo_cinco_acciones()
    probar_cantidad_refleja_los_intervalos()
    probar_un_intervalo_sin_cambios_cuenta_como_accion()
    probar_no_registra_mientras_deshace()
    probar_un_error_al_deshacer_no_bloquea_el_historial()
    probar_descartar_el_intervalo_abierto()
    probar_el_azar_se_restaura()
    probar_contra_fotos_del_estado()
    print("OK: todas las pruebas de HistorialRetroceso pasaron")
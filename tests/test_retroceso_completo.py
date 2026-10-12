"""
Retroceso de extremo a extremo con el motor REAL (Logic + Data con el paquete offline).

Para cada partida guionada (acciones elegidas de forma pseudoaleatoria pero siempre iguales) se comprueba:
  1. Reconstruir la partida hasta un punto t da exactamente la misma "foto" del estado que la partida original.
  2. Usar de 1 a 3 pergaminos seguidos deja el estado idéntico al de t-1, t-2 y t-3 acciones atrás.
  3. Repetir las acciones deshechas da, paso a paso, las mismas fotos que la partida original (el futuro
     se repite: mismo azar, mismos eventos, mismas secuencias).
La "foto" incluye reloj, azar, jugador, cola de eventos, efectos, salas, enemigos, objetos del suelo, puertas,
trampas, rastro e inventario. Se excluye lo que el enunciado deja fuera del retroceso (§2.11): la cantidad de
pergaminos (y su lugar) y la caché del catálogo. No se prueba con la partida terminada.

Se ejecuta desde cualquier carpeta; necesita el paquete offline en <raiz>/paquete.
"""
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from Data.FuenteOffline import FuenteOffline
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from Logic.Efectos import Velocidad, Veneno
from Logic.Inventario import Inventario
from Logic.Mazmorra import Mazmorra
from Logic.jugador import Jugador
from Logic.motorJuego import Motor

ID_CRIPTA = "cripta-01"
ID_PERGAMINO = "itm_pergamino_retroceso"      # id de la ficha en el catálogo
CLASE_PERGAMINO = "pergamino_retroceso"       # clase del objeto
ID_ANTIDOTO = "itm_antidoto"
SEMILLAS = range(1, 41)
ACCIONES_POR_PARTIDA = 45


def _crear_partida(semilla, carpeta_cache, pergaminos=3):
    fuente = FuenteOffline(str(RAIZ / "paquete"))
    cripta = fuente.obtener_datos_generales(ID_CRIPTA)
    resolvedor = ResolvedorCatalogo.crear(fuente, tope=25, carpeta=carpeta_cache)
    esqueleto = GestorEsqueleto(fuente)
    esqueleto.cargar(cripta)
    contenido = GestorContenido(fuente, esqueleto, resolvedor=resolvedor)
    mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
    mazmorra.cargar_esqueleto([esqueleto.obtener_sala(i) for i in esqueleto.ids_salas()])
    jugador = Jugador(cripta)
    jugador.vida = jugador.vida_Max = 400          # fuerte, para que la partida dure y se derrote enemigos
    jugador.ataque = 12                            # (de lo contrario las ratas lo matan en pocas acciones)
    inventario = Inventario(cripta.inventario_max)
    inventario.recoger(resolvedor.ficha(ID_ANTIDOTO))      # permite probar la cancelación del veneno
    for _ in range(pergaminos):
        inventario.recoger(resolvedor.ficha(ID_PERGAMINO))     # antes del Motor: no se registra nada
    motor = Motor(semilla, jugador, mazmorra, None, inventario)
    for id_sala in esqueleto.ids_salas():
        mazmorra.cargar_contenido(contenido.asegurar_sala(id_sala), resolvedor.ficha)
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    return motor, mazmorra, resolvedor, esqueleto


def _evento(e):
    return None if e is None else (e.tiempo, e.secuencia, e.tipo, e.valido)


def _dueno(d):
    if hasattr(d, "caras"):
        return ("cierre", tuple(s.destino for s in d.caras))
    if hasattr(d, "instancia") and hasattr(d, "ficha") and not hasattr(d, "vida"):
        return ("trampa", d.instancia)
    if hasattr(d, "actor") and hasattr(d, "tipo"):
        return ("efecto", d.tipo, d.actor.id)
    return ("actor", d.id)


def _foto(motor, mazmorra, esqueleto):
    j, inv = motor.jugador, motor.inventario
    salas = []
    for i in esqueleto.ids_salas():
        if not mazmorra.contenido_cargado(i):
            continue
        s = mazmorra.sala(i)
        salas.append((i, [o for o in s.objetos if o != ID_PERGAMINO],
                      [(t.instancia, t.armada) for t in s.trampas],
                      [(e.id, e.vida, e.Sala_Actual, e.activo, _evento(e.Evento_pendiente)) for e in s.enemigos],
                      [None if x is None else (x.destino, x.cerrada) for x in s.salidas]))
    rastro = list(motor.rastro.tiempos)
    while rastro and rastro[-1] is None:
        rastro.pop()
    return {
        "reloj": motor.reloj, "terminado": motor.terminado, "victoria": motor.victoria,
        "derrotados": motor.enemigos_derrotados, "azar": hash(motor.azar.getstate()),
        "salida_abierta": mazmorra.salida_abierta, "rastro": rastro,
        "jugador": (j.vida, j.velocidad, j.Sala_Actual, j.acciones, getattr(j.arma, "id", None),
                    getattr(j.armadura, "id", None), _evento(j.Evento_pendiente)),
        "cola": (motor.cola.siguiente_secuencia,
                 sorted((e.tiempo, e.secuencia, e.tipo, str(_dueno(e.dueno))) for e in motor.cola.eventos if e.valido)),
        "efectos": [(e.tipo, e.actor.id, e.fin, e.valor, _evento(e.evento), getattr(e, "cambio_real", None))
                    for e in motor.efectos.activos],
        "salas": salas,
        "inventario": ([o.id for o in inv.objetos() if o.clase != CLASE_PERGAMINO],
                       getattr(inv.arma_equipada(), "id", None), getattr(inv.armadura_equipada(), "id", None)),
    }


def _candidatas(motor, mazmorra, paso):
    sala = motor.jugador.Sala_Actual
    c = []
    for d in range(4):
        salida = mazmorra.salida(sala, d)
        if salida is None:
            continue
        if salida.cerrada:
            llave = mazmorra.llave_requerida(sala, d)
            if llave and motor.inventario.tiene_objeto(llave):
                c.append(("abrir", d))
        else:
            c.append(("mover", d))
    for enemigo in mazmorra.enemigos_vivos(sala):
        c.append(("atacar", enemigo.id))
    for id_objeto in mazmorra.sala(sala).objetos:
        if id_objeto != ID_PERGAMINO:
            c.extend([("recoger", id_objeto)] * 2)
    for objeto in motor.inventario.objetos():
        if objeto.clase == CLASE_PERGAMINO:
            continue
        c.append(("soltar", objeto.id))
        if objeto.clase in ("arma", "armadura"):
            c.extend([("equipar", objeto.id)] * 2)
        if objeto.clase in ("pocion", "antidoto", "antorcha"):
            c.extend([("usar", objeto.id)] * 2)
    c.append(("esperar",))
    if paso % 5 == 4:                                  # veneno y velocidad no tienen fuente en el juego aún: se inyectan
        c.extend([("veneno_y_esperar",)] * 2 + [("velocidad_y_esperar",)] * 2)
    for enemigo in mazmorra.enemigos_vivos(sala):      # favorecer el combate: así sí hay muertes que deshacer
        c.extend([("atacar", enemigo.id)] * 3)
    return c


def _ejecutar(motor, resolvedor, a):
    tipo = a[0]
    if tipo == "mover":
        return motor.mover_jugador(a[1])
    if tipo == "abrir":
        return motor.abrir_puerta(a[1], motor.inventario.tiene_objeto)
    if tipo == "atacar":
        return motor.atacar_enemigo(a[1])
    if tipo == "esperar":
        return motor.esperar()
    if tipo == "recoger":
        return motor.recoger(a[1], resolvedor.ficha)
    if tipo == "soltar":
        return motor.soltar(a[1])
    if tipo == "equipar":
        return motor.equipar(a[1])
    if tipo == "usar":
        return motor.usar(a[1])
    if tipo == "veneno_y_esperar":
        motor.efectos.aplicar(Veneno(motor.jugador, 1))
    else:                                              # "velocidad_y_esperar": reprograma la acción pendiente
        motor.efectos.aplicar(Velocidad(motor.jugador, -30, 250))
    return motor.esperar()


def _paso(motor, resolvedor, accion):
    resultado = _ejecutar(motor, resolvedor, accion)
    if resultado == "ok":
        motor.avanzar_hasta_jugador()
    return resultado


def _jugar(semilla, carpeta_cache, conteo):
    motor, mazmorra, resolvedor, esqueleto = _crear_partida(semilla, carpeta_cache)
    x = semilla * 7919 + 13
    guion, fotos = [], [_foto(motor, mazmorra, esqueleto)]
    for paso in range(ACCIONES_POR_PARTIDA):
        if motor.terminado:
            break
        for _ in range(12):                            # una acción rechazada no consume tiempo: se elige otra
            candidatas = _candidatas(motor, mazmorra, paso)
            x = (x * 1103515245 + 12345) % 2147483648
            accion = candidatas[(x >> 8) % len(candidatas)]
            if _paso(motor, resolvedor, accion) == "ok":
                guion.append(accion)
                fotos.append(_foto(motor, mazmorra, esqueleto))
                conteo[accion[0]] = conteo.get(accion[0], 0) + 1
                if accion == ("usar", ID_ANTIDOTO):
                    conteo["usar_antidoto"] = conteo.get("usar_antidoto", 0) + 1
                break
    conteo["enemigos_derrotados"] = conteo.get("enemigos_derrotados", 0) + fotos[-1]["derrotados"]
    return guion, fotos


def _verificar(semilla, guion, fotos, carpeta_cache, total):
    n = len(guion)
    for t in sorted(set(list(range(1, n + 1, 3)) + [n])):
        if t == 0 or fotos[t]["terminado"]:
            continue
        motor, mazmorra, resolvedor, esqueleto = _crear_partida(semilla, carpeta_cache)
        for i in range(t):
            assert _paso(motor, resolvedor, guion[i]) == "ok"
        assert _foto(motor, mazmorra, esqueleto) == fotos[t], f"la reconstrucción difiere (semilla {semilla}, t={t})"
        for k in range(1, min(3, t) + 1):
            assert motor.usar(ID_PERGAMINO) == "ok", f"pergamino rechazado (semilla {semilla}, t={t}, k={k})"
            foto = _foto(motor, mazmorra, esqueleto)
            esperada = fotos[t - k]
            assert foto == esperada, (f"estado restaurado distinto (semilla {semilla}, t={t}, k={k}): "
                                      f"{[c for c in foto if foto[c] != esperada[c]]}")
            total["retrocesos"] += 1
        for i in range(max(t - 3, 0), t):
            assert _paso(motor, resolvedor, guion[i]) == "ok", f"repetición rechazada (semilla {semilla}, acción {i})"
            foto = _foto(motor, mazmorra, esqueleto)
            assert foto == fotos[i + 1], (f"el futuro cambió tras retroceder (semilla {semilla}, acción {i}): "
                                          f"{[c for c in foto if foto[c] != fotos[i + 1][c]]}")
            total["repeticiones"] += 1


def probar_retroceso_completo():
    carpeta_cache = tempfile.mkdtemp()
    total = {"retrocesos": 0, "repeticiones": 0}
    conteo = {}
    try:
        for semilla in SEMILLAS:
            guion, fotos = _jugar(semilla, carpeta_cache, conteo)
            if len(guion) >= 2:
                _verificar(semilla, guion, fotos, carpeta_cache, total)
    finally:
        shutil.rmtree(carpeta_cache, ignore_errors=True)
    # La prueba solo vale si las partidas ejercitaron lo importante:
    for tipo in ("mover", "atacar", "recoger", "soltar", "equipar", "usar", "esperar", "veneno_y_esperar",
                 "velocidad_y_esperar", "usar_antidoto", "enemigos_derrotados"):
        assert conteo.get(tipo, 0) > 0, f"las partidas guionadas nunca hicieron '{tipo}': la prueba no cubre esa acción"
    assert total["retrocesos"] > 200
    return total, conteo


if __name__ == "__main__":
    total, conteo = probar_retroceso_completo()
    print(f"OK: retroceso completo verificado ({total['retrocesos']} retrocesos y {total['repeticiones']} repeticiones; "
          f"acciones: {dict(sorted(conteo.items()))})")
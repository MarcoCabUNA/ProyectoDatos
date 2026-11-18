"""ViajeAutomatico (Lógica, feature 002): reglas de «ir a»: el destino, el paso siguiente y los motivos para parar."""
from DTO.MapaConocidoDTO import ABIERTA
from DTO.ViajeDTO import AMBIGUO, DANO, DESTINO_INVALIDO, ENEMIGOS, LLEGO, TERMINADA, YA_AQUI
from Logic.BusquedaCostoMinimo import paso_desde_cero
from Logic.GrafoMapaConocido import GrafoMapaConocido
from Logic.MapaConocido import MapaConocido
from Logic.Mazmorra import Mazmorra

OK = "ok"


def resolver_destino(mapa: MapaConocido, nombre: str, sala_actual: int) -> tuple[str, int | None]:
    """El código del destino pedido (OK, YA_AQUI, AMBIGUO o DESTINO_INVALIDO) y su sala, si hay una sola."""
    encontradas = mapa.buscar_exploradas(nombre)
    if not encontradas:
        return DESTINO_INVALIDO, None
    if len(encontradas) > 1:
        return AMBIGUO, None
    if encontradas[0] == sala_actual:
        return YA_AQUI, encontradas[0]
    return OK, encontradas[0]


def decidir_paso(grafo: GrafoMapaConocido, mapa: MapaConocido, mazmorra: Mazmorra, sala_actual: int,
                 destino: int) -> tuple[int, int, int] | None:
    """La dirección, la sala vecina y el costo del primer paso de la ruta más barata, o None si no hay ruta."""
    paso = paso_desde_cero(grafo, destino, sala_actual, None)
    if paso is None:
        return None
    vecina, costo = paso
    for direccion in range(4):
        salida = mazmorra.salida(sala_actual, direccion)
        if (salida is not None and salida.destino == vecina and salida.costo == costo
                and mapa.estado_cara(sala_actual, direccion) == ABIERTA):
            return direccion, vecina, costo
    return None


def motivos_de_parada(sala_actual: int, destino: int, hay_enemigos: bool, recibio_dano: bool,
                      terminada: bool) -> list[str]:
    """Los motivos por los que el viaje se detiene después de un paso; vacía si sigue."""
    motivos = []
    if sala_actual == destino:
        motivos.append(LLEGO)
    if hay_enemigos:
        motivos.append(ENEMIGOS)
    if recibio_dano:
        motivos.append(DANO)
    if terminada:
        motivos.append(TERMINADA)
    return motivos

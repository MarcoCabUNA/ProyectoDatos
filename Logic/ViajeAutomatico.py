from DTO.MapaConocidoDTO import ABIERTA
from DTO.ViajeDTO import AMBIGUO, DANO, DESTINO_INVALIDO, ENEMIGOS, LLEGO, TERMINADA, YA_AQUI
from Logic.BusquedaCostoMinimo import paso_desde_cero

OK = "ok"


def resolver_destino(mapa, nombre, sala_actual):
    encontradas = mapa.buscar_exploradas(nombre)
    if not encontradas:
        return DESTINO_INVALIDO, None
    if len(encontradas) > 1:
        return AMBIGUO, None
    if encontradas[0] == sala_actual:
        return YA_AQUI, encontradas[0]
    return OK, encontradas[0]


def decidir_paso(grafo, mapa, mazmorra, sala_actual, destino):
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


def motivos_de_parada(sala_actual, destino, hay_enemigos, recibio_dano, terminada):
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

"""
Ayudantes de prueba de «ir a» (feature 002, integrante 3). No es un archivo de pruebas.

- contexto_de_prueba(cantidad, salidas, sala_jugador, conocidas): un ContextoPartida a mano (sin red, sin carpetas)
  con un Motor real sobre una cripta de letras de tests/ayudas_mapa.py, el mapa ya con `conocidas` exploradas y el
  motor listo para la primera decisión del jugador. Es lo que ServicioLineaTiempo y ArmadorEstado leen del contexto.
- BitacoraPrueba: lo único que ServicioIrA usa de la bitácora (anexar y anexar_comentario), en el orden en que llegan.
- poner_dormido(motor, sala, ficha): un enemigo vivo que NO está activo (se activa al entrar el jugador).
- conocer(motor, salas): deja `salas` exploradas en el mapa sin mover al jugador ni gastar tiempo.
"""
import os
import sys
from types import SimpleNamespace

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.Inventario import Inventario  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from tests.ayudas_mapa import EsqueletoPrueba  # noqa: E402
from tests.ayudas_terreno import LLAVE_FINAL, motor_con, salidas_con_costos  # noqa: E402


class Mensajes(list):
    def a_array(self):
        return list(self)


class EsqueletoCompleto(EsqueletoPrueba):
    def ids_salas(self):
        return [sala.id for sala in self._salas]


class ResolvedorPrueba:
    def ficha(self, id_objeto, contar_acierto=True):
        raise KeyError(id_objeto)

    def sincronizar_usos(self, ids):
        pass

    def version_catalogo(self):
        return "prueba"


class BitacoraPrueba:
    def __init__(self):
        self.lineas = []

    def anexar(self, accion):
        self.lineas.append(("accion", accion))

    def anexar_comentario(self, texto):
        self.lineas.append(("comentario", texto))

    def comentarios(self):
        return [texto for tipo, texto in self.lineas if tipo == "comentario"]


def conocer(motor, salas) -> None:
    jugador = motor.jugador
    donde_estaba = jugador.Sala_Actual
    for sala in salas:
        jugador.Sala_Actual = sala
        motor.mapa.entrar(sala, False)
    jugador.Sala_Actual = donde_estaba
    motor.historial.descartar_intervalo_abierto()


def contexto_de_prueba(cantidad: int, salidas: list[tuple], sala_jugador: int, conocidas=(), bitacora=None,
                       semilla: int = 1, salida_abierta: bool = False):
    salas = salidas_con_costos(cantidad, salidas)
    mazmorra = Mazmorra(sala_salida=cantidad, llave_salida=LLAVE_FINAL)
    mazmorra.cargar_esqueleto(salas)
    for id_sala in range(1, cantidad + 1):
        mazmorra.sala(id_sala).contenido_cargado = True
    mazmorra.salida_abierta = salida_abierta
    motor, mensajes_lista = motor_con(mazmorra, sala_jugador, semilla)
    mensajes = Mensajes()
    motor.fn_mensaje = mensajes.append
    inventario = Inventario(5)
    inventario.historial = motor.historial
    motor.inventario = inventario
    cripta = CriptaDTO(id="c-ir-a", version="1", salas_total=cantidad, paginas=1, salas_por_pagina=50,
                       sala_inicial=sala_jugador, sala_salida=cantidad, llave_salida=LLAVE_FINAL,
                       presupuesto_solicitudes=10, inventario_max=5, jugador_vida_max=30, jugador_ataque=5,
                       jugador_defensa=2, jugador_velocidad=100)
    motor.iniciar()
    motor.avanzar_hasta_jugador()
    conocer(motor, [sala_jugador] + list(conocidas))
    contexto = SimpleNamespace(
        cripta=cripta, nombre_jugador="Ana", semilla=semilla, fuente=None, resolvedor=ResolvedorPrueba(),
        esqueleto=EsqueletoCompleto(salas), contenido=None, mazmorra=mazmorra, jugador=motor.jugador,
        inventario=inventario, motor=motor, mensajes=mensajes, bitacora=bitacora, criterio_vista=None, linea=None,
        resolubilidad=None)
    return contexto


def poner_dormido(motor, sala: int, ficha, instancia: str = "e-1", vida: int | None = None) -> Enemigo:
    enemigo = Enemigo(ficha, instancia, vida, 1, sala)
    motor.mazmorra.sala(sala).enemigos.append(enemigo)
    return enemigo


ID_PERGAMINO = "itm_pergamino_retroceso"
LADO_REAL = 5


def _fuente_cuadricula_con_pergamino():
    from DTO.ObjetoDTO import ObjetoDTO
    from tests.Utilidades import FuenteCuadricula

    class FuenteCuadriculaConPergamino(FuenteCuadricula):
        def listar_criptas(self):
            from DTO.CriptaDTO import ResumenCriptaDTO
            return [ResumenCriptaDTO("cuadricula", "Cuadrícula de prueba", LADO_REAL * LADO_REAL, 1)]

        def obtener_catalogo(self, ids):
            return [ObjetoDTO(id=ID_PERGAMINO, nombre="Pergamino de retroceso", clase="pergamino_retroceso", peso=1,
                              valor=50) for i in ids if i == ID_PERGAMINO]

    return FuenteCuadriculaConPergamino(LADO_REAL)


def servicio_partida_cuadricula(carpeta: str):
    from DTO.ConfiguracionDTO import ConfiguracionDTO
    from Service.ServicioPartida import ServicioPartida
    config = ConfiguracionDTO(offline=True, cache_size=25)
    return ServicioPartida(config, fuente=_fuente_cuadricula_con_pergamino(),
                           carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))


def dar_pergaminos_a(contexto, cantidad: int) -> None:
    from tests.ayudas_linea_tiempo import dar_pergaminos
    dar_pergaminos(contexto, cantidad)

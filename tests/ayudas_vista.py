"""
Ayudas para probar la Vista de Pygame (no es una prueba). La Vista es la real; el Controlador y los servicios también
(paquete offline, carpetas temporales): nada se escribe en cache/, logs/ ni saves/. Necesita pygame.
"""
import os
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import CONFIG_OFFLINE  # noqa: E402
from ayudas_pygame import clic, crear_fabrica, letra, movimiento, pygame, tecla  # noqa: E402

import UIController.ControladorPygame as modulo  # noqa: E402
from UIController.ControladorPygame import DERROTA, JUEGO, ControladorPygame  # noqa: E402

ENTER, ESC = pygame.K_RETURN, pygame.K_ESCAPE
ARRIBA, ABAJO = pygame.K_UP, pygame.K_DOWN


class Recorrido:
    """ControladorPygame real + vista real + servicios reales, en una carpeta temporal. Úsalo con 'with'."""

    def __init__(self, vista):
        self.vista = vista
        self.carpeta = tempfile.mkdtemp()
        self._ruta_original = modulo.RUTA_GUARDADO
        modulo.RUTA_GUARDADO = os.path.join(self.carpeta, "saves", "partida.sav")
        ruta_puntajes = os.path.join(self.carpeta, "puntajes.jsonl")
        self.controlador = ControladorPygame(vista, CONFIG_OFFLINE, crear_fabrica(self.carpeta, ruta_puntajes))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        modulo.RUTA_GUARDADO = self._ruta_original
        shutil.rmtree(self.carpeta, ignore_errors=True)

    def pulsar(self, *codigos):
        for codigo in codigos:
            self.controlador.procesar_evento(tecla(codigo))

    def escribir(self, texto):
        for caracter in texto:
            self.controlador.procesar_evento(letra(caracter))

    def pantalla(self):
        return self.controlador.pantalla()

    def dibujar(self):
        """Dibuja el cuadro actual con la vista real y devuelve el PantallaDTO."""
        pantalla = self.pantalla()
        self.vista.dibujar(pantalla)
        return pantalla

    def centro_del_boton(self, posicion):
        """Dibuja el cuadro actual y devuelve el centro del botón que se VE en esa 'posicion': de arriba a abajo y, a la
        misma altura, de izquierda a derecha. Se ignora el índice que la Vista registró en la zona: si la Vista dijera
        que un botón es el de otro, el clic caería igual donde el jugador lo ve y la prueba lo notaría."""
        self.dibujar()
        botones = [rectangulo for rectangulo, elemento in zip(self.vista._zonas._rectangulos,
                                                              self.vista._zonas._elementos) if elemento.tipo == "boton"]
        botones.sort(key=lambda rectangulo: (rectangulo.top, rectangulo.left))
        assert posicion < len(botones), f"la Vista dibujó {len(botones)} botones y se pidió el {posicion}"
        return botones[posicion].center

    def clic_en_boton(self, posicion):
        self.controlador.procesar_evento(clic(self.centro_del_boton(posicion)))

    def pasar_el_raton_por(self, posicion):
        self.controlador.procesar_evento(movimiento(self.centro_del_boton(posicion)))

    def posicion_del_texto(self, texto):
        """La posición visual del botón cuyo texto es 'texto' en pantalla.opciones (el texto es lo que el jugador lee)."""
        opciones = self.pantalla().opciones
        assert texto in opciones, (texto, opciones)
        return opciones.index(texto)

    def clic_en_texto(self, texto):
        """Clic real sobre el botón que dice 'texto'; la prueba comprueba después que se hizo LO QUE DICE el texto."""
        self.clic_en_boton(self.posicion_del_texto(texto))

    def pasar_el_raton_por_texto(self, texto):
        self.pasar_el_raton_por(self.posicion_del_texto(texto))

    def perder(self):
        """Entra a la sala de las ratas y espera: en el paquete de pruebas la partida se pierde."""
        self.pulsar(ARRIBA)
        for _ in range(100):
            if self.pantalla().pantalla == DERROTA:
                return
            self.pulsar(pygame.K_z)
        raise AssertionError("la partida no terminó")


def las_ocho_pantallas(recorrido, al_dibujar=None):
    """Conduce el controlador por las 8 pantallas y dibuja cada una. Devuelve la lista de (nombre, PantallaDTO).
    La victoria real depende de la llave y del azar: se arma a mano a partir de la derrota real."""
    vistas = []

    def ver(nombre, pantalla=None):
        pantalla = recorrido.dibujar() if pantalla is None else pantalla
        if al_dibujar is not None:
            al_dibujar(nombre, pantalla)
        vistas.append((nombre, pantalla))

    ver("menu")
    recorrido.pulsar(ENTER)
    ver("criptas")
    recorrido.pulsar(ENTER)
    recorrido.escribir("Ana")
    ver("nombre")
    recorrido.pulsar(ENTER)
    assert recorrido.pantalla().pantalla == JUEGO
    ver("juego")
    recorrido.pulsar(ESC)
    ver("pausa")
    recorrido.pulsar(ESC)
    recorrido.perder()
    ver("derrota")
    derrota = recorrido.pantalla()
    victoria = replace(derrota, pantalla="victoria", estado=replace(derrota.estado, resultado="victoria"))
    recorrido.vista.dibujar(victoria)
    if al_dibujar is not None:
        al_dibujar("victoria", victoria)
    vistas.append(("victoria", victoria))
    recorrido.pulsar(ABAJO, ENTER)
    ver("puntajes")
    return vistas


# ================================================================== estados armados a mano (la escena de juego)
from DTO.ActorDTO import ActorDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ObjetoDTO import ObjetoDTO  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402

DIRECCIONES = {"N": N, "S": S, "E": E, "O": O}
_OBJETOS = [("itm_antorcha", "Antorcha", "antorcha"), ("itm_daga_oxidada", "Daga oxidada", "arma"),
            ("itm_pocion_menor", "Poción menor", "pocion"), ("itm_antidoto", "Antídoto", "antidoto"),
            ("itm_llave_bronce", "Llave de bronce", "llave"), ("itm_coraza_cuero", "Coraza de cuero", "armadura")]


def con_sala(estado, id_sala=None, **salidas):
    """El mismo estado en otra sala: 'salidas' son N=, S=, E=, O= con un SalidaDTO (las que no se nombran no tienen salida)."""
    lista = [None, None, None, None]
    for nombre, salida in salidas.items():
        lista[DIRECCIONES[nombre]] = salida
    sala = replace(estado.sala, salidas=lista)
    return replace(estado, sala=sala if id_sala is None else replace(sala, id=id_sala))


def cerrada(destino=99):
    return SalidaDTO(destino, cerrada=True, llave="itm_llave_bronce")


def con_enemigos(estado, cantidad):
    """'cantidad' enemigos (ratas y guardianes, con nombres e ids distintos) y vidas distintas."""
    enemigos = []
    for i in range(cantidad):
        tipo, nombre = ("ent_guardian_oseo", f"Guardián óseo #{i + 1}") if i % 3 == 2 else (
            "ent_rata_gigante", f"Rata gigante #{i + 1}")
        enemigos.append(ActorDTO(f"enemigo-{i + 1}", tipo, nombre, 12 - i % 12, 12, 3, 1, 100, estado.sala.id))
    return replace(estado, enemigos=enemigos)


def con_objetos(estado, cantidad):
    """'cantidad' objetos en el suelo, de los que tienen sprite propio, con nombres de catálogo."""
    objetos = []
    for i in range(cantidad):
        id_objeto, nombre, clase = _OBJETOS[i % len(_OBJETOS)]
        objetos.append(ObjetoDTO(f"{id_objeto}", nombre, clase, 1, 1))
    return replace(estado, objetos_suelo=objetos)


def estado_base(id_sala=3, **salidas):
    """Un estado de partida armado a mano, sin servicios: sala 'id_sala' (la inicial es la 1 y la de salida la 6), el
    jugador herido, sin enemigos ni objetos. 'salidas' como en con_sala."""
    from DTO.EstadoJuegoDTO import EstadoJuegoDTO
    from DTO.InventarioDTO import InventarioDTO
    from DTO.SalaDTO import SalaDTO
    jugador = ActorDTO("jugador", "jugador", "Jugador", 18, 30, 6, 2, 100, id_sala)
    estado = EstadoJuegoDTO(sala=SalaDTO(id_sala, "Sala de prueba", [None] * 4, "v"), jugador=jugador, enemigos=[],
                            objetos_suelo=[], efectos=[], inventario=InventarioDTO([], 0, 0, 10), mensajes=[], reloj=0,
                            sala_inicial=1, sala_salida=6)
    return con_sala(estado, **salidas) if salidas else estado

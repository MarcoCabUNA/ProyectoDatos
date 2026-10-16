"""
ControlesJuego (Interfaz, Integrante 3): los controles de la PARTIDA (teclado y ratón) traducidos a llamadas al
ControladorBackend. Implementan el documento de controles del equipo.

Es la parte del controlador gráfico que vive mientras se juega. Se separa de ControladorPygame (que lleva el flujo
de pantallas: menú, pausa, fin...) porque cambian por razones distintas (los controles contra el recorrido de la
aplicación), se pueden probar por separado y, juntas, pasaban de lo que se lee cómodo en un archivo.

    controles = ControlesJuego(backend, estado_inicial)
    orden = controles.procesar_evento(evento, elemento)   # evento de pygame; elemento: lo que hay bajo el ratón
    controles.estado                                       # el EstadoJuegoDTO vigente (lo que se dibuja)

Controles (la Vista los muestra con PantallaDTO.ayuda, que sale de AYUDA_JUEGO de aquí). El inventario está siempre
visible, así que sus controles no necesitan abrirlo:

    Moverse                  W A S D o flechas
    Atacar                   clic izquierdo sobre un enemigo; o Espacio (ataca al objetivo prefijado, ver abajo)
    Recoger                  clic izquierdo sobre un objeto del suelo
    Abrir una puerta         E (la única puerta cerrada de la sala) o clic izquierdo sobre la puerta
    Esperar                  Z o el botón "Esperar"
    Recorrer el inventario   rueda del ratón o Tab (Mayús + Tab hacia atrás); clic en una casilla la selecciona
    Usar                     U, o doble clic sobre la casilla
    Equipar                  Q, o clic derecho sobre la casilla
    Soltar                   G, o Mayús + clic izquierdo sobre la casilla
    Cambiar la vista         V (real, peso, valor, nombre; el orden real no cambia)
    Pergamino de retroceso   Retroceso o Ctrl + Z
    Guardar / Cargar         Ctrl + S o F5 / Ctrl + L o F9      (las hace ControladorPygame; aquí solo se piden)
    Menú                     Esc

Decisiones donde el documento deja un hueco (están anotadas para poder cambiarlas):
  - Objetivo prefijado: el último enemigo atacado si sigue en la sala; si no, el primero de la lista.
  - Con varias puertas cerradas en la sala, E no sabe cuál abrir: avisa y pide hacer clic sobre la puerta.
  - "Desequipar" no existe en las reglas (§2.7: equipar otra pieza del mismo tipo sustituye a la anterior; soltar
    una pieza equipada la desequipa). Q equipa; para quitarse algo se suelta con G.
  - Arrastrar un objeto fuera del inventario para soltarlo no está implementado: G y Mayús + clic hacen lo mismo.

Reglas:
  - Primero se mira Ctrl, después las teclas sueltas: así Ctrl + S guarda y NO mueve al sur, y Ctrl + Z retrocede y NO
    espera. Mismo motivo para Ctrl + L.
  - Valida la FORMA de lo que se pide (una casilla que ya no existe) antes de llamar al backend. Las reglas del juego
    las decide Lógica; si rechaza una acción, el motivo llega en estado.resultado y se muestra como aviso. Una acción
    rechazada no consume tiempo.
  - No conoce la Vista: recibe lo que hay bajo el ratón (ElementoDTO) ya resuelto. Expone 'estado', 'aviso',
    'objetivo()', 'botones()' y 'ayuda()' para que ControladorPygame los ponga en el PantallaDTO.
"""
from dataclasses import replace

import pygame

from DTO.Direcciones import DIRECCIONES, E, N, O, S
from DTO.ElementoDTO import (ELEMENTO_BOTON, ELEMENTO_ENEMIGO, ELEMENTO_INVENTARIO, ELEMENTO_OBJETO_SUELO,
                             ELEMENTO_PUERTA, ElementoDTO)
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.InventarioDTO import InventarioDTO
from UIController.ControladorBackend import CRITERIOS_INVENTARIO, ControladorBackend, ErrorOperacion

PIDE_PAUSA = "pausa"
PIDE_GUARDAR = "guardar"
PIDE_CARGAR = "cargar"

BOTONES = ("Esperar",)          # los botones de la pantalla de juego; ELEMENTO_BOTON con indice 0 es "Esperar"
DOBLE_CLIC_MS = 400             # dos clics sobre la misma casilla en menos de esto cuentan como doble clic

_TECLAS_DE_DIRECCION = (
    (pygame.K_UP, N), (pygame.K_w, N), (pygame.K_DOWN, S), (pygame.K_s, S),
    (pygame.K_RIGHT, E), (pygame.K_d, E), (pygame.K_LEFT, O), (pygame.K_a, O),
)
_CLIC_IZQUIERDO = 1
_CLIC_DERECHO = 3

AYUDA_JUEGO = (
    "WASD / flechas: moverse",
    "Clic en un enemigo (o Espacio): atacar",
    "Clic en un objeto del suelo: recoger",
    "E (o clic en la puerta): abrir una puerta",
    "Z: esperar",
    "Rueda o Tab: recorrer el inventario",
    "U (o doble clic): usar   Q (o clic derecho): equipar",
    "G (o Mayús + clic): soltar   V: cambiar el orden",
    "Retroceso o Ctrl + Z: pergamino de retroceso",
    "Ctrl + S / F5: guardar   Ctrl + L / F9: cargar",
    "Esc: menú",
)


class ControlesJuego:

    def __init__(self, backend: ControladorBackend, estado: EstadoJuegoDTO, reloj_ms=None, modificadores=None):
        """
        reloj_ms: función que devuelve los milisegundos actuales (por omisión pygame.time.get_ticks). Sirve para
        detectar el doble clic; las pruebas pasan un reloj propio.
        modificadores: función que devuelve las teclas modificadoras pulsadas (por omisión pygame.key.get_mods). Los
        eventos del ratón no traen Mayús, así que se consulta aparte; las pruebas pasan la suya.
        """
        self._backend = backend
        self._reloj_ms = reloj_ms if reloj_ms is not None else pygame.time.get_ticks
        self._modificadores = modificadores if modificadores is not None else pygame.key.get_mods
        self.estado = estado
        self.aviso: str | None = None
        self._objetivo: str | None = None
        self._ultimo_clic: tuple[int, int] | None = None     # (casilla, milisegundos) del último clic en el inventario

    def botones(self) -> list[str]:
        return list(BOTONES)

    def ayuda(self) -> list[str]:
        return list(AYUDA_JUEGO)

    def objetivo(self) -> str | None:
        """El id del enemigo al que atacaría Espacio: el último atacado si sigue aquí; si no, el primero. None si no hay."""
        ids = [enemigo.id for enemigo in self.estado.enemigos]
        if self._objetivo in ids:
            return self._objetivo
        return ids[0] if ids else None

    def procesar_evento(self, evento, elemento: ElementoDTO | None = None) -> str | None:
        """Devuelve PIDE_PAUSA, PIDE_GUARDAR o PIDE_CARGAR cuando el jugador lo pide; en cualquier otro caso, None.
        'elemento' es lo que hay bajo el ratón en un clic (None si nada, o si el evento no es un clic)."""
        if self.estado.terminado:
            return None
        tipo = evento.type
        es_clic = tipo == pygame.MOUSEBUTTONDOWN and evento.button in (_CLIC_IZQUIERDO, _CLIC_DERECHO)
        if tipo != pygame.KEYDOWN and tipo != pygame.MOUSEWHEEL and not es_clic:
            return None             # incluye los botones 4 y 5, que pygame genera además de MOUSEWHEEL
        self.aviso = None
        try:
            if tipo == pygame.KEYDOWN:
                return self._teclado(evento)
            if tipo == pygame.MOUSEWHEEL:
                self._rueda(evento.y)
            else:
                self._clic(evento.button, elemento)
        except ErrorOperacion as error:
            self.aviso = str(error)
        return None

    # ================================================================== teclado
    def _teclado(self, evento) -> str | None:
        tecla = evento.key
        if evento.mod & pygame.KMOD_CTRL:
            if tecla == pygame.K_s:
                return PIDE_GUARDAR
            if tecla == pygame.K_l:
                return PIDE_CARGAR
            if tecla == pygame.K_z:
                self._aplicar(self._backend.retroceder())
            return None             # Ctrl + otra tecla: nada
        direccion = _direccion_de(tecla)
        if direccion is not None:
            self._aplicar(self._backend.mover(direccion))
        elif tecla == pygame.K_e:
            self._abrir_la_puerta_cerrada()
        elif tecla == pygame.K_z:
            self._aplicar(self._backend.esperar())
        elif tecla == pygame.K_SPACE:
            self._atacar_al_objetivo()
        elif tecla == pygame.K_q:
            self._aplicar(self._backend.equipar(self._objeto_visto().id))
        elif tecla == pygame.K_u:
            self._aplicar(self._backend.usar(self._objeto_visto().id))
        elif tecla == pygame.K_g:
            self._aplicar(self._backend.soltar(self._objeto_visto().id))
        elif tecla == pygame.K_v:
            self._ver(self._backend.inventario_ordenar(_criterio_siguiente(self.estado.inventario.criterio)))
        elif tecla == pygame.K_TAB:
            if evento.mod & pygame.KMOD_SHIFT:
                self._ver(self._backend.inventario_anterior())
            else:
                self._ver(self._backend.inventario_siguiente())
        elif tecla == pygame.K_BACKSPACE:
            self._aplicar(self._backend.retroceder())
        elif tecla == pygame.K_F5:
            return PIDE_GUARDAR
        elif tecla == pygame.K_F9:
            return PIDE_CARGAR
        elif tecla == pygame.K_ESCAPE:
            return PIDE_PAUSA
        return None

    def _abrir_la_puerta_cerrada(self) -> None:
        """E: abre la puerta cerrada de la sala. Si hay varias, no adivina: pide hacer clic sobre la que se quiere."""
        salidas = self.estado.sala.salidas
        cerradas = [d for d in range(len(DIRECCIONES)) if salidas[d] is not None and salidas[d].cerrada]
        if not cerradas:
            raise ErrorOperacion("No hay puertas cerradas en esta sala.")
        if len(cerradas) > 1:
            raise ErrorOperacion("Hay varias puertas cerradas: haz clic en la que quieres abrir.")
        self._aplicar(self._backend.abrir(cerradas[0]))

    def _atacar_al_objetivo(self) -> None:
        objetivo = self.objetivo()
        if objetivo is None:
            raise ErrorOperacion("No hay enemigos en esta sala.")
        self._atacar(objetivo)

    def _objeto_visto(self):
        """El objeto que el cursor marca en la vista actual (§4.5: se actúa sobre el que se está viendo)."""
        inventario = self.estado.inventario
        if not inventario.objetos:
            raise ErrorOperacion("El inventario está vacío.")
        return inventario.objetos[inventario.cursor]

    # ================================================================== ratón
    def _rueda(self, desplazamiento: int) -> None:
        """Rueda hacia arriba: objeto anterior; hacia abajo: siguiente."""
        if desplazamiento > 0:
            self._ver(self._backend.inventario_anterior())
        elif desplazamiento < 0:
            self._ver(self._backend.inventario_siguiente())

    def _clic(self, boton: int, elemento: ElementoDTO | None) -> None:
        if elemento is None:
            return
        if elemento.tipo == ELEMENTO_INVENTARIO:
            self._clic_en_el_inventario(boton, elemento.indice)
        elif boton != _CLIC_IZQUIERDO:
            return                  # fuera del inventario, solo cuenta el clic izquierdo
        elif elemento.tipo == ELEMENTO_ENEMIGO:
            self._atacar(_de(self.estado.enemigos, elemento.indice, "enemigo").id)
        elif elemento.tipo == ELEMENTO_OBJETO_SUELO:
            self._aplicar(self._backend.recoger(_de(self.estado.objetos_suelo, elemento.indice, "objeto").id))
        elif elemento.tipo == ELEMENTO_PUERTA:
            self._aplicar(self._backend.abrir(elemento.indice))
        elif elemento.tipo == ELEMENTO_BOTON and elemento.indice == 0:
            self._aplicar(self._backend.esperar())

    def _clic_en_el_inventario(self, boton: int, casilla: int) -> None:
        objeto = _de(self.estado.inventario.objetos, casilla, "objeto")
        if boton == _CLIC_DERECHO:
            self._aplicar(self._backend.equipar(objeto.id))
        elif self._modificadores() & pygame.KMOD_SHIFT:
            self._aplicar(self._backend.soltar(objeto.id))
        else:
            ahora = self._reloj_ms()
            if self._ultimo_clic is not None and self._ultimo_clic[0] == casilla \
                    and ahora - self._ultimo_clic[1] <= DOBLE_CLIC_MS:
                self._aplicar(self._backend.usar(objeto.id))        # doble clic
            else:
                self._llevar_el_cursor_a(casilla)                   # clic simple: seleccionar
                self._ultimo_clic = (casilla, ahora)

    # ================================================================== lo que cambia el estado
    def _atacar(self, id_enemigo: str) -> None:
        self._objetivo = id_enemigo
        self._aplicar(self._backend.atacar(id_enemigo))

    def _aplicar(self, estado: EstadoJuegoDTO) -> None:
        """Una acción del jugador: el estado nuevo reemplaza al anterior. Si fue rechazada, el motivo es el aviso."""
        self.estado = estado
        self._ultimo_clic = None            # el inventario pudo cambiar: un clic anterior ya no cuenta
        if not estado.terminado and estado.resultado is not None:
            self.aviso = estado.resultado

    def _ver(self, inventario: InventarioDTO) -> None:
        """Cambió solo la vista del inventario (no es una acción del jugador): el resto del estado sigue igual."""
        self.estado = replace(self.estado, inventario=inventario)

    def _llevar_el_cursor_a(self, casilla: int) -> None:
        """Mueve el cursor del inventario hasta esa casilla, de a un paso (el backend no tiene 'ir a')."""
        for _ in range(len(self.estado.inventario.objetos)):
            cursor = self.estado.inventario.cursor
            if cursor == casilla:
                return
            self._ver(self._backend.inventario_siguiente() if cursor < casilla else self._backend.inventario_anterior())
            if self.estado.inventario.cursor == cursor:
                return                      # no avanzó (hay objetos repetidos: el servicio los salta)


def _de(lista: list, indice: int, que: str):
    """lista[indice], o un aviso si ese elemento ya no existe (la Vista pudo dibujarlo antes de la última acción)."""
    if not 0 <= indice < len(lista):
        raise ErrorOperacion(f"Ese {que} ya no está.")
    return lista[indice]


def _direccion_de(tecla: int) -> int | None:
    for par in _TECLAS_DE_DIRECCION:
        if par[0] == tecla:
            return par[1]
    return None


def _criterio_siguiente(actual: str | None) -> str | None:
    """Real -> peso -> valor -> nombre -> real."""
    for i in range(len(CRITERIOS_INVENTARIO)):
        if CRITERIOS_INVENTARIO[i] == actual:
            return CRITERIOS_INVENTARIO[(i + 1) % len(CRITERIOS_INVENTARIO)]
    return CRITERIOS_INVENTARIO[0]
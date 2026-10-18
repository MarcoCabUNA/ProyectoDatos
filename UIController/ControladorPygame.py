"""
ControladorPygame (Interfaz, Integrante 3): el recorrido de la aplicación gráfica, sus botones y su bucle principal.

Decide QUÉ pantalla toca, qué botones tiene, qué hace cada botón y cuándo se llama al ControladorBackend. Lo que pasa
DENTRO de la partida (mover, atacar, inventario) lo hace ControlesJuego; aquí solo se le pasan los eventos.

Pantallas (constantes de este archivo; la Vista dibuja según PantallaDTO.pantalla):

    MENU        Comenzar juego | Modo: Online/Offline | Cargar partida | Puntajes | Salir
    CRIPTAS     elegir una de las criptas que ofrece el servicio (o el paquete, en offline) | Volver
    NOMBRE      escribir el nombre del jugador | Aceptar | Volver
    JUEGO       la partida en curso, con el inventario siempre visible | Esperar
    PAUSA       Continuar | Guardar partida | Cargar partida | Salir al menú            (Esc durante la partida)
    VICTORIA    la partida terminó bien: puntaje y reporte | Jugar de nuevo | Ver puntajes | Menú principal
    DERROTA     la partida terminó mal: lo mismo que VICTORIA, con su propio fondo
    PUNTAJES    la tabla de puntajes local | Cambiar el orden | Volver

    MENU --Comenzar--> CRIPTAS --elegir--> NOMBRE --Aceptar--> JUEGO <--Esc/Continuar--> PAUSA
    MENU --Cargar----> NOMBRE ----------------------------------^     JUEGO --termina--> VICTORIA o DERROTA

Cómo funcionan los botones (el reparto entre Controlador y Vista):
  - ESTE controlador decide qué botones tiene cada pantalla y qué hace cada uno (PantallaDTO.opciones). Todas las
    pantallas con botones funcionan igual: arriba y abajo mueven el resaltado, Enter o un clic activan el botón.
  - La VISTA dibuja los botones y sabe dónde quedaron. Cuando hay un clic, este controlador le pregunta
    vista.elemento_en(posición) qué hay ahí; si la respuesta es un botón, lo activa. Pasar el ratón por encima de un
    botón lo deja resaltado (el mismo resaltado que usa el teclado: PantallaDTO.seleccion).

Configuración: la única que define el enunciado es online u offline (--offline). Sale de la línea de comandos y se
puede cambiar en el menú; cada partida nueva crea un ControladorBackend nuevo con la configuración vigente, porque
la fuente de datos cuenta las solicitudes contra el presupuesto de ESA partida. Elegir "Modo" no hace ninguna
solicitud: la red solo se toca al pedir la lista de criptas o al cargar una partida.

Qué NO hace (a propósito):
  - NO dibuja. Dibujar es de la Vista (View/VistaPygame.py); por eso el controlador entrega un PantallaDTO por cuadro.
    Si el controlador dibujara, la Vista dejaría de ser la que presenta y se perdería la separación
    Modelo-Vista-Controlador.
  - NO valida reglas del juego ni llama a Servicios: todo pasa por el ControladorBackend.

Contrato de la Vista (cuatro métodos):
    vista.abrir()                    crea la ventana (aquí se inicia pygame)
    vista.dibujar(pantalla)          dibuja un PantallaDTO
    vista.cerrar()                   cierra la ventana (se llama siempre, aunque el bucle termine por un error)
    vista.elemento_en((x, y))        devuelve un ElementoDTO con lo que hay en ese punto de lo último que dibujó, o None

Los errores esperados (ErrorOperacion) se muestran como aviso en la pantalla actual; ninguno cierra el programa.
Cerrar la ventana con la X termina el bucle de forma controlada desde cualquier pantalla.
"""
from dataclasses import replace

import pygame

from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.ElementoDTO import ELEMENTO_BOTON
from DTO.PantallaDTO import PantallaDTO
from UIController.ControladorBackend import (CRITERIOS_PUNTAJES, LARGO_MAXIMO_NOMBRE, ControladorBackend,
                                             ErrorOperacion)
from UIController.ControlesJuego import PIDE_CARGAR, PIDE_GUARDAR, PIDE_PAUSA, ControlesJuego

MENU = "menu"
CRIPTAS = "criptas"
NOMBRE = "nombre"
JUEGO = "juego"
PAUSA = "pausa"
VICTORIA = "victoria"
DERROTA = "derrota"
PUNTAJES = "puntajes"
_FIN = "fin"                    # estado interno: la Vista recibe VICTORIA o DERROTA, según cómo terminó

FPS = 30
RUTA_GUARDADO = "saves/partida.sav"     # una sola ranura; saves/ no se sube al repositorio (.gitignore)

_OPCION_COMENZAR, _OPCION_MODO, _OPCION_CARGAR, _OPCION_PUNTAJES, _OPCION_SALIR = 0, 1, 2, 3, 4
_OPCION_CONTINUAR, _OPCION_GUARDAR, _OPCION_CARGAR_EN_PAUSA, _OPCION_AL_MENU = 0, 1, 2, 3
_OPCION_JUGAR_DE_NUEVO, _OPCION_VER_PUNTAJES, _OPCION_MENU_PRINCIPAL = 0, 1, 2
_OPCION_ACEPTAR, _OPCION_VOLVER_DE_NOMBRE = 0, 1
_OPCION_CAMBIAR_ORDEN, _OPCION_VOLVER_DE_PUNTAJES = 0, 1

_OPCIONES_PAUSA = ["Continuar", "Guardar partida", "Cargar partida", "Salir al menú"]
_OPCIONES_FIN = ["Jugar de nuevo", "Ver puntajes", "Menú principal"]
_OPCIONES_NOMBRE = ["Aceptar", "Volver"]
_OPCIONES_PUNTAJES = ["Cambiar el orden", "Volver"]

_TECLAS_ENTER = (pygame.K_RETURN, pygame.K_KP_ENTER)
_CLIC_IZQUIERDO = 1
_CLIC_DERECHO = 3

_AYUDA_MENU = ("Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar")
_AYUDA_CRIPTAS = ("Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar", "Esc: volver")
_AYUDA_NOMBRE = ("Escribe tu nombre", "Enter o clic en Aceptar: aceptar", "Esc: volver")
_AYUDA_PAUSA = ("Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar", "Esc: volver a la partida")
_AYUDA_FIN = ("Arriba / Abajo o ratón: elegir", "Enter o clic: aceptar", "Esc: menú principal")
_AYUDA_PUNTAJES = ("Izquierda / Derecha: cambiar el orden", "Enter o clic: aceptar", "Esc: volver")


class ControladorPygame:

    def __init__(self, vista, config: ConfiguracionDTO, fabrica_backend=ControladorBackend, fabrica_controles=ControlesJuego,
                 demora_fin_ms: int = 0, reloj_ms=None):
        """
        vista: cualquier objeto con abrir(), dibujar(pantalla), cerrar() y elemento_en(posicion).
        config: lo que dejó LectorArgumentos (offline, cache_size...).
        fabrica_backend: función que crea un ControladorBackend a partir de la configuración.
        fabrica_controles: función que crea los ControlesJuego a partir de (backend, estado).
        Las dos fábricas las cambian las pruebas (caché y puntajes temporales, reloj propio); en el programa real
        se dejan las clases.
        demora_fin_ms: al terminar la partida, cuánto tiempo más se sigue mostrando la pantalla de juego (con el estado final)
        antes de pasar a la victoria o la derrota; 0 pasa de inmediato. El puntaje se guarda al terminar, no después.
        reloj_ms: función que devuelve los milisegundos actuales (por omisión pygame.time.get_ticks); mide esa demora.
        """
        self._vista = vista
        self._config = config
        self._fabrica = fabrica_backend
        self._fabrica_controles = fabrica_controles
        self._backend = fabrica_backend(config)       # sin partida: sirve para ver los puntajes
        self._activo = True
        self._pantalla = MENU
        self._seleccion = 0
        self._aviso: str | None = None
        self._criptas: list = []
        self._id_cripta: str | None = None
        self._texto = ""                              # el nombre que se está escribiendo
        self._cargando = False                        # en NOMBRE: True si el nombre es para cargar una partida
        self._nombre = ""                             # el último nombre usado
        self._juego: ControlesJuego | None = None
        self._puntaje = None
        self._reporte = None
        self._tabla: list = []
        self._criterio = 0                            # posición en CRITERIOS_PUNTAJES
        self._bajo_el_raton = None                    # el ElementoDTO bajo el ratón en su último movimiento (o None)
        self._demora_fin_ms = demora_fin_ms
        self._reloj_ms = reloj_ms if reloj_ms is not None else pygame.time.get_ticks
        self._fin_en: int | None = None               # cuándo termina la demora del fin (None: no hay demora en curso)
        self._aviso_del_fin: str | None = None        # el aviso del fin que se muestra al terminar la demora
        self._activaciones = 0                        # botones activados y esperas hechas; nunca baja (PantallaDTO.activaciones)

    def activo(self) -> bool:
        return self._activo

    # ================================================================== bucle principal
    def ejecutar(self, fuente_eventos=None) -> None:
        """Procesa eventos y dibuja hasta que el jugador sale. fuente_eventos() devuelve los eventos pendientes
        (por omisión, pygame.event.get); las pruebas pasan una función propia."""
        obtener = pygame.event.get if fuente_eventos is None else fuente_eventos
        reloj = pygame.time.Clock()
        self._vista.abrir()
        try:
            while self._activo:
                for evento in obtener():
                    self.procesar_evento(evento)
                self._vista.dibujar(self.pantalla())
                reloj.tick(FPS)
        finally:
            self._vista.cerrar()

    def procesar_evento(self, evento) -> None:
        if evento.type == pygame.QUIT:
            self._activo = False
            return
        if evento.type == pygame.MOUSEMOTION:
            self._resaltar_el_boton_bajo_el_raton(evento.pos)
            return                                    # mover el ratón no borra el aviso
        if evento.type not in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            return
        self._aviso = None
        self._bajo_el_raton = None                    # una tecla, un clic o la rueda: lo que se mostró ya puede ser otro
        try:
            if self._pantalla == JUEGO:
                self._en_juego(evento)
            elif evento.type == pygame.KEYDOWN:
                self._con_el_teclado(evento)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == _CLIC_IZQUIERDO:
                self._con_un_clic(evento.pos)
        except ErrorOperacion as error:
            self._aviso = str(error)

    def _con_el_teclado(self, evento) -> None:
        if self._pantalla == MENU:
            self._en_menu(evento)
        elif self._pantalla == CRIPTAS:
            self._en_criptas(evento)
        elif self._pantalla == NOMBRE:
            self._en_nombre(evento)
        elif self._pantalla == PAUSA:
            self._en_pausa(evento)
        elif self._pantalla == _FIN:
            self._en_fin(evento)
        elif self._pantalla == PUNTAJES:
            self._en_puntajes(evento)

    # ================================================================== ratón en las pantallas con botones
    def _resaltar_el_boton_bajo_el_raton(self, posicion) -> None:
        elemento = self._vista.elemento_en(posicion)
        self._bajo_el_raton = elemento
        if elemento is not None and elemento.tipo == ELEMENTO_BOTON:
            self._seleccion = elemento.indice
        elif self._pantalla == JUEGO:
            self._seleccion = -1                      # en la partida, sin botón bajo el ratón no hay resaltado

    def _con_un_clic(self, posicion) -> None:
        """Clic izquierdo en una pantalla con botones (la partida lleva sus propios clics en ControlesJuego)."""
        elemento = self._vista.elemento_en(posicion)
        if elemento is not None and elemento.tipo == ELEMENTO_BOTON:
            self._seleccion = elemento.indice
            self._activar(elemento.indice)

    def _activar(self, indice: int) -> None:
        """Lo que hace el botón 'indice' de la pantalla actual. Enter y el clic llegan aquí."""
        self._activaciones += 1
        if self._pantalla == MENU:
            self._activar_en_menu(indice)
        elif self._pantalla == CRIPTAS:
            self._activar_en_criptas(indice)
        elif self._pantalla == NOMBRE:
            self._activar_en_nombre(indice)
        elif self._pantalla == PAUSA:
            self._activar_en_pausa(indice)
        elif self._pantalla == _FIN:
            self._activar_en_fin(indice)
        elif self._pantalla == PUNTAJES:
            self._activar_en_puntajes(indice)

    # ================================================================== lo que la Vista dibuja
    def pantalla(self) -> PantallaDTO:
        self._pasar_al_fin_si_termino_la_demora()
        return replace(self._armar_pantalla(), activaciones=self._activaciones)

    def _armar_pantalla(self) -> PantallaDTO:
        if self._pantalla == MENU:
            return PantallaDTO(MENU, "CRIPTA", self._opciones_del_menu(), self._seleccion,
                               aviso=self._aviso, ayuda=list(_AYUDA_MENU))
        if self._pantalla == CRIPTAS:
            return PantallaDTO(CRIPTAS, "Elige una cripta", self._opciones_de_criptas(), self._seleccion,
                               aviso=self._aviso, ayuda=list(_AYUDA_CRIPTAS))
        if self._pantalla == NOMBRE:
            titulo = "Nombre para cargar la partida" if self._cargando else "¿Cómo te llamas?"
            return PantallaDTO(NOMBRE, titulo, list(_OPCIONES_NOMBRE), self._seleccion, texto=self._texto,
                               aviso=self._aviso, ayuda=list(_AYUDA_NOMBRE))
        if self._pantalla == JUEGO:
            return PantallaDTO(JUEGO, opciones=self._juego.botones(), seleccion=self._seleccion,
                               aviso=self._aviso or self._juego.aviso, ayuda=self._juego.ayuda(),
                               estado=self._juego.estado, objetivo=self._juego.objetivo(),
                               elemento_bajo_el_raton=self._bajo_el_raton)
        if self._pantalla == PAUSA:
            return PantallaDTO(PAUSA, "Pausa", list(_OPCIONES_PAUSA), self._seleccion, aviso=self._aviso,
                               ayuda=list(_AYUDA_PAUSA), estado=self._juego.estado)
        if self._pantalla == _FIN:
            estado = self._juego.estado
            return PantallaDTO(VICTORIA if estado.resultado == "victoria" else DERROTA,
                               opciones=list(_OPCIONES_FIN), seleccion=self._seleccion, aviso=self._aviso,
                               ayuda=list(_AYUDA_FIN), estado=estado, puntaje=self._puntaje, reporte=self._reporte)
        return PantallaDTO(PUNTAJES, "Puntajes", list(_OPCIONES_PUNTAJES), self._seleccion, aviso=self._aviso,
                           ayuda=list(_AYUDA_PUNTAJES), puntajes=self._tabla, criterio=CRITERIOS_PUNTAJES[self._criterio])

    def _opciones_del_menu(self) -> list[str]:
        modo = "Offline" if self._config.offline else "Online"
        return ["Comenzar juego", f"Modo: {modo}", "Cargar partida", "Puntajes", "Salir"]

    def _opciones_de_criptas(self) -> list[str]:
        return [f"{c.nombre} - {c.salas} salas, dificultad {c.dificultad}" for c in self._criptas] + ["Volver"]

    # ================================================================== menú y configuración
    def _en_menu(self, evento) -> None:
        if self._navegar(evento, len(self._opciones_del_menu())):
            self._activar_en_menu(self._seleccion)

    def _activar_en_menu(self, indice: int) -> None:
        if indice == _OPCION_COMENZAR:
            self._comenzar()
        elif indice == _OPCION_MODO:
            self._config = replace(self._config, offline=not self._config.offline)
        elif indice == _OPCION_CARGAR:
            self._backend = self._fabrica(self._config)
            self._pedir_nombre(cargando=True)
        elif indice == _OPCION_PUNTAJES:
            self._ver_puntajes()
        elif indice == _OPCION_SALIR:
            self._activo = False

    def _comenzar(self) -> None:
        backend = self._fabrica(self._config)           # partida nueva = servicios nuevos (su propio conteo de solicitudes)
        criptas = backend.criptas()                     # si falla (sin red...), el aviso se ve en la pantalla de origen
        if not criptas:
            raise ErrorOperacion("No hay ninguna cripta disponible.")
        self._backend = backend
        self._criptas = criptas
        self._ir_a(CRIPTAS)

    def _en_criptas(self, evento) -> None:
        if evento.key == pygame.K_ESCAPE:
            self._ir_a(MENU)
        elif self._navegar(evento, len(self._criptas) + 1):
            self._activar_en_criptas(self._seleccion)

    def _activar_en_criptas(self, indice: int) -> None:
        if indice >= len(self._criptas):                # el último botón es "Volver"
            self._ir_a(MENU)
        else:
            self._id_cripta = self._criptas[indice].id
            self._pedir_nombre(cargando=False)

    # ================================================================== nombre del jugador
    def _pedir_nombre(self, cargando: bool) -> None:
        self._cargando = cargando
        self._texto = self._nombre
        self._ir_a(NOMBRE)

    def _en_nombre(self, evento) -> None:
        if evento.key == pygame.K_ESCAPE:
            self._ir_a(MENU)
        elif evento.key in _TECLAS_ENTER:
            self._activaciones += 1
            self._activar_en_nombre(_OPCION_ACEPTAR)
        elif evento.key == pygame.K_BACKSPACE:
            self._texto = self._texto[:-1]
        elif len(evento.unicode) == 1 and evento.unicode.isprintable() and len(self._texto) < LARGO_MAXIMO_NOMBRE:
            self._texto += evento.unicode

    def _activar_en_nombre(self, indice: int) -> None:
        if indice == _OPCION_VOLVER_DE_NOMBRE:
            self._ir_a(MENU)
            return
        if self._cargando:
            estado = self._backend.cargar(RUTA_GUARDADO, self._texto)
        else:
            estado = self._backend.iniciar(self._id_cripta, self._texto)
        self._nombre = self._texto.strip()
        self._juego = self._fabrica_controles(self._backend, estado)
        self._ir_a(JUEGO)

    # ================================================================== partida, pausa y fin
    def _en_juego(self, evento) -> None:
        if self._fin_en is not None:                    # en la demora del fin la partida ya terminó: los controles no hacen nada
            return
        es_clic = evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (_CLIC_IZQUIERDO, _CLIC_DERECHO)
        elemento = self._vista.elemento_en(evento.pos) if es_clic else None   # la rueda no necesita saber qué hay debajo
        espera = self._es_esperar(evento, elemento)
        orden = self._juego.procesar_evento(evento, elemento)
        if espera and self._juego.aviso is None:        # esperar suena; si el backend la rechazó, no
            self._activaciones += 1
        if self._juego.estado.terminado:
            self._terminar_partida()
        elif orden == PIDE_PAUSA:
            self._ir_a(PAUSA)
        elif orden == PIDE_GUARDAR:
            self._guardar_partida()
        elif orden == PIDE_CARGAR:
            self._cargar_partida()

    @staticmethod
    def _es_esperar(evento, elemento) -> bool:
        """El clic en el botón Esperar, o la tecla Z (con Ctrl es retroceder, no esperar)."""
        if evento.type == pygame.KEYDOWN:
            return evento.key == pygame.K_z and not evento.mod & pygame.KMOD_CTRL
        return evento.type == pygame.MOUSEBUTTONDOWN and evento.button == _CLIC_IZQUIERDO \
            and elemento is not None and elemento.tipo == ELEMENTO_BOTON

    def _guardar_partida(self) -> None:
        bytes_escritos = self._backend.guardar(RUTA_GUARDADO)
        self._aviso = f"Partida guardada ({bytes_escritos} bytes)."

    def _cargar_partida(self) -> None:
        estado = self._backend.cargar(RUTA_GUARDADO, self._nombre)
        self._juego = self._fabrica_controles(self._backend, estado)
        self._ir_a(JUEGO)
        self._aviso = "Partida cargada."

    def _terminar_partida(self) -> None:
        aviso = None
        try:
            self._puntaje = self._backend.finalizar()
        except ErrorOperacion as error:                 # el fin se muestra igual aunque no se pueda guardar el puntaje
            self._puntaje = None
            aviso = f"No se pudo guardar el puntaje: {error}"
        self._reporte = self._backend.reporte()
        if self._demora_fin_ms > 0:                     # se sigue en JUEGO con el estado final; el puntaje ya está guardado
            self._fin_en = self._reloj_ms() + self._demora_fin_ms
            self._aviso_del_fin = aviso
            return
        self._ir_a(_FIN)
        self._aviso = aviso

    def _pasar_al_fin_si_termino_la_demora(self) -> None:
        if self._fin_en is not None and self._reloj_ms() >= self._fin_en:
            self._ir_a(_FIN)
            self._aviso = self._aviso_del_fin

    def _en_pausa(self, evento) -> None:
        if evento.key == pygame.K_ESCAPE:
            self._ir_a(JUEGO)
        elif self._navegar(evento, len(_OPCIONES_PAUSA)):
            self._activar_en_pausa(self._seleccion)

    def _activar_en_pausa(self, indice: int) -> None:
        if indice == _OPCION_CONTINUAR:
            self._ir_a(JUEGO)
        elif indice == _OPCION_GUARDAR:
            self._guardar_partida()                     # se queda en la pausa para que se vea el aviso
        elif indice == _OPCION_CARGAR_EN_PAUSA:
            self._cargar_partida()
        elif indice == _OPCION_AL_MENU:
            self._ir_a(MENU)

    def _en_fin(self, evento) -> None:
        if evento.key == pygame.K_ESCAPE:
            self._ir_a(MENU)
        elif self._navegar(evento, len(_OPCIONES_FIN)):
            self._activar_en_fin(self._seleccion)

    def _activar_en_fin(self, indice: int) -> None:
        if indice == _OPCION_JUGAR_DE_NUEVO:
            self._comenzar()
        elif indice == _OPCION_VER_PUNTAJES:
            self._ver_puntajes()
        elif indice == _OPCION_MENU_PRINCIPAL:
            self._ir_a(MENU)

    # ================================================================== puntajes
    def _ver_puntajes(self) -> None:
        self._criterio = 0
        self._tabla = self._backend.tabla_puntajes(CRITERIOS_PUNTAJES[0])
        self._ir_a(PUNTAJES)

    def _en_puntajes(self, evento) -> None:
        if evento.key == pygame.K_ESCAPE:
            self._ir_a(MENU)
        elif evento.key == pygame.K_LEFT:
            self._cambiar_orden(-1)
        elif evento.key == pygame.K_RIGHT:
            self._cambiar_orden(1)
        elif self._navegar(evento, len(_OPCIONES_PUNTAJES)):
            self._activar_en_puntajes(self._seleccion)

    def _activar_en_puntajes(self, indice: int) -> None:
        if indice == _OPCION_CAMBIAR_ORDEN:
            self._cambiar_orden(1)
        elif indice == _OPCION_VOLVER_DE_PUNTAJES:
            self._ir_a(MENU)

    def _cambiar_orden(self, paso: int) -> None:
        criterio = (self._criterio + paso) % len(CRITERIOS_PUNTAJES)
        self._tabla = self._backend.tabla_puntajes(CRITERIOS_PUNTAJES[criterio])
        self._criterio = criterio

    # ================================================================== interno
    def _ir_a(self, pantalla: str) -> None:
        self._pantalla = pantalla
        self._fin_en = None
        self._seleccion = -1 if pantalla == JUEGO else 0
        self._aviso = None
        self._bajo_el_raton = None

    def _navegar(self, evento, cantidad: int) -> bool:
        """Arriba y abajo mueven el resaltado (dando la vuelta). True si el jugador pulsó Enter."""
        if evento.key == pygame.K_UP:
            self._seleccion = (self._seleccion - 1) % cantidad
        elif evento.key == pygame.K_DOWN:
            self._seleccion = (self._seleccion + 1) % cantidad
        if evento.key in _TECLAS_ENTER:
            self._activaciones += 1                       # Enter activa el botón resaltado
            return True
        return False
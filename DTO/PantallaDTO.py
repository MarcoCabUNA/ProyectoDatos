"""
PantallaDTO (Integrante 3): todo lo que la Vista gráfica necesita para dibujar UN cuadro. Es el "Model de la
GUI" de la arquitectura: la Vista no conoce al Controlador ni a los Servicios, solo recibe este DTO y lo dibuja.

Lo arma ControladorPygame.pantalla() y lo recibe vista.dibujar(pantalla). Los campos que no aplican a la
pantalla actual quedan en su valor por omisión (None o vacío).

    pantalla   cuál se dibuja: "menu", "criptas", "nombre", "juego", "pausa", "victoria", "derrota", "puntajes".
               "victoria" y "derrota" son dos pantallas distintas (fondos/fondo_victoria y fondo_derrota), así la
               Vista elige el fondo sin tener que mirar el resultado de la partida
    titulo     encabezado de la pantalla
    opciones   los BOTONES de la pantalla, ya con su texto. En "juego" es el botón "Esperar". La Vista los dibuja y,
               cuando el jugador hace clic, el Controlador se entera con vista.elemento_en (ver ElementoDTO)
    seleccion  posición del botón resaltado en 'opciones' (el del teclado o el que está bajo el ratón); -1 si ninguno
    texto      lo que el jugador va escribiendo (pantalla "nombre")
    aviso      un mensaje breve para el jugador: un error, o por qué una acción fue rechazada; None si no hay
    ayuda      una línea por cada tecla o gesto que sirve en esta pantalla (así la Vista no repite los controles)
    estado     el EstadoJuegoDTO de la partida ("juego", "pausa", "victoria" y "derrota"). El inventario es
               estado.inventario y está siempre visible durante la partida
    objetivo   id del enemigo al que atacaría la tecla Espacio ("juego"); la Vista puede resaltarlo. None si no hay
    puntaje    la fila de puntaje de la partida terminada ("victoria" y "derrota"); None si no se pudo guardar
    reporte    solicitudes de red y caché de la partida terminada ("victoria" y "derrota")
    puntajes   la tabla de puntajes ya ordenada ("puntajes")
    criterio   el criterio con que está ordenada esa tabla
    elemento_bajo_el_raton   lo que había bajo el ratón en su último movimiento ("juego"); None si el ratón no se ha
               movido desde la última tecla, clic o rueda. La Vista lo usa para mostrar el nombre de un objeto del suelo
    activaciones   cuántas veces se activó un botón (con el ratón o con Enter) y cuántas veces se esperó en la partida
               (botón Esperar o tecla Z). Nunca se reinicia; la Vista toca un sonido cuando sube

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass, field

from DTO.ElementoDTO import ElementoDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.PuntajeDTO import PuntajeDTO
from DTO.ReporteDatosDTO import ReporteDatosDTO


@dataclass(frozen=True)
class PantallaDTO:
    pantalla: str
    titulo: str = ""
    opciones: list[str] = field(default_factory=list)
    seleccion: int = 0
    texto: str = ""
    aviso: str | None = None
    ayuda: list[str] = field(default_factory=list)
    estado: EstadoJuegoDTO | None = None
    objetivo: str | None = None
    puntaje: PuntajeDTO | None = None
    reporte: ReporteDatosDTO | None = None
    puntajes: list[PuntajeDTO] = field(default_factory=list)
    criterio: str | None = None
    elemento_bajo_el_raton: ElementoDTO | None = None
    activaciones: int = 0
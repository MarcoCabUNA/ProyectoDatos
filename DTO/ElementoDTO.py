"""
ElementoDTO (Integrante 3): qué hay bajo un punto de la pantalla.

La Vista sabe dónde dibujó cada cosa; el Controlador sabe qué significa un clic sobre ella. Para no mezclar las dos
cosas, el Controlador le pregunta a la Vista `vista.elemento_en((x, y))` y la Vista contesta con uno de estos DTO
(o None si en ese punto no hay nada). La Vista solo dice QUÉ hay y CUÁL es; no decide qué hacer.

    tipo     ELEMENTO_BOTON         un botón de la pantalla; indice = posición en PantallaDTO.opciones
             ELEMENTO_ENEMIGO       un enemigo de la sala; indice = posición en estado.enemigos
             ELEMENTO_OBJETO_SUELO  un objeto del suelo; indice = posición en estado.objetos_suelo
             ELEMENTO_PUERTA        una puerta; indice = dirección (N=0, S=1, E=2, O=3, de DTO/Direcciones.py)
             ELEMENTO_INVENTARIO    una casilla del inventario; indice = posición en estado.inventario.objetos

Regla de los DTOs: solo transportan datos. Las constantes de tipo viven aquí para que la Vista y el Controlador
usen exactamente las mismas palabras.
"""
from dataclasses import dataclass

ELEMENTO_BOTON = "boton"
ELEMENTO_ENEMIGO = "enemigo"
ELEMENTO_OBJETO_SUELO = "objeto_suelo"
ELEMENTO_PUERTA = "puerta"
ELEMENTO_INVENTARIO = "inventario"


@dataclass(frozen=True)
class ElementoDTO:
    tipo: str
    indice: int
"""
AlmacenSprites (Vista): carga, recorta, escala y guarda en caché los recursos gráficos, y aplica las reglas de
búsqueda de assets/LEEME.md. El nombre de archivo ES el id del catálogo: ningún id de cripta está escrito aquí (§9).

Reglas (todas terminan en una figura dibujada: un sprite que falta nunca rompe el juego):
    actor     <carpeta>/<tipo>_<estado>_<n>.png  ->  <tipo>_idle_<n>  ->  (solo enemigos) enemigo_<estado>  ->
              enemigo_idle  ->  figura.   Carpetas: personajes/ para "jugador", enemigos/ para los demás.
    objeto    objetos/<id>.png  ->  objetos/clase_<clase>.png  ->  objetos/objeto.png  ->  figura.
    fondo     fondos/<nombre>.jpg  ->  fondo liso.
    ui        ui/<nombre>.png  ->  figura.   Las puertas son para el borde norte: puerta() las rota.
    fotogramas   n = 1, 2, 3... hasta que falte uno; no se escribe cuántos hay.

Seguridad: todo id que venga de un DTO pasa por es_nombre_seguro ANTES de armar una ruta; si no pasa, se trata como
"no existe" (la búsqueda sigue con el respaldo).

Anclaje: cada fotograma se recorta a su contenido real (Surface.get_bounding_rect). Así, anclar el midbottom de la
imagen devuelta pone los pies en la misma línea aunque los lienzos y los márgenes sean distintos.

Caché (§7 del enunciado: nada de dict ni set): dos listas paralelas, _claves y _valores, con búsqueda lineal (hay unas
decenas de recursos). También se recuerdan los que NO existen (valor None) para no volver a mirar el disco.

Hay que llamar a las funciones de carga DESPUÉS de crear la ventana (convert_alpha() la necesita): sin ventana lanzan
RuntimeError y no recuerdan nada. Un archivo dañado, en cambio, cuenta como "no existe" y cae al respaldo.
"""
import os
from dataclasses import dataclass

import pygame

from DTO.Direcciones import E, N, O, S
from Security.ValidadorAcceso import es_nombre_seguro
from View import Componentes as c

PERSONAJES, ENEMIGOS, OBJETOS, FONDOS, UI = "personajes", "enemigos", "objetos", "fondos", "ui"
JUGADOR = "jugador"
GENERICO = "enemigo"                        # conjunto de respaldo de cualquier enemigo sin sprites propios
RESPALDO_OBJETO = "objeto"
ESTADO_BASE = "idle"
ORIGEN_FIGURA = "figura"                    # ConjuntoSprites.origen cuando no había archivo y se dibujó una figura

# Grados antihorarios de pygame.transform.rotate para cada dirección (los sprites miran al norte).
_GIRO = [0, 180, 270, 90]                   # indexado por N=0, S=1, E=2, O=3
assert (N, S, E, O) == (0, 1, 2, 3)

_ACTOR_FIGURA = (400, 500)                  # tamaño de la figura de respaldo de un actor, en píxeles "originales"
_COLOR_FIGURA = (150, 60, 60)
_COLOR_FONDO_LISO = (20, 16, 24)
_COLOR_UI = (90, 70, 60)


def es_de_respaldo(conjunto: "ConjuntoSprites") -> bool:
    """True si el actor se dibuja con el conjunto genérico de enemigos o con la figura de respaldo (no tiene sprites
    propios). Se reconoce por 'origen', no por el nombre del enemigo."""
    return conjunto.origen == ORIGEN_FIGURA or conjunto.origen.startswith(f"{ENEMIGOS}/{GENERICO}_")


@dataclass(frozen=True)
class ConjuntoSprites:
    """fotogramas: superficies ya recortadas y escaladas, listas para anclar por midbottom. origen: de dónde salieron
    ("<carpeta>/<nombre>_<estado>", "objetos/<id>", ... o ORIGEN_FIGURA si se dibujó una figura)."""
    fotogramas: list
    origen: str


class AlmacenSprites:

    def __init__(self, ruta_assets: str):
        self._ruta = ruta_assets
        self._claves: list[str] = []
        self._valores: list = []
        self.accesos_disco = 0              # cuántas veces se miró el disco (las pruebas comprueban la caché con esto)

    @property
    def entradas_cache(self) -> int:
        return len(self._claves)

    # ================================================================== lo que pide la Vista
    def actor(self, tipo: str, estado: str = ESTADO_BASE, escala: float = 1.0, nombre: str = "") -> ConjuntoSprites:
        """Fotogramas de un actor (el jugador tiene tipo 'jugador'). 'escala' multiplica los píxeles originales.
        'nombre' solo sirve para la inicial de la figura de respaldo: por eso los sprites reales se guardan sin él
        (ocho ratas con nombres distintos comparten un solo conjunto) y la figura se guarda con la inicial."""
        estado = estado if es_nombre_seguro(estado) else ESTADO_BASE
        inicial = (nombre or tipo or "?")[:1].upper()
        clave = f"actor|{tipo}|{estado}|{escala}"
        clave_figura = f"{clave}|{inicial}"
        guardado = self._recordado(clave)
        if guardado is None:
            guardado = self._recordado(clave_figura)
        if guardado is not None:
            return guardado
        carpeta = PERSONAJES if tipo == JUGADOR else ENEMIGOS
        candidatos = [(tipo, estado), (tipo, ESTADO_BASE)]
        if carpeta == ENEMIGOS:
            candidatos += [(GENERICO, estado), (GENERICO, ESTADO_BASE)]
        for nombre_conjunto, estado_buscado in candidatos:
            crudos = self._conjunto(carpeta, nombre_conjunto, estado_buscado)
            if crudos:
                fotogramas = [self._escalar(self._recortar(imagen), escala) for imagen in crudos]
                origen = f"{carpeta}/{nombre_conjunto}_{estado_buscado}"
                return self._recordar(clave, ConjuntoSprites(fotogramas, origen))
        figura = self._figura(_ACTOR_FIGURA, escala, inicial)
        return self._recordar(clave_figura, ConjuntoSprites([figura], ORIGEN_FIGURA))

    def actor_a_altura(self, tipo: str, alto: int, estado: str = ESTADO_BASE, nombre: str = "") -> ConjuntoSprites:
        """Como actor(), pero la escala se elige para que el primer fotograma (ya recortado a su contenido) mida 'alto'
        píxeles: así un jugador, una rata y un enemigo genérico, de tamaños originales muy distintos, se ven parejos."""
        alto_original = self.actor(tipo, estado, 1.0, nombre).fotogramas[0].get_height()
        return self.actor(tipo, estado, round(max(1, alto) / alto_original, 4), nombre)

    def objeto(self, id_objeto: str, clase: str, lado: int) -> ConjuntoSprites:
        """El sprite de un objeto, ajustado para caber en un cuadrado de 'lado' píxeles."""
        clave = f"objeto|{id_objeto}|{clase}|{lado}"
        guardado = self._recordado(clave)
        if guardado is not None:
            return guardado
        for nombre in (id_objeto, f"clase_{clase}", RESPALDO_OBJETO):
            imagen = self._imagen(OBJETOS, nombre, "png")
            if imagen is not None:
                reducida = self._escalar(imagen, lado / max(imagen.get_size()))
                return self._recordar(clave, ConjuntoSprites([reducida], f"{OBJETOS}/{nombre}"))
        return self._recordar(clave, ConjuntoSprites([self._figura((lado, lado), 1.0, "?")], ORIGEN_FIGURA))

    def aura_de_objeto(self, id_objeto: str, clase: str, lado: int, margen: int, color: tuple, intensidad: int):
        """El resplandor de un objeto del suelo: su silueta teñida de 'color' y difuminada, en un lienzo transparente
        'margen' píxeles más grande por cada lado que el sprite. Se prepara una vez por objeto y se guarda en la caché."""
        clave = f"aura|{id_objeto}|{clase}|{lado}|{margen}|{color}|{intensidad}"
        guardada = self._recordado(clave)
        if guardada is not None:
            return guardada
        sprite = self.objeto(id_objeto, clase, lado).fotogramas[0]
        tamano = (sprite.get_width() + 2 * margen, sprite.get_height() + 2 * margen)
        silueta = pygame.mask.from_surface(sprite).to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
        lienzo = pygame.Surface(tamano, pygame.SRCALPHA)
        for dx in (-2, 0, 2):                                         # la silueta engordada un poco y luego difuminada
            for dy in (-2, 0, 2):
                lienzo.blit(silueta, (margen + dx, margen + dy))
        pequeno = pygame.transform.smoothscale(lienzo, (max(1, tamano[0] // 3), max(1, tamano[1] // 3)))
        difuso = pygame.transform.smoothscale(pequeno, tamano)
        difuso.fill((255, 255, 255, intensidad), special_flags=pygame.BLEND_RGBA_MULT)
        return self._recordar(clave, difuso)

    def silueta_blanca(self, sprite: pygame.Surface) -> pygame.Surface:
        """La silueta de 'sprite' toda de DESTELLO_COLOR (opaca donde el sprite no es transparente): el destello del golpeado.
        Se prepara una vez por sprite y se guarda en la caché (junto al sprite, para que su id no se reutilice)."""
        clave = f"silueta|{id(sprite)}|{sprite.get_size()}"
        guardada = self._recordado(clave)
        if guardada is not None:
            return guardada[1]
        silueta = pygame.mask.from_surface(sprite).to_surface(setcolor=(*c.DESTELLO_COLOR, 255), unsetcolor=(0, 0, 0, 0))
        self._recordar(clave, (sprite, silueta))
        return silueta

    def fondo(self, nombre: str, tamano: tuple[int, int]) -> ConjuntoSprites:
        """Un fondo de pantalla completa, suavizado hasta 'tamano'. Sin archivo, un fondo liso."""
        clave = f"fondo|{nombre}|{tamano}"
        guardado = self._recordado(clave)
        if guardado is not None:
            return guardado
        imagen = self._imagen(FONDOS, nombre, "jpg")
        if imagen is None:
            liso = pygame.Surface(tamano)
            liso.fill(_COLOR_FONDO_LISO)
            return self._recordar(clave, ConjuntoSprites([liso], ORIGEN_FIGURA))
        ajustado = pygame.transform.smoothscale(imagen, tamano)
        return self._recordar(clave, ConjuntoSprites([ajustado], f"{FONDOS}/{nombre}"))

    def fondo_ambientado(self, nombre: str, tamano: tuple[int, int], intensidad: float) -> ConjuntoSprites:
        """El fondo() con la ambientación lúgubre (receta en Componentes.AMBIENTE_*), calculada una sola vez por
        (fondo, tamaño, intensidad) y guardada en la caché. Con intensidad 0 devuelve el mismo conjunto que fondo()."""
        intensidad = min(1.0, max(0.0, intensidad))
        original = self.fondo(nombre, tamano)
        if intensidad == 0:
            return original
        clave = f"fondo_ambientado|{nombre}|{tamano}|{intensidad}"
        guardado = self._recordado(clave)
        if guardado is not None:
            return guardado
        base = original.fotogramas[0]
        receta = base.copy()
        grises = pygame.transform.grayscale(base)
        grises.set_alpha(round(255 * c.AMBIENTE_GRIS))
        receta.blit(grises, (0, 0))
        receta.fill(c.AMBIENTE_TINTE, special_flags=pygame.BLEND_RGB_MULT)
        receta.blit(self._vineta(tamano), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        resultado = base.copy()
        receta.set_alpha(round(255 * intensidad))
        resultado.blit(receta, (0, 0))
        return self._recordar(clave, ConjuntoSprites([resultado], f"{original.origen}+ambiente"))

    @staticmethod
    def _vineta(tamano: tuple[int, int]) -> pygame.Surface:
        """Degradado radial (blanco al centro, oscuro en las esquinas) calculado en miniatura y ampliado a 'tamano'."""
        ancho, alto = c.AMBIENTE_VINETA_TAMANO
        miniatura = pygame.Surface((ancho, alto))
        for y in range(alto):
            for x in range(ancho):
                dx, dy = (x + 0.5) / ancho * 2 - 1, (y + 0.5) / alto * 2 - 1
                distancia = min(1.0, (dx * dx + dy * dy) / 2)                 # 0 al centro, 1 en las esquinas
                nivel = round(255 * (1 - c.AMBIENTE_VINETA * distancia))
                miniatura.set_at((x, y), (nivel, nivel, nivel))
        return pygame.transform.smoothscale(miniatura, tamano)

    def ui(self, nombre: str, escala: float = 1.0) -> ConjuntoSprites:
        """Una imagen de ui/ (pixel art: se amplía sin suavizar)."""
        clave = f"ui|{nombre}|{escala}"
        guardado = self._recordado(clave)
        if guardado is not None:
            return guardado
        imagen = self._imagen(UI, nombre, "png")
        if imagen is None:
            return self._recordar(clave, ConjuntoSprites([self._figura((64, 64), escala, "")], ORIGEN_FIGURA))
        return self._recordar(clave, ConjuntoSprites([self._escalar(imagen, escala)], f"{UI}/{nombre}"))

    def puerta(self, nombre: str, direccion: int, escala: float = 1.0) -> ConjuntoSprites:
        """Una puerta de ui/ girada hacia 'direccion' (N, S, E u O de DTO/Direcciones.py)."""
        base = self.ui(nombre, escala)
        grados = _GIRO[direccion]
        if grados == 0:
            return base
        clave = f"puerta|{nombre}|{direccion}|{escala}"
        guardado = self._recordado(clave)
        if guardado is not None:
            return guardado
        girada = pygame.transform.rotate(base.fotogramas[0], grados)
        return self._recordar(clave, ConjuntoSprites([girada], base.origen))

    # ================================================================== caché (listas paralelas)
    def _buscar(self, clave: str) -> int:
        for i in range(len(self._claves)):
            if self._claves[i] == clave:
                return i
        return -1

    def _recordado(self, clave: str):
        i = self._buscar(clave)
        return None if i < 0 else self._valores[i]

    def _recordar(self, clave: str, valor):
        self._claves.append(clave)
        self._valores.append(valor)
        return valor

    # ================================================================== disco
    def _imagen(self, carpeta: str, nombre: str, extension: str):
        """La imagen original (convertida) o None si no existe o el nombre no es seguro. Recuerda también los fallos."""
        clave = f"img|{carpeta}|{nombre}|{extension}"
        i = self._buscar(clave)
        if i >= 0:
            return self._valores[i]
        if pygame.display.get_surface() is None:
            # No se recuerda: sería un fallo de uso (falta la ventana), no una propiedad del archivo.
            raise RuntimeError("No se puede cargar una imagen sin ventana: crea la ventana (abrir) antes de pedir sprites.")
        imagen = None
        if es_nombre_seguro(nombre):
            ruta = os.path.join(self._ruta, carpeta, f"{nombre}.{extension}")
            self.accesos_disco += 1
            if os.path.isfile(ruta):
                try:
                    cargada = pygame.image.load(ruta)
                    imagen = cargada.convert_alpha() if extension == "png" else cargada.convert()
                except pygame.error:
                    imagen = None           # un archivo dañado cuenta como "no existe"
        return self._recordar(clave, imagen)

    def _conjunto(self, carpeta: str, nombre: str, estado: str) -> list:
        """Los fotogramas originales <nombre>_<estado>_1, _2, ... hasta que falte uno (lista vacía si no hay ninguno)."""
        clave = f"conjunto|{carpeta}|{nombre}|{estado}"
        i = self._buscar(clave)
        if i >= 0:
            return self._valores[i]
        fotogramas = []
        while True:
            imagen = self._imagen(carpeta, f"{nombre}_{estado}_{len(fotogramas) + 1}", "png")
            if imagen is None:
                break
            fotogramas.append(imagen)
        return self._recordar(clave, fotogramas)

    # ================================================================== imagen
    @staticmethod
    def _recortar(imagen: pygame.Surface) -> pygame.Surface:
        contenido = imagen.get_bounding_rect()
        if contenido.width == 0 or contenido.height == 0:
            return imagen                   # imagen totalmente transparente: se deja como está
        return imagen.subsurface(contenido).copy()

    @staticmethod
    def _escalar(imagen: pygame.Surface, factor: float) -> pygame.Surface:
        ancho, alto = imagen.get_size()
        return pygame.transform.scale(imagen, (max(1, round(ancho * factor)), max(1, round(alto * factor))))

    @staticmethod
    def _figura(tamano: tuple[int, int], escala: float, inicial: str) -> pygame.Surface:
        """Respaldo dibujado con código: un rectángulo con la inicial."""
        ancho, alto = max(1, round(tamano[0] * escala)), max(1, round(tamano[1] * escala))
        figura = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(figura, _COLOR_FIGURA if inicial else _COLOR_UI, figura.get_rect(), border_radius=6)
        pygame.draw.rect(figura, (230, 220, 200), figura.get_rect(), width=2, border_radius=6)
        if inicial:
            letra = pygame.font.Font(None, max(12, alto // 2)).render(inicial, True, (240, 235, 225))
            figura.blit(letra, letra.get_rect(center=figura.get_rect().center))
        return figura

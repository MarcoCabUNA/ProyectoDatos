"""
EscenaJuego (Vista): lo que se ve de la sala durante la partida (sin el HUD, que es de la Etapa 7).

Capas: fondo de la sala -> marcos de puerta SIN salida, oscurecidos -> puertas cerradas -> protagonista, enemigos y
objetos del suelo, todos ORDENADOS POR LOS PIES (el de más abajo se dibuja encima) -> nombre de un objeto.
Las zonas de clic se registran en ese mismo orden, así que la prioridad de las zonas coincide con lo que se ve encima.

Qué dibujar y dónde lo deciden funciones puras, que se prueban sin pintar píxeles:
    fondo_para, puertas_a_dibujar, direcciones_sin_salida      qué fondo y qué puertas
    posicion_del_protagonista(salidas, sala anterior)          dónde pisa el protagonista
    colocar(tamaños, ocupadas, ...)                            dónde se reparten enemigos y objetos
    orden_de_dibujo(pies)                                      quién va encima de quién
TODAS las medidas (tamaños, suelo, reparto, aura, marcos de puerta) están en View/Componentes.py; aquí no hay números.

Tamaños (altura del contenido del sprite): el protagonista, fija (ALTURA_JUGADOR); el enemigo con sprites propios,
ALTURA_ENEMIGO; el de respaldo (conjunto genérico, que se reconoce por ConjuntoSprites.origen), FACTOR_RESPALDO de eso.
Si no caben, todos los enemigos se achican con el mismo factor (FACTORES_ENEMIGOS); el protagonista no cambia.

Protagonista: sin sala anterior, en el centro del suelo; al entrar a una sala nueva, delante de la puerta por la que
entró. La escena recuerda la sala anterior comparando el id de sala entre cuadros; VistaPygame le dice cuándo olvidarla.

Los objetos del suelo llevan un aura (los enemigos no) y su nombre solo aparece al pasar el ratón por encima:
PantallaDTO.elemento_bajo_el_raton, que la Vista recibe ya hecho (no lee el ratón).
"""
import math
from dataclasses import dataclass, field

import pygame

from DTO.Direcciones import E, N, S
from DTO.ElementoDTO import ELEMENTO_ENEMIGO, ELEMENTO_OBJETO_SUELO, ELEMENTO_PUERTA, ElementoDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from View import Animaciones as anim
from View import Componentes as c
from View.AlmacenSprites import es_de_respaldo
from View.EfectosEscena import Instantanea, MarcaEnemigo, MarcaObjeto, MarcaPuerta

FONDO_INICIAL, FONDO_REGULAR, FONDO_FINAL = c.FONDO_INICIAL, c.FONDO_REGULAR, c.FONDO_FINAL
PUERTA_CERRADA, PUERTA_FINAL = c.PUERTA_CERRADA, c.PUERTA_FINAL
PANTALLA = pygame.Rect(0, 0, c.ANCHO, c.ALTO)


# ============================================================================ decisiones puras
def fondo_para(estado: EstadoJuegoDTO) -> str:
    """El fondo según el rol de la sala. Si la sala inicial es también la de salida, gana el fondo inicial."""
    if estado.sala.id == estado.sala_inicial:
        return FONDO_INICIAL
    if estado.sala.id == estado.sala_salida:
        return FONDO_FINAL
    return FONDO_REGULAR


def puertas_a_dibujar(estado: EstadoJuegoDTO) -> list[tuple[int, str]]:
    """(dirección, sprite) de cada salida CERRADA: puerta_final si lleva a la sala de salida, puerta_cerrada si no.
    Las salidas abiertas no dibujan nada (el fondo ya trae el marco) y las direcciones sin salida tampoco."""
    puertas = []
    for direccion, salida in enumerate(estado.sala.salidas):
        if salida is not None and salida.cerrada:
            final = salida.sala_destino == estado.sala_salida
            puertas.append((direccion, PUERTA_FINAL if final else PUERTA_CERRADA))
    return puertas


def direcciones_sin_salida(estado: EstadoJuegoDTO) -> list[int]:
    """Las direcciones donde la sala no tiene salida: su marco, si el fondo lo trae, se oscurece."""
    return [d for d, salida in enumerate(estado.sala.salidas) if salida is None]


def marcos_de(fondo: str) -> list[pygame.Rect]:
    """Los cuatro marcos (N, S, E, O) del fondo; los de un fondo desconocido son los del regular."""
    for i in range(len(c.FONDOS_CONOCIDOS)):
        if c.FONDOS_CONOCIDOS[i] == fondo:
            return c.MARCOS[i]
    return c.MARCOS[1]


def tiene_marcos(fondo: str) -> bool:
    """True si el fondo trae pintado el marco de las 4 direcciones (y por tanto se puede oscurecer el que sobre)."""
    for i in range(len(c.FONDOS_CONOCIDOS)):
        if c.FONDOS_CONOCIDOS[i] == fondo:
            return c.MARCOS_OSCURECIBLES[i]
    return False


def escala_de_puerta(nombre: str) -> float:
    for sprite, escala in c.ESCALA_PUERTA:
        if sprite == nombre:
            return escala
    return 1.0


def trapecio(marco: pygame.Rect, direccion: int) -> list[tuple[int, int]]:
    """Los cuatro vértices del hueco de la puerta dentro de su marco: ancho junto a la pared y estrecho hacia la sala."""
    izq, der, arriba, abajo = marco.left, marco.right - 1, marco.top, marco.bottom - 1
    t, u = round(marco.width * c.FRACCION_ESTRECHA), round(marco.height * c.FRACCION_ESTRECHA)
    if direccion == N:
        return [(izq, arriba), (der, arriba), (der - t, abajo), (izq + t, abajo)]
    if direccion == S:
        return [(izq, abajo), (der, abajo), (der - t, arriba), (izq + t, arriba)]
    if direccion == E:
        return [(der, arriba), (der, abajo), (izq, abajo - u), (izq, arriba + u)]
    return [(izq, arriba), (izq, abajo), (der, abajo - u), (der, arriba + u)]


def posicion_del_protagonista(salidas: list, id_sala_anterior: int | None) -> tuple[int, int]:
    """Dónde pisa el protagonista (sus pies). Sin sala anterior, en el centro del suelo. Si no, delante de la puerta por
    la que entró: la salida de esta sala cuya sala_destino es la sala anterior. Si esa puerta no se puede determinar (la
    sala anterior no es contigua, o hay varias salidas hacia ella), en el centro."""
    if id_sala_anterior is None:
        return c.PIES_CENTRO
    hacia_la_anterior = [d for d, salida in enumerate(salidas) if salida is not None
                         and salida.sala_destino == id_sala_anterior]
    return c.PIES_PUERTA[hacia_la_anterior[0]] if len(hacia_la_anterior) == 1 else c.PIES_CENTRO


def colocar(tamanos: list[tuple[int, int]], ocupadas: list[pygame.Rect], suelo: pygame.Rect, pies: tuple[int, int],
            radio: int, paso: int, separacion: int) -> tuple[list[pygame.Rect], bool]:
    """Reparte un rectángulo por cada (ancho, alto) de 'tamanos', en ese orden, dentro de 'suelo', sin solapar entre sí
    ni con 'ocupadas' (dejando 'separacion' píxeles de hueco). Cada uno toma la posición libre cuyo pie (centro de su
    borde de abajo) está más cerca de estar a 'radio' píxeles de 'pies': así se reparten alrededor del protagonista.
    Es determinista: mismos datos, mismo reparto. Devuelve (rectángulos, True si todos cupieron); el que no cabe se pone
    en su mejor posición aunque solape."""
    bloqueos = list(ocupadas)
    resultado = []
    todos = True
    for ancho, alto in tamanos:
        elegido, clave_elegido = None, None              # la mejor posición libre (la clave menor)
        mejor_aunque_solape, clave_mejor = None, None    # y la mejor sin mirar si está libre (por si no hay ninguna)
        for y in range(suelo.top, suelo.bottom - alto + 1, paso):
            for x in range(suelo.left, suelo.right - ancho + 1, paso):
                clave = (abs(math.hypot(x + ancho / 2 - pies[0], y + alto - pies[1]) - radio), y, x)
                if clave_mejor is None or clave < clave_mejor:
                    mejor_aunque_solape, clave_mejor = (x, y), clave
                if clave_elegido is not None and clave >= clave_elegido:
                    continue
                rectangulo = pygame.Rect(x, y, ancho, alto)
                if rectangulo.inflate(2 * separacion, 2 * separacion).collidelist(bloqueos) == -1:
                    elegido, clave_elegido = rectangulo, clave
        if elegido is None:
            todos = False
            elegido = (pygame.Rect(*mejor_aunque_solape, ancho, alto) if mejor_aunque_solape is not None
                       else pygame.Rect(suelo.left, suelo.top, ancho, alto).clamp(suelo))
        bloqueos.append(elegido)
        resultado.append(elegido)
    return resultado, todos


def orden_de_dibujo(pies_y: list[int]) -> list[int]:
    """Los índices de 'pies_y' en el orden en que se dibujan: el de los pies más abajo, el último (encima)."""
    pendientes = list(range(len(pies_y)))
    orden = []
    while pendientes:                                # selección del menor: los empates, por índice (el primero que sale)
        menor = pendientes[0]
        for i in pendientes[1:]:
            if pies_y[i] < pies_y[menor]:
                menor = i
        orden.append(menor)
        pendientes.remove(menor)
    return orden


# ============================================================================ dibujo
@dataclass(frozen=True)
class Reparto:
    """Lo que decide colocar para una escena: se recalcula solo si cambia algo de lo que depende."""
    enemigos: list                   # rectángulos (zona de clic) de cada enemigo, en el orden de estado.enemigos
    sprites: list                    # el sprite de cada enemigo, a su tamaño
    fuente_chica: bool               # nombres con la fuente chica (muchos enemigos)
    objetos: list                    # zona de clic de cada objeto del suelo
    conjuntos: list = field(default_factory=list)    # el ConjuntoSprites (todos los fotogramas) de cada enemigo


def repartir_escena(almacen, fuentes: c.Fuentes, enemigos: list, objetos: list, salidas: list,
                    pies: tuple[int, int]) -> "Reparto":
    """Dónde va cada enemigo y cada objeto del suelo, alrededor del protagonista (que pisa en 'pies'), sin tapar al
    protagonista ni las puertas con salida. Los enemigos primero y luego los objetos, probando factores de tamaño cada
    vez menores para los enemigos (los mismos para todos, para conservar sus proporciones) hasta que caben todos. Solo usa 'almacen' y
    'fuentes' para medir lo que se dibujará: no dibuja nada."""
    jugador = pygame.Rect((0, 0), c.JUGADOR_OCUPA)
    jugador.midbottom = pies
    ocupadas = ([jugador] + [c.PASILLOS[d] for d, salida in enumerate(salidas) if salida is not None]
                + list(c.HUD_PANELES))                # el HUD tampoco se puede tapar con un enemigo o un objeto
    respaldo = [es_de_respaldo(almacen.actor(a.tipo, "idle", 1.0, a.nombre)) for a in enemigos]
    margen = c.AURA_MARGEN
    sprites_objetos = [almacen.objeto(o.id, o.clase, c.LADO_OBJETO).fotogramas[0] for o in objetos]
    tamanos_objetos = [(s.get_width() + 2 * margen, s.get_height() + 2 * margen) for s in sprites_objetos]
    rectangulos, sprites, conjuntos, chica, huellas = [], [], [], False, []
    for factor in c.FACTORES_ENEMIGOS:
        chica = factor < c.FACTOR_NOMBRE_CHICO
        fuente = fuentes.chico if chica else fuentes.pie
        sprites, conjuntos, tamanos = [], [], []
        for a, es_respaldo_ in zip(enemigos, respaldo):
            alto = round(c.ALTURA_ENEMIGO * (c.FACTOR_RESPALDO if es_respaldo_ else 1.0) * factor)
            conjunto = almacen.actor_a_altura(a.tipo, max(c.ALTURA_MINIMA, alto), nombre=a.nombre)
            sprite = conjunto.fotogramas[0]
            ancho_ficha = max(c.BARRA_VIDA[0], min(fuente.size(a.nombre)[0], c.NOMBRE_ANCHO_MAX))
            if factor < c.FACTOR_FICHA_ESTRECHA:                # _ficha_de_actor ya ajusta barra y nombre al ancho
                ancho_ficha = min(ancho_ficha, c.FICHA_ANCHO_MIN)
            conjuntos.append(conjunto)
            sprites.append(sprite)
            tamanos.append((max(sprite.get_width(), ancho_ficha), sprite.get_height() + c.FICHA))
        rectangulos, caben = colocar(tamanos, ocupadas, c.SUELO, pies, c.REPARTO_RADIO_ENEMIGOS, c.REPARTO_PASO,
                                     c.REPARTO_SEPARACION)
        huellas, caben_objetos = colocar(tamanos_objetos, ocupadas + rectangulos, c.SUELO, pies,
                                         c.REPARTO_RADIO_OBJETOS, c.REPARTO_PASO, c.REPARTO_SEPARACION)
        if caben and caben_objetos:                  # si los objetos no caben, los enemigos se achican un poco más
            break
    return Reparto(rectangulos, sprites, chica, [huella.inflate(-2 * margen, -2 * margen) for huella in huellas], conjuntos)


class EscenaJuego:

    def __init__(self, almacen, fuentes: c.Fuentes, zonas, efectos=None):
        """'efectos' (View/EfectosEscena.py) solo se da con animaciones; sin él todo se dibuja como siempre."""
        self._almacen = almacen
        self._fuentes = fuentes
        self._zonas = zonas
        self._efectos = efectos
        self._ahora = 0                              # el instante del cuadro (solo con animaciones)
        self._objeto_resaltado = -1                  # qué objeto del suelo tiene el ratón encima (solo con animaciones)
        self._con_zonas = True
        self._id_visto: int | None = None            # la sala del cuadro anterior (None: no hay, o se olvidó)
        self._pies = c.PIES_CENTRO                   # dónde pisa el protagonista en la sala actual
        self._clave_reparto = None
        self._reparto: Reparto | None = None

    def olvidar_la_sala(self) -> None:
        """Se llama al mostrar menu, criptas, nombre, victoria, derrota o puntajes: la próxima partida empieza de cero."""
        self._id_visto = None
        if self._efectos is not None:
            self._efectos.olvidar()                  # y tampoco recuerda lo que pasó en el cuadro anterior

    def dibujar(self, superficie: pygame.Surface, estado: EstadoJuegoDTO, objetivo: str | None,
                con_zonas: bool = True, elemento_bajo_el_raton: ElementoDTO | None = None,
                con_nombre: bool = True, ahora: int | None = None) -> None:
        """Dibuja la sala. Con 'con_zonas' False (la pausa) no registra nada clicable. Con 'con_nombre' False no dibuja el
        nombre del objeto bajo el ratón: la Vista lo pide después con dibujar_nombre, por encima del HUD.
        'ahora' (ms) solo lo usan las animaciones; sin él (la pausa) la escena se dibuja congelada en el último instante."""
        self._con_zonas = con_zonas
        if self._efectos is not None:
            self._ahora = self._efectos.ahora_de_la_escena(ahora)
            self._objeto_resaltado = elemento_bajo_el_raton.indice if (
                elemento_bajo_el_raton is not None and elemento_bajo_el_raton.tipo == ELEMENTO_OBJETO_SUELO) else -1
        if estado.sala.id != self._id_visto:
            self._pies = posicion_del_protagonista(estado.sala.salidas, self._id_visto)
            self._id_visto = estado.sala.id
            if self._efectos is not None and ahora is not None:
                self._efectos.sala_nueva(ahora)               # empieza el fundido de entrada
        fondo = fondo_para(estado)
        ambiente = self._almacen.fondo_ambientado(fondo, (c.ANCHO, c.ALTO), c.AMBIENTE_INTENSIDAD)
        superficie.blit(ambiente.fotogramas[0], (0, 0))
        if self._efectos is not None:
            self._efectos.parpadeo(superficie, self._ahora)    # la luz vacila: una capa oscura sobre el fondo
        self._marcos_sin_salida(superficie, estado, fondo)
        puertas = self._puertas(superficie, estado, fondo)
        reparto = self._repartir(estado)
        if self._efectos is not None:
            if ahora is not None:                                  # en la pausa la escena está congelada: no se observa nada
                self._efectos.observar(self._instantanea(estado, reparto, puertas), ahora, self._cuadros_de_muerte)
            self._efectos.dibujar_puertas(superficie, self._ahora)
        entradas = [("jugador", 0, self._pies[1])]
        entradas += [("enemigo", i, r.bottom) for i, r in enumerate(reparto.enemigos)]
        entradas += [("objeto", i, r.bottom) for i, r in enumerate(reparto.objetos)]
        for k in orden_de_dibujo([pies for _, _, pies in entradas]):
            tipo, i, _ = entradas[k]
            if tipo == "jugador":
                self._jugador(superficie, estado)
            elif tipo == "enemigo":
                self._enemigo(superficie, estado.enemigos[i], i, reparto, objetivo)
            else:
                self._objeto(superficie, estado.objetos_suelo[i], i, reparto)
        if self._efectos is not None:
            self._efectos.dibujar_fantasmas(superficie, self._ahora)
            self._efectos.dibujar_numeros(superficie, self._ahora)
        if con_nombre:
            self._nombre_del_objeto(superficie, estado, reparto, elemento_bajo_el_raton)

    def dibujar_nombre(self, superficie: pygame.Surface, estado: EstadoJuegoDTO,
                       elemento_bajo_el_raton: ElementoDTO | None) -> None:
        """Lo último que se dibuja del cuadro: el nombre del objeto del suelo bajo el ratón, encima de todo (HUD incluido)."""
        self._nombre_del_objeto(superficie, estado, self._repartir(estado), elemento_bajo_el_raton)

    def _registrar(self, rectangulo: pygame.Rect, elemento: ElementoDTO) -> None:
        if self._con_zonas:
            self._zonas.agregar(rectangulo, elemento)

    # ------------------------------------------------------------------ puertas
    def _marcos_sin_salida(self, superficie, estado, fondo) -> None:
        if not tiene_marcos(fondo):
            return
        marcos = marcos_de(fondo)
        for direccion in direcciones_sin_salida(estado):
            marco = marcos[direccion]
            capa = pygame.Surface(marco.size, pygame.SRCALPHA)
            pygame.draw.polygon(capa, c.COLOR_OSCURO, [(x - marco.x, y - marco.y) for x, y in trapecio(marco, direccion)])
            superficie.blit(capa, marco)

    def _puertas(self, superficie, estado, fondo) -> list:
        """Dibuja las puertas cerradas y devuelve dónde quedó cada una (las animaciones recuerdan cuáles se abren)."""
        marcos = marcos_de(fondo)
        marcas = []
        for direccion, nombre in puertas_a_dibujar(estado):
            sprite = self._almacen.puerta(nombre, direccion, escala_de_puerta(nombre)).fotogramas[0]
            rectangulo = sprite.get_rect(center=marcos[direccion].center).clamp(PANTALLA)
            superficie.blit(sprite, rectangulo)
            self._registrar(rectangulo, ElementoDTO(ELEMENTO_PUERTA, direccion))
            marcas.append(MarcaPuerta(direccion, rectangulo, sprite, nombre == PUERTA_FINAL))
        return marcas

    # ------------------------------------------------------------------ lo que las animaciones de combate recuerdan
    def _rect_del_jugador(self, estado) -> pygame.Rect:
        jugador = estado.jugador
        reposo = self._almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas[0]
        return reposo.get_rect(midbottom=self._pies)

    def _instantanea(self, estado, reparto, puertas) -> Instantanea:
        """Lo que se acaba de decidir dibujar, para que la Vista lo compare con el cuadro anterior."""
        destinos = [salida.sala_destino for salida in estado.sala.salidas if salida is not None]
        marca = Instantanea(estado.sala.id, estado.reloj, destinos, estado.jugador.vida, self._rect_del_jugador(estado),
                            puertas=puertas)
        for i, enemigo in enumerate(estado.enemigos):
            sprite = reparto.sprites[i]
            rect = sprite.get_rect(midbottom=reparto.enemigos[i].midbottom)
            marca.enemigos.append(MarcaEnemigo(enemigo.id, enemigo.vida, rect, sprite, enemigo.tipo, enemigo.nombre))
        for i, objeto in enumerate(estado.objetos_suelo):
            sprite = self._almacen.objeto(objeto.id, objeto.clase, c.LADO_OBJETO).fotogramas[0]
            marca.objetos.append(MarcaObjeto(objeto.id, reparto.objetos[i].copy(), sprite))
        return marca

    def _cuadros_de_muerte(self, tipo: str, alto: int, nombre: str) -> list:
        """Los fotogramas 'muerte' de un enemigo a la altura 'alto', o una lista vacía si ese enemigo no los tiene (entonces
        el almacén devolvió su reposo o la figura de respaldo, y la muerte se dibuja encogiéndolo)."""
        conjunto = self._almacen.actor_a_altura(tipo, alto, "muerte", nombre)
        return list(conjunto.fotogramas) if conjunto.origen.endswith("_muerte") else []

    def _destello(self, superficie, sprite, destino, del_jugador: bool, id_enemigo: str) -> None:
        """El golpeado se aclara un instante: su silueta blanca, translúcida, sobre su sprite."""
        alfa = self._efectos.alfa_de_destello(del_jugador, id_enemigo, self._ahora)
        if alfa > 0:
            silueta = self._almacen.silueta_blanca(sprite)
            silueta.set_alpha(alfa)
            superficie.blit(silueta, destino)

    # ------------------------------------------------------------------ reparto
    def _repartir(self, estado) -> Reparto:
        """El reparto de la escena (repartir_escena). Se guarda el último: solo se recalcula si cambian los pies del
        protagonista, los enemigos (tipo y nombre), los objetos o qué direcciones tienen salida."""
        clave = (self._pies, tuple((a.tipo, a.nombre) for a in estado.enemigos),
                 tuple((o.id, o.clase) for o in estado.objetos_suelo), tuple(s is not None for s in estado.sala.salidas))
        if clave != self._clave_reparto:
            self._reparto = repartir_escena(self._almacen, self._fuentes, estado.enemigos, estado.objetos_suelo,
                                            estado.sala.salidas, self._pies)
            self._clave_reparto = clave
        return self._reparto

    # ------------------------------------------------------------------ actores y objetos
    def _ficha_de_actor(self, superficie, actor, sprite_rect, ancho: int, fuente) -> None:
        """Barra de vida y nombre sobre el sprite."""
        barra = pygame.Rect((0, 0), (min(c.BARRA_VIDA[0], ancho), c.BARRA_VIDA[1]))
        barra.midbottom = (sprite_rect.centerx, sprite_rect.top - c.FICHA_SEPARACION[0])
        c.barra_de_vida(superficie, self._fuentes, barra, actor.vida, actor.vida_max)
        c.texto_sombreado(superficie, fuente, c.recortar_a_ancho(fuente, actor.nombre, ancho), c.TEXTO,
                          (sprite_rect.centerx, barra.top - c.FICHA_SEPARACION[1]), "midbottom")

    def _jugador(self, superficie, estado) -> None:
        jugador = estado.jugador
        fotogramas = self._almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, nombre=jugador.nombre).fotogramas
        sprite_rect = fotogramas[0].get_rect(midbottom=self._pies)       # la ficha va sobre el reposo, no salta con el cuadro
        sprite = fotogramas[0]
        if self._efectos is not None:                                    # reposo en bucle
            sprite = fotogramas[anim.fotograma(len(fotogramas), self._ahora, c.ANIM_IDLE_JUGADOR_FPS)]
            muerte = self._efectos.ms_de_muerte(self._ahora, estado.terminado and estado.resultado == "derrota")
            if muerte is not None:                                       # la derrota: cae y se queda en el último fotograma
                caida = self._almacen.actor_a_altura(jugador.tipo, c.ALTURA_JUGADOR, "muerte", jugador.nombre).fotogramas
                sprite = caida[anim.fotograma_unico(len(caida), muerte, c.MUERTE_JUGADOR_MS)]
        superficie.blit(sprite, sprite.get_rect(midbottom=self._pies))
        if self._efectos is not None:
            self._destello(superficie, sprite, sprite.get_rect(midbottom=self._pies), True, "")
        self._ficha_de_actor(superficie, jugador, sprite_rect, c.JUGADOR_OCUPA[0], self._fuentes.pie)

    def _enemigo(self, superficie, enemigo, i, reparto, objetivo) -> None:
        zona, sprite = reparto.enemigos[i], reparto.sprites[i]
        sprite_rect = sprite.get_rect(midbottom=zona.midbottom)
        if enemigo.id == objetivo:
            halo = sprite_rect.inflate(*c.HALO_MARGEN)       # el que atacaría Espacio: un marco dorado translúcido
            c.panel(superficie, halo, c.HALO_COLOR, c.ORO, 2)
        if self._efectos is None:
            superficie.blit(sprite, sprite_rect)
        else:
            fotogramas = reparto.conjuntos[i].fotogramas
            if len(fotogramas) > 1:                                      # varios fotogramas: reposo en bucle
                sprite = fotogramas[anim.fotograma(len(fotogramas), self._ahora, c.ANIM_IDLE_FPS)]
                destino = sprite.get_rect(midbottom=zona.midbottom)
            else:                                                        # uno solo: vaivén vertical, con fase según su posición
                destino = sprite_rect.move(0, -anim.bamboleo(self._ahora, i))
            superficie.blit(sprite, destino)
            self._destello(superficie, sprite, destino, False, enemigo.id)
        self._ficha_de_actor(superficie, enemigo, sprite_rect, zona.width,
                             self._fuentes.chico if reparto.fuente_chica else self._fuentes.pie)
        self._registrar(zona, ElementoDTO(ELEMENTO_ENEMIGO, i))

    def _objeto(self, superficie, objeto, i, reparto) -> None:
        zona = reparto.objetos[i]
        intensidad = c.AURA_INTENSIDAD if self._efectos is None else c.AURA_INTENSIDAD_ANIMADA
        aura = self._almacen.aura_de_objeto(objeto.id, objeto.clase, c.LADO_OBJETO, c.AURA_MARGEN, c.AURA_COLOR, intensidad)
        if self._efectos is not None:                                    # el aura respira y brilla más con el ratón encima
            aura.set_alpha(anim.alfa_aura(self._ahora, i, i == self._objeto_resaltado))
        superficie.blit(aura, zona.inflate(2 * c.AURA_MARGEN, 2 * c.AURA_MARGEN).topleft)
        superficie.blit(self._almacen.objeto(objeto.id, objeto.clase, c.LADO_OBJETO).fotogramas[0], zona)
        self._registrar(zona, ElementoDTO(ELEMENTO_OBJETO_SUELO, i))

    def _nombre_del_objeto(self, superficie, estado, reparto, elemento) -> None:
        """El nombre del objeto del suelo bajo el ratón, junto a él. No registra zonas. Con cualquier otro elemento, o un
        índice que no existe, no dibuja nada."""
        if elemento is None or elemento.tipo != ELEMENTO_OBJETO_SUELO or not 0 <= elemento.indice < len(reparto.objetos):
            return
        zona = reparto.objetos[elemento.indice]
        imagen = self._fuentes.texto.render(estado.objetos_suelo[elemento.indice].nombre, True, c.TEXTO)
        etiqueta = imagen.get_rect().inflate(*c.ETIQUETA_RELLENO)
        etiqueta.midbottom = (zona.centerx, zona.top - c.AURA_MARGEN - c.ETIQUETA_SEPARACION)
        if etiqueta.top < 0:
            etiqueta.midtop = (zona.centerx, zona.bottom + c.AURA_MARGEN + c.ETIQUETA_SEPARACION)
        etiqueta.clamp_ip(PANTALLA)
        c.panel(superficie, etiqueta, c.PANEL, c.ORO, 2)
        superficie.blit(imagen, imagen.get_rect(center=etiqueta.center))

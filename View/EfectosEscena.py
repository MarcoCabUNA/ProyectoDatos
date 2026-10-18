"""
EfectosEscena (Vista): lo que la Vista recuerda de un cuadro al siguiente para animar, y el dibujo de esas animaciones. Solo
existe con VistaPygame(animaciones=True); sin él, la Vista no crea este objeto y dibuja exactamente como siempre.

Fase 1 (ambiente): el instante de la escena (también congelado en la pausa), el fundido de entrada a una sala o a una pantalla de
menú y la capa oscura que hace vacilar la luz del fondo. Ninguna capa registra zonas de clic: las animaciones no se pueden pulsar.
Las superficies se preparan una sola vez y se reutilizan; cada cuadro solo cambia su alfa.

Fase 2 (feedback de combate): la Vista recuerda una Instantanea del cuadro anterior (vida del protagonista y de cada enemigo, objetos
del suelo, puertas cerradas, y dónde se dibujaron) y, al ver la siguiente, deduce de las DIFERENCIAS qué pasó: números flotantes
(-N rojo, +N verde), destello del golpeado, borde rojo si es el protagonista, muerte de un enemigo, objeto recogido, puerta que se
abre. Nunca lee los mensajes. La memoria se reinicia SIN animar en el primer cuadro, si el reloj de la Vista o el del estado
retroceden, si la sala cambia de forma no contigua y al mostrar una pantalla que no es la partida; es de a lo sumo MAX_ANIMACIONES.
Las animaciones siguen dibujándose con la partida terminada (la demora del fin): solo las reglas de arriba las reinician.
"""
from dataclasses import dataclass, field

import pygame

from View import Animaciones as anim
from View import Componentes as c


@dataclass
class MarcaEnemigo:
    id: str
    vida: int
    rect: pygame.Rect            # donde se dibujó su sprite (midbottom en su zona)
    sprite: pygame.Surface
    tipo: str
    nombre: str


@dataclass
class MarcaObjeto:
    id: str
    rect: pygame.Rect
    sprite: pygame.Surface


@dataclass
class MarcaPuerta:
    direccion: int
    rect: pygame.Rect
    sprite: pygame.Surface
    final: bool                  # la puerta cerrada cuyo destino es la sala de salida


@dataclass
class Instantanea:
    """Lo que se dibujó en un cuadro de la partida y sirve para compararlo con el siguiente."""
    sala: int
    reloj: int                   # el reloj virtual del estado
    destinos: list               # las salas a las que llevan las salidas (para saber si dos salas son contiguas)
    vida_jugador: int
    rect_jugador: pygame.Rect
    enemigos: list = field(default_factory=list)
    objetos: list = field(default_factory=list)
    puertas: list = field(default_factory=list)


@dataclass
class Animacion:
    tipo: str                    # numero, destello, borde, muerte, recogido, puerta o calido
    inicio: int
    duracion: int
    clave: str = ""              # destello: el id del enemigo golpeado
    del_jugador: bool = False
    rect: pygame.Rect | None = None
    imagen: pygame.Surface | None = None
    cuadros: list = field(default_factory=list)


class EfectosEscena:

    def __init__(self):
        self._ahora = 0                              # el último instante dibujado (la pausa congela la escena en él)
        self._inicio_sala: int | None = None         # cuándo empezó el fundido de la sala actual
        self._inicio_pantalla: int | None = None     # cuándo empezó el fundido de la pantalla de menú actual
        self._pantalla_vista: str | None = None
        self._inicio_muerte: int | None = None       # el primer cuadro con la partida perdida
        self._fundido = self._capa(c.FUNDIDO_COLOR)
        self._parpadeo = self._capa(c.PARPADEO_COLOR)
        self._previa: Instantanea | None = None      # el cuadro anterior de la partida (None: no hay, o se olvidó)
        self._ultimo: int | None = None              # el instante en que se observó
        self._anims: list = []                       # las animaciones de combate en curso (a lo sumo MAX_ANIMACIONES)
        self._fuente = pygame.font.Font(None, c.NUMERO_TAMANO)
        self._borde = self._marco_rojo()
        self._velo_golpe = self._capa(c.BORDE_COLOR)
        self._vineta = self._marco_vineta()

    @staticmethod
    def _capa(color) -> pygame.Surface:
        capa = pygame.Surface((c.ANCHO, c.ALTO))
        capa.fill(color)
        return capa

    @staticmethod
    def _marco_rojo() -> pygame.Surface:
        """El borde de la pantalla: rojo en el filo y cada vez más transparente hacia adentro. Se prepara una sola vez."""
        marco = pygame.Surface((c.ANCHO, c.ALTO), pygame.SRCALPHA)
        for i in range(c.BORDE_GROSOR):
            alfa = round(255 * (1.0 - i / c.BORDE_GROSOR) ** 2)
            pygame.draw.rect(marco, (*c.BORDE_COLOR, alfa), (i, i, c.ANCHO - 2 * i, c.ALTO - 2 * i), 1)
        return marco

    @staticmethod
    def _marco_vineta() -> pygame.Surface:
        """La viñeta: negra en el filo, rojo oscuro hacia adentro y transparente al llegar al centro. Se prepara una sola vez."""
        marco = pygame.Surface((c.ANCHO, c.ALTO), pygame.SRCALPHA)
        for i in range(c.VINETA_GROSOR):
            t = i / c.VINETA_GROSOR
            color = tuple(round(canal * t) for canal in c.VINETA_ROJO)
            pygame.draw.rect(marco, (*color, round(255 * (1.0 - t) ** 2)), (i, i, c.ANCHO - 2 * i, c.ALTO - 2 * i), 1)
        return marco

    # ------------------------------------------------------------------ el instante
    def ahora_de_la_escena(self, ahora: int | None) -> int:
        """'ahora' si hay; si no (la escena detrás de la pausa), el último instante: la escena queda congelada."""
        if ahora is None:
            return self._ahora
        self._ahora = ahora
        return ahora

    def ms_de_muerte(self, ahora: int, muerto: bool) -> int | None:
        """Cuánto lleva el protagonista muriendo (None si no está muerto). Cuenta desde el primer cuadro con 'muerto'."""
        if not muerto:
            self._inicio_muerte = None
            return None
        if self._inicio_muerte is None or ahora < self._inicio_muerte:
            self._inicio_muerte = ahora
        return ahora - self._inicio_muerte

    # ------------------------------------------------------------------ fundidos
    def sala_nueva(self, ahora: int) -> None:
        self._inicio_sala = ahora

    def pantalla_vista(self, nombre: str, ahora: int) -> None:
        """Se llama en cada cuadro: al CAMBIAR a una pantalla de menú empieza su fundido."""
        if nombre != self._pantalla_vista and nombre in c.PANTALLAS_CON_FUNDIDO:
            self._inicio_pantalla = ahora
        self._pantalla_vista = nombre

    def fundido_de_la_sala(self, superficie: pygame.Surface, ahora: int) -> None:
        self._velar(superficie, self._inicio_sala, ahora, c.FUNDIDO_SALA_MS)

    def fundido_de_la_pantalla(self, superficie: pygame.Surface, ahora: int) -> None:
        self._velar(superficie, self._inicio_pantalla, ahora, c.FUNDIDO_PANTALLA_MS)

    def _velar(self, superficie, inicio, ahora, duracion) -> None:
        if inicio is None:
            return
        p = anim.progreso(inicio, ahora, duracion)
        if p >= 1.0:
            return
        self._fundido.set_alpha(anim.alfa_de_fundido(p))
        superficie.blit(self._fundido, (0, 0))

    # ------------------------------------------------------------------ luz que vacila
    def parpadeo(self, superficie: pygame.Surface, ahora: int) -> None:
        alfa = anim.alfa_parpadeo(ahora)
        if alfa > 0:
            self._parpadeo.set_alpha(alfa)
            superficie.blit(self._parpadeo, (0, 0))

    # ------------------------------------------------------------------ feedback de combate: la memoria
    def olvidar(self) -> None:
        """Al mostrar menú, criptas, nombre, victoria, derrota o puntajes: nada de lo recordado vale para la próxima partida."""
        self._previa = None
        self._ultimo = None
        self._anims = []

    def observar(self, nueva: Instantanea, ahora: int, cuadros_de_muerte) -> None:
        """Compara el cuadro 'nueva' con el anterior y crea las animaciones de lo que cambió. 'cuadros_de_muerte(tipo, alto,
        nombre)' da los fotogramas 'muerte' de un enemigo (lista vacía si no tiene). Solo se llama en un cuadro de la partida
        en marcha (en la pausa la escena queda congelada y no se observa nada)."""
        previa, self._previa = self._previa, nueva
        ultimo, self._ultimo = self._ultimo, ahora
        if previa is None or ultimo is None or ahora < ultimo or nueva.reloj < previa.reloj:
            self._anims = []                                   # el primer cuadro, o el tiempo retrocedió: sin animar
            return
        self._anims = [a for a in self._anims if ahora - a.inicio < a.duracion]
        if nueva.sala != previa.sala:
            if not self._contiguas(previa, nueva):
                self._anims = []                               # otra sala sin pasar por una puerta: se empieza de cero
                return
            self._anims = [a for a in self._anims if a.del_jugador]    # lo del protagonista lo acompaña de sala en sala
            self._la_vida_del_protagonista(previa, nueva, ahora)
            return
        self._la_vida_del_protagonista(previa, nueva, ahora)
        self._los_enemigos(previa, nueva, ahora, cuadros_de_muerte)
        self._los_objetos(previa, nueva, ahora)
        self._las_puertas(previa, nueva, ahora)
        while len(self._anims) > c.MAX_ANIMACIONES:
            self._anims.pop(0)                                 # las más viejas se olvidan

    @staticmethod
    def _contiguas(previa: Instantanea, nueva: Instantanea) -> bool:
        for destino in nueva.destinos:
            if destino == previa.sala:
                return True
        return False

    def _la_vida_del_protagonista(self, previa, nueva, ahora) -> None:
        cambio = nueva.vida_jugador - previa.vida_jugador
        if cambio == 0:
            return
        self._numero(cambio, nueva.rect_jugador, ahora, True)
        if cambio < 0:
            self._anims.append(Animacion("destello", ahora, c.DESTELLO_MS, "", True))
            self._anims.append(Animacion("borde", ahora, c.BORDE_MS, "", True))
            self._anims.append(Animacion("velo_golpe", ahora, c.VELO_GOLPE_MS, "", True))

    def _los_enemigos(self, previa, nueva, ahora, cuadros_de_muerte) -> None:
        for e in nueva.enemigos:
            antes = self._buscar_enemigo(previa.enemigos, e.id)
            if antes is None:
                continue
            cambio = e.vida - antes.vida
            if cambio != 0:
                self._numero(cambio, e.rect, ahora, False)
            if cambio < 0:
                self._anims.append(Animacion("destello", ahora, c.DESTELLO_MS, e.id))
        for m in previa.enemigos:
            if self._buscar_enemigo(nueva.enemigos, m.id) is not None:
                continue
            if m.vida > 0:
                self._numero(-m.vida, m.rect, ahora, False)    # lo que le quedaba: el golpe que lo mató
            cuadros = cuadros_de_muerte(m.tipo, m.rect.height, m.nombre)
            if cuadros:
                self._anims.append(Animacion("muerte", ahora, c.MUERTE_ENEMIGO_MS, rect=m.rect.copy(),
                                             cuadros=[cuadro.copy() for cuadro in cuadros]))
            else:
                self._anims.append(Animacion("muerte", ahora, c.MUERTE_ENEMIGO_MS, rect=m.rect.copy(),
                                             imagen=m.sprite.copy()))

    @staticmethod
    def _buscar_enemigo(lista: list, id_enemigo: str):
        for m in lista:
            if m.id == id_enemigo:
                return m
        return None

    def _los_objetos(self, previa, nueva, ahora) -> None:
        usados = [False] * len(nueva.objetos)
        for antes in previa.objetos:
            sigue = False
            for j in range(len(nueva.objetos)):
                if not usados[j] and nueva.objetos[j].id == antes.id:
                    usados[j] = sigue = True
                    break
            if not sigue:
                self._anims.append(Animacion("recogido", ahora, c.RECOGIDO_MS, rect=antes.rect.copy(),
                                             imagen=antes.sprite.copy()))

    def _las_puertas(self, previa, nueva, ahora) -> None:
        for antes in previa.puertas:
            sigue = False
            for despues in nueva.puertas:
                if despues.direccion == antes.direccion:
                    sigue = True
            if sigue:
                continue
            self._anims.append(Animacion("puerta", ahora, c.PUERTA_DESVANECE_MS, rect=antes.rect.copy(),
                                         imagen=antes.sprite.copy()))
            if antes.final:
                self._anims.append(Animacion("calido", ahora, c.PUERTA_CALIDO_MS, rect=antes.rect.copy(),
                                             imagen=self._resplandor(antes.rect.inflate(2 * c.PUERTA_CALIDO_MARGEN,
                                                                                         2 * c.PUERTA_CALIDO_MARGEN).size)))

    @staticmethod
    def _resplandor(tamano: tuple[int, int]) -> pygame.Surface:
        """Un destello cálido de bordes suaves: un rectángulo pequeño ampliado con suavizado."""
        chico = pygame.Surface((max(3, tamano[0] // 8), max(3, tamano[1] // 8)), pygame.SRCALPHA)
        pygame.draw.rect(chico, (*c.PUERTA_CALIDO_COLOR, 255), chico.get_rect().inflate(-2, -2))
        return pygame.transform.smoothscale(chico, tamano)

    def _numero(self, cambio: int, rect: pygame.Rect, ahora: int, del_jugador: bool) -> None:
        texto = f"+{cambio}" if cambio > 0 else str(cambio)
        color = c.NUMERO_VERDE if cambio > 0 else c.NUMERO_ROJO
        base = self._fuente.render(texto, True, color)
        contorno = self._fuente.render(texto, True, c.NUMERO_CONTORNO)
        imagen = pygame.Surface((base.get_width() + 4, base.get_height() + 4), pygame.SRCALPHA)
        for dx in (0, 2, 4):
            for dy in (0, 2, 4):
                if (dx, dy) != (2, 2):
                    imagen.blit(contorno, (dx, dy))
        imagen.blit(base, (2, 2))
        self._anims.append(Animacion("numero", ahora, c.NUMERO_MS, "", del_jugador, rect.copy(), imagen))

    # ------------------------------------------------------------------ feedback de combate: el dibujo
    @staticmethod
    def _p(a: Animacion, ahora: int) -> float:
        return anim.progreso(a.inicio, ahora, a.duracion)

    def alfa_de_destello(self, del_jugador: bool, id_enemigo: str, ahora: int) -> int:
        """El alfa del destello del actor (0 si no hay): el más intenso de los que tenga en curso."""
        mejor = 0
        for a in self._anims:
            if a.tipo == "destello" and a.del_jugador == del_jugador and (del_jugador or a.clave == id_enemigo):
                if self._p(a, ahora) < 1.0:
                    mejor = max(mejor, anim.alfa_destello(self._p(a, ahora)))
        return mejor

    def dibujar_puertas(self, superficie: pygame.Surface, ahora: int) -> None:
        """Las puertas que se acaban de abrir: se desvanecen donde estaban; la final, además, brilla."""
        for a in self._anims:
            p = self._p(a, ahora)
            if p >= 1.0:
                continue
            if a.tipo == "puerta":
                a.imagen.set_alpha(anim.alfa_desvanece(p))
                superficie.blit(a.imagen, a.rect)
            elif a.tipo == "calido":
                a.imagen.set_alpha(anim.alfa_calido(p))
                superficie.blit(a.imagen, a.imagen.get_rect(center=a.rect.center))

    def dibujar_fantasmas(self, superficie: pygame.Surface, ahora: int) -> None:
        """Los enemigos que mueren y los objetos que se recogen, donde estaban."""
        for a in self._anims:
            p = self._p(a, ahora)
            if p >= 1.0:
                continue
            if a.tipo == "recogido":
                a.imagen.set_alpha(anim.alfa_desvanece(p))
                superficie.blit(a.imagen, a.rect.move(0, -anim.sube_recogido(p)))
            elif a.tipo == "muerte" and a.cuadros:
                cuadro = a.cuadros[anim.fotograma_unico(len(a.cuadros), ahora - a.inicio, a.duracion)]
                cuadro.set_alpha(anim.alfa_muerte(p))
                superficie.blit(cuadro, cuadro.get_rect(midbottom=a.rect.midbottom))
            elif a.tipo == "muerte":
                escala = anim.escala_muerte(p)
                tamano = (max(1, round(a.imagen.get_width() * escala)), max(1, round(a.imagen.get_height() * escala)))
                chico = pygame.transform.scale(a.imagen, tamano)
                chico.set_alpha(anim.alfa_muerte(p))
                superficie.blit(chico, chico.get_rect(midbottom=a.rect.midbottom))

    def dibujar_numeros(self, superficie: pygame.Surface, ahora: int) -> None:
        pantalla = pygame.Rect(0, 0, c.ANCHO, c.ALTO)
        for a in self._anims:
            if a.tipo != "numero":
                continue
            p = self._p(a, ahora)
            if p >= 1.0:
                continue
            a.imagen.set_alpha(anim.alfa_numero(p))
            destino = a.imagen.get_rect(midbottom=(a.rect.centerx, a.rect.top - c.FICHA - anim.sube_numero(p)))
            superficie.blit(a.imagen, destino.clamp(pantalla))

    def vineta_de_vida(self, superficie: pygame.Surface, vida: int, vida_max: int, ahora: int) -> None:
        """La viñeta de vida baja (debajo del borde del golpe, encima de todo lo demás, el HUD incluido)."""
        if vida_max <= 0:
            return
        alfa = anim.alfa_vineta(vida / vida_max, ahora)
        if alfa > 0:
            self._vineta.set_alpha(alfa)
            superficie.blit(self._vineta, (0, 0))

    def borde_rojo(self, superficie: pygame.Surface, ahora: int) -> None:
        """El borde de la pantalla, mientras dura la pérdida de vida del protagonista (encima de todo, el HUD incluido)."""
        mejor = 0
        velo = 0
        for a in self._anims:
            if a.tipo == "borde" and self._p(a, ahora) < 1.0:
                mejor = max(mejor, anim.alfa_borde(self._p(a, ahora)))
            elif a.tipo == "velo_golpe" and self._p(a, ahora) < 1.0:
                velo = max(velo, anim.alfa_velo_golpe(self._p(a, ahora)))
        if velo > 0:
            self._velo_golpe.set_alpha(velo)
            superficie.blit(self._velo_golpe, (0, 0))
        if mejor > 0:
            self._borde.set_alpha(mejor)
            superficie.blit(self._borde, (0, 0))

"""
Sonidos (Vista): el MOTOR de sonido. Es lo único de la Vista que toca el mezclador de pygame; QUÉ suena y CUÁNDO lo decide
View/EventosSonoros.py, que solo le pide cosas a este motor:

    abrir()                                       inicia el mezclador y carga los efectos; False si no hay audio
    efecto(nombre)                                toca un sonido corto (los de la tabla SONIDOS_CORTOS)
    latido(encender) / pausar_latido(pausado)     Low_Health en bucle en el canal reservado 0; duracion_latido_ms es lo que dura
    fin(nombre) / parar_fin(fundido_ms)           derrota o victoria en el canal reservado 1; parar_fin los apaga con un fundido
    musica(nombre, volumen, inicio_ms, entrada_ms)   empieza un tema largo (streaming) con fundido de entrada
    volumen_musica(v) / parar_musica()            ajustes del tema en curso
    posicion_musica_ms()                          cuánto lleva sonando el tema (contando el inicio pedido); -1 si no suena
    cerrar()                                      libera el mezclador; es seguro llamarlo dos veces

Sin dispositivo de audio, o con un archivo ausente o dañado, el sonido se apaga (o ese sonido calla) y el juego sigue.

El CARGADOR prepara cada sonido corto una sola vez al abrir: le quita el silencio del inicio, lo limita a su tope, lo
sube de volumen solo si es muy bajo y le pone fundidos de entrada y de salida contra los chasquidos. Solo las muestras
de los extremos (y las de los dos sonidos muy bajos) se tocan una a una; lo demás se recorta como bytes.
"""
from pathlib import Path

import pygame

from View import Componentes as c


# ============================================================================ el cargador (funciones puras sobre bytes)
def primer_indice_sobre(muestras, umbral: int, paso: int = 2048) -> int:
    """El índice de la primera muestra con |amplitud| > umbral, o -1. Revisa por trozos (rápido) y mira una a una solo
    el trozo donde aparece."""
    total = len(muestras)
    inicio = 0
    while inicio < total:
        trozo = muestras[inicio:inicio + paso]
        if max(trozo) > umbral or min(trozo) < -umbral:
            for i in range(len(trozo)):
                if abs(trozo[i]) > umbral:
                    return inicio + i
        inicio += paso
    return -1


def _cuadros(ms: int, frecuencia: int) -> int:
    return ms * frecuencia // 1000


def _fundir(muestras, desde: int, hasta: int, canales: int, entrando: bool) -> None:
    """Fundido lineal de los cuadros [desde, hasta) de 'muestras' (entrando: de 0 a 1; si no, de 1 a 0)."""
    largo = hasta - desde
    for k in range(largo):
        factor = (k + 1) / (largo + 1) if entrando else (largo - k) / (largo + 1)
        base = (desde + k) * canales
        for canal in range(canales):
            muestras[base + canal] = int(muestras[base + canal] * factor)


def _amplificar(muestras, ganancia: float) -> None:
    for i in range(len(muestras)):
        valor = int(muestras[i] * ganancia)
        muestras[i] = 32767 if valor > 32767 else -32768 if valor < -32768 else valor


def preparar(crudo: bytes, canales: int, frecuencia: int, tope_ms: int, fundido_ms: int) -> tuple[bytes, float]:
    """(los bytes ya preparados, el pico del archivo entre 0 y 1). 'crudo' son muestras de 16 bits intercaladas por canal.
    Un sonido que es todo silencio se devuelve igual."""
    muestras = memoryview(crudo).cast("h")
    pico = max(max(muestras), -min(muestras)) / 32768
    if pico == 0:
        return bytes(crudo), 0.0
    primera = primer_indice_sobre(muestras, int(pico * 32768 * c.SONIDO_UMBRAL_INICIO))
    cuadros_total = len(muestras) // canales
    desde = max(0, primera // canales - _cuadros(c.SONIDO_MARGEN_MS, frecuencia))
    hasta = cuadros_total
    if tope_ms > 0:
        hasta = min(cuadros_total, desde + _cuadros(tope_ms, frecuencia))
    salida = bytearray(crudo[desde * canales * 2:hasta * canales * 2])
    editable = memoryview(salida).cast("h")
    largo = hasta - desde
    ganancia = min(c.SONIDO_GANANCIA_MAX, c.SONIDO_PICO_OBJETIVO / pico)
    if ganancia > c.SONIDO_GANANCIA_MIN:
        _amplificar(editable, ganancia)
    entrada = min(largo, max(1, _cuadros(c.SONIDO_FUNDIDO_BORDE_MS, frecuencia)))
    salida_fundido = min(largo, max(entrada, _cuadros(fundido_ms, frecuencia)))
    _fundir(editable, 0, entrada, canales, True)
    _fundir(editable, largo - salida_fundido, largo, canales, False)
    return bytes(salida), pico


def envolvente(crudo: bytes, canales: int, frecuencia: int) -> list[float]:
    """El máximo de |amplitud| por ventana de SONIDO_VENTANA_MS, normalizado a 0..1 (lista vacía si no hay muestras)."""
    muestras = memoryview(crudo).cast("h")
    por_ventana = _cuadros(c.SONIDO_VENTANA_MS, frecuencia) * canales
    if por_ventana <= 0:
        return []
    picos = []
    for inicio in range(0, len(muestras), por_ventana):
        ventana = muestras[inicio:inicio + por_ventana]
        picos.append(max(max(ventana), -min(ventana)))
    mayor = max(picos) if picos else 0
    if mayor == 0:
        return [0.0] * len(picos)
    return [p / mayor for p in picos]


# ============================================================================ el motor
class Sonidos:

    def __init__(self, ruta_assets: str):
        self._carpeta = Path(ruta_assets) / c.CARPETA_SONIDOS
        self.activo = False
        self.ms_de_carga = 0                       # cuánto tardó abrir() (mezclador y carga de efectos)
        self.envolvente_latido: list[float] = []   # la de Low_Health ya recortado (la sigue el latido visual)
        self.duracion_latido_ms = 0                # lo que dura Low_Health ya recortado (0 si no se cargó)
        self._efectos: list = []                   # (nombre, Sound)
        self._inicio_musica = 0

    def abrir(self) -> bool:
        if self.activo:
            return True
        comienzo = pygame.time.get_ticks()
        try:
            frecuencia, tamano, canales, buffer = c.MEZCLADOR
            pygame.mixer.init(frequency=frecuencia, size=tamano, channels=canales, buffer=buffer)
            pygame.mixer.set_num_channels(c.MEZCLADOR_CANALES)
            pygame.mixer.set_reserved(c.MEZCLADOR_RESERVADOS)
        except pygame.error:
            self._apagar()
            return False
        self.activo = True
        self._cargar_efectos()
        self.ms_de_carga = pygame.time.get_ticks() - comienzo
        return True

    def cerrar(self) -> None:
        self._apagar()

    def _apagar(self) -> None:
        self.activo = False
        self._efectos = []
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            pygame.mixer.quit()
        except pygame.error:
            pass

    # ------------------------------------------------------------------ los efectos
    def _cargar_efectos(self) -> None:
        formato = pygame.mixer.get_init()
        if formato is None:
            return
        frecuencia, tamano, canales = formato
        for nombre, tope_ms, fundido_ms, volumen in c.SONIDOS_CORTOS:
            try:
                sonido = pygame.mixer.Sound(str(self._carpeta / (nombre + c.SONIDO_EXTENSION)))
                if tamano == -16:                  # solo con muestras de 16 bits se puede procesar
                    crudo = sonido.get_raw()
                    preparado, _ = preparar(crudo, canales, frecuencia, tope_ms, fundido_ms)
                    if nombre == c.SONIDO_LATIDO:
                        self.envolvente_latido = envolvente(preparado, canales, frecuencia)
                    sonido = pygame.mixer.Sound(buffer=preparado)
                sonido.set_volume(volumen)
                if nombre == c.SONIDO_LATIDO:
                    self.duracion_latido_ms = round(sonido.get_length() * 1000)
            except (pygame.error, OSError, ValueError):
                continue                           # ese sonido calla; los demás siguen
            self._efectos.append((nombre, sonido))

    def efecto(self, nombre: str) -> None:
        sonido = self._sonido(nombre)
        if sonido is not None:
            try:
                sonido.play()
            except pygame.error:
                pass

    def _sonido(self, nombre: str):
        if not self.activo:
            return None
        for clave, sonido in self._efectos:
            if clave == nombre:
                return sonido
        return None

    # ------------------------------------------------------------------ los canales reservados
    def latido(self, encender: bool) -> None:
        """Low_Health en bucle en el canal 0 (encender) o silencio (apagar)."""
        sonido = self._sonido(c.SONIDO_LATIDO)
        if sonido is None:
            return
        try:
            canal = pygame.mixer.Channel(0)
            if encender:
                canal.play(sonido, -1)
            else:
                canal.stop()
        except pygame.error:
            pass

    def pausar_latido(self, pausado: bool) -> None:
        if self._sonido(c.SONIDO_LATIDO) is None:
            return
        try:
            canal = pygame.mixer.Channel(0)
            if pausado:
                canal.pause()
            else:
                canal.unpause()
        except pygame.error:
            pass

    def fin(self, nombre: str) -> None:
        """Defeat_Music o Victory_Music, una vez, en el canal 1."""
        sonido = self._sonido(nombre)
        if sonido is None:
            return
        try:
            pygame.mixer.Channel(1).play(sonido)
        except pygame.error:
            pass

    def parar_fin(self, fundido_ms: int) -> None:
        if not self.activo:
            return
        try:
            pygame.mixer.Channel(1).fadeout(fundido_ms)
        except pygame.error:
            pass

    # ------------------------------------------------------------------ la música
    def musica(self, nombre: str, volumen: float, inicio_ms: int, entrada_ms: int) -> None:
        if not self.activo:
            return
        try:
            pygame.mixer.music.load(str(self._carpeta / (nombre + c.SONIDO_EXTENSION)))
            pygame.mixer.music.set_volume(volumen)
            pygame.mixer.music.play(0, inicio_ms / 1000, entrada_ms)
            self._inicio_musica = inicio_ms
        except (pygame.error, OSError):
            pass

    def volumen_musica(self, volumen: float) -> None:
        if self.activo:
            try:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, volumen)))
            except pygame.error:
                pass

    def parar_musica(self) -> None:
        if self.activo:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass

    def posicion_musica_ms(self) -> int:
        if not self.activo:
            return -1
        try:
            transcurrido = pygame.mixer.music.get_pos() if pygame.mixer.music.get_busy() else -1
        except pygame.error:
            return -1
        return -1 if transcurrido < 0 else transcurrido + self._inicio_musica

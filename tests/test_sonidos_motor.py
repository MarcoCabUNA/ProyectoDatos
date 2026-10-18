"""
Pruebas del MOTOR de sonido y su cargador (View/Sonidos.py), de la Vista con sonido=True y de una partida punta a punta. Usan el
mezclador de pygame con el controlador de audio "dummy" (no suena nada) y los 11 archivos reales de assets/sonidos.
Se ejecuta desde cualquier carpeta.
"""
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import letra, pygame, tecla  # noqa: E402  (fija los controladores dummy de video y audio)
from ayudas_vista import Recorrido, estado_base  # noqa: E402

from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from UIController.ControladorPygame import ControladorPygame  # noqa: E402
from ayudas_controladores import CONFIG_OFFLINE  # noqa: E402
from View import Componentes as c  # noqa: E402
from View.Sonidos import Sonidos, envolvente, preparar, primer_indice_sobre  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = str(RAIZ / "assets")
FRECUENCIA, CANALES = 44100, 2


def crudo(*segmentos):
    """Muestras de 16 bits estéreo: cada segmento es (milisegundos, amplitud) con la misma amplitud en las dos canales."""
    cuadros = [ms * FRECUENCIA // 1000 for ms, _ in segmentos]
    datos = bytearray(sum(cuadros) * CANALES * 2)
    muestras = memoryview(datos).cast("h")
    posicion = 0
    for (_, amplitud), cantidad in zip(segmentos, cuadros):
        for i in range(posicion * CANALES, (posicion + cantidad) * CANALES):
            muestras[i] = amplitud
        posicion += cantidad
    return bytes(datos)


def en_muestras(datos):
    return memoryview(datos).cast("h")


def cuadros(datos):
    return len(datos) // (CANALES * 2)


def milisegundos(cuadro):
    return cuadro * 1000 / FRECUENCIA


def preparado(*segmentos, tope_ms=0, fundido_ms=50):
    return preparar(crudo(*segmentos), CANALES, FRECUENCIA, tope_ms, fundido_ms)[0]


class MotorFalso:
    def __init__(self, abre=True, envolvente=None):
        self.abre = abre
        self.llamadas = []
        self.envolvente_latido = envolvente if envolvente is not None else []
        self.duracion_latido_ms = len(self.envolvente_latido) * c.SONIDO_VENTANA_MS

    def abrir(self):
        self.llamadas.append(("abrir",))
        return self.abre

    def cerrar(self):
        self.llamadas.append(("cerrar",))

    def efecto(self, nombre):
        self.llamadas.append(("efecto", nombre))

    def musica(self, nombre, volumen, inicio_ms, entrada_ms):
        self.llamadas.append(("musica", nombre, volumen, inicio_ms, entrada_ms))

    def volumen_musica(self, volumen):
        self.llamadas.append(("volumen", volumen))

    def parar_musica(self):
        self.llamadas.append(("parar",))

    def posicion_musica_ms(self):
        return 0

    def latido(self, encender):
        self.llamadas.append(("latido", encender))

    def pausar_latido(self, pausado):
        self.llamadas.append(("pausa_latido", pausado))

    def fin(self, nombre):
        self.llamadas.append(("fin", nombre))

    def parar_fin(self, fundido_ms):
        self.llamadas.append(("parar_fin", fundido_ms))


# ================================================================== el cargador (funciones puras)
def probar_se_quita_el_silencio_del_inicio_y_queda_a_lo_sumo_5_ms_antes_del_tono():
    salida = en_muestras(preparado((1000, 0), (200, 20000)))
    primera = primer_indice_sobre(salida, 0) // CANALES
    assert milisegundos(primera) <= c.SONIDO_MARGEN_MS + 0.03, milisegundos(primera)
    assert abs(milisegundos(cuadros(bytes(salida))) - (c.SONIDO_MARGEN_MS + 200)) < 0.1


def probar_el_ruido_bajo_el_diez_por_ciento_del_pico_tambien_cuenta_como_silencio():
    salida = en_muestras(preparado((500, 1000), (200, 20000)))       # 1000 es el 5 % de 20000
    assert milisegundos(primer_indice_sobre(salida, 2000) // CANALES) <= c.SONIDO_MARGEN_MS + 0.03   # el tono, no el ruido
    assert abs(milisegundos(len(salida) // CANALES) - (c.SONIDO_MARGEN_MS + 200)) < 0.1              # y el ruido se fue


def probar_un_inicio_justo_por_encima_del_umbral_no_se_recorta():
    salida = en_muestras(preparado((500, 0), (100, 2100), (100, 20000)))   # 2100 > 10 % de 20000
    assert 2100 in salida and milisegundos(primer_indice_sobre(salida, 0) // CANALES) <= c.SONIDO_MARGEN_MS + 0.03


def probar_el_tope_limita_la_duracion_y_el_fundido_de_salida_baja_hasta_casi_cero():
    salida = en_muestras(preparado((100, 0), (3000, 20000), tope_ms=800, fundido_ms=100))
    total = len(salida) // CANALES
    assert total == 800 * FRECUENCIA // 1000
    assert abs(salida[-2]) < 20000 * 0.01                                  # la última muestra casi no se oye
    inicio_fundido = total - 100 * FRECUENCIA // 1000
    medio = salida[(total // 2) * CANALES]
    assert medio == 20000                                                  # lo de en medio no se toca
    tramo = [salida[i * CANALES] for i in range(inicio_fundido, total)]
    assert all(tramo[i] >= tramo[i + 1] for i in range(len(tramo) - 1))    # baja sin subir
    assert tramo[0] > 20000 * 0.9


def probar_hay_fundido_de_entrada_de_5_ms_si_el_sonido_empieza_fuerte():
    salida = en_muestras(preparado((300, 20000)))                          # sin silencio: empieza en la primera muestra
    entrada = c.SONIDO_FUNDIDO_BORDE_MS * FRECUENCIA // 1000
    tramo = [salida[i * CANALES] for i in range(entrada)]
    assert tramo[0] < 20000 * 0.02 and all(tramo[i] <= tramo[i + 1] for i in range(len(tramo) - 1))
    assert salida[(entrada + 10) * CANALES] == 20000


def probar_la_ganancia_solo_se_aplica_si_supera_1_5():
    sube = en_muestras(preparado((50, 0), (400, 16384)))                   # pico 0,5 -> ganancia 1,8
    assert abs(sube[(len(sube) // CANALES // 2) * CANALES] - int(16384 * 0.9 / 0.5)) <= 1
    igual = en_muestras(preparado((50, 0), (400, 26214)))                  # pico 0,8 -> ganancia 1,125: no se toca
    assert igual[(len(igual) // CANALES // 2) * CANALES] == 26214
    tope = en_muestras(preparado((50, 0), (400, 3277)))                    # pico 0,1 -> ganancia limitada a 6
    assert abs(tope[(len(tope) // CANALES // 2) * CANALES] - int(3277 * c.SONIDO_GANANCIA_MAX)) <= 1


def probar_la_ganancia_no_se_pasa_de_los_limites_de_16_bits():
    salida = en_muestras(preparado((50, 0), (400, 3277), (100, 32767)))    # el pico pide poca ganancia: nada se sale
    assert max(salida) <= 32767 and min(salida) >= -32768


def probar_un_sonido_que_es_todo_silencio_queda_igual():
    datos = crudo((300, 0))
    salida, pico = preparar(datos, CANALES, FRECUENCIA, 100, 20)
    assert salida == datos and pico == 0.0


def probar_la_envolvente_tiene_una_ventana_por_cada_20_ms_y_va_de_0_a_1():
    valores = envolvente(crudo((40, 0), (40, 10000)), CANALES, FRECUENCIA)
    assert valores == [0.0, 0.0, 1.0, 1.0]
    assert envolvente(crudo((40, 0)), CANALES, FRECUENCIA) == [0.0, 0.0]
    assert envolvente(b"", CANALES, FRECUENCIA) == []


# ================================================================== el motor con los archivos reales
def probar_se_cargan_los_nueve_efectos_reales_y_el_arranque_cumple_la_meta():
    motor = Sonidos(ASSETS)
    comienzo = time.perf_counter()
    try:
        assert motor.abrir() and motor.activo
        total_ms = (time.perf_counter() - comienzo) * 1000
        nombres = [nombre for nombre, _ in motor._efectos]
        assert nombres == [fila[0] for fila in c.SONIDOS_CORTOS], nombres
        assert total_ms < 800, total_ms
        print(f"  arranque del cargador (mezclador + 9 efectos): {total_ms:.0f} ms (meta: menos de 800 ms)")
    finally:
        motor.cerrar()


def probar_hero_impact_hit_empieza_casi_de_inmediato_y_main_room_y_victory_suben_de_volumen():
    pygame.mixer.init(frequency=FRECUENCIA, size=-16, channels=CANALES, buffer=512)
    try:
        resultados = []
        for nombre in ("Hero_Impact_Hit", "Main_Room_Sound", "Victory_Music", "Click"):
            sonido = pygame.mixer.Sound(str(RAIZ / "assets" / c.CARPETA_SONIDOS / (nombre + c.SONIDO_EXTENSION)))
            original = sonido.get_raw()
            fila = [f for f in c.SONIDOS_CORTOS if f[0] == nombre][0]
            salida, pico = preparar(original, CANALES, FRECUENCIA, fila[1], fila[2])
            muestras = en_muestras(salida)
            primera = primer_indice_sobre(muestras, int(pico * 32768 * c.SONIDO_UMBRAL_INICIO)) // CANALES
            resultados.append((nombre, milisegundos(primera), max(max(muestras), -min(muestras)) / 32768, pico))
        hero, sala, victoria, click = resultados
        assert hero[1] < 20, hero                                           # antes tardaba 3995 ms
        assert sala[2] > 0.85 and victoria[2] > 0.85                         # los dos muy bajos suben cerca de 0,9
        assert abs(click[2] - click[3]) < 0.01                               # Click no se amplifica
    finally:
        pygame.mixer.quit()


def probar_la_envolvente_de_low_health_cubre_el_sonido_recortado_en_ventanas_de_20_ms():
    motor = Sonidos(ASSETS)
    try:
        motor.abrir()
        sonido = [s for n, s in motor._efectos if n == c.SONIDO_LATIDO][0]
        ventanas = -(-int(sonido.get_length() * 1000) // c.SONIDO_VENTANA_MS)
        assert abs(len(motor.envolvente_latido) - ventanas) <= 1, (len(motor.envolvente_latido), ventanas)
        assert max(motor.envolvente_latido) == 1.0 and min(motor.envolvente_latido) >= 0.0
    finally:
        motor.cerrar()


def probar_la_musica_arranca_donde_se_pide_y_se_puede_parar():
    motor = Sonidos(ASSETS)
    try:
        assert motor.abrir()
        motor.musica("Main_Menu", 0.5, 2000, 0)
        assert pygame.mixer.music.get_busy()
        assert motor.posicion_musica_ms() >= 2000
        motor.volumen_musica(0.2)
        assert abs(pygame.mixer.music.get_volume() - 0.2) < 0.01
        motor.parar_musica()
        assert motor.posicion_musica_ms() == -1
    finally:
        motor.cerrar()


# ================================================================== lo que falla sin que el juego se entere
def probar_sin_la_carpeta_de_sonidos_no_hay_excepciones_y_no_suena_nada():
    with tempfile.TemporaryDirectory() as vacia:
        motor = Sonidos(vacia)
        try:
            assert motor.abrir()
            motor.efecto(c.SONIDO_CLICK)
            motor.musica("Main_Menu", 0.5, 0, 0)
            assert motor.posicion_musica_ms() == -1 and motor._efectos == []
        finally:
            motor.cerrar()


def probar_un_archivo_danado_calla_ese_sonido_y_los_demas_siguen():
    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / c.CARPETA_SONIDOS
        destino.mkdir()
        (destino / "Click.mp3").write_bytes(b"esto no es un mp3" * 50)
        for nombre in ("Hero_Impact_Hit", "Defeat_Music"):
            (destino / (nombre + c.SONIDO_EXTENSION)).write_bytes(
                (RAIZ / "assets" / c.CARPETA_SONIDOS / (nombre + c.SONIDO_EXTENSION)).read_bytes())
        motor = Sonidos(carpeta)
        try:
            assert motor.abrir()
            assert [n for n, _ in motor._efectos] == ["Hero_Impact_Hit", "Defeat_Music"]
            motor.efecto(c.SONIDO_CLICK)
            motor.efecto("Hero_Impact_Hit")
        finally:
            motor.cerrar()


def probar_si_el_mezclador_falla_el_sonido_se_apaga_sin_excepciones():
    original = pygame.mixer.init

    def falla(*_args, **_kwargs):
        raise pygame.error("no hay dispositivo de audio")

    pygame.mixer.init = falla
    try:
        motor = Sonidos(ASSETS)
        assert motor.abrir() is False and not motor.activo
        motor.efecto(c.SONIDO_CLICK)
        motor.musica("Main_Menu", 0.5, 0, 0)
        motor.volumen_musica(0.1)
        motor.parar_musica()
        assert motor.posicion_musica_ms() == -1
        motor.cerrar()
    finally:
        pygame.mixer.init = original


def probar_cerrar_dos_veces_es_seguro_y_deja_el_mezclador_apagado():
    motor = Sonidos(ASSETS)
    motor.abrir()
    motor.cerrar()
    motor.cerrar()
    assert pygame.mixer.get_init() is None
    Sonidos(ASSETS).cerrar()                                                 # sin haberse abierto nunca


# ================================================================== la Vista
def probar_con_sonido_false_el_motor_nunca_se_crea_y_el_mezclador_no_se_inicia():
    creados = []
    vista = VistaPygame(fabrica_sonidos=lambda ruta: creados.append(ruta) or MotorFalso())
    vista.abrir()
    try:
        vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Comenzar juego"], 0, activaciones=3))
        assert creados == [] and pygame.mixer.get_init() is None
    finally:
        vista.cerrar()


def probar_con_sonido_true_las_llamadas_al_motor_coinciden_con_lo_que_se_ve_y_se_oye():
    motor = MotorFalso()
    vista = VistaPygame(sonido=True, fabrica_sonidos=lambda ruta: motor)
    vista.abrir()
    try:
        assert motor.llamadas == [("abrir",)]
        vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Comenzar juego"], 0))
        assert motor.llamadas[1:] == [("musica", "Main_Menu", 0.5, 2000, c.MUSICA_ENTRADA_MS)]
        vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Comenzar juego"], 0, activaciones=1))
        assert motor.llamadas[-1] == ("efecto", c.SONIDO_CLICK)
    finally:
        vista.cerrar()
        vista.cerrar()
    assert motor.llamadas.count(("cerrar",)) == 1                           # el segundo cerrar() no vuelve a llamarlo


def probar_si_el_motor_no_puede_abrirse_la_vista_sigue_en_silencio():
    motor = MotorFalso(abre=False)
    vista = VistaPygame(sonido=True, fabrica_sonidos=lambda ruta: motor)
    vista.abrir()
    try:
        vista.dibujar(PantallaDTO("menu", "CRIPTA", ["Comenzar juego"], 0, activaciones=1))
    finally:
        vista.cerrar()
    assert motor.llamadas == [("abrir",)]


def probar_las_zonas_de_clic_no_cambian_con_sonido_y_dibujar_casi_no_cuesta():
    pantalla = PantallaDTO("menu", "CRIPTA", ["Comenzar juego", "Modo: Offline", "Salir"], 1)
    tiempos, respuestas = [], []
    for sonido in (False, True, False, True):
        vista = VistaPygame(sonido=sonido, fabrica_sonidos=lambda ruta: MotorFalso())
        vista.abrir()
        try:
            vista.dibujar(pantalla)
            respuestas.append([vista.elemento_en((x, y)) for x in range(0, c.ANCHO, 32) for y in range(0, c.ALTO, 32)])
            comienzo = time.perf_counter()
            for _ in range(150):
                vista.dibujar(pantalla)
            tiempos.append((time.perf_counter() - comienzo) * 1000 / 150)
        finally:
            vista.cerrar()
    assert respuestas[0] == respuestas[1] == respuestas[2] == respuestas[3]
    sin, con = (tiempos[0] + tiempos[2]) / 2, (tiempos[1] + tiempos[3]) / 2
    assert con - sin < 1.0, (sin, con)
    print(f"  dibujar(): {sin:.2f} ms sin sonido, {con:.2f} ms con sonido (diferencia {con - sin:+.2f} ms)")


# ================================================================== los canales reservados del motor real
def probar_low_health_suena_en_bucle_en_el_canal_0_y_se_apaga_sin_tocar_los_efectos():
    motor = Sonidos(ASSETS)
    try:
        assert motor.abrir()
        assert motor.duracion_latido_ms > 20000 and abs(motor.duracion_latido_ms - len(motor.envolvente_latido) * 20) <= 20
        motor.latido(True)
        assert pygame.mixer.Channel(0).get_busy()
        motor.pausar_latido(True)
        motor.pausar_latido(False)
        assert pygame.mixer.Channel(0).get_busy()
        motor.efecto(c.SONIDO_CLICK)                                         # los efectos usan otros canales, no el 0 ni el 1
        assert not pygame.mixer.Channel(1).get_busy()
        motor.latido(False)
        assert not pygame.mixer.Channel(0).get_busy()
    finally:
        motor.cerrar()


def probar_la_derrota_y_la_victoria_suenan_en_el_canal_1_y_se_apagan_con_fundido():
    motor = Sonidos(ASSETS)
    try:
        assert motor.abrir()
        motor.fin("Defeat_Music")
        assert pygame.mixer.Channel(1).get_busy() and not pygame.mixer.Channel(0).get_busy()
        motor.parar_fin(c.SONIDO_FIN_FUNDIDO_MS)
        time.sleep(c.SONIDO_FIN_FUNDIDO_MS / 1000 + 0.3)
        assert not pygame.mixer.Channel(1).get_busy()                        # el fundido terminó y el canal quedó libre
        motor.fin("Victory_Music")
        assert pygame.mixer.Channel(1).get_busy()
    finally:
        motor.cerrar()


def probar_los_metodos_de_la_fase_2_no_fallan_con_el_motor_apagado_o_sin_archivos():
    with tempfile.TemporaryDirectory() as vacia:
        for ruta, abrir in ((vacia, True), (ASSETS, False)):                  # sin archivos, y sin haberse abierto nunca
            motor = Sonidos(ruta)
            if abrir:
                motor.abrir()
            motor.latido(True)
            motor.pausar_latido(True)
            motor.fin("Defeat_Music")
            motor.parar_fin(100)
            motor.latido(False)
            motor.cerrar()


# ================================================================== la Vista: el latido visual y los sonidos de fin
def _pantalla_de_juego(vida):
    estado = estado_base()
    estado = replace(estado, jugador=replace(estado.jugador, vida=vida, vida_max=30))
    return PantallaDTO("juego", opciones=["Esperar"], seleccion=-1, estado=estado)


def _borde_tras_dibujar(envolvente, vida=3):
    """El brillo medio de la franja izquierda (donde más se nota la viñeta) en el segundo cuadro con vida baja, con esa envolvente."""
    reloj = [1000]
    vista = VistaPygame(animaciones=True, sonido=True, reloj=lambda: reloj[0],
                        fabrica_sonidos=lambda ruta: MotorFalso(envolvente=envolvente))
    vista.abrir()
    try:
        pantalla = _pantalla_de_juego(vida)
        vista.dibujar(pantalla)                                              # este cuadro hace que empiece a sonar Low_Health
        reloj[0] += 33
        vista.dibujar(pantalla)                                              # este ya dibuja la viñeta con la envolvente
        superficie = pygame.display.get_surface()
        puntos = [superficie.get_at((x, y))[:3] for x in range(30, 90, 10) for y in range(300, 400, 10)]
        return sum(sum(punto) for punto in puntos) / len(puntos), vista
    finally:
        vista.cerrar()


def probar_con_sonido_la_vineta_sigue_la_envolvente_y_sin_envolvente_usa_el_pulso_fijo():
    fuerte, _ = _borde_tras_dibujar([1.0] * 60)
    suave, _ = _borde_tras_dibujar([0.0] * 60)
    assert abs(fuerte - suave) > 1, (fuerte, suave)                          # la envolvente al máximo y al mínimo se ven distintas
    sin_sonido = VistaPygame(animaciones=True, reloj=lambda: 1033)           # sin sonido: pulso fijo de 1,8 s, sin excepciones
    sin_sonido.abrir()
    try:
        sin_sonido.dibujar(_pantalla_de_juego(3))
        sin_sonido.dibujar(_pantalla_de_juego(3))
    finally:
        sin_sonido.cerrar()


def probar_la_vista_llama_a_latido_y_a_los_sonidos_de_fin_del_motor():
    motor = MotorFalso(envolvente=[0.5] * 40)
    vista = VistaPygame(animaciones=True, sonido=True, reloj=lambda: 5000, fabrica_sonidos=lambda ruta: motor)
    vista.abrir()
    try:
        vista.dibujar(_pantalla_de_juego(25))
        assert ("latido", True) not in motor.llamadas                         # vida alta
        vista.dibujar(_pantalla_de_juego(5))
        assert ("latido", True) in motor.llamadas
        estado = _pantalla_de_juego(0).estado
        vista.dibujar(PantallaDTO("derrota", opciones=["Menú"], estado=replace(estado, terminado=True, resultado="derrota")))
        assert ("latido", False) in motor.llamadas and ("fin", "Defeat_Music") in motor.llamadas
        vista.dibujar(PantallaDTO("puntajes", "Puntajes", ["Volver"], 0))
        assert ("parar_fin", c.SONIDO_FIN_FUNDIDO_MS) in motor.llamadas
    finally:
        vista.cerrar()


def _eventos_de_una_partida_perdida():
    """Menú -> Comenzar -> cripta -> nombre -> partida -> esperar hasta perder -> salir. Un lote de eventos por cuadro."""
    lotes = [[], [tecla(pygame.K_RETURN)], [tecla(pygame.K_RETURN)]]        # el primer cuadro es el menú, sin eventos
    lotes.append([letra(caracter) for caracter in "Ana"])
    lotes.append([tecla(pygame.K_RETURN)])
    lotes.append([tecla(pygame.K_UP)])                                      # a la sala de las ratas: aquí se pierde
    lotes.extend([[tecla(pygame.K_SPACE)] for _ in range(3)])               # el héroe ataca a una rata (golpe a un enemigo)
    lotes.extend([[tecla(pygame.K_z)] for _ in range(100)])
    lotes.append([tecla(pygame.K_DOWN)])
    lotes.append([tecla(pygame.K_RETURN)])                                  # en la derrota: "Ver puntajes"
    lotes.append([pygame.event.Event(pygame.QUIT)])
    return lotes


def probar_una_partida_perdida_en_el_bucle_real_con_el_motor_real_no_da_excepciones():
    nombres = []
    pedidos = []

    class MotorQueAnota(Sonidos):
        def efecto(self, nombre):
            pedidos.append(("efecto", nombre))
            super().efecto(nombre)

        def fin(self, nombre):
            pedidos.append(("fin", nombre))
            super().fin(nombre)

        def latido(self, encender):
            pedidos.append(("latido", encender))
            super().latido(encender)

    class Vigilada(VistaPygame):
        def dibujar(self, pantalla):
            nombres.append(pantalla.pantalla)
            super().dibujar(pantalla)

    vista = Vigilada(animaciones=True, sonido=True, fabrica_sonidos=MotorQueAnota)
    with Recorrido(vista) as recorrido:
        # con una demora del fin (como en main.py) se dibuja el estado final: el golpe que mata se ve en un cuadro de partida
        controlador = ControladorPygame(vista, CONFIG_OFFLINE, recorrido.controlador._fabrica, demora_fin_ms=400)
        lotes = _eventos_de_una_partida_perdida()
        controlador.ejecutar(lambda: lotes.pop(0) if lotes else [])
        assert vista._sonidos is None                                       # ejecutar() la cerró
    for esperada in ("menu", "criptas", "nombre", "juego", "derrota", "puntajes"):
        assert esperada in nombres, (esperada, nombres)
    assert pygame.mixer.get_init() is None
    assert ("efecto", c.SONIDO_SALA) in pedidos and ("efecto", c.SONIDO_CLICK) in pedidos      # la partida nueva y los botones
    assert ("efecto", c.SONIDO_GOLPE_HEROE) in pedidos and ("efecto", c.SONIDO_GOLPE_ENEMIGO) in pedidos   # el combate con las ratas
    assert pedidos.count(("fin", "Defeat_Music")) == 1 and ("fin", "Victory_Music") not in pedidos     # perdió: solo la derrota
    assert pedidos.count(("latido", True)) == pedidos.count(("latido", False))                          # lo que se enciende se apaga


if __name__ == "__main__":
    probar_se_quita_el_silencio_del_inicio_y_queda_a_lo_sumo_5_ms_antes_del_tono()
    probar_el_ruido_bajo_el_diez_por_ciento_del_pico_tambien_cuenta_como_silencio()
    probar_un_inicio_justo_por_encima_del_umbral_no_se_recorta()
    probar_el_tope_limita_la_duracion_y_el_fundido_de_salida_baja_hasta_casi_cero()
    probar_hay_fundido_de_entrada_de_5_ms_si_el_sonido_empieza_fuerte()
    probar_la_ganancia_solo_se_aplica_si_supera_1_5()
    probar_la_ganancia_no_se_pasa_de_los_limites_de_16_bits()
    probar_un_sonido_que_es_todo_silencio_queda_igual()
    probar_la_envolvente_tiene_una_ventana_por_cada_20_ms_y_va_de_0_a_1()
    probar_se_cargan_los_nueve_efectos_reales_y_el_arranque_cumple_la_meta()
    probar_hero_impact_hit_empieza_casi_de_inmediato_y_main_room_y_victory_suben_de_volumen()
    probar_la_envolvente_de_low_health_cubre_el_sonido_recortado_en_ventanas_de_20_ms()
    probar_la_musica_arranca_donde_se_pide_y_se_puede_parar()
    probar_sin_la_carpeta_de_sonidos_no_hay_excepciones_y_no_suena_nada()
    probar_un_archivo_danado_calla_ese_sonido_y_los_demas_siguen()
    probar_si_el_mezclador_falla_el_sonido_se_apaga_sin_excepciones()
    probar_cerrar_dos_veces_es_seguro_y_deja_el_mezclador_apagado()
    probar_con_sonido_false_el_motor_nunca_se_crea_y_el_mezclador_no_se_inicia()
    probar_con_sonido_true_las_llamadas_al_motor_coinciden_con_lo_que_se_ve_y_se_oye()
    probar_si_el_motor_no_puede_abrirse_la_vista_sigue_en_silencio()
    probar_las_zonas_de_clic_no_cambian_con_sonido_y_dibujar_casi_no_cuesta()
    probar_low_health_suena_en_bucle_en_el_canal_0_y_se_apaga_sin_tocar_los_efectos()
    probar_la_derrota_y_la_victoria_suenan_en_el_canal_1_y_se_apagan_con_fundido()
    probar_los_metodos_de_la_fase_2_no_fallan_con_el_motor_apagado_o_sin_archivos()
    probar_con_sonido_la_vineta_sigue_la_envolvente_y_sin_envolvente_usa_el_pulso_fijo()
    probar_la_vista_llama_a_latido_y_a_los_sonidos_de_fin_del_motor()
    probar_una_partida_perdida_en_el_bucle_real_con_el_motor_real_no_da_excepciones()
    print("OK: todas las pruebas del motor de sonido pasaron")

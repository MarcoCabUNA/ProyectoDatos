"""
Pruebas de main.py (Etapa 8): los modos y sus códigos de salida, que --replay y --bench NO importan pygame (arquitectura §6), y la
partida completa con la Vista real (SDL_VIDEODRIVER=dummy), el Controlador real y los servicios reales, jugada con eventos
simulados dentro del bucle de verdad (ControladorPygame.ejecutar). Los clics van a la POSICIÓN VISUAL de cada cosa.
Se ejecuta desde cualquier carpeta; todo lo que se escribe va a carpetas temporales.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAIZ))
import test_servicio_replay as replay_ayudas  # noqa: E402  (genera un log jugando una partida real)
from ayudas_pygame import clic, movimiento, pygame, tecla  # noqa: E402
from ayudas_vista import ARRIBA, ESC, Recorrido  # noqa: E402

import main  # noqa: E402
from UIController.LectorArgumentos import TEXTO_AYUDA  # noqa: E402
from View import Componentes as c  # noqa: E402
from View.EscenaJuego import posicion_del_protagonista, repartir_escena  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402


@contextlib.contextmanager
def en_carpeta_temporal():
    """El directorio de trabajo es una carpeta vacía (cache/ y logs/ nacen ahí, no en el proyecto)."""
    anterior, carpeta = os.getcwd(), tempfile.mkdtemp()
    os.chdir(carpeta)
    try:
        yield carpeta
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


def correr_main(argumentos):
    """main.main(argumentos) con la salida capturada: (código, texto impreso)."""
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        codigo = main.main(argumentos)
    return codigo, salida.getvalue()


# ================================================================ los modos y sus códigos de salida
def probar_ayuda_sale_con_0_e_imprime_el_texto_de_ayuda():
    codigo, texto = correr_main(["--ayuda"])
    assert codigo == 0 and TEXTO_AYUDA in texto and "--replay" in texto and "--bench" in texto
    assert correr_main(["-h"])[0] == 0 and correr_main(["--help"])[0] == 0


def probar_opciones_invalidas_imprimen_el_error_y_la_ayuda_y_salen_con_2():
    for argumentos in (["--cache-size", "abc"], ["--cache-size", "0"], ["--no-existe"], ["--replay"], ["--replay", " "],
                       ["--bench", "--replay", "x.log"], ["--off"]):
        codigo, texto = correr_main(argumentos)
        assert codigo == 2, (argumentos, codigo)
        assert "Error en las opciones" in texto and TEXTO_AYUDA in texto, argumentos


def probar_un_replay_de_un_archivo_inexistente_sale_con_1_y_dice_cual():
    with en_carpeta_temporal() as carpeta:
        shutil.copytree(RAIZ / "paquete", Path(carpeta) / "paquete")
        codigo, texto = correr_main(["--offline", "--replay", os.path.join(carpeta, "no_existe.log")])
        assert codigo == 1 and "no_existe.log" in texto, texto
        assert "Traceback" not in texto


def probar_un_replay_real_imprime_una_linea_por_accion_y_el_resumen():
    with en_carpeta_temporal() as carpeta:
        shutil.copytree(RAIZ / "paquete", Path(carpeta) / "paquete")
        ruta, estados = replay_ayudas._jugar(os.path.join(carpeta, "origen"), 3)
        acciones = len(estados) - 1
        assert acciones >= 3
        codigo, texto = correr_main(["--offline", "--replay", ruta])
        lineas = texto.splitlines()
        assert codigo == 0, texto
        numeradas = [l for l in lineas if l.strip()[:1].isdigit()]
        assert len(numeradas) == acciones and numeradas[0].split()[0] == "1" and numeradas[-1].split()[0] == str(acciones)
        for esperado in ("Cripta: cripta-01", "Semilla: 3", f"Acciones reproducidas: {acciones}", "Resultado:"):
            assert any(l.startswith(esperado) for l in lineas), (esperado, texto)
        assert "versión" in texto and "catálogo" in texto


# ================================================================ sin pygame (§6)
def _correr_en_un_interprete_limpio(argumentos, carpeta):
    """main.main(argumentos) en un intérprete nuevo, con 'carpeta' (que trae paquete/) de directorio de trabajo.
    Devuelve (código de main, 'pygame' in sys.modules, salida)."""
    codigo = (f"import sys; sys.path.insert(0, {str(RAIZ)!r}); import main; "
              f"rc = main.main({argumentos!r}); print('RESULTADO', rc, 'pygame' in sys.modules)")
    resultado = subprocess.run([sys.executable, "-B", "-c", codigo], cwd=carpeta, capture_output=True, text=True,
                               encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ultima = [l for l in resultado.stdout.splitlines() if l.startswith("RESULTADO ")]
    assert ultima, (resultado.stdout[-500:], resultado.stderr[-800:])
    _, rc, con_pygame = ultima[-1].split()
    return int(rc), con_pygame == "True", resultado.stdout


def probar_replay_en_un_interprete_limpio_termina_con_0_y_sin_importar_pygame():
    with en_carpeta_temporal() as carpeta:
        shutil.copytree(RAIZ / "paquete", Path(carpeta) / "paquete")
        ruta, estados = replay_ayudas._jugar(os.path.join(carpeta, "origen"), 3)
        assert len(estados) > 1
        codigo, con_pygame, salida = _correr_en_un_interprete_limpio(["--offline", "--replay", ruta], carpeta)
        assert codigo == 0, salida
        assert con_pygame is False, "--replay importó pygame"
        assert "Acciones reproducidas" in salida


def probar_bench_en_un_interprete_limpio_termina_con_0_y_sin_importar_pygame():
    with en_carpeta_temporal() as carpeta:
        shutil.copytree(RAIZ / "paquete", Path(carpeta) / "paquete")
        codigo, con_pygame, salida = _correr_en_un_interprete_limpio(["--offline", "--bench"], carpeta)
        assert codigo == 0, salida[-800:]
        assert con_pygame is False, "--bench importó pygame"
        assert "Midiendo... grupo" in salida


def probar_importar_main_no_importa_pygame_ni_la_vista():
    with en_carpeta_temporal() as carpeta:
        codigo = (f"import sys; sys.path.insert(0, {str(RAIZ)!r}); import main; "
                  "print('RESULTADO', 0, 'pygame' in sys.modules or 'View.VistaPygame' in sys.modules)")
        r = subprocess.run([sys.executable, "-B", "-c", codigo], cwd=carpeta, capture_output=True, text=True,
                           encoding="utf-8", timeout=120, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        assert "RESULTADO 0 False" in r.stdout, (r.stdout, r.stderr[-500:])


def probar_si_falta_pygame_el_modo_interactivo_lo_dice_y_sale_con_1():
    codigo = (f"import sys; sys.path.insert(0, {str(RAIZ)!r}); sys.modules['pygame'] = None; import main; "
              "rc = main.main(['--offline']); print('RESULTADO', rc)")
    with en_carpeta_temporal() as carpeta:
        r = subprocess.run([sys.executable, "-B", "-c", codigo], cwd=carpeta, capture_output=True, text=True,
                           encoding="utf-8", timeout=120, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert "RESULTADO 1" in r.stdout, (r.stdout, r.stderr[-500:])
    assert "No se puede abrir la interfaz gráfica: falta el módulo 'pygame'" in r.stdout
    assert "Instálalo con: uv add pygame-ce" in r.stdout


# ================================================================ la partida completa, con la Vista real
class Guion:
    """Juega una partida dentro del bucle REAL de ControladorPygame.ejecutar: cada vez que el bucle pide eventos, el guion mira
    lo último que se dibujó y devuelve los eventos del siguiente paso (todos los clics, a la posición donde se VE cada cosa)."""

    def __init__(self, recorrido):
        self.r = recorrido
        self.vista = recorrido.vista
        self.pasos = self._pasos()
        self.anotaciones = []
        self.termino = False

    def __call__(self):
        try:
            return next(self.pasos)
        except StopIteration:
            self.termino = True
            raise AssertionError("el guion terminó y el juego sigue abierto: 'Salir' no cerró el programa")

    # -- ayudas
    def pantalla(self):
        return self.r.pantalla()

    def en(self, nombre):
        assert self.pantalla().pantalla == nombre, (nombre, self.pantalla().pantalla)

    def clic_en_boton(self, texto):
        """El clic al botón que dice 'texto', en el lugar donde se dibuja (el de más arriba es el 0)."""
        return [clic(self.r.centro_del_boton(self.r.posicion_del_texto(texto)))]

    def reparto(self, pies):
        estado = self.pantalla().estado
        return repartir_escena(self.vista._escena._almacen, self.vista._fuentes, estado.enemigos, estado.objetos_suelo,
                               estado.sala.salidas, pies)

    # -- el guion
    def _pasos(self):
        r = self.r
        yield []                                                     # el primer cuadro: el menú
        self.en("menu")
        yield self.clic_en_boton("Comenzar juego")
        self.en("criptas")
        yield [clic(r.centro_del_boton(0))]                          # la primera cripta de la lista (arriba)
        self.en("nombre")
        yield [tecla(pygame.K_BACKSPACE)] * 16
        for caracter in "Ana":
            yield [tecla(ord(caracter.lower()), mod=pygame.KMOD_LSHIFT if caracter.isupper() else 0, caracter=caracter)]
        yield self.clic_en_boton("Aceptar")
        self.en("juego")
        estado = self.pantalla().estado
        assert [o.nombre for o in estado.objetos_suelo] == ["Antorcha"]
        # recoger: clic sobre la antorcha del suelo, donde la función de reparto la pone (el protagonista, al centro)
        yield [movimiento(self.reparto(c.PIES_CENTRO).objetos[0].center)]      # (pasar el ratón: sale su nombre)
        yield [clic(self.reparto(c.PIES_CENTRO).objetos[0].center)]
        assert [o.nombre for o in self.pantalla().estado.inventario.objetos] == ["Antorcha"]
        # pausa -> guardar (en la sala 1, donde todavía no hay peligro)
        yield [tecla(ESC)]
        self.en("pausa")
        yield self.clic_en_boton("Guardar partida")
        self.en("pausa")
        assert os.path.exists(self._ruta_guardado()), "no se guardó la partida"
        guardado = self.pantalla().estado
        yield self.clic_en_boton("Continuar")
        self.en("juego")
        yield [tecla(pygame.K_z)]                                    # esperar un poco: el estado cambia después de guardar
        assert self.pantalla().estado.reloj > guardado.reloj
        # pausa -> cargar: vuelve a lo guardado
        yield [tecla(ESC)]
        yield self.clic_en_boton("Cargar partida")
        self.en("juego")
        cargado = self.pantalla().estado
        assert cargado.reloj == guardado.reloj and cargado.sala.id == guardado.sala.id, (cargado.reloj, guardado.reloj)
        assert [o.nombre for o in cargado.inventario.objetos] == ["Antorcha"]
        # mover: a la sala de las ratas
        yield [tecla(ARRIBA)]
        estado = self.pantalla().estado
        assert len(estado.enemigos) == 2, estado.enemigos
        pies = posicion_del_protagonista(estado.sala.salidas, 1)
        # atacar: clic sobre la primera rata
        yield [clic(self.reparto(pies).enemigos[0].center)]
        assert any("Jugador ataca a Rata gigante #1" in m for m in self.pantalla().estado.mensajes)
        # perder: esperar hasta que las ratas ganen
        for _ in range(150):
            if self.pantalla().pantalla != "juego":
                break
            yield [tecla(pygame.K_z)]
        self.en("derrota")
        yield []                                                     # (el cuadro de la derrota)
        yield self.clic_en_boton("Ver puntajes")
        self.en("puntajes")
        yield self.clic_en_boton("Volver")
        for _ in range(3):                                           # hasta el menú, por los botones que se vean
            if self.pantalla().pantalla == "menu":
                break
            yield self.clic_en_boton("Menú principal" if self.pantalla().pantalla in ("derrota", "victoria") else "Volver")
        self.en("menu")
        yield self.clic_en_boton("Salir")                            # el bucle debe terminar

    def _ruta_guardado(self):
        import UIController.ControladorPygame as modulo
        return modulo.RUTA_GUARDADO


def probar_una_partida_completa_con_la_vista_real_desde_el_menu_hasta_salir():
    vista = VistaPygame()                                            # sin abrir: ejecutar() la abre y la cierra
    with Recorrido(vista) as recorrido:
        guion = Guion(recorrido)
        recorrido.controlador.ejecutar(guion)
        assert recorrido.controlador._activo is False and guion.termino is False   # salió por el botón, no se agotó el guion
        assert vista._superficie is None                             # y la ventana se cerró


def probar_cerrar_la_ventana_en_cualquier_pantalla_termina_el_bucle_sin_error():
    for despues in ("menu", "criptas", "juego"):
        vista = VistaPygame()
        with Recorrido(vista) as recorrido:
            pasos = {"n": 0}

            def eventos(despues=despues, recorrido=recorrido, pasos=pasos):
                pasos["n"] += 1
                if pasos["n"] == 1:
                    return []
                if pasos["n"] == 2 and despues != "menu":
                    return [clic(recorrido.centro_del_boton(0))]       # a las criptas
                if pasos["n"] == 3 and despues == "juego":
                    return [clic(recorrido.centro_del_boton(0))]       # al nombre
                if pasos["n"] == 4 and despues == "juego":
                    return [tecla(pygame.K_RETURN)]
                if pasos["n"] > 6:
                    return [pygame.event.Event(pygame.QUIT)]
                return []
            recorrido.controlador.ejecutar(eventos)
            assert recorrido.controlador._activo is False and vista._superficie is None


if __name__ == "__main__":
    probar_ayuda_sale_con_0_e_imprime_el_texto_de_ayuda()
    probar_opciones_invalidas_imprimen_el_error_y_la_ayuda_y_salen_con_2()
    probar_un_replay_de_un_archivo_inexistente_sale_con_1_y_dice_cual()
    probar_un_replay_real_imprime_una_linea_por_accion_y_el_resumen()
    probar_replay_en_un_interprete_limpio_termina_con_0_y_sin_importar_pygame()
    probar_bench_en_un_interprete_limpio_termina_con_0_y_sin_importar_pygame()
    probar_importar_main_no_importa_pygame_ni_la_vista()
    probar_si_falta_pygame_el_modo_interactivo_lo_dice_y_sale_con_1()
    probar_una_partida_completa_con_la_vista_real_desde_el_menu_hasta_salir()
    probar_cerrar_la_ventana_en_cualquier_pantalla_termina_el_bucle_sin_error()
    print("OK: todas las pruebas de main.py pasaron")

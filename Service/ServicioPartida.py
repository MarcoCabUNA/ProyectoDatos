"""
ServicioPartida (Servicios, Integrante 3): crea la partida, y entrega su estado y sus resultados.

Es quien CONECTA Datos y Lógica: Lógica no conoce Datos, así que aquí se arma el juego con lo que
da la fuente. Orquesta, no decide reglas del juego ni valida datos (eso es de Lógica y de Datos).

    servicio = ServicioPartida(config)                  # config: ConfiguracionDTO (de LectorArgumentos)
    criptas = servicio.listar_criptas()                 # para que el jugador elija
    contexto = servicio.iniciar_partida("cripta-01", "Ana")
    estado = servicio.estado(contexto)                  # EstadoJuegoDTO para la Vista
    ...                                                 # ServicioAccionJugador ejecuta las acciones
    puntaje = servicio.puntaje(contexto)                # PuntajeDTO al terminar
    reporte = servicio.reporte(contexto)                # solicitudes y caché (§5.1)

Una instancia sirve para UNA partida: la fuente (y su conteo de solicitudes contra el presupuesto de la
cripta) vive lo que vive el servicio. Listar las criptas también cuenta como solicitud (§5.1), por eso
la misma fuente se usa antes y durante la partida.

Orden de arranque (§2.4): el contenido de la sala inicial se carga ANTES de aceptar la primera acción;
motor.iniciar() activa a sus enemigos en el instante 0.

Bitácora de replay: se crea con el encabezado (id y versión de la cripta, versión del catálogo y semilla) y
se anexa cada acción. Con registrar_bitacora=False (al REPRODUCIR un log) no se escribe ninguna.
"""
import random

from Data.BitacoraReplayIO import BitacoraReplayIO
from Data.FuenteOffline import FuenteOffline
from Data.FuenteRed import FuenteRed
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ReporteDatos import generar_reporte
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.PuntajeDTO import PuntajeDTO
from DTO.ReplayDTO import EncabezadoReplayDTO
from DTO.ReporteDatosDTO import ReporteDatosDTO
from Estructuras.BufferCircular import BufferCircular
from Logic.Inventario import Inventario
from Logic.Mazmorra import Mazmorra
from Logic.jugador import Jugador
from Logic.motorJuego import Motor
from Service.ArmadorEstado import ArmadorEstado
from Service.ContextoPartida import ContextoPartida
from Service.SincronizadorUsos import SincronizadorUsos

MENSAJES_EN_PANTALLA = 20       # §4.8: la interfaz muestra los últimos 20 mensajes


class ServicioPartida:

    def __init__(self, config: ConfiguracionDTO, fuente=None, carpeta_cache: str | None = None,
                 carpeta_logs: str = "logs"):
        """
        fuente, carpeta_cache: las pruebas los inyectan (otra fuente, una caché en una carpeta temporal).
        En el programa real se dejan en None: la fuente sale de config.offline y la caché usa su carpeta por defecto.
        """
        self._config = config
        self._fuente = fuente
        self._carpeta_cache = carpeta_cache
        self._carpeta_logs = carpeta_logs
        self._armador = ArmadorEstado()
        self._sincronizador = SincronizadorUsos()

    def fuente(self):
        """La fuente de datos de esta ejecución (se crea la primera vez que se necesita)."""
        if self._fuente is None:
            self._fuente = FuenteOffline() if self._config.offline else FuenteRed()
        return self._fuente

    def listar_criptas(self) -> list:
        """Las criptas disponibles (lista de ResumenCriptaDTO)."""
        return self.fuente().listar_criptas()

    def abrir_datos(self, id_cripta: str):
        """Lo que hace falta de Datos para jugar una cripta: (cripta, resolvedor, esqueleto, contenido).

        Lo comparten iniciar_partida y ServicioGuardado.cargar: ambos necesitan lo mismo de Datos y solo
        cambia cómo se arma el juego (uno nuevo, o uno restaurado de un archivo)."""
        fuente = self.fuente()
        cripta = fuente.obtener_datos_generales(id_cripta)           # también fija el presupuesto de solicitudes
        resolvedor = self._crear_resolvedor(fuente)
        esqueleto = GestorEsqueleto(fuente)
        esqueleto.cargar(cripta)
        contenido = GestorContenido(fuente, esqueleto, resolvedor=resolvedor)
        return cripta, resolvedor, esqueleto, contenido

    def nueva_ruta_de_log(self) -> str:
        """Una ruta libre en la carpeta de logs (BitacoraReplayIO no sobrescribe)."""
        return BitacoraReplayIO.ruta_libre(self._carpeta_logs)

    def iniciar_partida(self, id_cripta: str, nombre_jugador: str, semilla: int | None = None,
                        registrar_bitacora: bool = True) -> ContextoPartida:
        cripta, resolvedor, esqueleto, contenido = self.abrir_datos(id_cripta)
        if semilla is None:
            semilla = self._semilla_nueva()
        mazmorra = Mazmorra(cripta.sala_salida, cripta.llave_salida)
        mazmorra.cargar_esqueleto([esqueleto.obtener_sala(i) for i in esqueleto.ids_salas()])
        jugador = Jugador(cripta)
        inventario = Inventario(cripta.inventario_max)               # la capacidad la define la cripta
        mensajes = BufferCircular(MENSAJES_EN_PANTALLA)
        motor = Motor(semilla, jugador, mazmorra, mensajes.agregar, inventario)

        mazmorra.cargar_contenido(contenido.asegurar_sala(cripta.sala_inicial), resolvedor.ficha)
        motor.iniciar()
        motor.avanzar_hasta_jugador()
        motor.mensaje(f"Comienzas en {mazmorra.sala(cripta.sala_inicial).nombre}")

        contexto = ContextoPartida(cripta=cripta, nombre_jugador=nombre_jugador, semilla=semilla,
                                   fuente=self.fuente(), resolvedor=resolvedor, esqueleto=esqueleto,
                                   contenido=contenido, mazmorra=mazmorra, jugador=jugador,
                                   inventario=inventario, motor=motor, mensajes=mensajes)
        self._sincronizador.sincronizar(contexto)
        if registrar_bitacora:
            bitacora = BitacoraReplayIO(self.nueva_ruta_de_log())
            bitacora.iniciar(EncabezadoReplayDTO(cripta.id, cripta.version, resolvedor.version_catalogo(), semilla))
            contexto.bitacora = bitacora
        return contexto

    def estado(self, contexto: ContextoPartida) -> EstadoJuegoDTO:
        return self._armador.armar_estado(contexto)

    def puntaje(self, contexto: ContextoPartida) -> PuntajeDTO:
        """La fila de la tabla de puntajes (§2.12). Tiene sentido cuando la partida terminó."""
        return PuntajeDTO(nombre=contexto.nombre_jugador, mazmorra=contexto.cripta.id,
                          version=contexto.cripta.version, acciones=contexto.jugador.acciones,
                          enemigos_derrotados=contexto.motor.enemigos_derrotados,
                          tiempo_final=contexto.motor.reloj)

    def reporte(self, contexto: ContextoPartida) -> ReporteDatosDTO:
        """Solicitudes, presupuesto y caché, para mostrar al terminar (§5.1)."""
        return generar_reporte(contexto.fuente, contexto.resolvedor, contexto.contenido, contexto.cripta)

    # ---- interno ----

    def _crear_resolvedor(self, fuente) -> ResolvedorCatalogo:
        tope = self._config.cache_size
        if self._carpeta_cache is None:
            return ResolvedorCatalogo.crear(fuente, tope)
        return ResolvedorCatalogo.crear(fuente, tope, self._carpeta_cache)

    @staticmethod
    def _semilla_nueva() -> int:
        """La semilla se elige AQUÍ, fuera del modelo, y se guarda en la bitácora para poder reproducir."""
        return random.SystemRandom().randrange(1, 2 ** 31)
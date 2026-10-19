"""
ControladorBackend (Interfaz, Integrante 3): la ÚNICA puerta de la Interfaz hacia los Servicios.

Es el orquestador que pide la arquitectura: todo lo que el backend sabe hacer (las operaciones de la capa de
Servicios) llega aquí como un método con nombre propio, y ninguna otra pieza de la Interfaz toca un servicio.
No usa HTTP ni REST: "endpoint" es solo un método de esta clase. Tampoco conoce pygame ni ninguna Vista, por
eso sirve igual para el juego interactivo y para los modos que corren SIN interfaz (--replay y --bench, §6).

    backend = ControladorBackend(config)              # config: ConfiguracionDTO (de LectorArgumentos)
    cripta = backend.criptas()[0]
    estado = backend.iniciar(cripta.id, "Ana")        # EstadoJuegoDTO para la Vista
    estado = backend.mover(N)                         # N, S, E, O de DTO/Direcciones.py
    estado = backend.atacar(estado.enemigos[0].id)
    ...
    puntaje = backend.finalizar()                     # cuando estado.terminado
    reporte = backend.reporte()                       # solicitudes y caché (§5.1)

Qué hace y qué NO hace (reparto de responsabilidades de la arquitectura en capas):
  - VALIDA LA FORMA de lo que recibe (una dirección es 0 a 3, un id no está vacío, el criterio existe...).
    Lo que no tiene forma válida nunca llega a un servicio.
  - NO valida reglas del juego: ¿hay salida? ¿el inventario está lleno? Eso lo responde Lógica y Servicios
    lo traduce a un mensaje, que llega en EstadoJuegoDTO.resultado (la acción no consume tiempo).
  - Guarda UNA referencia opaca a la partida en curso (el ContextoPartida); nunca mira lo que tiene adentro.
  - Una instancia sirve para UNA partida: la fuente de datos cuenta las solicitudes contra el presupuesto de la
    cripta (ServicioPartida). Para otra partida se crea otro ControladorBackend.

Errores: todo fallo esperado (red, guardado, bitácora, puntajes, carga y replay incompatibles) y toda entrada
sin forma válida salen como UN solo tipo, ErrorOperacion, con un mensaje listo para mostrar. Los errores de
programación NO se esconden: siguen rompiendo con su traza.

Los métodos de acciones devuelven el EstadoJuegoDTO resultante; los del inventario, el InventarioDTO.
"""
from DTO.AccionDTO import AccionDTO
from DTO.ConfiguracionDTO import ConfiguracionDTO
from DTO.Direcciones import DIRECCIONES
from DTO.EstadoJuegoDTO import EstadoJuegoDTO
from DTO.InventarioDTO import InventarioDTO
from DTO.PuntajeDTO import PuntajeDTO
from DTO.ReporteDatosDTO import ReporteDatosDTO
from DTO.ResultadoBenchDTO import ResultadoBenchDTO
from DTO.ResultadoReplayDTO import ResultadoReplayDTO
from Service.ErroresServicio import ERRORES_ESPERADOS
from Service.ServicioAccionJugador import ServicioAccionJugador
from Service.ServicioBench import ServicioBench
from Service.ServicioGuardado import ServicioGuardado
from Service.ServicioInventario import ServicioInventario
from Service.ServicioPartida import ServicioPartida
from Service.ServicioPuntajes import ServicioPuntajes
from Service.ServicioReplay import ServicioReplay

# Criterios que existen. Son tuplas (no dict, §7) y públicas: la Interfaz las recorre para pasar de uno al siguiente.
CRITERIOS_INVENTARIO = (None, "peso", "valor", "nombre")  # None = orden real del inventario
CRITERIOS_PUNTAJES = ("enemigos", "tiempo", "acciones", "nombre")
LARGO_MAXIMO_NOMBRE = 16


class ErrorOperacion(ValueError):
    """La operación no se pudo hacer. El mensaje está listo para mostrarse al jugador."""


class ControladorBackend:

    def __init__(self, config: ConfiguracionDTO, servicio_partida: ServicioPartida | None = None,
                 servicio_puntajes: ServicioPuntajes | None = None, servicio_bench: ServicioBench | None = None):
        """Los tres servicios opcionales los inyectan las pruebas (otra carpeta de caché, otra tabla de puntajes...).
        En el programa real se dejan en None."""
        self._partida = servicio_partida if servicio_partida is not None else ServicioPartida(config)
        self._puntajes = servicio_puntajes if servicio_puntajes is not None else ServicioPuntajes()
        self._bench = servicio_bench if servicio_bench is not None else ServicioBench()
        self._acciones = ServicioAccionJugador()
        self._inventarios = ServicioInventario()
        self._guardado = ServicioGuardado(self._partida)
        self._replay = ServicioReplay(self._partida)
        self._contexto = None  # la partida en curso (opaca); None si no hay
        self._terminada = False
        self._puntaje_registrado = False

    # ================================================================== partida
    def criptas(self) -> list:
        """Las criptas disponibles (ResumenCriptaDTO). Cuenta como una solicitud de red (§5.1)."""
        return self._llamar(self._partida.listar_criptas)

    def iniciar(self, id_cripta: str, nombre_jugador: str) -> EstadoJuegoDTO:
        id_cripta = self._texto(id_cripta, "Falta indicar la cripta.")
        nombre = self._nombre(nombre_jugador)
        return self._empezar(self._llamar(self._partida.iniciar_partida, id_cripta, nombre))

    def cargar(self, ruta: str, nombre_jugador: str) -> EstadoJuegoDTO:
        """Continúa una partida guardada. Si falla, la partida que estaba en curso (si había) no se toca."""
        ruta = self._texto(ruta, "Falta indicar el archivo de la partida.")
        nombre = self._nombre(nombre_jugador)
        return self._empezar(self._llamar(self._guardado.cargar, ruta, nombre))

    def guardar(self, ruta: str) -> int:
        """Guarda la partida en curso. Devuelve los bytes escritos."""
        ruta = self._texto(ruta, "Falta indicar dónde guardar la partida.")
        return self._llamar(self._guardado.guardar, self._activa(), ruta)

    def hay_partida(self) -> bool:
        return self._contexto is not None

    def estado(self) -> EstadoJuegoDTO:
        return self._llamar(self._partida.estado, self._activa())

    def finalizar(self) -> PuntajeDTO:
        """Registra en la tabla local el puntaje de la partida TERMINADA (una sola vez, aunque se llame de nuevo)
        y lo devuelve (§2.12)."""
        contexto = self._activa()
        if not self._terminada:
            raise ErrorOperacion("La partida todavía no ha terminado.")
        puntaje = self._llamar(self._partida.puntaje, contexto)
        if not self._puntaje_registrado:
            self._llamar(self._puntajes.registrar, puntaje)
            self._puntaje_registrado = True
        return puntaje

    def reporte(self) -> ReporteDatosDTO:
        """Solicitudes hechas, presupuesto, aciertos y fallos de caché (§5.1)."""
        return self._llamar(self._partida.reporte, self._activa())

    def tabla_puntajes(self, criterio: str = "enemigos") -> list[PuntajeDTO]:
        criterio = self._criterio(criterio, CRITERIOS_PUNTAJES, "Criterio de puntajes desconocido")
        return self._llamar(self._puntajes.tabla, criterio)

    # ================================================================== acciones del jugador
    def mover(self, direccion: int) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("mover", direccion=self._direccion(direccion)))

    def abrir(self, direccion: int) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("abrir", direccion=self._direccion(direccion)))

    def atacar(self, id_enemigo: str) -> EstadoJuegoDTO:
        return self._ejecutar(
            AccionDTO("atacar", objetivo=self._texto(id_enemigo, "Falta indicar a qué enemigo atacar.")))

    def esperar(self) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("esperar"))

    def recoger(self, id_objeto: str) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("recoger", objeto=self._texto(id_objeto, "Falta indicar el objeto.")))

    def soltar(self, id_objeto: str) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("soltar", objeto=self._texto(id_objeto, "Falta indicar el objeto.")))

    def equipar(self, id_objeto: str) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("equipar", objeto=self._texto(id_objeto, "Falta indicar el objeto.")))

    def usar(self, id_objeto: str) -> EstadoJuegoDTO:
        return self._ejecutar(AccionDTO("usar", objeto=self._texto(id_objeto, "Falta indicar el objeto.")))

    def retroceder(self) -> EstadoJuegoDTO:
        """Usa un pergamino de retroceso (§2.11)."""
        return self._ejecutar(AccionDTO("retroceder"))

    # ================================================================== inventario (la vista; no consume tiempo)
    def inventario(self) -> InventarioDTO:
        return self._llamar(self._inventarios.inventario, self._activa())

    def inventario_siguiente(self) -> InventarioDTO:
        return self._llamar(self._inventarios.siguiente, self._activa())

    def inventario_anterior(self) -> InventarioDTO:
        return self._llamar(self._inventarios.anterior, self._activa())

    def inventario_ordenar(self, criterio: str | None) -> InventarioDTO:
        """Cambia la vista: None (orden real), 'peso', 'valor' o 'nombre'. El orden real no cambia."""
        criterio = self._criterio(criterio, CRITERIOS_INVENTARIO, "Criterio de inventario desconocido")
        return self._llamar(self._inventarios.ordenar, self._activa(), criterio)

    # ================================================================== modos sin interfaz (§6)
    def reproducir(self, ruta: str, al_avanzar=None) -> ResultadoReplayDTO:
        """--replay: reproduce una partida completa desde su log. al_avanzar(numero, accion, estado), opcional."""
        ruta = self._texto(ruta, "Falta indicar el archivo del log.")
        return self._llamar(self._replay.reproducir, ruta, al_avanzar)

    def medir(self, al_avanzar=None) -> list[ResultadoBenchDTO]:
        """--bench: corre las mediciones. al_avanzar(numero, total), opcional."""
        return self._llamar(self._bench.ejecutar, al_avanzar)

    @staticmethod
    def tabla_mediciones(resultados: list[ResultadoBenchDTO]) -> str:
        return ServicioBench.tabla_texto(resultados)

    # ================================================================== interno
    def _ejecutar(self, accion: AccionDTO) -> EstadoJuegoDTO:
        estado = self._llamar(self._acciones.ejecutar, self._activa(), accion)
        self._terminada = estado.terminado
        return estado

    def _empezar(self, contexto) -> EstadoJuegoDTO:
        """La partida nueva (o cargada) pasa a ser la vigente. Solo se llega aquí si el servicio no falló."""
        estado = self._llamar(self._partida.estado, contexto)
        self._contexto = contexto
        self._terminada = estado.terminado
        self._puntaje_registrado = False
        return estado

    def _activa(self):
        if self._contexto is None:
            raise ErrorOperacion("No hay una partida en curso.")
        return self._contexto

    @staticmethod
    def _llamar(servicio, *argumentos):
        """Toda llamada a un servicio pasa por aquí: los fallos esperados salen como ErrorOperacion."""
        try:
            return servicio(*argumentos)
        except ERRORES_ESPERADOS as error:
            raise ErrorOperacion(str(error)) from error

    # ---- validación de FORMA ----
    @staticmethod
    def _direccion(direccion) -> int:
        if not isinstance(direccion, int) or isinstance(direccion, bool) or not 0 <= direccion < len(DIRECCIONES):
            raise ErrorOperacion("Dirección inválida: use N, S, E u O.")
        return direccion

    @staticmethod
    def _texto(valor, mensaje: str) -> str:
        if not isinstance(valor, str) or valor.strip() == "":
            raise ErrorOperacion(mensaje)
        return valor.strip()

    @staticmethod
    def _nombre(valor) -> str:
        if not isinstance(valor, str) or valor.strip() == "":
            raise ErrorOperacion("Escribe un nombre para el jugador.")
        nombre = valor.strip()
        if len(nombre) > LARGO_MAXIMO_NOMBRE or not nombre.isprintable():
            raise ErrorOperacion(f"El nombre debe tener hasta {LARGO_MAXIMO_NOMBRE} caracteres imprimibles.")
        return nombre

    @staticmethod
    def _criterio(criterio, validos: tuple, mensaje: str):
        for valido in validos:
            if criterio == valido:
                return criterio
        raise ErrorOperacion(f"{mensaje}: {criterio!r}.")
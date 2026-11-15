"""
ServicioResolubilidad (Integrante 2, feature 003): verifica la resolubilidad de una cripta y, al iniciar una partida
nueva, decide si se inicia (research R8; FR-301, FR-311 a FR-315, FR-320, FR-323).

    servicio = ServicioResolubilidad(partida)                   # partida: ServicioPartida de esta ejecución
    reporte = servicio.verificar("cripta-01")                   # --verificar: nunca lanza por datos ni por red
    contexto = servicio.iniciar_partida_nueva("cripta-01", "Ana", forzar)   # contexto.resolubilidad = reporte

Orquesta y no valida: Data valida (FR-321, FR-323) y Lógica decide (VerificadorResolubilidad). No mira la bandera
--offline de la configuración: la fuente y el almacén de llaves llegan ya elegidos por ServicioPartida.fuente()
(Principio I).
La verificación ocurre antes de crear el motor: no descarga contenido, no consume el generador aleatorio y no registra
nada en el historial, la línea de tiempo ni partida.log (R9).
Cargar una partida y --replay NO pasan por aquí (FR-301): usan ServicioPartida directamente.
Este módulo no importa ErroresServicio (es ErroresServicio quien importa ErrorPartidaNoIniciada): sin import circular.
"""
from Data.ClienteHttp import ErrorRed
from Data.GestorEsqueleto import GestorEsqueleto
from Data.GestorLlaves import GestorLlaves
from DTO.CriptaDTO import CriptaDTO
from DTO.ReporteResolubilidadDTO import NO_CONCLUYO, NO_RESOLUBLE, RESOLUBLE, ReporteResolubilidadDTO
from Logic import VerificadorResolubilidad
from Service.ContextoPartida import ContextoPartida
from Service.ServicioPartida import ServicioPartida


class ErrorPartidaNoIniciada(ValueError):
    """La partida nueva no se inició porque la cripta no es resoluble o la verificación no concluyó (FR-311).
    reporte: el reporte completo, para mostrarlo. El mensaje es corto, para el jugador."""

    def __init__(self, reporte: ReporteResolubilidadDTO):
        self.reporte = reporte
        if reporte.veredicto == NO_RESOLUBLE:
            texto = (f"La cripta {reporte.id_cripta} no es resoluble: la partida no se inició "
                     f"(use --forzar para jugarla de todas formas).")
        else:
            texto = (f"No se pudo verificar si la cripta {reporte.id_cripta} es resoluble: la partida no se inició "
                     f"(use --forzar para jugarla de todas formas).")
        super().__init__(texto)


class ServicioResolubilidad:
    """Verificar sin jugar (--verificar) e iniciar una partida nueva pasando por la verificación."""

    def __init__(self, partida: ServicioPartida):
        self._partida = partida

    def verificar(self, id_cripta: str) -> ReporteResolubilidadDTO:
        """
        Solo datos generales, esqueleto y llaves (sin el resolvedor del catálogo). Cualquier ErrorRed (incluidos el
        404 de una cripta inexistente, el «falta el archivo» del paquete, FR-321 y FR-323) da NO_CONCLUYO con mensaje.
        """
        fuente = self._partida.fuente()
        try:
            cripta = fuente.obtener_datos_generales(id_cripta)
        except ErrorRed as error:
            return ReporteResolubilidadDTO(id_cripta, NO_CONCLUYO, mensaje=str(error))
        try:
            esqueleto = GestorEsqueleto(fuente)
            esqueleto.cargar(cripta)
        except ErrorRed as error:
            return _no_concluyo(cripta, error)
        return self._verificar_cargada(cripta, esqueleto)

    def iniciar_partida_nueva(self, id_cripta: str, nombre: str, forzar: bool,
                              semilla: int | None = None) -> ContextoPartida:
        """
        R8: 1) abrir_datos (un error aquí se propaga: no inicia ni con forzar); 2) llaves y 3) veredicto;
        4) sin forzar y no RESOLUBLE: ErrorPartidaNoIniciada, sin motor, log ni guardado; 5) si no, inicia con los
        mismos datos y deja el reporte en contexto.resolubilidad.
        """
        datos = self._partida.abrir_datos(id_cripta)
        cripta, _, esqueleto, _ = datos
        reporte = self._verificar_cargada(cripta, esqueleto)
        if reporte.veredicto != RESOLUBLE and not forzar:
            raise ErrorPartidaNoIniciada(reporte)
        contexto = self._partida.iniciar_partida(id_cripta, nombre, semilla, datos=datos)
        contexto.resolubilidad = reporte
        return contexto

    # ------------------------------------------------------------ interno
    def _verificar_cargada(self, cripta: CriptaDTO, esqueleto: GestorEsqueleto) -> ReporteResolubilidadDTO:
        """Paso de llaves (un ErrorRed o ErrorDatos da NO_CONCLUYO, FR-320, FR-321) y veredicto de Lógica."""
        try:
            ubicaciones = GestorLlaves(self._partida.fuente(), self._partida.almacen_llaves()).obtener(cripta, esqueleto)
        except ErrorRed as error:
            return _no_concluyo(cripta, error)
        salas = [esqueleto.obtener_sala(i) for i in esqueleto.ids_salas()]
        return VerificadorResolubilidad.verificar(cripta, salas, ubicaciones)


def _no_concluyo(cripta: CriptaDTO, error: ErrorRed) -> ReporteResolubilidadDTO:
    """Reporte sin veredicto (FR-323): solo el id, la versión, la llave de salida y el error con contexto."""
    return ReporteResolubilidadDTO(cripta.id, NO_CONCLUYO, cripta.version, cripta.llave_salida, mensaje=str(error))

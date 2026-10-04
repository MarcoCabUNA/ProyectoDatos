"""
Capa de Datos — cliente HTTP de bajo nivel para el API de Cripta (Integrante 2).

Responsabilidades (solo infraestructura, ninguna regla del juego):
  - enviar GET con el encabezado X-Cripta-Client-Id (el mismo toda la ejecución);
  - manejar HTTP 429 esperando 'reintentar_en' segundos REALES y reintentando;
  - contar cada solicitud enviada (reintentos incluidos) contra el presupuesto;
  - convertir cualquier fallo en ErrorRed con contexto, nunca una excepción
    cruda de requests.

No conoce DTOs: devuelve el JSON decodificado. FuenteRed (paso 2) lo traduce
a DTOs, de modo que la capa de Lógica nunca vea un dict de respuesta.json().
"""
import time
from urllib.parse import quote

import requests


class ErrorRed(Exception):
    """Fallo de red o de protocolo, con la operación que lo produjo."""

    def __init__(self, operacion: str, detalle: str, codigo: int | None = None):
        self.operacion = operacion
        self.detalle = detalle
        self.codigo = codigo
        texto = f"Falló '{operacion}': {detalle}"
        if codigo is not None:
            texto += f" (HTTP {codigo})"
        super().__init__(texto)


class PresupuestoAgotadoError(ErrorRed):
    """Enviar otra solicitud superaría presupuesto_solicitudes de la cripta."""


class ClienteHttp:
    ESPERA_POR_DEFECTO = 1  # segundos, si un 429 llega sin 'reintentar_en' legible

    def __init__(self, url_base: str, client_id: str, timeout: float = 10.0,
                 max_reintentos_429: int = 5, sesion=None, esperar=time.sleep):
        """
        sesion y esperar se inyectan para poder probar sin red y sin dormir.
        En el programa real se dejan los valores por defecto.
        """
        if not client_id:
            raise ValueError("client_id vacío: genérelo una vez con generar_client_id()")
        self._url_base = url_base.rstrip("/")
        self._client_id = client_id
        self._timeout = timeout
        self._max_reintentos_429 = max_reintentos_429
        self._sesion = sesion if sesion is not None else requests.Session()
        self._esperar = esperar

        self._presupuesto: int | None = None  # se conoce al leer los datos generales
        self._solicitudes = 0
        self._respuestas_429 = 0

    # ------------------------------------------------------------ presupuesto
    def fijar_presupuesto(self, presupuesto: int) -> None:
        if presupuesto < 0:
            raise ValueError("presupuesto negativo")
        self._presupuesto = presupuesto

    def reiniciar_conteo(self) -> None:
        """Llamar al empezar una partida nueva dentro de la misma ejecución."""
        self._solicitudes = 0
        self._respuestas_429 = 0
        self._presupuesto = None

    @property
    def solicitudes_realizadas(self) -> int:
        return self._solicitudes

    @property
    def presupuesto(self) -> int | None:
        return self._presupuesto

    @property
    def respuestas_429(self) -> int:
        return self._respuestas_429

    def solicitudes_restantes(self) -> int | None:
        if self._presupuesto is None:
            return None
        return max(0, self._presupuesto - self._solicitudes)

    # ------------------------------------------------------------ operación
    def get_json(self, ruta: str, operacion: str, parametros=()):
        """
        GET a url_base + ruta. 'parametros' es una secuencia de pares
        (nombre, valor), p. ej. (("salas", "1,2,3"),).
        Devuelve el JSON decodificado o lanza ErrorRed.
        """
        url = self._construir_url(ruta, parametros)
        reintentos = 0
        while True:
            self._verificar_presupuesto(operacion)
            # Se cuenta ANTES de enviar: si luego hay timeout, la solicitud
            # pudo haber llegado al servidor. Contar de más es lo seguro.
            self._solicitudes += 1
            respuesta = self._enviar(url, operacion)

            if respuesta.status_code == 200:
                return self._decodificar(respuesta, operacion)

            if respuesta.status_code == 429:
                self._respuestas_429 += 1
                if reintentos >= self._max_reintentos_429:
                    raise ErrorRed(operacion,
                                   f"límite de frecuencia excedido {reintentos + 1} veces seguidas",
                                   429)
                reintentos += 1
                self._esperar(self._segundos_espera(respuesta))  # tiempo REAL, no el reloj virtual
                continue

            raise ErrorRed(operacion, self._mensaje_error(respuesta), respuesta.status_code)

    # ------------------------------------------------------------ auxiliares
    def _verificar_presupuesto(self, operacion: str) -> None:
        if self._presupuesto is not None and self._solicitudes >= self._presupuesto:
            raise PresupuestoAgotadoError(
                operacion,
                f"se alcanzó el presupuesto de {self._presupuesto} solicitudes")

    def _construir_url(self, ruta: str, parametros) -> str:
        url = self._url_base + "/" + ruta.lstrip("/")
        partes = [f"{quote(str(n))}={quote(str(v), safe=',')}" for n, v in parametros]
        if partes:
            url += "?" + "&".join(partes)
        return url

    def _enviar(self, url: str, operacion: str):
        # requests exige un dict para los encabezados: es transporte HTTP,
        # no una estructura que resuelva un problema evaluado de §4.
        encabezados = {"X-Cripta-Client-Id": self._client_id}
        try:
            return self._sesion.get(url, headers=encabezados, timeout=self._timeout)
        except requests.Timeout as e:
            raise ErrorRed(operacion, f"el servidor no respondió en {self._timeout} s") from e
        except requests.ConnectionError as e:
            raise ErrorRed(operacion, f"no se pudo conectar al servidor ({e})") from e
        except requests.RequestException as e:
            raise ErrorRed(operacion, f"error de red inesperado ({e})") from e

    @staticmethod
    def _decodificar(respuesta, operacion: str):
        try:
            return respuesta.json()
        except ValueError as e:  # requests.JSONDecodeError hereda de ValueError
            raise ErrorRed(operacion, "la respuesta 200 no es JSON válido") from e

    def _segundos_espera(self, respuesta) -> int:
        try:
            cuerpo = respuesta.json()
            segundos = cuerpo.get("reintentar_en") if isinstance(cuerpo, dict) else None
            if isinstance(segundos, int) and segundos >= 1:
                return segundos
        except ValueError:
            pass
        cabecera = respuesta.headers.get("Retry-After")
        if cabecera is not None and cabecera.isdigit() and int(cabecera) >= 1:
            return int(cabecera)
        return self.ESPERA_POR_DEFECTO

    @staticmethod
    def _mensaje_error(respuesta) -> str:
        try:
            cuerpo = respuesta.json()
            if isinstance(cuerpo, dict) and isinstance(cuerpo.get("error"), str):
                return cuerpo["error"]
        except ValueError:
            pass
        texto = (respuesta.text or "").strip()
        return texto[:200] if texto else "respuesta sin detalle"
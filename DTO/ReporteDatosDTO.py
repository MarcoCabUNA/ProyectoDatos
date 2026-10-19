"""
ReporteDatosDTO (Integrante 2): lo que la capa de Datos reporta al final de la partida.

El enunciado (§6.1) pide reportar al final: solicitudes hechas, presupuesto, aciertos y fallos de
caché. Los demás campos son para --bench y el Documento de Decisiones (evidencia empírica de la
precarga, la caché en disco y la resolución del catálogo).

Viaja por las capas como cualquier DTO: Servicios lo recibe de Datos y la Vista lo muestra, sin que
ninguna de las dos conozca las clases de Datos que tienen los contadores.
Regla de los DTOs: solo transportan datos (los porcentajes o el formato los decide la Vista).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReporteDatosDTO:
    # --- lo que pide el enunciado (§6.1)
    solicitudes_realizadas: int        # todas las solicitudes HTTP, incluidos reintentos tras un 429
    presupuesto: int | None            # presupuesto_solicitudes de la cripta (None si no se conoce)
    aciertos_cache: int                # fichas encontradas en memoria
    fallos_cache: int                  # fichas que no estaban en memoria (se leyeron de disco o de la red)
    # --- detalle para --bench
    lecturas_disco: int = 0            # fichas recuperadas del disco en vez de la red (§4.4)
    fichas_descargadas: int = 0        # fichas que sí hubo que pedir a la red
    solicitudes_catalogo: int = 0      # lotes enviados a /catalogo (hasta 10 ids cada uno)
    lotes_contenido: int = 0           # lotes enviados a /contenido (hasta 10 salas cada uno)
    salas_pedidas: int = 0             # salas cuyo contenido se pidió
    offline: bool = False              # True en --offline: las lecturas locales no cuentan como solicitudes

    def a_diccionario(self) -> dict:
        """Para guardar los resultados de --bench en un archivo (JSON)."""
        return {
            "solicitudes_realizadas": self.solicitudes_realizadas,
            "presupuesto": self.presupuesto,
            "aciertos_cache": self.aciertos_cache,
            "fallos_cache": self.fallos_cache,
            "lecturas_disco": self.lecturas_disco,
            "fichas_descargadas": self.fichas_descargadas,
            "solicitudes_catalogo": self.solicitudes_catalogo,
            "lotes_contenido": self.lotes_contenido,
            "salas_pedidas": self.salas_pedidas,
            "offline": self.offline,
        }

    @classmethod
    def desde_diccionario(cls, d: dict) -> "ReporteDatosDTO":
        return cls(
            solicitudes_realizadas=d["solicitudes_realizadas"],
            presupuesto=d.get("presupuesto"),
            aciertos_cache=d["aciertos_cache"],
            fallos_cache=d["fallos_cache"],
            lecturas_disco=d.get("lecturas_disco", 0),
            fichas_descargadas=d.get("fichas_descargadas", 0),
            solicitudes_catalogo=d.get("solicitudes_catalogo", 0),
            lotes_contenido=d.get("lotes_contenido", 0),
            salas_pedidas=d.get("salas_pedidas", 0),
            offline=d.get("offline", False),
        )
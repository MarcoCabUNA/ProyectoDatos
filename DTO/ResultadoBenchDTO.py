"""
ResultadoBenchDTO (Integrante 2, acordado con el equipo): una fila del reporte de --bench (§5.3).

Cada integrante devuelve una lista de estos desde su archivo de mediciones (Service/BenchDatos.py,
Logic/BenchLogica.py, Service/BenchInventario.py) y ServicioBench los junta.

    subsistema  qué se mide: "caché", "guardado", "agenda de eventos", "inventario", ...
    caso        la variante: "búsqueda binaria", "búsqueda lineal (descartada)", "binario", "JSON", ...
    tamano      el tamaño de la carga sintética (fichas, salas, eventos, objetos, acciones...)
    mejor_ms    el menor tiempo de N repeticiones, en milisegundos (el menos afectado por otros programas)
    mediana_ms  la mediana de esas N repeticiones, en milisegundos
    nota        lo que hace falta para leer la fila (qué se cronometró, cuántas veces, tamaños, conteos)

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoBenchDTO:
    subsistema: str
    caso: str
    tamano: int
    mejor_ms: float
    mediana_ms: float
    nota: str = ""
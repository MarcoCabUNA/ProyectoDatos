"""
BenchLogica (Integrante 1, Marco): mediciones de Lógica para --bench (§5.2 y §5.3).

Lo que falta medir aquí (lo pide el enunciado):
  - agenda de eventos (ColaEventos): programar y sacar el siguiente con cientos o miles de eventos;
  - el ciclo completo de eventos entre dos decisiones del jugador, que debe tardar menos de 20 ms (§5.2).

Cómo agregar una medición (ver Service/BenchDatos.py como ejemplo):
    from DTO.ResultadoBenchDTO import ResultadoBenchDTO
    from Service.Cronometro import medir as cronometrar
    mejor, mediana = cronometrar(funcion, repeticiones)               # o con preparar=... si cambia el estado
    resultados.append(ResultadoBenchDTO("agenda de eventos", "programar", n, mejor, mediana, "nota"))
Usar cargas sintéticas (nada de una cripta específica) y devolver la lista desde medir().
"""
from DTO.ResultadoBenchDTO import ResultadoBenchDTO


def medir() -> list[ResultadoBenchDTO]:
    """Mediciones de Lógica. Pendiente (Marco)."""
    return []
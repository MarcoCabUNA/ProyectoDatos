"""
BenchInventario (Integrante 3, Kristel): mediciones de inventario, historial y ordenamiento para --bench (§5.3).

Lo que falta medir aquí (lo pide el enunciado):
  - inventario: recoger, soltar, equipar y recorrer (Logic/Inventario.py);
  - historial de retroceso: registrar y deshacer (Logic/HistorialRetroceso.py);
  - ordenamientos: inserción contra mezcla con distintos tamaños, datos casi ordenados y comparaciones
    costosas (Estructuras/Ordenador.py dice que --bench debe reproducir esas mediciones, §4.9).

Cómo agregar una medición (ver Service/BenchDatos.py como ejemplo):
    from DTO.ResultadoBenchDTO import ResultadoBenchDTO
    from Service.Cronometro import medir as cronometrar
    mejor, mediana = cronometrar(funcion, repeticiones)               # o con preparar=... si cambia el estado
    resultados.append(ResultadoBenchDTO("ordenamiento", "inserción", n, mejor, mediana, "casi ordenados"))
Usar cargas sintéticas y devolver la lista desde medir().
"""
from DTO.ResultadoBenchDTO import ResultadoBenchDTO


def medir() -> list[ResultadoBenchDTO]:
    """Mediciones de inventario, historial y ordenamiento. Pendiente (Kristel)."""
    return []
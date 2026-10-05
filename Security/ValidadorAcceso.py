"""
MSI — seguridad y control de acceso (Integrante 2).

Por ahora solo genera el X-Cripta-Client-Id. validar_version() se agrega
en el paso de caché/replay, cuando exista algo persistido que validar.
"""
import uuid

# Se genera una sola vez por ejecución del programa (requisito del enunciado).
_client_id: str | None = None


def generar_client_id() -> str:
    """Devuelve el UUID de esta ejecución. Llamadas repetidas devuelven el mismo valor."""
    global _client_id
    if _client_id is None:
        _client_id = str(uuid.uuid4())
    return _client_id
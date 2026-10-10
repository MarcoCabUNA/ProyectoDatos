"""
MSI — seguridad y control de acceso (Integrante 2).

- generar_client_id(): el X-Cripta-Client-Id, uno solo por ejecución.
- validar_version(): antes de aceptar algo persistido (caché en disco, partida guardada,
  --replay), para no continuar en silencio con datos de otra versión (Apéndice B).
- es_nombre_seguro(): un id que viene de afuera (API, archivos) solo se usa como nombre de
  archivo o carpeta si no puede salirse de la carpeta prevista (por ejemplo "../hack").
"""
import uuid

# Se genera una sola vez por ejecución del programa (requisito del enunciado).
_client_id: str | None = None

# Nombres que Windows reserva para dispositivos: "con.json" o "nul.json" no se pueden crear.
_RESERVADOS_WINDOWS = ["con", "prn", "aux", "nul",
                       "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
                       "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"]
_LARGO_MAXIMO = 100


def generar_client_id() -> str:
    """Devuelve el UUID de esta ejecución. Llamadas repetidas devuelven el mismo valor."""
    global _client_id
    if _client_id is None:
        _client_id = str(uuid.uuid4())
    return _client_id


def validar_version(version_local: str | None, version_remota: str | None) -> bool:
    """
    True solo si las dos versiones existen y son iguales. Si alguna falta (None o vacía) se
    considera que NO coinciden: ante la duda, no se confía en lo persistido.
    """
    if not version_local or not version_remota:
        return False
    return version_local == version_remota


def es_nombre_seguro(texto: str) -> bool:
    """
    ¿Se puede usar como nombre de archivo o carpeta? Solo letras y números ASCII, '-' y '_',
    hasta 100 caracteres y sin los nombres reservados de Windows. Así no puede contener
    '/', '\\' ni '..' para salirse de la carpeta.
    """
    if not isinstance(texto, str) or texto == "" or len(texto) > _LARGO_MAXIMO:
        return False
    for caracter in texto:
        es_letra = ("a" <= caracter <= "z") or ("A" <= caracter <= "Z")
        es_digito = "0" <= caracter <= "9"
        if not (es_letra or es_digito or caracter in "-_"):
            return False
    minusculas = texto.lower()
    for reservado in _RESERVADOS_WINDOWS:
        if minusculas == reservado:
            return False
    return True
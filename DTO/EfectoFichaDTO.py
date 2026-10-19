"""
EfectoFichaDTO: un efecto declarado en una ficha de catálogo (enunciado §2.10).

El API publicado todavía no trae campos de veneno ni de regeneración, pero la cripta de la revisión
puede traerlos (§9). Como el Swagger no fija su forma, la lectura es TOLERANTE: acepta las formas
razonables, ignora un valor inválido en vez de caerse y conserva lo que no entiende (campos_extra),
para que la caché en disco lo vuelva a escribir tal cual.

Formas aceptadas (las claves se comparan sin tildes ni mayúsculas, y "ñ" = "n"):
  enemigo   "veneno": 2                       al golpear al jugador lo envenena con 2 por pulso
            "veneno": {"daño": 2, "duracion": 400}
            "daño_veneno": 2
            "regeneracion": 3                 recupera 3 de vida cada 200 unidades
            "regeneracion": {"cantidad": 3}
            "modificador_velocidad": -30 + "duracion": 300    al golpear cambia la velocidad del jugador
  trampa    "efecto": "veneno"                el daño de la trampa pasa a ser el daño por pulso del veneno
            "efecto": "veneno" + "valor": 2   veneno de 2 por pulso; "daño" sigue siendo daño inmediato
            "veneno": 2 / "modificador_velocidad" + "duracion"   igual que en el enemigo
  ambas     "efectos": [{"tipo": "veneno", "daño": 2}, {"tipo": "velocidad", "valor": -30, "duracion": 300}]

Números: enteros, decimales exactos (2.0) o texto ("2"). Un valor que no se puede leer, o cero, hace que ese
efecto se ignore. Si un tipo se declara dos veces, gana la primera aparición: primero la lista
"efectos" y después las claves sueltas, en el orden de arriba (determinista).

Un tipo que no está en TIPOS_CONOCIDOS se conserva con su nombre: Lógica no lo simula (sus reglas no
están en el enunciado), pero avisa con un mensaje al activarse en lugar de perderlo en silencio.
"""
from dataclasses import dataclass

VENENO = "veneno"
VELOCIDAD = "velocidad"
REGENERACION = "regeneracion"
TIPOS_CONOCIDOS = [VENENO, VELOCIDAD, REGENERACION]

_ALIAS_TIPO = [("veneno", VENENO), ("envenenar", VENENO), ("envenenamiento", VENENO),
               ("velocidad", VELOCIDAD), ("modificador_velocidad", VELOCIDAD), ("lentitud", VELOCIDAD),
               ("regeneracion", REGENERACION), ("regenerar", REGENERACION), ("regenera", REGENERACION)]
_CLAVES_VALOR = ["valor", "dano", "danio", "cantidad", "cura", "modificador_velocidad", "modificador"]
_CLAVES_TIPO = ["tipo", "efecto", "nombre", "clase"]


@dataclass(frozen=True)
class EfectoFichaDTO:
    tipo: str                    # uno de TIPOS_CONOCIDOS, o el nombre normalizado de uno desconocido
    valor: int                   # daño por pulso, vida por pulso o modificador de velocidad
    duracion: int | None = None  # None: la del enunciado (veneno 400); velocidad la exige


def normalizar(texto) -> str:
    """'Regeneración' -> 'regeneracion', 'Daño' -> 'dano'. Solo para comparar claves y tipos."""
    if not isinstance(texto, str):
        return ""
    resultado = []
    for c in texto.strip().lower():
        posicion = "áéíóúüñ".find(c)
        resultado.append("aeiouun"[posicion] if posicion >= 0 else c)
    return "".join(resultado).replace(" ", "_").replace("-", "_")


def entero(valor) -> int | None:
    """int, float exacto o texto con un entero -> int. bool, None u otra cosa -> None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        cuerpo = texto[1:] if texto[:1] in ("-", "+") else texto
        if cuerpo.isdigit():
            return int(texto)
    return None


def buscar(d: dict, *claves):
    """El valor de la primera clave de 'claves' presente en el JSON 'd' (comparando normalizado), o None."""
    if not isinstance(d, dict):
        return None
    for clave in claves:
        for real in d:
            if normalizar(real) == clave:
                return d[real]
    return None


def campos_extra(d: dict, conocidos: list[str]) -> tuple:
    """Pares (clave, valor) del JSON que el DTO no tiene como campo propio, en el orden en que llegaron."""
    extra = []
    for clave in d:
        es_conocido = False
        for c in conocidos:
            if clave == c:
                es_conocido = True
                break
        if not es_conocido:
            extra.append((clave, d[clave]))
    return tuple(extra)


def leer_efectos(d: dict, dano_de_la_ficha: int | None = None) -> tuple:
    """
    Los efectos que declara la ficha 'd' (JSON del catálogo), como tupla de EfectoFichaDTO.
    dano_de_la_ficha: solo trampas; con "efecto": "veneno" y sin "valor", es el daño por pulso.
    """
    efectos: list[EfectoFichaDTO] = []
    lista = buscar(d, "efectos")
    if isinstance(lista, list):
        for elemento in lista:
            if isinstance(elemento, dict):
                _agregar(efectos, buscar(elemento, *_CLAVES_TIPO), buscar(elemento, *_CLAVES_VALOR),
                         buscar(elemento, "duracion"))
            elif isinstance(elemento, str):
                _agregar(efectos, elemento, dano_de_la_ficha, None)

    efecto = buscar(d, "efecto")
    if isinstance(efecto, str):
        valor = buscar(d, "valor")
        _agregar(efectos, efecto, dano_de_la_ficha if valor is None else valor, buscar(d, "duracion"))

    _agregar_anidado(efectos, VENENO, buscar(d, "veneno"))
    _agregar(efectos, VENENO, buscar(d, "dano_veneno", "danio_veneno"), buscar(d, "duracion_veneno"))
    _agregar_anidado(efectos, REGENERACION, buscar(d, "regeneracion", "regenera"))
    _agregar(efectos, VELOCIDAD, buscar(d, "modificador_velocidad"), buscar(d, "duracion"))
    return tuple(efectos)


def dano_inmediato_de_trampa(d: dict, dano: int) -> int:
    """
    Con "efecto": "<otro efecto>" y sin "valor", el "daño" de la trampa es el daño por pulso de ese efecto
    (ver leer_efectos) y la trampa no hace daño inmediato. En cualquier otro caso, "daño" es inmediato.
    """
    efecto = buscar(d, "efecto")
    if isinstance(efecto, str) and not _es_dano_directo(_tipo_canonico(efecto)) and buscar(d, "valor") is None:
        return 0
    return dano


def _agregar_anidado(efectos: list, tipo: str, valor) -> None:
    """"veneno": 2  o  "veneno": {"daño": 2, "duracion": 400}."""
    if isinstance(valor, dict):
        _agregar(efectos, tipo, buscar(valor, *_CLAVES_VALOR), buscar(valor, "duracion"))
    else:
        _agregar(efectos, tipo, valor, None)


def _agregar(efectos: list, tipo, valor, duracion) -> None:
    tipo = _tipo_canonico(tipo)
    cantidad = entero(valor)
    if not tipo or _es_dano_directo(tipo) or cantidad is None or cantidad == 0:
        return
    duracion = entero(duracion)
    if duracion is not None and duracion <= 0:
        duracion = None
    if tipo == VELOCIDAD and duracion is None:
        return                          # un cambio de velocidad sin duración no se puede deshacer al terminar
    if tipo != VELOCIDAD and cantidad < 0:
        return                          # veneno o regeneración negativos no tienen sentido en las reglas
    for existente in efectos:
        if existente.tipo == tipo:
            return
    efectos.append(EfectoFichaDTO(tipo, cantidad, duracion))


def _tipo_canonico(tipo) -> str:
    nombre = normalizar(tipo)
    for alias, canonico in _ALIAS_TIPO:
        if nombre == alias:
            return canonico
    return nombre


def _es_dano_directo(tipo: str) -> bool:
    """"efecto": "daño" describe la trampa común: su daño ya es el campo "daño", no es un efecto aparte."""
    return tipo == "dano" or tipo == "danio"

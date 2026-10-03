"""
DTOs de una sala (Integrante 2).

SalidaDTO         -> una salida en su ESTADO INICIAL (no el estado vivo de la puerta;
                     ese lo lleva Mazmorra en Lógica).
EnemigoEnSalaDTO  -> una instancia de enemigo colocada en la sala (instancia, tipo, vida).
TrampaEnSalaDTO   -> una instancia de trampa colocada en la sala (instancia, tipo).
ContenidoSalaDTO  -> la respuesta de /contenido para UNA sala. Solo circula dentro de
                     Data: /contenido no trae nombre ni salidas, así que por sí sola no
                     alcanza para armar un SalaDTO.
SalaDTO           -> esqueleto (/salas) + contenido (/contenido) de una sala.

Las colecciones son arrays (list). Convención del equipo: un DTO nunca se modifica
después de creado; si algo cambia, se crea uno nuevo.
"""
from dataclasses import dataclass, field, replace

from DTO.Direcciones import DIRECCIONES


@dataclass(frozen=True)
class SalidaDTO:
    sala_destino: int
    cerrada: bool = False
    llave: str | None = None
    cierre_automatico: int | None = None

    @classmethod
    def desde_diccionario(cls, d: dict) -> "SalidaDTO":
        # En el API, 'cerrada', 'llave' y 'cierre_automatico' pueden faltar o venir en null.
        return cls(
            sala_destino=d["sala"],
            cerrada=bool(d.get("cerrada")),          # null o ausente -> False
            llave=d.get("llave"),
            cierre_automatico=d.get("cierre_automatico"),
        )

    def a_diccionario(self) -> dict:
        d = {"sala": self.sala_destino}
        if self.cerrada:
            d["cerrada"] = True
        if self.llave is not None:
            d["llave"] = self.llave
        if self.cierre_automatico is not None:
            d["cierre_automatico"] = self.cierre_automatico
        return d


@dataclass(frozen=True)
class EnemigoEnSalaDTO:
    instancia: str
    tipo: str               # id de la ficha de catálogo
    vida: int | None = None  # None: Lógica usa vida_max de la ficha

    @classmethod
    def desde_diccionario(cls, d: dict) -> "EnemigoEnSalaDTO":
        return cls(instancia=d["instancia"], tipo=d["tipo"], vida=d.get("vida"))

    def a_diccionario(self) -> dict:
        return {"instancia": self.instancia, "tipo": self.tipo, "vida": self.vida}


@dataclass(frozen=True)
class TrampaEnSalaDTO:
    instancia: str
    tipo: str               # id de la ficha de catálogo

    @classmethod
    def desde_diccionario(cls, d: dict) -> "TrampaEnSalaDTO":
        return cls(instancia=d["instancia"], tipo=d["tipo"])

    def a_diccionario(self) -> dict:
        return {"instancia": self.instancia, "tipo": self.tipo}


@dataclass(frozen=True)
class ContenidoSalaDTO:
    sala: int
    enemigos: list[EnemigoEnSalaDTO] = field(default_factory=list)
    objetos: list[str] = field(default_factory=list)   # ids de catálogo
    trampas: list[TrampaEnSalaDTO] = field(default_factory=list)

    @classmethod
    def desde_diccionario(cls, d: dict) -> "ContenidoSalaDTO":
        # Solo 'sala' es obligatorio en el API; las tres listas pueden faltar.
        return cls(
            sala=d["sala"],
            enemigos=[EnemigoEnSalaDTO.desde_diccionario(e) for e in d.get("enemigos", [])],
            objetos=list(d.get("objetos", [])),
            trampas=[TrampaEnSalaDTO.desde_diccionario(t) for t in d.get("trampas", [])],
        )

    def a_diccionario(self) -> dict:
        return {
            "sala": self.sala,
            "enemigos": [e.a_diccionario() for e in self.enemigos],
            "objetos": list(self.objetos),
            "trampas": [t.a_diccionario() for t in self.trampas],
        }


@dataclass(frozen=True)
class SalaDTO:
    id: int
    nombre: str
    salidas: list[SalidaDTO | None]   # 4 posiciones: N, S, E, O (ver DTO/direcciones.py)
    version: str                      # versión de la cripta a la que pertenece
    contenido_cargado: bool = False
    enemigos: list[EnemigoEnSalaDTO] = field(default_factory=list)
    objetos: list[str] = field(default_factory=list)
    trampas: list[TrampaEnSalaDTO] = field(default_factory=list)

    @classmethod
    def desde_diccionario(cls, esqueleto: dict, version: str, contenido: dict | None = None) -> "SalaDTO":
        """
        esqueleto: una sala de GET /criptas/{id}/salas.
        version:   versión de la cripta (viene en CriptaDTO; /salas no la trae).
        contenido: la entrada de esa sala en /contenido, o None si aún no se tiene.
        """
        salidas_json = esqueleto.get("salidas") or {}   # 'salidas' puede faltar en el API
        salidas = [None, None, None, None]
        for i in range(len(DIRECCIONES)):
            s = salidas_json.get(DIRECCIONES[i])
            if s is not None:
                salidas[i] = SalidaDTO.desde_diccionario(s)
        sala = cls(id=esqueleto["id"], nombre=esqueleto["nombre"], salidas=salidas, version=version)
        if contenido is None:
            return sala
        return sala.con_contenido(ContenidoSalaDTO.desde_diccionario(contenido))

    def con_contenido(self, contenido: ContenidoSalaDTO) -> "SalaDTO":
        """Devuelve un SalaDTO NUEVO con el contenido incorporado (este no se modifica)."""
        if contenido.sala != self.id:
            raise ValueError(f"El contenido es de la sala {contenido.sala}, no de la sala {self.id}")
        return replace(self, contenido_cargado=True,
                       enemigos=list(contenido.enemigos),
                       objetos=list(contenido.objetos),
                       trampas=list(contenido.trampas))

    def a_diccionario(self) -> dict:
        """Formato para persistir: las mismas piezas del API más la versión."""
        salidas_json = {}
        for i in range(len(DIRECCIONES)):
            if self.salidas[i] is not None:
                salidas_json[DIRECCIONES[i]] = self.salidas[i].a_diccionario()
        contenido = None
        if self.contenido_cargado:
            contenido = ContenidoSalaDTO(self.id, list(self.enemigos), list(self.objetos),
                                         list(self.trampas)).a_diccionario()
        return {
            "esqueleto": {"id": self.id, "nombre": self.nombre, "salidas": salidas_json},
            "version": self.version,
            "contenido": contenido,
        }

    @classmethod
    def desde_persistido(cls, d: dict) -> "SalaDTO":
        """Inverso exacto de a_diccionario()."""
        return cls.desde_diccionario(d["esqueleto"], d["version"], d["contenido"])
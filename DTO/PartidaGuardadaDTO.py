"""
DTOs del guardado de la partida (Integrante 2, enunciado §4.10). PROPUESTA para revisar con el equipo.

Los llena Lógica (Marco: motor, jugador, mazmorra, efectos, eventos y azar) y Servicios
(Kristel: inventario, semilla y log de --replay). GuardadoBinario (Datos) los escribe y los lee
sin conocer Lógica. a_diccionario / desde_diccionario sirven para guardar EL MISMO estado en JSON
y comparar tamaño y tiempo de carga contra el formato binario (lo pide §4.10).

PartidaGuardadaDTO  -> el bloque global (todo lo que no es de una sala).
SalaGuardadaDTO     -> un bloque por CADA sala del esqueleto (se puede leer una sola sin leer el
                       archivo completo). Se guardan todas, no solo las que tienen contenido: una
                       sala sin contenido también puede tener una puerta abierta, un enemigo que
                       llegó o los objetos que soltó un enemigo al morir.

Acuerdos del equipo (10 y 11 de octubre):
  - Solo se guardan eventos VÁLIDOS. El dueño de un evento se guarda como una referencia:
        "accion_actor"                    actor = "jugador" o la instancia del enemigo
        "veneno" / "velocidad" / "antorcha" efecto = posición en PartidaGuardadaDTO.efectos
                                          (actor + tipo no basta: puede haber dos velocidades)
        "rearme_trampa"                   sala + trampa (instancia)
        "cierre_puerta"                   sala + direccion de una de las caras (0=N, 1=S, 2=E, 3=O)
  - El equipo equipado se guarda por POSICIÓN en el inventario (puede haber dos objetos iguales).
    Jugador.arma/armadura no se guardan: al cargar se llenan desde el inventario.
  - El historial de retroceso y la caché del catálogo no se guardan.
  - ruta_log y acciones_en_log permiten seguir el --replay de una partida cargada
    (BitacoraReplayIO.continuar_desde).

Regla de los DTOs: solo transportan datos. Las colecciones son arrays (list).
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class JugadorGuardadoDTO:
    vida: int
    vida_max: int
    ataque: int              # base, sin el arma (el arma sale del inventario)
    defensa: int             # base, sin la armadura
    velocidad: int           # actual: puede estar cambiada por un efecto de velocidad
    sala_actual: int
    acciones: int

    @classmethod
    def desde_diccionario(cls, d: dict) -> "JugadorGuardadoDTO":
        return cls(d["vida"], d["vida_max"], d["ataque"], d["defensa"], d["velocidad"],
                   d["sala_actual"], d["acciones"])

    def a_diccionario(self) -> dict:
        return {"vida": self.vida, "vida_max": self.vida_max, "ataque": self.ataque,
                "defensa": self.defensa, "velocidad": self.velocidad,
                "sala_actual": self.sala_actual, "acciones": self.acciones}


@dataclass(frozen=True)
class InventarioGuardadoDTO:
    objetos: list[str] = field(default_factory=list)   # ids de catálogo, en el ORDEN REAL
    cursor: int | None = None                          # posición del cursor; None si está vacío
    arma: int | None = None                            # posición del arma equipada
    armadura: int | None = None                        # posición de la armadura equipada

    @classmethod
    def desde_diccionario(cls, d: dict) -> "InventarioGuardadoDTO":
        return cls(list(d["objetos"]), d["cursor"], d["arma"], d["armadura"])

    def a_diccionario(self) -> dict:
        return {"objetos": list(self.objetos), "cursor": self.cursor,
                "arma": self.arma, "armadura": self.armadura}


@dataclass(frozen=True)
class ContadorTipoDTO:
    """Mazmorra.contadores_tipo: cuántos enemigos de un tipo se han numerado ("Rata #3")."""
    tipo: str
    cantidad: int

    @classmethod
    def desde_diccionario(cls, d: dict) -> "ContadorTipoDTO":
        return cls(d["tipo"], d["cantidad"])

    def a_diccionario(self) -> dict:
        return {"tipo": self.tipo, "cantidad": self.cantidad}


@dataclass(frozen=True)
class EfectoGuardadoDTO:
    tipo: str                # "veneno", "velocidad" o "antorcha"
    actor: str               # "jugador" o la instancia del enemigo
    duracion: int
    valor: int | None        # daño del veneno, modificador de la velocidad; None en la antorcha
    fin: int                 # reloj en que termina
    cambio_real: int = 0     # solo Velocidad: lo que realmente cambió (para deshacerlo al terminar)

    @classmethod
    def desde_diccionario(cls, d: dict) -> "EfectoGuardadoDTO":
        return cls(d["tipo"], d["actor"], d["duracion"], d["valor"], d["fin"], d.get("cambio_real", 0))

    def a_diccionario(self) -> dict:
        return {"tipo": self.tipo, "actor": self.actor, "duracion": self.duracion,
                "valor": self.valor, "fin": self.fin, "cambio_real": self.cambio_real}


@dataclass(frozen=True)
class EventoGuardadoDTO:
    """Un evento VÁLIDO de la cola. Solo se llenan los campos del dueño que le tocan a su tipo."""
    tiempo: int
    secuencia: int
    tipo: str
    actor: str | None = None       # accion_actor
    efecto: int | None = None      # veneno / velocidad / antorcha: posición en PartidaGuardadaDTO.efectos
    sala: int | None = None        # rearme_trampa y cierre_puerta
    trampa: str | None = None      # rearme_trampa: instancia de la trampa
    direccion: int | None = None   # cierre_puerta: dirección de una de las caras

    @classmethod
    def desde_diccionario(cls, d: dict) -> "EventoGuardadoDTO":
        return cls(d["tiempo"], d["secuencia"], d["tipo"], d.get("actor"), d.get("efecto"),
                   d.get("sala"), d.get("trampa"), d.get("direccion"))

    def a_diccionario(self) -> dict:
        return {"tiempo": self.tiempo, "secuencia": self.secuencia, "tipo": self.tipo,
                "actor": self.actor, "efecto": self.efecto, "sala": self.sala,
                "trampa": self.trampa, "direccion": self.direccion}


@dataclass(frozen=True)
class EnemigoGuardadoDTO:
    """Su sala es la del SalaGuardadaDTO que lo contiene. Ficha, ataque y defensa salen del catálogo."""
    instancia: str
    tipo: str                # id de la ficha de catálogo
    vida: int
    velocidad: int           # actual: puede estar cambiada por un efecto de velocidad
    numero: int              # el "#2" de "Rata #2"
    activo: bool

    @classmethod
    def desde_diccionario(cls, d: dict) -> "EnemigoGuardadoDTO":
        return cls(d["instancia"], d["tipo"], d["vida"], d["velocidad"], d["numero"], d["activo"])

    def a_diccionario(self) -> dict:
        return {"instancia": self.instancia, "tipo": self.tipo, "vida": self.vida,
                "velocidad": self.velocidad, "numero": self.numero, "activo": self.activo}


@dataclass(frozen=True)
class TrampaGuardadaDTO:
    instancia: str
    tipo: str                # id de la ficha de catálogo
    armada: bool

    @classmethod
    def desde_diccionario(cls, d: dict) -> "TrampaGuardadaDTO":
        return cls(d["instancia"], d["tipo"], d["armada"])

    def a_diccionario(self) -> dict:
        return {"instancia": self.instancia, "tipo": self.tipo, "armada": self.armada}


@dataclass(frozen=True)
class SalaGuardadaDTO:
    """
    El estado de UNA sala. Nombre, destinos, llaves y cierres automáticos no se guardan: vienen del
    esqueleto (que se vuelve a cargar del API o del paquete con la misma versión de la cripta).
    Si contenido_cargado es False, al entrar se pide el contenido como siempre y se AGREGA a lo de aquí.
    """
    id: int
    contenido_cargado: bool
    puertas_cerradas: list[bool] = field(default_factory=lambda: [False, False, False, False])  # N, S, E, O
    objetos: list[str] = field(default_factory=list)          # ids de catálogo, en orden
    trampas: list[TrampaGuardadaDTO] = field(default_factory=list)
    enemigos: list[EnemigoGuardadoDTO] = field(default_factory=list)   # en el orden de la lista de la sala

    @classmethod
    def desde_diccionario(cls, d: dict) -> "SalaGuardadaDTO":
        return cls(d["id"], d["contenido_cargado"], list(d["puertas_cerradas"]), list(d["objetos"]),
                   [TrampaGuardadaDTO.desde_diccionario(t) for t in d["trampas"]],
                   [EnemigoGuardadoDTO.desde_diccionario(e) for e in d["enemigos"]])

    def a_diccionario(self) -> dict:
        return {"id": self.id, "contenido_cargado": self.contenido_cargado,
                "puertas_cerradas": list(self.puertas_cerradas), "objetos": list(self.objetos),
                "trampas": [t.a_diccionario() for t in self.trampas],
                "enemigos": [e.a_diccionario() for e in self.enemigos]}


@dataclass(frozen=True)
class PartidaGuardadaDTO:
    # ---- identifica la partida (va en la cabecera; al cargar se comparan las versiones)
    id_cripta: str
    version_cripta: str
    version_catalogo: str
    semilla: int
    # ---- Motor
    reloj: int
    siguiente_secuencia: int       # ColaEventos.siguiente_secuencia
    enemigos_derrotados: int
    terminado: bool
    victoria: bool
    # ---- Mazmorra
    salida_abierta: bool
    # ---- estado del azar: random.Random.getstate() = (azar_version, tuple(azar_estado), azar_gauss)
    azar_version: int
    azar_estado: list[int]
    azar_gauss: float | None
    # ---- jugador e inventario
    jugador: JugadorGuardadoDTO
    inventario: InventarioGuardadoDTO
    # ---- el resto del estado global
    rastro: list[int | None] = field(default_factory=list)            # RastroSalas.tiempos, indexado por id de sala
    contadores_tipo: list[ContadorTipoDTO] = field(default_factory=list)
    efectos: list[EfectoGuardadoDTO] = field(default_factory=list)     # en el orden de GestorEfectos.activos
    eventos: list[EventoGuardadoDTO] = field(default_factory=list)     # solo los válidos
    # ---- --replay de una partida cargada
    ruta_log: str | None = None
    acciones_en_log: int = 0

    @classmethod
    def desde_diccionario(cls, d: dict) -> "PartidaGuardadaDTO":
        return cls(
            id_cripta=d["id_cripta"], version_cripta=d["version_cripta"],
            version_catalogo=d["version_catalogo"], semilla=d["semilla"],
            reloj=d["reloj"], siguiente_secuencia=d["siguiente_secuencia"],
            enemigos_derrotados=d["enemigos_derrotados"], terminado=d["terminado"], victoria=d["victoria"],
            salida_abierta=d["salida_abierta"],
            azar_version=d["azar_version"], azar_estado=list(d["azar_estado"]), azar_gauss=d["azar_gauss"],
            jugador=JugadorGuardadoDTO.desde_diccionario(d["jugador"]),
            inventario=InventarioGuardadoDTO.desde_diccionario(d["inventario"]),
            rastro=list(d["rastro"]),
            contadores_tipo=[ContadorTipoDTO.desde_diccionario(c) for c in d["contadores_tipo"]],
            efectos=[EfectoGuardadoDTO.desde_diccionario(e) for e in d["efectos"]],
            eventos=[EventoGuardadoDTO.desde_diccionario(e) for e in d["eventos"]],
            ruta_log=d.get("ruta_log"), acciones_en_log=d.get("acciones_en_log", 0),
        )

    def a_diccionario(self) -> dict:
        return {
            "id_cripta": self.id_cripta, "version_cripta": self.version_cripta,
            "version_catalogo": self.version_catalogo, "semilla": self.semilla,
            "reloj": self.reloj, "siguiente_secuencia": self.siguiente_secuencia,
            "enemigos_derrotados": self.enemigos_derrotados, "terminado": self.terminado,
            "victoria": self.victoria, "salida_abierta": self.salida_abierta,
            "azar_version": self.azar_version, "azar_estado": list(self.azar_estado),
            "azar_gauss": self.azar_gauss,
            "jugador": self.jugador.a_diccionario(), "inventario": self.inventario.a_diccionario(),
            "rastro": list(self.rastro),
            "contadores_tipo": [c.a_diccionario() for c in self.contadores_tipo],
            "efectos": [e.a_diccionario() for e in self.efectos],
            "eventos": [e.a_diccionario() for e in self.eventos],
            "ruta_log": self.ruta_log, "acciones_en_log": self.acciones_en_log,
        }
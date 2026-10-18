"""
EventosSonoros (Vista): la DECISIÓN de qué suena en cada cuadro. No toca el mezclador: le pide las cosas a un motor con
los métodos de View/Sonidos.py (efecto, musica, volumen_musica, parar_musica, posicion_musica_ms), así se prueba con un motor
falso que solo anota las llamadas. Recuerda el cuadro anterior; el instante lo recibe de la Vista ('ahora', en ms).

    actualizar(pantalla, ahora)        una vez por cuadro dibujado

Efectos (Etapa 9B, fase 1):
    Click             sube PantallaDTO.activaciones (botón activado o Esperar); o desaparece del suelo un objeto que NO es
                      una llave (recogido). A lo sumo uno por cuadro.
    Main_Room_Sound   el primer cuadro de juego tras la pantalla "nombre", si la partida es NUEVA (reloj 0)
No suenan, en el primer cuadro de una partida, cuando el reloj del estado retrocede (retroceso, cargar), cuando cambia la sala
ni en los cuadros que no son de la partida (salvo la música y el Click).

Música (un tema a la vez): Main_Menu en menu, criptas, nombre y puntajes; Game_Ambient en juego y pausa, y se apaga al terminar
la partida. Si el tema no cambia no se reinicia. Al cambiar de tema el anterior se apaga con un fundido hecho a mano (cuadro a
cuadro, con el reloj de la Vista) y el nuevo entra con su propio fundido. En la pausa baja a MUSICA_PAUSA de su volumen.
BUCLE A MANO: cada tema tiene un fin_util_ms (después viene silencio); MUSICA_BAJADA_MS antes el volumen baja a 0 y al llegar
vuelve a empezar desde 0. Durante la pausa no se revisa el bucle: se retoma al continuar.
"""
from View import Componentes as c

_CLASE_LLAVE = "llave"


def _fila(tabla: list, clave: str):
    for fila in tabla:
        if fila[0] == clave:
            return fila
    return None


def _contiene(lista: list, nombre: str) -> bool:
    for elemento in lista:
        if elemento == nombre:
            return True
    return False


def _cuantos(objetos: list, id_objeto: str) -> int:
    n = 0
    for otro, _ in objetos:
        if otro == id_objeto:
            n += 1
    return n


class EventosSonoros:

    def __init__(self, motor):
        self._motor = motor
        self._activaciones: int | None = None       # el contador del cuadro anterior (None: aún no hay)
        self._previa: tuple | None = None           # (sala, reloj, [(id, clase) del suelo]) del cuadro anterior de la partida
        self._viene_de_nombre = False               # el cuadro anterior era la pantalla "nombre"
        self._tema: str | None = None               # la música que suena (o se está apagando)
        self._saliendo = False
        self._salida_desde = 0
        self._salida_volumen = 0.0
        self._volumen = 0.0                         # el último volumen enviado al motor
        self._empezo_en = 0
        self._ya_sonaron: list[str] = []

    def actualizar(self, pantalla, ahora: int) -> None:
        self._efectos(pantalla)
        self._musica(pantalla, ahora)

    # ================================================================== efectos
    def _efectos(self, pantalla) -> None:
        nombre = pantalla.pantalla
        click = self._activaciones is not None and pantalla.activaciones > self._activaciones
        self._activaciones = pantalla.activaciones
        if nombre == "nombre":
            self._viene_de_nombre = True
        elif nombre != "juego":
            self._viene_de_nombre = False
        if nombre == "juego" and pantalla.estado is not None:
            if self._cuadro_de_partida(pantalla.estado):
                click = True
        elif nombre != "pausa":
            self._previa = None                     # otra pantalla: la próxima partida empieza de cero
        if click:
            self._motor.efecto(c.SONIDO_CLICK)

    def _cuadro_de_partida(self, estado) -> bool:
        """Compara el cuadro con el anterior. True si hay que tocar Click (se recogió un objeto)."""
        suelo = [(objeto.id, objeto.clase) for objeto in estado.objetos_suelo]
        nueva = (estado.sala.id, estado.reloj, suelo)
        previa, self._previa = self._previa, nueva
        if previa is None:                          # el primer cuadro: no compara nada
            if self._viene_de_nombre and estado.reloj == 0:
                self._motor.efecto(c.SONIDO_SALA)
            self._viene_de_nombre = False
            return False
        if nueva[0] != previa[0] or nueva[1] < previa[1]:
            return False                            # otra sala, o el reloj retrocedió (retroceso o cargar)
        for id_objeto, clase in previa[2]:
            if clase != _CLASE_LLAVE and _cuantos(previa[2], id_objeto) > _cuantos(suelo, id_objeto):
                return True
        return False

    # ================================================================== música
    @staticmethod
    def _tema_de(pantalla) -> str | None:
        if pantalla.pantalla in ("juego", "pausa") and pantalla.estado is not None and pantalla.estado.terminado:
            return None
        fila = _fila(c.MUSICA_POR_PANTALLA, pantalla.pantalla)
        return None if fila is None else fila[1]

    def _musica(self, pantalla, ahora: int) -> None:
        objetivo = self._tema_de(pantalla)
        pausa = pantalla.pantalla == "pausa"
        if self._saliendo:
            progreso = (ahora - self._salida_desde) / c.MUSICA_SALIDA_MS
            if progreso < 1.0:
                self._poner_volumen(self._salida_volumen * (1.0 - max(0.0, progreso)))
                return
            self._motor.parar_musica()
            self._tema = None
            self._saliendo = False
        if self._tema is None:
            if objetivo is not None:
                self._empezar(objetivo, ahora, pausa)
            return
        if objetivo != self._tema:
            self._saliendo = True
            self._salida_desde = ahora
            self._salida_volumen = self._volumen
            return
        self._sostener(pausa, ahora)

    def _empezar(self, tema: str, ahora: int, pausa: bool) -> None:
        fila = _fila(c.MUSICAS, tema)
        if fila is None:
            return
        inicio = 0 if _contiene(self._ya_sonaron, tema) else fila[3]     # el silencio del principio solo se salta la primera vez
        self._ya_sonaron.append(tema)
        volumen = fila[1] * (c.MUSICA_PAUSA if pausa else 1.0)
        self._motor.musica(tema, volumen, inicio, c.MUSICA_ENTRADA_MS)
        self._tema = tema
        self._volumen = volumen
        self._empezo_en = ahora

    def _sostener(self, pausa: bool, ahora: int) -> None:
        """El mismo tema sigue: el volumen de la pausa y el bucle a mano."""
        fila = _fila(c.MUSICAS, self._tema)
        base = fila[1]
        if pausa:
            self._poner_volumen(base * c.MUSICA_PAUSA)
            return
        posicion = self._motor.posicion_musica_ms()
        if posicion < 0:                            # no hay noticias de la música: si ya debería sonar, se reinicia
            if ahora - self._empezo_en > c.MUSICA_SIN_NOTICIAS_MS:
                self._reiniciar(fila, ahora)
            else:
                self._poner_volumen(base)
            return
        restante = fila[2] - posicion
        if restante <= 0:
            self._reiniciar(fila, ahora)
        elif restante <= c.MUSICA_BAJADA_MS:
            self._poner_volumen(base * restante / c.MUSICA_BAJADA_MS)
        else:
            self._poner_volumen(base)

    def _reiniciar(self, fila, ahora: int) -> None:
        self._motor.musica(fila[0], fila[1], 0, c.MUSICA_ENTRADA_MS)
        self._volumen = fila[1]
        self._empezo_en = ahora

    def _poner_volumen(self, volumen: float) -> None:
        if abs(volumen - self._volumen) > 1e-9:
            self._motor.volumen_musica(volumen)
            self._volumen = volumen

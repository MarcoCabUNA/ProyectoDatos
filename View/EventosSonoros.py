"""
EventosSonoros (Vista): la DECISIÓN de qué suena en cada cuadro. No toca el mezclador: le pide las cosas a un motor con
los métodos de View/Sonidos.py (efecto, musica, volumen_musica, parar_musica, posicion_musica_ms, latido, pausar_latido, fin,
parar_fin), así se prueba con un motor falso que solo anota las llamadas. Recuerda el cuadro anterior; el instante lo recibe de
la Vista ('ahora', en ms).

    actualizar(pantalla, ahora)        una vez por cuadro dibujado
    intensidad_latido(ahora)           0 a 1: la envolvente (suavizada) de Low_Health en este instante; None si no está sonando

Efectos de la partida (se deciden comparando el cuadro con el anterior):
    Click               sube PantallaDTO.activaciones (botón activado o Esperar); o desaparece del suelo un objeto que NO es
                        una llave (recogido). A lo sumo uno por cuadro.
    Grab_Key_Sound      desaparece del suelo un objeto de CLASE "llave" (en lugar del Click del recogido)
    Main_Room_Sound     el primer cuadro de juego tras la pantalla "nombre", si la partida es NUEVA (reloj 0); en ese cuadro
                        no suena Click (el de "Aceptar")
    Enemies_Impact_Hit  baja la vida de un enemigo (por id), o desaparece uno que tenía vida. A lo sumo uno por cuadro.
    Hero_Impact_Hit     baja la vida del protagonista (golpes, trampas y veneno). A lo sumo uno por cuadro.
    Locked_Room_Change  una puerta cerrada de la misma sala pasa a abierta (suena al abrirla, no al cruzarla)
No suenan en el primer cuadro de una partida, cuando el reloj del estado retrocede (retroceso, cargar), cuando cambia la sala
ni en los cuadros que no son de la partida (salvo la música, los sonidos de fin, Low_Health y el Click).

Low_Health (canal reservado 0, en bucle): empieza con vida <= VIDA_BAJA_ENTRA de la máxima (y vida > 0) y se apaga al superar
VIDA_BAJA_SALE, al terminar la partida o al salir de juego y pausa. La pausa lo pausa. Su posición de reproducción (tiempo
sonado SIN contar las pausas, módulo su duración) mueve el latido visual de la viñeta de vida baja (intensidad_latido).

Derrota y victoria (canal reservado 1): Defeat_Music / Victory_Music al aparecer su pantalla; al salir de ella se apagan con un
fundido corto (y entra Main_Menu).

Música (un tema a la vez): Main_Menu en menu, criptas, nombre y puntajes; Game_Ambient en juego y pausa, y se apaga al terminar
la partida (ya desde la fase 1). Si el tema no cambia no se reinicia. Al cambiar de tema el anterior se apaga con un fundido hecho
a mano (cuadro a cuadro, con el reloj de la Vista) y el nuevo entra con su propio fundido. En la pausa baja a MUSICA_PAUSA de su
volumen. BUCLE A MANO: cada tema tiene un fin_util_ms (después viene silencio); MUSICA_BAJADA_MS antes el volumen baja a 0 y al
llegar vuelve a empezar desde 0. El bucle se revisa también durante la pausa (con el volumen de la pausa).
"""
from View import Animaciones as anim
from View import Componentes as c

_CLASE_LLAVE = "llave"
_SALA, _RECOGIDO, _LLAVE, _GOLPE_ENEMIGO, _GOLPE_HEROE, _PUERTA = range(6)      # lo que puede pasar entre dos cuadros


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


def _vida_de(actores: list, id_actor: str):
    """La vida del actor 'id_actor' en la lista de (id, vida), o None si ya no está."""
    for otro, vida in actores:
        if otro == id_actor:
            return vida
    return None


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
        self._previa: tuple | None = None           # (sala, reloj, suelo, enemigos, vida, puertas) del cuadro anterior
        self._viene_de_nombre = False               # el cuadro anterior era la pantalla "nombre"
        self._tema: str | None = None               # la música que suena (o se está apagando)
        self._saliendo = False
        self._salida_desde = 0
        self._salida_volumen = 0.0
        self._volumen = 0.0                         # el último volumen enviado al motor
        self._empezo_en = 0
        self._ya_sonaron: list[str] = []
        self._latido = False                        # Low_Health está sonando (o en pausa)
        self._latido_pausado = False
        self._latido_sonado = 0                     # ms sonados antes de la última reanudación (sin contar las pausas)
        self._latido_desde: int | None = None       # desde cuándo suena sin parar (None: en pausa)
        self._suave: list[float] = []               # la envolvente suavizada, calculada una vez
        self._suave_de: list[float] | None = None   # la envolvente de la que sale
        self._pantalla_de_fin: str | None = None    # "derrota" o "victoria" mientras su sonido corresponde a la pantalla

    def actualizar(self, pantalla, ahora: int) -> None:
        self._efectos(pantalla)
        self._vida_baja(pantalla, ahora)
        self._fin(pantalla)
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
        eventos = []
        if nombre == "juego" and pantalla.estado is not None:
            eventos = self._cuadro_de_partida(pantalla.estado)
        elif nombre != "pausa":
            self._previa = None                     # otra pantalla: la próxima partida empieza de cero
        if _SALA in eventos:
            self._motor.efecto(c.SONIDO_SALA)
            click = False                           # el Click de "Aceptar" no se mezcla con la entrada a la sala
        elif _RECOGIDO in eventos:
            click = True
        if click:
            self._motor.efecto(c.SONIDO_CLICK)
        if _LLAVE in eventos:
            self._motor.efecto(c.SONIDO_LLAVE)
        if _GOLPE_ENEMIGO in eventos:
            self._motor.efecto(c.SONIDO_GOLPE_ENEMIGO)
        if _GOLPE_HEROE in eventos:
            self._motor.efecto(c.SONIDO_GOLPE_HEROE)
        if _PUERTA in eventos:
            self._motor.efecto(c.SONIDO_PUERTA)

    def _cuadro_de_partida(self, estado) -> list[int]:
        """Compara el cuadro con el anterior y dice qué pasó (una vez cada cosa): _SALA (empieza una partida nueva), _RECOGIDO,
        _LLAVE, _GOLPE_ENEMIGO, _GOLPE_HEROE y _PUERTA."""
        suelo = [(objeto.id, objeto.clase) for objeto in estado.objetos_suelo]
        enemigos = [(enemigo.id, enemigo.vida) for enemigo in estado.enemigos]
        puertas = [None if salida is None else bool(salida.cerrada) for salida in estado.sala.salidas]
        vida = estado.jugador.vida
        nueva = (estado.sala.id, estado.reloj, suelo, enemigos, vida, puertas)
        previa, self._previa = self._previa, nueva
        if previa is None:                          # el primer cuadro: no compara nada
            nueva_partida = self._viene_de_nombre and estado.reloj == 0
            self._viene_de_nombre = False
            return [_SALA] if nueva_partida else []
        if nueva[0] != previa[0] or nueva[1] < previa[1]:
            return []                               # otra sala, o el reloj retrocedió (retroceso o cargar)
        eventos = []
        recogido = llave = False
        for id_objeto, clase in previa[2]:
            if _cuantos(previa[2], id_objeto) > _cuantos(suelo, id_objeto):
                if clase == _CLASE_LLAVE:
                    llave = True
                else:
                    recogido = True
        if recogido:
            eventos.append(_RECOGIDO)
        if llave:
            eventos.append(_LLAVE)
        for id_enemigo, vida_antes in previa[3]:
            vida_ahora = _vida_de(enemigos, id_enemigo)
            if vida_antes > 0 and (vida_ahora is None or vida_ahora < vida_antes):
                eventos.append(_GOLPE_ENEMIGO)      # le bajó la vida, o desapareció teniéndola
                break
        if vida < previa[4]:
            eventos.append(_GOLPE_HEROE)
        for antes, despues in zip(previa[5], puertas):
            if antes is True and despues is False:
                eventos.append(_PUERTA)
                break
        return eventos

    # ================================================================== vida baja y su latido
    def _vida_baja(self, pantalla, ahora: int) -> None:
        estado = pantalla.estado if pantalla.pantalla in ("juego", "pausa") else None
        if estado is None or estado.terminado or estado.jugador.vida <= 0 or estado.jugador.vida_max <= 0:
            self._apagar_latido()
            return
        fraccion = estado.jugador.vida / estado.jugador.vida_max
        if not self._latido and fraccion <= c.VIDA_BAJA_ENTRA:
            self._motor.latido(True)
            self._latido = True
            self._latido_pausado = False
            self._latido_sonado = 0
            self._latido_desde = ahora
        elif self._latido and fraccion > c.VIDA_BAJA_SALE:
            self._apagar_latido()
        if not self._latido:
            return
        pausa = pantalla.pantalla == "pausa"
        if pausa and not self._latido_pausado:
            self._motor.pausar_latido(True)
            self._latido_sonado += max(0, ahora - self._latido_desde)
            self._latido_desde = None
            self._latido_pausado = True
        elif not pausa and self._latido_pausado:
            self._motor.pausar_latido(False)
            self._latido_desde = ahora
            self._latido_pausado = False

    def _apagar_latido(self) -> None:
        if self._latido:
            self._motor.latido(False)
            self._latido = False
            self._latido_pausado = False
            self._latido_sonado = 0
            self._latido_desde = None

    def intensidad_latido(self, ahora: int) -> float | None:
        """La envolvente suavizada de Low_Health en el instante de reproducción (0 a 1), o None si no suena o no hay envolvente."""
        if not self._latido:
            return None
        crudo = self._motor.envolvente_latido
        if not crudo:
            return None
        if crudo is not self._suave_de:
            self._suave = anim.suavizar_envolvente(crudo)
            self._suave_de = crudo
        duracion = self._motor.duracion_latido_ms or len(crudo) * c.SONIDO_VENTANA_MS
        sonado = self._latido_sonado + (0 if self._latido_desde is None else max(0, ahora - self._latido_desde))
        posicion = (sonado % duracion) / c.SONIDO_VENTANA_MS
        i = int(posicion) % len(self._suave)
        fraccion = posicion - int(posicion)
        return self._suave[i] * (1.0 - fraccion) + self._suave[(i + 1) % len(self._suave)] * fraccion

    # ================================================================== derrota y victoria
    def _fin(self, pantalla) -> None:
        nombre = pantalla.pantalla
        fila = _fila(c.SONIDOS_DE_FIN, nombre)
        if fila is not None:
            if nombre != self._pantalla_de_fin:     # la pantalla acaba de aparecer
                self._motor.fin(fila[1])
                self._pantalla_de_fin = nombre
        elif self._pantalla_de_fin is not None:     # el jugador salió de ella
            self._motor.parar_fin(c.SONIDO_FIN_FUNDIDO_MS)
            self._pantalla_de_fin = None

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
        """El mismo tema sigue: el volumen de la pausa y el bucle a mano (que se revisa también durante la pausa)."""
        fila = _fila(c.MUSICAS, self._tema)
        base = fila[1] * (c.MUSICA_PAUSA if pausa else 1.0)
        posicion = self._motor.posicion_musica_ms()
        if posicion < 0:                            # no hay noticias de la música: si ya debería sonar, se reinicia
            if ahora - self._empezo_en > c.MUSICA_SIN_NOTICIAS_MS:
                self._reiniciar(fila, base, ahora)
            else:
                self._poner_volumen(base)
            return
        restante = fila[2] - posicion
        if restante <= 0:
            self._reiniciar(fila, base, ahora)
        elif restante <= c.MUSICA_BAJADA_MS:
            self._poner_volumen(base * restante / c.MUSICA_BAJADA_MS)
        else:
            self._poner_volumen(base)

    def _reiniciar(self, fila, volumen: float, ahora: int) -> None:
        self._motor.musica(fila[0], volumen, 0, c.MUSICA_ENTRADA_MS)
        self._volumen = volumen
        self._empezo_en = ahora

    def _poner_volumen(self, volumen: float) -> None:
        if abs(volumen - self._volumen) > 1e-9:
            self._motor.volumen_musica(volumen)
            self._volumen = volumen

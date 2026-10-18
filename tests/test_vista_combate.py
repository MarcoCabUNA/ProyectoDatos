"""
Pruebas del feedback de combate de la Vista (Etapa 9, fase 2): números flotantes, destello, borde rojo, muerte de enemigo, objeto
recogido, puerta que se abre y cursor de mano. Todo se deduce de las DIFERENCIAS entre un cuadro y el anterior (nunca de los mensajes).
Se usa la Vista real con un reloj falso. Se ejecuta desde cualquier carpeta.
"""
import contextlib
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_pygame import pygame  # noqa: E402
from ayudas_vista import Recorrido, cerrada, con_enemigos, con_objetos, con_sala, estado_base  # noqa: E402
from test_vista_animaciones import (Lienzo, Reloj, RelojQueAvanza, _escena_cargada, _juego, _terminado,  # noqa: E402
                                    _zonas, vista_abierta)

import View.Animaciones as anim  # noqa: E402
import View.Componentes as c  # noqa: E402
from DTO.ElementoDTO import ELEMENTO_PUERTA, ElementoDTO  # noqa: E402
from DTO.PantallaDTO import PantallaDTO  # noqa: E402
from DTO.SalaDTO import SalidaDTO  # noqa: E402
from View.VistaPygame import VistaPygame  # noqa: E402


# ================================================================ ayudas
@contextlib.contextmanager
def vista_con_lienzo(reloj, animaciones=True):
    with vista_abierta(animaciones, reloj) as vista:
        vista._superficie = Lienzo((c.ANCHO, c.ALTO))
        yield vista


def cuadro(vista, reloj, ms, estado, bajo=None):
    """Dibuja 'estado' en el instante 'ms' y devuelve las animaciones que la Vista recuerda."""
    reloj.ahora = ms
    vista._superficie.blits.clear()
    vista.dibujar(_juego(estado, None, bajo))
    return list(vista._efectos._anims) if vista._efectos is not None else []


def siguiente(estado, **cambios):
    """El estado del juego un paso después: el reloj virtual avanza (retroceder lo reinicia todo)."""
    return replace(estado, reloj=estado.reloj + 1, **cambios)


def con_vida_de(estado, id_enemigo, vida):
    return replace(estado, enemigos=[replace(e, vida=vida) if e.id == id_enemigo else e for e in estado.enemigos])


def con_vida_del_jugador(estado, vida):
    return replace(estado, jugador=replace(estado.jugador, vida=vida))


def de_tipo(animaciones, tipo):
    return [a for a in animaciones if a.tipo == tipo]


def rect_del_enemigo(vista, estado, id_enemigo):
    reparto = vista._escena._repartir(estado)
    for i, e in enumerate(estado.enemigos):
        if e.id == id_enemigo:
            return reparto.sprites[i].get_rect(midbottom=reparto.enemigos[i].midbottom)
    raise AssertionError(id_enemigo)


def colores_en(superficie, rect, color):
    """Cuántos píxeles de 'rect' tienen exactamente ese color."""
    n = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            if tuple(superficie.get_at((x, y)))[:3] == tuple(color):
                n += 1
    return n


def hay_pixeles(imagen, color):
    return colores_en(imagen, imagen.get_rect(), color) > 0


def el_blit_de(vista, imagen):
    for fuente, rect in vista._superficie.blits:
        if fuente is imagen:
            return rect
    return None


# ================================================================ funciones puras
def probar_las_curvas_del_feedback_van_del_principio_al_fin_y_aguantan_cualquier_valor():
    assert [anim.sube_numero(p) for p in (-1, 0, 1, 2)] == [0, 0, c.NUMERO_SUBE, c.NUMERO_SUBE]
    subidas = [anim.sube_numero(k / 20) for k in range(21)]
    assert subidas == sorted(subidas) and subidas[10] > c.NUMERO_SUBE // 2                    # sube, cada vez más despacio
    assert anim.alfa_numero(0) == 255 and anim.alfa_numero(c.NUMERO_FIJO) == 255 and anim.alfa_numero(1) == 0
    assert anim.alfa_numero(0.8) < 255 and anim.alfa_numero(-3) == 255 and anim.alfa_numero(9) == 0
    assert anim.alfa_destello(0) == c.DESTELLO_ALFA and anim.alfa_destello(1) == 0 and 0 < anim.alfa_destello(0.5) < c.DESTELLO_ALFA
    assert anim.alfa_borde(0) == c.BORDE_ALFA and anim.alfa_borde(1) == 0
    assert anim.escala_muerte(0) == 1.0 and abs(anim.escala_muerte(1) - c.MUERTE_ENCOGE) < 1e-9
    assert anim.alfa_muerte(0) == 255 and anim.alfa_muerte(0.5) == 255 and anim.alfa_muerte(1) == 0
    assert anim.alfa_desvanece(0) == 255 and anim.alfa_desvanece(1) == 0
    assert anim.sube_recogido(0) == 0 and anim.sube_recogido(1) == c.RECOGIDO_SUBE
    assert anim.alfa_calido(0) == c.PUERTA_CALIDO_ALFA and anim.alfa_calido(1) == 0


def probar_las_duraciones_y_medidas_del_feedback_son_las_pedidas_y_viven_en_componentes():
    assert (c.NUMERO_MS, c.NUMERO_SUBE, c.DESTELLO_MS, c.BORDE_MS, c.MUERTE_ENEMIGO_MS) == (700, 36, 160, 220, 450)
    assert (c.RECOGIDO_MS, c.PUERTA_DESVANECE_MS, c.PUERTA_CALIDO_MS, c.MAX_ANIMACIONES) == (220, 260, 300, 24)


# ================================================================ números, destello y borde
def probar_el_numero_sale_sobre_el_actor_golpeado_por_su_id_aunque_cambie_el_orden_de_la_lista():
    reloj = Reloj(1000)
    base = _escena_cargada()
    with vista_con_lienzo(reloj) as vista:
        assert cuadro(vista, reloj, 1000, base) == []                                      # el primer cuadro: nada
        golpe = siguiente(base)
        golpe = con_vida_de(golpe, "enemigo-2", 8)
        anims = cuadro(vista, reloj, 1033, golpe)
        numeros = de_tipo(anims, "numero")
        assert len(numeros) == 1 and not numeros[0].del_jugador
        assert numeros[0].rect == rect_del_enemigo(vista, golpe, "enemigo-2")
        assert numeros[0].rect != rect_del_enemigo(vista, golpe, "enemigo-1")
        assert hay_pixeles(numeros[0].imagen, c.NUMERO_ROJO) and not hay_pixeles(numeros[0].imagen, c.NUMERO_VERDE)
        destellos = [a.clave for a in de_tipo(anims, "destello")]
        assert destellos == ["enemigo-2"]
        assert vista._efectos.alfa_de_destello(False, "enemigo-2", 1033) == c.DESTELLO_ALFA
        assert vista._efectos.alfa_de_destello(False, "enemigo-1", 1033) == 0
        assert vista._efectos.alfa_de_destello(True, "", 1033) == 0
        # ahora la lista cambia de orden y el golpeado es el otro: el número va con SU id, no con su posición
        vuelta = siguiente(golpe, enemigos=list(reversed(golpe.enemigos)))
        vuelta = con_vida_de(vuelta, "enemigo-1", 9)
        anims = cuadro(vista, reloj, 1066, vuelta)
        nuevos = [a for a in de_tipo(anims, "numero") if a.inicio == 1066]
        assert len(nuevos) == 1
        assert nuevos[0].rect == rect_del_enemigo(vista, vuelta, "enemigo-1"), (nuevos[0].rect, vuelta.enemigos[0].id)
        assert [a.clave for a in de_tipo(anims, "destello") if a.inicio == 1066] == ["enemigo-1"]


def probar_curar_saca_un_numero_verde_sin_destello_ni_borde_y_el_jugador_herido_sale_en_rojo_con_borde():
    reloj = Reloj(1000)
    base = con_vida_de(_escena_cargada(), "enemigo-1", 5)
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        sana = siguiente(con_vida_de(base, "enemigo-1", 9))
        anims = cuadro(vista, reloj, 1033, sana)
        verdes = de_tipo(anims, "numero")
        assert len(verdes) == 1 and hay_pixeles(verdes[0].imagen, c.NUMERO_VERDE) and not hay_pixeles(verdes[0].imagen, c.NUMERO_ROJO)
        assert de_tipo(anims, "destello") == [] and de_tipo(anims, "borde") == []
        herido = siguiente(con_vida_del_jugador(sana, 10))                                 # 18 -> 10
        anims = cuadro(vista, reloj, 1066, herido)
        propios = [a for a in de_tipo(anims, "numero") if a.del_jugador]
        assert len(propios) == 1 and hay_pixeles(propios[0].imagen, c.NUMERO_ROJO)
        assert propios[0].rect == vista._escena._rect_del_jugador(herido)
        assert len(de_tipo(anims, "destello")) == 1 and de_tipo(anims, "destello")[0].del_jugador
        assert len(de_tipo(anims, "borde")) == 1
        # el borde se ve en el filo de la pantalla y a los 220 ms ya no
        rojo = tuple(vista._superficie.get_at((0, 384)))[:3]
        assert rojo[0] > rojo[1] + 80, rojo
        assert vista._efectos.alfa_de_destello(True, "", 1066 + 159) > 0 and vista._efectos.alfa_de_destello(True, "", 1066 + 160) == 0
        cuadro(vista, reloj, 1066 + 221, herido)
        apagado = tuple(vista._superficie.get_at((0, 384)))[:3]
        assert apagado[0] < rojo[0] // 2 and apagado[0] < apagado[1] + 40, (rojo, apagado)


def probar_el_numero_sube_36_px_en_700_ms_y_desaparece_y_el_cuadro_lo_dibuja_visible():
    reloj = Reloj(1000)
    base = _escena_cargada()
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 100, base)                                                      # (su fundido de sala ya pasó en 1100)
        golpe = con_vida_de(siguiente(base), "enemigo-1", 3)
        cuadro(vista, reloj, 1100, golpe)
        numero = de_tipo(vista._efectos._anims, "numero")[0]
        ys = []
        for ms in (0, 100, 350, 699):
            cuadro(vista, reloj, 1100 + ms, golpe)
            rect = el_blit_de(vista, numero.imagen)
            assert rect is not None, ms
            ys.append(rect.bottom)
            if ms == 0:
                assert colores_en(vista._superficie, rect, c.NUMERO_ROJO) >= 20             # y se ve en pantalla
        assert ys == sorted(ys, reverse=True) and ys[0] - ys[-1] >= c.NUMERO_SUBE - 2, ys   # sube, y llega a ~36 px
        cuadro(vista, reloj, 1100 + 700, golpe)
        assert el_blit_de(vista, numero.imagen) is None and de_tipo(vista._efectos._anims, "numero") == []


def probar_el_golpe_mortal_al_protagonista_se_ve_aunque_la_partida_ya_termino_y_no_se_duplica():
    reloj = Reloj(1000)
    base = con_vida_del_jugador(_escena_cargada(), 6)
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 100, base)
        final = siguiente(_terminado(base, "derrota"))                                     # su vida pasa a 0 y termina
        anims = cuadro(vista, reloj, 1100, final)
        propios = [a for a in de_tipo(anims, "numero") if a.del_jugador]
        assert len(propios) == 1 and hay_pixeles(propios[0].imagen, c.NUMERO_ROJO)
        rect = el_blit_de(vista, propios[0].imagen)
        assert rect is not None and colores_en(vista._superficie, rect, c.NUMERO_ROJO) >= 20      # y se ve
        assert len(de_tipo(anims, "borde")) == 1 and len(de_tipo(anims, "destello")) == 1
        anims = cuadro(vista, reloj, 1100, final)                                            # el MISMO cuadro otra vez: nada nuevo
        assert (len(de_tipo(anims, "numero")), len(de_tipo(anims, "borde")), len(de_tipo(anims, "destello"))) == (1, 1, 1)
        for ms in (1150, 1400, 1700, 1799):                                                  # la demora: la partida terminada, igual
            anims = cuadro(vista, reloj, ms, final)
            assert len(de_tipo(anims, "numero")) == 1 and el_blit_de(vista, propios[0].imagen) is not None, ms
        anims = cuadro(vista, reloj, 1800, final)
        assert de_tipo(anims, "numero") == [] and el_blit_de(vista, propios[0].imagen) is None
        # al mostrar la derrota la memoria se borra, y la partida siguiente empieza sin nada
        vista.dibujar(PantallaDTO("derrota", estado=final))
        assert vista._efectos._anims == [] and vista._efectos._previa is None
        assert cuadro(vista, reloj, 5000, con_vida_del_jugador(base, 3)) == []


# ================================================================ muerte, recogido y puertas
def probar_el_enemigo_que_desaparece_muere_en_450_ms_la_rata_se_encoge_y_el_generico_usa_sus_4_fotogramas():
    reloj = Reloj(1000)
    base = con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 3)    # rata, rata, guardián
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        rata_antes = rect_del_enemigo(vista, base, "enemigo-1")
        muerta = siguiente(replace(base, enemigos=[e for e in base.enemigos if e.id != "enemigo-1"]))
        anims = cuadro(vista, reloj, 1100, muerta)
        fantasma = de_tipo(anims, "muerte")[0]
        assert fantasma.rect == rata_antes and fantasma.cuadros == [] and fantasma.imagen is not None   # la rata: sin fotogramas
        numero = [a for a in de_tipo(anims, "numero") if a.rect == rata_antes]
        assert len(numero) == 1 and hay_pixeles(numero[0].imagen, c.NUMERO_ROJO)
        anchos = []
        for ms in (0, 150, 300, 440):
            cuadro(vista, reloj, 1100 + ms, muerta)
            anchos.append(max(r.width for f, r in vista._superficie.blits if r.height <= fantasma.imagen.get_height()
                              and r.centerx == rata_antes.centerx and r.bottom == rata_antes.bottom))
        assert anchos == sorted(anchos, reverse=True) and anchos[-1] < anchos[0], anchos         # se encoge
        cuadro(vista, reloj, 1100 + 450, muerta)
        assert de_tipo(vista._efectos._anims, "muerte") == []
        # el genérico muere con sus fotogramas 'muerte'
        guardian_antes = rect_del_enemigo(vista, muerta, "enemigo-3")                        # (donde estaba en el cuadro anterior)
        sin_guardian = siguiente(replace(muerta, enemigos=[e for e in muerta.enemigos if e.id != "enemigo-3"]))
        anims = cuadro(vista, reloj, 2000, sin_guardian)
        fantasma = de_tipo(anims, "muerte")[0]
        assert len(fantasma.cuadros) == 4 and fantasma.imagen is None and fantasma.rect == guardian_antes
        usados = []
        for ms in (2000, 2120, 2230, 2340, 2440):
            cuadro(vista, reloj, ms, sin_guardian)
            for k, f in enumerate(fantasma.cuadros):
                if el_blit_de(vista, f) is not None:
                    usados.append(k)
        assert usados == [0, 1, 2, 3, 3], usados
        almacen = vista._escena._almacen
        for conjunto in (almacen.actor_a_altura("ent_guardian_oseo", fantasma.rect.height, "muerte"),):
            assert all(f.get_alpha() == 255 for f in conjunto.fotogramas)                    # los de la caché no se tocan


def probar_el_objeto_recogido_se_desvanece_subiendo_y_con_ids_repetidos_solo_desaparece_uno():
    reloj = Reloj(1000)
    base = con_objetos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 3)
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        antes = vista._escena._repartir(base).objetos[0].copy()
        recogido = siguiente(replace(base, objetos_suelo=base.objetos_suelo[1:]))
        anims = cuadro(vista, reloj, 1100, recogido)
        fantasma = de_tipo(anims, "recogido")
        assert len(fantasma) == 1 and fantasma[0].rect == antes
        ys = []
        for ms in (0, 110, 219):
            cuadro(vista, reloj, 1100 + ms, recogido)
            ys.append(el_blit_de(vista, fantasma[0].imagen).y)
        assert ys == sorted(ys, reverse=True) and ys[0] == antes.y and antes.y - ys[-1] >= c.RECOGIDO_SUBE - 2, ys
        cuadro(vista, reloj, 1100 + 220, recogido)
        assert de_tipo(vista._efectos._anims, "recogido") == []
        repetidos = replace(recogido, objetos_suelo=[recogido.objetos_suelo[0]] * 2 + recogido.objetos_suelo[1:])
        cuadro(vista, reloj, 3000, siguiente(repetidos))
        uno = replace(repetidos, objetos_suelo=repetidos.objetos_suelo[1:], reloj=repetidos.reloj + 5)
        assert len(de_tipo(cuadro(vista, reloj, 3100, uno), "recogido")) == 1


def probar_la_puerta_cerrada_que_se_abre_se_desvanece_y_solo_la_de_la_sala_de_salida_brilla():
    reloj = Reloj(1000)
    base = estado_base(3, N=cerrada(99), E=cerrada(6))                                    # la sala de salida es la 6
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        norte = [r for r, e in zip(vista._zonas._rectangulos, vista._zonas._elementos)
                 if e.tipo == ELEMENTO_PUERTA and e.indice == 0][0].copy()
        este = [r for r, e in zip(vista._zonas._rectangulos, vista._zonas._elementos)
                if e.tipo == ELEMENTO_PUERTA and e.indice == 2][0].copy()
        abierta_n = siguiente(con_sala(base, N=SalidaDTO(99), E=cerrada(6)))
        anims = cuadro(vista, reloj, 1100, abierta_n)
        assert [a.rect for a in de_tipo(anims, "puerta")] == [norte] and de_tipo(anims, "calido") == []
        assert el_blit_de(vista, de_tipo(anims, "puerta")[0].imagen) == norte
        abierta_e = siguiente(con_sala(abierta_n, N=SalidaDTO(99), E=SalidaDTO(6)))
        anims = cuadro(vista, reloj, 1200, abierta_e)
        assert [a.rect for a in de_tipo(anims, "puerta") if a.inicio == 1200] == [este]
        brillo = [a for a in de_tipo(anims, "calido")]
        assert len(brillo) == 1 and brillo[0].rect == este and brillo[0].duracion == 300
        assert el_blit_de(vista, brillo[0].imagen) is not None
        cuadro(vista, reloj, 1200 + 259, abierta_e)
        assert len(de_tipo(vista._efectos._anims, "puerta")) == 1
        cuadro(vista, reloj, 1200 + 260, abierta_e)
        assert de_tipo(vista._efectos._anims, "puerta") == [] and len(de_tipo(vista._efectos._anims, "calido")) == 1
        cuadro(vista, reloj, 1200 + 300, abierta_e)
        assert vista._efectos._anims == []


# ================================================================ cuándo se reinicia la memoria
def probar_el_primer_cuadro_y_el_reloj_que_retrocede_reinician_la_memoria_sin_animar():
    reloj = Reloj(1000)
    base = _escena_cargada()
    herida = con_vida_del_jugador(base, 5)
    with vista_con_lienzo(reloj) as vista:
        assert cuadro(vista, reloj, 5000, herida) == []                                    # primer cuadro, aunque esté herido
        golpe = con_vida_de(siguiente(herida), "enemigo-1", 2)
        assert len(de_tipo(cuadro(vista, reloj, 5100, golpe), "numero")) == 1
        retrocede = con_vida_de(siguiente(golpe), "enemigo-2", 1)
        assert cuadro(vista, reloj, 4000, retrocede) == []                                 # el reloj de la Vista retrocedió
        sigue = con_vida_de(siguiente(retrocede), "enemigo-2", 0)
        assert len(de_tipo(cuadro(vista, reloj, 4033, sigue), "numero")) == 1              # y la memoria sigue desde ahí
    reloj = Reloj(1000)
    with vista_con_lienzo(reloj) as vista:                                                 # el reloj del ESTADO retrocede (cargar/retroceso)
        cuadro(vista, reloj, 1000, replace(base, reloj=50))
        antes = replace(con_vida_del_jugador(con_vida_de(base, "enemigo-1", 3), 5), reloj=10)
        assert cuadro(vista, reloj, 1033, antes) == []


def probar_cambiar_de_sala_conserva_solo_lo_del_protagonista_si_es_contigua_y_borra_todo_si_no():
    reloj = Reloj(1000)
    sala_3 = estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada())
    sala_3 = con_objetos(con_enemigos(sala_3, 2), 2)
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, sala_3)
        golpe = siguiente(con_vida_de(sala_3, "enemigo-1", 4))
        assert len(de_tipo(cuadro(vista, reloj, 1033, golpe), "numero")) == 1
        # entra a la sala 4 (contigua: tiene una salida a la 3) y en la entrada pierde vida (una trampa)
        sala_4 = estado_base(4, S=SalidaDTO(3))
        sala_4 = replace(con_vida_del_jugador(sala_4, 12), reloj=golpe.reloj + 1)
        anims = cuadro(vista, reloj, 1066, sala_4)
        assert [a.del_jugador for a in anims if a.tipo == "numero"] == [True]               # el número del enemigo de la sala vieja no
        assert de_tipo(anims, "muerte") == [] and de_tipo(anims, "recogido") == [] and de_tipo(anims, "puerta") == []
    reloj = Reloj(1000)
    with vista_con_lienzo(reloj) as vista:                                                  # y si la sala no es contigua: nada
        cuadro(vista, reloj, 1000, sala_3)
        cuadro(vista, reloj, 1033, siguiente(con_vida_de(sala_3, "enemigo-1", 4)))
        lejana = replace(con_vida_del_jugador(estado_base(5, S=SalidaDTO(4)), 9), reloj=sala_3.reloj + 9)
        assert cuadro(vista, reloj, 1066, lejana) == []


def probar_al_mostrar_menus_y_pantallas_de_fin_la_memoria_se_borra_y_la_pausa_la_congela():
    reloj = Reloj(1000)
    base = _escena_cargada()
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        golpe = con_vida_de(siguiente(base), "enemigo-1", 4)
        numero = de_tipo(cuadro(vista, reloj, 1100, golpe), "numero")[0]
        # la pausa: la escena queda congelada y no se observa nada, aunque el estado traiga otro golpe
        reloj.ahora = 1300
        pausa = PantallaDTO("pausa", "Pausa", ["Continuar"], 0, estado=siguiente(con_vida_de(golpe, "enemigo-2", 1)))
        vista._superficie.blits.clear()
        vista.dibujar(pausa)
        assert len(de_tipo(vista._efectos._anims, "numero")) == 1                          # ni uno más
        assert el_blit_de(vista, numero.imagen) is not None                                # y el que había, congelado
        for pantalla in ("menu", "criptas", "nombre", "victoria", "derrota", "puntajes"):
            cuadro(vista, reloj, 1400, golpe)
            reloj.ahora = 1500
            vista.dibujar(PantallaDTO(pantalla, "", ["x"], 0, estado=golpe if pantalla in ("victoria", "derrota") else None))
            assert vista._efectos._anims == [] and vista._efectos._previa is None, pantalla
        assert cuadro(vista, reloj, 2000, con_vida_del_jugador(base, 2)) == []


def probar_la_memoria_no_pasa_de_24_animaciones_y_se_olvidan_las_mas_viejas():
    reloj = Reloj(1000)
    base = con_enemigos(estado_base(3, N=cerrada(), S=cerrada(), E=cerrada(), O=cerrada()), 12)
    with vista_con_lienzo(reloj) as vista:
        cuadro(vista, reloj, 1000, base)
        mazazo = base
        for e in base.enemigos:
            mazazo = con_vida_de(mazazo, e.id, 1)
        mazazo = con_vida_del_jugador(siguiente(mazazo), 3)
        anims = cuadro(vista, reloj, 1033, mazazo)
        assert len(anims) == c.MAX_ANIMACIONES == 24
        otra = mazazo
        for k in range(5):
            otra = siguiente(con_vida_del_jugador(otra, 3 - k - 1))
            assert len(cuadro(vista, reloj, 1066 + 33 * k, otra)) <= c.MAX_ANIMACIONES


# ================================================================ zonas, caché y cursor
def _secuencia_de_combate():
    base = estado_base(3, N=cerrada(99), E=cerrada(6), S=cerrada(), O=cerrada())
    base = con_objetos(con_enemigos(base, 3), 3)
    e1 = con_vida_de(siguiente(base), "enemigo-2", 6)
    e2 = con_vida_del_jugador(siguiente(e1), 9)
    e3 = siguiente(replace(e2, enemigos=[e for e in e2.enemigos if e.id != "enemigo-1"], objetos_suelo=e2.objetos_suelo[1:]))
    e4 = siguiente(con_sala(e3, N=SalidaDTO(99), E=SalidaDTO(6), S=cerrada(), O=cerrada()))
    return [base, base, e1, e1, e2, e3, e3, e4, e4, e4]


def _zonas_de_la_secuencia(animaciones):
    reloj = Reloj(1000)
    zonas = []
    with vista_abierta(animaciones, reloj) as vista:
        for k, estado in enumerate(_secuencia_de_combate()):
            reloj.ahora = 1000 + 100 * k
            vista.dibujar(_juego(estado, None, None))
            zonas.append(_zonas(vista))
    return zonas


def probar_ninguna_animacion_de_combate_registra_zonas_y_las_zonas_son_las_mismas_con_y_sin_animaciones():
    con = _zonas_de_la_secuencia(True)
    sin = _zonas_de_la_secuencia(False)
    assert con == sin
    reloj = Reloj(1000)
    with vista_con_lienzo(reloj) as vista:
        for k, estado in enumerate(_secuencia_de_combate()):
            cuadro(vista, reloj, 1000 + 100 * k, estado)


def probar_la_cache_no_crece_con_las_animaciones_de_combate_en_marcha():
    reloj = Reloj(1000)
    with vista_abierta(True, reloj) as vista:
        secuencia = _secuencia_de_combate()
        tamanos = []
        for vuelta in range(3):
            for k, estado in enumerate(secuencia):
                reloj.ahora = 10000 * vuelta + 1000 + 100 * k
                vista.dibujar(_juego(replace(estado, reloj=estado.reloj + 100 * vuelta + 100), None, None))
            tamanos.append(vista._escena._almacen.entradas_cache)
        assert tamanos[1] == tamanos[2], tamanos                                           # tras la primera vuelta ya no crece


def probar_el_cursor_es_una_mano_sobre_lo_pulsable_solo_al_cambiar_y_un_fallo_del_sistema_no_rompe_nada():
    pedidos = []
    original = pygame.mouse.set_cursor

    def espia(cursor):
        pedidos.append(cursor)
    pygame.mouse.set_cursor = espia
    try:
        base = _escena_cargada()
        sobre = ElementoDTO("objeto_suelo", 0)
        reloj = Reloj(1000)
        with vista_con_lienzo(reloj) as vista:
            for bajo in (None, None, sobre, sobre, ElementoDTO("enemigo", 1), None, None):
                cuadro(vista, reloj, reloj.ahora + 33, base, bajo)
            assert pedidos == [pygame.SYSTEM_CURSOR_HAND, pygame.SYSTEM_CURSOR_ARROW], pedidos
        pedidos.clear()
        with vista_con_lienzo(Reloj(1000), animaciones=False) as vista:                   # sin animaciones: ni se toca
            vista._reloj = Reloj(1000)
            cuadro(vista, vista._reloj, 1000, base, sobre)
            assert pedidos == []

        def falla(cursor):
            raise pygame.error("sin cursor del sistema")
        pygame.mouse.set_cursor = falla
        reloj = Reloj(1000)
        with vista_con_lienzo(reloj) as vista:
            cuadro(vista, reloj, 1000, base, sobre)
            cuadro(vista, reloj, 1033, base, None)                                          # sin excepción
    finally:
        pygame.mouse.set_cursor = original


# ================================================================ punta a punta
def probar_una_partida_perdida_con_demora_muestra_el_golpe_mortal_en_rojo_sin_duplicarlo():
    import os
    from ayudas_controladores import CONFIG_OFFLINE
    from ayudas_pygame import crear_fabrica, tecla
    from UIController.ControladorPygame import ControladorPygame
    reloj = RelojQueAvanza()
    vista = VistaPygame(animaciones=True, reloj=reloj)
    with Recorrido(vista) as recorrido:
        recorrido.controlador = ControladorPygame(vista, CONFIG_OFFLINE,
                                                  crear_fabrica(recorrido.carpeta, os.path.join(recorrido.carpeta, "puntajes.jsonl")),
                                                  demora_fin_ms=1500, reloj_ms=lambda: reloj.ahora)
        cuadros_vistos = []                                                                # (pantalla, terminado, ahora, números del jugador)
        dibujar = vista.dibujar

        def dibujando(pantalla):
            dibujar(pantalla)
            propios = ([(a.inicio, a.imagen) for a in vista._efectos._anims if a.tipo == "numero" and a.del_jugador]
                       if vista._efectos is not None else [])
            cuadros_vistos.append((pantalla.pantalla, pantalla.estado is not None and pantalla.estado.terminado, reloj.ahora, propios))
        vista.dibujar = dibujando
        pasos = [[tecla(pygame.K_RETURN)], [tecla(pygame.K_RETURN)]] + [[tecla(pygame.K_BACKSPACE)]] * 16 + \
                [[tecla(ord("a"), caracter="a")], [tecla(pygame.K_RETURN)], [tecla(pygame.K_UP)]]
        contador = {"n": 0}

        def eventos():
            contador["n"] += 1
            if cuadros_vistos and cuadros_vistos[-1][0] == "derrota":
                return [pygame.event.Event(pygame.QUIT)]
            if contador["n"] <= len(pasos):
                return pasos[contador["n"] - 1]
            terminado = bool(cuadros_vistos) and cuadros_vistos[-1][:2] == ("juego", True)
            assert contador["n"] < 600, "la partida no terminó"                              # (nunca un bucle sin fin)
            return [] if terminado else [tecla(pygame.K_z)]
        recorrido.controlador.ejecutar(eventos)
        finales = [cv for cv in cuadros_vistos if cv[:2] == ("juego", True)]
        assert finales, "la partida no terminó"
        primero = finales[0]
        letales = [ini for ini, _ in primero[3] if ini == primero[2]]
        assert len(letales) == 1, (primero[2], [ini for ini, _ in primero[3]])             # el golpe mortal: un número rojo, en el cuadro del golpe
        assert hay_pixeles([img for ini, img in primero[3] if ini == primero[2]][0], c.NUMERO_ROJO)
        for cv in finales:
            assert all(ini <= primero[2] for ini, _ in cv[3]), cv                          # y ninguno nuevo mientras dura la demora
        assert any(cv[3] for cv in finales[1:10])                                          # sigue en pantalla durante la demora


if __name__ == "__main__":
    probar_las_curvas_del_feedback_van_del_principio_al_fin_y_aguantan_cualquier_valor()
    probar_las_duraciones_y_medidas_del_feedback_son_las_pedidas_y_viven_en_componentes()
    probar_el_numero_sale_sobre_el_actor_golpeado_por_su_id_aunque_cambie_el_orden_de_la_lista()
    probar_curar_saca_un_numero_verde_sin_destello_ni_borde_y_el_jugador_herido_sale_en_rojo_con_borde()
    probar_el_numero_sube_36_px_en_700_ms_y_desaparece_y_el_cuadro_lo_dibuja_visible()
    probar_el_golpe_mortal_al_protagonista_se_ve_aunque_la_partida_ya_termino_y_no_se_duplica()
    probar_el_enemigo_que_desaparece_muere_en_450_ms_la_rata_se_encoge_y_el_generico_usa_sus_4_fotogramas()
    probar_el_objeto_recogido_se_desvanece_subiendo_y_con_ids_repetidos_solo_desaparece_uno()
    probar_la_puerta_cerrada_que_se_abre_se_desvanece_y_solo_la_de_la_sala_de_salida_brilla()
    probar_el_primer_cuadro_y_el_reloj_que_retrocede_reinician_la_memoria_sin_animar()
    probar_cambiar_de_sala_conserva_solo_lo_del_protagonista_si_es_contigua_y_borra_todo_si_no()
    probar_al_mostrar_menus_y_pantallas_de_fin_la_memoria_se_borra_y_la_pausa_la_congela()
    probar_la_memoria_no_pasa_de_24_animaciones_y_se_olvidan_las_mas_viejas()
    probar_ninguna_animacion_de_combate_registra_zonas_y_las_zonas_son_las_mismas_con_y_sin_animaciones()
    probar_la_cache_no_crece_con_las_animaciones_de_combate_en_marcha()
    probar_el_cursor_es_una_mano_sobre_lo_pulsable_solo_al_cambiar_y_un_fallo_del_sistema_no_rompe_nada()
    probar_una_partida_perdida_con_demora_muestra_el_golpe_mortal_en_rojo_sin_duplicarlo()
    print("OK: todas las pruebas del feedback de combate pasaron")

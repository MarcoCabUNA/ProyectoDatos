import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import crear_backend, crear_partida, paquete_con_otra_version  # noqa: E402  (también deja la raíz en sys.path)

from Data.ClienteHttp import ErrorRed  # noqa: E402
from DTO.Direcciones import N, O, S  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from DTO.ResultadoBenchDTO import ResultadoBenchDTO  # noqa: E402
from Service.ServicioBench import ServicioBench  # noqa: E402
from UIController.ControladorBackend import (CRITERIOS_INVENTARIO, CRITERIOS_PUNTAJES, LARGO_MAXIMO_NOMBRE,  # noqa: E402
                                             ErrorOperacion)


class Carpeta:
    """Una carpeta temporal que se borra sola: 'with Carpeta() as ruta:'."""

    def __enter__(self):
        self.ruta = tempfile.mkdtemp()
        return self.ruta

    def __exit__(self, *_):
        shutil.rmtree(self.ruta, ignore_errors=True)


class _PartidaQueFallaAlArmarElEstado(ServicioPartida):
    """Un ServicioPartida real cuyo estado() falla (como si la red se cayera al pedir una ficha) cuando se le dice."""
    fallar = False

    def estado(self, contexto):
        if self.fallar:
            raise ErrorRed("armar el estado", "sin conexión")
        return super().estado(contexto)


def _debe_fallar(funcion, trozo_del_mensaje=None):
    try:
        funcion()
    except ErrorOperacion as error:
        if trozo_del_mensaje is not None:
            assert trozo_del_mensaje in str(error), str(error)
        return
    raise AssertionError("Debió lanzar ErrorOperacion")


def _jugar_hasta_el_final(backend):
    """Entra a la sala de las ratas y espera: las ratas ganan siempre en este paquete."""
    backend.mover(N)
    for _ in range(100):
        estado = backend.esperar()
        if estado.terminado:
            return estado
    raise AssertionError("la partida no terminó")


# ---------------------------------------------------------------- sin partida
def probar_sin_partida_todo_lo_que_la_necesita_falla_con_un_mensaje():
    with Carpeta() as c:
        b = crear_backend(c)
        assert b.hay_partida() is False
        for operacion in (lambda: b.estado(), lambda: b.mover(N), lambda: b.esperar(), lambda: b.atacar("e-1"),
                          lambda: b.recoger("itm"), lambda: b.retroceder(), lambda: b.inventario(),
                          lambda: b.inventario_siguiente(), lambda: b.inventario_ordenar("peso"),
                          lambda: b.guardar(os.path.join(c, "x.sav")), lambda: b.finalizar(), lambda: b.reporte()):
            _debe_fallar(operacion, "No hay una partida en curso")


def probar_las_criptas_salen_del_paquete():
    with Carpeta() as c:
        criptas = crear_backend(c).criptas()
        del_paquete = json.loads((Path(__file__).resolve().parent.parent / "paquete" / "criptas.json")
                                 .read_text(encoding="utf-8"))["criptas"]          # las que tenga el paquete, en su orden
        assert [x.id for x in criptas] == [d["id"] for d in del_paquete]
        assert [x.nombre for x in criptas] == [d["nombre"] for d in del_paquete]
        assert criptas[0].id == "cripta-01" and criptas[0].nombre == "Osario menor"


# ---------------------------------------------------------------- validación de forma
def probar_iniciar_valida_la_forma():
    with Carpeta() as c:
        b = crear_backend(c)
        _debe_fallar(lambda: b.iniciar("", "Ana"), "cripta")
        _debe_fallar(lambda: b.iniciar("   ", "Ana"), "cripta")
        _debe_fallar(lambda: b.iniciar(None, "Ana"), "cripta")
        _debe_fallar(lambda: b.iniciar("cripta-01", ""), "nombre")
        _debe_fallar(lambda: b.iniciar("cripta-01", "   "), "nombre")
        _debe_fallar(lambda: b.iniciar("cripta-01", "x" * (LARGO_MAXIMO_NOMBRE + 1)), "caracteres")
        _debe_fallar(lambda: b.iniciar("cripta-01", "Ana\nPérez"), "caracteres")
        assert b.hay_partida() is False                            # nada de lo anterior llegó a crear una partida
        b.iniciar("cripta-01", "x" * LARGO_MAXIMO_NOMBRE)          # justo en el límite sí vale


def probar_iniciar_con_cripta_inexistente_es_un_error_de_operacion_y_no_deja_partida():
    with Carpeta() as c:
        b = crear_backend(c)
        _debe_fallar(lambda: b.iniciar("cripta-99", "Ana"))
        assert b.hay_partida() is False


def probar_el_nombre_se_recorta():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "  Ana  ")
        _jugar_hasta_el_final(b)
        assert b.finalizar().nombre == "Ana"


def probar_direcciones_con_forma_invalida():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        for mala in (-1, 4, 99, "N", None, 1.0, True):
            _debe_fallar(lambda: b.mover(mala), "Dirección inválida")
            _debe_fallar(lambda: b.abrir(mala), "Dirección inválida")
        assert b.estado().reloj == 0                                # ninguna llegó al motor: no pasó el tiempo


def probar_ids_vacios_o_sin_forma():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        for accion in (b.atacar, b.recoger, b.soltar, b.equipar, b.usar):
            for malo in ("", "  ", None, 5):
                _debe_fallar(lambda: accion(malo))
        assert b.estado().reloj == 0


def probar_criterios_con_forma_invalida():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        _debe_fallar(lambda: b.inventario_ordenar("color"), "Criterio de inventario")
        _debe_fallar(lambda: b.tabla_puntajes("color"), "Criterio de puntajes")
        _debe_fallar(lambda: b.tabla_puntajes(None), "Criterio de puntajes")
        for criterio in CRITERIOS_INVENTARIO:
            assert b.inventario_ordenar(criterio).criterio == criterio
        for criterio in CRITERIOS_PUNTAJES:
            assert b.tabla_puntajes(criterio) == []


def probar_los_errores_de_forma_no_mueven_la_partida():
    with Carpeta() as c:
        b = crear_backend(c)
        antes = b.iniciar("cripta-01", "Ana")
        _debe_fallar(lambda: b.mover(9))
        assert b.estado() == antes


# ---------------------------------------------------------------- acciones y reglas del juego
def probar_mover_recoger_y_esperar_cambian_el_estado():
    with Carpeta() as c:
        b = crear_backend(c)
        inicial = b.iniciar("cripta-01", "Ana")
        assert inicial.sala.nombre == "Entrada derruida" and [o.id for o in inicial.objetos_suelo] == ["itm_antorcha"]
        estado = b.recoger("itm_antorcha")
        assert estado.resultado is None and [o.id for o in estado.inventario.objetos] == ["itm_antorcha"]
        assert estado.objetos_suelo == [] and estado.reloj > 0
        estado = b.mover(N)
        assert estado.sala.id == 2 and len(estado.enemigos) == 2
        assert b.estado().sala.id == 2                                # estado() devuelve lo mismo que dejó la acción


def probar_una_accion_rechazada_trae_su_motivo_y_no_consume_tiempo():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        antes = b.estado().reloj
        for accion, texto in ((lambda: b.mover(O), "No hay salida"), (lambda: b.abrir(N), "nada que abrir"),
                              (lambda: b.atacar("e-999"), "enemigo"), (lambda: b.recoger("itm_no_existe"), "objeto"),
                              (lambda: b.equipar("itm_antorcha"), "objeto"), (lambda: b.retroceder(), "pergamino")):
            estado = accion()
            assert estado.resultado is not None and texto in estado.resultado, (texto, estado.resultado)
            assert estado.reloj == antes and not estado.terminado


def probar_inventario_recorrer_y_ordenar_no_son_acciones_del_jugador():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        b.recoger("itm_antorcha")
        reloj = b.estado().reloj
        assert b.inventario().capacidad == 1
        assert b.inventario_siguiente().cursor == 0 and b.inventario_anterior().cursor == 0
        assert b.inventario_ordenar("nombre").criterio == "nombre"
        assert b.estado().inventario.criterio == "nombre"            # la vista elegida persiste en el estado
        assert b.inventario_ordenar(None).criterio is None
        assert b.estado().reloj == reloj


def probar_la_partida_termina_y_ya_no_acepta_acciones():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        final = _jugar_hasta_el_final(b)
        assert final.terminado and final.resultado == "derrota"
        despues = b.mover(S)
        assert despues.terminado and despues.reloj == final.reloj      # con la partida terminada nada cambia


def probar_atacar_llega_al_motor_y_golpea_al_enemigo_elegido():
    """Las ratas actúan antes que el jugador (t=66 contra t=100) y no pueden matarlo antes: el golpe siempre ocurre."""
    with Carpeta() as c:
        for posicion, nombre in ((0, "Rata gigante #1"), (1, "Rata gigante #2")):
            b = crear_backend(c)
            b.iniciar("cripta-01", "Ana")
            enemigos = b.mover(N).enemigos
            assert [e.nombre for e in enemigos] == ["Rata gigante #1", "Rata gigante #2"]
            estado = b.atacar(enemigos[posicion].id)
            assert any(f"Jugador ataca a {nombre}" in mensaje for mensaje in estado.mensajes), (nombre, estado.mensajes)


def probar_recoger_soltar_equipar_y_usar_llegan_al_motor_cada_uno_con_su_accion():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        estado = b.recoger("itm_antorcha")
        assert [o.id for o in estado.inventario.objetos] == ["itm_antorcha"] and estado.objetos_suelo == []
        estado = b.equipar("itm_antorcha")                                  # una antorcha no se equipa
        assert "no se puede equipar" in estado.resultado and len(estado.inventario.objetos) == 1
        estado = b.soltar("itm_antorcha")                                   # vuelve al suelo
        assert estado.resultado is None and estado.inventario.objetos == []
        assert [o.id for o in estado.objetos_suelo] == ["itm_antorcha"]
        b.recoger("itm_antorcha")
        estado = b.usar("itm_antorcha")                                     # se consume y se enciende
        assert estado.resultado is None and estado.inventario.objetos == []
        assert [e.tipo for e in estado.efectos] == ["antorcha"]


def probar_si_falla_armar_el_estado_no_queda_una_partida_a_medias_ni_se_pierde_la_anterior():
    with Carpeta() as c:
        partida = crear_partida(c, clase=_PartidaQueFallaAlArmarElEstado)
        b = crear_backend(c, partida=partida)
        partida.fallar = True
        _debe_fallar(lambda: b.iniciar("cripta-01", "Ana"), "sin conexión")
        assert b.hay_partida() is False                                     # nada a medias
        partida.fallar = False
        assert b.iniciar("cripta-01", "Ana").sala.id == 1
        assert b.mover(N).sala.id == 2
        partida.fallar = True
        _debe_fallar(lambda: b.iniciar("cripta-01", "Luis"), "sin conexión")
        _debe_fallar(lambda: b.cargar(os.path.join(c, "x.sav"), "Luis"))
        partida.fallar = False
        assert b.hay_partida() and b.estado().sala.id == 2                  # la partida anterior sigue intacta


def probar_una_segunda_partida_en_el_mismo_backend_tambien_registra_su_puntaje():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        _jugar_hasta_el_final(b)
        primero = b.finalizar()
        b.iniciar("cripta-01", "Luis")                                      # otra partida, mismo controlador
        _debe_fallar(lambda: b.finalizar(), "todavía no ha terminado")      # la terminada anterior ya no cuenta
        _jugar_hasta_el_final(b)
        segundo = b.finalizar()
        assert (primero.nombre, segundo.nombre) == ("Ana", "Luis")
        assert [p.nombre for p in b.tabla_puntajes("nombre")] == ["Ana", "Luis"]


# ---------------------------------------------------------------- puntajes
def probar_finalizar_exige_partida_terminada_y_registra_una_sola_vez():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        _debe_fallar(lambda: b.finalizar(), "todavía no ha terminado")
        assert b.tabla_puntajes() == []
        _jugar_hasta_el_final(b)
        primero = b.finalizar()
        segundo = b.finalizar()
        assert primero == segundo and primero.mazmorra == "cripta-01" and primero.acciones >= 2
        assert b.tabla_puntajes() == [primero]                         # una sola fila aunque se llamó dos veces


def probar_los_puntajes_sobreviven_y_se_ordenan():
    with Carpeta() as c:
        for nombre in ("Zoe", "Ana"):
            b = crear_backend(c)
            b.iniciar("cripta-01", nombre)
            _jugar_hasta_el_final(b)
            b.finalizar()
        nuevo = crear_backend(c)                                       # otra ejecución: lee la tabla del archivo
        assert [p.nombre for p in nuevo.tabla_puntajes("nombre")] == ["Ana", "Zoe"]
        assert [p.nombre for p in nuevo.tabla_puntajes("enemigos")] == ["Zoe", "Ana"]   # empate: orden en que se jugaron


def probar_una_tabla_danada_es_un_error_de_operacion():
    with Carpeta() as c:
        b = crear_backend(c)
        with open(os.path.join(c, "puntajes.jsonl"), "w", encoding="utf-8") as archivo:
            archivo.write("esto no es json\n")
        _debe_fallar(lambda: b.tabla_puntajes())


def probar_el_reporte_trae_solicitudes_y_cache():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        reporte = b.reporte()
        assert reporte.offline is True and reporte.solicitudes_realizadas == 0     # offline: no cuenta solicitudes
        assert reporte.presupuesto is not None and reporte.presupuesto > 0           # lo declara la cripta
        b.mover(N)                                                                   # entrar a una sala resuelve fichas
        despues = b.reporte()
        assert despues.aciertos_cache + despues.fallos_cache > reporte.aciertos_cache + reporte.fallos_cache


# ---------------------------------------------------------------- guardar y cargar
def probar_guardar_y_cargar_restauran_la_partida():
    with Carpeta() as c:
        ruta = os.path.join(c, "saves", "p.sav")
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        b.recoger("itm_antorcha")
        guardado = b.estado()
        assert b.guardar(ruta) > 0 and os.path.exists(ruta)
        b.mover(N)                                                      # sigue jugando después de guardar
        nuevo = crear_backend(c)
        cargado = nuevo.cargar(ruta, "Ana")
        assert nuevo.hay_partida()
        assert cargado.sala == guardado.sala and cargado.reloj == guardado.reloj
        assert cargado.jugador == guardado.jugador
        assert [o.id for o in cargado.inventario.objetos] == ["itm_antorcha"]
        assert nuevo.mover(N).sala.id == 2                              # y se puede seguir jugando


def probar_cargar_con_error_no_toca_la_partida_en_curso():
    with Carpeta() as c:
        b = crear_backend(c)
        antes = b.iniciar("cripta-01", "Ana")
        _debe_fallar(lambda: b.cargar(os.path.join(c, "no_existe.sav"), "Ana"), "no existe")
        _debe_fallar(lambda: b.cargar("", "Ana"), "archivo")
        _debe_fallar(lambda: b.cargar(os.path.join(c, "x.sav"), ""), "nombre")
        with open(os.path.join(c, "malo.sav"), "wb") as archivo:
            archivo.write(b"esto no es una partida")
        _debe_fallar(lambda: b.cargar(os.path.join(c, "malo.sav"), "Ana"))
        assert b.hay_partida() and b.estado() == antes


def probar_guardar_con_ruta_vacia():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        _debe_fallar(lambda: b.guardar(""), "Falta indicar dónde guardar")


# ---------------------------------------------------------------- modos sin interfaz
def probar_reproducir_repite_exactamente_la_partida():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        b.recoger("itm_antorcha")
        final = _jugar_hasta_el_final(b)
        ruta = os.path.join(c, "logs", sorted(os.listdir(os.path.join(c, "logs")))[0])
        avances = []
        resultado = crear_backend(c).reproducir(ruta, lambda n, accion, estado: avances.append((n, accion.tipo)))
        assert resultado.acciones_reproducidas == len(avances) >= 3
        assert avances[0] == (1, "recoger")
        assert resultado.estado_final.reloj == final.reloj and resultado.estado_final.resultado == "derrota"
        assert resultado.estado_final.jugador == final.jugador


def probar_reproducir_con_log_inexistente_o_sin_forma():
    with Carpeta() as c:
        b = crear_backend(c)
        _debe_fallar(lambda: b.reproducir(os.path.join(c, "no_existe.log")), "no existe")
        _debe_fallar(lambda: b.reproducir(""), "Falta indicar el archivo del log")
        with open(os.path.join(c, "malo.log"), "w", encoding="utf-8") as archivo:
            archivo.write("basura\n")
        _debe_fallar(lambda: b.reproducir(os.path.join(c, "malo.log")))


def probar_una_partida_guardada_con_otra_version_de_la_cripta_se_rechaza():
    """Apéndice B: no se continúa en silencio con datos distintos a los que se guardaron."""
    with Carpeta() as c:
        ruta = os.path.join(c, "p.sav")
        original = crear_backend(c)
        original.iniciar("cripta-01", "Ana")
        original.guardar(ruta)
        otra = crear_backend(c, paquete=paquete_con_otra_version(c))
        _debe_fallar(lambda: otra.cargar(ruta, "Ana"), "No se puede continuar esa partida")
        assert otra.hay_partida() is False
        assert crear_backend(c).cargar(ruta, "Ana").sala.id == 1          # con la versión original sí carga


def probar_un_log_grabado_con_otra_version_no_se_reproduce_y_no_ejecuta_nada():
    """§4.11: si la versión no coincide, se avisa que no se puede garantizar una reproducción fiel."""
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        b.recoger("itm_antorcha")
        b.esperar()
        carpeta_logs = os.path.join(c, "logs")
        ruta = os.path.join(carpeta_logs, os.listdir(carpeta_logs)[0])
        acciones = []
        otra = crear_backend(c, paquete=paquete_con_otra_version(c))
        _debe_fallar(lambda: otra.reproducir(ruta, lambda n, a, e: acciones.append(n)), "garantizar una reproducción fiel")
        assert acciones == []                                              # ni una sola acción se ejecutó


def probar_reproducir_no_crea_logs_ni_puntajes():
    with Carpeta() as c:
        b = crear_backend(c)
        b.iniciar("cripta-01", "Ana")
        _jugar_hasta_el_final(b)
        carpeta_logs = os.path.join(c, "logs")
        ruta = os.path.join(carpeta_logs, os.listdir(carpeta_logs)[0])
        antes = sorted(os.listdir(carpeta_logs))
        crear_backend(c).reproducir(ruta)
        assert sorted(os.listdir(carpeta_logs)) == antes
        assert not os.path.exists(os.path.join(c, "puntajes.jsonl"))


def probar_medir_usa_el_servicio_de_mediciones_y_avisa_el_avance():
    fila = ResultadoBenchDTO("x", "caso", 1, 0.1, 0.2, "nota")
    with Carpeta() as c:
        b = crear_backend(c, bench=ServicioBench([lambda: [fila], lambda: []]))
        avances = []
        assert b.medir(lambda numero, total: avances.append((numero, total))) == [fila]
        assert avances == [(1, 2), (2, 2)]
        assert "caso" in b.tabla_mediciones([fila]) and "mejor ms" in b.tabla_mediciones([fila])


# ---------------------------------------------------------------- arquitectura
def probar_el_controlador_no_importa_pygame_ni_capas_prohibidas():
    """La Interfaz solo habla con Servicios (y DTO): ni Datos, ni Lógica, ni pygame en el backend (§6, §7)."""
    raiz = Path(__file__).resolve().parent.parent
    for nombre in ("ControladorBackend.py",):
        texto = (raiz / "UIController" / nombre).read_text(encoding="utf-8")
        for linea in texto.splitlines():
            if linea.startswith(("import ", "from ")):
                assert not linea.startswith(("from Data", "from Logic", "import Data", "import Logic")), (nombre, linea)
                if nombre == "ControladorBackend.py":
                    assert "pygame" not in linea, linea
        assert "dict(" not in texto and "sorted(" not in texto and ".sort(" not in texto, nombre


if __name__ == "__main__":
    probar_sin_partida_todo_lo_que_la_necesita_falla_con_un_mensaje()
    probar_las_criptas_salen_del_paquete()
    probar_iniciar_valida_la_forma()
    probar_iniciar_con_cripta_inexistente_es_un_error_de_operacion_y_no_deja_partida()
    probar_el_nombre_se_recorta()
    probar_direcciones_con_forma_invalida()
    probar_ids_vacios_o_sin_forma()
    probar_criterios_con_forma_invalida()
    probar_los_errores_de_forma_no_mueven_la_partida()
    probar_mover_recoger_y_esperar_cambian_el_estado()
    probar_una_accion_rechazada_trae_su_motivo_y_no_consume_tiempo()
    probar_inventario_recorrer_y_ordenar_no_son_acciones_del_jugador()
    probar_la_partida_termina_y_ya_no_acepta_acciones()
    probar_atacar_llega_al_motor_y_golpea_al_enemigo_elegido()
    probar_recoger_soltar_equipar_y_usar_llegan_al_motor_cada_uno_con_su_accion()
    probar_si_falla_armar_el_estado_no_queda_una_partida_a_medias_ni_se_pierde_la_anterior()
    probar_una_segunda_partida_en_el_mismo_backend_tambien_registra_su_puntaje()
    probar_finalizar_exige_partida_terminada_y_registra_una_sola_vez()
    probar_los_puntajes_sobreviven_y_se_ordenan()
    probar_una_tabla_danada_es_un_error_de_operacion()
    probar_el_reporte_trae_solicitudes_y_cache()
    probar_guardar_y_cargar_restauran_la_partida()
    probar_cargar_con_error_no_toca_la_partida_en_curso()
    probar_guardar_con_ruta_vacia()
    probar_reproducir_repite_exactamente_la_partida()
    probar_reproducir_con_log_inexistente_o_sin_forma()
    probar_una_partida_guardada_con_otra_version_de_la_cripta_se_rechaza()
    probar_un_log_grabado_con_otra_version_no_se_reproduce_y_no_ejecuta_nada()
    probar_reproducir_no_crea_logs_ni_puntajes()
    probar_medir_usa_el_servicio_de_mediciones_y_avisa_el_avance()
    probar_el_controlador_no_importa_pygame_ni_capas_prohibidas()
    print("OK: todas las pruebas de ControladorBackend pasaron")
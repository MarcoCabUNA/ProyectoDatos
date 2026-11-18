"""
Pruebas de los DTO de la línea de tiempo (feature 004): ResumenHistoriaDTO (T009) y LineaTiempoDTO (T010).
"""
import dataclasses
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_terreno import ficha_cazador, salida, salidas_con_costos
from TestPartidaGuardadaDTO import partida_de_ejemplo, sala_de_ejemplo
from DTO.ActorDTO import ActorDTO
from DTO.EfectoDTO import EfectoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.LineaTiempoDTO import (AccionGuardadaDTO, LineaTiempoGuardadaDTO, PuntoControlGuardadoDTO,
                                RegistroCargaGuardadoDTO)
from DTO.ObjetoDTO import ObjetoDTO
from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO


def _resumen(**cambios) -> ResumenHistoriaDTO:
    jugador = ActorDTO("jugador", "jugador", "Ana", 20, 30, 5, 2, 100, 3)
    datos = dict(reloj=740, sala_id=3, sala_nombre="Sala 3", jugador=jugador, inventario=["itm_daga"],
                 arma_equipada=None, armadura_equipada=None, efectos=[EfectoDTO("veneno", 200, 2)],
                 enemigos=[])
    datos.update(cambios)
    return ResumenHistoriaDTO(**datos)


class PruebasResumenHistoriaDTO(unittest.TestCase):

    def test_resumen_no_tiene_cursor_ni_mensajes_fr406(self):
        campos = [campo.name for campo in dataclasses.fields(ResumenHistoriaDTO)]
        for prohibido in ("cursor", "mensajes", "mensaje", "criterio"):
            self.assertNotIn(prohibido, campos)
        self.assertIn("inventario", campos)                              # el inventario sí, sin cursor
        resumen = _resumen()
        self.assertFalse(hasattr(resumen, "cursor"))
        self.assertFalse(hasattr(resumen, "mensajes"))

    def test_resumen_mapa_conocido_es_opcional_fr405(self):
        self.assertIsNone(_resumen().mapa_conocido)                      # ausente hasta que exista la spec 002
        self.assertEqual(_resumen(mapa_conocido="mapa").mapa_conocido, "mapa")

    def test_resumen_es_inmutable_y_trae_los_valores_por_defecto_fr412(self):
        resumen = _resumen()
        self.assertFalse(resumen.terminada_antes)
        self.assertIsNone(resumen.instante_pedido)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            resumen.reloj = 1                                            # type: ignore[misc]


# ---------- T010: LineaTiempoGuardadaDTO

def _linea_guardada(k: int = 3, acciones: int = 6, posiciones: tuple = (0, 3, 6)) -> LineaTiempoGuardadaDTO:
    """Una línea guardada de ejemplo: `acciones` acciones, puntos en `posiciones`, dos cargas y tres fichas."""
    lista = [AccionGuardadaDTO(100 * (i + 1), "esperar") for i in range(acciones)]
    lista[0] = AccionGuardadaDTO(100, "mover", direccion=2)
    lista[1] = AccionGuardadaDTO(200, "atacar", objetivo="e-201")
    lista[2] = AccionGuardadaDTO(300, "recoger", objeto="itm_pocion")
    puntos = [PuntoControlGuardadoDTO(p, partida_de_ejemplo(), [sala_de_ejemplo()]) for p in posiciones]
    salas = salidas_con_costos(2, [salida(1, 2, 2, 100)])
    cargas = [RegistroCargaGuardadoDTO(0, salas[0]), RegistroCargaGuardadoDTO(2, salas[1])]
    fichas = [ficha_cazador(3),
              FichaTrampaDTO.desde_diccionario({"id": "trp_pinchos", "clase": "trampa", "nombre": "Pinchos",
                                                "daño": 4, "rearme": 300}),
              ObjetoDTO.desde_diccionario({"id": "itm_pocion", "clase": "pocion", "nombre": "Poción",
                                           "peso": 1, "valor": 5, "cura": 10})]
    return LineaTiempoGuardadaDTO(k, lista, puntos, cargas, fichas)


class PruebasLineaTiempoGuardadaDTO(unittest.TestCase):

    def test_linea_guardada_ida_y_vuelta_fr420(self):
        linea = _linea_guardada()
        por_json = json.loads(json.dumps(linea.a_diccionario()))          # como si pasara por disco
        self.assertEqual(LineaTiempoGuardadaDTO.desde_diccionario(por_json), linea)
        vacia = LineaTiempoGuardadaDTO(5, [], [], [], [])                 # una línea sin nada también viaja
        self.assertEqual(LineaTiempoGuardadaDTO.desde_diccionario(vacia.a_diccionario()), vacia)

    def test_linea_guardada_solo_lleva_k_acciones_puntos_cargas_y_fichas_fr420(self):
        campos = [campo.name for campo in dataclasses.fields(LineaTiempoGuardadaDTO)]
        self.assertEqual(campos, ["k", "acciones", "puntos", "cargas", "fichas"])   # sin marcadores de pergamino

    def test_linea_guardada_rechaza_orden_invalido_fr420(self):
        d = _linea_guardada().a_diccionario()
        d["acciones"][0], d["acciones"][1] = d["acciones"][1], d["acciones"][0]       # tiempos decrecientes
        with self.assertRaises(ValueError):
            LineaTiempoGuardadaDTO.desde_diccionario(d)
        d = _linea_guardada().a_diccionario()
        d["puntos"][1], d["puntos"][2] = d["puntos"][2], d["puntos"][1]               # puntos desordenados
        with self.assertRaises(ValueError):
            LineaTiempoGuardadaDTO.desde_diccionario(d)

    def test_linea_guardada_rechaza_k_invalido_fr420(self):
        for malo in (0, -1, 2.5, "3", None, True):
            d = _linea_guardada().a_diccionario()
            d["k"] = malo
            with self.assertRaises(ValueError):
                LineaTiempoGuardadaDTO.desde_diccionario(d)

    def test_linea_guardada_rechaza_punto_invalido_fr420(self):
        casos = {
            "posición repetida": _linea_guardada(posiciones=(0, 3, 3)),
            "posición fuera de rango": _linea_guardada(posiciones=(0, 3, 7)),
            "posición negativa": _linea_guardada(posiciones=(-1, 3, 6)),
            "más de k acciones entre dos puntos": _linea_guardada(k=3, posiciones=(0, 4, 6)),
        }
        for nombre, linea in casos.items():
            with self.subTest(nombre):
                with self.assertRaises(ValueError):
                    LineaTiempoGuardadaDTO.desde_diccionario(linea.a_diccionario())

    def test_linea_guardada_acepta_puntos_mas_cerca_que_k_tras_un_pergamino_fr420(self):
        linea = _linea_guardada(k=3, posiciones=(0, 2, 5))               # un pergamino dejó el punto en 2
        self.assertEqual(LineaTiempoGuardadaDTO.desde_diccionario(linea.a_diccionario()), linea)

    def test_linea_guardada_rechaza_ficha_de_clase_desconocida_fr420(self):
        d = _linea_guardada().a_diccionario()
        d["fichas"][0]["clase"] = "dragon"
        with self.assertRaises(ValueError):
            LineaTiempoGuardadaDTO.desde_diccionario(d)


if __name__ == "__main__":
    unittest.main()

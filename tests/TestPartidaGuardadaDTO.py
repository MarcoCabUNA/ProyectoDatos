"""
Pruebas de DTO/PartidaGuardadaDTO.py (DTOs del guardado, enunciado §4.10).
Comprueban que el estado pasa por JSON sin cambiar (será la base de la comparación contra el
formato binario) y que el estado del azar guardado continúa la misma secuencia.
"""
import dataclasses
import json
import random
import unittest

from DTO.PartidaGuardadaDTO import (ContadorTipoDTO, EfectoGuardadoDTO, EnemigoGuardadoDTO,
                                    EventoGuardadoDTO, InventarioGuardadoDTO, JugadorGuardadoDTO,
                                    PartidaGuardadaDTO, SalaGuardadaDTO, TrampaGuardadaDTO)


def partida_de_ejemplo(azar: random.Random | None = None) -> PartidaGuardadaDTO:
    version, estado, gauss = (azar or random.Random(12345)).getstate()
    return PartidaGuardadaDTO(
        id_cripta="cripta-01", version_cripta="fd58f7743b9e", version_catalogo="be68d322d2f5", semilla=12345,
        reloj=740, siguiente_secuencia=31, enemigos_derrotados=1, terminado=False, victoria=False,
        salida_abierta=False, azar_version=version, azar_estado=list(estado), azar_gauss=gauss,
        jugador=JugadorGuardadoDTO(vida=22, vida_max=30, ataque=6, defensa=2, velocidad=125,
                                   sala_actual=3, acciones=9),
        inventario=InventarioGuardadoDTO(objetos=["itm_daga", "itm_daga", "itm_cota"], cursor=1,
                                         arma=1, armadura=2),
        rastro=[None, 0, 300, 700, None, None, None],
        contadores_tipo=[ContadorTipoDTO("ene_rata", 2)],
        efectos=[EfectoGuardadoDTO("velocidad", "jugador", 300, 25, 900, cambio_real=25),
                 EfectoGuardadoDTO("velocidad", "jugador", 300, 25, 1000, cambio_real=25),
                 EfectoGuardadoDTO("antorcha", "jugador", 500, None, 1100)],
        eventos=[EventoGuardadoDTO(740, 30, "accion_actor", actor="jugador"),
                 EventoGuardadoDTO(780, 29, "accion_actor", actor="e-201"),
                 EventoGuardadoDTO(900, 20, "velocidad", efecto=0),
                 EventoGuardadoDTO(1000, 25, "velocidad", efecto=1),          # dos del mismo tipo
                 EventoGuardadoDTO(820, 27, "rearme_trampa", sala=3, trampa="t-301"),
                 EventoGuardadoDTO(850, 28, "cierre_puerta", sala=2, direccion=2)],
        ruta_log="logs/partida_001.log", acciones_en_log=9,
    )


def sala_de_ejemplo() -> SalaGuardadaDTO:
    return SalaGuardadaDTO(3, True, [False, True, False, False], ["itm_pocion"],
                           [TrampaGuardadaDTO("t-301", "trp_pinchos", False)],
                           [EnemigoGuardadoDTO("e-201", "ene_rata", 4, 100, 2, True)])


class PruebasPartidaGuardadaDTO(unittest.TestCase):

    def test_partida_ida_y_vuelta_por_json(self):
        p = partida_de_ejemplo()
        texto = json.dumps(p.a_diccionario())
        self.assertEqual(PartidaGuardadaDTO.desde_diccionario(json.loads(texto)), p)

    def test_sala_ida_y_vuelta_por_json(self):
        s = sala_de_ejemplo()
        self.assertEqual(SalaGuardadaDTO.desde_diccionario(json.loads(json.dumps(s.a_diccionario()))), s)

    def test_sala_sin_contenido_por_defecto(self):
        s = SalaGuardadaDTO(5, False)
        self.assertEqual((s.puertas_cerradas, s.objetos, s.trampas, s.enemigos), ([False] * 4, [], [], []))
        self.assertIsNot(s.puertas_cerradas, SalaGuardadaDTO(6, False).puertas_cerradas)   # no comparten la lista

    def test_el_azar_guardado_continua_la_misma_secuencia(self):
        azar = random.Random(12345)
        for _ in range(37):
            azar.randint(0, 4)
        p = PartidaGuardadaDTO.desde_diccionario(json.loads(json.dumps(partida_de_ejemplo(azar).a_diccionario())))
        esperado = [azar.randint(0, 4) for _ in range(50)]
        recuperado = random.Random()
        recuperado.setstate((p.azar_version, tuple(p.azar_estado), p.azar_gauss))    # lo que hará Marco
        self.assertEqual([recuperado.randint(0, 4) for _ in range(50)], esperado)

    def test_el_azar_con_gauss_pendiente(self):
        azar = random.Random(7)
        azar.gauss(0, 1)                    # deja un valor guardado en gauss_next
        p = partida_de_ejemplo(azar)
        self.assertIsNotNone(p.azar_gauss)
        recuperado = random.Random()
        q = PartidaGuardadaDTO.desde_diccionario(json.loads(json.dumps(p.a_diccionario())))
        recuperado.setstate((q.azar_version, tuple(q.azar_estado), q.azar_gauss))
        self.assertEqual(recuperado.gauss(0, 1), azar.gauss(0, 1))

    def test_valores_por_defecto(self):
        p = partida_de_ejemplo()
        minima = dataclasses.replace(p, rastro=[], contadores_tipo=[], efectos=[], eventos=[],
                                     ruta_log=None, acciones_en_log=0)
        self.assertEqual(PartidaGuardadaDTO.desde_diccionario(minima.a_diccionario()), minima)
        self.assertEqual(InventarioGuardadoDTO(), InventarioGuardadoDTO([], None, None, None))

    def test_inmutables(self):
        for dto, campo in ((partida_de_ejemplo(), "reloj"), (sala_de_ejemplo(), "contenido_cargado"),
                           (EventoGuardadoDTO(1, 1, "accion_actor", actor="jugador"), "tiempo")):
            with self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(dto, campo, 0)


if __name__ == "__main__":
    unittest.main()
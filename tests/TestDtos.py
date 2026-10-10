"""
Pruebas de los DTOs del Integrante 2 (CriptaDTO, ResumenCriptaDTO, SalidaDTO, SalaDTO,
ContenidoSalaDTO, EnemigoEnSalaDTO, TrampaEnSalaDTO, ObjetoDTO y Direcciones) con los
datos REALES del paquete y con los casos límite del Swagger (campos ausentes o en null).
"""
import dataclasses
import unittest

from DTO.CriptaDTO import CriptaDTO, ResumenCriptaDTO
from DTO.Direcciones import DIRECCIONES, E, N, O, S, indice_direccion
from DTO.ObjetoDTO import ObjetoDTO, es_clase_objeto
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO, SalidaDTO
from tests.Utilidades import catalogo_real, contenido_real, destino, general_real, leer_paquete, pagina_real


class PruebasDirecciones(unittest.TestCase):

    def test_indices_acordados(self):
        self.assertEqual((N, S, E, O), (0, 1, 2, 3))
        self.assertEqual(DIRECCIONES, ["N", "S", "E", "O"])
        self.assertEqual(indice_direccion("E"), 2)

    def test_letra_invalida(self):
        with self.assertRaises(ValueError):
            indice_direccion("X")


class PruebasCripta(unittest.TestCase):

    def test_resumenes_reales(self):
        for c in leer_paquete("criptas.json")["criptas"]:
            r = ResumenCriptaDTO.desde_diccionario(c)
            self.assertEqual(r.a_diccionario(), c)

    def test_cripta_real_aplana_jugador_y_vuelve_igual(self):
        g = general_real()
        c = CriptaDTO.desde_diccionario(g)
        self.assertEqual(c.jugador_vida_max, g["jugador"]["vida_max"])
        self.assertEqual(c.salas_por_pagina, g["salas_por_pagina"])
        self.assertEqual(c.presupuesto_solicitudes, g["presupuesto_solicitudes"])
        self.assertEqual(c.a_diccionario(), g)            # mismo formato que el API

    def test_es_inmutable(self):
        c = CriptaDTO.desde_diccionario(general_real())
        # Se intenta modificar A PROPÓSITO: un DTO congelado debe impedirlo.
        # Se usa setattr para que PyCharm no lo marque como error (el objetivo es que falle).
        with self.assertRaises(dataclasses.FrozenInstanceError):
            setattr(c, "version", "otra")


class PruebasSalida(unittest.TestCase):

    def test_salida_simple_y_campos_en_null(self):
        s = SalidaDTO.desde_diccionario({"sala": 4})
        self.assertEqual((s.sala_destino, s.cerrada, s.llave, s.cierre_automatico), (4, False, None, None))
        s = SalidaDTO.desde_diccionario({"sala": 4, "cerrada": None, "llave": None, "cierre_automatico": None})
        self.assertFalse(s.cerrada)

    def test_salida_cerrada_real_ida_y_vuelta(self):
        salida_este = pagina_real()["salas"][1]["salidas"]["E"]   # sala 2 -> 5, cerrada
        s = SalidaDTO.desde_diccionario(salida_este)
        self.assertTrue(s.cerrada)
        self.assertEqual(s.llave, "itm_llave_bronce")
        self.assertEqual(s.a_diccionario(), salida_este)


class PruebasSala(unittest.TestCase):

    def test_esqueleto_real_en_array_de_4(self):
        sala2 = SalaDTO.desde_diccionario(pagina_real()["salas"][1], "v")
        self.assertEqual(destino(sala2, N), 3)
        self.assertEqual(destino(sala2, S), 1)
        self.assertEqual(destino(sala2, E), 5)
        self.assertIsNone(sala2.salidas[O])
        self.assertFalse(sala2.contenido_cargado)

    def test_sala_sin_salidas(self):
        self.assertEqual(SalaDTO.desde_diccionario({"id": 9, "nombre": "x"}, "v").salidas,
                         [None, None, None, None])

    def test_con_contenido_crea_otro_dto(self):
        sola = SalaDTO.desde_diccionario(pagina_real()["salas"][1], "v")
        llena = sola.con_contenido(ContenidoSalaDTO.desde_diccionario(contenido_real()[1]))
        self.assertFalse(sola.contenido_cargado)                 # el original no cambió
        self.assertTrue(llena.contenido_cargado)
        self.assertEqual([e.instancia for e in llena.enemigos], ["e-201", "e-202"])
        self.assertEqual(llena.objetos, ["itm_daga_oxidada"])
        self.assertEqual(llena.trampas[0].tipo, "trp_dardos")

    def test_contenido_de_otra_sala_se_rechaza(self):
        sala = SalaDTO.desde_diccionario(pagina_real()["salas"][0], "v")
        with self.assertRaises(ValueError):
            sala.con_contenido(ContenidoSalaDTO.desde_diccionario({"sala": 5}))

    def test_contenido_con_listas_ausentes_y_vida_null(self):
        c = ContenidoSalaDTO.desde_diccionario({"sala": 3})
        self.assertEqual((c.enemigos, c.objetos, c.trampas), ([], [], []))
        guardian = ContenidoSalaDTO.desde_diccionario(contenido_real()[3]).enemigos[0]   # sala 4, sin 'vida'
        self.assertEqual(guardian.instancia, "e-401")
        self.assertIsNone(guardian.vida)

    def test_las_6_salas_reales_se_guardan_y_leen_igual(self):
        for esqueleto, contenido in zip(pagina_real()["salas"], contenido_real()):
            for sala in (SalaDTO.desde_diccionario(esqueleto, "v"),
                         SalaDTO.desde_diccionario(esqueleto, "v", contenido)):
                self.assertEqual(SalaDTO.desde_persistido(sala.a_diccionario()), sala)

    def test_sala_cargada_pero_vacia_sigue_marcada_como_cargada(self):
        vacia = SalaDTO.desde_diccionario({"id": 6, "nombre": "x"}, "v", {"sala": 6})
        self.assertTrue(SalaDTO.desde_persistido(vacia.a_diccionario()).contenido_cargado)


class PruebasObjeto(unittest.TestCase):

    def test_todas_las_fichas_reales_de_objeto(self):
        objetos = [f for f in catalogo_real() if es_clase_objeto(f["clase"])]
        self.assertEqual(len(objetos), 8)
        for f in objetos:
            o = ObjetoDTO.desde_diccionario(f)
            self.assertEqual(o.a_diccionario(), f)

    def test_campos_que_no_aplican_quedan_en_none(self):
        daga = ObjetoDTO.desde_diccionario(
            {"id": "itm_daga_oxidada", "nombre": "Daga", "clase": "arma", "peso": 2, "valor": 15, "ataque_bonus": 3})
        self.assertEqual(daga.ataque_bonus, 3)
        self.assertIsNone(daga.defensa_bonus)

    def test_llave_con_abre_numerico(self):
        k = ObjetoDTO.desde_diccionario({"id": "k", "nombre": "K", "clase": "llave", "peso": 1, "valor": 1, "abre": 7})
        self.assertEqual(k.abre, 7)

    def test_las_7_clases_de_objeto(self):
        for clase in ("arma", "armadura", "pocion", "antidoto", "llave", "antorcha", "pergamino_retroceso"):
            self.assertEqual(ObjetoDTO.desde_diccionario(
                {"id": "x", "nombre": "X", "clase": clase, "peso": 1, "valor": 1}).clase, clase)

    def test_enemigo_y_trampa_no_son_objetos(self):
        for f in catalogo_real():
            if f["clase"] in ("enemigo", "trampa"):
                with self.assertRaises(ValueError):
                    ObjetoDTO.desde_diccionario(f)


if __name__ == "__main__":
    unittest.main()
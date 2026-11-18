"""
Pruebas del reporte de resolubilidad (feature 003, integrante 2; contracts/contrato-reporte-resolubilidad.md):
el DTO del reporte y el reporte completo de una cripta no resoluble (FR-307 a FR-310, NFR-303).
"""
import dataclasses
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from DTO import ReporteResolubilidadDTO as modulo_reporte  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.ReporteResolubilidadDTO import (NO_CONCLUYO, NO_RESOLUBLE, RESOLUBLE, CicloLlavesDTO,  # noqa: E402
                                         DependienteCicloDTO, LlaveNoObtenibleDTO, PasoCicloDTO, PuertaLlaveDTO,
                                         ReporteResolubilidadDTO)
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO  # noqa: E402
from Logic.VerificadorResolubilidad import verificar as verificar_logica  # noqa: E402
from tests.ayudas_resolubilidad import abierta, cara, cripta, permutar, puerta, ubic  # noqa: E402

U = UbicacionLlaveDTO
P = PuertaLlaveDTO


def verificar(datos) -> ReporteResolubilidadDTO:
    dto, salas, ubicaciones = datos
    return verificar_logica(dto, salas, ubicaciones)


# ---------------------------------------------------------------- criptas de la historia 2
def cripta_h2_1():
    """Apéndice B, caso 1: sala_salida 5; S en la 5, detrás de la única puerta 4–5 (S); la 4 alcanzable."""
    return cripta(5, [abierta(1, E, 2), abierta(2, E, 3), abierta(3, E, 4), puerta(4, E, 5, "S")], [ubic("S", 5)],
                  sala_salida=5)


def salidas_h2_2():
    """A en 6 (puerta 2–6 (B)), B en 7 (puerta 3–7 (A)), S en 8 (puerta 5–8 (A)); 2, 3 y 5 alcanzables desde la 1."""
    return [abierta(1, E, 2), abierta(1, S, 3), abierta(1, O, 5), puerta(2, E, 6, "B"), puerta(3, S, 7, "A"),
            puerta(5, S, 8, "A"), puerta(8, E, 9, "S")]


def cripta_h2_2():
    return cripta(9, salidas_h2_2(), [ubic("A", 6), ubic("B", 7), ubic("S", 8)])


def cripta_h2_4():
    """La del H2-2 más C en la 10, detrás de la puerta 4–10 (A), con la 4 alcanzable."""
    return cripta(10, salidas_h2_2() + [abierta(1, N, 4), puerta(4, E, 10, "A")],
                  [ubic("C", 10), ubic("A", 6), ubic("B", 7), ubic("S", 8)])


def cripta_h2_5():
    """Región 1 a 4 rodeada por 2–6 (B), 3–7 (A) y 4–10 (A); D obtenible en la 2; A y B sin ubicación."""
    return cripta(10, [abierta(1, E, 2), abierta(1, S, 3), abierta(1, N, 4), puerta(2, E, 6, "B"),
                       puerta(3, S, 7, "A"), puerta(4, E, 10, "A"), abierta(6, S, 8), puerta(8, E, 9, "S")],
                  [ubic("D", 2), ubic("S", 6)])


def cripta_h2_6():
    """Puerta 4–5 (C), la 4 alcanzable, S en la 5; C no está en la lista de ubicaciones."""
    return cripta(9, [abierta(1, E, 4), puerta(4, E, 5, "C"), abierta(5, S, 8), puerta(8, E, 9, "S")], [ubic("S", 5)])


def cripta_h2_9(a_obtenible: bool):
    """Puerta 2–6: la cara de la 2 pide A y la de la 6 pide B (B sin ubicación). A en la 1 si a_obtenible."""
    ubicaciones = [ubic("S", 6)] + ([ubic("A", 1)] if a_obtenible else [])
    return cripta(9, [abierta(1, E, 2), cara(2, E, 6, cerrada=True, llave="A"), cara(6, O, 2, cerrada=True, llave="B"),
                      abierta(6, S, 8), puerta(8, E, 9, "S")], ubicaciones)


def cripta_h2_10():
    """Puerta 3–7: la cara de la 3 cerrada sin llave y la de la 7 abierta; la 7 sin otro acceso; S en la 7."""
    return cripta(9, [abierta(1, E, 3), cara(3, E, 7, cerrada=True), cara(7, O, 3), abierta(7, S, 8),
                      puerta(8, E, 9, "S")], [ubic("S", 7)])


def cripta_h2_10_por_otro_camino():
    """La 7 se alcanza por la salida 1–7; desde ella se llega a la 3 por su cara abierta; S en la 3."""
    return cripta(9, [abierta(1, E, 7), cara(7, S, 3), cara(3, N, 7, cerrada=True), abierta(7, E, 8),
                      puerta(8, E, 9, "S")], [ubic("S", 3)])


def cripta_h2_11():
    """Región 1 a 4; puerta 4–5 (B) sin B; la 10 solo desde la 5; salida sin vuelta cerrada 10→4 que pide B."""
    return cripta(10, [abierta(1, E, 2), abierta(2, E, 3), abierta(3, E, 4), puerta(4, S, 5, "B"), abierta(5, E, 10),
                       cara(10, N, 4, cerrada=True, llave="B"), puerta(8, E, 9, "S")], [ubic("S", 10)])


def cripta_h1_12():
    """C con cuatro ubicaciones fuera de la región: 10, 13, otra vez 10 y 13 con e-1301; S en la 1."""
    return cripta(13, [abierta(1, E, 2), puerta(2, E, 10, "C"), puerta(2, S, 13, "C"), puerta(8, E, 9, "S")],
                  [ubic("C", 10), ubic("C", 13), ubic("C", 10), ubic("C", 13, "e-1301"), ubic("S", 1)])


def cripta_h2_12():
    """La del H2-2 más E en 11 (3–11 (F)), F en 12 (5–12 (E)), G en 13 (2–13 (A)) y H en 14 (3–14 (E))."""
    return cripta(14, salidas_h2_2() + [puerta(3, E, 11, "F"), puerta(5, N, 12, "E"), puerta(2, S, 13, "A"),
                                        puerta(3, O, 14, "E")],
                  [ubic("H", 14), ubic("G", 13), ubic("F", 12), ubic("E", 11), ubic("S", 8), ubic("B", 7),
                   ubic("A", 6)])


def cripta_h2_13():
    """
    Región 1 a 4 (1–2, 1–4, 4–3); A en la 6, a la que se entra por 2–6 (B, desde la 2 al este) y por 3–6 (A, desde
    la 3 al norte); B en la 7 (4–7 (B)); S en la 1; la 8 solo por 4–8 (A), y desde la 8 la puerta de salida 8–9.
    """
    return cripta(9, [abierta(1, E, 2), abierta(1, S, 4), abierta(4, E, 3), puerta(2, E, 6, "B"), puerta(3, N, 6, "A"),
                      puerta(4, S, 7, "B"), puerta(4, O, 8, "A"), puerta(8, S, 9, "S")],
                  [ubic("A", 6), ubic("B", 7), ubic("S", 1)])


NO_RESOLUBLES = [cripta_h2_1, cripta_h2_2, cripta_h2_4, cripta_h2_5, cripta_h2_6, lambda: cripta_h2_9(False),
                 cripta_h2_10, cripta_h2_11, cripta_h1_12, cripta_h2_12, cripta_h2_13]


class PruebasDtoReporte(unittest.TestCase):
    """T005: las clases del contrato del reporte (FR-307 a FR-310, FR-322)."""

    def test_fr307_reporte_constantes_de_veredicto(self):
        self.assertEqual((RESOLUBLE, NO_RESOLUBLE, NO_CONCLUYO), ("resoluble", "no_resoluble", "no_concluyo"))
        self.assertIs(modulo_reporte.RESOLUBLE, RESOLUBLE)

    def test_fr307_reporte_valores_por_defecto(self):
        r = ReporteResolubilidadDTO("prueba", RESOLUBLE)
        self.assertEqual((r.id_cripta, r.veredicto), ("prueba", RESOLUBLE))
        self.assertIsNone(r.version_cripta)
        self.assertIsNone(r.llave_salida)
        self.assertIsNone(r.motivo)
        self.assertIsNone(r.mensaje)
        self.assertEqual((r.orden_llaves, r.llaves_no_obtenibles, r.frontera, r.ciclos), ([], [], [], []))
        otro = ReporteResolubilidadDTO("otra", NO_CONCLUYO)
        for campo in ("orden_llaves", "llaves_no_obtenibles", "frontera", "ciclos"):
            self.assertIsNot(getattr(r, campo), getattr(otro, campo), campo)   # default_factory: no se comparten
        with self.assertRaises(TypeError):
            ReporteResolubilidadDTO("prueba")  # type: ignore[call-arg]   # veredicto es obligatorio

    def test_fr307_reporte_orden_de_campos(self):
        nombres = [f.name for f in dataclasses.fields(ReporteResolubilidadDTO)]
        self.assertEqual(nombres, ["id_cripta", "veredicto", "version_cripta", "llave_salida", "orden_llaves",
                                   "llaves_no_obtenibles", "frontera", "ciclos", "motivo", "mensaje"])
        self.assertEqual([f.name for f in dataclasses.fields(PuertaLlaveDTO)],
                         ["sala_origen", "direccion", "sala_destino", "llave"])
        self.assertEqual([f.name for f in dataclasses.fields(LlaveNoObtenibleDTO)], ["id", "ubicaciones"])
        self.assertEqual([f.name for f in dataclasses.fields(PasoCicloDTO)], ["llave", "ubicacion", "puerta"])
        self.assertEqual([f.name for f in dataclasses.fields(DependienteCicloDTO)],
                         ["llave", "ubicacion", "puerta", "depende_de"])
        self.assertEqual([f.name for f in dataclasses.fields(CicloLlavesDTO)], ["pasos", "dependientes"])

    def test_fr310_clases_del_reporte_son_inmutables(self):
        u = UbicacionLlaveDTO("A", 6)
        p = PuertaLlaveDTO(2, 2, 6, "B")
        paso = PasoCicloDTO("A", u, p)
        dep = DependienteCicloDTO("S", UbicacionLlaveDTO("S", 8), PuertaLlaveDTO(5, 0, 8, "A"), "A")
        objetos = [(p, "llave"), (LlaveNoObtenibleDTO("A", [u]), "id"), (paso, "llave"), (dep, "depende_de"),
                   (CicloLlavesDTO([paso], [dep]), "pasos"), (ReporteResolubilidadDTO("prueba", NO_RESOLUBLE), "veredicto")]
        for objeto, campo in objetos:
            with self.assertRaises(dataclasses.FrozenInstanceError, msg=type(objeto).__name__):
                setattr(objeto, campo, None)


class PruebasNoObteniblesYFrontera(unittest.TestCase):
    """T026: llaves no obtenibles, ubicaciones y frontera bloqueada (FR-307 a FR-309)."""

    def no_resoluble(self, datos) -> ReporteResolubilidadDTO:
        reporte = verificar(datos)
        self.assertEqual(reporte.veredicto, NO_RESOLUBLE)
        self.assertEqual(reporte.orden_llaves, [])
        return reporte

    def test_h2_1_apendiceB_caso1_fr304_fr307_fr308_fr309_fr310_llave_salida_detras_de_su_puerta(self):
        reporte = self.no_resoluble(cripta_h2_1())
        self.assertEqual(reporte, ReporteResolubilidadDTO(
            "prueba", NO_RESOLUBLE, "v1", "S",
            llaves_no_obtenibles=[LlaveNoObtenibleDTO("S", [U("S", 5)])],
            frontera=[P(4, E, 5, "S")],
            ciclos=[CicloLlavesDTO([PasoCicloDTO("S", U("S", 5), P(4, E, 5, "S"))], [])]))

    def test_h2_5_fr307_fr308_frontera_sin_repetir(self):
        reporte = self.no_resoluble(cripta_h2_5())
        self.assertEqual(reporte.frontera, [P(2, E, 6, "B"), P(3, S, 7, "A"), P(4, E, 10, "A")])
        self.assertEqual([ll.id for ll in reporte.llaves_no_obtenibles], ["A", "B", "S"])   # D no aparece

    def test_h2_6_fr307_fr308_fr309_fr321_llave_sin_ubicacion(self):
        reporte = self.no_resoluble(cripta_h2_6())
        self.assertEqual(reporte.llaves_no_obtenibles, [LlaveNoObtenibleDTO("C", []),
                                                        LlaveNoObtenibleDTO("S", [U("S", 5)])])
        self.assertEqual(reporte.frontera, [P(4, E, 5, "C")])
        self.assertEqual(reporte.ciclos, [])          # S depende de C, que no tiene ubicación: sin ciclo
        self.assertIsNone(reporte.mensaje)

    def test_h2_9_fr302_fr308_llaves_distintas_por_cara(self):
        con_a = verificar(cripta_h2_9(True))
        self.assertEqual((con_a.veredicto, con_a.orden_llaves), (RESOLUBLE, ["A", "S"]))   # la 6 entrando con A
        sin_a = self.no_resoluble(cripta_h2_9(False))
        self.assertEqual(sin_a.frontera, [P(2, E, 6, "A")])                  # la llave de la cara de la sala alcanzable

    def test_h2_10_fr302_fr308_cara_cerrada_sin_llave(self):
        reporte = self.no_resoluble(cripta_h2_10())
        self.assertEqual(reporte.frontera, [P(3, E, 7, None)])               # «sin llave: no se puede abrir»
        self.assertEqual(reporte.llaves_no_obtenibles, [LlaveNoObtenibleDTO("S", [U("S", 7)])])
        self.assertEqual(reporte.ciclos, [])
        otro_camino = verificar(cripta_h2_10_por_otro_camino())
        self.assertEqual((otro_camino.veredicto, otro_camino.orden_llaves), (RESOLUBLE, ["S"]))

    def test_h2_11_fr308_salida_sin_vuelta_hacia_la_region_no_es_frontera(self):
        reporte = self.no_resoluble(cripta_h2_11())
        self.assertEqual(reporte.frontera, [P(4, S, 5, "B")])

    def test_h1_12_fr316_fr309_fr306_ubicaciones_identicas_una_sola_vez(self):
        dto, salas, ubicaciones = cripta_h1_12()
        esperado = LlaveNoObtenibleDTO("C", [U("C", 10), U("C", 13), U("C", 13, "e-1301")])
        for semilla in range(5):
            reporte = self.no_resoluble((dto, permutar(salas, semilla), permutar(ubicaciones, semilla)))
            self.assertEqual(reporte.llaves_no_obtenibles, [esperado], semilla)


class PruebasCiclos(unittest.TestCase):
    """T027: ciclos de llaves y llaves dependientes (FR-310)."""

    def test_h2_2_fr307_fr310_ciclo_de_dos_llaves(self):
        reporte = verificar(cripta_h2_2())
        self.assertEqual(reporte, ReporteResolubilidadDTO(
            "prueba", NO_RESOLUBLE, "v1", "S",
            llaves_no_obtenibles=[LlaveNoObtenibleDTO("A", [U("A", 6)]), LlaveNoObtenibleDTO("B", [U("B", 7)]),
                                  LlaveNoObtenibleDTO("S", [U("S", 8)])],
            frontera=[P(2, E, 6, "B"), P(3, S, 7, "A"), P(5, S, 8, "A")],
            ciclos=[CicloLlavesDTO(
                pasos=[PasoCicloDTO("A", U("A", 6), P(2, E, 6, "B")), PasoCicloDTO("B", U("B", 7), P(3, S, 7, "A"))],
                dependientes=[DependienteCicloDTO("S", U("S", 8), P(5, S, 8, "A"), "A")])]))

    def test_h2_3_fr306_fr310_reporte_identico_en_cada_ejecucion(self):
        dto, salas, ubicaciones = cripta_h2_2()
        esperado = verificar((dto, salas, ubicaciones))
        self.assertEqual([p.llave for p in esperado.ciclos[0].pasos], ["A", "B"])    # el ciclo empieza por A
        for semilla in range(5):
            self.assertEqual(verificar((dto, permutar(salas, semilla), permutar(ubicaciones, 50 + semilla))), esperado)

    def test_h2_4_fr307_fr309_fr310_dependiente_del_ciclo(self):
        reporte = verificar(cripta_h2_4())
        self.assertIn(LlaveNoObtenibleDTO("C", [U("C", 10)]), reporte.llaves_no_obtenibles)
        self.assertEqual(len(reporte.ciclos), 1)
        ciclo = reporte.ciclos[0]
        self.assertEqual([p.llave for p in ciclo.pasos], ["A", "B"])          # C no forma un ciclo propio
        self.assertEqual(ciclo.dependientes, [DependienteCicloDTO("C", U("C", 10), P(4, E, 10, "A"), "A"),
                                              DependienteCicloDTO("S", U("S", 8), P(5, S, 8, "A"), "A")])

    def test_h2_12_fr307_fr310_fr306_dos_ciclos_independientes(self):
        dto, salas, ubicaciones = cripta_h2_12()
        esperado = [
            CicloLlavesDTO(
                pasos=[PasoCicloDTO("A", U("A", 6), P(2, E, 6, "B")), PasoCicloDTO("B", U("B", 7), P(3, S, 7, "A"))],
                dependientes=[DependienteCicloDTO("G", U("G", 13), P(2, S, 13, "A"), "A"),
                              DependienteCicloDTO("S", U("S", 8), P(5, S, 8, "A"), "A")]),
            CicloLlavesDTO(
                pasos=[PasoCicloDTO("E", U("E", 11), P(3, E, 11, "F")), PasoCicloDTO("F", U("F", 12), P(5, N, 12, "E"))],
                dependientes=[DependienteCicloDTO("H", U("H", 14), P(3, O, 14, "E"), "E")]),
        ]
        for semilla in range(5):
            reporte = verificar((dto, permutar(salas, semilla), permutar(ubicaciones, semilla)))
            self.assertEqual(reporte.ciclos, esperado, semilla)
            self.assertEqual([ll.id for ll in reporte.llaves_no_obtenibles], ["A", "B", "E", "F", "G", "H", "S"])

    def test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea(self):
        reporte = verificar(cripta_h2_13())
        self.assertEqual((reporte.veredicto, reporte.motivo), (NO_RESOLUBLE, None))
        self.assertEqual(reporte.llaves_no_obtenibles, [LlaveNoObtenibleDTO("A", [U("A", 6)]),
                                                        LlaveNoObtenibleDTO("B", [U("B", 7)])])
        self.assertEqual(reporte.frontera, [P(2, E, 6, "B"), P(3, N, 6, "A"), P(4, S, 7, "B"), P(4, O, 8, "A")])
        self.assertEqual(reporte.ciclos, [CicloLlavesDTO(
            pasos=[PasoCicloDTO("B", U("B", 7), P(4, S, 7, "B"))],
            dependientes=[DependienteCicloDTO("A", U("A", 6), P(2, E, 6, "B"), "B")])])   # la 2–6, no la 3–6

    def test_sc305_reporte_completo_en_todas_las_no_resolubles(self):
        for i in range(len(NO_RESOLUBLES)):
            with self.subTest(i):
                dto, salas, ubicaciones = NO_RESOLUBLES[i]()
                reporte = verificar((dto, salas, ubicaciones))
                self.assertEqual(reporte.veredicto, NO_RESOLUBLE)
                self.assertGreater(len(reporte.llaves_no_obtenibles), 0)   # todas estas tienen alguna (FR-307)
                for llave in reporte.llaves_no_obtenibles:
                    distintas = []
                    for u in ubicaciones:
                        if u.id == llave.id and u not in distintas:
                            distintas.append(u)
                    self.assertCountEqual(llave.ubicaciones, distintas, llave.id)   # todas, o lista vacía
                for p in reporte.frontera:
                    self.assertIsInstance(p.sala_origen, int)
                    self.assertIsInstance(p.sala_destino, int)
                    self.assertIn(p.direccion, (N, S, E, O))
                    self.assertTrue(p.llave is None or isinstance(p.llave, str))
                ids_no_obtenibles = [ll.id for ll in reporte.llaves_no_obtenibles]
                for ciclo in reporte.ciclos:
                    pasos = ciclo.pasos
                    self.assertGreater(len(pasos), 0)
                    for j in range(len(pasos)):
                        self.assertIn(pasos[j].llave, ids_no_obtenibles)
                        self.assertEqual(pasos[j].puerta.llave, pasos[(j + 1) % len(pasos)].llave)   # vuelve a la 1.ª
                        self.assertEqual(pasos[j].ubicacion.id, pasos[j].llave)
                    del_ciclo = [p.llave for p in pasos]
                    self.assertEqual(del_ciclo[0], min(del_ciclo))
                    for dep in ciclo.dependientes:
                        self.assertIn(dep.depende_de, del_ciclo)
                        self.assertNotIn(dep.llave, del_ciclo)
                        self.assertIn(dep.llave, ids_no_obtenibles)


class PruebasSinRecursion(unittest.TestCase):
    """T029: una cadena de más de 1000 dependientes no llega al límite de recursión (research R6 y R7, riesgo R-9)."""

    def test_fr310_cadena_de_mas_de_1000_dependientes_sin_recursion(self):
        from Logic.BenchResolubilidad import cripta_en_cuadricula
        limite = sys.getrecursionlimit()
        columnas = 3000
        datos = cripta_en_cuadricula(filas=2, columnas=columnas, semilla=7, resoluble=False)
        self.assertEqual(len(datos[1]), 6000)
        reporte = verificar(datos)                                           # sin RecursionError
        self.assertEqual(reporte.veredicto, NO_RESOLUBLE)
        self.assertEqual(len(reporte.ciclos), 1)
        m = (columnas - 1) // 2
        self.assertEqual(len(reporte.ciclos[0].pasos), 1)
        self.assertEqual(len(reporte.ciclos[0].dependientes), columnas - m - 1)   # 1500 > límite de recursión
        self.assertGreater(len(reporte.ciclos[0].dependientes), limite)
        self.assertEqual(len(reporte.llaves_no_obtenibles), columnas - m)
        self.assertEqual(sys.getrecursionlimit(), limite)


if __name__ == "__main__":
    unittest.main()

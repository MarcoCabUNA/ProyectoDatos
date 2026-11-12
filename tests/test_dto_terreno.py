import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from types import SimpleNamespace  # noqa: E402

from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from DTO.Direcciones import E, N, O, S  # noqa: E402
from DTO.FichaEnemigoDTO import FichaEnemigoDTO  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.jugador import Jugador  # noqa: E402
from Logic.Mazmorra import Mazmorra  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from tests.ayudas_terreno import salida, salidas_con_costos  # noqa: E402


def _cripta() -> CriptaDTO:
    return CriptaDTO.desde_diccionario({
        "id": "cripta-01", "version": "a3f91c", "salas_total": 20, "paginas": 2,
        "salas_por_pagina": 10, "sala_inicial": 1, "sala_salida": 20,
        "llave_salida": "itm_llave_maestra", "presupuesto_solicitudes": 50,
        "inventario_max": 10,
        "jugador": {"vida_max": 20, "ataque": 5, "defensa": 2, "velocidad": 100}})


def _enemigo(comportamiento: str) -> Enemigo:
    ficha = FichaEnemigoDTO("ene_prueba", "Prueba", 10, 3, 1, 100, comportamiento, [])
    return Enemigo(ficha, "e-1", None, 1, 3)


class TestSalidaDTOTerreno(unittest.TestCase):
    def test_h4_1_fr116_el_costo_llega_a_la_vista(self) -> None:
        """
        Escenario H4-1 (FR-101, FR-116, T036): la sala que ArmadorEstado entrega a la vista trae en cada
        SalidaDTO el costo ya igualado por Lógica, no el declarado, también en una salida cerrada.
        Se llama a _sala_con_estado_actual porque armar_estado pide un contexto de partida completo
        (motor, inventario, resolvedor...) que no aporta nada a lo que se comprueba aquí.
        """
        # Sala 1: N -> 2 (100), S -> 3 (250), E -> 4 (sin costo), O -> 5 (solo el lado de la sala 5 declara 300; cerrada).
        esqueleto = salidas_con_costos(5, [salida(1, N, 2, 100), salida(1, S, 3, 250), salida(1, E, 4),
                                           (1, O, 5, None, 300, True)])
        mazmorra = Mazmorra(sala_salida=5, llave_salida="llave_final")
        mazmorra.cargar_esqueleto(esqueleto)
        contexto = SimpleNamespace(esqueleto=SimpleNamespace(obtener_sala=lambda i: esqueleto[i - 1]),
                                   mazmorra=mazmorra)
        sala = ArmadorEstado()._sala_con_estado_actual(contexto, 1)
        self.assertIsNone(esqueleto[0].salidas[O].costo)          # el esqueleto trae lo declarado
        self.assertEqual([sala.salidas[d].costo for d in (N, S, E, O)], [100, 250, 100, 300])
        self.assertTrue(sala.salidas[O].cerrada)


class TestActorDTOTerreno(unittest.TestCase):
    def test_h4_2_fr117_actor_dto_trae_el_comportamiento(self) -> None:
        """FR-117: el ActorDTO de cada enemigo trae su comportamiento; el del jugador, None."""
        for comportamiento in ("errante", "guardián", "rastreador", "cazador"):
            with self.subTest(comportamiento=comportamiento):
                self.assertEqual(_enemigo(comportamiento).a_dto().comportamiento, comportamiento)
        self.assertIsNone(Jugador(_cripta()).a_dto().comportamiento)


def _ficha_json(**cambios) -> dict:
    d = {"id": "ent_sabueso_oseo", "clase": "enemigo", "nombre": "Sabueso óseo", "vida_max": 18,
         "ataque": 6, "defensa": 2, "velocidad": 120, "comportamiento": "cazador", "rango": 600, "suelta": []}
    d.update(cambios)
    return d


class TestFichaRango(unittest.TestCase):
    """FR-106: la ficha del cazador trae `rango`; las fichas de P1 se leen y escriben igual que antes."""

    def test_fr106_lee_rango(self) -> None:
        self.assertEqual(FichaEnemigoDTO.desde_diccionario(_ficha_json()).rango, 600)

    def test_fr106_sin_rango_queda_en_none(self) -> None:
        d = _ficha_json(comportamiento="errante")
        del d["rango"]
        self.assertIsNone(FichaEnemigoDTO.desde_diccionario(d).rango)

    def test_fr106_a_diccionario_escribe_rango_solo_si_no_es_none(self) -> None:
        self.assertEqual(FichaEnemigoDTO.desde_diccionario(_ficha_json()).a_diccionario()["rango"], 600)
        d = _ficha_json(comportamiento="errante")
        del d["rango"]
        self.assertNotIn("rango", FichaEnemigoDTO.desde_diccionario(d).a_diccionario())

    def test_fr106_ida_y_vuelta_igual(self) -> None:
        ficha = FichaEnemigoDTO.desde_diccionario(_ficha_json())
        self.assertEqual(FichaEnemigoDTO.desde_diccionario(ficha.a_diccionario()), ficha)
        self.assertEqual(ficha.a_diccionario(), _ficha_json())

    def test_fr106_rango_no_aparece_en_extras(self) -> None:
        ficha = FichaEnemigoDTO.desde_diccionario(_ficha_json())
        for clave, _ in ficha.extras:
            self.assertNotEqual(clave, "rango")

    def test_fr106_ficha_de_p1_sin_rango_igual_que_antes(self) -> None:
        d = {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 10, "ataque": 3,
             "defensa": 1, "velocidad": 100, "comportamiento": "errante", "suelta": ["itm_queso"]}
        ficha = FichaEnemigoDTO.desde_diccionario(d)
        self.assertIsNone(ficha.rango)
        self.assertEqual(ficha.a_diccionario(), d)
        # Los constructores posicionales de 8 argumentos (como los de Logic/BenchLogica.py) siguen sirviendo.
        self.assertIsNone(FichaEnemigoDTO("ene_rata", "Rata", 10, 1, 0, 150, "errante", []).rango)


if __name__ == "__main__":
    unittest.main()

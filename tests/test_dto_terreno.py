import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from DTO.CriptaDTO import CriptaDTO  # noqa: E402
from DTO.FichaEnemigoDTO import FichaEnemigoDTO  # noqa: E402
from Logic.Enemigo import Enemigo  # noqa: E402
from Logic.jugador import Jugador  # noqa: E402


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


class TestActorDTOTerreno(unittest.TestCase):
    def test_h4_2_fr117_actor_dto_trae_el_comportamiento(self) -> None:
        """FR-117: el ActorDTO de cada enemigo trae su comportamiento; el del jugador, None."""
        for comportamiento in ("errante", "guardián", "rastreador"):
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

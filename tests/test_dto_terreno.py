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


if __name__ == "__main__":
    unittest.main()

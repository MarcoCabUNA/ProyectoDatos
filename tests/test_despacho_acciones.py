"""
Pruebas de Service/DespachoAcciones.py (feature 004, T013/T014): el despacho propio de acciones de la línea.

Dos partidas iguales (misma semilla, jugador reforzado para que dure): A usa ServicioAccionJugador y B usa
DespachoAcciones sobre su motor. Después de cada acción se compara el estado completo del motor con
PartidaGuardada.guardar. El proveedor de datos de B sale de la partida A (la línea lo hará con sus registros).
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import ID_CRIPTA, _correr, _crear, _elegir_accion  # noqa: F401
from test_servicios import ID_PERGAMINO
from DTO.AccionDTO import AccionDTO
from Logic.PartidaGuardada import PartidaGuardada
from Service.ArmadorEstado import ArmadorEstado
from Service.DespachoAcciones import DespachoAcciones
from Service.ServicioAccionJugador import ServicioAccionJugador

TIPOS = ["mover", "abrir", "atacar", "esperar", "recoger", "soltar", "equipar", "usar"]


class _DatosDeLaPartidaViva:
    """El proveedor de datos del despacho: ficha(id) y sala(id), respaldado por otra partida."""

    def __init__(self, contexto) -> None:
        self._contexto = contexto

    def ficha(self, id_ficha: str):
        return self._contexto.resolvedor.ficha(id_ficha)

    def sala(self, id_sala: int):
        return self._contexto.contenido.asegurar_sala(id_sala)


def _foto(contexto) -> tuple:
    """Todo el estado del motor, como diccionarios comparables."""
    partida, salas = PartidaGuardada.guardar(contexto.motor, contexto.cripta,
                                             contexto.resolvedor.version_catalogo(), contexto.semilla)
    return partida.a_diccionario(), [sala.a_diccionario() for sala in salas]


def _solicitudes(fuente) -> int:
    """Las solicitudes que le han hecho a la fuente (en FuenteJson es un método; en la offline, siempre 0)."""
    cuenta = fuente.solicitudes_realizadas
    return cuenta() if callable(cuenta) else cuenta


def _numeros_de_data(contexto) -> tuple:
    """Todo lo que cuenta lo que se le pidió a Data."""
    r, g = contexto.resolvedor, contexto.contenido
    return (_solicitudes(contexto.fuente), r.aciertos(), r.fallos(), r.lecturas_disco(),
            r.solicitudes_catalogo(), r.fichas_descargadas(), g.lotes_realizados(), g.salas_pedidas())


def _ejecutar_en_b(despacho: DespachoAcciones, contexto, datos, accion: AccionDTO) -> str:
    """Lo que hará el reconstructor: despachar y, si fue aceptada, avanzar hasta la decisión del jugador."""
    codigo = despacho.ejecutar(contexto.motor, datos, accion)
    if codigo == "ok":
        contexto.motor.avanzar_hasta_jugador()
    return codigo


class PruebasDespachoAcciones(unittest.TestCase):

    def test_despacho_igual_al_servicio_de_acciones_fr419(self):
        despacho, vistos = DespachoAcciones(), []
        for semilla in (1, 4, 5):
            def prueba(carpeta, semilla=semilla):
                _, servicio, a = _crear(os.path.join(carpeta, "a"), semilla=semilla, reforzar=True)
                _, _, b = _crear(os.path.join(carpeta, "b"), semilla=semilla, reforzar=True)
                datos = _DatosDeLaPartidaViva(a)
                estado = ArmadorEstado().armar_estado(a)
                x = semilla * 2654435761 % (1 << 32)
                for _ in range(200):
                    if a.motor.terminado:
                        break
                    x = (x * 1103515245 + 12345) % (1 << 32)
                    accion = _elegir_accion(estado, x)
                    self.assertNotEqual(accion.tipo, "retroceder", "estas semillas no encuentran pergaminos")
                    antes = a.jugador.acciones
                    estado = servicio.ejecutar(a, accion)
                    codigo = _ejecutar_en_b(despacho, b, datos, accion)
                    self.assertEqual(codigo == "ok", a.jugador.acciones != antes, f"{accion} dio {codigo}")
                    self.assertEqual(_foto(a), _foto(b), f"el estado difiere tras {accion}")
                    if codigo == "ok":
                        vistos.append(accion.tipo)
            _correr(prueba)
        for tipo in TIPOS:
            self.assertIn(tipo, vistos, f"la prueba no cubrió la acción {tipo}")

    def test_despacho_no_escribe_log_fr408(self):
        def prueba(carpeta):
            _, _, a = _crear(os.path.join(carpeta, "a"), semilla=1, reforzar=True)
            _, _, b = _crear(os.path.join(carpeta, "b"), semilla=1, reforzar=True)
            ruta = b.bitacora.ruta()
            texto_antes = Path(ruta).read_text(encoding="utf-8")
            despacho, datos = DespachoAcciones(), _DatosDeLaPartidaViva(a)
            estado = ArmadorEstado().armar_estado(a)
            for i in range(40):
                accion = _elegir_accion(estado, i * 7919 + 13)
                _ejecutar_en_b(despacho, b, datos, accion)
                estado = ArmadorEstado().armar_estado(b)
            self.assertGreater(b.jugador.acciones, 0)
            self.assertEqual(b.bitacora.acciones_escritas(), 0)
            self.assertEqual(Path(ruta).read_text(encoding="utf-8"), texto_antes)
        _correr(prueba)

    def test_despacho_no_pide_nada_a_data_fr407(self):
        def prueba(carpeta):
            _, _, a = _crear(os.path.join(carpeta, "a"), semilla=1, reforzar=True)
            _, _, b = _crear(os.path.join(carpeta, "b"), semilla=1, reforzar=True)
            despacho, datos = DespachoAcciones(), _DatosDeLaPartidaViva(a)
            estado = ArmadorEstado().armar_estado(a)
            antes = _numeros_de_data(b)
            for i in range(60):
                accion = _elegir_accion(estado, i * 104729 + 7)
                estado = ServicioAccionJugador().ejecutar(a, accion)        # A prepara lo que B va a pedir a "la línea"
                _ejecutar_en_b(despacho, b, datos, accion)
            self.assertEqual(_numeros_de_data(b), antes)                    # B no le pidió nada a su Data
        _correr(prueba)

    def test_despacho_rechaza_retroceder_fr413(self):
        def prueba(carpeta):
            _, _, b = _crear(os.path.join(carpeta, "b"), semilla=1, pergaminos=1)
            despacho = DespachoAcciones()
            with self.assertRaises(ValueError):
                despacho.ejecutar(b.motor, _DatosDeLaPartidaViva(b), AccionDTO("retroceder"))
            with self.assertRaises(ValueError):                             # usar un pergamino es lo mismo
                despacho.ejecutar(b.motor, _DatosDeLaPartidaViva(b), AccionDTO("usar", objeto=ID_PERGAMINO))
            ids = [objeto.id for objeto in b.inventario.objetos()]
            self.assertIn(ID_PERGAMINO, ids)                                # y el pergamino no se consumió
        _correr(prueba)

    def test_despacho_codigos_de_rechazo_como_el_servicio_fr419(self):
        def prueba(carpeta):
            _, _, b = _crear(os.path.join(carpeta, "b"), semilla=1)
            despacho, datos = DespachoAcciones(), _DatosDeLaPartidaViva(b)
            reloj, acciones = b.motor.reloj, b.jugador.acciones
            esperado = [(AccionDTO("mover", direccion=9), "direccion_invalida"),
                        (AccionDTO("abrir", direccion=-1), "direccion_invalida"),
                        (AccionDTO("atacar"), "falta_objetivo"),
                        (AccionDTO("recoger"), "falta_objeto"),
                        (AccionDTO("soltar"), "falta_objeto"),
                        (AccionDTO("equipar"), "falta_objeto"),
                        (AccionDTO("usar"), "falta_objeto"),
                        (AccionDTO("bailar"), "accion_desconocida")]
            for accion, codigo in esperado:
                self.assertEqual(despacho.ejecutar(b.motor, datos, accion), codigo, str(accion))
            self.assertEqual((b.motor.reloj, b.jugador.acciones), (reloj, acciones))   # nada cambió
        _correr(prueba)


if __name__ == "__main__":
    unittest.main()

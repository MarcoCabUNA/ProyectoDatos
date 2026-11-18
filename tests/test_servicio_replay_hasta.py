"""
Pruebas de ServicioReplayHasta (feature 004, historia 2, T038): `--replay partida.log --hasta t`.

Se juega una partida con el paquete offline y se guarda su log; se reproduce en una partida nueva (otra carpeta, otra
caché) y se compara con lo que mostraría `historia t` en la partida viva (ServicioLineaTiempo.consultar_por_instante).
Las partidas largas usan FuenteReforzada (jugador fuerte, ver tests/ayudas_linea_tiempo.py), también al reproducir.
"""
import dataclasses
import os
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayudas_linea_tiempo import FuenteReforzada, _correr, jugar, partida_de_prueba, resumen_vivo
from Data.FuenteOffline import FuenteOffline
from DTO.ConfiguracionDTO import ConfiguracionDTO
from Service.ServicioLineaTiempo import ServicioLineaTiempo
from Service.ServicioPartida import ServicioPartida
from Service.ServicioReplayHasta import ServicioReplayHasta


def servicio_para_reproducir(carpeta: str, reforzado: bool) -> ServicioReplayHasta:
    clase = FuenteReforzada if reforzado else FuenteOffline
    partida = ServicioPartida(ConfiguracionDTO(offline=True), fuente=clase(str(RAIZ / "paquete")),
                              carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))
    return ServicioReplayHasta(partida)


def jugar_y_guardar(carpeta: str, semilla: int, intentos: int, reforzado: bool):
    """Una partida normal: (contexto vivo, ruta de su log)."""
    _, ctx = partida_de_prueba(os.path.join(carpeta, "origen"), semilla=semilla, reforzado=reforzado)
    jugar(ctx, intentos)
    return ctx, ctx.bitacora.ruta()


def con_comentarios_ir_a(ruta: str) -> str:
    """Copia del log con una línea «# ir a» entre cada par de acciones. Devuelve la ruta de la copia."""
    with open(ruta, encoding="utf-8", newline="") as archivo:
        lineas = archivo.read().split("\n")
    inicio = lineas.index("#ACCIONES") + 1
    nuevas = lineas[:inicio]
    for linea in lineas[inicio:]:
        nuevas.append(linea)
        if linea != "":
            nuevas.append("# ir a 3")
    nueva = ruta + ".ir_a.log"
    with open(nueva, "w", encoding="utf-8", newline="") as archivo:
        archivo.write("\n".join(nuevas))
    return nueva


class PruebasReplayHasta(unittest.TestCase):

    def test_h2_1_fr410_fr411_mismo_resumen_que_historia_t(self):
        def prueba(carpeta):
            ctx, ruta = jugar_y_guardar(carpeta, 2026, 10, reforzado=True)
            self.assertFalse(ctx.motor.terminado)
            self.assertEqual(ctx.jugador.acciones, 10)
            servicio = servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=True)
            historia = ServicioLineaTiempo()
            for t in (1, 5, ctx.motor.reloj // 2, ctx.motor.reloj - 1, ctx.motor.reloj):
                self.assertEqual(servicio.reproducir_hasta(ruta, t), historia.consultar_por_instante(ctx, t), f"t={t}")
        _correr(prueba)

    def test_h2_2_apendiceB_caso5_fr412_t_posterior_al_final(self):
        def prueba(carpeta):
            ctx, ruta = jugar_y_guardar(carpeta, 1, 60, reforzado=False)
            self.assertTrue(ctx.motor.terminado)
            final = ctx.motor.reloj
            resumen = servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=False).reproducir_hasta(ruta, final + 1161)
            self.assertTrue(resumen.terminada_antes)
            self.assertEqual(resumen.reloj, final)                       # el del final, no el pedido
            self.assertEqual(resumen.instante_pedido, final + 1161)
            vivo = resumen_vivo(ctx)
            self.assertEqual(dataclasses.replace(resumen, terminada_antes=False, instante_pedido=vivo.instante_pedido), vivo)
            exacto = servicio_para_reproducir(os.path.join(carpeta, "replay2"), reforzado=False).reproducir_hasta(ruta, final)
            self.assertFalse(exacto.terminada_antes)                     # justo en el final: no terminó «antes»
        _correr(prueba)

    def test_h2_5_fr402_fr410_hasta_cero_es_el_estado_inicial(self):
        def prueba(carpeta):
            ctx, ruta = jugar_y_guardar(carpeta, 2026, 10, reforzado=True)
            resumen = servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=True).reproducir_hasta(ruta, 0)
            self.assertEqual(resumen, ServicioLineaTiempo().consultar_por_instante(ctx, 0))
            self.assertEqual((resumen.reloj, resumen.terminada_antes), (0, False))
            self.assertEqual(resumen.sala_id, 1)
        _correr(prueba)

    def test_h2_6_fr410_sin_hasta_reproduce_todo(self):
        """ServicioReplay (la primera parte) sigue reproduciendo la partida completa y ServicioReplayHasta no la toca."""
        def prueba(carpeta):
            from Service.ServicioReplay import ServicioReplay
            ctx, ruta = jugar_y_guardar(carpeta, 1, 60, reforzado=False)
            partida = ServicioPartida(ConfiguracionDTO(offline=True), fuente=FuenteOffline(str(RAIZ / "paquete")),
                                      carpeta_cache=os.path.join(carpeta, "c"), carpeta_logs=os.path.join(carpeta, "l"))
            resultado = ServicioReplay(partida).reproducir(ruta)
            self.assertEqual(resultado.acciones_reproducidas, ctx.jugador.acciones)
            self.assertEqual(resultado.estado_final.reloj, ctx.motor.reloj)
        _correr(prueba)

    def test_una_linea_ir_a_no_cambia_el_resultado_fr410(self):
        def prueba(carpeta):
            ctx, ruta = jugar_y_guardar(carpeta, 2026, 10, reforzado=True)
            con_ir_a = con_comentarios_ir_a(ruta)
            servicio = servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=True)
            for t in (0, 7, ctx.motor.reloj):
                self.assertEqual(servicio.reproducir_hasta(con_ir_a, t), servicio.reproducir_hasta(ruta, t), f"t={t}")
        _correr(prueba)

    def test_t_negativo_o_no_entero_lo_rechaza_logica_con_el_rango_fr409(self):
        def prueba(carpeta):
            ctx, ruta = jugar_y_guardar(carpeta, 2026, 10, reforzado=True)
            servicio = servicio_para_reproducir(os.path.join(carpeta, "replay"), reforzado=True)
            for malo in (-1, "5", 2.5, None):
                with self.subTest(t=malo):
                    with self.assertRaises(ValueError) as contexto:
                        servicio.reproducir_hasta(ruta, malo)
                    self.assertIn(str(ctx.motor.reloj), str(contexto.exception))     # el mensaje trae el rango
            with self.assertRaises(ValueError):                                      # la partida no terminó: no hay «final»
                servicio.reproducir_hasta(ruta, ctx.motor.reloj + 1)
        _correr(prueba)

    def test_fr411_no_importa_la_vista(self):
        """El módulo del servicio y todo lo que arrastra se cargan sin pygame ni View/."""
        codigo = ("import sys; import Service.ServicioReplayHasta; "
                  "malos = [m for m in sys.modules if m == 'pygame' or m == 'View' or m.startswith(('pygame.', 'View.'))]; "
                  "sys.exit(1 if malos else 0)")
        resultado = subprocess.run([sys.executable, "-c", codigo], cwd=str(RAIZ), capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()

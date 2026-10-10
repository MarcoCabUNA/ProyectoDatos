"""
Pruebas de Data/CacheCatalogo.py (caché del catálogo en memoria, enunciado §4.4).
Usa las 11 fichas REALES del paquete (las lee FuenteOffline, igual que en el juego) y fichas
inventadas cuando hace falta un catálogo grande.
"""
import random
import time
import unittest

from Data.CacheCatalogo import TOPE_POR_DEFECTO, CacheCatalogo
from Data.FuenteOffline import FuenteOffline
from DTO.FichaEnemigoDTO import FichaEnemigoDTO
from DTO.FichaTrampaDTO import FichaTrampaDTO
from DTO.ObjetoDTO import ObjetoDTO
from tests.Utilidades import PAQUETE, catalogo_real


def fichas_reales() -> list:
    ids = [f["id"] for f in catalogo_real()]
    fuente = FuenteOffline(PAQUETE)
    return fuente.obtener_catalogo(ids[:10]) + fuente.obtener_catalogo(ids[10:])   # lotes de máximo 10


def ficha(id_ficha: str) -> ObjetoDTO:
    return ObjetoDTO(id=id_ficha, nombre=id_ficha, clase="arma", peso=1, valor=1, ataque_bonus=1)


def llena(tope: int, *ids: str) -> CacheCatalogo:
    c = CacheCatalogo(tope)
    for i in ids:
        c.insertar(ficha(i))
    return c


class PruebasCacheCatalogo(unittest.TestCase):

    # ------------------------------------------------------------ básico
    def test_nueva_vacia_y_tope_por_defecto(self):
        c = CacheCatalogo()
        self.assertEqual((c.tamano(), c.tope(), TOPE_POR_DEFECTO), (0, 25, 25))
        self.assertFalse(c.contiene("itm_antorcha"))
        self.assertIsNone(c.obtener("itm_antorcha"))
        self.assertEqual((c.aciertos(), c.fallos()), (0, 1))

    def test_tope_invalido(self):
        for malo in (0, -3):
            with self.assertRaises(ValueError):
                CacheCatalogo(malo)

    def test_fichas_reales_de_las_tres_clases(self):
        c = CacheCatalogo()
        fichas = fichas_reales()
        for f in fichas:
            self.assertEqual(c.insertar(f), [])
        self.assertEqual(c.tamano(), 11)
        for f in fichas:
            self.assertIs(c.obtener(f.id), f)               # la misma ficha, no una copia
        rata, dardos = c.obtener("ent_rata_gigante"), c.obtener("trp_dardos")
        self.assertIsInstance(rata, FichaEnemigoDTO)        # cada clase conserva su DTO
        self.assertIsInstance(dardos, FichaTrampaDTO)
        assert isinstance(rata, FichaEnemigoDTO) and isinstance(dardos, FichaTrampaDTO)
        self.assertEqual((rata.suelta, dardos.danio), (["itm_pocion_menor"], 4))
        self.assertEqual((c.aciertos(), c.fallos()), (13, 0))

    def test_contiene_no_cuenta_aciertos_ni_fallos(self):
        c = llena(5, "a")
        self.assertTrue(c.contiene("a"))
        self.assertFalse(c.contiene("b"))
        self.assertEqual((c.aciertos(), c.fallos()), (0, 0))

    def test_el_array_queda_ordenado_aunque_se_inserte_en_desorden(self):
        ids = [f"id_{i:03d}" for i in range(60)]
        desorden = list(ids)
        random.Random(7).shuffle(desorden)
        c = llena(100, *desorden)
        self.assertEqual(c.ids_en_memoria(), ids)
        for i in ids:
            self.assertTrue(c.contiene(i))
        for falta in ("id_", "id_060", "a", "zzz", "id_00"):   # antes del primero, después del último, en medio
            self.assertFalse(c.contiene(falta))

    def test_insertar_un_id_repetido_lo_reemplaza(self):
        c = llena(2, "a", "b")
        nueva = ObjetoDTO(id="a", nombre="Nueva", clase="arma", peso=9, valor=9)
        self.assertEqual(c.insertar(nueva), [])
        self.assertEqual(c.tamano(), 2)
        self.assertIs(c.obtener("a"), nueva)

    def test_ficha_sin_id(self):
        with self.assertRaises(ValueError):
            CacheCatalogo().insertar(ficha(""))

    # ------------------------------------------------------------ desalojo LRU
    def test_al_pasar_el_tope_sale_la_usada_hace_mas_tiempo(self):
        c = llena(3, "a", "b", "c")
        c.obtener("a")                       # orden de uso: a (reciente), c, b (vieja)
        self.assertEqual(c.insertar(ficha("d")), ["b"])
        self.assertEqual(c.ids_en_memoria(), ["a", "c", "d"])
        self.assertEqual(c.desalojos(), 1)
        self.assertIsNone(c.obtener("b"))   # volver a necesitarla es un fallo

    def test_tope_1(self):
        c = llena(1, "a")
        self.assertEqual(c.insertar(ficha("b")), ["a"])
        self.assertEqual(c.ids_en_memoria(), ["b"])

    # ------------------------------------------------------------ fichas en uso
    def test_una_ficha_en_uso_no_se_libera(self):
        c = llena(2, "a", "b")
        c.marcar_en_uso("a")                 # a es la más vieja, pero está en uso
        self.assertEqual(c.insertar(ficha("c")), ["b"])
        self.assertTrue(c.contiene("a"))
        self.assertTrue(c.esta_en_uso("a"))

    def test_todas_en_uso_queda_por_encima_del_tope_y_vuelve_al_liberar(self):
        c = llena(2, "a", "b")
        c.marcar_en_uso("a")
        c.marcar_en_uso("b")
        self.assertEqual(c.insertar(ficha("c")), [])     # no se puede liberar nada
        self.assertEqual(c.tamano(), 3)
        self.assertIsNotNone(c.obtener("c"))              # la recién insertada sigue ahí
        self.assertEqual(c.liberar_uso("a"), ["c"])       # c llevaba más tiempo sin usarse que a
        self.assertEqual(c.ids_en_memoria(), ["a", "b"])

    def test_varios_usos_de_la_misma_ficha(self):
        c = llena(1, "rata")
        c.marcar_en_uso("rata")              # dos ratas vivas
        c.marcar_en_uso("rata")
        self.assertEqual(c.liberar_uso("rata"), [])       # muere una: sigue en uso
        self.assertEqual(c.insertar(ficha("x")), [])       # rata en uso y x protegida: tamaño 2
        self.assertTrue(c.contiene("rata"))
        # Muere la otra: rata vuelve como la más reciente, así que sale x (más vieja).
        self.assertEqual(c.liberar_uso("rata"), ["x"])
        self.assertFalse(c.esta_en_uso("rata"))
        self.assertEqual(c.ids_en_memoria(), ["rata"])

    def test_errores_de_uso(self):
        c = llena(3, "a")
        with self.assertRaises(ValueError):
            c.liberar_uso("a")               # nunca se marcó
        with self.assertRaises(ValueError):
            c.marcar_en_uso("no_esta")
        with self.assertRaises(ValueError):
            c.liberar_uso("no_esta")
        self.assertFalse(c.esta_en_uso("no_esta"))

    def test_reemplazar_una_ficha_en_uso_no_pierde_sus_usos(self):
        c = llena(2, "a")
        c.marcar_en_uso("a")
        c.insertar(ficha("a"))
        self.assertTrue(c.esta_en_uso("a"))
        c.liberar_uso("a")
        self.assertFalse(c.esta_en_uso("a"))

    # ------------------------------------------------------------ después de un retroceso
    def test_reiniciar_usos_no_libera_nada_hasta_ajustar(self):
        c = llena(2, "a", "b")
        c.marcar_en_uso("a")
        c.marcar_en_uso("a")
        c.marcar_en_uso("b")
        c.insertar(ficha("c"))                       # todas en uso: queda en 3, por encima del tope
        c.reiniciar_usos()
        self.assertFalse(c.esta_en_uso("a") or c.esta_en_uso("b"))
        self.assertEqual(c.tamano(), 3)              # reiniciar no desaloja
        c.marcar_en_uso("b")                         # el estado restaurado solo usa b
        self.assertEqual(c.ajustar_al_tope(), ["c"])  # c era la usada hace más tiempo; b está en uso
        self.assertEqual(c.ids_en_memoria(), ["a", "b"])
        with self.assertRaises(ValueError):
            c.liberar_uso("a")                       # a quedó sin usos

    def test_reiniciar_usos_sin_nada_en_uso_no_cambia_nada(self):
        c = llena(3, "a", "b", "c")
        c.reiniciar_usos()
        self.assertEqual(c.insertar(ficha("d")), ["a"])   # el orden LRU se conservó

    # ------------------------------------------------------------ contra un modelo simple
    def test_operaciones_al_azar_contra_un_modelo(self):
        """
        Modelo ingenuo con listas (lento pero obvio): 'orden' tiene los ids en memoria del más
        reciente al más viejo y 'usos' cuántos usos tiene cada uno. Se comparan miles de pasos.
        """
        azar = random.Random(2026)
        for _ in range(40):
            tope = azar.randint(1, 6)
            c = CacheCatalogo(tope)
            orden: list[str] = []
            usos: list[int] = []
            for _ in range(150):
                op = azar.randint(0, 3)
                i = f"f{azar.randint(0, 9)}"
                if op == 0:                                   # obtener
                    esperado = i in orden
                    self.assertEqual(c.obtener(i) is not None, esperado)
                    if esperado:
                        k = orden.index(i)
                        orden.insert(0, orden.pop(k))
                        usos.insert(0, usos.pop(k))
                elif op == 1:                                 # insertar
                    liberadas = c.insertar(ficha(i))
                    if i in orden:
                        k = orden.index(i)
                        orden.insert(0, orden.pop(k))
                        usos.insert(0, usos.pop(k))
                        esperadas = []
                    else:
                        orden.insert(0, i)
                        usos.insert(0, 0)
                        esperadas = self._liberar_modelo(orden, usos, tope, protegida=i)
                    self.assertEqual(liberadas, esperadas)
                elif op == 2 and i in orden:                  # marcar en uso
                    c.marcar_en_uso(i)
                    usos[orden.index(i)] += 1
                elif op == 3 and i in orden and usos[orden.index(i)] > 0:   # liberar uso
                    liberadas = c.liberar_uso(i)
                    k = orden.index(i)
                    usos[k] -= 1
                    esperadas = []
                    if usos[k] == 0:
                        orden.insert(0, orden.pop(k))
                        usos.insert(0, usos.pop(k))
                        esperadas = self._liberar_modelo(orden, usos, tope, protegida=None)
                    self.assertEqual(liberadas, esperadas)
                ordenados = list(orden)
                ordenados.sort()   # sort solo dentro de la prueba, para comparar
                self.assertEqual(c.ids_en_memoria(), ordenados)

    @staticmethod
    def _liberar_modelo(orden, usos, tope, protegida):
        """
        Mientras sobren fichas, saca la más vieja que no esté en uso. Una ficha en uso conserva el
        lugar de su último uso real; al dejar de estar en uso vuelve a ser la más reciente.
        """
        liberadas = []
        while len(orden) > tope:
            k = len(orden) - 1
            while k >= 0 and usos[k] > 0:
                k -= 1
            if k < 0 or orden[k] == protegida:
                break
            liberadas.append(orden.pop(k))
            usos.pop(k)
        return liberadas

    # ------------------------------------------------------------ costo
    def test_buscar_cuesta_logaritmico(self):
        """Con búsqueda lineal, pasar de 1.000 a 100.000 fichas haría cada consulta ~100 veces más lenta."""
        def ns_por_consulta(n):
            c = CacheCatalogo(n)
            for k in range(n):                     # en orden: cada insertar va al final, sin correr nada
                c.insertar(ficha(f"f{k:06d}"))
            consultas = [f"f{k:06d}" for k in range(0, n, max(1, n // 2000))]
            inicio = time.perf_counter()
            for _ in range(5):
                for i in consultas:
                    c.contiene(i)
            return (time.perf_counter() - inicio) / (5 * len(consultas))
        pequeno, grande = ns_por_consulta(1_000), ns_por_consulta(100_000)
        self.assertLess(grande, pequeno * 10)


if __name__ == "__main__":
    unittest.main()
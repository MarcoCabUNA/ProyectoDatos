"""
Pruebas de AlmacenSprites (Etapa 3) con los recursos reales (<raiz>/assets) y con carpetas temporales casi vacías.
Se ejecuta desde cualquier carpeta.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayudas_controladores import RAIZ  # noqa: E402
from ayudas_pygame import pygame  # noqa: E402  (fija SDL_VIDEODRIVER=dummy antes de importar pygame)

from DTO.Direcciones import E, N, O, S  # noqa: E402
from View.AlmacenSprites import ORIGEN_FIGURA, AlmacenSprites  # noqa: E402

ASSETS = str(RAIZ / "assets")


def _ventana():
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((200, 200))          # convert_alpha() la necesita


def _carpeta_con(*archivos):
    """Una carpeta de recursos temporal con solo esos archivos (rutas relativas a 'assets'); cada uno, una imagen 8x8."""
    carpeta = tempfile.mkdtemp()
    for relativa in archivos:
        ruta = os.path.join(carpeta, relativa)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        imagen = pygame.Surface((8, 8), pygame.SRCALPHA)
        imagen.fill((255, 0, 0, 255))
        pygame.image.save(imagen, ruta)
    return carpeta


def _con_almacen(ruta, prueba):
    _ventana()
    try:
        prueba(AlmacenSprites(ruta))
    finally:
        pygame.quit()


def _con_carpeta(archivos, prueba):
    carpeta = _carpeta_con(*archivos)
    try:
        _con_almacen(carpeta, prueba)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------- recursos reales
def probar_el_jugador_tiene_3_idle_1_ataque_y_los_estados_inexistentes_caen_a_idle():
    def prueba(almacen):
        idle = almacen.actor("jugador")
        assert len(idle.fotogramas) == 3 and idle.origen == "personajes/jugador_idle"
        ataque = almacen.actor("jugador", "ataque")
        assert len(ataque.fotogramas) == 1 and ataque.origen == "personajes/jugador_ataque"
        assert len(almacen.actor("jugador", "caminar").fotogramas) == 3
        inexistente = almacen.actor("jugador", "bailar")
        assert len(inexistente.fotogramas) == 3 and inexistente.origen == "personajes/jugador_idle"
    _con_almacen(ASSETS, prueba)


def probar_la_rata_gigante_tiene_idle_1_ataque_2_y_caminar_y_muerte_caen_a_idle():
    def prueba(almacen):
        assert len(almacen.actor("ent_rata_gigante").fotogramas) == 1
        ataque = almacen.actor("ent_rata_gigante", "ataque")
        assert len(ataque.fotogramas) == 2 and ataque.origen == "enemigos/ent_rata_gigante_ataque"
        for estado in ("caminar", "muerte"):
            conjunto = almacen.actor("ent_rata_gigante", estado)
            assert len(conjunto.fotogramas) == 1 and conjunto.origen == "enemigos/ent_rata_gigante_idle", estado
    _con_almacen(ASSETS, prueba)


def probar_el_enemigo_generico_y_los_enemigos_sin_sprites_propios():
    def prueba(almacen):
        generico = almacen.actor("enemigo")
        assert len(generico.fotogramas) == 1 and generico.origen == "enemigos/enemigo_idle"
        assert len(almacen.actor("enemigo", "ataque").fotogramas) == 4
        assert len(almacen.actor("enemigo", "muerte").fotogramas) == 4
        for tipo in ("ent_guardian_oseo", "ent_que_no_existe"):
            assert almacen.actor(tipo).origen == "enemigos/enemigo_idle", tipo
            assert almacen.actor(tipo, "ataque").origen == "enemigos/enemigo_ataque", tipo
    _con_almacen(ASSETS, prueba)


def probar_objetos_reales_y_respaldo():
    def prueba(almacen):
        assert almacen.objeto("itm_daga_oxidada", "arma", 64).origen == "objetos/itm_daga_oxidada"
        desconocido = almacen.objeto("itm_no_existe", "arma", 64)
        assert desconocido.origen == "objetos/objeto" and len(desconocido.fotogramas) == 1
        for conjunto in (almacen.objeto("itm_daga_oxidada", "arma", 64), desconocido):
            assert max(conjunto.fotogramas[0].get_size()) == 64
    _con_almacen(ASSETS, prueba)


def probar_los_fotogramas_recortados_tienen_los_pies_en_el_borde_inferior():
    def prueba(almacen):
        for tipo, estado in (("jugador", "idle"), ("jugador", "ataque"), ("ent_rata_gigante", "idle"),
                             ("enemigo", "ataque")):
            for fotograma in almacen.actor(tipo, estado, 0.5).fotogramas:
                assert fotograma.get_bounding_rect().bottom == fotograma.get_height(), (tipo, estado)
        alturas = [f.get_height() for f in almacen.actor("jugador", "idle", 0.5).fotogramas]
        assert len(alturas) == 3                 # (los lienzos originales miden distinto; el recorte los iguala al contenido)
    _con_almacen(ASSETS, prueba)


def probar_la_escala_multiplica_el_tamano_sin_suavizar():
    def prueba(almacen):
        entero = almacen.actor("jugador", "idle", 1.0).fotogramas[0]
        mitad = almacen.actor("jugador", "idle", 0.5).fotogramas[0]
        assert abs(entero.get_width() - 2 * mitad.get_width()) <= 1
        assert abs(entero.get_height() - 2 * mitad.get_height()) <= 1
        puerta = almacen.puerta("puerta_cerrada", N, 2.0).fotogramas[0]
        assert puerta.get_size() == (98, 72)
        original = pygame.image.load(os.path.join(ASSETS, "ui", "puerta_cerrada.png"))
        usados = [original.get_at((x, y)) for x in range(original.get_width()) for y in range(original.get_height())]
        for x in range(puerta.get_width()):
            for y in range(puerta.get_height()):
                assert puerta.get_at((x, y)) in usados      # vecino más cercano: no aparecen colores nuevos
    _con_almacen(ASSETS, prueba)


def probar_las_puertas_se_giran_hacia_su_borde():
    def prueba(almacen):
        norte = almacen.puerta("puerta_cerrada", N, 3.0).fotogramas[0]
        ancho, alto = norte.get_size()
        grados = [(N, 0), (S, 180), (E, 270), (O, 90)]                  # antihorario, como pygame.transform.rotate
        for direccion, giro in grados:
            esperada = pygame.transform.rotate(norte, giro)
            obtenida = almacen.puerta("puerta_cerrada", direccion, 3.0).fotogramas[0]
            assert obtenida.get_size() == esperada.get_size(), direccion
            assert pygame.image.tobytes(obtenida, "RGBA") == pygame.image.tobytes(esperada, "RGBA"), direccion
        assert almacen.puerta("puerta_cerrada", E, 3.0).fotogramas[0].get_size() == (alto, ancho)
        final = almacen.puerta("puerta_final", S, 1.0)
        assert final.origen == "ui/puerta_final"
    _con_almacen(ASSETS, prueba)


def probar_fondos_y_ui():
    def prueba(almacen):
        fondo = almacen.fondo("fondo_regular", (688, 384))
        assert fondo.origen == "fondos/fondo_regular" and fondo.fotogramas[0].get_size() == (688, 384)
        for nombre in ("fondo_inicial", "fondo_final", "fondo_menu", "fondo_victoria", "fondo_derrota"):
            assert almacen.fondo(nombre, (100, 60)).origen == f"fondos/{nombre}"
        ausente = almacen.fondo("fondo_que_no_existe", (100, 60))
        assert ausente.origen == ORIGEN_FIGURA and ausente.fotogramas[0].get_size() == (100, 60)
        assert almacen.ui("inventario", 1.0).origen == "ui/inventario"
    _con_almacen(ASSETS, prueba)


# ---------------------------------------------------------------- carpetas casi vacías: nada debe fallar
def probar_con_la_carpeta_vacia_todo_cae_a_figuras_sin_fallar():
    def prueba(almacen):
        assert almacen.actor("jugador").origen == ORIGEN_FIGURA
        figura = almacen.actor("ent_rata_gigante", nombre="Rata gigante #1")
        assert figura.origen == ORIGEN_FIGURA and len(figura.fotogramas) == 1 and figura.fotogramas[0].get_width() > 0
        assert almacen.objeto("itm_daga_oxidada", "arma", 48).origen == ORIGEN_FIGURA
        assert almacen.objeto("itm_daga_oxidada", "arma", 48).fotogramas[0].get_size() == (48, 48)
        assert almacen.fondo("fondo_regular", (50, 50)).origen == ORIGEN_FIGURA
        assert almacen.ui("puerta_cerrada").origen == ORIGEN_FIGURA
        assert almacen.puerta("puerta_final", E).origen == ORIGEN_FIGURA
    _con_carpeta([], prueba)


def probar_el_respaldo_de_clase_y_el_generico_en_una_carpeta_minima():
    def prueba(almacen):
        assert almacen.objeto("itm_x", "arma", 32).origen == "objetos/clase_arma"
        assert almacen.objeto("itm_x", "pocion", 32).origen == "objetos/objeto"
        assert almacen.actor("ent_nuevo").origen == "enemigos/enemigo_idle"
    _con_carpeta(["objetos/clase_arma.png", "objetos/objeto.png", "enemigos/enemigo_idle_1.png"], prueba)


def probar_un_id_inseguro_se_trata_como_inexistente_y_no_sale_de_la_carpeta():
    carpeta = _carpeta_con("x_idle_1.png", "x.png", "enemigos/enemigo_idle_1.png", "objetos/objeto.png")
    try:
        def prueba(almacen):
            for peligroso in ("../x", "..\\x", "a/b", "../../x", "", "x.png", "con"):
                assert almacen.actor(peligroso).origen == "enemigos/enemigo_idle", peligroso   # usa el genérico
                assert almacen.objeto(peligroso, "arma", 16).origen == "objetos/objeto", peligroso
            assert almacen.actor("x").origen == "enemigos/enemigo_idle"          # x_idle_1 está FUERA de enemigos/
            assert almacen.actor("enemigo", "../x").origen == "enemigos/enemigo_idle"
        _con_almacen(carpeta, prueba)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------- ventana y archivos dañados
def probar_pedir_un_sprite_sin_ventana_lanza_un_error_claro_y_no_recuerda_el_fallo():
    pygame.display.init()
    pygame.font.init()
    try:
        almacen = AlmacenSprites(ASSETS)
        for pedir in (lambda: almacen.actor("jugador"), lambda: almacen.objeto("itm_daga_oxidada", "arma", 32),
                      lambda: almacen.fondo("fondo_regular", (50, 50)), lambda: almacen.ui("inventario")):
            try:
                pedir()
            except RuntimeError as error:
                assert "ventana" in str(error)
            else:
                raise AssertionError("debía fallar sin ventana")
        assert almacen.entradas_cache == 0 and almacen.accesos_disco == 0
        pygame.display.set_mode((200, 200))                  # ahora sí hay ventana: el MISMO almacén funciona
        assert almacen.actor("jugador").origen == "personajes/jugador_idle"
        assert almacen.objeto("itm_daga_oxidada", "arma", 32).origen == "objetos/itm_daga_oxidada"
    finally:
        pygame.quit()


def probar_un_archivo_danado_cae_al_respaldo_sin_fallar():
    carpeta = _carpeta_con("enemigos/enemigo_idle_1.png", "objetos/objeto.png")
    try:
        with open(os.path.join(carpeta, "enemigos", "ent_roto_idle_1.png"), "wb") as archivo:
            archivo.write(b"esto no es un PNG")
        with open(os.path.join(carpeta, "objetos", "itm_roto.png"), "wb") as archivo:
            archivo.write(b"esto tampoco")

        def prueba(almacen):
            assert almacen.actor("ent_roto").origen == "enemigos/enemigo_idle"
            assert almacen.objeto("itm_roto", "arma", 16).origen == "objetos/objeto"
        _con_almacen(carpeta, prueba)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# ---------------------------------------------------------------- caché
def probar_dos_pedidos_iguales_no_vuelven_a_leer_el_disco_y_devuelven_el_mismo_objeto():
    def prueba(almacen):
        pedidos = [lambda: almacen.actor("jugador", "idle", 0.5), lambda: almacen.actor("ent_guardian_oseo", "ataque"),
                   lambda: almacen.objeto("itm_no_existe", "arma", 48), lambda: almacen.objeto("itm_daga_oxidada", "arma", 48),
                   lambda: almacen.fondo("fondo_regular", (100, 60)), lambda: almacen.fondo("fondo_nada", (100, 60)),
                   lambda: almacen.puerta("puerta_cerrada", E, 2.0)]
        primeras = [pedir() for pedir in pedidos]
        accesos = almacen.accesos_disco
        assert accesos > 0
        segundas = [pedir() for pedir in pedidos]
        assert almacen.accesos_disco == accesos
        for primera, segunda in zip(primeras, segundas):
            assert primera is segunda
    _con_almacen(ASSETS, prueba)


def probar_los_nombres_que_no_existen_tambien_se_recuerdan():
    def prueba(almacen):
        almacen.actor("ent_fantasma")
        accesos = almacen.accesos_disco
        almacen.actor("ent_fantasma", "ataque")             # estado distinto: el conjunto propio ya se sabe inexistente
        nuevos = almacen.accesos_disco - accesos
        almacen.actor("ent_fantasma", "ataque", 0.25)       # otra escala: no hay que volver al disco
        almacen.actor("ent_fantasma", "idle", 2.0, "Otro")
        assert almacen.accesos_disco - accesos == nuevos
        assert nuevos <= 6                                  # solo los nombres nuevos del estado "ataque", una vez cada uno
        almacen.objeto("itm_fantasma", "arma", 32)          # no existe ni él ni clase_arma: se recuerda cada nombre
        accesos = almacen.accesos_disco
        almacen.objeto("itm_fantasma", "arma", 64)          # otro tamaño: otra clave de caché, mismos nombres
        almacen.objeto("itm_fantasma", "pocion", 64)        # solo clase_pocion es un nombre nuevo
        assert almacen.accesos_disco - accesos == 1
    _con_almacen(ASSETS, prueba)


# ---------------------------------------------------------------- higiene (sección 10.1 de la guía)
def probar_instancias_distintas_del_mismo_tipo_comparten_el_conjunto_y_la_cache_no_crece():
    def prueba(almacen):
        primera = almacen.actor("ent_rata_gigante", "idle", 0.5, "Rata gigante #1")
        entradas = almacen.entradas_cache
        for numero in range(2, 9):
            otra = almacen.actor("ent_rata_gigante", "idle", 0.5, f"Rata gigante #{numero}")
            assert otra is primera
        assert almacen.entradas_cache == entradas
        guardian = almacen.actor("ent_guardian_oseo", "idle", 0.5, "Guardián óseo #1")
        entradas = almacen.entradas_cache
        assert almacen.actor("ent_guardian_oseo", "idle", 0.5, "Guardián óseo #2") is guardian
        assert almacen.entradas_cache == entradas
    _con_almacen(ASSETS, prueba)


def probar_la_figura_de_respaldo_se_comparte_por_inicial():
    def prueba(almacen):
        uno = almacen.actor("ent_x", "idle", 0.5, "Rata #1")
        assert uno.origen == ORIGEN_FIGURA
        entradas = almacen.entradas_cache
        assert almacen.actor("ent_x", "idle", 0.5, "Rata #2") is uno          # misma inicial: la misma figura
        assert almacen.entradas_cache == entradas
        otro = almacen.actor("ent_x", "idle", 0.5, "Araña #1")
        assert otro is not uno and otro.origen == ORIGEN_FIGURA                # otra inicial: otra figura
    _con_carpeta([], prueba)


def probar_el_codigo_de_la_vista_no_usa_dict_ni_set_ni_ordenamientos():
    carpeta = RAIZ / "View"
    assert (carpeta / "AlmacenSprites.py").is_file()
    for ruta in carpeta.glob("*.py"):
        codigo = ruta.read_text(encoding="utf-8")
        for prohibido in ("dict(", "set(", "{}", "sorted(", ".sort(", "defaultdict", "OrderedDict", "frozenset("):
            assert prohibido not in codigo, (ruta.name, prohibido)


if __name__ == "__main__":
    probar_el_jugador_tiene_3_idle_1_ataque_y_los_estados_inexistentes_caen_a_idle()
    probar_la_rata_gigante_tiene_idle_1_ataque_2_y_caminar_y_muerte_caen_a_idle()
    probar_el_enemigo_generico_y_los_enemigos_sin_sprites_propios()
    probar_objetos_reales_y_respaldo()
    probar_los_fotogramas_recortados_tienen_los_pies_en_el_borde_inferior()
    probar_la_escala_multiplica_el_tamano_sin_suavizar()
    probar_las_puertas_se_giran_hacia_su_borde()
    probar_fondos_y_ui()
    probar_con_la_carpeta_vacia_todo_cae_a_figuras_sin_fallar()
    probar_el_respaldo_de_clase_y_el_generico_en_una_carpeta_minima()
    probar_un_id_inseguro_se_trata_como_inexistente_y_no_sale_de_la_carpeta()
    probar_pedir_un_sprite_sin_ventana_lanza_un_error_claro_y_no_recuerda_el_fallo()
    probar_un_archivo_danado_cae_al_respaldo_sin_fallar()
    probar_dos_pedidos_iguales_no_vuelven_a_leer_el_disco_y_devuelven_el_mismo_objeto()
    probar_instancias_distintas_del_mismo_tipo_comparten_el_conjunto_y_la_cache_no_crece()
    probar_la_figura_de_respaldo_se_comparte_por_inicial()
    probar_los_nombres_que_no_existen_tambien_se_recuerdan()
    probar_el_codigo_de_la_vista_no_usa_dict_ni_set_ni_ordenamientos()
    print("OK: todas las pruebas de AlmacenSprites pasaron")

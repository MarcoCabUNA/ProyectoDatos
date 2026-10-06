"""
DescargadorPaquete (Integrante 2): arma el paquete del modo --offline.

Según el profesor, el paquete offline son los JSON que se obtienen al llamar al API.
Esta clase descarga UNA cripta completa por la red y guarda esas respuestas en disco:

    paquete/
    ├── criptas.json              GET /criptas (tal cual)
    ├── catalogo_version.json     GET /catalogo/version (tal cual)
    ├── catalogo.json             {"entidades": [...]}  TODAS las fichas descargadas, juntas
    └── cripta-01/
        ├── general.json          GET /criptas/cripta-01 (tal cual)
        ├── salas_p1.json         GET /criptas/cripta-01/salas?pagina=1 (tal cual), una por página
        └── contenido.json        {"contenido": [...]}  el contenido de TODAS las salas, junto

Contenido y catálogo se guardan juntos (no una respuesta por lote) para que FuenteOffline
pueda responder cualquier combinación de salas o ids, aunque el juego pida lotes
distintos a los de la descarga.

El catálogo se comparte entre criptas: si ya existe y su versión coincide con la del API,
las fichas nuevas se agregan a las que ya estaban. Si la versión cambió, se empieza de cero.

Uso (desde la raíz del proyecto):
    python -m Data.DescargadorPaquete cripta-01
    python -m Data.DescargadorPaquete cripta-01 otra_carpeta
"""
import json
import os
import sys

from Data.ClienteHttp import ClienteHttp, ErrorRed
from Data.FuenteRed import URL_BASE
from Security.ValidadorAcceso import generar_client_id

CARPETA_POR_DEFECTO = "paquete"
LOTE = 10   # el API acepta hasta 10 salas o 10 ids por solicitud


class DescargadorPaquete:

    def __init__(self, carpeta: str = CARPETA_POR_DEFECTO, cliente: ClienteHttp | None = None):
        self._carpeta = carpeta
        self._cliente = cliente if cliente is not None else ClienteHttp(URL_BASE, generar_client_id())

    def descargar(self, id_cripta: str) -> None:
        """Descarga la cripta completa y escribe el paquete. Lanza ErrorRed si algo falla."""
        self._validar_id(id_cripta)

        criptas = self._cliente.get_json("criptas", "listar criptas")
        if not self._existe_cripta(criptas, id_cripta):
            raise ErrorRed("descargar paquete", f"la cripta {id_cripta!r} no está publicada")

        general = self._cliente.get_json(f"criptas/{id_cripta}", f"datos generales de {id_cripta}")
        paginas = self._descargar_paginas(id_cripta, general)
        ids_salas = self._ids_de_salas(paginas)
        contenido = self._descargar_contenido(id_cripta, ids_salas)

        version_catalogo = self._cliente.get_json("catalogo/version", "versión del catálogo")
        fichas = self._fichas_existentes(version_catalogo)
        self._descargar_catalogo(self._ids_de_catalogo(contenido, general), fichas)

        # Se escribe todo al final: si algo falló antes, el paquete anterior queda intacto.
        carpeta_cripta = os.path.join(self._carpeta, id_cripta)
        os.makedirs(carpeta_cripta, exist_ok=True)
        self._escribir(os.path.join(self._carpeta, "criptas.json"), criptas)
        self._escribir(os.path.join(self._carpeta, "catalogo_version.json"), version_catalogo)
        self._escribir(os.path.join(self._carpeta, "catalogo.json"), {"entidades": fichas})
        self._escribir(os.path.join(carpeta_cripta, "general.json"), general)
        for i in range(len(paginas)):
            self._escribir(os.path.join(carpeta_cripta, f"salas_p{i + 1}.json"), paginas[i])
        self._escribir(os.path.join(carpeta_cripta, "contenido.json"), {"contenido": contenido})

    def solicitudes_realizadas(self) -> int:
        return self._cliente.solicitudes_realizadas

    # ------------------------------------------------------------ descarga
    def _descargar_paginas(self, id_cripta: str, general: dict) -> list:
        paginas = []
        for p in range(1, general["paginas"] + 1):
            paginas.append(self._cliente.get_json(f"criptas/{id_cripta}/salas",
                                                  f"esqueleto de {id_cripta}, página {p}",
                                                  (("pagina", p),)))
        return paginas

    def _descargar_contenido(self, id_cripta: str, ids_salas: list[int]) -> list:
        """Contenido de todas las salas, en lotes de 10, en el orden de ids_salas."""
        contenido = []
        for inicio in range(0, len(ids_salas), LOTE):
            lote = ids_salas[inicio:inicio + LOTE]
            texto = ",".join(str(i) for i in lote)
            respuesta = self._cliente.get_json(f"criptas/{id_cripta}/contenido",
                                               f"contenido de {id_cripta}, salas {texto}",
                                               (("salas", texto),))
            for id_sala in lote:   # se guarda en el orden pedido y se verifica que no falte nada
                contenido.append(self._buscar(respuesta["contenido"], "sala", id_sala, "contenido"))
        return contenido

    def _descargar_catalogo(self, ids: list[str], fichas: list) -> None:
        """
        Agrega a 'fichas' las que falten de 'ids', en lotes de 10. Si un enemigo suelta
        objetos que todavía no están, también se descargan (se repite hasta que no falte nada).
        """
        pendientes = self._faltantes(ids, fichas)
        while len(pendientes) > 0:
            nuevas = []
            for inicio in range(0, len(pendientes), LOTE):
                lote = pendientes[inicio:inicio + LOTE]
                texto = ",".join(lote)
                respuesta = self._cliente.get_json("catalogo", f"catálogo de {texto}", (("ids", texto),))
                for id_ficha in lote:
                    ficha = self._buscar(respuesta["entidades"], "id", id_ficha, "catálogo")
                    fichas.append(ficha)
                    nuevas.append(ficha)
            sueltas = []
            for ficha in nuevas:
                for id_objeto in ficha.get("suelta") or []:
                    self._agregar_sin_repetir(sueltas, id_objeto)
            pendientes = self._faltantes(sueltas, fichas)

    def _fichas_existentes(self, version_catalogo: dict) -> list:
        """Fichas del paquete anterior, solo si su versión de catálogo sigue vigente."""
        ruta_version = os.path.join(self._carpeta, "catalogo_version.json")
        ruta_catalogo = os.path.join(self._carpeta, "catalogo.json")
        if not (os.path.exists(ruta_version) and os.path.exists(ruta_catalogo)):
            return []
        if self._leer(ruta_version).get("version") != version_catalogo.get("version"):
            return []   # el catálogo cambió en el API: las fichas viejas ya no son válidas
        return list(self._leer(ruta_catalogo).get("entidades", []))

    # ------------------------------------------------------------ ids
    @staticmethod
    def _ids_de_salas(paginas: list) -> list[int]:
        ids = []
        for pagina in paginas:
            for sala in pagina["salas"]:
                ids.append(sala["id"])
        return ids

    def _ids_de_catalogo(self, contenido: list, general: dict) -> list[str]:
        """Todos los ids de catálogo que aparecen en las salas, sin repetir."""
        ids: list[str] = []
        for sala in contenido:
            for enemigo in sala.get("enemigos", []):
                self._agregar_sin_repetir(ids, enemigo["tipo"])
            for id_objeto in sala.get("objetos", []):
                self._agregar_sin_repetir(ids, id_objeto)
            for trampa in sala.get("trampas", []):
                self._agregar_sin_repetir(ids, trampa["tipo"])
        self._agregar_sin_repetir(ids, general["llave_salida"])
        return ids

    @staticmethod
    def _faltantes(ids: list[str], fichas: list) -> list[str]:
        """Los ids que todavía no tienen ficha. Búsqueda lineal (herramienta de descarga, no del juego)."""
        resultado = []
        for id_ficha in ids:
            encontrado = False
            for ficha in fichas:
                if ficha["id"] == id_ficha:
                    encontrado = True
                    break
            if not encontrado:
                resultado.append(id_ficha)
        return resultado

    @staticmethod
    def _agregar_sin_repetir(lista: list, valor) -> None:
        for x in lista:
            if x == valor:
                return
        lista.append(valor)

    # ------------------------------------------------------------ auxiliares
    @staticmethod
    def _existe_cripta(criptas: dict, id_cripta: str) -> bool:
        for c in criptas["criptas"]:
            if c["id"] == id_cripta:
                return True
        return False

    @staticmethod
    def _buscar(elementos: list, campo: str, valor, que: str) -> dict:
        for e in elementos:
            if e[campo] == valor:
                return e
        raise ErrorRed(f"descargar {que}", f"la respuesta no incluye {valor!r}")

    @staticmethod
    def _validar_id(id_cripta: str) -> None:
        """El id se usa como nombre de carpeta: solo letras, números, '-' y '_'."""
        if id_cripta == "":
            raise ValueError("id de cripta vacío")
        for caracter in id_cripta:
            if not (caracter.isalnum() or caracter in "-_"):
                raise ValueError(f"id de cripta no válido como nombre de carpeta: {id_cripta!r}")

    @staticmethod
    def _escribir(ruta: str, datos) -> None:
        """Escribe en un archivo temporal y luego lo reemplaza, para no dejar archivos a medias."""
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)

    @staticmethod
    def _leer(ruta: str):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)


def main(argumentos: list[str]) -> int:
    if len(argumentos) < 1 or len(argumentos) > 2:
        print("Uso: python -m Data.DescargadorPaquete <id_cripta> [carpeta]")
        return 2
    carpeta = argumentos[1] if len(argumentos) == 2 else CARPETA_POR_DEFECTO
    descargador = DescargadorPaquete(carpeta)
    try:
        descargador.descargar(argumentos[0])
    except (ErrorRed, ValueError) as e:
        print("ERROR:", e)
        return 1
    print(f"Paquete de {argumentos[0]} guardado en '{carpeta}/' "
          f"({descargador.solicitudes_realizadas()} solicitudes).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
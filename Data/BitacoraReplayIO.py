"""
BitacoraReplayIO (Integrante 2): escribe y lee el log de la partida para --replay (enunciado §4.11).

Solo guarda y entrega datos crudos (encabezado + AccionDTO). Decidir si se reproduce, y
reproducir, es de Servicios (ServicioReplay, Integrante 3), como dice la Guía.

Formato del archivo (texto UTF-8, versión 1 del formato):

    #CRIPTA-REPLAY 1
    id_cripta=cripta-01
    version_cripta=fd58f7743b9e
    version_catalogo=be68d322d2f5
    semilla=12345
    #ACCIONES
    mover|0||                    <- una línea por acción: AccionDTO.a_linea() (Integrante 3)
    recoger|||itm_daga_oxidada

Uso desde Servicios:
    # partida normal
    bitacora = BitacoraReplayIO("logs/partida_001.log")
    bitacora.iniciar(EncabezadoReplayDTO(cripta.id, cripta.version, resolvedor.version_catalogo(), semilla))
    bitacora.anexar(accion)                 # después de cada acción del jugador

    # al guardar la partida (paso 12b): el guardado lleva bitacora.ruta() y bitacora.acciones_escritas()
    # al cargar esa partida: log nuevo con las primeras N acciones del anterior, y se sigue anexando ahí
    bitacora = BitacoraReplayIO.continuar_desde(ruta_guardada, n_guardado, "logs/partida_002.log", encabezado)

    # --replay partida.log
    partida = BitacoraReplayIO.leer(config.replay)          # lanza ErrorBitacora si no se puede
    problemas = comprobar_compatibilidad(partida.encabezado, cripta.version, resolvedor.version_catalogo())
    if problemas: avisar que no se puede garantizar una reproducción fiel (§4.11, Apéndice B)

Decisiones:
  - Solo anexado: iniciar() crea el archivo y NUNCA sobrescribe uno que ya exista; anexar()
    abre en modo "a", escribe una línea y cierra. Al cerrar, la línea ya quedó en el archivo:
    si el programa se cae después, el log tiene todas las acciones hasta ese momento.
  - Antes de escribir una acción se comprueba que al leerla vuelva igual
    (desde_linea(a_linea(a)) == a). Así nunca se escribe una línea que el replay leería distinto
    (por ejemplo un id con '|' o un campo vacío "" que se leería como None).
  - Si la última línea quedó a medio escribir (sin el '\\n' final) se descarta y se avisa en
    PartidaReplayDTO.ultima_linea_descartada: aunque se pudiera leer, podría estar cortada
    ("atacar||e-20" en lugar de "e-201") y reproduciría otra cosa.
  - Cualquier otra línea mal formada es un error con su número de línea: no se reproduce algo dudoso.
    Una acción solo se acepta si es exactamente lo que escribiría a_linea() (por ejemplo,
    "mover| 0||" se rechaza aunque desde_linea() la pudiera leer).
  - Se escribe con newline="" para que Windows no cambie '\\n' por '\\r\\n'; al leer se acepta
    '\\r\\n' por si alguien abrió y guardó el log con un editor.
  - El encabezado se lee con 4 variables, sin dict (restricción del enunciado §7).

  - Partida cargada (paso 12b): en lugar de recortar el log anterior (eso no sería solo anexado) o
    meter todas las acciones dentro del archivo de guardado (lo haría crecer en cada guardado),
    el guardado solo recuerda la ruta del log y cuántas acciones tenía; continuar_desde() copia esas
    acciones a un log nuevo. Así una partida cargada se sigue pudiendo reproducir desde la semilla.

Costos (n = acciones del log):
    anexar            O(1) por acción (abrir en modo "a" no lee lo que ya hay)
    leer              O(n) tiempo y memoria (el array de acciones)
    continuar_desde   O(n) una sola vez al cargar (lee el log anterior y escribe el nuevo de una vez)
"""
import os

from DTO.AccionDTO import AccionDTO
from DTO.ReplayDTO import EncabezadoReplayDTO, PartidaReplayDTO
from Security.ValidadorAcceso import validar_version

VERSION_FORMATO = 1
_PREFIJO_FORMATO = "#CRIPTA-REPLAY "
_LINEA_FORMATO = f"{_PREFIJO_FORMATO}{VERSION_FORMATO}"
_LINEA_ACCIONES = "#ACCIONES"

_CLAVE_ID = "id_cripta"
_CLAVE_VERSION_CRIPTA = "version_cripta"
_CLAVE_VERSION_CATALOGO = "version_catalogo"
_CLAVE_SEMILLA = "semilla"


class ErrorBitacora(ValueError):
    """El log no se puede escribir o leer. El mensaje dice qué pasó (y en qué línea, si aplica)."""


class BitacoraReplayIO:
    """Escribe el log de UNA partida. Para leer un log se usa BitacoraReplayIO.leer(ruta)."""

    def __init__(self, ruta: str):
        self._ruta = ruta
        self._iniciada = False
        self._acciones_escritas = 0

    # ------------------------------------------------------------ escritura
    def iniciar(self, encabezado: EncabezadoReplayDTO) -> None:
        """Crea el archivo con el encabezado. Crea la carpeta si falta. Nunca sobrescribe un log."""
        self._crear(encabezado, [])

    @staticmethod
    def continuar_desde(ruta_anterior: str, cantidad: int, ruta_nueva: str,
                        encabezado_esperado: EncabezadoReplayDTO | None = None) -> "BitacoraReplayIO":
        """
        Para cargar una partida guardada sin perder el replay. El guardado recuerda el log de la partida
        (ruta()) y cuántas acciones tenía al guardar (acciones_escritas()). Al cargar, esto crea un log
        NUEVO con el mismo encabezado y esas primeras 'cantidad' acciones, y devuelve la bitácora lista
        para seguir anexando. El log anterior no se toca (sigue siendo de solo anexado), aunque después
        de guardar se hayan jugado más acciones.

        encabezado_esperado: el de la partida guardada; si el log anterior tiene otro, es de otra
        partida y se rechaza. Lanza ErrorBitacora sin crear nada si algo no cuadra.
        Costo: O(acciones del log anterior) para leerlo, una sola vez al cargar.
        """
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 0:
            raise ErrorBitacora(f"la cantidad de acciones debe ser un entero >= 0 (llegó {cantidad!r})")
        anterior = BitacoraReplayIO.leer(ruta_anterior)
        if encabezado_esperado is not None and anterior.encabezado != encabezado_esperado:
            raise ErrorBitacora(f"el log {ruta_anterior!r} es de otra partida: su encabezado es "
                                f"{anterior.encabezado} y la partida guardada tiene {encabezado_esperado}")
        if cantidad > len(anterior.acciones):
            raise ErrorBitacora(f"el log {ruta_anterior!r} tiene {len(anterior.acciones)} acciones completas "
                                f"y la partida guardada necesita {cantidad}")
        primeras = [anterior.acciones[i] for i in range(cantidad)]
        nueva = BitacoraReplayIO(ruta_nueva)
        nueva._crear(anterior.encabezado, primeras)
        return nueva

    def _crear(self, encabezado: EncabezadoReplayDTO, acciones: list[AccionDTO]) -> None:
        """Escribe encabezado y acciones iniciales con una sola escritura, en un archivo que no existía."""
        if self._iniciada:
            raise ErrorBitacora(f"la bitácora {self._ruta!r} ya fue iniciada")
        _validar_encabezado(encabezado)
        partes = [f"{_LINEA_FORMATO}\n"
                  f"{_CLAVE_ID}={encabezado.id_cripta}\n"
                  f"{_CLAVE_VERSION_CRIPTA}={encabezado.version_cripta}\n"
                  f"{_CLAVE_VERSION_CATALOGO}={encabezado.version_catalogo}\n"
                  f"{_CLAVE_SEMILLA}={encabezado.semilla}\n"
                  f"{_LINEA_ACCIONES}\n"]
        for accion in acciones:            # vienen de leer(): ya se comprobó que se escriben igual
            partes.append(accion.a_linea() + "\n")
        texto = "".join(partes)
        carpeta = os.path.dirname(self._ruta)
        try:
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self._ruta, "x", encoding="utf-8", newline="") as archivo:   # "x": falla si ya existe
                archivo.write(texto)
        except FileExistsError:
            raise ErrorBitacora(f"ya existe un log en {self._ruta!r}; no se sobrescribe") from None
        except OSError as error:
            raise ErrorBitacora(f"no se pudo crear el log {self._ruta!r}: {error}") from None
        self._iniciada = True
        self._acciones_escritas = len(acciones)

    def anexar(self, accion: AccionDTO) -> None:
        """Agrega una línea al final del log. Si la acción no se puede escribir, no escribe nada."""
        if not self._iniciada:
            raise ErrorBitacora("primero hay que llamar a iniciar() con el encabezado")
        if not isinstance(accion, AccionDTO):
            raise ErrorBitacora(f"se esperaba un AccionDTO y llegó {type(accion).__name__}")
        linea = accion.a_linea()
        try:
            reversible = "\n" not in linea and "\r" not in linea and _leer_accion(linea) == accion
        except ValueError:          # por ejemplo, un '|' de más cambia la cantidad de campos
            reversible = False
        if not reversible:
            raise ErrorBitacora(f"la acción {accion!r} no se puede escribir sin cambiar al leerla "
                                f"(no se permiten '|', saltos de línea ni campos vacíos \"\")")
        if not os.path.isfile(self._ruta):     # el modo "a" lo crearía de nuevo, pero sin encabezado
            raise ErrorBitacora(f"el log {self._ruta!r} ya no existe")
        try:
            with open(self._ruta, "a", encoding="utf-8", newline="") as archivo:
                archivo.write(linea + "\n")
        except OSError as error:
            raise ErrorBitacora(f"no se pudo escribir en el log {self._ruta!r}: {error}") from None
        self._acciones_escritas += 1

    def acciones_escritas(self) -> int:
        """Acciones que tiene el log (incluye las copiadas por continuar_desde). Es lo que se guarda."""
        return self._acciones_escritas

    def ruta(self) -> str:
        return self._ruta

    # ------------------------------------------------------------ lectura
    @staticmethod
    def leer(ruta: str) -> PartidaReplayDTO:
        """Lee un log completo. Lanza ErrorBitacora si no existe o no tiene el formato correcto."""
        try:
            with open(ruta, encoding="utf-8", newline="") as archivo:
                texto = archivo.read()
        except FileNotFoundError:
            raise ErrorBitacora(f"no existe el log {ruta!r}") from None
        except UnicodeDecodeError:
            raise ErrorBitacora(f"{ruta!r} no es un log de partida (no es texto UTF-8)") from None
        except OSError as error:
            raise ErrorBitacora(f"no se pudo leer el log {ruta!r}: {error}") from None

        lineas = texto.split("\n")
        # Si el archivo termina en '\n', el último elemento es "". Si no, es una línea a medio escribir.
        incompleta = lineas.pop() != ""

        if not lineas or _sin_retorno(lineas[0]) != _LINEA_FORMATO:
            primera = _sin_retorno(lineas[0]) if lineas else ""
            if primera.startswith(_PREFIJO_FORMATO):
                raise ErrorBitacora(f"{ruta!r} usa la versión {primera[len(_PREFIJO_FORMATO):]!r} del formato "
                                    f"y este programa lee la versión {VERSION_FORMATO}")
            raise ErrorBitacora(f"{ruta!r} no es un log de partida (falta {_LINEA_FORMATO!r} en la línea 1)")

        id_cripta = version_cripta = version_catalogo = semilla_texto = None
        i = 1
        while i < len(lineas) and _sin_retorno(lineas[i]) != _LINEA_ACCIONES:
            linea = _sin_retorno(lineas[i])
            numero = i + 1
            pos = linea.find("=")
            if pos <= 0:
                raise ErrorBitacora(f"{ruta!r}, línea {numero}: se esperaba 'clave=valor' y dice {linea!r}")
            clave, valor = linea[:pos], linea[pos + 1:]
            if valor == "":
                raise ErrorBitacora(f"{ruta!r}, línea {numero}: {clave!r} está vacío")
            if clave == _CLAVE_ID and id_cripta is None:
                id_cripta = valor
            elif clave == _CLAVE_VERSION_CRIPTA and version_cripta is None:
                version_cripta = valor
            elif clave == _CLAVE_VERSION_CATALOGO and version_catalogo is None:
                version_catalogo = valor
            elif clave == _CLAVE_SEMILLA and semilla_texto is None:
                semilla_texto = valor
            elif clave in (_CLAVE_ID, _CLAVE_VERSION_CRIPTA, _CLAVE_VERSION_CATALOGO, _CLAVE_SEMILLA):
                raise ErrorBitacora(f"{ruta!r}, línea {numero}: {clave!r} aparece dos veces")
            else:
                raise ErrorBitacora(f"{ruta!r}, línea {numero}: clave desconocida {clave!r}")
            i += 1

        if i >= len(lineas):
            raise ErrorBitacora(f"{ruta!r}: el encabezado está incompleto (falta la línea {_LINEA_ACCIONES!r})")
        faltan = [clave for clave, valor in ((_CLAVE_ID, id_cripta), (_CLAVE_VERSION_CRIPTA, version_cripta),
                                             (_CLAVE_VERSION_CATALOGO, version_catalogo),
                                             (_CLAVE_SEMILLA, semilla_texto)) if valor is None]
        if faltan:
            raise ErrorBitacora(f"{ruta!r}: al encabezado le falta {', '.join(faltan)}")
        assert id_cripta is not None and version_cripta is not None
        assert version_catalogo is not None and semilla_texto is not None
        semilla = _entero(semilla_texto)
        if semilla is None:
            raise ErrorBitacora(f"{ruta!r}: la semilla debe ser un número entero y dice {semilla_texto!r}")
        encabezado = EncabezadoReplayDTO(id_cripta, version_cripta, version_catalogo, semilla)

        acciones: list[AccionDTO] = []
        for j in range(i + 1, len(lineas)):
            linea = _sin_retorno(lineas[j])
            try:
                accion = _leer_accion(linea)
            except ValueError:
                raise ErrorBitacora(f"{ruta!r}, línea {j + 1}: acción con formato inválido {linea!r}") from None
            acciones.append(accion)
        return PartidaReplayDTO(encabezado, acciones, ultima_linea_descartada=incompleta)


def comprobar_compatibilidad(encabezado: EncabezadoReplayDTO, version_cripta_disponible: str | None,
                             version_catalogo_disponible: str | None) -> list[str]:
    """
    Compara las versiones del log con las que hay disponibles AHORA en la fuente que se va a usar
    (FuenteRed o FuenteOffline). Devuelve la lista de problemas; vacía = se puede reproducir fielmente.

    Para no gastar solicitudes extra, Servicios puede pasar cripta.version (de los datos generales
    que ya pidió) y resolvedor.version_catalogo() (ya pedida por ResolvedorCatalogo.crear).
    Si el API cambió de versión pero el paquete de --offline tiene la del log, esa es la
    "copia local compatible" del §4.11: Servicios puede volver a comprobar contra FuenteOffline.
    """
    problemas: list[str] = []
    if not validar_version(encabezado.version_cripta, version_cripta_disponible):
        problemas.append(f"la cripta {encabezado.id_cripta!r} del log es la versión {encabezado.version_cripta!r} "
                         f"y la disponible es {version_cripta_disponible!r}")
    if not validar_version(encabezado.version_catalogo, version_catalogo_disponible):
        problemas.append(f"el catálogo del log es la versión {encabezado.version_catalogo!r} "
                         f"y el disponible es {version_catalogo_disponible!r}")
    return problemas


# ------------------------------------------------------------ auxiliares
def _leer_accion(linea: str) -> AccionDTO:
    """
    AccionDTO.desde_linea, pero solo acepta la línea si es EXACTAMENTE la que a_linea() escribiría.
    desde_linea por sí sola aceptaría variantes (" mover|0||" o "mover|+0||") que nunca escribe
    este programa: si aparecen, el log fue alterado y no se reproduce.
    """
    accion = AccionDTO.desde_linea(linea)
    if accion.a_linea() != linea:
        raise ValueError("la línea no es la forma que escribe a_linea()")
    return accion


def _sin_retorno(linea: str) -> str:
    """Quita el '\\r' final de una línea guardada con '\\r\\n' (por ejemplo, editada en Windows)."""
    return linea[:-1] if linea.endswith("\r") else linea


def _entero(texto: str) -> int | None:
    """Entero escrito solo con dígitos y un '-' opcional al inicio; None si no lo es."""
    digitos = texto[1:] if texto.startswith("-") else texto
    if digitos == "":
        return None
    for caracter in digitos:
        if not ("0" <= caracter <= "9"):
            return None
    return int(texto)


def _validar_encabezado(encabezado: EncabezadoReplayDTO) -> None:
    if not isinstance(encabezado, EncabezadoReplayDTO):
        raise ErrorBitacora(f"se esperaba un EncabezadoReplayDTO y llegó {type(encabezado).__name__}")
    for nombre, valor in ((_CLAVE_ID, encabezado.id_cripta), (_CLAVE_VERSION_CRIPTA, encabezado.version_cripta),
                          (_CLAVE_VERSION_CATALOGO, encabezado.version_catalogo)):
        if not isinstance(valor, str) or valor == "" or valor != valor.strip() or "\n" in valor or "\r" in valor:
            raise ErrorBitacora(f"{nombre} debe ser un texto no vacío, sin espacios en los extremos "
                                f"ni saltos de línea (llegó {valor!r})")
    if not isinstance(encabezado.semilla, int) or isinstance(encabezado.semilla, bool):
        raise ErrorBitacora(f"la semilla debe ser un número entero (llegó {encabezado.semilla!r})")
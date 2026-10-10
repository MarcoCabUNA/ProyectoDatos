from Logic.Enemigo import Enemigo


# COORDINAR (Integrante 2): SalidaDTO con sala_destino, cerrada (bool, nunca None), llave y cierre_automatico
class SalidaViva:
    def __init__(self, salida_dto):
        self.destino = salida_dto.sala_destino
        self.cerrada = salida_dto.cerrada
        self.llave = salida_dto.llave
        self.cierre_automatico = salida_dto.cierre_automatico


class TrampaViva:
    def __init__(self, instancia, ficha):
        self.instancia = instancia
        self.ficha = ficha
        self.armada = True

    def activar(self, motor, evento):
        motor.historial.registrar_atributo(self, "armada", self.armada)
        self.armada = True


class CierrePuerta:
    def __init__(self, caras):
        self.caras = caras

    def activar(self, motor, evento):
        for salida in self.caras:
            motor.historial.registrar_atributo(salida, "cerrada", salida.cerrada)
            salida.cerrada = True


# COORDINAR (Integrante 2): SalaDTO con id, nombre y salidas como array de 4 en orden N, S, E, O
class SalaViva:
    def __init__(self, sala_dto):
        self.id = sala_dto.id
        self.nombre = sala_dto.nombre
        self.salidas = [None, None, None, None]
        for i in range(4):
            if sala_dto.salidas[i] is not None:
                self.salidas[i] = SalidaViva(sala_dto.salidas[i])
        self.objetos = []
        self.trampas = []
        self.enemigos = []
        self.contenido_cargado = False


class Mazmorra:
    # COORDINAR (Integrante 2): sala_salida y llave_salida vienen de CriptaDTO
    def __init__(self, sala_salida, llave_salida):
        self.salas = []
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.salida_abierta = False
        self.contadores_tipo = []
        self.historial = None

    # ---------- Metodos publicos

    def cargar_esqueleto(self, salas_dto):
        for sala_dto in salas_dto:
            while len(self.salas) <= sala_dto.id:
                self.salas.append(None)
            self.salas[sala_dto.id] = SalaViva(sala_dto)

    # COORDINAR (Integrante 2): enemigos con .instancia, .tipo y .vida; trampas con .instancia y .tipo; objetos como ids
    # COORDINAR (Integrante 2): fn_ficha(tipo) la provee la caché del catálogo y nunca devuelve None
    def cargar_contenido(self, sala_dto, fn_ficha):
        sala = self.salas[sala_dto.id]
        if sala.contenido_cargado:
            return
        for enemigo_dto in sala_dto.enemigos:
            numero = self._siguiente_numero(enemigo_dto.tipo)
            ficha = fn_ficha(enemigo_dto.tipo)
            sala.enemigos.append(Enemigo(ficha, enemigo_dto.instancia, enemigo_dto.vida, numero, sala.id))
        for id_objeto in sala_dto.objetos:
            sala.objetos.append(id_objeto)
        for trampa_dto in sala_dto.trampas:
            sala.trampas.append(TrampaViva(trampa_dto.instancia, fn_ficha(trampa_dto.tipo)))
        sala.contenido_cargado = True

    def sala(self, id_sala):
        return self.salas[id_sala]

    def contenido_cargado(self, id_sala):
        return self._existe(id_sala) and self.salas[id_sala].contenido_cargado

    def salida(self, id_sala, direccion):
        return self.salas[id_sala].salidas[direccion]

    def salidas_abiertas(self, id_sala):
        destinos = []
        for salida in self.salas[id_sala].salidas:
            if salida is not None and not salida.cerrada and self._existe(salida.destino):
                destinos.append(salida.destino)
        return destinos

    def enemigos_vivos(self, id_sala):
        vivos = []
        for enemigo in self.salas[id_sala].enemigos:
            if enemigo.Vivo():
                vivos.append(enemigo)
        return vivos

    def enemigos_dormidos(self, id_sala):
        dormidos = []
        for enemigo in self.enemigos_vivos(id_sala):
            if not enemigo.activo:
                dormidos.append(enemigo)
        return dormidos

    def buscar_enemigo(self, id_sala, instancia):
        for enemigo in self.enemigos_vivos(id_sala):
            if enemigo.id == instancia:
                return enemigo
        return None

    def llave_requerida(self, id_sala, direccion):
        salida = self.salida(id_sala, direccion)
        if salida is None or not salida.cerrada:
            return None
        return salida.llave

    def abrir_puerta(self, id_sala, direccion, motor):
        salida = self.salida(id_sala, direccion)
        caras = [salida]
        inversa = self._salida_inversa(id_sala, salida.destino)
        if inversa is not None:
            caras.append(inversa)
        for cara in caras:
            self._registrar_atributo(cara, "cerrada", cara.cerrada)
            cara.cerrada = False
        if salida.llave == self.llave_salida:
            self._registrar_atributo(self, "salida_abierta", self.salida_abierta)
            self.salida_abierta = True
        if salida.cierre_automatico is not None:
            motor.programar_efecto(salida.cierre_automatico, "cierre_puerta", CierrePuerta(caras))

    def mover_enemigo(self, enemigo, destino):
        origen = enemigo.Sala_Actual
        indice = self.salas[origen].enemigos.index(enemigo)
        self._registrar_cambio(lambda: self._deshacer_movimiento(enemigo, origen, indice))
        self.salas[origen].enemigos.pop(indice)
        self.salas[destino].enemigos.append(enemigo)
        enemigo.Sala_Actual = destino

    # reversible=False para los pergaminos de retroceso: el retroceso no los devuelve ni los quita del suelo (§2.11)
    def soltar_objeto(self, id_sala, id_objeto, reversible=True):
        if reversible:
            self._registrar_cambio(lambda: self._quitar_ultimo(id_sala, id_objeto))
        self.salas[id_sala].objetos.append(id_objeto)

    # Lo llama el Motor al recoger, después de validar que el inventario no esté lleno
    def recoger_objeto(self, id_sala, id_objeto, reversible=True):
        objetos = self.salas[id_sala].objetos
        for i in range(len(objetos)):
            if objetos[i] == id_objeto:
                if reversible:
                    self._registrar_cambio(lambda: objetos.insert(min(i, len(objetos)), id_objeto))
                objetos.pop(i)
                return True
        return False

    def hay_objeto(self, id_sala, id_objeto):
        for objeto in self.salas[id_sala].objetos:
            if objeto == id_objeto:
                return True
        return False

    def trampas_armadas(self, id_sala):
        armadas = []
        for trampa in self.salas[id_sala].trampas:
            if trampa.armada:
                armadas.append(trampa)
        return armadas

    # ---------- Metodos privados

    def _registrar_atributo(self, objeto, nombre, valor_anterior):
        if self.historial is not None:
            self.historial.registrar_atributo(objeto, nombre, valor_anterior)

    def _registrar_cambio(self, deshacer):
        if self.historial is not None:
            self.historial.registrar_cambio(deshacer)

    def _deshacer_movimiento(self, enemigo, origen, indice):
        self.salas[enemigo.Sala_Actual].enemigos.remove(enemigo)
        self.salas[origen].enemigos.insert(indice, enemigo)
        enemigo.Sala_Actual = origen

    # Se quita la última aparición: un pergamino soltado después (sin registrar) pudo quedar detrás
    def _quitar_ultimo(self, id_sala, id_objeto):
        objetos = self.salas[id_sala].objetos
        for i in range(len(objetos) - 1, -1, -1):
            if objetos[i] == id_objeto:
                objetos.pop(i)
                return

    def _existe(self, id_sala):
        return id_sala < len(self.salas) and self.salas[id_sala] is not None

    def _salida_inversa(self, origen, destino):
        if not self._existe(destino):
            return None
        for salida in self.salas[destino].salidas:
            if salida is not None and salida.destino == origen:
                return salida
        return None

    def _siguiente_numero(self, tipo):
        for par in self.contadores_tipo:
            if par[0] == tipo:
                par[1] += 1
                return par[1]
        self.contadores_tipo.append([tipo, 1])
        return 1

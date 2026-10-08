from Logic.Enemigo import Enemigo


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
        self.armada = True


class CierrePuerta:
    def __init__(self, caras):
        self.caras = caras

    def activar(self, motor, evento):
        for salida in self.caras:
            salida.cerrada = True


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
    def __init__(self, sala_salida, llave_salida):
        self.salas = []
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.salida_abierta = False
        self.contadores_tipo = []

    # ---------- Metodos publicos

    def cargar_esqueleto(self, salas_dto):
        for sala_dto in salas_dto:
            while len(self.salas) <= sala_dto.id:
                self.salas.append(None)
            self.salas[sala_dto.id] = SalaViva(sala_dto)

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
            cara.cerrada = False
        if salida.llave == self.llave_salida:
            self.salida_abierta = True
        if salida.cierre_automatico is not None:
            motor.programar_efecto(salida.cierre_automatico, "cierre_puerta", CierrePuerta(caras))

    def mover_enemigo(self, enemigo, destino):
        self.salas[enemigo.Sala_Actual].enemigos.remove(enemigo)
        self.salas[destino].enemigos.append(enemigo)
        enemigo.Sala_Actual = destino

    def soltar_objeto(self, id_sala, id_objeto):
        self.salas[id_sala].objetos.append(id_objeto)

    def recoger_objeto(self, id_sala, id_objeto):
        objetos = self.salas[id_sala].objetos
        for i in range(len(objetos)):
            if objetos[i] == id_objeto:
                objetos.pop(i)
                return True
        return False

    def trampas_armadas(self, id_sala):
        armadas = []
        for trampa in self.salas[id_sala].trampas:
            if trampa.armada:
                armadas.append(trampa)
        return armadas

    # ---------- Metodos privados

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

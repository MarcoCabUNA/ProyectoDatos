"""
SincronizadorUsos (Servicios, Integrante 3): le dice a la caché del catálogo qué fichas están en uso (§4.4).

Una ficha en uso no se puede liberar de memoria. El enunciado define "en uso" como una ficha
referenciada por al menos una instancia activa:
    - un enemigo vivo (de cualquier sala cargada),
    - un objeto en el inventario,
    - un objeto en el suelo de la sala actual,
    - una trampa de la sala actual.

En lugar de marcar y liberar a mano en cada evento (un enemigo que muere, un objeto que se recoge,
una sala que se abandona, un retroceso...), después de cada acción se RECONSTRUYE la lista completa
a partir del estado del juego y se entrega a ResolvedorCatalogo.sincronizar_usos(). Un solo camino
para todos los casos, incluido el retroceso, que revive enemigos y devuelve objetos.

Costo: O(salas + instancias activas) por acción. Con el paquete de prueba mide ~0.015 ms.
"""


class SincronizadorUsos:

    def ids_en_uso(self, contexto) -> list:
        """Ids de ficha de todas las instancias activas (con repetidos: uno por instancia)."""
        mazmorra = contexto.mazmorra
        usados = []
        for id_sala in contexto.esqueleto.ids_salas():
            if mazmorra.contenido_cargado(id_sala):
                for enemigo in mazmorra.enemigos_vivos(id_sala):
                    usados.append(enemigo.ficha.id)
        sala_actual = mazmorra.sala(contexto.jugador.Sala_Actual)
        for id_objeto in sala_actual.objetos:
            usados.append(id_objeto)
        for trampa in sala_actual.trampas:
            usados.append(trampa.ficha.id)
        for objeto in contexto.inventario.objetos():
            usados.append(objeto.id)
        return usados

    def sincronizar(self, contexto) -> None:
        contexto.resolvedor.sincronizar_usos(self.ids_en_uso(contexto))
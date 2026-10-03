"""Una acción del jugador. Es exactamente lo que se escribe en el log (--replay).

   tipo: mover, atacar, esperar, abrir, recoger, soltar, usar, equipar, retroceder
   direccion: 0-3 (N, S, E, O) para mover o abrir; None en los demás casos
   objetivo: id de instancia del enemigo a atacar; None en los demás casos
   objeto: id del objeto a recoger, usar, equipar o soltar; None en los demás casos
   """

from dataclasses import dataclass

SEPARADOR = "|"


@dataclass(frozen=True)
class AccionDTO:
    tipo : str
    direccion : int | None = None
    objetivo : str | None = None
    objeto : str | None = None

    def a_linea(self):
        """Convierte la acción en una línea de texto: tipo|direccion|objetivo|objeto.

                Un campo None se escribe vacío. Ejemplos:
                    mover|0||
                    atacar||e-201|
                    recoger|||itm_daga_oxidada
                """

        direccion = "" if self.direccion is None else str(self.direccion)
        objetivo = "" if self.objetivo is None else self.objetivo
        objeto = "" if self.objeto is None else self.objeto
        return SEPARADOR.join([self.tipo, direccion, objetivo, objeto])

    @staticmethod
    def desde_linea(texto):
        partes = texto.strip().split(SEPARADOR)
        if len(partes) != 4:
            raise ValueError(f"Línea de acción con formato inválido: {texto!r}")

        tipo, direccion, objetivo, objeto = partes
        return AccionDTO(
            tipo = tipo,
            direccion = int(direccion) if direccion != "" else None,
            objetivo = objetivo if objetivo != "" else None,
            objeto = objeto if objeto != "" else None
        )
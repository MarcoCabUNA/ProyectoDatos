from DTO.PantallaDTO import PantallaDTO
from View import Componentes as c

ARRIBA_DEL_TEXTO = 26
ROJO_ADVERTENCIA = (70, 14, 16, 235)


def lineas_a_dibujar(fuente, lineas: list[str], ancho: int, capacidad: int) -> list[str]:
    ajustadas = []
    for linea in lineas:
        ajustadas.extend(c.ajustar_lineas(fuente, linea.replace("→", "->"), ancho))     # la fuente del juego no tiene la flecha
    if len(ajustadas) <= capacidad:
        return ajustadas
    cortadas = ajustadas[:capacidad - 1]
    cortadas.append(f"... y {len(ajustadas) - len(cortadas)} líneas más (python main.py --verificar CRIPTA las muestra todas)")
    return cortadas


def dibujar(superficie, fuentes: c.Fuentes, pantalla: PantallaDTO, marco, pista: str) -> list[str]:
    advertencia = pantalla.reporte_advertencia
    c.panel(superficie, marco, ROJO_ADVERTENCIA if advertencia else c.PANEL, c.ROJO_VIVO if advertencia else c.ORO, 2)
    titulo = "Advertencia: la cripta no es resoluble" if advertencia else "Verificación de resolubilidad"
    c.texto_en(superficie, fuentes.chico, titulo, c.AVISO if advertencia else c.ORO,
               (marco.x + c.HUD_RELLENO + 2, marco.y + 6), "topleft")
    fuente = fuentes.ayuda_juego
    ancho = marco.width - 2 * c.HUD_RELLENO
    capacidad = (marco.height - ARRIBA_DEL_TEXTO - c.HUD_RELLENO) // c.HUD_AYUDA_INTERLINEA
    lineas = lineas_a_dibujar(fuente, pantalla.reporte_resolubilidad, ancho, capacidad)
    for i, linea in enumerate(lineas):
        c.texto_en(superficie, fuente, c.recortar_a_ancho(fuente, linea, ancho), c.TEXTO,
                   (marco.x + c.HUD_RELLENO, marco.y + ARRIBA_DEL_TEXTO + i * c.HUD_AYUDA_INTERLINEA), "topleft")
    c.texto_en(superficie, fuentes.chico, pista, c.TEXTO_SUAVE, (marco.right - c.HUD_RELLENO - 2, marco.y + 6), "topright")
    return lineas

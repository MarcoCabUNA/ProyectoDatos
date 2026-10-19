"""
ErroresServicio (Servicios, Integrante 3): los fallos ESPERADOS que la Interfaz debe mostrar sin caerse.

La arquitectura dice que la Interfaz solo habla con Servicios: no importa clases de Datos ni de Lógica.
Pero varios de estos fallos nacen en Datos (la red, el guardado, la bitácora, los puntajes). Servicios es la
capa que sí conoce a Datos, así que reúne aquí los tipos y el Controlador importa únicamente este archivo.

    except ERRORES_ESPERADOS as error:      # 'except' acepta una tupla de tipos
        ...mostrar str(error) al jugador...

Qué NO está aquí: los errores de programación (un TypeError, un IndexError...). Esos deben seguir
rompiendo el programa con su traza, porque esconderlos escondería un error en el código.
"""
from Data.AlmacenPuntajes import ErrorPuntajes
from Data.BitacoraReplayIO import ErrorBitacora
from Data.ClienteHttp import ErrorRed
from Data.GuardadoBinario import ErrorGuardado
from Service.ServicioGuardado import ErrorCarga
from Service.ServicioReplay import ErrorReplay

ERRORES_ESPERADOS = (ErrorRed, ErrorGuardado, ErrorBitacora, ErrorPuntajes, ErrorCarga, ErrorReplay)
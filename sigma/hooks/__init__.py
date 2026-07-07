# Este espacio de desarrollo está pensado para que los desarrolladores 
# puedan crear sus propios hooks y personalizar el comportamiento de la aplicación.

# Exportamos las funciones principales del notificador para que el orquestador
# pueda importarlas directamente desde el paquete 'hooks'.
from .zulip_notifier import notify_hitl, notify_pipeline_end, parse_hitl_response
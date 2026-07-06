# =============================================================================
# LANGFUSE CONFIGURACIÓN - SIGMA HITO 1
# =============================================================================
# Este script usa el decorador @observe para enviar una traza a Langfuse.
# Es la forma más estable en la versión 4.13.0 de la librería.
# =============================================================================
#-----------------------------------------------------------------------------------------
#test_langfuse.py (Versión 2) en modo de prueba no funciona correctamente debido a cambios en 
#la API de Langfuse.
#------------------------------------------------------------------------------------------

### test_langfuse.py (7ma Prueba)
## Este script prueba la integración con Langfuse usando la API v4.12.0. Habiendo insatlado
# 'pip install langchain' y 'pip install langfuse-langchain'

""" 
# test_langfuse.py
from langfuse.decorators import observe
from langfuse import Langfuse
from config import CONFIG
import time

# Inicializar el cliente (necesario aunque no lo uses directamente)
langfuse = Langfuse(
    public_key=CONFIG.langfuse.public_key,
    secret_key=CONFIG.langfuse.secret_key,
    host=CONFIG.langfuse.host,
)

@observe()
def test_function():
    # Esta función se registrará como una traza en Langfuse.
    print("🔍 Ejecutando función de prueba...")
    # Simular trabajo
    time.sleep(0.5)
    # Puedes añadir sub-spans con @observe anidados
    return {"status": "ok", "message": "Hola desde SIGMA"}

# Ejecutar la función
result = test_function()

# Forzar el envío de datos a Langfuse
langfuse.flush()

print("✅ Traza enviada a Langfuse usando @observe. Revisa http://localhost:3001")
print("Resultado:", result)
"""



import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (si no lo haces, usa valores directos)
load_dotenv()

# Importar Langfuse y el decorador
from langfuse import Langfuse
from langfuse.decorators import observe

# Inicializar el cliente Langfuse (obligatorio para que @observe funcione)
# Las claves pueden venir de variables de entorno o escribirse directamente
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-fd7d177d-af4e-4543-9416-b7f40f2e1f4b"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-c795c23b-7f85-406f-948a-dc6aa6501771"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3001")
)

# -----------------------------------------------------------------------------
# Función decorada con @observe (se convierte automáticamente en una traza)
# -----------------------------------------------------------------------------
@observe()
def mi_funcion_de_prueba():
    # Esta función será registrada como una traza completa en Langfuse.
    print("🔍 Ejecutando función de prueba...")
    time.sleep(0.5)  # Simular trabajo
    # Puedes añadir más lógica aquí, incluso llamadas a otras funciones con @observe
    return {"status": "ok", "mensaje": "Hola desde SIGMA con @observe"}

# -----------------------------------------------------------------------------
# Ejecutar la función y forzar el envío de la traza
# -----------------------------------------------------------------------------
resultado = mi_funcion_de_prueba()

# Asegurar que todos los datos se envían a Langfuse
langfuse.flush()

print("✅ Traza enviada correctamente a Langfuse usando @observe.")
print("🔗 Revisa en: http://localhost:3001")
print("📦 Resultado devuelto:", resultado)
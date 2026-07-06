"""
Script: scripts/download_model.py
Proyecto: SIGMA Hito 1
Proposito: Descargar y verificar el modelo de sentimiento para skill 0008.
Modelo: cardiffnlp/twitter-roberta-base-sentiment-latest
"""
from transformers import pipeline
import json

MODEL_ID = "cardiffnlp/twitter-roberta-base-sentiment-latest"

print(f"Descargando modelo SIGMA 0008: {MODEL_ID}")
print("Esto puede tardar 2-3 minutos (~500MB)...")

clf = pipeline(
    "text-classification",
    model=MODEL_ID,
    device=-1
)

# Pruebas de verificacion
casos = [
    "Argentina campeon del mundo!",
    "Terrible arbitraje, robo descarado",
    "El partido estuvo bien jugado"
]

print("\nVerificacion del modelo:")
for texto in casos:
    resultado = clf(texto)[0]
    print(f"  '{texto[:40]}' -> {resultado['label']} ({resultado['score']:.3f})")

print("\nModelo listo para SIGMA skill 0008-sentiment-analyzer.")
print(f"Cache en: ~/.cache/huggingface/hub/")
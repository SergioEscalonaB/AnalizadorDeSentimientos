import pandas as pd
import numpy as np
import re
import nltk
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

# Descargar stopwords de NLTK (solo la primera vez) y las importa
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

# Función para limpiar el texto: elimina caracteres no alfabéticos
# (conserva letras con tilde y ñ), pasa a minúsculas y colapsa espacios.
def limpiar_texto(texto: str) -> str:
    texto = re.sub(r'[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ\s]', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# URL base para descargar los archivos JSONL del dataset desde Hugging Face
BASE_URL = "https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es/resolve/main"

print("=" * 60)
print("ENTRENAMIENTO DE MODELO DE ANÁLISIS DE SENTIMIENTOS")
print("Dataset: SetFit/amazon_reviews_multi_es")
print("=" * 60)

# 1. Carga de datos
# Se cargan train.jsonl y test.jsonl directamente desde Hugging Face con pd.read_json.
print("\n[1/8] Cargando datos...")

df_train = pd.read_json(f"{BASE_URL}/train.jsonl", lines=True)
df_test  = pd.read_json(f"{BASE_URL}/test.jsonl", lines=True)

print(f"  Train: {len(df_train):,} registros")
print(f"  Test:  {len(df_test):,} registros")

# 2. Mapeo de sentimiento
# El dataset tiene label 0,1,2,3,4 que corresponden a 1,2,3,4,5 estrellas.
# Se decidió mapearlo de la siguiente forma por la naturaleza binaria del análisis de sentimientos:
#   - 1 y 2 estrellas (label 0,1) → Negativo (0)
#   - 4 y 5 estrellas (label 3,4) → Positivo (1)
#   - 3 estrellas  (label 2)      → Se descartan (ya que son ambiguas, mezclan opiniones positivas y negativas, lo que genera ruido en el modelo)
print("\n[2/8] Mapeando sentimiento (label 0,1 -> Negativo; 3,4 -> Positivo; descartando 3 estrellas)...")

df_train['sentimiento'] = df_train['label'].apply(lambda x: 0 if x <= 1 else (1 if x >= 3 else None))
df_test['sentimiento']  = df_test['label'].apply(lambda x: 0 if x <= 1 else (1 if x >= 3 else None))

# Guarda el tamaño original para mostrar cuántas se descartaron
n_train_before = len(df_train)
n_test_before  = len(df_test)

# Elimina las filas con None (las de 3 estrellas) y reinicia índices para evitar problemas, dejando solo reseñas con sentimiento 0 o 1.
df_train = df_train.dropna(subset=['sentimiento']).reset_index(drop=True)
df_test  = df_test.dropna(subset=['sentimiento']).reset_index(drop=True)

# Convierte la columna a entero (pandas la convierte a float por el None)
df_train['sentimiento'] = df_train['sentimiento'].astype(int)
df_test['sentimiento']  = df_test['sentimiento'].astype(int)

print(f"  Train: {n_train_before:,} -> {len(df_train):,} (descartadas {n_train_before - len(df_train):,})")
print(f"  Test:  {n_test_before:,} -> {len(df_test):,} (descartadas {n_test_before - len(df_test):,})")

print(f"  Train distribución: {df_train['sentimiento'].value_counts().to_dict()}")
print(f"  Test  distribución: {df_test['sentimiento'].value_counts().to_dict()}")

# 3. Limpieza de texto
# Aplica la función limpiar_texto a cada reseña para normalizar el texto antes de vectorizarlo.
print("\n[3/8] Limpiando texto...")

df_train['texto_limpio'] = df_train['text'].apply(limpiar_texto)
df_test['texto_limpio']  = df_test['text'].apply(limpiar_texto)

# 4. Verificación de balanceo
# El dataset ya está balanceado entre clases después de eliminar las reseñas de 3 estrellas.
print("\n[4/8] Verificando balanceo...")
print(f"  Dataset ya balanceado: {df_train['sentimiento'].value_counts().to_dict()}")

# 5. División train/validation
# Se separa el 80% para entrenar y 20% para validar, manteniendo la misma proporción de clases en ambos conjuntos.
print("\n[5/8] Dividiendo en train/validation (80/20)...")

X = df_train['texto_limpio']
y = df_train['sentimiento']

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"  Train: {len(X_train):,} | Val: {len(X_val):,}")

# 6. Vectorización TF-IDF 
# Convierte el texto a una matriz numérica usando TF-IDF.
#   - stopwords: elimina palabras comunes en español ("el", "la", "de", etc.)
#   - ngram_range=(1,2): usa palabras individuales y pares de palabras para capturar frases como "no funciona", "muy bueno"
#   - max_features=5000: limita el vocabulario a las 5000 palabras más relevantes para evitar sobreajuste y reducir dimensionalidad.
print("\n[6/8] Vectorizando con TF-IDF...")

stopwords_es = stopwords.words('spanish')
print(f"  Stopwords cargadas: {len(stopwords_es)} palabras")

vectorizer = TfidfVectorizer(
    stop_words=stopwords_es,
    ngram_range=(1, 2),
    max_features=5000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_val_vec   = vectorizer.transform(X_val)

print(f"  Vocabulario: {len(vectorizer.get_feature_names_out()):,} tokens")

# 7. Entrenamiento del modelo

print("\n[7/8] Entrenando LogisticRegression...")

modelo = LogisticRegression(max_iter=1000, random_state=42)
modelo.fit(X_train_vec, y_train)

# 8. Evaluación del modelo
# Se evalúa en dos conjuntos:
#   - Validation: 20% del train balanceado (mide desempeño en datos vistos indirectamente durante el entrenamiento)
#   - Test: dataset independiente test.jsonl (mide desempeño realista en datos nunca antes vistos por el modelo)
print("\n[8/8] Evaluando modelo...\n")

# Evaluación en validation set
y_pred_val = modelo.predict(X_val_vec)
y_prob_val = modelo.predict_proba(X_val_vec)

print("=" * 60)
print("RESULTADOS EN VALIDATION (20% de train.jsonl)")
print("=" * 60)
print(f"\nAccuracy:  {accuracy_score(y_val, y_pred_val):.4f}")
print(f"\nMatriz de confusión:")
print(confusion_matrix(y_val, y_pred_val))
print(f"\nClassification Report:")
print(classification_report(y_val, y_pred_val, target_names=['Negativo', 'Positivo']))

# Evaluación en test set independiente
X_test_vec = vectorizer.transform(df_test['texto_limpio'])
y_pred_test = modelo.predict(X_test_vec)
y_prob_test = modelo.predict_proba(X_test_vec)

print("=" * 60)
print("RESULTADOS EN TEST (test.jsonl, 4K registros independientes)")
print("=" * 60)
print(f"\nAccuracy:  {accuracy_score(df_test['sentimiento'], y_pred_test):.4f}")
print(f"\nMatriz de confusión:")
print(confusion_matrix(df_test['sentimiento'], y_pred_test))
print(f"\nClassification Report:")
print(classification_report(df_test['sentimiento'], y_pred_test, target_names=['Negativo', 'Positivo']))

# 9. Análisis de 3 ejemplos
print("\n" + "=" * 60)
print("ANÁLISIS DE 3 EJEMPLOS DEL TEST")
print("=" * 60)

# Crea un dataframe auxiliar con predicciones y probabilidades
df_eval = df_test.copy()
df_eval['prediccion'] = y_pred_test
df_eval['prob_pos']   = y_prob_test[:, 1]
df_eval['prob_neg']   = y_prob_test[:, 0]
df_eval['correcto']   = df_eval['sentimiento'] == df_eval['prediccion']

# Ejemplo 1: Bien clasificado
# Busca la reseña que el modelo clasificó correctamente con mayor confianza (es decir, mayor acierto)
bien = df_eval[df_eval['correcto']].copy()
bien['confianza'] = bien[['prob_pos', 'prob_neg']].max(axis=1)
bien = bien.sort_values('confianza', ascending=False)
ej_bien = bien.iloc[0]

print(f"\nEJEMPLO 1: Bien clasificado (confianza: {ej_bien['confianza']:.4f})")
print(f"Texto:           {ej_bien['text'][:150]}")
print(f"Real/Pred:       {'Positivo' if ej_bien['sentimiento'] == 1 else 'Negativo'} / {'Positivo' if ej_bien['prediccion'] == 1 else 'Negativo'}")
print(f"Prob Pos/Neg:    {ej_bien['prob_pos']:.4f} / {ej_bien['prob_neg']:.4f}")

# Ejemplo 2: Mal clasificado
# Busca la reseña mal clasificada con mayor confianza en su error (es decir, mayor error) para entender qué patrones confunden al modelo
mal = df_eval[~df_eval['correcto']].copy()
mal['confianza'] = mal[['prob_pos', 'prob_neg']].max(axis=1)
mal = mal.sort_values('confianza', ascending=False)
ej_mal = mal.iloc[0]

print(f"\nEJEMPLO 2: Mal clasificado (confianza erronea: {ej_mal['confianza']:.4f})")
print(f"Texto:           {ej_mal['text'][:200]}")
print(f"Real/Pred:       {'Positivo' if ej_mal['sentimiento'] == 1 else 'Negativo'} / {'Positivo' if ej_mal['prediccion'] == 1 else 'Negativo'}")
print(f"Prob Pos/Neg:    {ej_mal['prob_pos']:.4f} / {ej_mal['prob_neg']:.4f}")

# Ejemplo 3: Dudoso
# Busca la reseña con probabilidad más cercana a 0.5 (máxima incertidumbre del modelo)
df_eval['duda'] = abs(df_eval['prob_pos'] - 0.5)
ej_dudoso = df_eval.sort_values('duda').iloc[0]

print(f"\nEJEMPLO 3: Dudoso (probabilidad ~0.5)")
print(f"Texto:           {ej_dudoso['text'][:200]}")
print(f"Real/Pred:       {'Positivo' if ej_dudoso['sentimiento'] == 1 else 'Negativo'} / {'Positivo' if ej_dudoso['prediccion'] == 1 else 'Negativo'}")
print(f"Prob Pos/Neg:    {ej_dudoso['prob_pos']:.4f} / {ej_dudoso['prob_neg']:.4f}")

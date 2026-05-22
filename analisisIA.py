import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix

# Cargar dataset de reseñas en español (reseñas de restaurantes scrapeadas de Google)
df = pd.read_csv(
    "https://raw.githubusercontent.com/fjramirezv/sentiment-webscraping/main/dataset_sentiment_analisys.csv",
    sep=';',
    encoding='utf-8-sig'
)

# Preparamos los datos en el dataframe
# Eliminamos filas vacías y nos quedamos solo con las columnas necesarias
df = df[['review', 'sentimiento']].dropna()

# Convertimos la etiqueta de texto a numérica: positivo = 1, negativo = 0
df['label'] = df['sentimiento'].str.strip().str.lower().map({'positivo': 1, 'negativo': 0})

# Eliminamos filas donde la etiqueta no sea válida (por si hay valores inesperados)
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)
df = df[['review', 'label']]

# Balancea el dataset (con el fin de reducir el número de registros y que no se desbalancen los resultados)
df_positivo = df[df['label'] == 1]  # Crea un dataset donde solo están los registros con label positivo.
df_negativo = df[df['label'] == 0]  # Crea un dataset donde solo están los registros con label negativo.

# Crea un dataset donde toma solamente una parte de los registros con etiqueta negativa
# (Toma exactamente la misma cantidad de registros que los positivos)
min_size = min(len(df_positivo), len(df_negativo))
df_positivo_ejemplo = df_positivo.sample(min_size, random_state=42)
df_negativo_ejemplo = df_negativo.sample(min_size, random_state=42)

# Crea un dataset donde une el dataset de positivos con el de negativos simplificado.
df_balanceado = pd.concat([df_positivo_ejemplo, df_negativo_ejemplo])

# Añade frases extra en español para que el modelo entienda palabras clave que no están en el df original.
frases_extra = [
    # Positivas
    "La aplicación es muy intuitiva",
    "La app es intuitiva y fácil de usar",
    "Interfaz muy intuitiva y sencilla",
    "Diseño extremadamente intuitivo",
    "Esta aplicación es muy fácil de usar",
    "Presentación fantástica del producto",
    "Una presentación increíble",
    "Excelente presentación, muy profesional",
    "Gran experiencia, muy satisfecho con el servicio",
    "Muy buena atención, volvería sin duda",
    # Negativas
    "No disfruté el servicio al cliente para nada",
    "El servicio al cliente fue muy malo",
    "El servicio es terrible y pésimo",
    "Una experiencia bastante mediocre",
    "La experiencia fue completamente decepcionante",
    "La comida estaba horrible y fría",
    "La comida fue muy mala, sin sabor",
    "Experiencia terrible en general, no recomiendo",
    "Para nada intuitivo, muy confuso de usar",
    "La app es confusa y difícil de entender",
]

# Asigna etiqueta
sentimientos_extra = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Crea df de las frases extra
df_extra = pd.DataFrame({
    'review': frases_extra,
    'label': sentimientos_extra
})

# Unifica el dataset original con el de las frases extra
df_balanceado = pd.concat([df_balanceado, df_extra])

# Mezcla los datos para evitar sesgos y fallas en el momento de train test split
df_balanceado = df_balanceado.sample(frac=1, random_state=42)

# Muestra como se distribuyeron los datos según etiqueta
print("\nDistribución final:")
print(df_balanceado['label'].value_counts())

# Define el train test split
texts = df_balanceado['review']
labels = df_balanceado['label']

x_train, x_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

# Realizamos la vectorización
  # stopwords -> elimina palabras comunes en español ("el", "la", "y", etc.)
  # ngram -> usa unigramas y bigramas, para entender frases como "no recomiendo", "muy malo" como negativo
  #          y no como "recomiendo", "malo" por separado.
  # min_df -> solo usa palabras que aparezcan por lo menos dos veces, para evitar palabras raras.
# Stopwords en español (sklearn solo acepta 'english' como string; para español pasamos como lista)
stopwords_es = [
    "de","la","que","el","en","y","a","los","del","se","las","por","un","para","con","una","su",
    "al","lo","como","más","pero","sus","le","ya","o","este","sí","porque","esta","entre","cuando",
    "muy","sin","sobre","también","me","hasta","hay","donde","quien","desde","todo","nos","durante",
    "todos","uno","les","ni","contra","otros","ese","eso","ante","ellos","e","esto","mí","antes",
    "algunos","qué","unos","yo","otro","otras","otra","él","tanto","esa","estos","mucho","quienes",
    "nada","muchos","cual","poco","ella","estar","estas","algunas","algo","nosotros","mi","mis",
    "tú","te","ti","tu","tus","ellas","nosotras","vosotros","vosotras","os","mío","mía","míos",
    "mías","tuyo","tuya","tuyos","tuyas","suyo","suya","suyos","suyas","nuestro","nuestra",
    "nuestros","nuestras","vuestro","vuestra","vuestros","vuestras","ese","esos","esas",
    "aquel","aquellas","aquellos","aquella","aquello","estoy","estás","está","estamos","estáis",
    "están","esté","estés","estemos","estéis","estén","fue","ser","era","eres","somos","sois",
    "son","soy","han","ha","he","hemos","habéis","has","haya","sean","sea","no","si","le","les"
]

vectorizer = TfidfVectorizer(stop_words=stopwords_es, ngram_range=(1, 2), min_df=1)

X_train = vectorizer.fit_transform(x_train)
X_test = vectorizer.transform(x_test)

# Crea y entrena al modelo
modelo = MultinomialNB()
modelo.fit(X_train, y_train)

# Evalua el modelo
y_pred = modelo.predict(X_test)

print("\n=== Evaluación ===\n")

print(f"Precisión: {accuracy_score(y_test, y_pred)}\n")

print("Matriz de confusión:")
print(confusion_matrix(y_test, y_pred))
print()

# Evalua el modelo con frases de prueba dadas en español
frases_prueba = [
    "¡Esta app es muy intuitiva!",
    "No disfruté el servicio al cliente.",
    "Una experiencia bastante promedio.",
    "¡Presentación fantástica!",
    "La comida estaba horrible."
]

X_prueba = vectorizer.transform(frases_prueba)
predicciones = modelo.predict(X_prueba)

print("=== Resultados ===\n")

for frase, pred in zip(frases_prueba, predicciones):
    sentimiento = "Positivo" if pred == 1 else "Negativo"

    print(f"Frase: {frase}")
    print(f"Sentimiento: {sentimiento}")
    print("-" * 50)



import joblib

# Guardar modelo y vectorizador
joblib.dump(modelo, 'modelo_sentimiento.pkl')
joblib.dump(vectorizer, 'vectorizador.pkl')

print("Modelo y vectorizador guardados correctamente.")
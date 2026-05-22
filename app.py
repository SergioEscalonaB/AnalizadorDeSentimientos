from flask import Flask, request, jsonify
import joblib

# Inicializar la aplicación Flask
app = Flask(__name__)

# Cargar el modelo y el vectorizador
try:
    modelo = joblib.load('modelo_sentimiento.pkl')
    vectorizer = joblib.load('vectorizador.pkl')
    print("Modelo y vectorizador cargados correctamente.")
except Exception as e:
    print(f"Error al cargar el modelo o vectorizador: {e}")
    modelo = None
    vectorizer = None


# Definir la ruta para el análisis de sentimiento
@app.route('/analizar', methods=['POST'])
def analizar_sentimiento():
    if modelo is None or vectorizer is None:
        return jsonify({"error": "Modelo o vectorizador no disponible."}), 500

    # Obtener los datos que vamos a recibir de make en formato JSON
    data = request.get_json()
    reseña = data.get('reseña', '')

    if not reseña:
        return jsonify({"error": "No se proporcionó una reseña para analizar."}), 400

    # LLamamos al modelo para predecir el sentimiento de la reseña recibida
    try:
        # Transformar la reseña usando el vectorizador
        reseña_vectorizada = vectorizer.transform([reseña])
        
        # Predecir el sentimiento
        prediccion = modelo.predict(reseña_vectorizada)[0]
        # Convertir el numero a texto para que sea más entendible en la respuesta JSON
        sentimiento = "Positivo" if prediccion == 1 else "Negativo"

        # Respuesta en formato JSON con el resultado del análisis de sentimiento
        respuesta = {
            "sentimiento": sentimiento,
            "prediccion_original": int(prediccion) # Por si acaso
        }
        return jsonify(respuesta)
    
    except Exception as e:
        print(f"Error al analizar el sentimiento: {e}")
        return jsonify({"error": f"Error al analizar el sentimiento: {e}"}), 500

# Finalmente, ejecutamos la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
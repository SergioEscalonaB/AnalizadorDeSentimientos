# Analizador de Sentimientos — API Flask

API REST que analiza el sentimiento (positivo o negativo) de reseñas en español, usando un modelo de Machine Learning entrenado con scikit-learn y servido con Flask + Gunicorn.

---

## Contenido

- [Estructura del Proyecto](README.md)
- [Despliegue en VPS](DESPLIEGUE.md)
- [Uso de la API](USO_API.md)

---

## Estructura del proyecto

```
AnalizadorDeSentimientos/
├── app.py                    # API Flask principal
├── analisisIA.py             # Script de entrenamiento del modelo
├── modelo_sentimiento.pkl    # Modelo ML serializado
└── vectorizador.pkl          # Vectorizador TF-IDF serializado
└── index.html                # Pagina para las reseñas

```


## Tecnologías utilizadas

| Tecnología | Rol |
|---|---|
| Flask | Framework web de la API |
| Gunicorn | Servidor WSGI de producción |
| scikit-learn | Modelo de Machine Learning |
| joblib | Serialización del modelo |
| systemd | Gestión del proceso en el servidor |
| Oracle Cloud | Infraestructura VPS |
```

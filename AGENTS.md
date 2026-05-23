# AGENTS.md

## Project
Academic project (AI class, 8th semester Systems Engineering).  
Sentiment analysis system for product reviews — binary classifier + Flask API + Make (n8n) automation.

## Branches
- `main` — teammate's work
- `jesu` — current development branch (model training, Flask API)

Work exclusively on `jesu` unless told otherwise.

## Key files
| File | Purpose |
|---|---|
| `app.py` | Flask API. Endpoint `POST /analizar` receives `{"reseña": "..."}`, returns `{"sentimiento": "Positivo"/"Negativo", "prediccion_original": 1/0}`. |
| `analisisIA.py` | OLD training script (Naive Bayes, tiny dataset). Dead code. |
| `modelo_sentimiento.pkl` / `vectorizador.pkl` | OLD model/vocab artifacts. Must be replaced by new training. |

## Planned: `train_amazon.py`
Will replace `analisisIA.py`. Pipeline:
1. Load `SetFit/amazon_reviews_multi_es` from Hugging Face via `pd.read_json` (NOT the `datasets` library)
2. Map stars 1-3 → 0 (neg), 4-5 → 1 (pos)
3. Clean text: `limpiar_texto()` — strip non-alphabetic (keep accented/ñ), lowercase, collapse spaces
4. Balance via random undersampling to match minority class size
5. Split 80/20 stratified, `random_state=42`
6. TF-IDF: `stopwords.words('spanish')` (NLTK), `ngram_range=(1,2)`, `max_features=5000`
7. `LogisticRegression(max_iter=1000, random_state=42)`
8. Save `modelo_sentimiento.pkl` / `vectorizador.pkl`
9. Report accuracy, confusion matrix, classification report, 3 analyzed examples

## API contract (must not change)
```
POST /analizar
Request:  {"reseña": "texto"}
Response: {"sentimiento": "Positivo"|"Negativo", "prediccion_original": 1|0}
```

## Dependencies
`requirements.txt`: flask, joblib, pandas, numpy, scikit-learn.  
Add nltk (`nltk.download('stopwords')`) for Spanish stopwords.  
Trains on CPU, no GPU needed.

## Commands
```bash
# Train new model
python train_amazon.py

# Run API
python app.py   # listens on 0.0.0.0:5000
```

## Current status
- Old model: ~83% accuracy, Naive Bayes, 28 training samples
- Target: >85% accuracy with LogisticRegression on ~200K Amazon reviews

# Uso de la API

## Endpoint

```
POST http://IP_DE_TU_VPS:5000/analizar
```

## Headers

```
Content-Type: application/json
```

## Body — Parámetros de entrada

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reseña` | `string` | Sí | Texto de la reseña a analizar |

**Ejemplo de request:**

```json
{
  "reseña": "El servicio fue excelente, muy recomendado"
}
```

---

## Respuesta exitosa — `200 OK`

| Campo | Tipo | Descripción |
|---|---|---|
| `sentimiento` | `string` | Resultado del análisis: `"Positivo"` o `"Negativo"` |
| `prediccion_original` | `integer` | Valor numérico del modelo: `1` (positivo) o `0` (negativo) |

**Ejemplo de respuesta:**

```json
{
  "sentimiento": "Positivo",
  "prediccion_original": 1
}
```

---

## Respuestas de error

| Código | Causa | Respuesta |
|---|---|---|
| `400` | No se envió el campo `reseña` | `{"error": "No se proporcionó una reseña para analizar."}` |
| `500` | El modelo no pudo cargarse | `{"error": "Modelo o vectorizador no disponible."}` |
| `500` | Error interno al predecir | `{"error": "Error al analizar el sentimiento: <detalle>"}` |

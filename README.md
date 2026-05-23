# Analizador de Sentimientos — API Flask

API REST que analiza el sentimiento (positivo o negativo) de reseñas en español, usando un modelo de Machine Learning entrenado con scikit-learn y servido con Flask + Gunicorn.

---

## Estructura del proyecto

```
AnalizadorDeSentimientos/
├── app.py                    # API Flask principal
├── analisisIA.py             # Script de entrenamiento del modelo
├── modelo_sentimiento.pkl    # Modelo ML serializado
└── vectorizador.pkl          # Vectorizador TF-IDF serializado
```

---

## Despliegue en VPS (Oracle Cloud / Ubuntu)

### Requisitos previos
- VPS con Ubuntu 20.04 o superior
- Acceso SSH al servidor
- Puerto 5000 disponible

---

### Paso 1 — Conectarse al VPS

```bash
ssh ubuntu@IP_DE_TU_VPS
```

---

### Paso 2 — Instalar dependencias del sistema

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
```

---

### Paso 3 — Clonar el repositorio

```bash
cd /home/ubuntu
git clone https://github.com/SergioEscalonaB/AnalizadorDeSentimientos.git
cd AnalizadorDeSentimientos
```

---

### Paso 4 — Crear entorno virtual e instalar librerías

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask joblib scikit-learn gunicorn
```

---

### Paso 5 — Verificar que el servidor arranca correctamente

```bash
python app.py
```

Si ves el mensaje `Modelo y vectorizador cargados correctamente.` y el servidor inicia, todo está bien. Detén con `Ctrl+C`.

---

### Paso 6 — Crear el servicio systemd

Esto permite que la API corra en segundo plano y se reinicie automáticamente si falla.

```bash
sudo nano /etc/systemd/system/analizador.service
```

Pega el siguiente contenido:

```ini
[Unit]
Description=Analizador de Sentimiento Flask
After=network.target

[Service]
User=ubuntu (reemplazar por el usuario, normalmente es root)
WorkingDirectory=/home/ubuntu/AnalizadorDeSentimientos
Environment="PATH=/home/ubuntu/AnalizadorDeSentimientos/venv/bin"
ExecStart=/home/ubuntu/AnalizadorDeSentimientos/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Guarda con `Ctrl+O` → `Enter` → `Ctrl+X`.

---

### Paso 7 — Activar e iniciar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable analizador
sudo systemctl start analizador
sudo systemctl status analizador
```

Deberías ver `Active: active (running)` en verde. 
YA CON ESTO DEBERIA FUNCIONAR EL API

Para revisar los logs en tiempo real:

```bash
sudo journalctl -u analizador -f
```

---


#### 8. Firewall interno del VPS (iptables)

```bash
sudo apt install iptables-persistent -y
sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
sudo netfilter-persistent save
```

> Haz esto si no funciona, porque aveces el puerto esta bloqueado en la vps aunque esté abierto en la consola de Oracle.

---

## Uso de la API

### Endpoint

```
POST http://IP_DE_TU_VPS:5000/analizar
```

### Headers

```
Content-Type: application/json
```

### Body — Parámetros de entrada

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

### Respuesta exitosa — `200 OK`

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

### Respuestas de error

| Código | Causa | Respuesta |
|---|---|---|
| `400` | No se envió el campo `reseña` | `{"error": "No se proporcionó una reseña para analizar."}` |
| `500` | El modelo no pudo cargarse | `{"error": "Modelo o vectorizador no disponible."}` |
| `500` | Error interno al predecir | `{"error": "Error al analizar el sentimiento: <detalle>"}` |


## Actualizar la API desde el repositorio
 
Cada vez que haya cambios en el repositorio, conéctate al VPS y corre:
 
```bash
cd /home/ubuntu/AnalizadorDeSentimientos
git pull
sudo systemctl restart analizador


## Tecnologías utilizadas

| Tecnología | Rol |
|---|---|
| Flask | Framework web de la API |
| Gunicorn | Servidor WSGI de producción |
| scikit-learn | Modelo de Machine Learning |
| joblib | Serialización del modelo |
| systemd | Gestión del proceso en el servidor |
| Oracle Cloud | Infraestructura VPS |

# Configurar HTTPS en VPS con Cloudflare Tunnel

Guía para exponer una API HTTP local con HTTPS usando Cloudflare Tunnel, sin necesidad de configurar certificados SSL manualmente.

---

## Requisitos previos

- VPS con Ubuntu (ARM64 o AMD64)
- Un dominio activo en Cloudflare (plan gratuito funciona)
- Tu API corriendo localmente en un puerto (ej: `localhost:5000`)

---

## Paso 1: Instalar cloudflared

**Para VPS ARM64: La que usamos**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```

**Para VPS AMD64:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

Verificar instalación:
```bash
cloudflared --version
```

---

## Paso 2: Autenticarse en Cloudflare

```bash
cloudflared tunnel login
```

Abre el enlace que aparece en el navegador, inicia sesión en tu cuenta de Cloudflare y selecciona el dominio que quieres usar.

---

## Paso 3: Crear el tunnel

```bash
cloudflared tunnel create mi-api
```

Guarda el **UUID** que aparece en la salida. Ejemplo:
```
Created tunnel mi-api with id 87423868-09f3-4dbf-9c8d-01590b71d2b7
```

Las credenciales se guardan automáticamente en:
```
~/.cloudflared/<UUID>.json
```

---

## Paso 4: Crear el archivo de configuración

```bash
nano ~/.cloudflared/config.yml
```

Contenido del archivo (reemplaza con tu UUID y dominio):
```yaml
tunnel: 87423868-09f3-4dbf-9c8d-01590b71d2b7
credentials-file: /etc/cloudflared/87423868-09f3-4dbf-9c8d-01590b71d2b7.json

ingress:
  - hostname: api.tu-dominio.com
    service: http://localhost:5000
  - service: http_status:404
```

> El subdominio `api.tu-dominio.com` es independiente de cualquier otro subdominio que ya tengas configurado (ej: Next.js en el dominio raíz).

---

## Paso 5: Crear el registro DNS

```bash
cloudflared tunnel route dns mi-api api.tu-dominio.com
```

Esto crea automáticamente un registro CNAME en Cloudflare apuntando al tunnel.

---

## Paso 6: Instalar como servicio del sistema

Copia los archivos de configuración a la ruta del sistema:
```bash
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
sudo cp ~/.cloudflared/<UUID>.json /etc/cloudflared/
```

Edita el config para actualizar la ruta del JSON:
```bash
sudo nano /etc/cloudflared/config.yml
```

Cambia la línea `credentials-file` a:
```yaml
credentials-file: /etc/cloudflared/<UUID>.json
```

Instala y habilita el servicio:
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Verifica que esté corriendo:
```bash
sudo systemctl status cloudflared
```

---

## Paso 7: Verificar que funciona

```bash
curl https://api.tu-dominio.com/analizar \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"reseña": "me encantó el producto"}'
```

Si la API responde correctamente, ya está disponible con HTTPS.

---

## Resultado

| Antes | Después |
|---|---|
| `http://IP:5000/analizar` | `https://api.tu-dominio.com/analizar` |
| Sin SSL | HTTPS automático |
| No compatible con Make.com | Compatible con Make.com y cualquier cliente |

---

## Notas

- El tunnel arranca automáticamente con el sistema gracias a `systemd`.
- Cloudflare gestiona el certificado SSL sin costo adicional.
- No interfiere con otros subdominios ni servicios en el mismo dominio.
- Si cambias el puerto de la API, edita `/etc/cloudflared/config.yml` y reinicia: `sudo systemctl restart cloudflared`.
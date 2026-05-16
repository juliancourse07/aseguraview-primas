# 🚀 Guía de Despliegue - AseguraView

Esta guía describe cómo desplegar AseguraView en diferentes entornos de producción.

## 📑 Tabla de Contenidos

- [Opciones de Despliegue](#opciones-de-despliegue)
- [Streamlit Cloud (Recomendado)](#streamlit-cloud-recomendado)
- [Heroku](#heroku)
- [AWS EC2](#aws-ec2)
- [Docker](#docker)
- [Configuración de Producción](#configuración-de-producción)
- [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
- [Backup y Recuperación](#backup-y-recuperación)

---

## Opciones de Despliegue

### Comparación de Plataformas

| Plataforma | Costo | Dificultad | Escalabilidad | Mantenimiento | Recomendado Para |
|------------|-------|------------|---------------|---------------|------------------|
| **Streamlit Cloud** | Gratis | ⭐ Fácil | Media | Bajo | MVP, proyectos académicos |
| **Heroku** | $7-$25/mes | ⭐⭐ Media | Media | Medio | Equipos pequeños |
| **AWS EC2** | $10-$100/mes | ⭐⭐⭐ Difícil | Alta | Alto | Empresas, alta demanda |
| **Docker + VPS** | $5-$20/mes | ⭐⭐⭐ Difícil | Media | Alto | Flexibilidad máxima |

---

## Streamlit Cloud (Recomendado)

### Ventajas

- ✅ **Gratis** para proyectos públicos
- ✅ Deploy automático desde GitHub
- ✅ SSL/HTTPS incluido
- ✅ Fácil gestión de secrets
- ✅ Actualizaciones automáticas en cada push

### Desventajas

- ❌ Recursos limitados (1 CPU, 800 MB RAM)
- ❌ Tiempo de inicio lento (cold start)
- ❌ Solo para apps Streamlit

### Paso a Paso

#### 1. Preparar Repositorio

**Verificar archivos requeridos**:
```
aseguraview-primas/
├── app.py
├── config.py
├── requirements.txt
├── packages.txt (opcional)
├── .streamlit/
│   └── config.toml (opcional)
└── README.md
```

**Crear `packages.txt`** (si necesitas paquetes del sistema):
```
poppler-utils
```

**Crear `.streamlit/config.toml`** (configuración UI):
```toml
[theme]
primaryColor = "#38bdf8"
backgroundColor = "#071428"
secondaryBackgroundColor = "#1e293b"
textColor = "#f8fafc"

[server]
headless = true
port = 8501
enableCORS = false
```

**Commitear cambios**:
```bash
git add .
git commit -m "Preparar para deploy en Streamlit Cloud"
git push origin main
```

#### 2. Crear Cuenta en Streamlit Cloud

1. Ir a [streamlit.io/cloud](https://streamlit.io/cloud)
2. Hacer clic en **"Sign up"**
3. Autenticar con GitHub
4. Autorizar acceso a repositorios

#### 3. Deploy de la App

1. Hacer clic en **"New app"**
2. Seleccionar:
   - **Repository**: `juliancourse07/aseguraview-primas`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. Hacer clic en **"Deploy"**

#### 4. Configurar Secrets

1. En la app desplegada, ir a **"Settings"** (⚙️)
2. Ir a **"Secrets"**
3. Agregar secrets en formato TOML:

```toml
# Google Sheets Configuration
GOOGLE_SHEET_ID = "1ThVwW3IbkL7Dw_Vrs9heT1QMiHDZw1Aj-n0XNbDi9i8"
SHEET_NAME_DATOS = "Hoja1"
SHEET_NAME_FECHA = "Hoja2"

# Google Service Account Credentials (JSON)
[google_credentials]
type = "service_account"
project_id = "aseguraview-xxxxx"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nXXXXX...XXXXX\n-----END PRIVATE KEY-----\n"
client_email = "aseguraview-sa@aseguraview-xxxxx.iam.gserviceaccount.com"
client_id = "xxxxxxxxxxxxxxxxxxxxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

# Ley de Garantías Configuration
FIANZAS_LEY_GARANTIAS_INICIO = "2026-01-31"
FIANZAS_LEY_GARANTIAS_FIN_1V = "2026-05-24"
FIANZAS_LEY_GARANTIAS_FIN_2V = "2026-06-21"
FIANZAS_USAR_SEGUNDA_VUELTA = "True"

# Adjustment Factors
FIANZAS_FACTOR_PRE = "0.75"
FIANZAS_FACTOR_DURANTE = "0.25"
FIANZAS_FACTOR_POST = "0.60"
FIANZAS_FACTOR_REBOTE = "1.10"
```

4. Hacer clic en **"Save"**
5. App se reinicia automáticamente

#### 5. Acceder a Credenciales en Código

Actualizar `utils/data_loader.py` para leer secrets:

```python
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def get_google_credentials():
    """Lee credenciales desde secrets de Streamlit Cloud"""
    if 'google_credentials' in st.secrets:
        # Streamlit Cloud
        creds_dict = dict(st.secrets['google_credentials'])
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    else:
        # Local con archivo JSON
        credentials = Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    return credentials

def load_data():
    credentials = get_google_credentials()
    client = gspread.authorize(credentials)
    # ... resto del código
```

#### 6. Verificar Deploy

1. Esperar mensaje: **"Your app is live!"** (2-5 minutos)
2. URL será: `https://juliancourse07-aseguraview-primas-app-xxxxx.streamlit.app`
3. Abrir URL y verificar funcionamiento

#### 7. Configurar Dominio Personalizado (Opcional)

**Solo disponible en plan pagado ($200/mes)**

Si tienes plan pagado:
1. Ir a **Settings > General**
2. Agregar custom domain: `aseguraview.tudominio.com`
3. Configurar DNS:
   ```
   CNAME  aseguraview  juliancourse07-aseguraview-primas-app-xxxxx.streamlit.app
   ```

### Actualización de la App

**Deploy automático**: Cada `git push` a `main` redeploya automáticamente.

**Forzar redeploy manual**:
1. Ir a Settings > General
2. Hacer clic en **"Reboot app"**

---

## Heroku

### Ventajas

- ✅ Fácil escalabilidad horizontal
- ✅ Add-ons para BD, logs, monitoring
- ✅ CLI poderoso
- ✅ Git-based deployment

### Desventajas

- ❌ Costo mensual ($7+ por dyno)
- ❌ Cold start en dyno gratis (deprecated)

### Paso a Paso

#### 1. Crear Cuenta Heroku

1. Ir a [heroku.com](https://www.heroku.com/)
2. Sign up
3. Verificar email

#### 2. Instalar Heroku CLI

**macOS**:
```bash
brew tap heroku/brew && brew install heroku
```

**Windows**:
Descargar installer desde [devcenter.heroku.com](https://devcenter.heroku.com/articles/heroku-cli)

**Linux**:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

**Verificar instalación**:
```bash
heroku --version
```

#### 3. Preparar Archivos

**Crear `Procfile`**:
```
web: sh setup.sh && streamlit run app.py
```

**Crear `setup.sh`**:
```bash
mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

**Hacer ejecutable**:
```bash
chmod +x setup.sh
```

**Actualizar `requirements.txt`** (agregar gunicorn si usas):
```
streamlit>=1.30.0
...
```

#### 4. Deploy

```bash
# Login a Heroku
heroku login

# Crear app
heroku create aseguraview-primas

# Configurar secrets
heroku config:set GOOGLE_SHEET_ID="1ThVwW3IbkL7Dw_Vrs9heT1QMiHDZw1Aj-n0XNbDi9i8"
heroku config:set SHEET_NAME_DATOS="Hoja1"
heroku config:set SHEET_NAME_FECHA="Hoja2"

# Configurar credenciales Google (todo en una línea)
heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'

# Deploy
git push heroku main

# Abrir app
heroku open
```

#### 5. Escalar

```bash
# Ver dynos actuales
heroku ps

# Escalar a dyno básico ($7/mes)
heroku ps:scale web=1:basic

# Escalar a 2 dynos
heroku ps:scale web=2
```

---

## AWS EC2

### Ventajas

- ✅ Control total del servidor
- ✅ Alta escalabilidad
- ✅ Integración con otros servicios AWS
- ✅ Opciones de red avanzadas

### Desventajas

- ❌ Configuración compleja
- ❌ Requiere conocimiento de Linux
- ❌ Mantenimiento manual

### Paso a Paso

#### 1. Crear Instancia EC2

1. Ir a [AWS Console](https://console.aws.amazon.com/)
2. Navegar a **EC2 > Launch Instance**
3. Configurar:
   - **Name**: AseguraView-Production
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: t2.small (1 vCPU, 2 GB RAM)
   - **Key pair**: Crear o seleccionar existente
   - **Network**: Default VPC
   - **Security group**: Crear nuevo
     - Nombre: aseguraview-sg
     - Reglas:
       - SSH (22) desde tu IP
       - HTTP (80) desde anywhere
       - HTTPS (443) desde anywhere
       - Custom TCP (8501) desde anywhere
4. Hacer clic en **"Launch instance"**

#### 2. Conectar a Instancia

```bash
# Cambiar permisos de key
chmod 400 tu-key.pem

# Conectar via SSH
ssh -i tu-key.pem ubuntu@<EC2-PUBLIC-IP>
```

#### 3. Instalar Dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y pip
sudo apt install python3.10 python3.10-venv python3-pip git -y

# Instalar Nginx (reverse proxy)
sudo apt install nginx -y

# Instalar Certbot (SSL gratis)
sudo apt install certbot python3-certbot-nginx -y
```

#### 4. Clonar y Configurar App

```bash
# Crear usuario para app
sudo useradd -m -s /bin/bash aseguraview
sudo su - aseguraview

# Clonar repo
git clone https://github.com/juliancourse07/aseguraview-primas.git
cd aseguraview-primas

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
nano .env
# ... agregar variables ...
```

#### 5. Configurar como Servicio (systemd)

```bash
# Salir de usuario aseguraview
exit

# Crear archivo de servicio
sudo nano /etc/systemd/system/aseguraview.service
```

**Contenido**:
```ini
[Unit]
Description=AseguraView Streamlit App
After=network.target

[Service]
Type=simple
User=aseguraview
WorkingDirectory=/home/aseguraview/aseguraview-primas
Environment="PATH=/home/aseguraview/aseguraview-primas/venv/bin"
ExecStart=/home/aseguraview/aseguraview-primas/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Habilitar y iniciar**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aseguraview
sudo systemctl start aseguraview

# Verificar status
sudo systemctl status aseguraview
```

#### 6. Configurar Nginx como Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/aseguraview
```

**Contenido**:
```nginx
server {
    listen 80;
    server_name aseguraview.tudominio.com;  # O usar IP pública

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

**Activar configuración**:
```bash
sudo ln -s /etc/nginx/sites-available/aseguraview /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar sintaxis
sudo systemctl restart nginx
```

#### 7. Configurar SSL con Let's Encrypt

```bash
sudo certbot --nginx -d aseguraview.tudominio.com
```

Seguir wizard:
1. Ingresar email
2. Aceptar términos
3. Seleccionar opción de redirect HTTP → HTTPS

**Renovación automática** (ya configurado por Certbot):
```bash
# Test renovación
sudo certbot renew --dry-run
```

#### 8. Verificar Deploy

1. Abrir `https://aseguraview.tudominio.com`
2. Verificar funcionamiento
3. Verificar SSL (candado en navegador)

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando de inicio
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  aseguraview:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Build y Deploy

```bash
# Build imagen
docker-compose build

# Iniciar contenedor
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

---

## Configuración de Producción

### Variables de Entorno de Producción

```bash
# Producción
ENVIRONMENT=production
DEBUG=False

# Performance
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200

# Cache
STREAMLIT_CACHE_TTL=3600

# Logging
LOG_LEVEL=WARNING
```

### Optimizaciones

#### 1. Caching Agresivo

```python
@st.cache_data(ttl=3600, show_spinner=False)
def load_all_data():
    # Cache por 1 hora
    pass
```

#### 2. Lazy Loading

```python
# Solo cargar datos cuando tab está activo
if selected_tab == "Primas":
    df_primas = load_primas_data()
```

#### 3. Comprimir Responses

```python
# En config.toml
[server]
enableCompression = true
```

---

## Monitoreo y Mantenimiento

### Logs

**Streamlit Cloud**:
- Ver logs en dashboard de Streamlit Cloud
- Logs limitados a últimas 24 horas

**Heroku**:
```bash
heroku logs --tail
```

**AWS EC2**:
```bash
# Logs de systemd
sudo journalctl -u aseguraview -f

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoreo de Uptime

**Servicios recomendados**:
- [UptimeRobot](https://uptimerobot.com/) (gratis)
- [Pingdom](https://www.pingdom.com/)
- [StatusCake](https://www.statuscake.com/)

**Configurar check**:
- URL: `https://tu-app.streamlit.app/_stcore/health`
- Intervalo: 5 minutos
- Alertas: Email/SMS cuando down

### Monitoreo de Performance

**Streamlit built-in**:
```python
import streamlit as st

# En app.py
if st.secrets.get("ENVIRONMENT") == "production":
    st.set_page_config(page_title="AseguraView", layout="wide")
    
    # Track usage
    with open("/tmp/analytics.log", "a") as f:
        f.write(f"{datetime.now()}, {st.session_state}\n")
```

**Google Analytics** (opcional):
```html
<!-- En app.py -->
import streamlit.components.v1 as components

components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
""", height=0)
```

---

## Backup y Recuperación

### Backup de Datos

**Google Sheets** (fuente de datos principal):
- Backup automático de Google (versioning)
- Export manual a CSV periódicamente:
  ```bash
  # Script de backup
  python scripts/backup_sheets.py
  ```

### Backup de Código

**Git** (control de versiones):
```bash
# Tags para releases
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Plan de Recuperación

**Escenario 1: App caída**
1. Verificar logs
2. Reiniciar servicio
3. Si persiste, rollback a versión anterior

**Escenario 2: Pérdida de datos**
1. Restaurar desde backup de Google Sheets
2. Verificar integridad
3. Recargar en app

**Escenario 3: Infraestructura comprometida**
1. Crear nueva instancia
2. Deploy desde código en Git
3. Restaurar configuraciones y secrets
4. Actualizar DNS

---

## Checklist Pre-Deploy

- [ ] Código commiteado y pusheado
- [ ] `requirements.txt` actualizado
- [ ] Variables de entorno configuradas
- [ ] Credenciales de Google configuradas
- [ ] Tests locales pasados
- [ ] Performance optimizada (caching, lazy loading)
- [ ] Logs configurados
- [ ] Monitoreo configurado
- [ ] Plan de backup definido
- [ ] Documentación actualizada

---

## Conclusión

AseguraView puede desplegarse en múltiples plataformas según necesidades:

- **Para MVP/académico**: Streamlit Cloud (gratis, fácil)
- **Para equipos pequeños**: Heroku (pagado, medio)
- **Para producción empresarial**: AWS EC2 (complejo, escalable)
- **Para máxima flexibilidad**: Docker + VPS

Cada opción tiene trade-offs de costo, complejidad y escalabilidad. Elegir según:
- Presupuesto
- Expertise técnico
- Usuarios esperados
- Requerimientos de SLA

Para más información:
- [INSTALACION.md](INSTALACION.md) - Setup local
- [README.md](../README.md) - Uso de la aplicación
- [ARQUITECTURA.md](../ARQUITECTURA.md) - Detalles técnicos

# ⚙️ Guía de Instalación Detallada - AseguraView

Esta guía proporciona instrucciones paso a paso para instalar y configurar AseguraView en diferentes entornos.

## 📑 Tabla de Contenidos

- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación Local](#instalación-local)
- [Configuración de Google Sheets](#configuración-de-google-sheets)
- [Variables de Entorno](#variables-de-entorno)
- [Verificación de Instalación](#verificación-de-instalación)
- [Solución de Problemas](#solución-de-problemas)
- [Instalación en Diferentes Sistemas Operativos](#instalación-en-diferentes-sistemas-operativos)

---

## Requisitos del Sistema

### Hardware Mínimo

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 1 GB libre
- **Conexión**: Internet (para acceso a Google Sheets)

### Hardware Recomendado

- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disco**: 5 GB libre
- **Conexión**: Internet banda ancha

### Software Requerido

| Software | Versión Mínima | Versión Recomendada | Propósito |
|----------|----------------|---------------------|-----------|
| Python | 3.9 | 3.10 o 3.11 | Lenguaje principal |
| pip | 21.0 | Última | Gestor de paquetes |
| Git | 2.0 | Última | Control de versiones |
| poppler-utils | - | Última | Procesamiento PDF (opcional) |

---

## Instalación Local

### Paso 1: Verificar Python

Abrir terminal/CMD y verificar versión de Python:

```bash
python --version
# o
python3 --version
```

**Resultado esperado**: `Python 3.9.x` o superior

**Si no está instalado**:
- **Windows**: Descargar desde [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python@3.10`
- **Linux**: `sudo apt install python3.10`

### Paso 2: Verificar pip

```bash
pip --version
# o
pip3 --version
```

**Resultado esperado**: `pip 21.x.x` o superior

**Si no está instalado**:
```bash
python -m ensurepip --upgrade
```

### Paso 3: Clonar el Repositorio

```bash
# Navegar a carpeta deseada
cd ~/Proyectos  # o C:\Users\TuUsuario\Proyectos en Windows

# Clonar repositorio
git clone https://github.com/juliancourse07/aseguraview-primas.git

# Entrar al directorio
cd aseguraview-primas
```

**Verificar archivos**:
```bash
ls -la  # En Windows: dir
```

**Deberías ver**:
```
.
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── componentes/
├── modelos/
├── utils/
└── README.md
```

### Paso 4: Crear Entorno Virtual

**¿Por qué?**: Aislar dependencias del proyecto del Python global.

#### En Windows:

```cmd
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Verificar activación (prompt debe mostrar (venv))
```

#### En macOS/Linux:

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Verificar activación (prompt debe mostrar (venv))
```

**Indicador de éxito**: Prompt cambia a:
```
(venv) usuario@computadora:~/aseguraview-primas$
```

### Paso 5: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt
```

**Tiempo estimado**: 2-5 minutos

**Paquetes que se instalan**:
```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
statsmodels>=0.14.0
scipy>=1.10.0
openpyxl>=3.1.0
scikit-learn>=1.3.0
python-dotenv>=1.0.0
xgboost>=2.0.0
```

**Verificar instalación**:
```bash
pip list
```

**Debe mostrar todos los paquetes arriba**.

### Paso 6: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# En Windows:
copy .env.example .env
```

**Editar `.env`**:

Abrir con editor de texto (VS Code, Notepad++, nano, vim):

```bash
# Windows
notepad .env

# macOS
open -a TextEdit .env

# Linux
nano .env
```

**Contenido inicial** (`.env.example`):
```bash
# Google Sheets Configuration
GOOGLE_SHEET_ID=1ThVwW3IbkL7Dw_Vrs9heT1QMiHDZw1Aj-n0XNbDi9i8
SHEET_NAME_DATOS=Hoja1
SHEET_NAME_FECHA=Hoja2

# Ley de Garantías Configuration
FIANZAS_LEY_GARANTIAS_INICIO=2026-01-31
FIANZAS_LEY_GARANTIAS_FIN_1V=2026-05-24
FIANZAS_LEY_GARANTIAS_FIN_2V=2026-06-21
FIANZAS_USAR_SEGUNDA_VUELTA=True

# Adjustment Factors
FIANZAS_FACTOR_PRE=0.75
FIANZAS_FACTOR_DURANTE=0.25
FIANZAS_FACTOR_POST=0.60
FIANZAS_FACTOR_REBOTE=1.10
```

**Actualizar**:
1. `GOOGLE_SHEET_ID`: ID de tu Google Sheet (ver paso siguiente)
2. `SHEET_NAME_DATOS`: Nombre de la hoja con datos de producción
3. `SHEET_NAME_FECHA`: Nombre de la hoja con fecha de corte

**Guardar y cerrar**.

---

## Configuración de Google Sheets

### Paso 1: Crear Google Sheet

1. Ir a [Google Sheets](https://sheets.google.com)
2. Crear nuevo spreadsheet
3. Nombrar: "AseguraView - Datos de Producción"

### Paso 2: Estructurar Hojas

#### Hoja 1: Datos de Producción

**Nombre de hoja**: `Hoja1` (o el que configuraste en `.env`)

**Columnas** (fila 1):
```
| FECHA | LINEA_PLUS | IMP_PRIMA | PRESUPUESTO | RAMO |
```

**Datos de ejemplo** (filas 2+):
```
| 01/01/2024 | SOAT    | 1500000 | 18000000 | SOAT                |
| 01/01/2024 | FIANZAS | 2300000 | 10000000 | FIANZAS CUMPLIMIENTO |
| 01/01/2024 | VIDA    | 1200000 |  7000000 | VIDA GRUPO          |
| 02/01/2024 | AUTOS   |  890000 |  6000000 | AUTOS PARTICULARES  |
```

**Notas**:
- Formato de fecha: `DD/MM/YYYY`
- Números sin separadores de miles
- Líneas permitidas: `SOAT`, `FIANZAS`, `VIDA`, `AUTOS`, `HOGAR`, `PYMES`, `SALUD`, `ACCIDENTES`, `RESPONSABILIDAD CIVIL`, `TRANSPORTE`

#### Hoja 2: Fecha de Corte

**Nombre de hoja**: `Hoja2` (o el que configuraste en `.env`)

**Columnas** (fila 1):
```
| FECHA_CORTE |
```

**Datos** (fila 2):
```
| 15/05/2024 |
```

**Actualizar diariamente** con el último día con datos disponibles.

### Paso 3: Obtener ID del Sheet

**En la URL del Google Sheet**:
```
https://docs.google.com/spreadsheets/d/1ThVwW3IbkL7Dw_Vrs9heT1QMiHDZw1Aj-n0XNbDi9i8/edit
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                    Este es el SHEET_ID
```

**Copiar el ID** y actualizar en `.env`:
```bash
GOOGLE_SHEET_ID=TU_SHEET_ID_AQUI
```

### Paso 4: Configurar Acceso con Service Account

#### 4.1 Crear Proyecto en Google Cloud

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto:
   - Nombre: "AseguraView"
   - Hacer clic en "Crear"
3. Seleccionar el proyecto recién creado

#### 4.2 Habilitar Google Sheets API

1. En el menú lateral, ir a **APIs & Services > Library**
2. Buscar "Google Sheets API"
3. Hacer clic en "Google Sheets API"
4. Hacer clic en **"Enable"** (Habilitar)

#### 4.3 Crear Service Account

1. En el menú lateral, ir a **APIs & Services > Credentials**
2. Hacer clic en **"Create Credentials"**
3. Seleccionar **"Service Account"**
4. Configurar:
   - **Service account name**: aseguraview-sa
   - **Service account ID**: aseguraview-sa (auto-generado)
   - **Description**: Service Account para AseguraView
5. Hacer clic en **"Create and Continue"**
6. **Role**: Omitir (no necesario para Sheets)
7. Hacer clic en **"Continue"**
8. Hacer clic en **"Done"**

#### 4.4 Descargar Credenciales JSON

1. En la lista de Service Accounts, hacer clic en el recién creado
2. Ir a tab **"Keys"**
3. Hacer clic en **"Add Key" > "Create new key"**
4. Seleccionar **"JSON"**
5. Hacer clic en **"Create"**
6. Archivo JSON se descargará automáticamente

**Guardar archivo JSON**:
```bash
# Mover a carpeta del proyecto
mv ~/Downloads/aseguraview-sa-xxxxxxx.json /ruta/a/aseguraview-primas/credentials.json
```

**⚠️ IMPORTANTE**: NO commitear este archivo a Git.

**Verificar que `.gitignore` incluye**:
```
credentials.json
*.json
```

#### 4.5 Compartir Sheet con Service Account

1. Abrir el archivo JSON descargado
2. Copiar el valor de `"client_email"`:
   ```json
   {
     "type": "service_account",
     "project_id": "aseguraview-xxxxx",
     "client_email": "aseguraview-sa@aseguraview-xxxxx.iam.gserviceaccount.com",
     ...
   }
   ```
3. Ir a tu Google Sheet
4. Hacer clic en **"Share"** (Compartir)
5. Pegar el email del service account
6. Rol: **"Viewer"** (solo lectura es suficiente)
7. Desmarcar "Notify people" (no enviar notificación)
8. Hacer clic en **"Share"**

### Paso 5: Configurar Ruta a Credenciales

**Opción A: Variable de entorno** (Recomendado)

Agregar a `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

**Opción B: Configurar en código**

Editar `utils/data_loader.py` si es necesario (ya debe estar configurado).

---

## Variables de Entorno

### Variables Requeridas

| Variable | Descripción | Ejemplo | Default |
|----------|-------------|---------|---------|
| `GOOGLE_SHEET_ID` | ID del Google Sheet | `1ThVwW3I...` | (ninguno) |
| `SHEET_NAME_DATOS` | Nombre hoja datos | `Hoja1` | `Hoja1` |
| `SHEET_NAME_FECHA` | Nombre hoja fecha corte | `Hoja2` | `Hoja2` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta a JSON credentials | `./credentials.json` | (ninguno) |

### Variables Opcionales (Ley de Garantías)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `FIANZAS_LEY_GARANTIAS_INICIO` | Inicio Ley Garantías | `2026-01-31` |
| `FIANZAS_LEY_GARANTIAS_FIN_1V` | Fin 1ra vuelta | `2026-05-24` |
| `FIANZAS_LEY_GARANTIAS_FIN_2V` | Fin 2da vuelta | `2026-06-21` |
| `FIANZAS_USAR_SEGUNDA_VUELTA` | Usar 2da vuelta | `True` |
| `FIANZAS_FACTOR_PRE` | Factor pre-electoral | `0.75` |
| `FIANZAS_FACTOR_DURANTE` | Factor durante ley | `0.25` |
| `FIANZAS_FACTOR_POST` | Factor post-electoral | `0.60` |
| `FIANZAS_FACTOR_REBOTE` | Factor recuperación | `1.10` |

---

## Verificación de Instalación

### Test 1: Importaciones de Python

```bash
python -c "import streamlit; import pandas; import numpy; import plotly; print('✅ Todas las dependencias instaladas correctamente')"
```

**Resultado esperado**: `✅ Todas las dependencias instaladas correctamente`

### Test 2: Conexión a Google Sheets

Crear archivo `test_connection.py`:

```python
from utils.data_loader import load_data, load_cutoff_date

try:
    df = load_data()
    print(f"✅ Datos cargados: {len(df)} registros")
    
    cutoff = load_cutoff_date()
    print(f"✅ Fecha de corte: {cutoff}")
    
    print("\n✅ Conexión exitosa a Google Sheets")
except Exception as e:
    print(f"❌ Error: {e}")
```

Ejecutar:
```bash
python test_connection.py
```

**Resultado esperado**:
```
✅ Datos cargados: 50247 registros
✅ Fecha de corte: 2024-05-15 00:00:00
✅ Conexión exitosa a Google Sheets
```

### Test 3: Ejecutar Aplicación

```bash
streamlit run app.py
```

**Resultado esperado**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

**Abrir navegador en**: `http://localhost:8501`

**Verificar**:
- ✅ Dashboard carga sin errores
- ✅ Sidebar muestra filtros
- ✅ Datos se visualizan en tablas
- ✅ Gráficos se renderizan

**Si todo funciona**: ¡Instalación exitosa! 🎉

---

## Solución de Problemas

### Problema 1: `python` no reconocido

**Error**:
```
'python' is not recognized as an internal or external command
```

**Solución**:
1. Agregar Python al PATH
2. O usar `python3` en lugar de `python`
3. O reinstalar Python marcando "Add to PATH"

### Problema 2: Error al instalar `xgboost`

**Error**:
```
ERROR: Failed building wheel for xgboost
```

**Solución Windows**:
```bash
# Instalar Visual C++ Build Tools
# Descargar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**Solución macOS**:
```bash
brew install libomp
pip install xgboost
```

**Solución Linux**:
```bash
sudo apt install build-essential
pip install xgboost
```

### Problema 3: Error de autenticación Google

**Error**:
```
google.auth.exceptions.DefaultCredentialsError
```

**Soluciones**:
1. Verificar que `credentials.json` existe
2. Verificar que `GOOGLE_APPLICATION_CREDENTIALS` apunta al archivo correcto
3. Verificar que Service Account email tiene acceso al Sheet
4. Verificar permisos del archivo:
   ```bash
   chmod 600 credentials.json
   ```

### Problema 4: Error al cargar datos

**Error**:
```
gspread.exceptions.APIError: PERMISSION_DENIED
```

**Solución**:
1. Verificar que el Sheet fue compartido con el Service Account email
2. Verificar que el `GOOGLE_SHEET_ID` es correcto
3. Verificar que Google Sheets API está habilitada

### Problema 5: Streamlit no se inicia

**Error**:
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solución**:
1. Verificar que el entorno virtual está activado:
   ```bash
   which python  # Debe apuntar a venv/bin/python
   ```
2. Reinstalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### Problema 6: Puerto 8501 ocupado

**Error**:
```
OSError: [Errno 48] Address already in use
```

**Solución**:
```bash
# Opción 1: Usar otro puerto
streamlit run app.py --server.port 8502

# Opción 2: Matar proceso en 8501
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8501 | xargs kill -9
```

---

## Instalación en Diferentes Sistemas Operativos

### Windows 10/11

**Requisitos adicionales**:
- Visual C++ Redistributable 2015-2022
- Git for Windows

**Pasos específicos**:
1. Instalar Python desde [python.org](https://www.python.org/downloads/windows/)
   - ✅ Marcar "Add Python to PATH"
2. Instalar Git desde [git-scm.com](https://git-scm.com/download/win)
3. Usar PowerShell o Git Bash para comandos
4. Seguir pasos generales arriba

### macOS (10.15+)

**Requisitos adicionales**:
- Homebrew (gestor de paquetes)
- Xcode Command Line Tools

**Pasos específicos**:
```bash
# Instalar Homebrew (si no está instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python
brew install python@3.10

# Instalar Git
brew install git

# Continuar con pasos generales
```

### Linux (Ubuntu/Debian)

**Pasos específicos**:
```bash
# Actualizar repositorios
sudo apt update

# Instalar Python y pip
sudo apt install python3.10 python3.10-venv python3-pip

# Instalar Git
sudo apt install git

# Instalar poppler-utils (para PDFs si es necesario)
sudo apt install poppler-utils

# Continuar con pasos generales
```

### Docker (Opcional)

Si prefieres usar Docker:

**Crear `Dockerfile`**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

**Build y ejecutar**:
```bash
# Build imagen
docker build -t aseguraview .

# Ejecutar contenedor
docker run -p 8501:8501 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/credentials.json:/app/credentials.json \
  aseguraview
```

---

## Actualización

Para actualizar a una nueva versión:

```bash
# Navegar al directorio
cd aseguraview-primas

# Activar entorno virtual
source venv/bin/activate  # o venv\Scripts\activate en Windows

# Actualizar código
git pull origin main

# Actualizar dependencias
pip install --upgrade -r requirements.txt

# Reiniciar aplicación
streamlit run app.py
```

---

## Desinstalación

Para desinstalar completamente:

```bash
# 1. Desactivar entorno virtual
deactivate

# 2. Eliminar entorno virtual
rm -rf venv  # o rd /s /q venv en Windows

# 3. Eliminar repositorio
cd ..
rm -rf aseguraview-primas  # o rd /s /q aseguraview-primas en Windows
```

---

## Soporte

Si encuentras problemas no listados aquí:

1. Revisar logs de error completos
2. Buscar en [Issues de GitHub](https://github.com/juliancourse07/aseguraview-primas/issues)
3. Crear nuevo issue con:
   - Sistema operativo y versión
   - Versión de Python
   - Mensaje de error completo
   - Pasos para reproducir

---

## Conclusión

Si seguiste todos los pasos, deberías tener:

- ✅ Python 3.9+ instalado
- ✅ Repositorio clonado
- ✅ Entorno virtual configurado
- ✅ Dependencias instaladas
- ✅ Google Sheets configurado
- ✅ Credenciales funcionando
- ✅ Aplicación corriendo en `localhost:8501`

**¡Listo para usar AseguraView!** 🚀

Para siguiente paso, consulta:
- [DEPLOYMENT.md](DEPLOYMENT.md) para desplegar en producción
- [README.md](../README.md) para uso de la aplicación
- [CASOS_USO.md](CASOS_USO.md) para ejemplos prácticos

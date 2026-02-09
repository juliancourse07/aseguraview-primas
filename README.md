# 📊 AseguraView · Primas & Presupuesto

> Dashboard interactivo de ciencia de datos para análisis y pronóstico de primas de seguros en Colombia

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Academic-green.svg)](LICENSE)

## 📑 Tabla de Contenidos
- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Características Principales](#-características-principales)
- [Metodología de Ciencia de Datos](#-metodología-de-ciencia-de-datos)
- [Arquitectura de la Aplicación](#-arquitectura-de-la-aplicación)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso de la Aplicación](#-uso-de-la-aplicación)
- [Modelos Implementados](#-modelos-implementados)
- [Fuente de Datos](#-fuente-de-datos)
- [Métricas y KPIs](#-métricas-y-kpis)
- [Validación y Calidad](#-validación-y-calidad)
- [Documentación Adicional](#-documentación-adicional)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)
- [Autor](#-autor)

## 🎯 Descripción del Proyecto

AseguraView es una solución integral de análisis predictivo desarrollada para el sector asegurador colombiano. El sistema permite:

1. **Análisis de Producción Actual**: Monitoreo en tiempo real de primas por línea de negocio
2. **Nowcasting**: Estimación del cierre del mes en curso
3. **Forecasting**: Proyección de cierre anual con modelos de series temporales
4. **Análisis Presupuestario**: Comparación de ejecución vs presupuesto
5. **Planificación 2026**: Generación automática de presupuesto con ML
6. **Análisis Especializado FIANZAS**: Ajustes por Ley de Garantías Electorales

### Problema que Resuelve
Las aseguradoras necesitan:
- Proyectar con precisión el cierre de producción mensual y anual
- Identificar brechas entre ejecución y presupuesto
- Considerar factores externos (ej: Ley de Garantías en FIANZAS)
- Generar presupuestos basados en datos históricos y tendencias

## ✨ Características Principales

### 📈 Módulo de Primas
- **3 Vistas de Análisis**: Mes, Año, Acumulado
- **Métricas Clave**:
  - Producción actual vs período anterior
  - % de ejecución presupuestal
  - Forecast de cierre con SARIMAX/ARIMA
  - Crecimiento año a año
  - Requerimiento diario para cumplir meta
  
### 🏛️ Módulo FIANZAS
- Calendario de impacto Ley de Garantías 2026
- Ajustes automáticos por fase electoral:
  - Pre-electoral: Factor 0.75
  - Durante ley: Factor 0.25
  - Post-electoral: Factor 0.60
  - Recuperación: Factor 1.10
- Visualización de diferencias por ajuste

### 📊 Módulo Presupuesto 2026
- Generación automática con XGBoost
- Ajuste por IPC/inflación configurable
- Exportación a Excel
- Análisis por línea de negocio

## 🔬 Metodología de Ciencia de Datos

### 1. Recolección de Datos
- **Fuente**: Google Sheets (integración en tiempo real)
- **Periodicidad**: Mensual
- **Variables**:
  - Fecha
  - Línea de negocio (LINEA_PLUS)
  - Importe prima (IMP_PRIMA)
  - Presupuesto
  - Ramo

### 2. Procesamiento de Datos
- Normalización de fechas (formato colombiano DD/MM/YYYY)
- Limpieza de valores nulos
- Agregación por línea de negocio
- Detección y tratamiento de outliers
- Imputación conservadora para datos faltantes

### 3. Modelos Implementados

#### A. Forecasting con SARIMAX/ARIMA
- **Uso**: Pronóstico de primas mensuales y anuales
- **Proceso**:
  1. Análisis de estacionalidad
  2. Selección automática de parámetros (p,d,q)(P,D,Q,s)
  3. Entrenamiento con datos históricos
  4. Validación con SMAPE
  5. Ajuste conservador configurable (-5% a -20%)
- **Implementación**: `modelos/forecast_engine.py`

#### B. Ajuste Especializado FIANZAS
- **Uso**: Corrección de forecast por Ley de Garantías
- **Método**:
  - Identificación automática de fases electorales
  - Aplicación de factores de ajuste por fase
  - Cálculo de impacto mensual
- **Implementación**: `modelos/fianzas_adjuster.py`

#### C. Presupuesto 2026 con XGBoost
- **Uso**: Generación de presupuesto anual
- **Features**:
  - Histórico de producción por línea
  - Tendencias de crecimiento
  - Estacionalidad
  - Factores macroeconómicos (IPC)
- **Implementación**: `modelos/budget_2026.py`

### 4. Validación
- **SMAPE** (Symmetric Mean Absolute Percentage Error) para forecasts
- Validación cruzada temporal
- Comparación con períodos anteriores

## 🏗️ Arquitectura de la Aplicación

```
┌─────────────────────────────────────────────────────┐
│                   STREAMLIT UI                      │
│  (app.py - 619 líneas)                             │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐   │
│  │ Primas  │  │ FIANZAS  │  │ Presupuesto    │   │
│  │ Tab     │  │ Tab      │  │ 2026 Tab       │   │
│  └─────────┘  └──────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────┘
         │                │              │
         ▼                ▼              ▼
┌─────────────────────────────────────────────────────┐
│              COMPONENTES (UI)                       │
│  ├── charts.py       (Gráficos Plotly)            │
│  ├── sidebar.py      (Filtros)                    │
│  ├── tables.py       (Tablas HTML)                │
│  └── summary_cards.py (Métricas)                  │
└─────────────────────────────────────────────────────┘
         │                │              │
         ▼                ▼              ▼
┌─────────────────────────────────────────────────────┐
│               MODELOS (ML/TS)                       │
│  ├── forecast_engine.py   (SARIMAX/ARIMA)         │
│  ├── fianzas_adjuster.py  (Ley Garantías)         │
│  └── budget_2026.py       (XGBoost)               │
└─────────────────────────────────────────────────────┘
         │                │              │
         ▼                ▼              ▼
┌─────────────────────────────────────────────────────┐
│                 UTILS (Servicios)                   │
│  ├── data_loader.py      (Google Sheets API)      │
│  ├── data_processor.py   (ETL)                    │
│  ├── date_utils.py       (Fechas)                 │
│  └── formatters.py       (Formato moneda)         │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│            CONFIGURACIÓN                            │
│  ├── config.py           (Parámetros)             │
│  └── .env               (Credenciales)            │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              FUENTE DE DATOS                        │
│  Google Sheets (Producción + Fecha Corte)         │
└─────────────────────────────────────────────────────┘
```

## 🛠️ Tecnologías Utilizadas

### Lenguaje y Framework
- **Python 3.9+**: Lenguaje principal
- **Streamlit**: Framework web interactivo

### Ciencia de Datos y ML
- **pandas**: Manipulación de datos
- **numpy**: Computación numérica
- **statsmodels**: SARIMAX/ARIMA
- **xgboost**: Gradient Boosting
- **scikit-learn**: Preprocesamiento y validación

### Visualización
- **plotly**: Gráficos interactivos

### Integración de Datos
- **python-dotenv**: Variables de entorno

### Utilidades
- **openpyxl**: Exportación Excel
- **scipy**: Computación científica

## 📂 Estructura del Proyecto

```
aseguraview-primas/
│
├── 📄 app.py                    # Aplicación principal (619 líneas)
├── ⚙️ config.py                 # Configuración centralizada
├── 📋 requirements.txt          # Dependencias Python
├── 📦 packages.txt             # Paquetes sistema (poppler-utils)
├── 🔐 .env.example             # Template variables de entorno
├── 📖 README.md                # Este archivo
│
├── 🎨 componentes/             # Componentes de UI
│   ├── __init__.py
│   ├── charts.py              # Gráficos con Plotly
│   ├── sidebar.py             # Barra lateral con filtros
│   ├── summary_cards.py       # Tarjetas de resumen
│   └── tables.py              # Tablas HTML personalizadas
│
├── 🤖 modelos/                 # Modelos de ML/Time Series
│   ├── __init__.py
│   ├── forecast_engine.py     # Motor SARIMAX/ARIMA
│   ├── fianzas_adjuster.py    # Ajuste Ley de Garantías
│   └── budget_2026.py         # Generador presupuesto
│
├── 🔧 utils/                   # Utilidades y servicios
│   ├── __init__.py
│   ├── data_loader.py         # Carga desde Google Sheets
│   ├── data_processor.py      # Procesamiento y limpieza
│   ├── date_utils.py          # Utilidades de fechas
│   └── formatters.py          # Formateo de números/moneda
│
└── 📁 .devcontainer/           # Configuración Dev Container
    └── devcontainer.json

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes)
- Cuenta Google (para acceso a Sheets)
- Git

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/juliancourse07/aseguraview-primas.git
cd aseguraview-primas
```

### Paso 2: Crear Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno
```bash
# Copiar ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# GOOGLE_SHEET_ID=tu_id_de_sheet
# SHEET_NAME_DATOS=Hoja1
# SHEET_NAME_FECHA=Hoja2
```

### Paso 5: Configurar Acceso a Google Sheets
1. Crear proyecto en Google Cloud Console
2. Habilitar Google Sheets API
3. Crear credenciales (Service Account)
4. Descargar JSON de credenciales
5. Compartir Sheet con email del Service Account

### Paso 6: Ejecutar la Aplicación
```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

## 📱 Uso de la Aplicación

### 1. Filtros en Barra Lateral
- **Año de Análisis**: Seleccionar año a analizar
- **Línea de Negocio**: Filtrar por línea específica o ver todas
- **Ajuste Conservador**: Factor de corrección para forecasts (0-20%)

### 2. Tab Presentación
Información general del sistema y características

### 3. Tab Primas
- Seleccionar vista: **Mes** / **Año** / **Acumulado**
- Ver tabla resumen por línea con:
  - Producción actual vs anterior
  - % Ejecución presupuestal
  - Forecast de cierre
  - Crecimiento
  - Requerimiento diario
- Visualizar gráfico de pronóstico
- Descargar tabla detallada

### 4. Tab FIANZAS
- Ver calendario de impacto Ley de Garantías 2026
- Comparar forecast original vs ajustado
- Analizar diferencias mensuales

### 5. Tab Presupuesto 2026
- Ajustar % IPC/Incrementos
- Generar propuesta automática
- Descargar Excel con presupuesto

## 🧮 Modelos Implementados

### 1. ForecastEngine (SARIMAX/ARIMA)
**Archivo**: `modelos/forecast_engine.py`

**Funcionalidades**:
- Limpieza y sanitización de series temporales
- Detección automática de períodos parciales
- Entrenamiento de modelos SARIMAX
- Ajuste conservador configurable
- Cálculo de métricas (SMAPE)

**Parámetros Clave**:
```python
conservative_factor: float = 0.95  # Factor de ajuste (5% conservador)
order: tuple = (1, 1, 1)          # Orden ARIMA
seasonal_order: tuple = (1, 1, 1, 12)  # Estacionalidad mensual
```

### 2. FianzasAdjuster
**Archivo**: `modelos/fianzas_adjuster.py`

**Funcionalidades**:
- Identificación de fases electorales
- Aplicación de factores de ajuste
- Generación de calendario visual
- Resumen de impacto

**Fases y Factores**:
- Pre-electoral (Nov-Dic 2025): 0.75
- Ley activa (Ene-May 2026): 0.25
- Post-electoral (Jun-Ago 2026): 0.60
- Recuperación (Sep-Nov 2026): 1.10

### 3. Budget2026Generator
**Archivo**: `modelos/budget_2026.py`

**Funcionalidades**:
- Generación de features desde histórico
- Entrenamiento XGBoost por línea
- Ajuste por IPC
- Exportación a Excel

## 📊 Fuente de Datos

### Estructura de Google Sheets

**Hoja 1 - Datos de Producción**:
| Columna | Tipo | Descripción |
|---------|------|-------------|
| FECHA | Date | Fecha en formato DD/MM/YYYY |
| LINEA_PLUS | String | Línea de negocio agrupada |
| IMP_PRIMA | Numeric | Importe de prima |
| PRESUPUESTO | Numeric | Presupuesto mensual |
| RAMO | String | Ramo específico |

**Hoja 2 - Fecha de Corte**:
| Columna | Tipo | Descripción |
|---------|------|-------------|
| FECHA_CORTE | Date | Último día con datos disponibles |

### Líneas de Negocio (LINEA_PLUS)
- SOAT
- FIANZAS
- VIDA
- AUTOS
- HOGAR
- PYMES
- SALUD
- ACCIDENTES
- RESPONSABILIDAD CIVIL
- TRANSPORTE

## 📈 Métricas y KPIs

### Métricas de Producción
- **Producción Real**: Suma de primas emitidas
- **Presupuesto**: Meta establecida
- **% Ejecución**: (Producción / Presupuesto) × 100
- **Faltante**: Presupuesto - Producción

### Métricas de Forecast
- **Forecast Mensual**: Proyección mes actual
- **Forecast Anual**: Proyección cierre año
- **Cierre Estimado**: YTD Real + Forecast Faltante
- **% Forecast Ejecución**: (Cierre Estimado / Presupuesto) × 100

### Métricas de Crecimiento
- **Crecimiento COP**: Diferencia absoluta vs año anterior
- **Crecimiento %**: ((Actual / Anterior) - 1) × 100

### Métricas Operativas
- **Requerimiento x Día**: Faltante / Días hábiles restantes
- **SMAPE**: Error porcentual simétrico del modelo

## 🔍 Validación y Calidad

### Validación de Modelos
- **SMAPE < 15%**: Modelo aceptable
- **SMAPE 15-25%**: Modelo moderado
- **SMAPE > 25%**: Requiere revisión

### Controles de Calidad
- Detección de outliers
- Validación de fechas
- Completitud de datos
- Consistencia entre vistas

## 📚 Documentación Adicional

Para más información, consulta la documentación detallada:

- [📐 ARQUITECTURA.md](ARQUITECTURA.md) - Arquitectura técnica y patrones de diseño
- [🔬 METODOLOGIA.md](METODOLOGIA.md) - Metodología CRISP-DM aplicada
- [🎤 PRESENTACION.md](PRESENTACION.md) - Guía para presentación oral
- [📖 docs/](docs/) - Documentación técnica detallada
  - [🤖 MODELOS.md](docs/MODELOS.md) - Modelos de ML/TS en detalle
  - [📊 DATOS.md](docs/DATOS.md) - Diccionario de datos
  - [📋 CASOS_USO.md](docs/CASOS_USO.md) - Casos de uso del sistema
  - [⚙️ INSTALACION.md](docs/INSTALACION.md) - Instalación paso a paso
  - [🚀 DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guía de despliegue

## 🤝 Contribuciones

Este proyecto fue desarrollado como parte de un proyecto de grado en Ciencia de Datos.

### Metodología de Desarrollo
1. Análisis de requerimientos del sector asegurador
2. Diseño de arquitectura modular
3. Implementación iterativa por módulos
4. Pruebas con datos reales
5. Validación con expertos del negocio

## 📄 Licencia

Este proyecto es de uso académico como parte del proyecto de grado.

## 👤 Autor

**Julian Course**
- GitHub: [@juliancourse07](https://github.com/juliancourse07)
- Proyecto: AseguraView - Primas & Presupuesto
- Año: 2025

---

## 📞 Soporte

Para preguntas o problemas:
1. Abrir un issue en GitHub
2. Revisar documentación en `/docs`
3. Contactar al autor

---

## 🎓 Proyecto de Grado

Este proyecto representa la aplicación práctica de conceptos de:
- Ciencia de Datos
- Machine Learning
- Series Temporales
- Ingeniería de Software
- Visualización de Datos

**Objetivo Académico**: Demostrar la capacidad de desarrollar una solución end-to-end de análisis predictivo para resolver problemas reales del sector empresarial.

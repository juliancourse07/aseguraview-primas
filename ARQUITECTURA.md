# 📐 Arquitectura de AseguraView

Este documento describe la arquitectura técnica, los patrones de diseño y las decisiones arquitectónicas del sistema AseguraView.

## 📑 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura de Capas](#arquitectura-de-capas)
- [Patrones de Diseño](#patrones-de-diseño)
- [Componentes Principales](#componentes-principales)
- [Flujo de Datos](#flujo-de-datos)
- [Diagramas de Secuencia](#diagramas-de-secuencia)
- [Decisiones Arquitectónicas](#decisiones-arquitectónicas)
- [Escalabilidad y Rendimiento](#escalabilidad-y-rendimiento)

---

## Visión General

AseguraView implementa una **arquitectura en capas** que separa responsabilidades y facilita el mantenimiento. El sistema está construido sobre **Streamlit** como framework de UI y sigue principios de **separación de concerns** y **modularidad**.

### Principios Arquitectónicos

1. **Separación de Responsabilidades**: Cada módulo tiene una responsabilidad clara
2. **Modularidad**: Componentes reutilizables e independientes
3. **Configuración Centralizada**: Un solo punto de configuración
4. **Inyección de Dependencias**: Componentes configurables desde exterior
5. **Single Source of Truth**: Datos centralizados desde Google Sheets

---

## Arquitectura de Capas

```
┌─────────────────────────────────────────────────────────────┐
│                      CAPA DE PRESENTACIÓN                   │
│                         (Streamlit UI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Tab 1:     │  │   Tab 2:     │  │   Tab 3:     │    │
│  │   Primas     │  │   FIANZAS    │  │  Presupuesto │    │
│  │              │  │              │  │     2026     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE COMPONENTES UI                   │
│                      (componentes/)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐│
│  │  charts   │  │  sidebar  │  │  tables   │  │ summary │││
│  │    .py    │  │    .py    │  │    .py    │  │_cards.py│││
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘││
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE LÓGICA DE NEGOCIO                 │
│                         (modelos/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  forecast_   │  │   fianzas_   │  │   budget_    │    │
│  │  engine.py   │  │ adjuster.py  │  │   2026.py    │    │
│  │              │  │              │  │              │    │
│  │ SARIMAX/     │  │ Ajustes Ley  │  │  XGBoost     │    │
│  │ ARIMA        │  │  Garantías   │  │  Budget      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE SERVICIOS                         │
│                        (utils/)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  data_   │  │  data_   │  │  date_   │  │ format-  │  │
│  │ loader   │  │processor │  │  utils   │  │  ters    │  │
│  │   .py    │  │   .py    │  │   .py    │  │   .py    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE CONFIGURACIÓN                      │
│                     (config.py + .env)                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │  • Parámetros de modelos                           │   │
│  │  • Configuración de Google Sheets                  │   │
│  │  • Factores de ajuste Ley de Garantías            │   │
│  │  • Líneas de negocio                               │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     CAPA DE DATOS                           │
│                    (Google Sheets)                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │  • Datos de producción histórica                   │   │
│  │  • Presupuestos por línea                          │   │
│  │  • Fecha de corte                                  │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Patrones de Diseño

### 1. **Patrón Strategy** (Estrategia)

Utilizado en los modelos de forecasting para permitir diferentes estrategias de predicción.

```python
# Interfaz común para motores de forecast
class ForecastEngine:
    def forecast_monthly(self, ts, periods):
        # Implementación SARIMAX
        pass
    
    def forecast_yearly(self, ts, year):
        # Implementación ARIMA
        pass
```

**Beneficios**:
- Fácil cambio entre algoritmos
- Código extensible para nuevos modelos
- Testing independiente de cada estrategia

### 2. **Patrón Facade** (Fachada)

Los componentes de UI actúan como fachadas simplificadas para funcionalidad compleja.

```python
# sidebar.py simplifica la configuración
def render_sidebar(df_full, cutoff_date):
    # Encapsula toda la lógica de filtros
    year = st.selectbox(...)
    linea = st.selectbox(...)
    return year, linea, conservative_pct
```

**Beneficios**:
- Interfaz simple para usuario
- Complejidad oculta detrás de componentes
- Reutilización de componentes

### 3. **Patrón Adapter** (Adaptador)

`data_processor.py` adapta datos crudos de Google Sheets al formato requerido.

```python
def normalize_dataframe(df_raw):
    # Adapta formato DD/MM/YYYY a pandas datetime
    # Normaliza columnas
    # Limpia valores nulos
    return df_normalized
```

**Beneficios**:
- Desacoplamiento entre fuente de datos y lógica
- Fácil cambio de fuente de datos
- Validación centralizada

### 4. **Patrón Singleton Implícito**

La configuración en `config.py` actúa como singleton de facto.

```python
# config.py - una sola instancia de configuración
SHEET_ID = os.getenv('GOOGLE_SHEET_ID', ...)
LEY_GARANTIAS_2026 = {...}
ADJUSTMENT_FACTORS = {...}
```

**Beneficios**:
- Configuración centralizada
- Un solo punto de cambio
- Fácil testing con variables de entorno

### 5. **Patrón Template Method**

El flujo de pronóstico sigue un template definido:

```python
def forecast_flow(data, year):
    # 1. Sanitizar datos
    clean_data = sanitize_series(data, year)
    
    # 2. Separar entrenamiento/test
    train, test, is_partial = split_series_exclude_partial(...)
    
    # 3. Entrenar modelo
    model = train_sarimax(train)
    
    # 4. Hacer forecast
    forecast = model.forecast(periods)
    
    # 5. Aplicar ajustes
    adjusted = apply_conservative_factor(forecast)
    
    return adjusted
```

**Beneficios**:
- Flujo consistente y predecible
- Pasos intercambiables
- Fácil debugging

---

## Componentes Principales

### 1. Capa de Presentación (app.py)

**Responsabilidad**: Orquestar la interfaz de usuario y coordinar componentes.

**Características**:
- 619 líneas de código
- 3 tabs principales (Primas, FIANZAS, Presupuesto 2026)
- Gestión de estado con `st.session_state`
- Carga inicial de datos con caching (`@st.cache_data`)

**Patrón de carga de datos**:
```python
@st.cache_data(ttl=3600)
def load_all_data():
    df = load_data()
    cutoff = load_cutoff_date()
    return df, cutoff
```

### 2. Capa de Componentes UI (componentes/)

#### charts.py
- Generación de gráficos interactivos con Plotly
- Gráficos de forecast con intervalos de confianza
- Gráficos de comparación año a año

#### sidebar.py
- Filtros principales: Año, Línea de Negocio, Ajuste Conservador
- Validación de selecciones
- Retorno de parámetros filtrados

#### summary_cards.py
- Tarjetas de métricas clave
- Badges de crecimiento (positivo/negativo)
- Formateo de números grandes

#### tables.py
- Tablas HTML personalizadas con estilos
- Exportación a Excel
- Formateo condicional

### 3. Capa de Lógica de Negocio (modelos/)

#### forecast_engine.py
**Clase**: `ForecastEngine`

**Métodos clave**:
- `sanitize_series()`: Limpia series temporales
- `split_series_exclude_partial()`: Separa train/test
- `train_sarimax()`: Entrena modelo SARIMAX
- `forecast_monthly()`: Proyecta mes actual
- `forecast_yearly()`: Proyecta cierre anual
- `calculate_smape()`: Calcula error del modelo

**Algoritmo SARIMAX**:
```
SARIMAX(p, d, q)(P, D, Q, s)
- p: orden autorregresivo
- d: orden de diferenciación
- q: orden de media móvil
- P: orden autorregresivo estacional
- D: orden de diferenciación estacional
- Q: orden de media móvil estacional
- s: período estacional (12 para mensual)
```

#### fianzas_adjuster.py
**Clase**: `FianzasAdjuster`

**Métodos clave**:
- `get_periodo_fase()`: Identifica fase electoral
- `adjust_forecast()`: Aplica factores de ajuste
- `generate_calendar()`: Crea calendario visual
- `calculate_impact()`: Calcula impacto mensual

**Fases identificadas**:
1. Pre-electoral: 2 meses antes (Nov-Dic 2025)
2. Ley activa: Durante elecciones (Ene-May 2026)
3. Post-electoral: 2 meses después (Jun-Ago 2026)
4. Recuperación: 3 meses de rebote (Sep-Nov 2026)

#### budget_2026.py
**Clase**: `Budget2026Generator`

**Métodos clave**:
- `prepare_features()`: Crea features de histórico
- `train_model()`: Entrena XGBoost por línea
- `generate_budget()`: Genera presupuesto anual
- `export_to_excel()`: Exporta resultados

**Features utilizados**:
- Producción histórica por mes
- Tendencias de crecimiento
- Componentes estacionales
- Factores macroeconómicos (IPC)

### 4. Capa de Servicios (utils/)

#### data_loader.py
- Conexión a Google Sheets
- Carga de datos de producción
- Carga de fecha de corte
- Manejo de errores de conexión

#### data_processor.py
- Normalización de fechas
- Limpieza de valores nulos
- Agregación por dimensiones
- Validación de estructura de datos

#### date_utils.py
- Conversión de formatos de fecha
- Cálculo de días hábiles
- Detección de períodos parciales
- Utilidades de temporalidad

#### formatters.py
- Formato de moneda colombiana (COP)
- Formateo de porcentajes
- Badges HTML para métricas
- Formateo de números grandes (K, M, B)

---

## Flujo de Datos

### Flujo Principal de Análisis

```
┌──────────────────────────────────────────────────────────┐
│ 1. CARGA DE DATOS                                        │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Google Sheets API            │
    │  - Datos producción           │
    │  - Fecha corte                │
    └───────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 2. PROCESAMIENTO Y NORMALIZACIÓN                        │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  data_processor.py            │
    │  - Normalizar fechas          │
    │  - Limpiar nulos              │
    │  - Validar estructura         │
    └───────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 3. FILTRADO POR USUARIO                                 │
└──────────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Sidebar                      │
    │  - Año seleccionado           │
    │  - Línea de negocio           │
    │  - Ajuste conservador         │
    └───────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│ 4. ANÁLISIS Y MODELADO                                  │
└──────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬───────────────┐
        ▼                       ▼               ▼
┌───────────────┐      ┌───────────────┐   ┌──────────────┐
│ Forecast      │      │ Ajuste        │   │ Presupuesto  │
│ SARIMAX/ARIMA │      │ FIANZAS       │   │ XGBoost 2026 │
└───────────────┘      └───────────────┘   └──────────────┘
        │                       │               │
        └───────────┬───────────┘               │
                    ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│ 5. VISUALIZACIÓN                                         │
└──────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬───────────────┐
        ▼                       ▼               ▼
┌───────────────┐      ┌───────────────┐   ┌──────────────┐
│ Gráficos      │      │ Tablas        │   │ Métricas     │
│ Plotly        │      │ HTML          │   │ Cards        │
└───────────────┘      └───────────────┘   └──────────────┘
```

### Flujo de Forecasting Detallado

```
Entrada: Serie temporal de producción histórica
│
├─► 1. SANITIZACIÓN
│   ├─ Eliminar ceros finales del año actual
│   ├─ Eliminar valores nulos
│   └─ Validar continuidad temporal
│
├─► 2. DETECCIÓN DE PERÍODO PARCIAL
│   ├─ Identificar si mes actual está incompleto
│   ├─ Excluir mes parcial del entrenamiento
│   └─ Marcar para nowcasting separado
│
├─► 3. ENTRENAMIENTO MODELO
│   ├─ Configurar SARIMAX(1,1,1)(1,1,1,12)
│   ├─ Entrenar con datos históricos completos
│   └─ Validar convergencia
│
├─► 4. GENERACIÓN DE FORECAST
│   ├─ Forecast mensual (mes actual si parcial)
│   ├─ Forecast anual (meses restantes)
│   └─ Calcular intervalos de confianza
│
├─► 5. AJUSTE CONSERVADOR
│   ├─ Aplicar factor de ajuste (configurable)
│   ├─ Reducir predicción en % definido
│   └─ Mantener intervalos ajustados
│
├─► 6. VALIDACIÓN
│   ├─ Calcular SMAPE vs períodos anteriores
│   ├─ Verificar razonabilidad de resultados
│   └─ Alertar si error > 25%
│
└─► Salida: Forecast ajustado con métricas
```

---

## Diagramas de Secuencia

### Secuencia: Carga Inicial de Aplicación

```
Usuario          app.py       data_loader    Google Sheets    data_processor
  │                │                │               │                │
  │──Abre app──────>│                │               │                │
  │                │──load_data()──>│               │                │
  │                │                │──GET API─────>│                │
  │                │                │<──JSON data───│                │
  │                │<──df_raw───────│               │                │
  │                │──normalize_dataframe(df_raw)───>│                │
  │                │<──df_clean────────────────────│                │
  │                │──load_cutoff_date()──>         │                │
  │                │<──cutoff──────────────────────│                │
  │<──UI cargada───│                │               │                │
```

### Secuencia: Generación de Forecast

```
Usuario       app.py    ForecastEngine    SARIMAX     componentes
  │             │             │              │             │
  │─Select año─>│             │              │             │
  │             │─forecast()─>│              │             │
  │             │             │─sanitize()───>             │
  │             │             │─split()──────>             │
  │             │             │─train()──────>│            │
  │             │             │              │─fit()───┐  │
  │             │             │              │<────────┘  │
  │             │             │<─model───────│            │
  │             │             │─predict()────>│            │
  │             │             │<─forecast────│            │
  │             │             │─adjust()─────>             │
  │             │<─result────│              │             │
  │             │─render_forecast_chart(result)──────────>│
  │<──Gráfico actualizado─────────────────────────────────│
```

### Secuencia: Ajuste FIANZAS

```
Usuario       app.py    FianzasAdjuster    forecast_result    calendar
  │             │             │                   │              │
  │─Tab FIANZAS>│             │                   │              │
  │             │─adjust()───>│                   │              │
  │             │             │─get_periodo_fase()>              │
  │             │             │─apply_factors()──>│              │
  │             │             │─calculate_impact()>              │
  │             │<─adjusted───│                   │              │
  │             │─generate_calendar()────────────────────────────>│
  │<──Calendario + Forecast ajustado──────────────────────────────│
```

---

## Decisiones Arquitectónicas

### ADR-001: Uso de Streamlit como Framework

**Contexto**: Necesitamos un framework para construir dashboard interactivo.

**Decisión**: Usar Streamlit

**Razones**:
- ✅ Rápido desarrollo de prototipos
- ✅ Python nativo (sin necesidad de HTML/CSS/JS)
- ✅ Reactividad automática
- ✅ Fácil despliegue
- ❌ Limitaciones en personalización avanzada
- ❌ Difícil testing de UI

**Alternativas consideradas**: Dash, Flask + React

### ADR-002: Google Sheets como Fuente de Datos

**Contexto**: Necesitamos almacenar y acceder a datos de producción.

**Decisión**: Usar Google Sheets

**Razones**:
- ✅ Familiar para usuarios de negocio
- ✅ Fácil actualización manual
- ✅ Sin infraestructura de BD
- ✅ Versionamiento automático
- ❌ Límites de volumen (10M celdas)
- ❌ Latencia en consultas grandes

**Alternativas consideradas**: PostgreSQL, MongoDB, CSV files

### ADR-003: SARIMAX/ARIMA para Forecasting

**Contexto**: Necesitamos modelo para pronóstico de series temporales.

**Decisión**: Usar SARIMAX/ARIMA

**Razones**:
- ✅ Interpretable y explicable
- ✅ Captura estacionalidad
- ✅ Funciona bien con datos mensuales
- ✅ Rápido entrenamiento
- ❌ Asume estacionariedad
- ❌ No captura relaciones no lineales

**Alternativas consideradas**: Prophet, LSTM, XGBoost regressor

### ADR-004: XGBoost para Presupuesto 2026

**Contexto**: Generar presupuesto anual considerando múltiples factores.

**Decisión**: Usar XGBoost

**Razones**:
- ✅ Maneja bien features heterogéneos
- ✅ Robusto a outliers
- ✅ Captura relaciones no lineales
- ✅ Feature importance interpretable
- ❌ Requiere más datos de entrenamiento
- ❌ Menos interpretable que ARIMA

**Alternativas consideradas**: Random Forest, Linear Regression, Prophet

### ADR-005: Arquitectura Modular en Capas

**Contexto**: Organizar código de 619 líneas en app.py.

**Decisión**: Separar en capas (componentes/, modelos/, utils/)

**Razones**:
- ✅ Separación de responsabilidades
- ✅ Reutilización de código
- ✅ Testing independiente por módulo
- ✅ Mantenibilidad a largo plazo
- ❌ Mayor complejidad inicial
- ❌ Más archivos que gestionar

**Alternativas consideradas**: Monolito en un solo archivo, microservicios

---

## Escalabilidad y Rendimiento

### Optimizaciones Implementadas

#### 1. Caching de Datos
```python
@st.cache_data(ttl=3600)
def load_all_data():
    # Cache por 1 hora
    return df, cutoff_date
```

**Beneficio**: Evita cargas repetidas de Google Sheets (latencia ~2-5s)

#### 2. Lazy Loading de Modelos
- Modelos solo se entrenan cuando se selecciona la tab correspondiente
- No se entrenan todos los modelos al inicio

#### 3. Procesamiento Vectorizado
```python
# Uso de pandas/numpy para operaciones vectorizadas
df['growth'] = (df['current'] / df['previous'] - 1) * 100
# En lugar de loops sobre filas
```

#### 4. Agregaciones Previas
- Datos agregados por línea de negocio antes de pasarlos a modelos
- Reduce volumen de datos procesados

### Limitaciones de Escala

#### Límites Actuales
- **Datos**: ~50,000 filas de producción histórica
- **Líneas de negocio**: 10 líneas
- **Período**: 2007-2026 (20 años)
- **Usuarios concurrentes**: 1-5 (single instance)

#### Escalabilidad Futura
Para escalar a mayor volumen:
1. **Base de datos relacional**: Reemplazar Google Sheets
2. **Caching distribuido**: Redis para múltiples instancias
3. **Load balancing**: Múltiples instancias de Streamlit
4. **Procesamiento asíncrono**: Celery para modelos pesados
5. **Microservicios**: Separar forecasting engine en servicio independiente

---

## Seguridad

### Medidas Implementadas

1. **Variables de Entorno**: Credenciales en `.env` (no commiteadas)
2. **Service Account**: Acceso limitado solo a Google Sheets específico
3. **Sin Exposición de Datos**: No se expone información sensible en UI
4. **Validación de Entrada**: Validación de datos desde Google Sheets

### Consideraciones Futuras

1. **Autenticación de usuarios**: OAuth para acceso controlado
2. **Encriptación de datos**: Datos sensibles encriptados en tránsito
3. **Auditoría**: Logging de acciones y cambios
4. **Rate limiting**: Limitar requests a APIs externas

---

## Testing

### Estrategia de Testing

Actualmente el proyecto es académico y no incluye suite de tests formal, pero se recomienda:

#### Tests Unitarios
```python
# Ejemplo tests para ForecastEngine
def test_sanitize_series_removes_trailing_zeros():
    ts = pd.Series([100, 200, 0, 0], 
                   index=pd.date_range('2024-01', periods=4, freq='MS'))
    engine = ForecastEngine()
    result = engine.sanitize_series(ts, ref_year=2024)
    assert len(result) == 2

def test_forecast_monthly_returns_positive():
    ts = create_sample_series()
    engine = ForecastEngine()
    forecast = engine.forecast_monthly(ts, periods=3)
    assert (forecast > 0).all()
```

#### Tests de Integración
- Validar carga de datos desde Google Sheets
- Validar flujo completo de forecast
- Validar exportación a Excel

#### Tests de UI (Manual)
- Verificar cambios de filtros actualizan datos
- Verificar gráficos se renderizan correctamente
- Verificar descarga de reportes

---

## Monitoreo y Logging

### Logging Actual

El proyecto usa logging básico de Python:
```python
import warnings
warnings.filterwarnings("ignore")
```

### Monitoreo Recomendado

Para producción, implementar:
1. **Application Performance Monitoring (APM)**: New Relic, DataDog
2. **Error Tracking**: Sentry
3. **Usage Analytics**: Google Analytics, Mixpanel
4. **Model Monitoring**: MLflow para tracking de modelos

---

## Conclusión

AseguraView implementa una arquitectura modular y escalable que:
- ✅ Separa claramente responsabilidades
- ✅ Facilita mantenimiento y extensión
- ✅ Usa patrones de diseño reconocidos
- ✅ Optimiza rendimiento con caching
- ✅ Es fácil de entender y documentar

La arquitectura es apropiada para un **proyecto académico** y una **aplicación MVP** para un equipo pequeño (1-5 usuarios). Para escalar a producción empresarial, se recomiendan las mejoras descritas en la sección de escalabilidad.

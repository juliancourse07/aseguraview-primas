# 📊 Diccionario de Datos - AseguraView

Este documento describe la estructura detallada de los datos utilizados en AseguraView, incluyendo fuentes, esquemas, tipos de datos y validaciones.

## 📑 Tabla de Contenidos

- [Visión General](#visión-general)
- [Fuente de Datos: Google Sheets](#fuente-de-datos-google-sheets)
- [Estructura de Datos](#estructura-de-datos)
- [Transformaciones y Limpieza](#transformaciones-y-limpieza)
- [Calidad de Datos](#calidad-de-datos)
- [Ejemplos de Datos](#ejemplos-de-datos)

---

## Visión General

### Fuente Principal

- **Sistema**: Google Sheets
- **Actualización**: Manual, diaria
- **Propietario**: Área de Producción/Planeación
- **Período**: 2007-2025 (18 años)
- **Volumen**: ~50,000 registros
- **Frecuencia original**: Diaria
- **Frecuencia procesada**: Mensual (agregación)

### Estructura de Hojas

```
Google Spreadsheet
├── Hoja 1: "Datos de Producción"
│   └── Transacciones de primas por fecha, línea y ramo
│
└── Hoja 2: "Fecha de Corte"
    └── Último día con datos disponibles
```

---

## Fuente de Datos: Google Sheets

### Conexión

**Configuración** (en `.env`):
```bash
GOOGLE_SHEET_ID=1ThVwW3IbkL7Dw_Vrs9heT1QMiHDZw1Aj-n0XNbDi9i8
SHEET_NAME_DATOS=Hoja1
SHEET_NAME_FECHA=Hoja2
```

**Autenticación**:
- Método: Service Account (JSON credentials)
- Permisos: Lectura únicamente
- API: Google Sheets API v4

### Hoja 1: Datos de Producción

#### Estructura de Columnas

| # | Nombre Columna | Tipo | Nullable | Descripción | Ejemplo |
|---|---------------|------|----------|-------------|---------|
| 1 | FECHA | Date | No | Fecha de emisión de la póliza | 01/01/2024 |
| 2 | LINEA_PLUS | String | No | Línea de negocio agrupada | AUTOS |
| 3 | IMP_PRIMA | Numeric | Sí | Importe de la prima en COP | 1500000 |
| 4 | PRESUPUESTO | Numeric | Sí | Presupuesto mensual en COP | 2000000 |
| 5 | RAMO | String | Sí | Ramo específico del seguro | AUTOS PARTICULARES |

#### Detalle por Columna

##### FECHA

**Tipo**: Date  
**Formato esperado**: `DD/MM/YYYY` (formato colombiano)  
**Ejemplos válidos**:
- `01/01/2024` → 1 de enero de 2024
- `15/06/2023` → 15 de junio de 2023
- `31/12/2022` → 31 de diciembre de 2022

**Validaciones**:
- ✅ Debe ser una fecha válida
- ✅ No puede ser futura (> fecha actual)
- ✅ Debe estar en rango 2007-2025
- ❌ Formato `MM/DD/YYYY` se rechaza

**Transformación**:
```python
df['FECHA'] = pd.to_datetime(df['FECHA'], 
                             format='%d/%m/%Y', 
                             dayfirst=True)
```

##### LINEA_PLUS

**Tipo**: String  
**Descripción**: Línea de negocio agrupada (nivel de agregación principal)

**Valores permitidos** (10 líneas):
1. `SOAT` - Seguro Obligatorio de Accidentes de Tránsito
2. `FIANZAS` - Fianzas y Garantías
3. `VIDA` - Seguros de Vida
4. `AUTOS` - Automóviles (sin SOAT)
5. `HOGAR` - Seguros de Hogar
6. `PYMES` - Pequeñas y Medianas Empresas
7. `SALUD` - Seguros de Salud
8. `ACCIDENTES` - Accidentes Personales
9. `RESPONSABILIDAD CIVIL` - RC General
10. `TRANSPORTE` - Transporte de Mercancías

**Validaciones**:
- ✅ Debe ser uno de los 10 valores permitidos
- ✅ Case-insensitive (se normaliza a mayúsculas)
- ✅ Espacios múltiples se eliminan

**Transformación**:
```python
df['LINEA_PLUS'] = df['LINEA_PLUS'].str.upper().str.strip()
```

##### IMP_PRIMA

**Tipo**: Numeric (Float)  
**Unidad**: COP (Pesos Colombianos)  
**Descripción**: Importe de la prima emitida

**Rango esperado**:
- **Mínimo**: 0 COP (puede haber registros sin prima por cancelaciones)
- **Máximo**: ~$500M COP (pólizas corporativas grandes)
- **Promedio**: ~$1M COP
- **Mediana**: ~$500K COP

**Valores especiales**:
- `NULL` → Se trata como 0
- `0` → Válido (puede ser cancelación o ajuste)
- Negativos → Se rechazan (error de datos)

**Validaciones**:
- ✅ Debe ser numérico
- ✅ Debe ser >= 0
- ⚠️ Si > $1B, se marca como outlier potencial

**Transformación**:
```python
df['IMP_PRIMA'] = pd.to_numeric(df['IMP_PRIMA'], errors='coerce')
df['IMP_PRIMA'] = df['IMP_PRIMA'].fillna(0)
df.loc[df['IMP_PRIMA'] < 0, 'IMP_PRIMA'] = 0
```

##### PRESUPUESTO

**Tipo**: Numeric (Float)  
**Unidad**: COP (Pesos Colombianos)  
**Descripción**: Presupuesto mensual asignado a la línea/ramo

**Características**:
- Se repite para todas las transacciones del mismo mes/línea
- Es un valor de referencia, no acumulativo
- Se define al inicio del año y puede tener ajustes

**Rango esperado**:
- Varía por línea de negocio
- SOAT: $15B-$20B/mes
- FIANZAS: $8B-$12B/mes
- Otras líneas: $1B-$10B/mes

**Valores especiales**:
- `NULL` → Se imputa con promedio histórico de la línea
- `0` → Se considera como sin presupuesto asignado

**Transformación**:
```python
df['PRESUPUESTO'] = df.groupby('LINEA_PLUS')['PRESUPUESTO'].transform(
    lambda x: x.fillna(x.mean())
)
```

##### RAMO

**Tipo**: String  
**Descripción**: Ramo específico del seguro (nivel más granular que LINEA_PLUS)

**Ejemplos por línea**:

**AUTOS**:
- `AUTOS PARTICULARES`
- `AUTOS COMERCIALES`
- `MOTOS`
- `FLOTAS`

**FIANZAS**:
- `FIANZAS CUMPLIMIENTO`
- `FIANZAS SERIEDAD OFERTA`
- `FIANZAS ANTICIPO`
- `FIANZAS SALARIOS`
- `FIANZAS BUEN MANEJO`
- `FIANZAS GARANTIA`

**VIDA**:
- `VIDA INDIVIDUAL`
- `VIDA GRUPO`
- `VIDA DEUDORES`

**Uso en sistema**:
- FIANZAS: Se usa para filtrar ramos afectados por Ley de Garantías
- Otros: Solo informativo, no afecta modelos

### Hoja 2: Fecha de Corte

#### Estructura

| # | Nombre Columna | Tipo | Nullable | Descripción | Ejemplo |
|---|---------------|------|----------|-------------|---------|
| 1 | FECHA_CORTE | Date | No | Último día con datos disponibles | 15/05/2024 |

#### Detalle

**FECHA_CORTE**

**Tipo**: Date  
**Formato**: `DD/MM/YYYY`

**Descripción**: Indica hasta qué fecha están disponibles los datos de producción. Permite al sistema determinar si el mes actual está completo o parcial.

**Uso en sistema**:
```python
if cutoff_date.day < ultimo_dia_del_mes:
    mes_parcial = True
    # Excluir mes actual del entrenamiento
else:
    mes_parcial = False
    # Mes completo, incluir en entrenamiento
```

**Actualización**: Diaria (manual o automática)

---

## Estructura de Datos

### Datos Raw (Cargados desde Sheets)

```python
df_raw.shape
# (50247, 5)

df_raw.head()
#        FECHA    LINEA_PLUS  IMP_PRIMA  PRESUPUESTO              RAMO
# 0  1/1/2024          SOAT    1500000      2000000              SOAT
# 1  1/1/2024        FIANZAS    2300000      1500000  FIANZAS CUMPLIMIENTO
# 2  1/1/2024          VIDA    1200000       800000         VIDA GRUPO
# 3  2/1/2024          AUTOS    890000       700000   AUTOS PARTICULARES
# 4  2/1/2024         HOGAR    450000       350000           HOGAR TODO RIESGO

df_raw.dtypes
# FECHA           object
# LINEA_PLUS      object
# IMP_PRIMA       float64
# PRESUPUESTO     float64
# RAMO            object
```

### Datos Procesados (Después de normalización)

```python
df_clean.shape
# (49832, 5)  # Algunas filas eliminadas por validaciones

df_clean.head()
#        FECHA    LINEA_PLUS  IMP_PRIMA  PRESUPUESTO              RAMO
# 0  2024-01-01          SOAT    1500000      2000000              SOAT
# 1  2024-01-01        FIANZAS    2300000      1500000  FIANZAS CUMPLIMIENTO
# 2  2024-01-01          VIDA    1200000       800000         VIDA GRUPO
# 3  2024-01-02          AUTOS    890000       700000   AUTOS PARTICULARES
# 4  2024-01-02         HOGAR    450000       350000           HOGAR TODO RIESGO

df_clean.dtypes
# FECHA           datetime64[ns]
# LINEA_PLUS      object
# IMP_PRIMA       float64
# PRESUPUESTO     float64
# RAMO            object
```

### Datos Agregados (Por mes y línea)

```python
df_monthly = df_clean.groupby([
    pd.Grouper(key='FECHA', freq='MS'),  # Month Start
    'LINEA_PLUS'
]).agg({
    'IMP_PRIMA': 'sum',
    'PRESUPUESTO': 'first'  # Tomar primer valor (presupuesto es mensual)
}).reset_index()

df_monthly.shape
# (2160, 4)  # 18 años × 12 meses × 10 líneas

df_monthly.head()
#        FECHA    LINEA_PLUS  IMP_PRIMA  PRESUPUESTO
# 0  2007-01-01          SOAT   15000000     18000000
# 1  2007-01-01        FIANZAS   8500000     10000000
# 2  2007-01-01          VIDA   6200000      7000000
# 3  2007-02-01          SOAT   16500000     18000000
# 4  2007-02-01        FIANZAS   9100000     10000000
```

---

## Transformaciones y Limpieza

### Pipeline Completo

```
1. CARGA
   ↓
2. NORMALIZACIÓN
   - Fechas a datetime
   - Strings a uppercase
   - Números a float
   ↓
3. VALIDACIÓN
   - Rechazar fechas inválidas
   - Rechazar líneas no permitidas
   - Rechazar valores negativos
   ↓
4. LIMPIEZA
   - Eliminar nulos en FECHA
   - Imputar nulos en IMP_PRIMA (0)
   - Imputar nulos en PRESUPUESTO (promedio)
   ↓
5. TRATAMIENTO OUTLIERS
   - Identificar con IQR
   - Winsorizar valores extremos
   ↓
6. AGREGACIÓN
   - Agrupar por mes y línea
   - Sumar IMP_PRIMA
   - Tomar primer PRESUPUESTO
   ↓
7. FEATURES
   - Agregar año, mes, trimestre
   - Calcular YTD
   - Calcular % ejecución
```

### Código de Normalización

```python
def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza DataFrame cargado desde Google Sheets.
    """
    df = df.copy()
    
    # 1. Fechas
    df['FECHA'] = pd.to_datetime(df['FECHA'], 
                                  format='%d/%m/%Y', 
                                  dayfirst=True,
                                  errors='coerce')
    
    # 2. Eliminar filas con fecha nula
    df = df.dropna(subset=['FECHA'])
    
    # 3. Líneas a uppercase y trim
    df['LINEA_PLUS'] = df['LINEA_PLUS'].str.upper().str.strip()
    
    # 4. Validar líneas permitidas
    lineas_validas = [
        'SOAT', 'FIANZAS', 'VIDA', 'AUTOS', 'HOGAR',
        'PYMES', 'SALUD', 'ACCIDENTES', 'RESPONSABILIDAD CIVIL', 'TRANSPORTE'
    ]
    df = df[df['LINEA_PLUS'].isin(lineas_validas)]
    
    # 5. Convertir a numérico
    df['IMP_PRIMA'] = pd.to_numeric(df['IMP_PRIMA'], errors='coerce')
    df['PRESUPUESTO'] = pd.to_numeric(df['PRESUPUESTO'], errors='coerce')
    
    # 6. Limpiar valores negativos
    df.loc[df['IMP_PRIMA'] < 0, 'IMP_PRIMA'] = 0
    
    # 7. Imputar nulos
    df['IMP_PRIMA'] = df['IMP_PRIMA'].fillna(0)
    df['PRESUPUESTO'] = df.groupby('LINEA_PLUS')['PRESUPUESTO'].transform(
        lambda x: x.fillna(x.mean())
    )
    
    return df
```

---

## Calidad de Datos

### Estadísticas de Calidad

**Completitud**:
```python
Columna          % Completo   Registros Nulos
FECHA            100%         0
LINEA_PLUS       100%         0
IMP_PRIMA        98.2%        905 (imputados a 0)
PRESUPUESTO      96.8%        1,607 (imputados con promedio)
RAMO             94.5%        2,764 (opcional)
```

**Consistencia**:
```python
# Fechas fuera de rango
fechas_futuras = 0
fechas_pre_2007 = 23 (eliminadas)

# Líneas no válidas
lineas_invalidas = 0 (eliminadas en validación)

# Valores negativos
imp_prima_negativos = 45 (corregidos a 0)
```

**Outliers**:
```python
# Método: IQR (Interquartile Range)
# Q1 - 1.5*IQR < valor < Q3 + 1.5*IQR

Por línea:
SOAT:        89 outliers (0.4%)
FIANZAS:     156 outliers (0.8%)
VIDA:        67 outliers (0.3%)
AUTOS:       134 outliers (0.7%)
...
TOTAL:       723 outliers (1.4%)

Acción: Winsorización (reemplazar con límites IQR)
```

### Monitoreo de Calidad

**Checks Automáticos**:
```python
def validate_data_quality(df):
    """
    Valida calidad de datos y retorna reporte.
    """
    checks = {
        'total_rows': len(df),
        'null_fecha': df['FECHA'].isnull().sum(),
        'null_imp_prima': df['IMP_PRIMA'].isnull().sum(),
        'negative_prima': (df['IMP_PRIMA'] < 0).sum(),
        'invalid_lineas': (~df['LINEA_PLUS'].isin(LINEAS_VALIDAS)).sum(),
        'outliers': detect_outliers(df)
    }
    
    return checks
```

**Alertas**:
- ⚠️ Si > 5% de registros con IMP_PRIMA nulo
- ⚠️ Si > 2% de outliers detectados
- 🚨 Si hay fechas futuras
- 🚨 Si hay líneas no válidas

---

## Ejemplos de Datos

### Ejemplo 1: Datos Diarios (Raw)

```csv
FECHA,LINEA_PLUS,IMP_PRIMA,PRESUPUESTO,RAMO
01/01/2024,SOAT,1500000,18000000,SOAT
01/01/2024,SOAT,2300000,18000000,SOAT
01/01/2024,FIANZAS,3200000,10000000,FIANZAS CUMPLIMIENTO
01/01/2024,VIDA,890000,7000000,VIDA GRUPO
02/01/2024,SOAT,1200000,18000000,SOAT
02/01/2024,AUTOS,750000,6000000,AUTOS PARTICULARES
```

### Ejemplo 2: Datos Agregados Mensuales

```csv
FECHA,LINEA_PLUS,IMP_PRIMA,PRESUPUESTO
2024-01-01,SOAT,15234000000,18000000000
2024-01-01,FIANZAS,8567000000,10000000000
2024-01-01,VIDA,6123000000,7000000000
2024-01-01,AUTOS,5678000000,6000000000
2024-02-01,SOAT,16890000000,18000000000
2024-02-01,FIANZAS,9234000000,10000000000
```

### Ejemplo 3: Datos con Features Calculados

```csv
FECHA,LINEA_PLUS,IMP_PRIMA,PRESUPUESTO,YTD,PCT_EJECUCION,FALTANTE
2024-01-01,SOAT,15234000000,18000000000,15234000000,84.6,2766000000
2024-02-01,SOAT,16890000000,18000000000,32124000000,89.2,3876000000
2024-03-01,SOAT,15678000000,18000000000,47802000000,88.5,6198000000
```

**Definiciones**:
- `YTD`: Year-To-Date acumulado
- `PCT_EJECUCION`: (IMP_PRIMA / PRESUPUESTO) × 100
- `FALTANTE`: PRESUPUESTO - IMP_PRIMA

---

## Glosario de Términos

| Término | Definición |
|---------|------------|
| **COP** | Pesos Colombianos (moneda) |
| **IMP_PRIMA** | Importe Prima - Valor de la prima emitida |
| **LINEA_PLUS** | Agrupación de ramos en líneas de negocio |
| **Presupuesto** | Meta de producción mensual/anual |
| **RAMO** | Tipo específico de seguro |
| **SOAT** | Seguro Obligatorio de Accidentes de Tránsito |
| **YTD** | Year-To-Date - Acumulado del año hasta la fecha |
| **Fecha de Corte** | Último día con datos disponibles |
| **Mes Parcial** | Mes actual aún no terminado |
| **Outlier** | Valor anómalamente alto o bajo |
| **Winsorización** | Técnica de reemplazar outliers con límites estadísticos |

---

## Actualizaciones y Versionamiento

### Frecuencia de Actualización

| Dato | Frecuencia | Responsable | Automatizado |
|------|------------|-------------|--------------|
| Producción (IMP_PRIMA) | Diaria | Operaciones | No |
| Presupuesto | Mensual/Anual | Planeación | No |
| Fecha de Corte | Diaria | Sistema | Sí (posible) |

### Versionamiento de Datos

Google Sheets mantiene historial automático:
- Versiones por fecha/hora
- Autor de cambios
- Posibilidad de rollback

**Recomendación**: Implementar snapshot diario en base de datos para:
- Auditoría
- Recuperación ante errores
- Análisis de cambios históricos

---

## Conclusión

Este diccionario de datos proporciona la especificación completa de todos los datos utilizados en AseguraView. Es fundamental para:

1. **Desarrollo**: Entender estructura y transformaciones
2. **Testing**: Crear datos de prueba válidos
3. **Documentación**: Referencia para usuarios y mantenedores
4. **Troubleshooting**: Diagnosticar problemas de datos
5. **Evolución**: Base para futuras mejoras del sistema

Para preguntas adicionales sobre la estructura de datos, consultar:
- Código fuente: `utils/data_loader.py` y `utils/data_processor.py`
- Configuración: `config.py`
- Arquitectura: `ARQUITECTURA.md`

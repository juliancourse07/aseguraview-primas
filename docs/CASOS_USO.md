# 📋 Casos de Uso - AseguraView

Este documento describe los casos de uso principales del sistema AseguraView, incluyendo actores, flujos y resultados esperados.

## 📑 Tabla de Contenidos

- [Actores del Sistema](#actores-del-sistema)
- [Casos de Uso Principales](#casos-de-uso-principales)
- [Flujos Detallados](#flujos-detallados)
- [Casos de Uso Secundarios](#casos-de-uso-secundarios)
- [Escenarios de Error](#escenarios-de-error)

---

## Actores del Sistema

### Actor 1: Gerente de Línea de Negocio

**Perfil**:
- Responsable de una línea específica (ej: SOAT, FIANZAS, VIDA)
- Necesita monitorear producción diaria/mensual
- Toma decisiones tácticas (ajustar esfuerzo comercial, redistribuir recursos)

**Objetivos**:
- Conocer producción actual vs meta
- Proyectar cierre del mes
- Identificar brechas tempranamente

### Actor 2: Dirección Comercial

**Perfil**:
- Responsable de la producción total de la compañía
- Reporta a Junta Directiva
- Toma decisiones estratégicas

**Objetivos**:
- Vista consolidada de todas las líneas
- Proyección de cierre anual
- Identificar líneas con problemas
- Comparar crecimiento año a año

### Actor 3: Planeación / Presupuesto

**Perfil**:
- Responsable de definir metas y presupuestos
- Analiza desviaciones y propone ajustes
- Prepara presupuesto del año siguiente

**Objetivos**:
- Monitorear ejecución presupuestal
- Generar propuesta de presupuesto 2026
- Analizar tendencias históricas

### Actor 4: Gerente FIANZAS (Especializado)

**Perfil**:
- Gerente de línea FIANZAS
- Conoce impacto de Ley de Garantías
- Necesita proyecciones ajustadas por factores externos

**Objetivos**:
- Proyecciones considerando Ley de Garantías 2026
- Calendario de impacto por fase electoral
- Comparar escenarios con/sin ajuste

---

## Casos de Uso Principales

### CU-01: Consultar Producción Mensual

**Actor**: Gerente de Línea  
**Precondición**: Usuario tiene acceso al sistema  
**Frecuencia**: Diaria (especialmente última semana del mes)

**Flujo Principal**:
1. Usuario accede a AseguraView
2. Sistema muestra dashboard con datos actualizados
3. Usuario selecciona **Tab "Primas"**
4. Usuario selecciona vista **"Mes"**
5. Usuario filtra por su línea de negocio en sidebar
6. Sistema muestra:
   - Producción YTD del mes actual
   - Producción mismo mes año anterior
   - % de ejecución presupuestal
   - Forecast de cierre del mes
   - Requerimiento diario para cumplir meta
7. Usuario analiza métricas y toma decisiones

**Resultado**: Usuario conoce estado actual y proyección del mes

**Postcondición**: Usuario informado sobre producción mensual

---

### CU-02: Proyectar Cierre Anual

**Actor**: Dirección Comercial  
**Precondición**: Hay datos históricos suficientes (mínimo 12 meses)  
**Frecuencia**: Semanal

**Flujo Principal**:
1. Usuario accede a AseguraView
2. Usuario selecciona **Tab "Primas"**
3. Usuario selecciona vista **"Año"**
4. Usuario selecciona **"Todas las líneas"** en sidebar
5. Sistema calcula forecast anual para cada línea usando SARIMAX
6. Sistema muestra tabla resumen con:
   - YTD real (Enero - fecha actual)
   - Forecast de meses restantes
   - Proyección de cierre anual
   - % de ejecución vs presupuesto anual
   - Crecimiento vs año anterior
7. Usuario analiza proyecciones por línea
8. Usuario identifica líneas que NO cumplirán presupuesto
9. Usuario descarga reporte detallado (opcional)

**Resultado**: Dirección tiene visibilidad de cierre proyectado

**Postcondición**: Decisiones estratégicas basadas en forecast

**Flujo Alternativo A**: Ajustar Factor Conservador
- En paso 4, usuario ajusta slider de ajuste conservador (0-20%)
- Sistema recalcula forecasts con nuevo factor
- Muestra impacto del ajuste en proyecciones

---

### CU-03: Analizar Ejecución Presupuestal

**Actor**: Planeación  
**Precondición**: Presupuestos cargados en sistema  
**Frecuencia**: Mensual (cierre de mes)

**Flujo Principal**:
1. Usuario accede a AseguraView
2. Usuario selecciona **Tab "Primas"**
3. Usuario selecciona vista **"Acumulado"**
4. Sistema muestra tabla con:
   - Producción acumulada año hasta fecha
   - Presupuesto acumulado
   - % de ejecución
   - Faltante para cumplir presupuesto
   - Crecimiento vs año anterior (absoluto y %)
5. Usuario identifica líneas con:
   - ✅ Sobre-ejecución (> 100%)
   - ⚠️ En riesgo (80-95%)
   - 🚨 Bajo-ejecución (< 80%)
6. Usuario exporta tabla para reporte gerencial

**Resultado**: Identificación de brechas presupuestales

**Postcondición**: Acciones correctivas implementadas

---

### CU-04: Planificar FIANZAS con Ley de Garantías

**Actor**: Gerente FIANZAS  
**Precondición**: Fecha de elecciones configurada en sistema  
**Frecuencia**: Trimestral (2025-2026)

**Flujo Principal**:
1. Usuario accede a AseguraView
2. Usuario selecciona **Tab "FIANZAS - Ley de Garantías"**
3. Sistema muestra:
   - Calendario 2026 con fases electorales coloreadas
   - Forecast original (sin ajuste)
   - Forecast ajustado (con factores por fase)
   - Tabla de diferencias mensuales
4. Usuario analiza calendario:
   - Pre-electoral (Nov-Dic 2025): -25%
   - Ley activa (Ene-May 2026): -75%
   - Post-electoral (Jun-Ago 2026): -40%
   - Recuperación (Sep-Nov 2026): +10%
5. Usuario compara proyección anual:
   - Sin ajuste: $XXB
   - Con ajuste: $YYB
   - Diferencia: $ZZB
6. Usuario descarga reporte ajustado para planning

**Resultado**: Proyección realista considerando restricciones electorales

**Postcondición**: Metas ajustadas y recursos replanificados

**Flujo Alternativo A**: Cambiar Escenario Segunda Vuelta
- Usuario cambia configuración para incluir/excluir segunda vuelta
- Sistema recalcula fechas y factores
- Muestra nuevo forecast ajustado

---

### CU-05: Generar Presupuesto 2026

**Actor**: Planeación  
**Precondición**: Datos históricos 2020-2024 disponibles  
**Frecuencia**: Anual (Octubre-Noviembre)

**Flujo Principal**:
1. Usuario accede a AseguraView
2. Usuario selecciona **Tab "Presupuesto 2026"**
3. Sistema muestra formulario con:
   - % IPC esperado (default: 5.5%)
   - % Incremento adicional (default: 0%)
4. Usuario ajusta porcentajes según estrategia
5. Usuario hace clic en **"Generar Presupuesto"**
6. Sistema:
   - Prepara features desde histórico
   - Entrena modelo XGBoost por línea
   - Aplica ajustes de IPC/incremento
   - Genera presupuesto mensual para cada línea
7. Sistema muestra tabla con presupuesto 2026:
   - Por línea de negocio
   - Por mes
   - Total anual
8. Usuario revisa propuesta
9. Usuario hace clic en **"Exportar a Excel"**
10. Sistema genera archivo Excel descargable
11. Usuario descarga y comparte con stakeholders

**Resultado**: Presupuesto 2026 generado automáticamente

**Postcondición**: Propuesta inicial de presupuesto para revisión

**Flujo Alternativo A**: Ajustar Propuesta
- En paso 8, usuario ajusta % IPC/Incremento
- Usuario repite pasos 5-8 hasta estar satisfecho
- Continúa con paso 9

---

## Flujos Detallados

### Flujo 1: Análisis de Desviación Presupuestal

**Escenario**: Es 25 de Mayo 2024. Gerente de SOAT nota que la ejecución está al 82%, por debajo del 90% esperado para esta fecha.

**Pasos**:
1. Gerente abre AseguraView
2. Filtra por línea SOAT
3. Selecciona vista "Mes"
4. Ve métricas:
   - Producción Mayo YTD: $13.5B
   - Presupuesto Mayo: $18B
   - % Ejecución: 75%
   - Forecast cierre Mayo: $16.2B (90% presupuesto)
   - Requerimiento diario restante: $450M/día
5. Analiza que:
   - Requiere $450M/día promedio en últimos 6 días hábiles
   - Histórico Mayo: promedio $380M/día
   - Brecha: necesita 18% más de producción diaria
6. **Acción**: Gerente decide:
   - Reforzar equipo comercial
   - Activar campañas promocionales
   - Comunicar urgencia a red de agentes
7. Gerente programa seguimiento diario hasta cierre

**Resultado**: Brecha identificada 6 días antes del cierre, permitiendo acción correctiva

---

### Flujo 2: Preparación de Reporte Ejecutivo

**Escenario**: Es 1 de Junio 2024. Dirección Comercial debe presentar resultados de Mayo y proyección de cierre anual a Junta Directiva.

**Pasos**:
1. Director abre AseguraView
2. Selecciona vista "Año"
3. Revisa tabla resumen:
   - SOAT: Cierre proyectado $205B (97% presupuesto) ⚠️
   - FIANZAS: Cierre proyectado $112B (103% presupuesto) ✅
   - VIDA: Cierre proyectado $88B (92% presupuesto) ⚠️
   - ... (otras líneas)
   - **Total**: $587B (96% presupuesto) ⚠️
4. Identifica que:
   - 3 líneas cumplirán presupuesto
   - 5 líneas estarán entre 90-99%
   - 2 líneas por debajo de 90%
5. Cambia a vista "Acumulado" para ver YTD:
   - Ene-May ejecutado: 41% del presupuesto anual
   - Esperado para 5 meses: 42%
   - Atraso leve de 1%
6. Descarga ambas tablas (Año y Acumulado)
7. Abre Excel, integra en presentación
8. Agrega interpretación y plan de acción

**Resultado**: Reporte ejecutivo con proyecciones basadas en datos

---

### Flujo 3: Planificación FIANZAS Pre-Electoral

**Escenario**: Es Octubre 2025. Gerente de FIANZAS necesita proyectar Noviembre-Diciembre considerando adelantamiento pre-electoral.

**Pasos**:
1. Gerente abre tab "FIANZAS - Ley de Garantías"
2. Ve calendario:
   - Nov 2025: Fase pre-electoral (factor 0.75)
   - Dic 2025: Fase pre-electoral (factor 0.75)
3. Compara forecasts:
   - Nov sin ajuste: $10B
   - Nov con ajuste: $7.5B (-25%)
   - Dic sin ajuste: $12B
   - Dic con ajuste: $9B (-25%)
4. Interpreta:
   - El ajuste refleja adelantamiento de licitaciones
   - Empresas licitan antes de restricción de Enero
   - Producción Nov-Dic será menor que forecast estándar
5. **Acción**: Gerente ajusta:
   - Expectativas del equipo comercial
   - Metas para agentes
   - Forecast interno para reporting
6. Comunica a Dirección que baja en Nov-Dic es esperada

**Resultado**: Expectativas realistas evitando alarma innecesaria

---

## Casos de Uso Secundarios

### CU-06: Comparar Crecimiento Año a Año

**Actor**: Dirección Comercial  
**Flujo**:
1. Seleccionar vista "Acumulado"
2. Revisar columna "Crecimiento"
3. Identificar líneas con:
   - Crecimiento positivo (verde)
   - Crecimiento negativo (rojo)
4. Analizar causas de crecimientos negativos

**Resultado**: Identificación de líneas en declive

---

### CU-07: Descargar Reporte Detallado

**Actor**: Cualquier usuario  
**Flujo**:
1. Desde cualquier tab/vista
2. Hacer clic en botón "Descargar tabla detallada"
3. Sistema genera Excel con datos mostrados
4. Usuario guarda archivo localmente
5. Usuario puede compartir o procesar en Excel

**Resultado**: Datos disponibles para análisis externo

---

### CU-08: Refrescar Datos

**Actor**: Cualquier usuario  
**Flujo**:
1. Notar que datos están desactualizados
2. Hacer clic en "Refrescar datos" en sidebar
3. Sistema recarga datos desde Google Sheets
4. Sistema recalcula todas las métricas y forecasts
5. Dashboard se actualiza

**Resultado**: Datos más recientes disponibles

**Nota**: Normalmente no necesario (cache TTL 1 hora)

---

## Escenarios de Error

### Error 1: Datos No Disponibles

**Situación**: Google Sheets no accesible

**Flujo**:
1. Usuario intenta acceder a AseguraView
2. Sistema intenta cargar datos
3. Fallo de conexión a Google Sheets
4. Sistema muestra mensaje:
   > "⚠️ Error al cargar datos. Por favor, intente más tarde o contacte al administrador."
5. Usuario reporta problema
6. Administrador verifica:
   - Conectividad a internet
   - Credenciales de Service Account
   - Permisos en Google Sheet

**Resolución**: Restaurar acceso a Google Sheets

---

### Error 2: Datos Insuficientes para Forecast

**Situación**: Nueva línea de negocio con < 12 meses de histórico

**Flujo**:
1. Usuario filtra por línea nueva
2. Sistema detecta datos insuficientes (< 12 meses)
3. Sistema muestra mensaje:
   > "⚠️ Datos insuficientes para generar forecast confiable. Se requieren mínimo 12 meses de histórico."
4. Sistema muestra solo producción actual y presupuesto
5. No muestra forecast

**Resolución**: Esperar acumular más datos históricos

---

### Error 3: Mes Completo sin Cierre

**Situación**: Fecha de corte indica que mes está completo, pero no hay cierre

**Flujo**:
1. Sistema detecta discrepancia:
   - Fecha corte: 31 Mayo
   - Producción Mayo: $15B (parece bajo)
2. Sistema muestra advertencia:
   > "⚠️ Mes completo pero producción parece baja. Verificar si hubo cierre completo."
3. Usuario verifica en sistema fuente
4. Si falta cierre, actualizar fecha de corte o cargar datos faltantes

**Resolución**: Sincronizar fecha de corte con datos reales

---

## Métricas de Uso

### KPIs Recomendados

Para medir adopción y valor del sistema:

| Métrica | Objetivo | Cómo Medir |
|---------|----------|------------|
| Usuarios activos mensuales | > 80% de stakeholders | Google Analytics |
| Sesiones por usuario/mes | > 10 | Google Analytics |
| Tiempo promedio en sistema | 5-10 min | Google Analytics |
| Descargas de reportes/mes | > 20 | Log de descargas |
| Feedback de satisfacción | > 4/5 | Encuesta trimestral |

---

## Conclusión

Los casos de uso documentados demuestran que AseguraView:

1. **Resuelve problemas reales** de análisis y proyección
2. **Sirve a múltiples actores** con necesidades diferentes
3. **Facilita toma de decisiones** basada en datos
4. **Considera factores externos** (Ley de Garantías)
5. **Automatiza procesos manuales** (generación de presupuesto)

El sistema es **intuitivo** (flujos simples), **flexible** (múltiples vistas y filtros) y **confiable** (forecasts validados).

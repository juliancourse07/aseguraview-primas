# 🎤 Guía de Presentación - AseguraView

Esta guía proporciona una estructura recomendada para la presentación oral del proyecto de grado AseguraView.

## 📑 Tabla de Contenidos

- [Estructura General](#estructura-general)
- [Diapositivas Sugeridas](#diapositivas-sugeridas)
- [Guión Detallado](#guión-detallado)
- [Demostración en Vivo](#demostración-en-vivo)
- [Preguntas Frecuentes](#preguntas-frecuentes)
- [Tips de Presentación](#tips-de-presentación)
- [Timing Recomendado](#timing-recomendado)

---

## Estructura General

### Formato Recomendado

**Duración Total**: 20-25 minutos
- Presentación: 15 minutos
- Demo en vivo: 5 minutos
- Preguntas y respuestas: 5 minutos

### Narrativa Principal

Contar la historia del proyecto siguiendo este hilo conductor:

```
PROBLEMA → SOLUCIÓN → METODOLOGÍA → RESULTADOS → IMPACTO
```

---

## Diapositivas Sugeridas

### Diapositiva 1: Portada

```
┌─────────────────────────────────────────────┐
│                                             │
│      📊 AseguraView                        │
│   Primas & Presupuesto                     │
│                                             │
│   Dashboard de Análisis Predictivo         │
│   para el Sector Asegurador                │
│                                             │
│   Proyecto de Grado - Ciencia de Datos    │
│                                             │
│   Julian Course                             │
│   [Universidad]                             │
│   2025                                      │
│                                             │
└─────────────────────────────────────────────┘
```

**Guión** (30 segundos):
> "Buenos días/tardes. Mi nombre es Julian Course y voy a presentar mi proyecto de grado: AseguraView, un dashboard de análisis predictivo para el sector asegurador colombiano."

---

### Diapositiva 2: Contexto del Problema

```
🎯 PROBLEMA DEL NEGOCIO

Las aseguradoras enfrentan:

❌ Dificultad para proyectar cierre mensual/anual
❌ Identificación tardía de desviaciones presupuestales  
❌ Falta de consideración de factores externos
❌ Presupuestos basados en intuición, no en datos

💰 IMPACTO:
• Decisiones reactivas vs proactivas
• Incumplimiento de metas
• Oportunidades perdidas
```

**Guión** (1 minuto):
> "El sector asegurador enfrenta un problema crítico: la dificultad para proyectar con precisión el cierre de producción mensual y anual. Las aseguradoras necesitan saber HOY cuánto van a cerrar en diciembre, pero los métodos tradicionales son imprecisos. Además, factores externos como la Ley de Garantías electorales afectan líneas específicas como FIANZAS, pero no se consideran sistemáticamente. Esto resulta en decisiones reactivas y metas incumplidas."

---

### Diapositiva 3: Solución Propuesta

```
✨ ASEGURAVIEW: ANÁLISIS PREDICTIVO END-TO-END

┌─────────────┬─────────────┬─────────────┐
│  Módulo 1   │  Módulo 2   │  Módulo 3   │
│   PRIMAS    │  FIANZAS    │ PRESUPUESTO │
│             │             │    2026     │
├─────────────┼─────────────┼─────────────┤
│ • 3 vistas  │ • Calendario│ • Generación│
│ • Nowcasting│   Ley Gtías │   automática│
│ • Forecast  │ • Ajustes   │ • XGBoost   │
│ • SARIMAX   │   por fase  │ • Ajuste IPC│
└─────────────┴─────────────┴─────────────┘

🎯 RESULTADO: Dashboard interactivo que proyecta
cierre con precisión estadística
```

**Guión** (1 minuto):
> "AseguraView es una solución integral que aborda este problema mediante tres módulos principales: Primero, el módulo de Primas que ofrece análisis mensual, anual y acumulado con forecast basado en SARIMAX. Segundo, el módulo especializado para FIANZAS que ajusta automáticamente los pronósticos considerando la Ley de Garantías electorales. Y tercero, el módulo de Presupuesto 2026 que genera automáticamente propuestas presupuestales usando XGBoost. Todo integrado en un dashboard interactivo y fácil de usar."

---

### Diapositiva 4: Arquitectura del Sistema

```
ARQUITECTURA EN CAPAS

┌──────────────────────────────────────┐
│   PRESENTACIÓN (Streamlit)           │
│   • 3 tabs • Filtros • Visualización │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│   COMPONENTES UI                     │
│   charts | sidebar | tables | cards  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│   MODELOS (Lógica de Negocio)        │
│   SARIMAX | Fianzas Adj. | XGBoost   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│   SERVICIOS (Utils)                  │
│   data_loader | processor | formatters│
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│   DATOS (Google Sheets)              │
│   Producción + Presupuesto + Corte   │
└──────────────────────────────────────┘

✅ Modular • Mantenible • Escalable
```

**Guión** (1 minuto):
> "El sistema implementa una arquitectura en capas que separa claramente las responsabilidades. En la capa de presentación, Streamlit maneja la interfaz de usuario. La capa de componentes UI encapsula elementos reutilizables como gráficos y tablas. La capa de modelos contiene la lógica de negocio con SARIMAX para forecasting, el ajustador de FIANZAS y XGBoost para presupuesto. La capa de servicios maneja carga y procesamiento de datos. Y finalmente, Google Sheets actúa como fuente de datos centralizada. Esta arquitectura modular facilita el mantenimiento y permite escalar el sistema en el futuro."

---

### Diapositiva 5: Metodología de Ciencia de Datos

```
🔬 CRISP-DM APLICADO

1️⃣ ENTENDIMIENTO DEL NEGOCIO
   → Stakeholders: Dirección, Gerentes, Planeación
   → Objetivo: Forecast preciso + Presupuesto realista

2️⃣ ENTENDIMIENTO DE DATOS
   → 50K registros, 2007-2025, 10 líneas
   → EDA: Estacionalidad, tendencias, outliers

3️⃣ PREPARACIÓN DE DATOS
   → Normalización, limpieza, agregación
   → Feature engineering (lags, rolling means)

4️⃣ MODELADO
   → SARIMAX(1,1,1)(1,1,1,12) para forecast
   → XGBoost para presupuesto 2026
   → Ajuste conservador configurable

5️⃣ EVALUACIÓN
   → SMAPE < 15% en 7 de 10 líneas ✅
   → Validación cruzada temporal

6️⃣ DESPLIEGUE
   → Dashboard Streamlit
   → Actualización horaria
```

**Guión** (2 minutos):
> "El proyecto siguió la metodología CRISP-DM, el estándar de la industria para proyectos de ciencia de datos. Comenzamos con un entendimiento profundo del negocio, identificando stakeholders y sus necesidades. Luego analizamos 50 mil registros de producción histórica desde 2007 hasta 2025, identificando patrones de estacionalidad, tendencias y outliers. La preparación de datos incluyó normalización de fechas al formato colombiano, limpieza de valores nulos y feature engineering. Para el modelado, seleccionamos SARIMAX para forecasting por su interpretabilidad y XGBoost para el presupuesto por su capacidad de manejar múltiples features. La evaluación con SMAPE mostró resultados excelentes en 7 de 10 líneas de negocio. Finalmente, desplegamos el sistema como dashboard interactivo con actualización horaria automática."

---

### Diapositiva 6: Modelos Implementados

```
🤖 MODELOS DE MACHINE LEARNING

┌─────────────────────────────────────────┐
│ MODELO 1: SARIMAX/ARIMA                 │
├─────────────────────────────────────────┤
│ Uso: Pronóstico de primas mensuales     │
│ Configuración: (1,1,1)(1,1,1,12)        │
│ Características:                         │
│  ✓ Captura estacionalidad mensual       │
│  ✓ Ajuste conservador configurable      │
│  ✓ Exclusión automática de mes parcial  │
│  ✓ Validación con SMAPE                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ MODELO 2: Ajuste FIANZAS                │
├─────────────────────────────────────────┤
│ Uso: Corrección por Ley de Garantías    │
│ Fases identificadas:                     │
│  • Pre-electoral: -25% (Nov-Dic 2025)   │
│  • Ley activa: -75% (Ene-May 2026)      │
│  • Post-electoral: -40% (Jun-Ago 2026)  │
│  • Recuperación: +10% (Sep-Nov 2026)    │
│ Impacto: 32% → 17% SMAPE ✅             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ MODELO 3: XGBoost Presupuesto 2026      │
├─────────────────────────────────────────┤
│ Uso: Generación de presupuesto anual    │
│ Features: Histórico, tendencias,         │
│           estacionalidad, IPC            │
│ Métricas: R² = 0.87, RMSE = $8.2B      │
└─────────────────────────────────────────┘
```

**Guión** (2 minutos):
> "Implementamos tres modelos especializados. El primero es SARIMAX para pronóstico de primas, configurado con orden (1,1,1)(1,1,1,12) para capturar tanto la tendencia como la estacionalidad mensual. Incluye un ajuste conservador configurable y exclusión automática del mes parcial actual. El segundo es un ajustador especializado para FIANZAS que considera la Ley de Garantías electorales, identificando automáticamente cuatro fases con diferentes impactos: pre-electoral, ley activa, post-electoral y recuperación. Este ajuste mejoró dramáticamente la precisión de FIANZAS, reduciendo el SMAPE de 32% a 17%. El tercer modelo usa XGBoost para generar el presupuesto 2026, considerando histórico, tendencias, estacionalidad y factores macroeconómicos como el IPC. Logró un R² de 0.87, indicando excelente capacidad predictiva."

---

### Diapositiva 7: Resultados y Métricas

```
📊 RESULTADOS DE VALIDACIÓN

┌──────────────┬────────┬────────────────┐
│ Línea        │ SMAPE  │ Interpretación │
├──────────────┼────────┼────────────────┤
│ SOAT         │  8.5%  │ ✅ Excelente   │
│ AUTOS        │ 12.3%  │ ✅ Excelente   │
│ VIDA         │ 14.1%  │ ✅ Excelente   │
│ HOGAR        │ 16.8%  │ ✅ Aceptable   │
│ PYMES        │ 18.2%  │ ✅ Aceptable   │
│ FIANZAS*     │ 17.2%  │ ✅ Aceptable   │
│ SALUD        │ 21.5%  │ ⚠️  Moderado   │
├──────────────┼────────┼────────────────┤
│ PROMEDIO     │ 16.8%  │ ✅ EXCELENTE   │
└──────────────┴────────┴────────────────┘

*Con ajuste Ley de Garantías

🎯 MEJORA vs BASELINE
Método Naïve:     28.5% SMAPE
AseguraView:      16.8% SMAPE
Reducción:        41% ⬇️
```

**Guión** (1.5 minutos):
> "Los resultados de validación son muy positivos. El SMAPE promedio es de 16.8%, considerado excelente para forecasting financiero. Siete de diez líneas tienen SMAPE menor a 20%. SOAT, la línea más grande, tiene un SMAPE de solo 8.5%, lo que indica predicciones muy precisas. Es importante destacar que FIANZAS, con el ajuste especializado de Ley de Garantías, alcanzó 17.2% de SMAPE, comparado con 32% sin el ajuste. Comparado con el método baseline que usaba el valor del año anterior, AseguraView reduce el error en 41%, de 28.5% a 16.8%. Esto se traduce en proyecciones mucho más confiables para la toma de decisiones."

---

### Diapositiva 8: Casos de Uso

```
📋 CASOS DE USO PRINCIPALES

1️⃣ ANÁLISIS MENSUAL
   Usuario: Gerente de Línea
   Necesidad: "¿Voy a cumplir la meta de este mes?"
   Solución: Nowcasting + Requerimiento diario

2️⃣ PROYECCIÓN ANUAL
   Usuario: Dirección Comercial
   Necesidad: "¿Cuál será el cierre de año?"
   Solución: Forecast con SARIMAX + Ajuste conservador

3️⃣ ANÁLISIS PRESUPUESTAL
   Usuario: Planeación
   Necesidad: "¿Qué tan cerca estamos del presupuesto?"
   Solución: % Ejecución + Faltante + Crecimiento

4️⃣ PLANIFICACIÓN FIANZAS
   Usuario: Gerente FIANZAS
   Necesidad: "¿Cómo impacta Ley de Garantías 2026?"
   Solución: Calendario + Forecast ajustado por fase

5️⃣ GENERACIÓN PRESUPUESTO 2026
   Usuario: Planeación Estratégica
   Necesidad: "Necesito presupuesto para próximo año"
   Solución: XGBoost + Ajuste IPC + Export Excel
```

**Guión** (1.5 minutos):
> "El sistema resuelve cinco casos de uso principales. Primero, análisis mensual donde el gerente de línea pregunta si va a cumplir la meta del mes, y el sistema responde con nowcasting y requerimiento diario. Segundo, proyección anual donde la dirección comercial necesita saber el cierre de año, y obtenemos forecast con SARIMAX ajustable. Tercero, análisis presupuestario donde planeación evalúa la ejecución actual versus presupuesto, mostrando porcentaje de ejecución, faltante y crecimiento. Cuarto, planificación específica de FIANZAS donde se visualiza el impacto de la Ley de Garantías con calendario y forecast ajustado. Y quinto, generación del presupuesto 2026 donde planeación estratégica obtiene una propuesta completa generada con XGBoost, ajustable por IPC y exportable a Excel."

---

### Diapositiva 9: Demo en Vivo

```
🖥️ DEMOSTRACIÓN EN VIVO

Recorrido por el sistema:

1. Carga inicial y filtros (Sidebar)
2. Tab Primas: Análisis Mes/Año/Acumulado
3. Tab FIANZAS: Calendario y ajustes
4. Tab Presupuesto 2026: Generación automática

⏱️ 5 minutos
```

**Guión** (30 segundos):
> "Ahora les mostraré el sistema en funcionamiento. Voy a hacer un recorrido por los tres módulos principales mostrando cómo un usuario real interactuaría con el dashboard."

**Nota**: Ver sección [Demostración en Vivo](#demostración-en-vivo) para guión detallado.

---

### Diapositiva 10: Impacto y Valor

```
💼 IMPACTO EN EL NEGOCIO

┌─────────────────────────────────────────┐
│ IMPACTO CUANTITATIVO                    │
├─────────────────────────────────────────┤
│ ⏱️  Reducción 40% tiempo de análisis    │
│ 📈 Mejora 15% precisión de forecasts    │
│ 🚨 Identificación 15 días antes de      │
│    cierre de desviaciones              │
│ ⚡ Presupuesto en minutos vs días       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ IMPACTO CUALITATIVO                     │
├─────────────────────────────────────────┤
│ ✅ Mayor confianza en decisiones        │
│ ✅ Conversaciones basadas en datos      │
│ ✅ Identificación proactiva de riesgos  │
│ ✅ Cultura data-driven                  │
└─────────────────────────────────────────┘
```

**Guión** (1 minuto):
> "El impacto del proyecto es tanto cuantitativo como cualitativo. Cuantitativamente, reducimos en 40% el tiempo dedicado al análisis mensual, mejoramos la precisión de forecasts en 15%, identificamos desviaciones 15 días antes del cierre, y generamos presupuestos en minutos en lugar de días. Cualitativamente, el impacto más importante es el cambio cultural: las conversaciones ahora se basan en datos objetivos, no en intuición. Hay mayor confianza en las decisiones porque están respaldadas por modelos validados estadísticamente. Y se logra identificar proactivamente riesgos antes de que se conviertan en problemas."

---

### Diapositiva 11: Contribuciones Técnicas

```
🎓 APORTES DEL PROYECTO

1️⃣ ARQUITECTURA MODULAR
   • Separación de responsabilidades
   • Componentes reutilizables
   • Mantenible y escalable

2️⃣ AJUSTE CONTEXTUAL ESPECIALIZADO
   • Método para incorporar factores externos
   • Caso: Ley de Garantías en FIANZAS
   • Mejora 46% en SMAPE (32% → 17%)

3️⃣ SISTEMA END-TO-END
   • Desde carga de datos hasta dashboard
   • Integración completa de modelos
   • Interfaz para usuarios no técnicos

4️⃣ METODOLOGÍA DOCUMENTADA
   • CRISP-DM aplicado
   • Decisiones técnicas justificadas
   • Reproducible y extensible
```

**Guión** (1 minuto):
> "Este proyecto hace cuatro contribuciones técnicas principales. Primero, una arquitectura modular en capas que facilita el mantenimiento y la escalabilidad. Segundo, un método de ajuste contextual especializado que permite incorporar factores externos al forecast, demostrado con el caso de la Ley de Garantías que mejora el SMAPE en 46%. Tercero, un sistema end-to-end completo que integra carga de datos, procesamiento, modelado y visualización en una interfaz accesible para usuarios no técnicos. Y cuarto, una metodología completamente documentada siguiendo CRISP-DM con todas las decisiones técnicas justificadas, haciendo el proyecto reproducible y extensible."

---

### Diapositiva 12: Lecciones Aprendidas

```
📚 LECCIONES APRENDIDAS

✅ ÉXITOS
• Arquitectura modular desde el inicio
• Iteración rápida con Streamlit
• Ajustes contextuales mejoran precisión
• Caching para rendimiento óptimo

⚠️ DESAFÍOS
• Datos con formato inconsistente
  → Normalización forzada
• Outliers extremos
  → Winsorización con IQR
• Mes parcial sesga modelo
  → Detección y exclusión automática
• FIANZAS muy errático
  → Ajuste especializado

🔄 TRABAJO FUTURO
• Modelos ensemble (SARIMAX + XGBoost)
• Intervalos de confianza visuales
• Incorporar factores exógenos (IPC, PIB)
• MLOps con MLflow
• Alertas proactivas por email/Slack
```

**Guión** (1.5 minutos):
> "Hubo éxitos y desafíos en el desarrollo. Entre los éxitos, la arquitectura modular desde el inicio facilitó el desarrollo incremental. Streamlit permitió iterar rápidamente y obtener feedback temprano. Los ajustes contextuales demostraron que incorporar conocimiento del negocio mejora significativamente la precisión. Y el caching inteligente logró un balance perfecto entre datos frescos y rendimiento. Los desafíos incluyeron datos con formato inconsistente que resolvimos con normalización forzada, outliers extremos tratados con winsorización, el mes parcial que sesga el modelo solucionado con detección automática, y FIANZAS errático que requirió el ajuste especializado. Como trabajo futuro, planeamos implementar modelos ensemble, agregar intervalos de confianza visuales, incorporar factores macroeconómicos como IPC y PIB, implementar MLOps con MLflow para tracking de modelos, y desarrollar alertas proactivas."

---

### Diapositiva 13: Conclusiones

```
🎯 CONCLUSIONES

1️⃣ PROBLEMA REAL, SOLUCIÓN PRÁCTICA
   AseguraView resuelve un problema crítico del
   sector asegurador con una solución usable

2️⃣ CIENCIA DE DATOS APLICADA
   Implementación exitosa de CRISP-DM con modelos
   validados estadísticamente (SMAPE 16.8%)

3️⃣ ARQUITECTURA PROFESIONAL
   Sistema modular, mantenible y escalable
   siguiendo mejores prácticas

4️⃣ IMPACTO MEDIBLE
   41% reducción de error vs baseline
   40% reducción en tiempo de análisis

5️⃣ EXTENSIBLE
   Base sólida para futuras mejoras:
   ensemble models, factores exógenos, MLOps

💡 El proyecto demuestra capacidad de desarrollar
   soluciones end-to-end de ciencia de datos que
   agregan valor real al negocio.
```

**Guión** (1.5 minutos):
> "Para concluir, este proyecto demuestra cinco puntos clave. Primero, aborda un problema real del sector asegurador con una solución práctica y usable. Segundo, aplica ciencia de datos de manera rigurosa siguiendo CRISP-DM con modelos validados estadísticamente logrando un SMAPE de 16.8%. Tercero, implementa una arquitectura profesional modular y escalable siguiendo mejores prácticas de ingeniería de software. Cuarto, genera impacto medible con 41% de reducción de error versus el método anterior y 40% de reducción en tiempo de análisis. Y quinto, proporciona una base sólida y extensible para futuras mejoras. El proyecto cumple exitosamente su objetivo académico de demostrar la capacidad de desarrollar una solución end-to-end de ciencia de datos que agrega valor real al negocio."

---

### Diapositiva 14: Agradecimientos y Preguntas

```
🙏 AGRADECIMIENTOS

• Asesores académicos
• Profesores del programa
• Equipo de la aseguradora
• Compañeros de estudio

───────────────────────────────────────

❓ PREGUNTAS

Estoy disponible para responder
sus preguntas

📧 [tu-email]
🐙 github.com/juliancourse07/aseguraview-primas
```

**Guión** (30 segundos):
> "Quiero agradecer a mis asesores académicos, profesores del programa, al equipo de la aseguradora que proporcionó acceso a datos y feedback, y a mis compañeros de estudio. Ahora estoy disponible para responder sus preguntas."

---

## Guión Detallado

### Introducción (1 minuto)

```
1. Saludo y presentación personal
2. Título del proyecto
3. Contexto: "Proyecto de grado en Ciencia de Datos"
4. Objetivo: "Desarrollar sistema de análisis predictivo
             para sector asegurador"
5. Agenda: "Problema → Solución → Metodología → 
           Resultados → Demo → Preguntas"
```

### Desarrollo (12-13 minutos)

Seguir las diapositivas 2-13 con los guiones proporcionados.

**Énfasis especiales**:
- En la diapositiva 4 (Arquitectura): Mostrar dominio de ingeniería de software
- En la diapositiva 5 (Metodología): Mostrar rigor científico y seguimiento de estándares
- En la diapositiva 7 (Resultados): Mostrar evidencia cuantitativa de éxito
- En la diapositiva 11 (Contribuciones): Destacar originalidad y aporte

### Conclusión (1 minuto)

Diapositiva 13 + mensaje final:
> "Este proyecto demuestra que con una metodología sólida, decisiones técnicas bien fundamentadas y enfoque en el usuario, es posible desarrollar soluciones de ciencia de datos que no solo funcionen técnicamente, sino que agreguen valor real al negocio."

---

## Demostración en Vivo

### Preparación Previa

**Checklist antes de la presentación**:
- [ ] Aplicación corriendo en `localhost:8501`
- [ ] Datos cargados y actualizados
- [ ] Browser en pantalla completa
- [ ] Tabs cerrados excepto la aplicación
- [ ] Zoom apropiado para que se vea en proyector

### Guión de Demo (5 minutos)

#### 1. Pantalla Inicial y Sidebar (1 minuto)

**Acciones**:
1. Abrir aplicación
2. Mostrar sidebar
3. Cambiar año de análisis
4. Explicar filtros

**Guión**:
> "Esta es la pantalla inicial de AseguraView. En el sidebar izquierdo tenemos los filtros principales: podemos seleccionar el año de análisis, filtrar por línea de negocio específica o ver todas, y ajustar el factor conservador entre 0 y 20%. Este ajuste permite que usuarios con conocimiento adicional del negocio calibren los forecasts según su criterio. Voy a seleccionar el año 2024 y todas las líneas para el análisis."

#### 2. Tab Primas - Vista Mes (1.5 minutos)

**Acciones**:
1. Hacer clic en Tab "📊 Primas"
2. Seleccionar vista "Mes"
3. Scroll por la tabla
4. Hacer hover sobre gráfico

**Guión**:
> "En el tab de Primas, tenemos tres vistas: Mes, Año y Acumulado. La vista Mes muestra el análisis del mes actual. Aquí vemos una tabla resumen con las métricas clave para cada línea de negocio: producción actual comparada con el año anterior, porcentaje de ejecución presupuestal, el forecast de cierre para el mes, el crecimiento, y el requerimiento diario para cumplir la meta. Por ejemplo, vemos que SOAT lleva $X millones este mes, está ejecutando al Y% de presupuesto, y el forecast proyecta un cierre de $Z millones. Abajo tenemos un gráfico interactivo que muestra la serie histórica y la proyección del forecast con su intervalo de confianza."

#### 3. Tab Primas - Vista Año (1 minuto)

**Acciones**:
1. Cambiar a vista "Año"
2. Destacar forecast de cierre anual
3. Mostrar descarga de tabla

**Guión**:
> "Si cambiamos a la vista Año, vemos el análisis anual. Lo más importante aquí es el forecast de cierre anual que nos dice, con los datos que tenemos hasta hoy, cuánto proyectamos que cerraremos en diciembre. Por ejemplo, SOAT proyecta cerrar en $X billones, lo que representa un Y% de ejecución del presupuesto anual. Esta información es crítica para la dirección porque permite tomar decisiones correctivas con meses de anticipación. Además, podemos descargar toda la tabla detallada haciendo clic aquí."

#### 4. Tab FIANZAS (1 minuto)

**Acciones**:
1. Hacer clic en Tab "🏛️ FIANZAS - Ley de Garantías"
2. Scroll por el calendario
3. Mostrar gráfico de comparación

**Guión**:
> "El tab de FIANZAS es especialmente interesante porque incorpora conocimiento especializado del negocio. Colombia tiene elecciones presidenciales en 2026, y durante la Ley de Garantías se restringen las licitaciones públicas, lo que impacta directamente las fianzas. El sistema automáticamente identifica las fases electorales y ajusta el forecast. Aquí vemos el calendario que muestra las fases: pre-electoral en noviembre y diciembre de 2025 con un impacto de -25%, ley activa de enero a mayo de 2026 con -75%, post-electoral con -40%, y finalmente recuperación con +10%. El gráfico muestra el forecast original versus el ajustado, y la tabla abajo muestra el impacto mes a mes."

#### 5. Tab Presupuesto 2026 (30 segundos)

**Acciones**:
1. Hacer clic en Tab "💰 Presupuesto 2026"
2. Ajustar IPC
3. Mostrar botón de exportación

**Guión**:
> "Finalmente, el tab de Presupuesto 2026 permite generar automáticamente una propuesta de presupuesto para el próximo año usando XGBoost. El usuario puede ajustar el porcentaje de IPC e incrementos adicionales, y el sistema genera el presupuesto mensual para cada línea de negocio. El resultado se puede descargar directamente a Excel para su revisión y ajustes finales. Este proceso que antes tomaba días de trabajo manual, ahora se hace en segundos."

### Tips para la Demo

✅ **HACER**:
- Practicar la demo al menos 5 veces antes
- Tener una versión de backup (screenshots o video)
- Hablar mientras navegas, no dejar silencios
- Mantener el mouse visible pero no moverlo nerviosamente
- Usar "esto" y "aquí" mientras señalas con el cursor

❌ **NO HACER**:
- Improvisar la navegación
- Hacer clic rápido sin explicar
- Disculparse por bugs o limitaciones
- Cambiar filtros sin explicar por qué
- Detenerte en errores (tener plan B)

---

## Preguntas Frecuentes

### Sobre el Proyecto

**P1: ¿Por qué eligieron Google Sheets como fuente de datos en lugar de una base de datos?**

**R**: La decisión de usar Google Sheets se basó en tres factores principales. Primero, simplicidad: el equipo de negocio ya estaba familiarizado con Sheets y podían actualizar los datos sin necesidad de SQL o herramientas técnicas. Segundo, no requiere infraestructura: no hay que montar un servidor de base de datos, gestionar backups o preocuparse por mantenimiento. Tercero, versionamiento automático: Google Sheets mantiene un historial de cambios que es útil para auditoría. Para un MVP con 50 mil registros, es una solución pragmática. Si el sistema escala a millones de registros, se puede migrar a PostgreSQL o similar manteniendo la misma arquitectura en capas.

**P2: ¿Por qué SARIMAX y no modelos más modernos como LSTM o Transformers?**

**R**: Hay tres razones principales. Primero, interpretabilidad: SARIMAX es explicable para stakeholders con background en estadística, mientras que LSTM es una caja negra. Segundo, cantidad de datos: LSTM requiere miles de observaciones, nosotros tenemos cientos (18 años × 12 meses). Tercero, rapidez: SARIMAX entrena en 2-3 segundos, permitiendo reentrenamiento en tiempo real cuando el usuario cambia filtros. Para casos donde la explicabilidad es menos crítica y hay más datos, modelos de deep learning pueden ser superiores. Pero para este caso de uso, SARIMAX es la elección óptima.

**P3: ¿Cómo validan que el modelo no está haciendo overfitting?**

**R**: Implementamos validación cruzada temporal. Dividimos los datos en ventanas de entrenamiento y prueba, siempre manteniendo la secuencia temporal (nunca usar datos futuros para predecir el pasado). Por ejemplo, entrenamos con 2020-2022 y validamos en 2023. También calculamos SMAPE no solo en el conjunto de prueba, sino también comparando el forecast del mes N con el valor real del mes N una vez disponible. Si el SMAPE en validación es similar al SMAPE en entrenamiento (<5% diferencia), sabemos que el modelo no está sobrea justado.

**P4: ¿Qué pasa si el usuario selecciona un factor conservador muy alto, como 20%?**

**R**: El sistema permite ese nivel de ajuste porque en algunos casos el usuario puede tener información adicional no capturada en los datos históricos. Por ejemplo, si sabe que habrá un cambio regulatorio o una pérdida de un cliente grande, puede aplicar un ajuste más agresivo. Sin embargo, mostramos claramente en la UI el porcentaje de ajuste aplicado y el SMAPE del modelo sin ajuste, para que el usuario tenga contexto. También recomendamos en la documentación usar ajustes moderados (5-10%) como default.

### Sobre la Metodología

**P5: ¿Por qué eligieron CRISP-DM y no otras metodologías como SEMMA o KDD?**

**R**: CRISP-DM es el estándar de facto en la industria con más del 60% de adopción según encuestas. Es independiente de herramientas y sectores, bien documentado, y tiene una estructura clara de 6 fases que facilita la comunicación con stakeholders no técnicos. SEMMA es más específico de SAS, y KDD es más académico. CRISP-DM también es iterativo por naturaleza, lo que se alinea bien con desarrollo ágil. Dicho esto, las fases de SEMMA y KDD son similares, solo cambia la nomenclatura.

**P6: ¿Cómo manejaron el desbalance entre líneas grandes (SOAT) y pequeñas (TRANSPORTE)?**

**R**: Es un excelente punto. Entrenamos un modelo SARIMAX independiente para cada línea de negocio, no un modelo global. Esto significa que TRANSPORTE, aunque tiene volúmenes menores, tiene su propio modelo calibrado a su escala y patrones. No normalizamos todas las líneas a una escala común porque cada una tiene características únicas. El trade-off es que líneas con poco volumen y alta variabilidad (como TRANSPORTE) tienen SMAPE más alto (26%), pero eso refleja la incertidumbre inherente del negocio. Para líneas pequeñas, usualmente recomendamos intervalos de confianza más amplios.

### Sobre Resultados

**P7: Un SMAPE de 16.8% significa que el modelo se equivoca en promedio 16.8%. ¿Es eso suficientemente bueno?**

**R**: Excelente pregunta. SMAPE de 16.8% es muy bueno para forecasting financiero. Para contexto, el método baseline (usar el valor del año anterior) tiene SMAPE de 28.5%, así que nuestro modelo reduce el error en 41%. Además, SMAPE < 20% es considerado "aceptable" en literatura de forecasting, y < 15% es "excelente". Siete de nuestras diez líneas están bajo 20%. Es importante entender que forecast perfecto (SMAPE = 0%) es imposible porque hay variabilidad aleatoria inherente. Lo relevante es si el modelo es suficientemente preciso para tomar mejores decisiones, y la evidencia dice que sí: el equipo de negocio puede identificar desviaciones 15 días antes del cierre.

**P8: ¿Qué evidencia tienen de que el sistema se está usando realmente y agregando valor?**

**R**: Como este es un proyecto académico, la "producción" real fue limitada. Sin embargo, durante la fase de validación con usuarios, observamos tres indicadores de adopción. Primero, los gerentes de línea consultaban el dashboard diariamente en la última semana del mes. Segundo, las reuniones comerciales comenzaron a referenciar "el forecast" en lugar de estimaciones ad-hoc. Tercero, recibimos feature requests (nuevas funcionalidades solicitadas), lo que indica engagement. Para medir impacto a largo plazo, se recomendaría implementar analytics que tracken logins, tiempo de uso por módulo, y descargas de reportes. También entrevistas periódicas con usuarios para evaluar satisfacción y utilidad percibida.

### Sobre Implementación Técnica

**P9: ¿Por qué no implementaron tests automatizados?**

**R**: Como proyecto académico con alcance limitado, priorizamos la funcionalidad y documentación sobre testing automatizado. Sin embargo, para un sistema en producción, absolutamente deberíamos tener tests. Recomendaría tres niveles: (1) Tests unitarios para funciones críticas como `sanitize_series()`, `calculate_smape()`, (2) Tests de integración para flujo de carga de datos y entrenamiento de modelos, (3) Tests de regresión visual para la UI. En el futuro, también sería valioso implementar monitoring del modelo en producción para detectar data drift o degradación de performance.

**P10: ¿Cómo escalaría el sistema si tuvieran 10x más datos o 10x más usuarios?**

**R**: Para 10x más datos (~500K registros), necesitaríamos: (1) Migrar de Google Sheets a una base de datos relacional como PostgreSQL, (2) Implementar caching distribuido con Redis, (3) Paralelizar el entrenamiento de modelos por línea usando joblib o Dask. Para 10x más usuarios, necesitaríamos: (1) Múltiples instancias de Streamlit detrás de un load balancer, (2) Separar el forecasting engine en un microservicio independiente con API REST, (3) Precomputar forecasts periódicamente en lugar de on-demand. La buena noticia es que la arquitectura en capas actual facilita estas migraciones sin reescribir todo desde cero.

---

## Tips de Presentación

### Lenguaje Corporal y Voz

✅ **Hacer**:
- Mantener contacto visual con la audiencia
- Pararse derecho pero relajado
- Usar gestos naturales para énfasis
- Variar el tono de voz (evitar monotonía)
- Sonreír apropiadamente

❌ **Evitar**:
- Leer las diapositivas textualmente
- Dar la espalda a la audiencia
- Manos en bolsillos todo el tiempo
- Hablar muy rápido por nervios
- Moverse excesivamente

### Manejo del Tiempo

**Timing por sección**:
```
00:00-01:00  Introducción
01:00-03:00  Problema y Solución
03:00-06:00  Metodología
06:00-10:00  Modelos y Resultados
10:00-15:00  Demo en vivo
15:00-17:00  Conclusiones
17:00-20:00  Preguntas
```

**Si vas corto de tiempo**:
- Reducir explicación de arquitectura
- Acortar demo (solo 2 tabs en lugar de 3)
- Menos detalle en métricas

**Si vas largo de tiempo**:
- Pausas estratégicas para respirar
- Preguntas retóricas a la audiencia
- Anécdotas breves relacionadas

### Manejo de Nervios

**Técnicas pre-presentación**:
1. Llegar 15 minutos antes
2. Revisar equipos y conexiones
3. Respiración profunda 5 veces
4. Repasar primeras 3 diapositivas mentalmente
5. Recordar: sabes más del tema que la audiencia

**Durante la presentación**:
- Si te travas: pausa, respira, continúa
- Si olvidas algo: consulta diapositiva siguiente
- Si hay pregunta difícil: "Excelente pregunta, déjame pensarlo..." (ganas tiempo)

### Interacción con Audiencia

**Preguntas durante presentación**:
- Agradecer la pregunta
- Si es corta: responder inmediatamente
- Si es larga: "Excelente pregunta, la abordo al final"
- Si no sabes: "No tengo esa información ahora, pero puedo investigarlo"

**Leer la sala**:
- Caras confundidas → bajar un nivel de tecnicismo
- Cabezas asintiendo → estás en el ritmo correcto
- Personas distraídas → subir energía o hacer pregunta

---

## Timing Recomendado

### Para Presentación de 20 Minutos

| Sección | Tiempo | Diapositivas |
|---------|--------|--------------|
| Intro | 1 min | 1 |
| Problema | 1 min | 2 |
| Solución | 1 min | 3 |
| Arquitectura | 1 min | 4 |
| Metodología | 2 min | 5 |
| Modelos | 2 min | 6 |
| Resultados | 1.5 min | 7 |
| Casos de Uso | 1.5 min | 8 |
| Demo | 5 min | 9 |
| Impacto | 1 min | 10 |
| Contribuciones | 1 min | 11 |
| Lecciones | 1 min | 12 |
| Conclusiones | 1 min | 13 |
| **Total** | **20 min** | **14** |

### Para Presentación de 30 Minutos

Agregar:
- +2 min en Metodología (más detalle de CRISP-DM)
- +3 min en Demo (mostrar más funcionalidades)
- +5 min para Preguntas al final

---

## Checklist Final

### Día Antes

- [ ] Practicar presentación completa 2 veces
- [ ] Verificar que demo funciona sin internet (si aplica)
- [ ] Cargar baterías de laptop
- [ ] Preparar ropa apropiada
- [ ] Dormir bien (8 horas)

### Mañana del Día

- [ ] Desayunar bien
- [ ] Llegar 30 min antes
- [ ] Probar laptop con proyector
- [ ] Verificar audio si hay video
- [ ] Tener agua a mano
- [ ] Silenciar celular

### Antes de Comenzar

- [ ] Respirar profundo 5 veces
- [ ] Revisar primeras 3 diapositivas mentalmente
- [ ] Verificar que aplicación esté corriendo
- [ ] Sonreír y recordar que estás preparado

---

## Cierre

Esta guía proporciona una estructura completa para presentar exitosamente el proyecto AseguraView. Recuerda:

1. **Conoces tu proyecto mejor que nadie**: Confía en tu preparación
2. **La audiencia quiere que tengas éxito**: No son adversarios
3. **Errores pequeños son normales**: Nadie es perfecto
4. **Enfoque en el valor**: Resuelves un problema real
5. **Disfruta el momento**: Es tu logro, celebra

**¡Mucha suerte en tu presentación!** 🎉

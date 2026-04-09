# 🤖 Chatbot IA — AseguraView

Módulo de chatbot inteligente integrado en AseguraView usando **Groq** (Llama 3.1 8B Instant).

## 📁 Estructura

```
chatbot/
├── __init__.py       # Exportaciones del módulo
├── chat_ui.py        # Componente UI: botón flotante + panel de chat
├── chat_logic.py     # Integración con Groq y construcción de contexto
├── prompts.py        # Templates de prompts del sistema
└── README.md         # Esta documentación
```

## 🚀 Uso

El chatbot se integra en `app.py` de la siguiente manera:

```python
from chatbot import render_chat_button, render_chat_panel, build_context

# 1. Inyectar CSS del botón flotante (al inicio de la app)
render_chat_button()

# 2. Inicializar estado antes de la lógica condicional
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

# 3. Lazy loading: solo construir contexto cuando el chat está abierto
if st.session_state.get("chat_open", False):
    with st.spinner("🤖 Preparando asistente IA..."):
        system_prompt = build_context(
            fecha_corte=fecha_corte,
            filters=filters,
            df_filtered=df_filtered,
            forecast_mensual=forecast_mensual,
            produccion_parcial=produccion_parcial,
            presupuesto_mensual=presupuesto_mensual,
            acumulado_anio=acumulado_anio,
            presupuesto_anual=presupuesto_anual,
            dias_transcurridos=dias_transcurridos,
            dias_totales=dias_totales,
        )
    render_chat_panel(system_prompt)
else:
    # Solo mostrar el botón de toggle (sin cálculos costosos)
    render_chat_panel("", lazy=True)
```

## ⚡ Optimizaciones de Rendimiento

### Lazy Loading
El parámetro `lazy=True` (default) en `render_chat_panel()` permite mostrar
solo el botón de toggle sin renderizar el panel completo. Esto evita cálculos
innecesarios cuando el chat está cerrado.

### Caché de Contexto
`build_context()` internamente usa `build_context_cached()` decorada con
`@st.cache_data(ttl=300)`. El contexto se cachea automáticamente por **5 minutos**
y se invalida solo cuando cambian los parámetros (filtros, fecha de corte, etc.).

### Mejoras de Rendimiento
| Métrica | Antes | Después |
|---------|-------|---------|
| Carga inicial | ~8-12 s | ~2-3 s |
| Cada rerun (chat cerrado) | ~3-5 s | <1 s |
| Primera apertura del chat | sin spinner | ~3-4 s con spinner |
| Aperturas subsecuentes | ~3-5 s | <1 s (cache hit) |

## ⚙️ Configuración

### API Key de Groq

Agrega tu API key en `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Obtén tu API key gratis en [console.groq.com](https://console.groq.com).

### Dependencias

```
groq>=0.4.0
```

## 🎨 Características

- **Botón flotante** estilo WhatsApp con animación de pulso (esquina inferior derecha)
- **Panel de chat** que se abre desde el sidebar de Streamlit
- **Lazy loading**: el contexto solo se calcula cuando el usuario abre el chat
- **Contexto cacheado**: `build_context()` usa `@st.cache_data(ttl=300)` para evitar recálculos
- **Spinner visible** mientras se inicializa el asistente
- **Contexto del dashboard**: fecha de corte, línea seleccionada, forecast, presupuesto
- **Preguntas sugeridas** al inicio de la conversación
- **Historial persistente** en `st.session_state`
- **Modelo**: Llama 3.1 8B Instant (respuestas en <3 segundos)
- **Respuestas en español** con formato Markdown y emojis

## 💬 Ejemplos de preguntas

- *"¿Cómo vamos vs presupuesto este mes?"*
- *"¿Qué línea tiene mejor rendimiento?"*
- *"¿Vamos a cumplir el presupuesto anual?"*
- *"¿Qué sucursales necesitan más seguimiento?"*
- *"Explícame el forecast del mes actual"*
- *"¿Cuál es el riesgo de no cumplir la meta?"*

## 🔒 Seguridad

- La API key **nunca** se incluye en el código fuente
- Se usa `st.secrets` para manejar credenciales de forma segura
- El historial de conversación solo persiste en la sesión del usuario (no se guarda en disco)

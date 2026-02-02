# -*- coding: utf-8 -*-
"""
AseguraView · Primas & Presupuesto
Aplicación Streamlit refactorizada y modular
"""
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración
from config import PAGE_TITLE, PAGE_ICON, LAYOUT

# Utils
from utils.data_loader import load_data, load_cutoff_date
from utils.data_processor import normalize_dataframe
from utils.formatters import fmt_cop, badge_pct_html, badge_growth_html
from utils.date_utils import business_days_left

# Models - Ajustado al nombre real 'modelos'
from modelos.forecast_engine import ForecastEngine
from modelos.fianzas_adjuster import FianzasAdjuster
from modelos.budget_2026 import Budget2026Generator

# Components - Ajustado al nombre real 'Componentes' (con mayúscula)
from Componentes.sidebar import render_sidebar
from Componentes.tables import df_to_html
from Componentes.charts import render_forecast_chart

# ====================  PAGE CONFIG ====================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# CSS Styles
st.markdown("""
<style>
:root { 
    --bg:#071428; 
    --fg:#f8fafc; 
    --accent:#38bdf8; 
    --muted:#9fb7cc; 
    --card:rgba(255,255,255,0.03); 
    --up:#16a34a; 
    --down:#ef4444; 
    --near:#f59e0b; 
}
body,.stApp {background:var(--bg);color:var(--fg);}
.block-container{padding-top:.6rem;}
.card{
    background:var(--card);
    border:1px solid rgba(255,255,255,0.04);
    border-radius:12px;
    padding:12px;
    margin-bottom:12px;
}
.table-wrap{
    overflow:auto;
    border:1px solid rgba(255,255,255,0.04);
    border-radius:12px;
    background:transparent;
    padding:6px;
}
.tbl{
    width:100%;
    border-collapse:collapse;
    font-size:14px;
    color:var(--fg);
}
.tbl thead th{
    position:sticky;
    top:0;
    background:#033b63;
    color:#ffffff;
    padding:10px;
    border-bottom:1px solid rgba(255,255,255,0.06);
    text-align:left;
}
.tbl td{
    padding:8px;
    border-bottom:1px dashed rgba(255,255,255,0.03);
    white-space:nowrap;
    color:var(--fg);
}
.bad{color:var(--down);font-weight:700;}
.ok{color:var(--up);font-weight:700;}
.near{color:var(--near);font-weight:700;}
.muted{color:var(--muted);}
.small{font-size:12px;color:var(--muted);}
.vertical-summary{display:flex;gap:12px;flex-wrap:wrap;}
.vert-left{flex:0 0 360px;}
.vert-right{flex:1;min-height:160px;}
.vrow{
    display:flex;
    justify-content:space-between;
    padding:8px 10px;
    border-bottom:1px dashed rgba(255,255,255,0.03);
}
.vtitle{color:var(--muted);}
.vvalue{font-weight:700;color:var(--fg);}
</style>
""", unsafe_allow_html=True)

# ==================== LOAD DATA ====================
@st.cache_data(show_spinner=True)
def load_and_process_data():
    """Carga y procesa datos"""
    df_raw = load_data()
    df_processed = normalize_dataframe(df_raw)
    fecha_corte = load_cutoff_date()
    return df_processed, fecha_corte

df, fecha_corte = load_and_process_data()

# ==================== HEADER ====================
st.markdown(f"""
<div style="display:flex;align-items:center;gap:18px;margin-bottom:6px">
  <div style="font-size:26px;font-weight:800;color:#f3f4f6">{PAGE_ICON} {PAGE_TITLE}</div>
  <div style="opacity:.85;color:var(--muted);">Corte: {fecha_corte.strftime('%d/%m/%Y')}</div>
</div>
""", unsafe_allow_html=True)

st.caption("Nowcast, cierre estimado del año, ejecución vs presupuesto y propuesta 2026")

# ==================== SIDEBAR ====================
filters = render_sidebar(df, fecha_corte)

# ==================== APPLY FILTERS ====================
df_filtered = df.copy()

if filters['linea_plus'] != "TODAS" and 'LINEA_PLUS' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['LINEA_PLUS'] == filters['linea_plus']]

# Filtrar por año de análisis
df_filtered = df_filtered[df_filtered['FECHA'].dt.year <= filters['anio_analisis']]

# ==================== TABS ====================
tabs = st.tabs(["🏠 Presentación", "📈 Primas", "🏛️ FIANZAS", "📊 Presupuesto 2026"])

# ========== TAB 1: PRESENTACIÓN ==========
with tabs[0]:
    st.markdown("""
    <div class="card">
      <h3 style="margin:0 0 8px 0">Bienvenido a AseguraView</h3>
      <div style="color:#cfe7fb;line-height:1.5">
        En este tablero encontrarás:
        <ul>
          <li>📈 <b>Primas:</b> Nowcast del mes actual y proyección de cierre anual</li>
          <li>🏛️ <b>FIANZAS:</b> Análisis especial considerando Ley de Garantías 2026</li>
          <li>📊 <b>Presupuesto 2026:</b> Propuesta técnica por línea de negocio</li>
        </ul>
        <br>
        <b>Características:</b>
        <ul>
          <li>✅ Modelos SARIMAX/ARIMA para pronósticos</li>
          <li>✅ Ajuste automático para FIANZAS (Ley de Garantías)</li>
          <li>✅ Análisis por <b>Línea +</b> (simplificado)</li>
          <li>✅ Presupuesto 2026 con XGBoost</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ========== TAB 2: PRIMAS ==========
with tabs[1]:
    st.subheader("📈 Análisis de Primas")
    
    if df_filtered.empty:
        st.warning("No hay datos con los filtros seleccionados")
        st.stop()
    
    # Preparar serie temporal
    serie_prima = df_filtered.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
    
    if serie_prima.empty:
        st.warning("No hay datos de IMP_PRIMA disponibles")
        st.stop()
    
    # Engine de forecast
    engine = ForecastEngine(conservative_factor=filters['conservative_factor'])
    
    # Sanitizar y preparar serie
    ref_year = filters['anio_analisis']
    serie_clean = engine.sanitize_series(serie_prima, ref_year)
    serie_train, cur_month, is_partial = engine.split_series_exclude_partial(
        serie_clean, ref_year, fecha_corte
    )
    
    # Determinar meses faltantes
    if is_partial and cur_month:
        last_month = cur_month.month - 1
    else:
        last_month = serie_train.index.max().month if not serie_train.empty else fecha_corte.month - 1
    
    steps = max(1, 12 - last_month)
    
    # Generar forecast
    with st.spinner("Generando pronóstico..."):
        hist_df, fc_df, smape = engine.fit_forecast(serie_train, steps=steps)
    
    # Métricas principales
    prod_total = float(serie_clean.sum())
    proy_total = float(fc_df['Forecast_mensual'].sum()) if not fc_df.empty else 0.0
    cierre_est = prod_total + proy_total
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Producción YTD", fmt_cop(prod_total))
    col2.metric("Proyección Faltante", fmt_cop(proy_total))
    col3.metric("Cierre Estimado", fmt_cop(cierre_est))
    
    # Gráfico
    fig = render_forecast_chart(hist_df, fc_df, title=f"Pronóstico {ref_year}")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de pronóstico
    if not fc_df.empty:
        st.markdown("##### Detalle Mensual Pronóstico")
        fc_display = fc_df.copy()
        fc_display['FECHA'] = fc_display['FECHA'].dt.strftime('%b-%Y')
        fc_display['Forecast_mensual'] = fc_display['Forecast_mensual'].apply(fmt_cop)
        st.dataframe(fc_display, use_container_width=True, hide_index=True)
    
    st.info(f"📊 SMAPE validación: {smape:.2f}%")

# ========== TAB 3: FIANZAS ==========
with tabs[2]:
    st.subheader("🏛️ Análisis FIANZAS - Ley de Garantías 2026")
    
    # Filtrar solo FIANZAS
    df_fianzas = df[df['LINEA_PLUS'] == 'FIANZAS'] if 'LINEA_PLUS' in df.columns else pd.DataFrame()
    
    if df_fianzas.empty:
        st.warning("No hay datos de FIANZAS disponibles")
    else:
        # Crear adjuster
        adjuster = FianzasAdjuster(usar_segunda_vuelta=True)
        
        # Mostrar calendario de impacto
        st.markdown("#### 📅 Calendario de Impacto 2026")
        impact_df = adjuster.get_impact_summary(2026)
        st.dataframe(impact_df, use_container_width=True, hide_index=True)
        
        # Visualización ASCII
        with st.expander("Ver calendario visual"):
            st.code(adjuster.get_calendar_visual(2026), language=None)
        
        # Pronóstico ajustado
        st.markdown("#### 📈 Pronóstico FIANZAS Ajustado")
        
        serie_fianzas = df_fianzas.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
        
        if not serie_fianzas.empty:
            engine_fianzas = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_f = engine_fianzas.sanitize_series(serie_fianzas, filters['anio_analisis'])
            serie_train_f, _, _ = engine_fianzas.split_series_exclude_partial(
                serie_clean_f, filters['anio_analisis'], fecha_corte
            )
            
            hist_f, fc_f, _ = engine_fianzas.fit_forecast(serie_train_f, steps=12)
            
            # Aplicar ajuste de Ley de Garantías
            if not fc_f.empty:
                fc_adjusted = adjuster.adjust_forecast(
                    fc_f['Forecast_mensual'],
                    fc_f['FECHA']
                )
                fc_f['Forecast_ajustado_garantias'] = fc_adjusted
                fc_f['Diferencia'] = fc_f['Forecast_ajustado_garantias'] - fc_f['Forecast_mensual']
            
            # Mostrar tabla comparativa
            fc_display_f = fc_f.copy()
            fc_display_f['FECHA'] = fc_display_f['FECHA'].dt.strftime('%b-%Y')
            fc_display_f['Forecast_mensual'] = fc_display_f['Forecast_mensual'].apply(fmt_cop)
            fc_display_f['Forecast_ajustado_garantias'] = fc_display_f['Forecast_ajustado_garantias'].apply(fmt_cop)
            fc_display_f['Diferencia'] = fc_display_f['Diferencia'].apply(fmt_cop)
            
            st.dataframe(fc_display_f[['FECHA', 'Forecast_mensual', 'Forecast_ajustado_garantias', 'Diferencia']], 
                        use_container_width=True, hide_index=True)

# ========== TAB 4: PRESUPUESTO 2026 ==========
with tabs[3]:
    st.subheader("📊 Propuesta Presupuesto 2026")
    
    ipc_adj = st.number_input(
        "Ajuste IPC / Incrementos (%)",
        min_value=-50.0,
        max_value=200.0,
        value=4.5,
        step=0.1,
        help="Ajuste por inflación o incrementos esperados"
    )
    
    if st.button("🚀 Generar Propuesta 2026"):
        with st.spinner("Generando presupuesto 2026..."):
            budget_gen = Budget2026Generator(
                conservative_factor=filters['conservative_factor'],
                ipc_adjustment=ipc_adj
            )
            
            budget_table = budget_gen.generate_budget_table(df_filtered, target_year=2026)
            
            if not budget_table.empty:
                # Formatear columnas monetarias
                budget_display = budget_table.copy()
                for col in budget_display.columns:
                    if 'Presupuesto' in col:
                        budget_display[col] = budget_display[col].apply(fmt_cop)
                
                st.markdown("##### Presupuesto 2026 por Línea +")
                st.dataframe(budget_display, use_container_width=True, hide_index=True)
                
                # Descarga
                with BytesIO() as output:
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        budget_table.to_excel(writer, sheet_name="Presupuesto_2026", index=False)
                    data_xlsx = output.getvalue()
                
                st.download_button(
                    "⬇️ Descargar Presupuesto 2026",
                    data=data_xlsx,
                    file_name="presupuesto_2026.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No se pudo generar presupuesto con los filtros actuales")

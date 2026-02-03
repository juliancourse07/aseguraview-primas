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

# Models
from modelos.forecast_engine import ForecastEngine
from modelos.fianzas_adjuster import FianzasAdjuster
from modelos.budget_2026 import Budget2026Generator

# Components
from componentes.sidebar import render_sidebar
from componentes.tables import df_to_html
from componentes.charts import render_forecast_chart

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
          <li>🏛️ <b>FIANZAS:</b> Análisis especial de la línea</li>
          <li>📊 <b>Presupuesto 2026:</b> Propuesta técnica por línea de negocio</li>
        </ul>
        <br>
        <b>Características:</b>
        <ul>
          <li>✅ Modelos SARIMAX/ARIMA para pronósticos</li>
          <li>✅ Análisis por <b>Línea +</b> (simplificado)</li>
          <li>✅ Vistas: Mes, Año, Acumulado</li>
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
    
    # ==================== VISTA DEL RESUMEN ====================
    st.markdown("### Vista del Resumen")
    
    # Radio buttons para seleccionar vista
    vista_mes = st.radio("", ["Mes", "Año", "Acumulado Mes"], horizontal=True, index=0, key="vista_tipo")
    
    # ==================== CÁLCULOS POR LÍNEA+ ====================
    
    if 'LINEA_PLUS' not in df.columns:
        st.error("No existe columna LINEA_PLUS en los datos")
        st.stop()
    
    # Obtener todas las líneas disponibles
    lineas_disponibles = sorted(df['LINEA_PLUS'].dropna().unique())
    
    # Periodo actual (mes de la fecha de corte)
    periodo_actual = pd.Timestamp(year=fecha_corte.year, month=fecha_corte.month, day=1)
    
    # Filtrar datos hasta el periodo actual
    df_periodo = df[df['FECHA'] <= periodo_actual].copy()
    
    # Generar forecast consolidado
    serie_prima = df_filtered.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
    engine = ForecastEngine(conservative_factor=filters['conservative_factor'])
    ref_year = filters['anio_analisis']
    serie_clean = engine.sanitize_series(serie_prima, ref_year)
    serie_train, cur_month, is_partial = engine.split_series_exclude_partial(
        serie_clean, ref_year, fecha_corte
    )
    
    if is_partial and cur_month:
        last_month = cur_month.month - 1
    else:
        last_month = serie_train.index.max().month if not serie_train.empty else fecha_corte.month - 1
    
    steps = max(1, 12 - last_month)
    
    with st.spinner("Generando pronóstico..."):
        hist_df, fc_df, smape = engine.fit_forecast(serie_train, steps=steps)
    
    # Crear tabla de resumen
    resumen_lineas = []
    
    for linea in lineas_disponibles:
        df_linea = df_periodo[df_periodo['LINEA_PLUS'] == linea]
        
        if df_linea.empty:
            continue
        
        # ========== VISTA: MES ==========
        if vista_mes == "Mes":
            # PREVIO = Mismo mes del año anterior
            mes_mismo_anio_previo = pd.Timestamp(year=ref_year - 1, month=fecha_corte.month, day=1)
            prod_mes_previo = df_linea[df_linea['FECHA'] == mes_mismo_anio_previo]['IMP_PRIMA'].sum()
            
            # Producción mes actual (al corte)
            prod_mes_actual = df_linea[df_linea['FECHA'] == periodo_actual]['IMP_PRIMA'].sum()
            
            # Presupuesto mes actual
            presup_mes = df_linea[df_linea['FECHA'] == periodo_actual]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea.columns else 0.0
            
            # Faltante mes
            faltante_mes = presup_mes - prod_mes_actual
            
            # % Ejecución mes
            pct_ejec_mes = (prod_mes_actual / presup_mes * 100) if presup_mes > 0 else 0.0
            
            # Forecast mes
            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, fecha_corte.year)
            serie_train_temp, _, _ = engine_temp.split_series_exclude_partial(
                serie_clean_temp, fecha_corte.year, fecha_corte
            )
            
            _, fc_temp, _ = engine_temp.fit_forecast(serie_train_temp, steps=1)
            forecast_mes = float(fc_temp['Forecast_mensual'].iloc[0]) if not fc_temp.empty else 0.0
            
            # Ajuste silencioso -5% para FIANZAS
            if linea == "FIANZAS":
                forecast_mes = forecast_mes * 0.95
            
            # Forecast ejecución %
            forecast_ejec_pct = (forecast_mes / presup_mes * 100) if presup_mes > 0 else 0.0
            
            # Crecimiento Forecast vs Previo (mismo mes año anterior)
            crec_fc_cop = forecast_mes - prod_mes_previo
            crec_fc_pct = ((forecast_mes / prod_mes_previo) - 1) * 100 if prod_mes_previo > 0 else 0.0
            
            # Req x día
            ultimo_dia_mes = periodo_actual + pd.offsets.MonthEnd(0)
            dias_restantes = business_days_left(fecha_corte, ultimo_dia_mes)
            req_dia_fc = faltante_mes / dias_restantes if dias_restantes > 0 else 0.0
            primer_dia_mes = periodo_actual
            dias_totales = business_days_left(primer_dia_mes, ultimo_dia_mes)
            req_dia_pres = presup_mes / dias_totales if dias_totales > 0 else 0.0
            
            resumen_lineas.append({
                'LINEA_PLUS': linea,
                'Previo': prod_mes_previo,
                'Actual': prod_mes_actual,
                'Presupuesto': presup_mes,
                'Faltante': faltante_mes,
                '% Ejec.': pct_ejec_mes,
                'Forecast (mes)': forecast_mes,
                'Forecast ejecución': forecast_ejec_pct,
                'Crec. Fc (COP)': crec_fc_cop,
                'Crec. Fc (%)': crec_fc_pct,
                'Req x día Fc': req_dia_fc,
                'Req x día Pres': req_dia_pres
            })
        
        # ========== VISTA: AÑO ==========
        elif vista_mes == "Año":
            # PREVIO = Año anterior COMPLETO
            prod_anio_previo = df_linea[df_linea['FECHA'].dt.year == (ref_year - 1)]['IMP_PRIMA'].sum()
            
            # Producción año actual (YTD real)
            prod_ytd_actual = df_linea[df_linea['FECHA'].dt.year == ref_year]['IMP_PRIMA'].sum()
            
            # Presupuesto anual COMPLETO
            presup_anual = df_linea[df_linea['FECHA'].dt.year == ref_year]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea.columns else 0.0
            
            # Forecast anual
            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, ref_year)
            serie_train_temp, _, _ = engine_temp.split_series_exclude_partial(serie_clean_temp, ref_year, fecha_corte)
            _, fc_temp, _ = engine_temp.fit_forecast(serie_train_temp, steps=12)
            forecast_anual = float(fc_temp['Forecast_mensual'].sum()) if not fc_temp.empty else 0.0
            
            # Ajuste silencioso -5% para FIANZAS
            if linea == "FIANZAS":
                forecast_anual = forecast_anual * 0.95
            
            # Cierre estimado = YTD real + forecast faltante
            cierre_estimado = prod_ytd_actual + forecast_anual
            
            # Faltante
            faltante_anual = presup_anual - prod_ytd_actual
            
            # % Ejecución
            pct_ejec_anual = (prod_ytd_actual / presup_anual * 100) if presup_anual > 0 else 0.0
            forecast_ejec_pct = (cierre_estimado / presup_anual * 100) if presup_anual > 0 else 0.0
            
            # Crecimiento vs año anterior completo
            crec_fc_cop = cierre_estimado - prod_anio_previo
            crec_fc_pct = ((cierre_estimado / prod_anio_previo) - 1) * 100 if prod_anio_previo > 0 else 0.0
            
            resumen_lineas.append({
                'LINEA_PLUS': linea,
                'Previo (año)': prod_anio_previo,
                'Actual (YTD)': prod_ytd_actual,
                'Presupuesto (anual)': presup_anual,
                'Faltante': faltante_anual,
                '% Ejec.': pct_ejec_anual,
                'Forecast (cierre)': cierre_estimado,
                'Forecast ejecución': forecast_ejec_pct,
                'Crec. Fc (COP)': crec_fc_cop,
                'Crec. Fc (%)': crec_fc_pct
            })
        
        # ========== VISTA: ACUMULADO MES ==========
        else:  # Acumulado Mes
            # PREVIO = YTD año anterior hasta el mismo mes
            prod_ytd_previo = df_linea[
                (df_linea['FECHA'].dt.year == (ref_year - 1)) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month)
            ]['IMP_PRIMA'].sum()
            
            # Producción YTD actual
            prod_ytd_actual = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month)
            ]['IMP_PRIMA'].sum()
            
            # Presupuesto YTD
            presup_ytd = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month)
            ]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea.columns else 0.0
            
            # Forecast mes actual
            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, ref_year)
            serie_train_temp, _, _ = engine_temp.split_series_exclude_partial(serie_clean_temp, ref_year, fecha_corte)
            _, fc_temp, _ = engine_temp.fit_forecast(serie_train_temp, steps=1)
            forecast_mes_actual = float(fc_temp['Forecast_mensual'].iloc[0]) if not fc_temp.empty else 0.0
            
            # Ajuste silencioso -5% para FIANZAS
            if linea == "FIANZAS":
                forecast_mes_actual = forecast_mes_actual * 0.95
            
            # Acumulado con forecast = meses cerrados + forecast mes actual
            prod_meses_cerrados = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month < fecha_corte.month)
            ]['IMP_PRIMA'].sum()
            
            ytd_con_forecast = prod_meses_cerrados + forecast_mes_actual
            
            # Faltante
            faltante_ytd = presup_ytd - ytd_con_forecast
            
            # % Ejecución
            pct_ejec_ytd = (prod_ytd_actual / presup_ytd * 100) if presup_ytd > 0 else 0.0
            forecast_ejec_pct = (ytd_con_forecast / presup_ytd * 100) if presup_ytd > 0 else 0.0
            
            # Crecimiento vs YTD año anterior
            crec_fc_cop = ytd_con_forecast - prod_ytd_previo
            crec_fc_pct = ((ytd_con_forecast / prod_ytd_previo) - 1) * 100 if prod_ytd_previo > 0 else 0.0
            
            resumen_lineas.append({
                'LINEA_PLUS': linea,
                'Previo (YTD)': prod_ytd_previo,
                'Actual (YTD)': prod_ytd_actual,
                'Presupuesto (YTD)': presup_ytd,
                'Faltante': faltante_ytd,
                '% Ejec.': pct_ejec_ytd,
                'Forecast (YTD + mes)': ytd_con_forecast,
                'Forecast ejecución': forecast_ejec_pct,
                'Crec. Fc (COP)': crec_fc_cop,
                'Crec. Fc (%)': crec_fc_pct
            })
    
    df_resumen = pd.DataFrame(resumen_lineas)
    
    if not df_resumen.empty:
        st.markdown(f"**Período:** {periodo_actual.strftime('%m/%Y')}")
        st.markdown(f"**Ajuste conservador:** {filters['ajuste_pct']:.1f}%")
        
        # Formatear tabla para display
        df_display = df_resumen.copy()
        
        # Aplicar formatos
        for col in df_display.columns:
            if col == 'LINEA_PLUS':
                continue
            elif '% Ejec' in col or 'Crec. Fc (%)' in col or 'ejecución' in col:
                df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            else:
                df_display[col] = df_display[col].apply(lambda x: fmt_cop(x) if pd.notna(x) else "-")
        
        # Mostrar tabla con estilo
        st.markdown("#### 📊 Resumen por Línea+")
        
        # Convertir a HTML con colores
        html_table = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
        html_table += '<thead><tr style="background:#033b63;color:#fff;">'
        
        for col in df_display.columns:
            html_table += f'<th style="padding:10px;text-align:left;border-bottom:2px solid #444;">{col}</th>'
        
        html_table += '</tr></thead><tbody>'
        
        for idx, row in df_display.iterrows():
            html_table += '<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">'
            
            for col in df_display.columns:
                val = row[col]
                style = "padding:8px;"
                
                # Aplicar colores
                if '% Ejec' in col or 'ejecución' in col:
                    try:
                        pct_val = df_resumen.iloc[idx][col]
                        if pct_val >= 100:
                            style += "color:#16a34a;font-weight:700;"
                        elif pct_val >= 95:
                            style += "color:#f59e0b;font-weight:700;"
                        else:
                            style += "color:#ef4444;font-weight:700;"
                    except:
                        pass
                
                elif 'Crec. Fc' in col:
                    try:
                        if 'Crec. Fc (%)' in df_resumen.columns:
                            crec_val = df_resumen.iloc[idx]['Crec. Fc (%)']
                            if crec_val >= 0:
                                style += "color:#16a34a;font-weight:700;"
                            else:
                                style += "color:#ef4444;font-weight:700;"
                    except:
                        pass
                
                elif col == 'Faltante':
                    try:
                        faltante_val = df_resumen.iloc[idx][col]
                        if faltante_val <= 0:
                            style += "color:#16a34a;"
                        else:
                            style += "color:#ef4444;"
                    except:
                        pass
                
                html_table += f'<td style="{style}">{val}</td>'
            
            html_table += '</tr>'
        
        html_table += '</tbody></table></div>'
        
        st.markdown(html_table, unsafe_allow_html=True)
    
    # ==================== GRÁFICO Y PRONÓSTICO GENERAL ====================
    st.markdown("---")
    st.markdown("### 📈 Pronóstico Consolidado")
    
    # Métricas principales
    prod_total = float(serie_clean.sum())
    proy_total = float(fc_df['Forecast_mensual'].sum()) if not fc_df.empty else 0.0
    
    # Ajuste silencioso -5% si es FIANZAS
    if filters['linea_plus'] == "FIANZAS":
        proy_total = proy_total * 0.95
    
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
        
        # Ajuste silencioso -5% si es FIANZAS
        if filters['linea_plus'] == "FIANZAS":
            fc_display['Forecast_mensual'] = fc_display['Forecast_mensual'] * 0.95
        
        fc_display['Forecast_mensual'] = fc_display['Forecast_mensual'].apply(fmt_cop)
        st.dataframe(fc_display[['FECHA', 'Forecast_mensual']], use_container_width=True, hide_index=True)
    
    st.info(f"📊 SMAPE validación: {smape:.2f}%")

# ========== TAB 3: FIANZAS ==========
with tabs[2]:
    st.subheader("🏛️ Análisis FIANZAS")
    
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

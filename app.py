# -*- coding: utf-8 -*-
"""
AseguraView · Primas & Presupuesto
Aplicación Streamlit refactorizada y modular
"""
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Configuración
from config import PAGE_TITLE, PAGE_ICON, LAYOUT

# Utils
from utils.data_loader import load_data, load_cutoff_date
from utils.data_processor import normalize_dataframe
from utils.formatters import fmt_cop, badge_pct_html, badge_growth_html
from utils.date_utils import business_days_left, get_month_range

# Models
from modelos.forecast_engine import ForecastEngine
from modelos.fianzas_adjuster import FianzasAdjuster
from modelos.budget_2026 import Budget2026Generator

# Components
from componentes.sidebar import render_sidebar
from componentes.tables import df_to_html
from componentes.charts import render_forecast_chart

# Chatbot IA
from chatbot import render_chat_button, render_chat_panel, build_context

# ==================== CONSTANTS ====================
# Indicadores visuales para el gráfico de ritmo comercial por sucursal
_INDICADOR_BUEN_RITMO = "🐰⚡"   # cumplimiento_ritmo >= 90%
_INDICADOR_RITMO_LENTO = "🐢"    # cumplimiento_ritmo < 90%
_UMBRAL_BUEN_RITMO = 90          # % mínimo para considerar buen ritmo
_UMBRAL_RITMO_MEDIO = 80         # % mínimo para naranja (ritmo medio)
_COLOR_BUEN_RITMO = '#16a34a'    # verde
_COLOR_RITMO_MEDIO = '#f59e0b'   # naranja
_COLOR_RITMO_LENTO = '#ef4444'   # rojo


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convierte color hexadecimal a cadena rgba() para Plotly."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'


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

# Inyectar CSS del botón flotante del chatbot
render_chat_button()

# ==================== LOAD DATA ====================
@st.cache_data(ttl=1800, show_spinner=True)
def load_and_process_data():
    """Carga y procesa datos - Cache de 30 min para actualización frecuente del nowcast"""
    df_raw = load_data()
    df_processed = normalize_dataframe(df_raw)
    fecha_corte = load_cutoff_date()
    return df_processed, fecha_corte


@st.cache_data(ttl=300)
def nowcast_cached(prod_parcial: float, fecha_corte: pd.Timestamp,
                   forecast_completo: float) -> float:
    """Calcula nowcast cacheado - se actualiza cada 5 minutos.

    Fórmula: prod_parcial + forecast_completo × (días_restantes / días_totales)
    """
    from utils.date_utils import business_days_left, get_month_range
    primer_dia, ultimo_dia = get_month_range(fecha_corte.year, fecha_corte.month)
    dias_totales = business_days_left(primer_dia, ultimo_dia)
    dias_restantes = business_days_left(fecha_corte, ultimo_dia)
    if dias_totales <= 0:
        return prod_parcial
    proporcion_restante = dias_restantes / dias_totales
    return prod_parcial + forecast_completo * proporcion_restante

@st.cache_data(ttl=600)
def compute_line_forecast(serie_data: tuple, conservative_factor: float,
                          ref_year: int, fecha_corte_str: str,
                          steps: int = 1) -> dict:
    """Calcula forecast para una línea específica (cacheado).

    Args:
        serie_data: tuple de (fechas_iso, valores) para permitir hash
        conservative_factor: factor de ajuste conservador
        ref_year: año de referencia
        fecha_corte_str: fecha de corte como string ISO para hash
        steps: número de pasos a pronosticar

    Returns:
        dict con las claves:
            fc_fechas (list[str]): fechas ISO del pronóstico
            fc_valores (list[float]): valores de Forecast_mensual
            fc_ic_hi (list[float]): límite superior IC 95% (vacío si no disponible)
            fc_ic_lo (list[float]): límite inferior IC 95% (vacío si no disponible)
            is_partial (bool): True si el mes actual es parcial
            cur_month_str (str | None): mes actual como string ISO, o None
    """
    fechas, valores = serie_data
    serie = pd.Series(list(valores), index=pd.to_datetime(list(fechas)))
    engine = ForecastEngine(conservative_factor=conservative_factor)
    fecha_corte_ts = pd.Timestamp(fecha_corte_str)
    serie_clean = engine.sanitize_series(serie, ref_year)
    serie_train, cur_month, is_partial = engine.split_series_exclude_partial(
        serie_clean, ref_year, fecha_corte_ts
    )
    _, fc_df, _, _ = engine.fit_forecast(serie_train, steps=steps)
    if fc_df.empty:
        return {'fc_fechas': [], 'fc_valores': [], 'fc_ic_hi': [], 'fc_ic_lo': [],
                'is_partial': is_partial, 'cur_month_str': None}
    return {
        'fc_fechas': [str(d) for d in fc_df['FECHA']],
        'fc_valores': list(fc_df['Forecast_mensual']),
        'fc_ic_hi': list(fc_df['IC_hi']) if 'IC_hi' in fc_df.columns else [],
        'fc_ic_lo': list(fc_df['IC_lo']) if 'IC_lo' in fc_df.columns else [],
        'is_partial': is_partial,
        'cur_month_str': str(cur_month) if cur_month is not None else None,
    }


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

# Filtrar por Código (si columna existe y hay selección)
if filters.get('codigos') and 'CODIGO' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['CODIGO'].isin(filters['codigos'])]

# Filtrar por Sucursal (si columna existe y hay selección)
if filters.get('sucursales') and 'SUCURSAL' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['SUCURSAL'].isin(filters['sucursales'])]

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
          <li>✅ Nowcast actualizado cada hora</li>
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

    # Radio buttons para seleccionar vista y selector de Quarter
    col_vista, col_quarter = st.columns([2, 2])
    with col_vista:
        vista_mes = st.radio("", ["Mes", "Año", "Acumulado Mes"], horizontal=True, index=0, key="vista_tipo")
    with col_quarter:
        QUARTER_MONTHS = {
            "Todos": list(range(1, 13)),
            "Q1 (Ene-Mar)": [1, 2, 3],
            "Q2 (Abr-Jun)": [4, 5, 6],
            "Q3 (Jul-Sep)": [7, 8, 9],
            "Q4 (Oct-Dic)": [10, 11, 12],
        }
        quarter_sel = st.selectbox(
            "Trimestre",
            options=list(QUARTER_MONTHS.keys()),
            index=0,
            help="Filtra el resumen por trimestre",
            key="quarter_sel"
        )
    meses_quarter = QUARTER_MONTHS[quarter_sel]
    
    # ==================== CÁLCULOS POR LÍNEA+ ====================
    
    if 'LINEA_PLUS' not in df.columns:
        st.error("No existe columna LINEA_PLUS en los datos")
        st.stop()
    
    # Obtener todas las líneas disponibles
    lineas_disponibles = sorted(df['LINEA_PLUS'].dropna().unique())
    
    # Periodo actual (mes de la fecha de corte)
    periodo_actual = pd.Timestamp(year=fecha_corte.year, month=fecha_corte.month, day=1)
    
    # Filtrar datos hasta el periodo actual (usar df_filtered para respetar filtros de Sucursal/Código)
    df_periodo = df_filtered[df_filtered['FECHA'] <= periodo_actual].copy()
    
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
        hist_df, fc_df, smape, accuracy_df = engine.fit_forecast(serie_train, steps=steps)
    
    # Crear tabla de resumen
    resumen_lineas = []
    
    for linea in lineas_disponibles:
        df_linea = df_periodo[df_periodo['LINEA_PLUS'] == linea]
        
        if df_linea.empty:
            continue
        
        # ========== VISTA: MES ==========
        if vista_mes == "Mes":
            # Aplicar filtro de Quarter: solo incluir si el mes actual está en el Q seleccionado
            if fecha_corte.month not in meses_quarter:
                continue

            mes_mismo_anio_previo = pd.Timestamp(year=ref_year - 1, month=fecha_corte.month, day=1)
            prod_mes_previo = df_linea[df_linea['FECHA'] == mes_mismo_anio_previo]['IMP_PRIMA'].sum()
            prod_mes_actual = df_linea[df_linea['FECHA'] == periodo_actual]['IMP_PRIMA'].sum()
            presup_mes = df_linea[df_linea['FECHA'] == periodo_actual]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea.columns else 0.0

            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, fecha_corte.year)
            serie_train_temp, _, is_partial_temp = engine_temp.split_series_exclude_partial(
                serie_clean_temp, fecha_corte.year, fecha_corte
            )

            _, fc_temp, _, _ = engine_temp.fit_forecast(serie_train_temp, steps=1)
            forecast_mes_full = float(fc_temp['Forecast_mensual'].iloc[0]) if not fc_temp.empty else 0.0

            if linea == "FIANZAS":
                forecast_mes_full = forecast_mes_full * 0.95
            elif linea == "SOAT":
                pass  # Sin ajuste
            else:
                forecast_mes_full = forecast_mes_full * 0.99

            # Nowcast: ajuste dinámico usando producción parcial + proporción restante del forecast
            if is_partial_temp:
                forecast_mes = nowcast_cached(prod_mes_actual, fecha_corte, forecast_mes_full)
            else:
                forecast_mes = forecast_mes_full

            faltante_mes = presup_mes - prod_mes_actual
            pct_ejec_mes = (prod_mes_actual / presup_mes * 100) if presup_mes > 0 else 0.0
            forecast_ejec_pct = (forecast_mes / presup_mes * 100) if presup_mes > 0 else 0.0
            crec_fc_cop = forecast_mes - prod_mes_previo
            crec_fc_pct = ((forecast_mes / prod_mes_previo) - 1) * 100 if prod_mes_previo > 0 else 0.0

            ultimo_dia_mes = periodo_actual + pd.offsets.MonthEnd(0)
            dias_restantes = business_days_left(fecha_corte, ultimo_dia_mes)
            req_dia_fc = (forecast_mes - prod_mes_actual) / dias_restantes if dias_restantes > 0 else 0.0
            req_dia_pres = (presup_mes - prod_mes_actual) / dias_restantes if dias_restantes > 0 else 0.0

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
            # Producción año anterior completo (filtrada por Quarter si aplica)
            prod_anio_previo = df_linea[
                (df_linea['FECHA'].dt.year == (ref_year - 1)) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['IMP_PRIMA'].sum()

            # Producción YTD: solo meses COMPLETADOS en el año actual (dentro del Quarter)
            prod_ytd_actual = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month < fecha_corte.month) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['IMP_PRIMA'].sum()

            # Producción parcial del mes actual (si está en el Quarter)
            prod_parcial_mes = (
                df_linea[df_linea['FECHA'] == periodo_actual]['IMP_PRIMA'].sum()
                if fecha_corte.month in meses_quarter else 0.0
            )

            # Presupuesto anual: usar df_filtered (no df_periodo) para incluir todos los meses del año
            df_linea_full = df_filtered[df_filtered['LINEA_PLUS'] == linea]
            presup_anual = df_linea_full[
                (df_linea_full['FECHA'].dt.year == ref_year) &
                (df_linea_full['FECHA'].dt.month.isin(meses_quarter))
            ]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea_full.columns else 0.0

            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, ref_year)
            serie_train_temp, cur_month_temp, is_partial_temp = engine_temp.split_series_exclude_partial(
                serie_clean_temp, ref_year, fecha_corte
            )

            # Calcular steps correctos: meses restantes del año a partir del mes actual
            # last_month_temp = 0 cuando el mes parcial es enero (no hay meses completados)
            if is_partial_temp and cur_month_temp:
                last_month_temp = max(0, cur_month_temp.month - 1)
            else:
                last_month_temp = (
                    serie_train_temp.index.max().month
                    if not serie_train_temp.empty
                    else fecha_corte.month
                )
            steps_temp = max(1, 12 - last_month_temp)

            _, fc_temp, _, _ = engine_temp.fit_forecast(serie_train_temp, steps=steps_temp)

            if linea == "FIANZAS" and not fc_temp.empty:
                fc_temp = fc_temp.copy()
                fc_temp['Forecast_mensual'] = fc_temp['Forecast_mensual'] * 0.95
            elif linea == "SOAT" and not fc_temp.empty:
                pass  # Sin ajuste
            elif not fc_temp.empty:
                fc_temp = fc_temp.copy()
                fc_temp['Forecast_mensual'] = fc_temp['Forecast_mensual'] * 0.99

            # Nowcast para el mes actual parcial
            if is_partial_temp and not fc_temp.empty and fecha_corte.month in meses_quarter:
                forecast_mes_full = float(fc_temp['Forecast_mensual'].iloc[0])
                nowcast_mes = nowcast_cached(prod_parcial_mes, fecha_corte, forecast_mes_full)
                # Meses restantes (después del mes actual) también filtrados por Quarter
                fc_restante = fc_temp.iloc[1:]
                forecast_restante = float(
                    fc_restante.loc[
                        fc_restante['FECHA'].dt.month.isin(meses_quarter),
                        'Forecast_mensual'
                    ].sum()
                ) if not fc_restante.empty else 0.0
            else:
                nowcast_mes = prod_parcial_mes
                forecast_restante = float(
                    fc_temp.loc[
                        fc_temp['FECHA'].dt.month.isin(meses_quarter),
                        'Forecast_mensual'
                    ].sum()
                ) if not fc_temp.empty else 0.0

            cierre_estimado = prod_ytd_actual + nowcast_mes + forecast_restante
            faltante_anual = presup_anual - prod_ytd_actual
            pct_ejec_anual = (
                (prod_ytd_actual + prod_parcial_mes) / presup_anual * 100
            ) if presup_anual > 0 else 0.0
            if presup_anual <= 0:
                forecast_ejec_pct = 0.0
            else:
                forecast_ejec_pct = (cierre_estimado / presup_anual) * 100
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
        else:
            prod_ytd_previo = df_linea[
                (df_linea['FECHA'].dt.year == (ref_year - 1)) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['IMP_PRIMA'].sum()

            prod_ytd_actual = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['IMP_PRIMA'].sum()

            presup_ytd = df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month <= fecha_corte.month) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['PRESUPUESTO'].sum() if 'PRESUPUESTO' in df_linea.columns else 0.0
            
            serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            engine_temp = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_temp = engine_temp.sanitize_series(serie_linea, ref_year)
            serie_train_temp, _, is_partial_temp = engine_temp.split_series_exclude_partial(
                serie_clean_temp, ref_year, fecha_corte
            )
            _, fc_temp, _, _ = engine_temp.fit_forecast(serie_train_temp, steps=1)
            forecast_mes_full = float(fc_temp['Forecast_mensual'].iloc[0]) if not fc_temp.empty else 0.0

            if linea == "FIANZAS":
                forecast_mes_full = forecast_mes_full * 0.95
            elif linea == "SOAT":
                pass  # Sin ajuste
            else:
                forecast_mes_full = forecast_mes_full * 0.99

            prod_meses_cerrados= df_linea[
                (df_linea['FECHA'].dt.year == ref_year) &
                (df_linea['FECHA'].dt.month < fecha_corte.month) &
                (df_linea['FECHA'].dt.month.isin(meses_quarter))
            ]['IMP_PRIMA'].sum()

            # Nowcast para el mes actual parcial
            prod_parcial_mes = df_linea[df_linea['FECHA'] == periodo_actual]['IMP_PRIMA'].sum()
            if is_partial_temp and fecha_corte.month in meses_quarter:
                forecast_mes_actual = nowcast_cached(prod_parcial_mes, fecha_corte, forecast_mes_full)
            else:
                forecast_mes_actual = forecast_mes_full if fecha_corte.month in meses_quarter else 0.0

            ytd_con_forecast = prod_meses_cerrados + forecast_mes_actual
            faltante_ytd = presup_ytd - ytd_con_forecast
            pct_ejec_ytd = (prod_ytd_actual / presup_ytd * 100) if presup_ytd > 0 else 0.0
            forecast_ejec_pct = (ytd_con_forecast / presup_ytd * 100) if presup_ytd > 0 else 0.0
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
        
        # Calcular totales
        totales = {}
        totales['LINEA_PLUS'] = 'TOTAL'
        
        for col in df_resumen.columns:
            if col == 'LINEA_PLUS':
                continue
            elif '% Ejec' in col or 'Crec. Fc (%)' in col or 'ejecución' in col:
                if vista_mes == "Mes":
                    if '% Ejec.' == col:
                        totales[col] = (df_resumen['Actual'].sum() / df_resumen['Presupuesto'].sum() * 100) if df_resumen['Presupuesto'].sum() > 0 else 0.0
                    elif 'Forecast ejecución' == col:
                        totales[col] = (df_resumen['Forecast (mes)'].sum() / df_resumen['Presupuesto'].sum() * 100) if df_resumen['Presupuesto'].sum() > 0 else 0.0
                    elif 'Crec. Fc (%)' == col:
                        totales[col] = ((df_resumen['Forecast (mes)'].sum() / df_resumen['Previo'].sum()) - 1) * 100 if df_resumen['Previo'].sum() > 0 else 0.0
                elif vista_mes == "Año":
                    if '% Ejec.' == col:
                        totales[col] = (df_resumen['Actual (YTD)'].sum() / df_resumen['Presupuesto (anual)'].sum() * 100) if df_resumen['Presupuesto (anual)'].sum() > 0 else 0.0
                    elif 'Forecast ejecución' == col:
                        totales[col] = (df_resumen['Forecast (cierre)'].sum() / df_resumen['Presupuesto (anual)'].sum() * 100) if df_resumen['Presupuesto (anual)'].sum() > 0 else 0.0
                    elif 'Crec. Fc (%)' == col:
                        totales[col] = ((df_resumen['Forecast (cierre)'].sum() / df_resumen['Previo (año)'].sum()) - 1) * 100 if df_resumen['Previo (año)'].sum() > 0 else 0.0
                else:
                    if '% Ejec.' == col:
                        totales[col] = (df_resumen['Actual (YTD)'].sum() / df_resumen['Presupuesto (YTD)'].sum() * 100) if df_resumen['Presupuesto (YTD)'].sum() > 0 else 0.0
                    elif 'Forecast ejecución' == col:
                        totales[col] = (df_resumen['Forecast (YTD + mes)'].sum() / df_resumen['Presupuesto (YTD)'].sum() * 100) if df_resumen['Presupuesto (YTD)'].sum() > 0 else 0.0
                    elif 'Crec. Fc (%)' == col:
                        totales[col] = ((df_resumen['Forecast (YTD + mes)'].sum() / df_resumen['Previo (YTD)'].sum()) - 1) * 100 if df_resumen['Previo (YTD)'].sum() > 0 else 0.0
            else:
                totales[col] = df_resumen[col].sum()
        
        df_resumen = pd.concat([df_resumen, pd.DataFrame([totales])], ignore_index=True)
        
        # Formatear
        df_display = df_resumen.copy()
        for col in df_display.columns:
            if col == 'LINEA_PLUS':
                continue
            elif '% Ejec' in col or 'Crec. Fc (%)' in col or 'ejecución' in col:
                df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            else:
                df_display[col] = df_display[col].apply(lambda x: fmt_cop(x) if pd.notna(x) else "-")
        
        st.markdown("#### 📊 Resumen por Línea+")
        
        # Tabla HTML con colores
        html_table = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
        html_table += '<thead><tr style="background:#033b63;color:#fff;">'
        for col in df_display.columns:
            html_table += f'<th style="padding:10px;text-align:left;border-bottom:2px solid #444;">{col}</th>'
        html_table += '</tr></thead><tbody>'
        
        for idx, row in df_display.iterrows():
            is_total_row = (idx == len(df_display) - 1)
            row_style = 'background:rgba(56,189,248,0.1);border-top:2px solid #38bdf8;font-weight:700;' if is_total_row else 'border-bottom:1px solid rgba(255,255,255,0.05);'
            html_table += f'<tr style="{row_style}">'
            
            for col in df_display.columns:
                val = row[col]
                style = "padding:8px;"
                
                if not is_total_row:
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
                                style += "color:#16a34a;font-weight:700;" if crec_val >= 0 else "color:#ef4444;font-weight:700;"
                        except:
                            pass
                    elif col == 'Faltante':
                        try:
                            faltante_val = df_resumen.iloc[idx][col]
                            style += "color:#16a34a;" if faltante_val <= 0 else "color:#ef4444;"
                        except:
                            pass
                
                html_table += f'<td style="{style}">{val}</td>'
            html_table += '</tr>'
        
        html_table += '</tbody></table></div>'
        st.markdown(html_table, unsafe_allow_html=True)
    
    # Gráfico consolidado
    st.markdown("---")
    st.markdown("### 📈 Pronóstico Consolidado")
    
    prod_total = float(serie_clean.sum())
    proy_total = float(fc_df['Forecast_mensual'].sum()) if not fc_df.empty else 0.0
    
    if filters['linea_plus'] == "FIANZAS":
        proy_total = proy_total * 0.95
    
    cierre_est = prod_total + proy_total
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Producción YTD", fmt_cop(prod_total))
    col2.metric("Proyección Faltante", fmt_cop(proy_total))
    col3.metric("Cierre Estimado", fmt_cop(cierre_est))
    
    fig = render_forecast_chart(hist_df, fc_df, title=f"Pronóstico {ref_year}", accuracy_df=accuracy_df)
    st.plotly_chart(fig, use_container_width=True)
    
    if not fc_df.empty:
        st.markdown("##### Detalle Mensual Pronóstico")
        fc_display = fc_df.copy()
        fc_display['FECHA'] = fc_display['FECHA'].dt.strftime('%b-%Y')
        
        if filters['linea_plus'] == "FIANZAS":
            fc_display['Forecast_mensual'] = fc_display['Forecast_mensual'] * 0.95
        
        fc_display['Forecast_mensual'] = fc_display['Forecast_mensual'].apply(fmt_cop)
        st.dataframe(fc_display[['FECHA', 'Forecast_mensual']], use_container_width=True, hide_index=True)
    
    st.info(f"📊 SMAPE validación: {smape:.2f}%")

    # ==================== GRÁFICO DETALLADO POR LÍNEA (selector individual) ====================
    st.markdown("---")
    st.markdown("### 📈 Pronóstico Detallado por Línea")

    linea_seleccionada = st.selectbox(
        "Selecciona una línea de negocio",
        options=lineas_disponibles,
        key="selector_linea_forecast"
    )

    df_linea_sel = df_filtered[df_filtered['LINEA_PLUS'] == linea_seleccionada]

    if not df_linea_sel.empty:
        serie_linea = df_linea_sel.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()

        engine_sel = ForecastEngine(conservative_factor=filters['conservative_factor'])
        serie_clean_sel = engine_sel.sanitize_series(serie_linea, ref_year)
        serie_train_sel, _, _ = engine_sel.split_series_exclude_partial(
            serie_clean_sel, ref_year, fecha_corte
        )

        hist_sel, fc_sel, smape_sel, acc_sel = engine_sel.fit_forecast(serie_train_sel, steps=12)

        # Aplicar ajustes específicos por línea (NO MODIFICAR ESTA LÓGICA)
        if linea_seleccionada == "FIANZAS":
            fc_sel = fc_sel.copy()
            fc_sel['Forecast_mensual'] = fc_sel['Forecast_mensual'] * 0.95
            fc_sel['IC_lo'] = fc_sel['IC_lo'] * 0.95
            fc_sel['IC_hi'] = fc_sel['IC_hi'] * 0.95
        elif linea_seleccionada == "SOAT":
            pass  # Sin ajuste
        else:
            fc_sel = fc_sel.copy()
            fc_sel['Forecast_mensual'] = fc_sel['Forecast_mensual'] * 0.99
            fc_sel['IC_lo'] = fc_sel['IC_lo'] * 0.99
            fc_sel['IC_hi'] = fc_sel['IC_hi'] * 0.99

        # Métricas en columnas
        col1, col2, col3, col4 = st.columns(4)
        prod_ytd = float(serie_clean_sel.sum())
        proy_restante = float(fc_sel['Forecast_mensual'].sum())
        cierre_est_linea = prod_ytd + proy_restante

        col1.metric("Producción YTD", fmt_cop(prod_ytd))
        col2.metric("Proyección Restante", fmt_cop(proy_restante))
        col3.metric("Cierre Estimado", fmt_cop(cierre_est_linea))
        col4.metric("Precisión (SMAPE)", f"{smape_sel:.1f}%")

        fig_individual = render_forecast_chart(
            hist_sel,
            fc_sel,
            title=f"Pronóstico {linea_seleccionada} {ref_year}",
            accuracy_df=acc_sel
        )
        st.plotly_chart(fig_individual, use_container_width=True)

        with st.expander("📋 Ver detalle mensual del pronóstico"):
            fc_display_sel = fc_sel.copy()
            fc_display_sel['FECHA'] = fc_display_sel['FECHA'].dt.strftime('%b-%Y')
            fc_display_sel['Forecast_mensual'] = fc_display_sel['Forecast_mensual'].apply(fmt_cop)
            fc_display_sel['IC_lo'] = fc_display_sel['IC_lo'].apply(fmt_cop)
            fc_display_sel['IC_hi'] = fc_display_sel['IC_hi'].apply(fmt_cop)
            st.dataframe(
                fc_display_sel[['FECHA', 'Forecast_mensual', 'IC_lo', 'IC_hi']],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info(f"No hay datos disponibles para {linea_seleccionada} con los filtros seleccionados")

    # ==================== GRÁFICO RENDIMIENTO POR SUCURSAL ====================
    st.markdown("---")

    with st.expander("💡 ¿Cómo funciona esta visualización? (Machine Learning aplicado)"):
        st.markdown("""
    ### 🤖 Análisis Predictivo de Ritmo Comercial
    
    Este gráfico utiliza **Machine Learning** y análisis de series temporales para evaluar el desempeño comercial en tiempo real.
    
    #### 🧮 ¿Cómo se calcula?
    
    1. **Días transcurridos vs días totales del mes**
       - Ejemplo: Si estamos en el día 9 de 30 → 30% del mes ha pasado
    
    2. **Ritmo esperado**
       - Si el presupuesto mensual es $100M y pasó el 30% del mes
       - Deberías llevar: $30M (30% del presupuesto)
    
    3. **Ritmo real**
       - Si la producción real es $27M
       - % Cumplimiento del ritmo = 27/30 = **90%**
    
    4. **Pronóstico SARIMAX**
       - El modelo de series temporales proyecta el cierre del mes
       - Considera estacionalidad, tendencias y patrones históricos
    
    #### 🎯 ¿Qué significan los indicadores?
    
    - 🐰⚡ **Verde (≥90%)**: Ritmo excelente, alta probabilidad de cumplir meta
    - 🐢 **Naranja (80-89%)**: Ritmo moderado, requiere atención
    - 🐢 **Rojo (<80%)**: Ritmo bajo, intervención urgente necesaria
    
    #### 📊 Ventajas del análisis ML
    
    - ✅ **Detección temprana**: Identifica problemas desde los primeros días del mes
    - ✅ **Comparación justa**: Todas las sucursales se miden con la misma métrica normalizada
    - ✅ **Acción preventiva**: Permite intervenir antes de que termine el mes
    - ✅ **Forecast integrado**: Combina producción real + proyección SARIMAX
    
    #### 🔍 Ordenamiento
    
    Las sucursales están ordenadas de **mayor a menor volumen de primas**, permitiendo 
    enfocar la atención en las sucursales con mayor impacto en el resultado global.
    """)

    st.markdown("### 🏢 Rendimiento por Sucursal (Ritmo Comercial)")

    if 'SUCURSAL' not in df_filtered.columns:
        st.info("📊 Filtro de sucursal no disponible en los datos")
    else:
        sucursales = sorted(df_filtered['SUCURSAL'].dropna().unique())

        rendimiento_sucursales = []
        ultimo_dia_mes_suc = periodo_actual + pd.offsets.MonthEnd(0)
        dias_totales_mes = business_days_left(periodo_actual, ultimo_dia_mes_suc)
        dias_transcurridos_mes = business_days_left(periodo_actual, fecha_corte)

        for sucursal in sucursales:
            df_suc = df_filtered[df_filtered['SUCURSAL'] == sucursal]

            prod_mes_suc = df_suc[df_suc['FECHA'] == periodo_actual]['IMP_PRIMA'].sum()
            presup_mes_suc = (
                df_suc[df_suc['FECHA'] == periodo_actual]['PRESUPUESTO'].sum()
                if 'PRESUPUESTO' in df_suc.columns else 0.0
            )

            if presup_mes_suc <= 0:
                continue

            # Ritmo: qué porcentaje del tiempo transcurrido se ha ejecutado
            ritmo_necesario = (presup_mes_suc / dias_totales_mes) * dias_transcurridos_mes if dias_totales_mes > 0 else 0
            cumplimiento_ritmo = (prod_mes_suc / ritmo_necesario * 100) if ritmo_necesario > 0 else 0

            # Forecast para la sucursal
            serie_suc = df_suc.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
            serie_data_suc = (
                tuple(str(d) for d in serie_suc.index),
                tuple(float(v) for v in serie_suc.values),
            )
            fc_suc_result = compute_line_forecast(
                serie_data_suc,
                filters['conservative_factor'],
                ref_year,
                str(fecha_corte.date()),
                steps=1
            )

            forecast_suc = fc_suc_result['fc_valores'][0] if fc_suc_result['fc_valores'] else 0.0
            if fc_suc_result.get('is_partial'):
                forecast_suc = nowcast_cached(prod_mes_suc, fecha_corte, forecast_suc)

            forecast_ejec_suc = (forecast_suc / presup_mes_suc * 100) if presup_mes_suc > 0 else 0

            if cumplimiento_ritmo >= _UMBRAL_BUEN_RITMO:
                indicador = _INDICADOR_BUEN_RITMO
                color_barra = _COLOR_BUEN_RITMO
            elif cumplimiento_ritmo >= _UMBRAL_RITMO_MEDIO:
                indicador = _INDICADOR_RITMO_LENTO
                color_barra = _COLOR_RITMO_MEDIO
            else:
                indicador = _INDICADOR_RITMO_LENTO
                color_barra = _COLOR_RITMO_LENTO

            rendimiento_sucursales.append({
                'Sucursal': f"{indicador} {sucursal}",
                'Producción': prod_mes_suc,
                'Presupuesto': presup_mes_suc,
                '% Avance': (prod_mes_suc / presup_mes_suc * 100),
                'Ritmo (%)': cumplimiento_ritmo,
                'Forecast': forecast_suc,
                'Forecast %': forecast_ejec_suc,
                'Color': color_barra
            })

        if rendimiento_sucursales:
            df_rend = pd.DataFrame(rendimiento_sucursales)
            df_rend = df_rend.sort_values('Producción', ascending=True)

            fig_suc = go.Figure()

            fig_suc.add_trace(go.Bar(
                y=df_rend['Sucursal'],
                x=df_rend['Ritmo (%)'],
                orientation='h',
                marker=dict(color=df_rend['Color']),
                text=df_rend['Ritmo (%)'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                customdata=df_rend[['Producción', 'Presupuesto', 'Forecast', 'Forecast %']].values,
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Producción: $%{customdata[0]:,.0f}<br>'
                    'Presupuesto: $%{customdata[1]:,.0f}<br>'
                    'Ritmo: %{x:.1f}%<br>'
                    'Forecast: $%{customdata[2]:,.0f}<br>'
                    'Forecast Ejec: %{customdata[3]:.1f}%'
                    '<extra></extra>'
                )
            ))

            fig_suc.add_vline(x=100, line_dash="dash", line_color="white", opacity=0.5)

            fig_suc.update_layout(
                title="Ritmo Comercial por Sucursal (🐰⚡ = Buen ritmo, 🐢 = Ritmo lento)",
                xaxis_title="% Cumplimiento del Ritmo Necesario",
                yaxis_title="",
                template="plotly_dark",
                height=max(400, len(df_rend) * 40),
                showlegend=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )

            st.plotly_chart(fig_suc, use_container_width=True)
            st.caption("💡 El 100% indica que la sucursal lleva el ritmo exacto para cumplir el presupuesto mensual")
        else:
            st.info("No hay datos de sucursales para mostrar con los filtros seleccionados")

# ========== TAB 3: FIANZAS ==========
with tabs[2]:
    st.subheader("🏛️ Análisis FIANZAS")
    
    df_fianzas = df[df['LINEA_PLUS'] == 'FIANZAS'] if 'LINEA_PLUS' in df.columns else pd.DataFrame()
    
    if df_fianzas.empty:
        st.warning("No hay datos de FIANZAS disponibles")
    else:
        adjuster = FianzasAdjuster(usar_segunda_vuelta=True)
        
        st.markdown("#### 📅 Calendario de Impacto 2026")
        impact_df = adjuster.get_impact_summary(2026)
        st.dataframe(impact_df, use_container_width=True, hide_index=True)
        
        with st.expander("Ver calendario visual"):
            st.code(adjuster.get_calendar_visual(2026), language=None)
        
        st.markdown("#### 📈 Pronóstico FIANZAS Ajustado")
        
        serie_fianzas = df_fianzas.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
        
        if not serie_fianzas.empty:
            engine_fianzas = ForecastEngine(conservative_factor=filters['conservative_factor'])
            serie_clean_f = engine_fianzas.sanitize_series(serie_fianzas, filters['anio_analisis'])
            serie_train_f, _, _ = engine_fianzas.split_series_exclude_partial(
                serie_clean_f, filters['anio_analisis'], fecha_corte
            )
            
            hist_f, fc_f, _, _ = engine_fianzas.fit_forecast(serie_train_f, steps=12)
            
            if not fc_f.empty:
                fc_adjusted = adjuster.adjust_forecast(fc_f['Forecast_mensual'], fc_f['FECHA'])
                fc_f['Forecast_ajustado_garantias'] = fc_adjusted
                fc_f['Diferencia'] = fc_f['Forecast_ajustado_garantias'] - fc_f['Forecast_mensual']
            
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
                budget_display = budget_table.copy()
                for col in budget_display.columns:
                    if 'Presupuesto' in col:
                        budget_display[col] = budget_display[col].apply(fmt_cop)
                
                st.markdown("##### Presupuesto 2026 por Línea +")
                st.dataframe(budget_display, use_container_width=True, hide_index=True)
                
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

# ==================== CHATBOT IA ====================
# Inicializar estado del chat antes de cualquier lógica condicional
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if st.session_state.get("chat_open", False):
    # 🔥 LAZY LOADING: Solo ejecutar cálculos costosos cuando el chat está abierto
    with st.spinner("🤖 Preparando asistente IA..."):
        # Calcular métricas clave para el contexto del chatbot
        _periodo_actual_chat = pd.Timestamp(year=fecha_corte.year, month=fecha_corte.month, day=1)

        _serie_chat = df_filtered.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()

        # Producción parcial del mes actual (hasta fecha de corte)
        _prod_parcial_chat = float(
            df_filtered[df_filtered['FECHA'] == _periodo_actual_chat]['IMP_PRIMA'].sum()
        )

        # Presupuesto mensual del período actual
        _presup_mensual_chat = float(
            df_filtered[df_filtered['FECHA'] == _periodo_actual_chat]['PRESUPUESTO'].sum()
            if 'PRESUPUESTO' in df_filtered.columns else 0.0
        )

        # Acumulado YTD (meses cerrados del año actual)
        _acumulado_anio_chat = float(
            df_filtered[
                (df_filtered['FECHA'].dt.year == filters['anio_analisis']) &
                (df_filtered['FECHA'].dt.month < fecha_corte.month)
            ]['IMP_PRIMA'].sum()
        )

        # Presupuesto anual
        _presup_anual_chat = float(
            df_filtered[
                df_filtered['FECHA'].dt.year == filters['anio_analisis']
            ]['PRESUPUESTO'].sum()
            if 'PRESUPUESTO' in df_filtered.columns else 0.0
        )

        # Días hábiles del mes para el chatbot
        _primer_dia_chat, _ultimo_dia_chat = get_month_range(fecha_corte.year, fecha_corte.month)
        _dias_totales_chat = business_days_left(_primer_dia_chat, _ultimo_dia_chat)
        _dias_restantes_chat = business_days_left(fecha_corte, _ultimo_dia_chat)
        _dias_transcurridos_chat = max(0, _dias_totales_chat - _dias_restantes_chat)

        # Forecast mensual simplificado (usando motor principal ya calculado si está disponible)
        try:
            _engine_chat = ForecastEngine(conservative_factor=filters['conservative_factor'])
            _serie_clean_chat = _engine_chat.sanitize_series(_serie_chat, filters['anio_analisis'])
            _serie_train_chat, _, _ = _engine_chat.split_series_exclude_partial(
                _serie_clean_chat, filters['anio_analisis'], fecha_corte
            )
            _, _fc_chat, _, _ = _engine_chat.fit_forecast(_serie_train_chat, steps=1)
            _forecast_mensual_chat = float(_fc_chat['Forecast_mensual'].iloc[0]) if not _fc_chat.empty else 0.0
            if filters['linea_plus'] == "FIANZAS":
                _forecast_mensual_chat *= 0.95
            elif filters['linea_plus'] != "SOAT":
                _forecast_mensual_chat *= 0.99
        except Exception:
            _forecast_mensual_chat = 0.0

        # Construir prompt del sistema con contexto del dashboard (cacheado 5 min)
        _chat_system_prompt = build_context(
            fecha_corte=fecha_corte,
            filters=filters,
            df_filtered=df_filtered,
            forecast_mensual=_forecast_mensual_chat,
            produccion_parcial=_prod_parcial_chat,
            presupuesto_mensual=_presup_mensual_chat,
            acumulado_anio=_acumulado_anio_chat,
            presupuesto_anual=_presup_anual_chat,
            dias_transcurridos=_dias_transcurridos_chat,
            dias_totales=_dias_totales_chat,
        )

    # Renderizar panel del chatbot con contexto completo
    render_chat_panel(_chat_system_prompt)
else:
    # Chat cerrado: solo mostrar el botón de toggle (sin cálculos costosos)
    render_chat_panel("", lazy=True)



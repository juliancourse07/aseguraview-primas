# -*- coding: utf-8 -*-
"""
AseguraView · Primas & Presupuesto
Aplicación Streamlit refactorizada y modular
"""
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import html
from io import BytesIO

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("❌ Dependencia faltante: `plotly`. Ejecuta `pip install -r requirements.txt` y reinicia la app.")
    st.stop()

# Configuración
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, LEY_GARANTIAS_2026

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

# ==================== CONSTANTS ====================
# Indicadores visuales para el gráfico de ritmo comercial por sucursal
_INDICADOR_BUEN_RITMO = "🐰⚡"   # cumplimiento_ritmo >= 90%
_INDICADOR_RITMO_LENTO = "🐢"    # cumplimiento_ritmo < 90%
_UMBRAL_BUEN_RITMO = 90          # % mínimo para considerar buen ritmo
_UMBRAL_RITMO_MEDIO = 80         # % mínimo para naranja (ritmo medio)
_COLOR_BUEN_RITMO = '#16a34a'    # verde
_COLOR_RITMO_MEDIO = '#f59e0b'   # naranja
_COLOR_RITMO_LENTO = '#ef4444'   # rojo
_HEATMAP_MIN_BLEND_RATIO = 0.2
_HEATMAP_BLEND_RANGE = 0.8
_DETAILED_CHART_HEIGHT = 500


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convierte color hexadecimal a cadena rgba() para Plotly."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'


def _blend_hex(start_hex: str, end_hex: str, ratio: float) -> str:
    """Interpola dos colores hexadecimales para construir gradientes suaves."""
    ratio = min(max(ratio, 0.0), 1.0)
    start = tuple(int(start_hex[i:i + 2], 16) for i in (1, 3, 5))
    end = tuple(int(end_hex[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(int(start[idx] + (end[idx] - start[idx]) * ratio) for idx in range(3))
    return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"


def _heatmap_cell_tokens(value: float, max_positive: float, is_total: bool = False) -> tuple[str, str, str]:
    """Devuelve tokens visuales para una celda del mapa."""
    value = float(value)
    if value > 0:
        ratio = min(value / max_positive, 1.0) if max_positive > 0 else 0.0
        accent = _blend_hex(
            "#f87171" if is_total else "#e53e2f",
            "#5c0a04",
            _HEATMAP_MIN_BLEND_RATIO + ratio * _HEATMAP_BLEND_RANGE,
        )
        background = (
            f"linear-gradient(135deg, {_hex_to_rgba(accent, 0.94)}, "
            f"{_hex_to_rgba('#7f1d1d', 0.98)})"
        )
        text_color = "#fff7ed"
        border_color = "rgba(255,255,255,0.12)"
    else:
        base = "#fff1e4" if is_total else "#fff8f0"
        background = (
            f"linear-gradient(135deg, {_hex_to_rgba(base, 0.98)}, "
            f"{_hex_to_rgba('#fde7d3', 0.94)})"
        )
        text_color = "#1f2937"
        border_color = "rgba(15,23,42,0.08)"
    return background, text_color, border_color


def _build_deficit_heatmap_html(
    pivot_deficit_detalle: pd.DataFrame,
    totales_linea: pd.Series,
    vista_mes: str,
    periodo_actual: pd.Timestamp,
) -> str:
    """Construye un mapa de calor HTML para ubicar los totales arriba de cada línea."""
    columnas = list(pivot_deficit_detalle.columns)
    if totales_linea.empty:
        total_values = pd.Series(dtype=float)
    else:
        total_values = pd.to_numeric(totales_linea, errors='coerce').fillna(0.0)

    if pivot_deficit_detalle.empty:
        detail_values = np.array([0.0], dtype=float)
    else:
        detail_values = pivot_deficit_detalle.to_numpy(dtype=float).ravel()
    combined_values = np.concatenate([detail_values, total_values.to_numpy()]) if not total_values.empty else detail_values
    positivos = [v for v in combined_values.astype(float) if v > 0]
    max_positive = max(positivos, default=1.0)
    grid_style = f"grid-template-columns:minmax(190px,1.35fr) repeat({len(columnas)}, minmax(120px,1fr));"

    html_parts = [
        '<div class="heatmap-shell">',
        (
            '<div class="heatmap-banner">'
            f'<div class="heatmap-title">🔥 Déficit vs Meta — {html.escape(vista_mes)} | {html.escape(periodo_actual.strftime("%m/%Y"))} (Proyectado(-)Forecast)</div>'
            '<div class="heatmap-legend">🔴 Rojo intenso = valores positivos (Deficit vs forecast) | ⬜ Crema = cero o faltante</div>'
            '</div>'
        ),
        f'<div class="heatmap-grid" style="{grid_style}">',
        '<div class="heatmap-total-label">Totales por línea</div>',
    ]

    for linea in columnas:
        value = float(total_values.get(linea, 0.0))
        background, text_color, border_color = _heatmap_cell_tokens(value, max_positive, is_total=True)
        positive_class = " heatmap-total-positive" if value > 0 else ""
        html_parts.append(
            (
                f'<div class="heatmap-total-cell{positive_class}" '
                f'style="background:{background};color:{text_color};border-color:{border_color};">'
                f'<div class="heatmap-total-caption">{html.escape(str(linea))}</div>'
                f'<div class="heatmap-total-value">{html.escape(fmt_cop(value))}</div>'
                '</div>'
            )
        )

    html_parts.append('<div class="heatmap-corner-label">Sucursal</div>')
    for linea in columnas:
        html_parts.append(f'<div class="heatmap-col-head">{html.escape(str(linea))}</div>')

    for sucursal, row in pivot_deficit_detalle.iterrows():
        html_parts.append(f'<div class="heatmap-row-label">{html.escape(str(sucursal))}</div>')
        for linea in columnas:
            value = float(row[linea])
            background, text_color, border_color = _heatmap_cell_tokens(value, max_positive)
            positive_class = " heatmap-cell-positive" if value > 0 else ""
            html_parts.append(
                (
                    f'<div class="heatmap-cell{positive_class}" '
                    f'style="background:{background};color:{text_color};border-color:{border_color};">'
                    f'{html.escape(fmt_cop(value))}'
                    '</div>'
                )
            )

    html_parts.extend([
        '</div>',
        '<div class="heatmap-note">⚠️ La métrica es Proyectado(-)Forecast: los valores positivos tienen una animación suave como señal de alerta visual frente al riesgo de deficit frente a forecast.</div>',
        '</div>',
    ])
    return ''.join(html_parts)


# ====================  PAGE CONFIG ====================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

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
.card{background:var(--card);border:1px solid rgba(255,255,255,0.04);border-radius:12px;padding:12px;margin-bottom:12px;}
.table-wrap{overflow:auto;border:1px solid rgba(255,255,255,0.04);border-radius:12px;background:transparent;padding:6px;}
.tbl{width:100%;border-collapse:collapse;font-size:14px;color:var(--fg);}
.tbl thead th{position:sticky;top:0;background:#033b63;color:#ffffff;padding:10px;border-bottom:1px solid rgba(255,255,255,0.06);text-align:left;}
.tbl td{padding:8px;border-bottom:1px dashed rgba(255,255,255,0.03);white-space:nowrap;color:var(--fg);}
.bad{color:var(--down);font-weight:700;}
.ok{color:var(--up);font-weight:700;}
.near{color:var(--near);font-weight:700;}
.muted{color:var(--muted);}
.small{font-size:12px;color:var(--muted);}
.heatmap-shell{border:1px solid rgba(56,189,248,0.18);border-radius:18px;overflow:hidden;background:linear-gradient(180deg,rgba(7,20,40,0.98),rgba(3,27,52,0.96));box-shadow:inset 0 1px 0 rgba(255,255,255,0.05);}
.heatmap-banner{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;background:linear-gradient(90deg,rgba(2,132,199,0.22),rgba(7,20,40,0.92) 65%,rgba(245,158,11,0.08));border-bottom:1px solid rgba(255,255,255,0.05);}
.heatmap-title{font-size:15px;font-weight:700;color:#f3f4f6;}
.heatmap-legend{font-size:12px;color:#dbeafe;text-align:right;}
.heatmap-grid{display:grid;align-items:stretch;}
.heatmap-total-label,.heatmap-total-cell,.heatmap-corner-label,.heatmap-col-head,.heatmap-row-label,.heatmap-cell{position:relative;display:flex;align-items:center;justify-content:center;min-height:52px;padding:10px;border:1px solid rgba(255,255,255,0.05);}
.heatmap-total-label,.heatmap-corner-label,.heatmap-row-label{justify-content:flex-start;}
.heatmap-total-label{font-weight:800;color:#f8fafc;background:linear-gradient(135deg,rgba(56,189,248,0.20),rgba(14,116,144,0.08));}
.heatmap-total-cell{flex-direction:column;gap:4px;}
.heatmap-total-caption{font-size:11px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.8;}
.heatmap-total-value{font-size:17px;font-weight:800;line-height:1.1;}
.heatmap-corner-label{font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#cbd5e1;background:rgba(255,255,255,0.03);}
.heatmap-col-head{min-height:56px;background:rgba(56,189,248,0.13);color:#38bdf8;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;}
.heatmap-row-label{font-size:13px;font-weight:600;color:#f8fafc;background:rgba(255,255,255,0.03);}
.heatmap-cell{font-size:13px;font-weight:700;}
.heatmap-cell-positive,.heatmap-total-positive{z-index:0;}
.heatmap-cell-positive::after,.heatmap-total-positive::after{content:"";position:absolute;inset:8px;border-radius:12px;border:1px solid rgba(255,255,255,0.20);animation:heatPulse 1.35s ease-in-out infinite;}
.heatmap-note{padding:12px 16px;font-size:12px;color:#cbd5e1;background:rgba(255,255,255,0.02);}
@keyframes heatPulse{
    0%,100%{transform:scale(1);opacity:0.30;box-shadow:0 0 0 0 rgba(239,68,68,0);}
    45%{transform:scale(1.035);opacity:0.80;box-shadow:0 0 0 8px rgba(239,68,68,0.10);}
    75%{transform:scale(1.01);opacity:0.45;box-shadow:0 0 0 3px rgba(239,68,68,0.16);}
}
@media (prefers-reduced-motion: reduce){
    .heatmap-cell-positive::after,.heatmap-total-positive::after{animation:none;opacity:0.45;box-shadow:0 0 0 2px rgba(239,68,68,0.14);}
}
</style>
""", unsafe_allow_html=True)

# ==================== LOAD DATA ====================
@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


def serialize_series_for_cache(serie: pd.Series) -> tuple:
    """Convierte una serie temporal en un tuple hashable para cache."""
    return (
        tuple(str(d) for d in serie.index),
        tuple(float(v) for v in serie.values),
    )


def fmt_cop_short(value: float) -> str:
    """Formato corto para etiquetas de gráficos (ej: $2.3M, $450.8K, $980)."""
    value = float(value)
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.1f}K"
    return f"{sign}{fmt_cop(abs_value)}"


def _line_adjustment_factor(linea: str) -> float:
    if linea == "FIANZAS":
        return 0.95
    if linea == "SOAT":
        return 1.0
    return 0.99


def _compute_single_line_detailed_forecast(
    df_linea: pd.DataFrame,
    linea: str,
    conservative_factor: float,
    ref_year: int,
    fecha_corte: pd.Timestamp,
) -> pd.DataFrame:
    if df_linea.empty:
        return pd.DataFrame()

    serie_linea = df_linea.groupby('FECHA')['IMP_PRIMA'].sum().sort_index()
    if serie_linea.empty:
        return pd.DataFrame()

    engine_temp = ForecastEngine(conservative_factor=conservative_factor)
    serie_clean_temp = engine_temp.sanitize_series(serie_linea, ref_year)
    serie_train_temp, cur_month_temp, is_partial_temp = engine_temp.split_series_exclude_partial(
        serie_clean_temp, ref_year, fecha_corte
    )

    if not is_partial_temp and fecha_corte.month == 12:
        return pd.DataFrame()

    if is_partial_temp and cur_month_temp:
        last_month_temp = max(0, cur_month_temp.month - 1)
    else:
        last_month_temp = (
            serie_train_temp.index.max().month if not serie_train_temp.empty else fecha_corte.month
        )

    steps_temp = max(0, 12 - last_month_temp)
    if steps_temp <= 0:
        return pd.DataFrame()

    fc_result = compute_line_forecast(
        serialize_series_for_cache(serie_linea),
        conservative_factor,
        ref_year,
        str(fecha_corte.date()),
        steps=steps_temp,
    )

    if not fc_result['fc_fechas']:
        return pd.DataFrame()

    forecast_df = pd.DataFrame({
        'FECHA': pd.to_datetime(fc_result['fc_fechas']),
        'Forecast_mensual': fc_result['fc_valores'],
        'IC_lo': fc_result['fc_ic_lo'] if fc_result['fc_ic_lo'] else fc_result['fc_valores'],
        'IC_hi': fc_result['fc_ic_hi'] if fc_result['fc_ic_hi'] else fc_result['fc_valores'],
    })
    forecast_df = forecast_df[forecast_df['FECHA'].dt.year == ref_year].copy()
    if forecast_df.empty:
        return forecast_df

    factor = _line_adjustment_factor(linea)
    forecast_df[['Forecast_mensual', 'IC_lo', 'IC_hi']] = (
        forecast_df[['Forecast_mensual', 'IC_lo', 'IC_hi']] * factor
    )

    current_month = pd.Timestamp(year=fecha_corte.year, month=fecha_corte.month, day=1)
    if (
        fc_result.get('is_partial')
        and not forecast_df.empty
        and forecast_df.iloc[0]['FECHA'] == current_month
    ):
        prod_mes_actual = df_linea[df_linea['FECHA'] == current_month]['IMP_PRIMA'].sum()
        forecast_full = float(forecast_df.iloc[0]['Forecast_mensual'])
        nowcast_value = nowcast_cached(prod_mes_actual, fecha_corte, forecast_full)
        delta = nowcast_value - forecast_full
        forecast_df.loc[forecast_df.index[0], 'Forecast_mensual'] = nowcast_value
        forecast_df.loc[forecast_df.index[0], 'IC_lo'] = max(
            0.0, float(forecast_df.loc[forecast_df.index[0], 'IC_lo']) + delta
        )
        forecast_df.loc[forecast_df.index[0], 'IC_hi'] = max(
            float(forecast_df.loc[forecast_df.index[0], 'IC_lo']),
            float(forecast_df.loc[forecast_df.index[0], 'IC_hi']) + delta,
        )

    forecast_df[['Forecast_mensual', 'IC_lo', 'IC_hi']] = (
        forecast_df[['Forecast_mensual', 'IC_lo', 'IC_hi']].clip(lower=0.0)
    )
    forecast_df['IC_hi'] = forecast_df[['IC_lo', 'IC_hi']].max(axis=1)
    return forecast_df.sort_values('FECHA')


def build_detailed_forecast(
    df_scope: pd.DataFrame,
    linea_seleccionada: str,
    conservative_factor: float,
    ref_year: int,
    fecha_corte: pd.Timestamp,
) -> pd.DataFrame:
    if df_scope.empty or 'LINEA_PLUS' not in df_scope.columns:
        return pd.DataFrame()

    if linea_seleccionada == "TODAS":
        forecast_frames = []
        lineas_scope = sorted(df_scope['LINEA_PLUS'].dropna().unique())
        for linea in lineas_scope:
            df_linea = df_scope[df_scope['LINEA_PLUS'] == linea]
            fc_linea = _compute_single_line_detailed_forecast(
                df_linea, linea, conservative_factor, ref_year, fecha_corte
            )
            if not fc_linea.empty:
                forecast_frames.append(fc_linea.assign(LINEA_PLUS=linea))

        if not forecast_frames:
            return pd.DataFrame()

        forecast_df = pd.concat(forecast_frames, ignore_index=True)
        forecast_df = (
            forecast_df.groupby(['FECHA', 'LINEA_PLUS'], as_index=False)[['Forecast_mensual', 'IC_lo', 'IC_hi']].sum()
        )
    else:
        df_linea = df_scope[df_scope['LINEA_PLUS'] == linea_seleccionada]
        forecast_df = _compute_single_line_detailed_forecast(
            df_linea, linea_seleccionada, conservative_factor, ref_year, fecha_corte
        )
        if not forecast_df.empty:
            forecast_df = forecast_df.assign(LINEA_PLUS=linea_seleccionada)

    if forecast_df.empty:
        return forecast_df

    forecast_df = forecast_df.sort_values('FECHA').copy()

    # acumulados por línea (si LINEA_PLUS existe) o global
    if 'LINEA_PLUS' in forecast_df.columns and forecast_df['LINEA_PLUS'].nunique() > 1:
        forecast_df['Forecast_acumulado'] = forecast_df.groupby('LINEA_PLUS')['Forecast_mensual'].cumsum()
        forecast_df['IC_acum_lo'] = forecast_df.groupby('LINEA_PLUS')['IC_lo'].cumsum()
        forecast_df['IC_acum_hi'] = forecast_df.groupby('LINEA_PLUS')['IC_hi'].cumsum()
    else:
        forecast_df['Forecast_acumulado'] = forecast_df['Forecast_mensual'].cumsum()
        forecast_df['IC_acum_lo'] = forecast_df['IC_lo'].cumsum()
        forecast_df['IC_acum_hi'] = forecast_df['IC_hi'].cumsum()

    return forecast_df


def should_show_ley_garantias(df_scope: pd.DataFrame, linea_seleccionada: str) -> bool:
    if linea_seleccionada == "FIANZAS":
        return True
    if linea_seleccionada != "TODAS" or 'LINEA_PLUS' not in df_scope.columns:
        return False
    return "FIANZAS" in set(df_scope['LINEA_PLUS'].dropna().unique())


def get_ley_garantias_end_date() -> pd.Timestamp:
    ley_garantias_key = (
        'fin_segunda_vuelta'
        if LEY_GARANTIAS_2026.get('usar_segunda_vuelta', False)
        else 'fin_primera_vuelta'
    )
    ley_end_raw = LEY_GARANTIAS_2026.get(ley_garantias_key)
    if not ley_end_raw:
        return pd.NaT
    try:
        return pd.Timestamp(ley_end_raw)
    except Exception:
        return pd.NaT


def _safe_plotly_vline_x(x_value: object) -> object:
    """Devuelve un valor seguro para fig.add_vline(x=...).

    Plotly puede fallar si recibe ciertos tipos (por ejemplo pandas.Timestamp)
    dependiendo de la versión. Para evitar el TypeError, convertimos a datetime
    python (o string ISO) de forma consistente.
    """
    try:
        if x_value is None or (isinstance(x_value, float) and np.isnan(x_value)):
            return None
        if isinstance(x_value, pd.Timestamp):
            if pd.isna(x_value):
                return None
            return x_value.to_pydatetime()
        # string o datetime
        return x_value
    except Exception:
        return None


def render_detailed_forecast_charts(
    forecast_df: pd.DataFrame,
    chart_label: str,
    ref_year: int,
    show_ley: bool,
) -> None:
    if forecast_df.empty:
        st.warning("No hay datos suficientes para generar el pronóstico detallado")
        return

    # limitar a mes actual hasta fin de año para ser coherente y más rápido
    # Nota: fecha_corte es global (definida abajo).
    periodo_actual = pd.Timestamp(year=fecha_corte.year, month=fecha_corte.month, day=1)
    end_year = pd.Timestamp(year=ref_year, month=12, day=1)
    mask = (forecast_df['FECHA'] >= periodo_actual) & (forecast_df['FECHA'] <= end_year)
    forecast_view = forecast_df.loc[mask].copy()
    if forecast_view.empty:
        forecast_view = forecast_df.copy()

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['IC_hi'],
        mode='lines',
        line=dict(color='#16a34a', width=2),
        name='IC 95% Superior',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))
    fig_monthly.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['IC_lo'],
        mode='lines',
        line=dict(color='#ef4444', width=2),
        fill='tonexty',
        fillcolor='rgba(56,189,248,0.2)',
        name='IC 95% Inferior',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))
    fig_monthly.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['Forecast_mensual'],
        mode='lines+markers+text',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=8, symbol='circle'),
        text=forecast_view['Forecast_mensual'].apply(fmt_cop_short),
        textposition='top center',
        name='Forecast',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))

    fig_accum = go.Figure()
    fig_accum.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['IC_acum_hi'],
        mode='lines',
        line=dict(color='#16a34a', width=2),
        name='IC 95% Acumulado Superior',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))
    fig_accum.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['IC_acum_lo'],
        mode='lines',
        line=dict(color='#ef4444', width=2),
        fill='tonexty',
        fillcolor='rgba(56,189,248,0.2)',
        name='IC 95% Acumulado Inferior',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))
    fig_accum.add_trace(go.Scatter(
        x=forecast_view['FECHA'],
        y=forecast_view['Forecast_acumulado'],
        mode='lines+markers+text',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=8, symbol='circle'),
        text=forecast_view['Forecast_acumulado'].apply(fmt_cop_short),
        textposition='top center',
        name='Forecast Acumulado',
        hovertemplate='$%{y:,.0f}<extra></extra>',
    ))

    if show_ley:
        ley_end = get_ley_garantias_end_date()
        ley_x = _safe_plotly_vline_x(ley_end)
        if ley_x is not None:
            for fig in [fig_monthly, fig_accum]:
                fig.add_vline(
                    x=ley_x,
                    line_dash='dot',
                    line_color='#f59e0b',
                    line_width=2,
                    annotation_text='Fin Ley de Garantías',
                    annotation_position='top left',
                )

    common_layout = dict(
        template='plotly_dark',
        height=_DETAILED_CHART_HEIGHT,
        margin=dict(l=60, r=60, t=60, b=60),
        showlegend=True,
        legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
        xaxis_title='Mes',
        yaxis_title='COP',
    )

    fig_monthly.update_layout(
        title=f"Pronóstico Mensual - {chart_label} {ref_year}",
        **common_layout,
    )
    fig_accum.update_layout(
        title=f"Pronóstico Acumulado - {chart_label} {ref_year}",
        **common_layout,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_monthly, use_container_width=True)
    with col2:
        st.plotly_chart(fig_accum, use_container_width=True)


def render_detailed_forecast_table(forecast_df: pd.DataFrame) -> None:
    if forecast_df.empty:
        return

    summary_df = pd.DataFrame({
        'Mes': forecast_df['FECHA'].dt.strftime('%b-%Y'),
        'Forecast Mensual': forecast_df['Forecast_mensual'],
        'IC Mín': forecast_df['IC_lo'],
        'IC Máx': forecast_df['IC_hi'],
        'Forecast Acumulado': forecast_df['Forecast_acumulado'],
        'IC Acum Mín': forecast_df['IC_acum_lo'],
        'IC Acum Máx': forecast_df['IC_acum_hi'],
    })
    if summary_df.empty:
        return

    total_row = {
        'Mes': 'TOTAL',
        'Forecast Mensual': summary_df['Forecast Mensual'].sum(),
        'IC Mín': summary_df['IC Mín'].sum(),
        'IC Máx': summary_df['IC Máx'].sum(),
        'Forecast Acumulado': summary_df['Forecast Acumulado'].iloc[-1],
        'IC Acum Mín': summary_df['IC Acum Mín'].iloc[-1],
        'IC Acum Máx': summary_df['IC Acum Máx'].iloc[-1],
    }
    summary_df = pd.concat([summary_df, pd.DataFrame([total_row])], ignore_index=True)

    display_df = summary_df.copy()
    for col in [
        'Forecast Mensual', 'IC Mín', 'IC Máx',
        'Forecast Acumulado', 'IC Acum Mín', 'IC Acum Máx',
    ]:
        display_df[col] = display_df[col].apply(fmt_cop)

    st.dataframe(display_df, use_container_width=True, hide_index=True)


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
tabs = st.tabs(["🏠 Presentación", "📈 Primas", "📅 Pronóstico Detallado", "🏛️ FIANZAS", "📊 Presupuesto 2026"])

# (resto del archivo sin cambios...)

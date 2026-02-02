# -*- coding: utf-8 -*-
"""
Componente de sidebar con filtros
"""
import streamlit as st
import pandas as pd


def render_sidebar(df: pd.DataFrame, fecha_corte: pd.Timestamp) -> dict:
    """
    Renderiza sidebar con filtros simplificados.
    Solo filtro por LINEA_PLUS.
    """
    st.sidebar.header("🔍 Filtros")
    
    lineas_opts = ["TODAS"]
    if 'LINEA_PLUS' in df.columns:
        lineas_opts += sorted(df['LINEA_PLUS'].dropna().unique())
    
    linea_selected = st.sidebar.selectbox(
        "Línea +",
        lineas_opts,
        help="Filtra por línea de negocio principal"
    )
    
    anio_analisis = st.sidebar.number_input(
        "Año de análisis",
        min_value=2018,
        max_value=2100,
        value=fecha_corte.year,
        step=1,
        help="Año para realizar el análisis y pronósticos"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚙️ Ajustes de Forecast")
    
    ajuste_pct = st.sidebar.slider(
        "Ajuste conservador (%)",
        min_value=-20.0,
        max_value=10.0,
        step=0.5,
        value=0.0,
        help="Porcentaje de ajuste aplicado a las proyecciones"
    )
    
    nota_ajuste = st.sidebar.text_input(
        "Nota del ajuste (opcional)",
        value="",
        help="Comentario sobre el ajuste realizado"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📅 Información")
    st.sidebar.info(f"**Fecha de corte:**\n{fecha_corte.strftime('%d/%m/%Y')}")
    
    return {
        'linea_plus': linea_selected,
        'anio_analisis': int(anio_analisis),
        'ajuste_pct': float(ajuste_pct),
        'nota_ajuste': nota_ajuste,
        'conservative_factor': 1.0 + (ajuste_pct / 100.0)
    }

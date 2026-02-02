# -*- coding: utf-8 -*-
"""
Componente para gráficos Plotly
"""
import plotly.graph_objects as go
import pandas as pd


def render_forecast_chart(hist_df: pd.DataFrame, 
                         forecast_df: pd.DataFrame,
                         title: str = "Pronóstico de Primas") -> go.Figure:
    """Genera gráfico de pronóstico con histórico y predicción"""
    fig = go.Figure()
    
    if not hist_df.empty and 'FECHA' in hist_df.columns and 'Mensual' in hist_df.columns:
        fig.add_trace(go.Scatter(
            x=hist_df['FECHA'],
            y=hist_df['Mensual'],
            mode='lines',
            name='Histórico',
            line=dict(color='#38bdf8', width=2)
        ))
    
    if not forecast_df.empty and 'FECHA' in forecast_df.columns and 'Forecast_mensual' in forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=forecast_df['FECHA'],
            y=forecast_df['Forecast_mensual'],
            mode='lines+markers',
            name='Pronóstico',
            line=dict(color='#f59e0b', width=2, dash='dash')
        ))
        
        if 'IC_hi' in forecast_df.columns and 'IC_lo' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df['FECHA'],
                y=forecast_df['IC_hi'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_df['FECHA'],
                y=forecast_df['IC_lo'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(245, 158, 11, 0.2)',
                line=dict(width=0),
                name='IC 95%',
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        yaxis_title="COP",
        hovermode='x unified',
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        template="plotly_dark"
    )
    
    return fig

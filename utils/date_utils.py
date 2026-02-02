# -*- coding: utf-8 -*-
"""
Utilidades para fechas
"""
import pandas as pd
from datetime import date, datetime


def business_days_left(fecha_inicio, fecha_fin) -> int:
    """
    Calcula días hábiles restantes entre dos fechas.
    
    Args:
        fecha_inicio: fecha inicial (puede ser pd.Timestamp, date o datetime)
        fecha_fin: fecha final (puede ser pd.Timestamp, date o datetime)
        
    Returns:
        Número de días hábiles
    """
    # Convertir a pd.Timestamp para asegurar compatibilidad
    if isinstance(fecha_inicio, (date, datetime)):
        fecha_inicio = pd.Timestamp(fecha_inicio)
    if isinstance(fecha_fin, (date, datetime)):
        fecha_fin = pd.Timestamp(fecha_fin)
    
    # Normalizar a solo fecha (sin hora)
    fecha_inicio = pd.Timestamp(fecha_inicio.date())
    fecha_fin = pd.Timestamp(fecha_fin.date())
    
    if fecha_fin < fecha_inicio:
        return 0
    
    # Generar rango de días hábiles
    rng = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="B")
    return len(rng)


def get_month_range(year: int, month: int) -> tuple:
    """
    Obtiene primer y último día de un mes.
    
    Args:
        year: Año
        month: Mes (1-12)
        
    Returns:
        Tupla (primer_dia, ultimo_dia)
    """
    primer_dia = pd.Timestamp(year=year, month=month, day=1)
    ultimo_dia = primer_dia + pd.offsets.MonthEnd(0)
    return primer_dia, ultimo_dia


def ensure_monthly(ts: pd.Series) -> pd.Series:
    """
    Asegura frecuencia mensual en una serie temporal.
    
    Args:
        ts: Serie temporal
        
    Returns:
        Serie con frecuencia mensual
    """
    ts = ts.asfreq("MS")
    ts = ts.interpolate(method="linear", limit_area="inside")
    return ts

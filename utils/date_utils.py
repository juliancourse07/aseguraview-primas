# -*- coding: utf-8 -*-
"""
Utilidades para fechas
"""
import pandas as pd
from datetime import date


def business_days_left(fecha_inicio: date, fecha_fin: date) -> int:
    """Calcula días hábiles restantes"""
    if fecha_fin < fecha_inicio:
        return 0
    
    rng = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="B")
    return len(rng)


def get_month_range(year: int, month: int) -> tuple:
    """Obtiene primer y último día de un mes"""
    primer_dia = pd.Timestamp(year=year, month=month, day=1)
    ultimo_dia = primer_dia + pd.offsets.MonthEnd(0)
    return primer_dia, ultimo_dia


def ensure_monthly(ts: pd.Series) -> pd.Series:
    """Asegura frecuencia mensual"""
    ts = ts.asfreq("MS")
    ts = ts.interpolate(method="linear", limit_area="inside")
    return ts

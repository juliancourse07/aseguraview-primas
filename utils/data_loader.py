# -*- coding: utf-8 -*-
"""
Carga de datos desde Google Sheets
"""
import pandas as pd
import streamlit as st
from config import SHEET_GID_DATOS, SHEET_GID_FECHA_CORTE, SHEET_ID


def gsheet_csv_url(sheet_id: str, gid: int) -> str:
    """Genera URL para leer Google Sheet como CSV usando GID."""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=300, show_spinner=False)
def load_cutoff_date(sheet_id: str = SHEET_ID, 
                     gid: int = SHEET_GID_FECHA_CORTE) -> pd.Timestamp:
    """
    Carga fecha de corte desde la hoja configurada por GID.
    
    Args:
        sheet_id: ID del Google Sheet
        gid: GID de la hoja (por defecto hoja de fecha de corte)
        
    Returns:
        pd.Timestamp con la fecha de corte
    """
    url = gsheet_csv_url(sheet_id, gid)
    
    try:
        df = pd.read_csv(url, header=None)
        raw = str(df.iloc[0, 0]).strip() if not df.empty else ""
        
        # Parsear fecha con formato colombiano (día primero)
        ts = pd.to_datetime(raw, dayfirst=True, errors='coerce')
        
        if pd.isna(ts):
            st.warning(f"⚠️ Fecha inválida en hoja GID {gid}: '{raw}'. Usando fecha actual.")
            ts = pd.Timestamp.today().normalize()
        
        return pd.Timestamp(ts.date())
    
    except Exception as e:
        st.error(f"❌ Error cargando fecha de corte desde hoja GID {gid}: {e}")
        return pd.Timestamp.today().normalize()


@st.cache_data(ttl=1800, show_spinner=False)
def load_data(sheet_id: str = SHEET_ID, 
              gid: int = SHEET_GID_DATOS) -> pd.DataFrame:
    """
    Carga datos principales desde la hoja configurada por GID.
    
    Args:
        sheet_id: ID del Google Sheet
        gid: GID de la hoja (por defecto hoja de datos)
        
    Returns:
        DataFrame con datos normalizados
    """
    url = gsheet_csv_url(sheet_id, gid)
    
    try:
        df = pd.read_csv(url)
        
        if df.empty:
            st.error(f"❌ La hoja con GID {gid} está vacía. Verifica los datos en Google Sheets.")
            st.stop()
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error cargando datos desde hoja GID {gid}: {e}")
        st.stop()

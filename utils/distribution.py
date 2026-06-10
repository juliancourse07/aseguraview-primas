# -*- coding: utf-8 -*-
"""Cálculo y render de la distribución mensual del faltante proyectado."""

from __future__ import annotations

import html

import numpy as np
import pandas as pd

from utils.formatters import fmt_cop
from utils.performance import calculate_increments, fast_proportional_distribution

MONTH_ABBR = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}

MONTH_HEADER = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE",
}

POSITIVE_INCREMENT_COLOR = '#ef4444'
NEGATIVE_INCREMENT_COLOR = '#15803d'
POSITIVE_PCT_TEXT_COLOR = '#dc2626'
NEGATIVE_PCT_TEXT_COLOR = '#15803d'
POSITIVE_PCT_BG = '#fef2f2'
NEGATIVE_PCT_BG = '#dcfce7'


def get_remaining_months(cutoff_month: int, meses_quarter: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    """Devuelve meses restantes del año respetando el filtro de quarter."""
    quarter_months = set(int(month) for month in meses_quarter)
    return tuple(month for month in range(int(cutoff_month), 13) if month in quarter_months)


def _previous_cutoff_period(ref_year: int, cutoff_date: pd.Timestamp) -> tuple[int, int]:
    """Obtiene el año/mes inmediatamente anterior al corte."""
    previous_month = int(cutoff_date.month) - 1
    if previous_month >= 1:
        return int(ref_year), previous_month
    return int(ref_year) - 1, 12


def _accumulated_period_label(ref_year: int, cutoff_date: pd.Timestamp) -> str:
    """Construye etiqueta del período acumulado usado para el faltante."""
    previous_year, previous_month = _previous_cutoff_period(ref_year, cutoff_date)
    if previous_month == 12 and previous_year != int(ref_year):
        return f"Enero - {MONTH_HEADER[previous_month].title()} {previous_year}"
    return f"Enero - {MONTH_HEADER[previous_month].title()} {previous_year}"


def build_monthly_distribution(
    df_filtered: pd.DataFrame,
    ref_year: int,
    cutoff_date: pd.Timestamp,
    meses_quarter: tuple[int, ...] | list[int],
) -> tuple[pd.DataFrame, tuple[int, ...]]:
    """Distribuye el faltante proyectado acumulado por sucursal × línea."""
    required_cols = {'FECHA', 'Suc_agrupada', 'LINEA_PLUS', 'PRESUPUESTO', 'IMP_PRIMA'}
    if not required_cols.issubset(df_filtered.columns):
        return pd.DataFrame(), tuple()

    remaining_months = get_remaining_months(int(cutoff_date.month), meses_quarter)
    if not remaining_months:
        return pd.DataFrame(), tuple()

    previous_year, previous_month = _previous_cutoff_period(ref_year, cutoff_date)

    df_work = df_filtered[['FECHA', 'Suc_agrupada', 'LINEA_PLUS', 'PRESUPUESTO', 'IMP_PRIMA']].copy()
    df_work = df_work[df_work['LINEA_PLUS'].notna()].copy()
    df_work['PRESUPUESTO'] = pd.to_numeric(df_work['PRESUPUESTO'], errors='coerce').fillna(0.0)
    df_work['IMP_PRIMA'] = pd.to_numeric(df_work['IMP_PRIMA'], errors='coerce').fillna(0.0)

    df_ytd = df_work[
        (df_work['FECHA'].dt.year == previous_year) &
        (df_work['FECHA'].dt.month <= previous_month)
    ]
    if df_ytd.empty:
        return pd.DataFrame(), remaining_months

    faltante_by_row = (
        df_ytd
        .groupby(['Suc_agrupada', 'LINEA_PLUS'], dropna=False)[['PRESUPUESTO', 'IMP_PRIMA']]
        .sum()
        .rename(columns={
            'PRESUPUESTO': 'Presupuesto_Acumulado_Anterior',
            'IMP_PRIMA': 'Produccion_Acumulada_Anterior',
        })
    )
    faltante_by_row['Faltante_Proyectado'] = (
        faltante_by_row['Presupuesto_Acumulado_Anterior'] -
        faltante_by_row['Produccion_Acumulada_Anterior']
    )

    df_budget = df_work[
        (df_work['FECHA'].dt.year == int(ref_year)) &
        (df_work['FECHA'].dt.month.isin(remaining_months))
    ][['Suc_agrupada', 'LINEA_PLUS', 'FECHA', 'PRESUPUESTO']].copy()
    if df_budget.empty:
        return pd.DataFrame(), remaining_months

    df_budget['MES'] = df_budget['FECHA'].dt.month

    monthly_budget = (
        df_budget
        .groupby(['Suc_agrupada', 'LINEA_PLUS', 'MES'], dropna=False)['PRESUPUESTO']
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=list(remaining_months), fill_value=0.0)
    )
    if monthly_budget.empty:
        return pd.DataFrame(), remaining_months

    base_result = monthly_budget.join(faltante_by_row, how='outer').fillna(0.0)
    base_result = base_result[
        (base_result['Faltante_Proyectado'] != 0) |
        (base_result[list(remaining_months)].sum(axis=1) != 0)
    ]
    if base_result.empty:
        return pd.DataFrame(), remaining_months

    budget_matrix = base_result[list(remaining_months)].to_numpy(dtype=np.float64)
    faltante_totals = base_result['Faltante_Proyectado'].to_numpy(dtype=np.float64)
    distribution_matrix = fast_proportional_distribution(faltante_totals, budget_matrix)
    increment_pct_matrix = calculate_increments(
        distribution_matrix.ravel(),
        budget_matrix.ravel(),
    ).reshape(distribution_matrix.shape)
    objective_matrix = budget_matrix + distribution_matrix

    result = pd.DataFrame({
        'Suc_agrupada': base_result.index.get_level_values('Suc_agrupada'),
        'LINEA_PLUS': base_result.index.get_level_values('LINEA_PLUS'),
        'Faltante_Proyectado': faltante_totals,
        'Presupuesto_Total_Anio': (
            base_result['Presupuesto_Acumulado_Anterior'].to_numpy(dtype=np.float64) +
            objective_matrix.sum(axis=1)
        ),
    })

    for idx, month in enumerate(remaining_months):
        prefix = MONTH_ABBR[month]
        monthly_budget_values = budget_matrix[:, idx]
        result[f'{prefix}_Presup_Original'] = monthly_budget_values
        result[f'{prefix}_Objetivo_Nuevo'] = objective_matrix[:, idx]
        result[f'{prefix}_Incremento_Pct'] = increment_pct_matrix[:, idx]

    result = result.sort_values(
        by=['Faltante_Proyectado', 'Suc_agrupada', 'LINEA_PLUS'],
        ascending=[False, True, True],
        kind='mergesort',
    ).reset_index(drop=True)
    return result, remaining_months


def append_distribution_totals(
    df_distribution: pd.DataFrame,
    remaining_months: tuple[int, ...] | list[int],
) -> pd.DataFrame:
    """Agrega fila TOTAL para exportación/visualización."""
    if df_distribution.empty:
        return df_distribution.copy()

    total_row = {
        'Suc_agrupada': 'TOTAL',
        'LINEA_PLUS': '',
        'Faltante_Proyectado': float(df_distribution['Faltante_Proyectado'].sum()),
        'Presupuesto_Total_Anio': float(df_distribution['Presupuesto_Total_Anio'].sum()),
    }

    for month in remaining_months:
        prefix = MONTH_ABBR[month]
        budget_total = float(df_distribution[f'{prefix}_Presup_Original'].sum())
        objetivo_total = float(df_distribution[f'{prefix}_Objetivo_Nuevo'].sum())
        total_row[f'{prefix}_Presup_Original'] = budget_total
        total_row[f'{prefix}_Objetivo_Nuevo'] = objetivo_total
        total_row[f'{prefix}_Incremento_Pct'] = _safe_increment_pct(objetivo_total - budget_total, budget_total)

    return pd.concat([df_distribution, pd.DataFrame([total_row])], ignore_index=True)

def _fmt_signed_pct(value: float) -> str:
    sign = '+' if value > 0 else '-' if value < 0 else ''
    return f"{sign}{abs(float(value)):.1f}%"


def _safe_increment_pct(deficit_value: float, budget_value: float) -> float:
    return float((deficit_value / budget_value) * 100.0) if budget_value else 0.0


def build_distribution_html(
    df_distribution: pd.DataFrame,
    remaining_months: tuple[int, ...] | list[int],
    ref_year: int,
    cutoff_date: pd.Timestamp,
) -> str:
    """Construye el HTML de la matriz desplegable mensual."""
    if df_distribution.empty or not remaining_months:
        return ""

    df_export = append_distribution_totals(df_distribution, remaining_months)
    value_suffixes = ('Faltante_Proyectado', 'Presupuesto_Total_Anio', 'Presup_Original', 'Objetivo_Nuevo')
    for col in df_export.columns:
        if col.endswith(value_suffixes):
            df_export[f'{col}__fmt'] = df_export[col].map(fmt_cop)
        elif col.endswith('Incremento_Pct'):
            df_export[f'{col}__fmt'] = df_export[col].map(_fmt_signed_pct)

    header_months = ''.join(
        f'<th colspan="3" style="padding:12px;border:1px solid #2d5a7f;background:#0a5a8a;min-width:330px;">{MONTH_HEADER[month]}</th>'
        for month in remaining_months
    )
    header_metrics = ''.join(
        (
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Presup.<br/>Original</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Objetivo<br/>Nuevo</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Increm.<br/>%</th>'
        )
        for _month in remaining_months
    )

    sticky_styles = {
        'col1': 'position:sticky;left:0;min-width:210px;max-width:210px;background:#ffffff;z-index:5;box-shadow:2px 0 4px rgba(15,23,42,0.08);',
        'col2': 'position:sticky;left:210px;min-width:150px;max-width:150px;background:#ffffff;z-index:5;box-shadow:2px 0 4px rgba(15,23,42,0.08);',
        'col3': 'position:sticky;left:360px;min-width:190px;max-width:190px;background:#ffffff;z-index:5;box-shadow:2px 0 4px rgba(15,23,42,0.08);',
        'col4': 'position:sticky;left:550px;min-width:210px;max-width:210px;background:#ffffff;z-index:5;box-shadow:2px 0 4px rgba(15,23,42,0.08);',
        'head1': 'position:sticky;left:0;background:#1e3a5f;z-index:12;',
        'head2': 'position:sticky;left:210px;background:#1e3a5f;z-index:12;',
        'head3': 'position:sticky;left:360px;background:#1e3a5f;z-index:12;',
        'head4': 'position:sticky;left:550px;background:#1e3a5f;z-index:12;',
        'total1': 'position:sticky;left:0;background:rgba(56,189,248,0.15);z-index:9;',
        'total2': 'position:sticky;left:210px;background:rgba(56,189,248,0.15);z-index:9;',
        'total3': 'position:sticky;left:360px;background:rgba(56,189,248,0.15);z-index:9;',
        'total4': 'position:sticky;left:550px;background:rgba(56,189,248,0.15);z-index:9;',
    }

    body_rows = []
    data_rows = df_export.iloc[:-1]
    for row in data_rows.to_dict(orient='records'):
        row_cells = [
            f'<td style="padding:10px;border:1px solid #e2e8f0;{sticky_styles["col1"]}">{html.escape(str(row["Suc_agrupada"]))}</td>',
            f'<td style="padding:10px;border:1px solid #e2e8f0;{sticky_styles["col2"]}">{html.escape(str(row["LINEA_PLUS"]))}</td>',
            f'<td style="padding:10px;border:1px solid #e2e8f0;font-weight:700;color:#ef4444;text-align:right;{sticky_styles["col3"]}">{row["Faltante_Proyectado__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #e2e8f0;font-weight:700;text-align:right;background:#eff6ff;{sticky_styles["col4"]}">{row["Presupuesto_Total_Anio__fmt"]}</td>',
        ]
        for month in remaining_months:
            prefix = MONTH_ABBR[month]
            increment_pct = row[f'{prefix}_Incremento_Pct']
            pct_color = POSITIVE_PCT_TEXT_COLOR if increment_pct >= 0 else NEGATIVE_PCT_TEXT_COLOR
            pct_bg = POSITIVE_PCT_BG if increment_pct >= 0 else NEGATIVE_PCT_BG
            row_cells.extend([
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;">{row[f"{prefix}_Presup_Original__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;font-weight:600;background:#dbeafe;">{row[f"{prefix}_Objetivo_Nuevo__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;color:{pct_color};font-weight:700;background:{pct_bg};">{row[f"{prefix}_Incremento_Pct__fmt"]}</td>',
            ])
        body_rows.append(f'<tr style="border-bottom:1px solid #e2e8f0;">{"".join(row_cells)}</tr>')

    total = df_export.iloc[-1]
    total_cells = [
        f'<td style="padding:12px;border:1px solid #38bdf8;font-weight:700;{sticky_styles["total1"]}">TOTAL</td>',
        f'<td style="padding:12px;border:1px solid #38bdf8;{sticky_styles["total2"]}"></td>',
        f'<td style="padding:12px;border:1px solid #38bdf8;color:#ef4444;text-align:right;{sticky_styles["total3"]}">{total["Faltante_Proyectado__fmt"]}</td>',
        f'<td style="padding:12px;border:1px solid #38bdf8;text-align:right;{sticky_styles["total4"]}">{total["Presupuesto_Total_Anio__fmt"]}</td>',
    ]
    for month in remaining_months:
        prefix = MONTH_ABBR[month]
        total_cells.extend([
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;">{total[f"{prefix}_Presup_Original__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;">{total[f"{prefix}_Objetivo_Nuevo__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;color:#dc2626;">{total[f"{prefix}_Incremento_Pct__fmt"]}</td>',
        ])

    total_faltante_fmt = total['Faltante_Proyectado__fmt']
    period_text = f"{MONTH_HEADER[remaining_months[0]].title()} - {MONTH_HEADER[remaining_months[-1]].title()} {ref_year}"
    accumulated_label = _accumulated_period_label(ref_year, cutoff_date)

    return f"""
<style>
.distribucion-container {{
  overflow-x: auto;
  overflow-y: visible;
  max-width: 100%;
  margin-top: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  -webkit-overflow-scrolling: touch;
  scrollbar-width: auto;
  scrollbar-color: #38bdf8 #f1f5f9;
}}
.distribucion-container::-webkit-scrollbar {{
  height: 12px;
  background-color: #f1f5f9;
  border-radius: 6px;
}}
.distribucion-container::-webkit-scrollbar-thumb {{
  background: linear-gradient(90deg, #38bdf8, #0284c7);
  border-radius: 6px;
  border: 2px solid #f1f5f9;
}}
.distribucion-container::-webkit-scrollbar-thumb:hover {{
  background: linear-gradient(90deg, #0284c7, #075985);
}}
.distribucion-container::-webkit-scrollbar-track {{
  background-color: #f1f5f9;
  border-radius: 6px;
}}
</style>
<div style="margin-top:20px;">
  <div style="background:linear-gradient(135deg, #033b63 0%, #0a5a8a 100%);padding:16px;border-radius:8px 8px 0 0;color:#fff;">
    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
      <h4 style="margin:0;font-size:18px;">📅 Distribución Mensual del Faltante Proyectado</h4>
      <div style="font-size:12px;padding:6px 10px;background:rgba(255,255,255,0.12);border-radius:999px;">↔️ Desliza para ver todos los meses</div>
    </div>
    <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:12px;">
      <div>
        <div style="font-size:12px;opacity:0.8;">Faltante Total a Distribuir</div>
        <div style="font-size:24px;font-weight:700;">{total_faltante_fmt}</div>
        <div style="font-size:11px;opacity:0.7;">(Calculado {html.escape(accumulated_label)})</div>
      </div>
      <div>
        <div style="font-size:12px;opacity:0.8;">Período de Distribución</div>
        <div style="font-size:16px;font-weight:600;">{html.escape(period_text)}</div>
      </div>
      <div>
        <div style="font-size:12px;opacity:0.8;">Meses Restantes</div>
        <div style="font-size:16px;font-weight:600;">{len(remaining_months)} meses</div>
      </div>
    </div>
    <p style="font-size:13px;margin:12px 0 0 0;opacity:0.9;line-height:1.5;">
      ℹ️ El <strong>Faltante Proyectado</strong> es la diferencia entre el presupuesto y la producción real
      acumulada hasta el mes anterior al corte.
      Se distribuye proporcionalmente en los meses visibles según el peso del presupuesto mensual.
      El <strong>Incremento %</strong> indica cuánto más debe producir cada sucursal/línea
      sobre su presupuesto original para compensar su parte del faltante.
    </p>
    <div style="margin-top:12px;padding:8px;background:rgba(255,255,255,0.1);border-radius:4px;font-size:12px;">
      💡 <strong>Tip:</strong> usa la barra horizontal inferior para navegar la matriz y mantener visibles las primeras columnas.
    </div>
  </div>
  <div class="distribucion-container">
  <table style="width:max-content;min-width:100%;border-collapse:separate;border-spacing:0;font-size:12px;background:#fff;">
    <thead>
      <tr style="background:#1e3a5f;color:#fff;">
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;min-width:210px;{sticky_styles["head1"]}">Sucursal</th>
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;min-width:150px;{sticky_styles["head2"]}">Línea</th>
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;min-width:190px;{sticky_styles["head3"]}">Faltante<br/>Proyectado</th>
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;min-width:210px;{sticky_styles["head4"]}">Presupuesto<br/>Total Año</th>
        {header_months}
      </tr>
      <tr style="background:#1e3a5f;color:#fff;">{header_metrics}</tr>
    </thead>
    <tbody>{''.join(body_rows)}</tbody>
    <tfoot>
      <tr style="background:rgba(56,189,248,0.15);border-top:3px solid #38bdf8;font-weight:700;">
        {''.join(total_cells)}
      </tr>
    </tfoot>
  </table>
  </div>
  <div style="padding:14px;background:#f8fafc;border-top:2px solid #e2e8f0;border-radius:0 0 8px 8px;">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;font-size:12px;line-height:1.6;">
      <div><strong>💰 Presup. Original:</strong> Presupuesto inicial del mes</div>
      <div><strong>🎯 Objetivo Nuevo:</strong> Presupuesto original más la porción del faltante distribuido</div>
      <div><strong>📈 Incremento %:</strong> Porcentaje adicional requerido</div>
      <div><strong>✅ Presupuesto Total Año:</strong> Presupuesto acumulado hasta el corte anterior + nuevos objetivos del período mostrado</div>
    </div>
    <div style="margin-top:12px;padding:10px;background:#fff3cd;border-left:4px solid #ffc107;border-radius:4px;">
      <strong>⚠️ Interpretación:</strong> Un <strong>Incremento %</strong> positivo indica cuánto más debe producirse sobre el presupuesto original del mes.
    </div>
  </div>
</div>
"""

# -*- coding: utf-8 -*-
"""Cálculo y render de la distribución mensual del déficit."""

from __future__ import annotations

import html

import numpy as np
import pandas as pd

from utils.formatters import fmt_cop
from utils.performance import fast_proportional_distribution, calculate_increments

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


def get_remaining_months(cutoff_month: int, meses_quarter: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    """Devuelve meses restantes del año respetando el filtro de quarter."""
    quarter_months = set(int(month) for month in meses_quarter)
    return tuple(month for month in range(int(cutoff_month), 13) if month in quarter_months)


def build_monthly_distribution(
    df_filtered: pd.DataFrame,
    df_resumen: pd.DataFrame,
    metric_col: str,
    ref_year: int,
    cutoff_month: int,
    meses_quarter: tuple[int, ...] | list[int],
) -> tuple[pd.DataFrame, tuple[int, ...]]:
    """Distribuye el déficit de línea en meses restantes por sucursal × línea."""
    required_cols = {'FECHA', 'Suc_agrupada', 'LINEA_PLUS', 'PRESUPUESTO'}
    if not required_cols.issubset(df_filtered.columns):
        return pd.DataFrame(), tuple()
    if 'LINEA_PLUS' not in df_resumen.columns or metric_col not in df_resumen.columns:
        return pd.DataFrame(), tuple()

    remaining_months = get_remaining_months(cutoff_month, meses_quarter)
    if not remaining_months:
        return pd.DataFrame(), tuple()

    metric_by_line = df_resumen.copy()
    metric_by_line = metric_by_line[metric_by_line['LINEA_PLUS'].notna()].copy()
    metric_by_line = metric_by_line[
        ~metric_by_line['LINEA_PLUS'].astype(str).str.upper().isin({'TOTAL', 'TOTAL LÍNEA'})
    ]
    if metric_by_line.empty:
        return pd.DataFrame(), remaining_months

    metric_by_line[metric_col] = pd.to_numeric(metric_by_line[metric_col], errors='coerce').fillna(0.0)
    metric_total_by_line = metric_by_line.groupby('LINEA_PLUS', dropna=False)[metric_col].sum()

    df_budget = df_filtered[
        (df_filtered['FECHA'].dt.year == int(ref_year)) &
        (df_filtered['FECHA'].dt.month.isin(remaining_months))
    ][['Suc_agrupada', 'LINEA_PLUS', 'FECHA', 'PRESUPUESTO']].copy()
    if df_budget.empty:
        return pd.DataFrame(), remaining_months

    df_budget['PRESUPUESTO'] = pd.to_numeric(df_budget['PRESUPUESTO'], errors='coerce').fillna(0.0)
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

    line_budget_totals = monthly_budget.groupby(level='LINEA_PLUS').sum().sum(axis=1)
    row_budget_totals = monthly_budget.sum(axis=1).to_numpy(dtype=np.float64)
    row_lineas = monthly_budget.index.get_level_values('LINEA_PLUS')
    metric_total_rows = row_lineas.map(metric_total_by_line).to_numpy(dtype=np.float64)
    budget_total_rows = row_lineas.map(line_budget_totals).to_numpy(dtype=np.float64)

    row_deficit_totals = np.divide(
        metric_total_rows * row_budget_totals,
        budget_total_rows,
        out=np.zeros_like(row_budget_totals, dtype=np.float64),
        where=budget_total_rows != 0,
    )

    budget_matrix = monthly_budget.to_numpy(dtype=np.float64)
    distribution_matrix = fast_proportional_distribution(row_deficit_totals, budget_matrix)
    increment_pct_matrix = calculate_increments(
        distribution_matrix.ravel(),
        budget_matrix.ravel(),
    ).reshape(distribution_matrix.shape)

    result = pd.DataFrame({
        'Suc_agrupada': monthly_budget.index.get_level_values('Suc_agrupada'),
        'LINEA_PLUS': row_lineas,
        'Deficit_Total': distribution_matrix.sum(axis=1),
    })

    for idx, month in enumerate(remaining_months):
        prefix = MONTH_ABBR[month]
        monthly_deficit = distribution_matrix[:, idx]
        monthly_budget_values = budget_matrix[:, idx]
        result[f'{prefix}_Deficit'] = monthly_deficit
        result[f'{prefix}_Presup_Original'] = monthly_budget_values
        result[f'{prefix}_Objetivo_Nuevo'] = monthly_budget_values + monthly_deficit
        result[f'{prefix}_Incremento_$'] = monthly_deficit
        result[f'{prefix}_Incremento_Pct'] = increment_pct_matrix[:, idx]

    result = result.sort_values(
        by=['Deficit_Total', 'Suc_agrupada', 'LINEA_PLUS'],
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
        'Deficit_Total': float(df_distribution['Deficit_Total'].sum()),
    }

    for month in remaining_months:
        prefix = MONTH_ABBR[month]
        deficit_total = float(df_distribution[f'{prefix}_Deficit'].sum())
        budget_total = float(df_distribution[f'{prefix}_Presup_Original'].sum())
        total_row[f'{prefix}_Deficit'] = deficit_total
        total_row[f'{prefix}_Presup_Original'] = budget_total
        total_row[f'{prefix}_Objetivo_Nuevo'] = budget_total + deficit_total
        total_row[f'{prefix}_Incremento_$'] = deficit_total
        total_row[f'{prefix}_Incremento_Pct'] = (deficit_total / budget_total * 100.0) if budget_total else 0.0

    return pd.concat([df_distribution, pd.DataFrame([total_row])], ignore_index=True)


def _fmt_signed_cop(value: float) -> str:
    sign = '+' if value > 0 else '-' if value < 0 else ''
    return f"{sign}{fmt_cop(abs(value))}" if sign else fmt_cop(0)


def _fmt_signed_pct(value: float) -> str:
    sign = '+' if value > 0 else '-' if value < 0 else ''
    return f"{sign}{abs(float(value)):.1f}%"


def build_distribution_html(
    df_distribution: pd.DataFrame,
    remaining_months: tuple[int, ...] | list[int],
    period_label: str,
    ref_year: int,
) -> str:
    """Construye el HTML de la matriz desplegable mensual."""
    if df_distribution.empty:
        return ""

    df_export = append_distribution_totals(df_distribution, remaining_months)
    value_suffixes = ('Deficit_Total', 'Deficit', 'Presup_Original', 'Objetivo_Nuevo')
    for col in df_export.columns:
        if col.endswith(value_suffixes):
            df_export[f'{col}__fmt'] = df_export[col].map(fmt_cop)
        elif col.endswith('Incremento_$'):
            df_export[f'{col}__fmt'] = df_export[col].map(_fmt_signed_cop)
        elif col.endswith('Incremento_Pct'):
            df_export[f'{col}__fmt'] = df_export[col].map(_fmt_signed_pct)

    header_months = ''.join(
        f'<th colspan="5" style="padding:12px;border:1px solid #2d5a7f;background:#0a5a8a;">{MONTH_HEADER[month]}</th>'
        for month in remaining_months
    )
    header_metrics = ''.join(
        (
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Déficit<br/>Mes</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Presup.<br/>Original</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Objetivo<br/>Nuevo</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Increm.<br/>$</th>'
            '<th style="padding:8px;border:1px solid #2d5a7f;font-size:11px;">Increm.<br/>%</th>'
        )
        for _month in remaining_months
    )

    body_rows = []
    data_rows = df_export.iloc[:-1]
    for row in data_rows.to_dict(orient='records'):
        row_cells = [
            f'<td style="padding:10px;border:1px solid #e2e8f0;">{html.escape(str(row["Suc_agrupada"]))}</td>',
            f'<td style="padding:10px;border:1px solid #e2e8f0;">{html.escape(str(row["LINEA_PLUS"]))}</td>',
            f'<td style="padding:10px;border:1px solid #e2e8f0;font-weight:700;color:#ef4444;text-align:right;">{row["Deficit_Total__fmt"]}</td>',
        ]
        for month in remaining_months:
            prefix = MONTH_ABBR[month]
            increment_pct = row[f'{prefix}_Incremento_Pct']
            pct_color = '#dc2626' if increment_pct >= 0 else '#15803d'
            pct_bg = '#fef2f2' if increment_pct >= 0 else '#dcfce7'
            amount_color = '#ef4444' if row[f'{prefix}_Incremento_$'] >= 0 else '#15803d'
            row_cells.extend([
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;background:#fef2f2;">{row[f"{prefix}_Deficit__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;">{row[f"{prefix}_Presup_Original__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;font-weight:600;background:#dbeafe;">{row[f"{prefix}_Objetivo_Nuevo__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;color:{amount_color};font-weight:600;">{row[f"{prefix}_Incremento_$__fmt"]}</td>',
                f'<td style="padding:8px;border:1px solid #e2e8f0;text-align:right;color:{pct_color};font-weight:700;background:{pct_bg};">{row[f"{prefix}_Incremento_Pct__fmt"]}</td>',
            ])
        body_rows.append(f'<tr style="border-bottom:1px solid #e2e8f0;">{"".join(row_cells)}</tr>')

    total = df_export.iloc[-1]
    total_cells = [
        '<td colspan="2" style="padding:12px;border:1px solid #38bdf8;">TOTAL</td>',
        f'<td style="padding:12px;border:1px solid #38bdf8;color:#ef4444;text-align:right;">{total["Deficit_Total__fmt"]}</td>',
    ]
    for month in remaining_months:
        prefix = MONTH_ABBR[month]
        total_cells.extend([
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;">{total[f"{prefix}_Deficit__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;">{total[f"{prefix}_Presup_Original__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;">{total[f"{prefix}_Objetivo_Nuevo__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;color:#ef4444;">{total[f"{prefix}_Incremento_$__fmt"]}</td>',
            f'<td style="padding:10px;border:1px solid #38bdf8;text-align:right;color:#dc2626;">{total[f"{prefix}_Incremento_Pct__fmt"]}</td>',
        ])

    total_deficit_fmt = total['Deficit_Total__fmt']
    period_text = f"{period_label} {ref_year}".strip()

    return f"""
<div class="distribucion-container" style="overflow-x:auto;margin-top:20px;">
  <div style="background:linear-gradient(135deg, #033b63 0%, #0a5a8a 100%);padding:16px;border-radius:8px 8px 0 0;color:#fff;">
    <h4 style="margin:0 0 8px 0;font-size:18px;">📅 Distribución Mensual del Déficit</h4>
    <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:12px;">
      <div>
        <div style="font-size:12px;opacity:0.8;">Déficit Total a Distribuir</div>
        <div style="font-size:24px;font-weight:700;">{total_deficit_fmt}</div>
      </div>
      <div>
        <div style="font-size:12px;opacity:0.8;">Período</div>
        <div style="font-size:16px;font-weight:600;">{html.escape(period_text)}</div>
      </div>
      <div>
        <div style="font-size:12px;opacity:0.8;">Meses Restantes</div>
        <div style="font-size:16px;font-weight:600;">{len(remaining_months)} meses</div>
      </div>
    </div>
    <p style="font-size:13px;margin:12px 0 0 0;opacity:0.9;line-height:1.5;">
      ℹ️ La distribución se basa en el peso del presupuesto mensual.
      El <strong>Incremento %</strong> indica cuánto más debe producir cada sucursal/línea
      sobre su presupuesto original para compensar su parte del déficit.
    </p>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <thead>
      <tr style="background:#1e3a5f;color:#fff;">
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;">Sucursal</th>
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;">Línea</th>
        <th rowspan="2" style="padding:12px;border:1px solid #2d5a7f;">Déficit Total</th>
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
  <div style="padding:14px;background:#f8fafc;border-top:2px solid #e2e8f0;border-radius:0 0 8px 8px;">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;font-size:12px;line-height:1.6;">
      <div><strong>📊 Déficit Mes:</strong> Porción del déficit asignada a ese mes</div>
      <div><strong>💰 Presup. Original:</strong> Presupuesto inicial del mes</div>
      <div><strong>🎯 Objetivo Nuevo:</strong> Meta ajustada (Original + Déficit)</div>
      <div><strong>📈 Incremento %:</strong> Porcentaje adicional requerido</div>
    </div>
    <div style="margin-top:12px;padding:10px;background:#fff3cd;border-left:4px solid #ffc107;border-radius:4px;">
      <strong>⚠️ Interpretación:</strong> Un <strong>Incremento %</strong> positivo indica cuánto más debe producirse sobre el presupuesto original del mes.
    </div>
  </div>
</div>
"""

"""
Performance Analytics Engine — calculates production-grade trading metrics.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import math
from datetime import datetime, time
from typing import Any

def calculate_strategy_metrics(trades: list[dict[str, Any]], initial_capital: float) -> dict[str, Any]:
    """
    Calculate comprehensive performance metrics from trade history.
    """
    if not trades:
        return {
            "total": {},
            "rolling": {},
            "risk": {},
            "confidence": {},
            "segmented": {},
            "warnings": []
        }

    df = pd.DataFrame(trades)
    warnings = []
    
    # Ensure numeric types
    df['points'] = pd.to_numeric(df['points'], errors='coerce').fillna(0)
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce').fillna(0)
    df['entry_dt'] = pd.to_datetime(df['entry_time'])
    df['exit_dt'] = pd.to_datetime(df['exit_time'])
    
    def get_summary(sub_df: pd.DataFrame, segment_name: str = ""):
        if sub_df.empty: return None
        wins = sub_df[sub_df['points'] > 0]
        losses = sub_df[sub_df['points'] <= 0]
        n = len(sub_df)
        wr = (len(wins) / n) * 100
        gp = wins['points'].sum()
        gl = abs(losses['points'].sum())
        pf = (gp / gl) if gl > 0 else (gp if gp > 0 else 0)
        aw = wins['points'].mean() if len(wins) > 0 else 0
        al = abs(losses['points'].mean()) if len(losses) > 0 else 0
        exp = ((wr / 100) * aw) - (((100 - wr) / 100) * al)
        
        # Sample Sufficiency Warning
        if n < 20 and segment_name:
            warnings.append(f"Sample size too small for {segment_name} ({n} trades). Metrics may be unreliable.")
            
        # 95% Confidence Interval for Win Rate
        p = wr / 100
        se = math.sqrt((p * (1 - p)) / n) if n > 0 else 0
        ci_lower = max(0, (p - 1.96 * se) * 100)
        ci_upper = min(100, (p + 1.96 * se) * 100)
        
        return {
            "trades": n,
            "win_rate": round(wr, 2),
            "win_rate_ci": [round(ci_lower, 2), round(ci_upper, 2)],
            "profit_factor": round(pf, 2),
            "expectancy": round(exp, 2),
            "avg_win": round(aw, 2),
            "avg_loss": round(al, 2),
            "reliable": n >= 20
        }

    # Total Metrics
    total_metrics = get_summary(df, "Aggregate")
    
    # --- Rolling Metrics ---
    df['rolling_exp_20'] = df['points'].rolling(window=20).mean()
    df['rolling_exp_50'] = df['points'].rolling(window=50).mean()
    
    rolling_20_std = df['rolling_exp_20'].std()
    rolling_20_mean = df['rolling_exp_20'].mean()
    stability_score = (rolling_20_mean / rolling_20_std) if rolling_20_std > 0 else 0
    
    # --- Capital Curve Risk Metrics ---
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity'] = initial_capital + df['cum_pnl']
    df['peak'] = df['equity'].cummax()
    df['drawdown_pct'] = (df['peak'] - df['equity']) / df['peak'] * 100
    df['drawdown_abs'] = df['peak'] - df['equity']
    
    max_drawdown_pct = df['drawdown_pct'].max()
    max_drawdown_abs = df['drawdown_abs'].max()
    ulcer_index = math.sqrt((df['drawdown_pct']**2).mean())
    net_profit = df['pnl'].sum()
    recovery_factor = (net_profit / max_drawdown_abs) if max_drawdown_abs > 0 else 0
    
    in_drawdown = df['drawdown_abs'] > 0
    df['dd_streak'] = in_drawdown.ne(in_drawdown.shift()).cumsum()
    time_under_water = df[in_drawdown].groupby('dd_streak')['dd_streak'].count().max() if in_drawdown.any() else 0
    
    if len(df) > 1:
        x = np.arange(len(df))
        y = df['equity'].values
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0

    # --- Regime Transition Analysis ---
    transition_metrics = {}
    if 'prev_regime' in df and 'regime' in df:
        df['transition'] = df['prev_regime'].fillna('NONE') + " -> " + df['regime'].fillna('NONE')
        for t in df['transition'].unique():
            trans_df = df[df['transition'] == t]
            transition_metrics[t] = get_summary(trans_df)

    # --- Segmentation ---
    regime_metrics = {}
    if 'regime' in df:
        for r in df['regime'].unique():
            if r: regime_metrics[r] = get_summary(df[df['regime'] == r], f"Regime {r}")

    df['hour'] = df['entry_dt'].dt.hour
    df['minute'] = df['entry_dt'].dt.minute
    df['session'] = df.apply(lambda x: 'Morning' if (x['hour'] < 12 or (x['hour'] == 12 and x['minute'] < 30)) else 'Afternoon', axis=1)
    session_metrics = {
        "Morning": get_summary(df[df['session'] == 'Morning'], "Morning Session"),
        "Afternoon": get_summary(df[df['session'] == 'Afternoon'], "Afternoon Session")
    }

    # --- Execution Feasibility Analysis ---
    exec_metrics = {}
    if 'execution_score' in df:
        df['exec_class'] = pd.cut(df['execution_score'], bins=[0, 40, 70, 100], labels=['Dangerous', 'Medium', 'High'])
        for c in df['exec_class'].unique():
            if not pd.isna(c):
                exec_metrics[str(c)] = get_summary(df[df['exec_class'] == c], f"Execution {c}")

    return {
        "total": total_metrics,
        "rolling": {
            "exp_20": round(df['rolling_exp_20'].iloc[-1], 2) if not np.isnan(df['rolling_exp_20'].iloc[-1]) else 0,
            "exp_50": round(df['rolling_exp_50'].iloc[-1], 2) if not np.isnan(df['rolling_exp_50'].iloc[-1]) else 0,
            "stability_score": round(stability_score, 2)
        },
        "risk": {
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "max_drawdown_abs": round(max_drawdown_abs, 2),
            "ulcer_index": round(ulcer_index, 2),
            "recovery_factor": round(recovery_factor, 2),
            "time_under_water_trades": int(time_under_water),
            "equity_slope": round(slope, 2)
        },
        "confidence": {
            "stability_score": round(stability_score, 2),
            "win_rate_ci": total_metrics["win_rate_ci"] if total_metrics else [0, 0],
            "reliable": total_metrics["reliable"] if total_metrics else False
        },
        "segmented": {
            "regime": regime_metrics,
            "session": session_metrics,
            "transitions": transition_metrics,
            "execution": exec_metrics
        },
        "warnings": list(set(warnings)),
        "exit_distribution": df['trigger'].value_counts().to_dict() if 'trigger' in df else {}
    }

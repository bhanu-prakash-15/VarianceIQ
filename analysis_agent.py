from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

import numpy as np
import pandas as pd


# ---------- CONFIG & DATA CLASSES ----------

@dataclass
class AnalysisConfig:
    """
    Configuration for the AnalysisAgent.
    """
    department_col: str = "department"
    account_col: str = "account"
    budget_col: str = "budget"
    actual_col: str = "actual"
    period_col: Optional[str] = "period"          # optional, can be None

    # Materiality thresholds
    materiality_threshold_abs: float = 10_000.0   # e.g. 10k
    materiality_threshold_pct: float = 0.05       # 5%


@dataclass
class LineItemVariance:
    department: str
    account: str
    period: Optional[str]
    budget: float
    actual: float
    variance: float
    variance_pct: Optional[float]
    direction: str              # "favorable" / "unfavorable" / "neutral"
    material: bool
    drivers: List[str] = field(default_factory=list)


@dataclass
class AggregateVariance:
    department: str
    budget_total: float
    actual_total: float
    variance_total: float
    variance_pct_total: Optional[float]


@dataclass
class AnalysisSummary:
    metadata: Dict[str, Any]
    aggregate: List[AggregateVariance]
    line_items: List[LineItemVariance]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "aggregate": [
                {
                    "department": a.department,
                    "budget_total": a.budget_total,
                    "actual_total": a.actual_total,
                    "variance_total": a.variance_total,
                    "variance_pct_total": a.variance_pct_total,
                }
                for a in self.aggregate
            ],
            "line_items": [
                {
                    "department": li.department,
                    "account": li.account,
                    "period": li.period,
                    "budget": li.budget,
                    "actual": li.actual,
                    "variance": li.variance,
                    "variance_pct": li.variance_pct,
                    "direction": li.direction,
                    "material": li.material,
                    "drivers": li.drivers,
                }
                for li in self.line_items
            ],
        }

    def to_json_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


# ---------- ANALYSIS AGENT ----------

class AnalysisAgent:
    """
    Deterministic numeric agent for budget vs actual.
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.cfg = config or AnalysisConfig()

    def run(self, df: pd.DataFrame) -> AnalysisSummary:
        df_clean = self._validate_and_prepare(df)
        df_var = self._compute_variances(df_clean)
        df_tagged = self._apply_materiality_and_drivers(df_var)
        aggregate = self._aggregate_by_department(df_tagged)
        lines = self._to_line_items(df_tagged)

        metadata = {
            "description": "Budget vs Actual variance analysis",
            "row_count": len(df_tagged),
            "materiality_abs": self.cfg.materiality_threshold_abs,
            "materiality_pct": self.cfg.materiality_threshold_pct,
        }

        return AnalysisSummary(metadata=metadata, aggregate=aggregate, line_items=lines)

    # ----- helpers -----

    def _validate_and_prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        c = self.cfg
        required = {c.department_col, c.account_col, c.budget_col, c.actual_col}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()
        df[c.budget_col] = pd.to_numeric(df[c.budget_col], errors="coerce")
        df[c.actual_col] = pd.to_numeric(df[c.actual_col], errors="coerce")
        df = df.dropna(subset=[c.budget_col, c.actual_col])
        return df

    def _compute_variances(self, df: pd.DataFrame) -> pd.DataFrame:
        c = self.cfg
        df["variance"] = df[c.actual_col] - df[c.budget_col]
        with np.errstate(divide="ignore", invalid="ignore"):
            df["variance_pct"] = df["variance"] / df[c.budget_col]
        return df

    def _apply_materiality_and_drivers(self, df: pd.DataFrame) -> pd.DataFrame:
        c = self.cfg

        df["is_material_abs"] = df["variance"].abs() >= c.materiality_threshold_abs
        df["is_material_pct"] = (df["variance_pct"].abs() >= c.materiality_threshold_pct).fillna(False)
        df["is_material"] = df["is_material_abs"] | df["is_material_pct"]

        def direction(v: float) -> str:
            if np.isclose(v, 0.0):
                return "neutral"
            return "unfavorable" if v > 0 else "favorable"

        df["direction"] = df["variance"].apply(direction)

        drivers_col: List[List[str]] = []
        for _, row in df.iterrows():
            row_drivers: List[str] = []
            if row["is_material"]:
                if row["direction"] == "unfavorable":
                    row_drivers.append("overspend")
                elif row["direction"] == "favorable":
                    row_drivers.append("underspend")
            if not row_drivers:
                row_drivers.append("baseline")
            drivers_col.append(row_drivers)

        df["drivers"] = drivers_col
        return df

    def _aggregate_by_department(self, df: pd.DataFrame) -> List[AggregateVariance]:
        c = self.cfg
        grouped = (
            df.groupby(c.department_col)
            .agg(
                budget_total=(c.budget_col, "sum"),
                actual_total=(c.actual_col, "sum"),
                variance_total=("variance", "sum"),
            )
            .reset_index()
        )

        aggregates: List[AggregateVariance] = []
        for _, row in grouped.iterrows():
            budget_total = float(row["budget_total"])
            variance_total = float(row["variance_total"])
            variance_pct_total: Optional[float] = None
            if not np.isclose(budget_total, 0.0):
                variance_pct_total = variance_total / budget_total

            aggregates.append(
                AggregateVariance(
                    department=str(row[c.department_col]),
                    budget_total=budget_total,
                    actual_total=float(row["actual_total"]),
                    variance_total=variance_total,
                    variance_pct_total=variance_pct_total,
                )
            )
        return aggregates

    def _to_line_items(self, df: pd.DataFrame) -> List[LineItemVariance]:
        c = self.cfg
        lines: List[LineItemVariance] = []

        for _, row in df.iterrows():
            variance = float(row["variance"])
            variance_pct_val = row["variance_pct"]
            variance_pct: Optional[float] = None
            if pd.notna(variance_pct_val):
                variance_pct = float(variance_pct_val)

            period_val = None
            if c.period_col and c.period_col in df.columns:
                period_val = str(row[c.period_col])

            lines.append(
                LineItemVariance(
                    department=str(row[c.department_col]),
                    account=str(row[c.account_col]),
                    period=period_val,
                    budget=float(row[c.budget_col]),
                    actual=float(row[c.actual_col]),
                    variance=variance,
                    variance_pct=variance_pct,
                    direction=str(row["direction"]),
                    material=bool(row["is_material"]),
                    drivers=list(row["drivers"]),
                )
            )
        return lines

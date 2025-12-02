# forecasting_agent.py
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI


@dataclass
class ForecastingConfig:
    """Configuration for the ForecastingAgent."""
    use_llm: bool = True
    max_focus_items: int = 6
    azure_endpoint_env: str = "AZURE_OPENAI_ENDPOINT"
    azure_key_env: str = "AZURE_OPENAI_KEY"
    azure_deployment_env: str = "AZURE_OPENAI_DEPLOYMENT"


@dataclass
class ForecastResult:
    mode: str
    narrative: str
    focus_areas: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "narrative": self.narrative,
            "focus_areas": self.focus_areas,
        }


class ForecastingAgent:
    """
    Agent that takes the structured variance summary (same summary_dict
    used by ExplanationAgent) and produces forward-looking guidance.

    If Azure OpenAI is configured it uses LLM mode; otherwise it falls
    back to a simple rule-based forecast.
    """

    def __init__(self, config: ForecastingConfig):
        self.config = config
        self.client: Optional[AzureOpenAI] = None
        self.deployment_name: Optional[str] = None

        if self.config.use_llm:
            endpoint = os.getenv(self.config.azure_endpoint_env)
            key = os.getenv(self.config.azure_key_env)
            deployment = os.getenv(self.config.azure_deployment_env)

            if endpoint and key and deployment:
                self.client = AzureOpenAI(
                    api_key=key,
                    azure_endpoint=endpoint,
                    api_version="2024-02-15-preview",
                )
                self.deployment_name = deployment
            else:
                # If any env var is missing, silently fall back
                self.client = None
                self.deployment_name = None

    # ---------------- PUBLIC API ----------------
    def run(self, summary_dict: Dict[str, Any]) -> ForecastResult:
        """
        Main entry point. Uses LLM if available; otherwise rule-based.
        """
        if self.client and self.deployment_name:
            try:
                return self._run_llm_forecast(summary_dict)
            except Exception:
                # On any LLM error, fall back to rule-based
                pass

        return self._run_rule_based(summary_dict)

    # ---------------- RULE-BASED ----------------
    def _run_rule_based(self, summary_dict: Dict[str, Any]) -> ForecastResult:
        aggregate = summary_dict.get("aggregate", [])

        total_budget = sum(float(a.get("budget_total", 0.0)) for a in aggregate)
        total_actual = sum(float(a.get("actual_total", 0.0)) for a in aggregate)
        variance = total_actual - total_budget

        if total_budget != 0:
            variance_pct = (variance / total_budget) * 100.0
        else:
            variance_pct = 0.0

        # Rank by variance magnitude
        sorted_aggs = sorted(
            aggregate,
            key=lambda x: abs(float(x.get("variance_total", 0.0))),
            reverse=True,
        )

        top = sorted_aggs[: self.config.max_focus_items]

        narrative = (
            "Looking ahead based on the current run-rate, the organisation is "
            f"{'unfavourable' if variance > 0 else 'favourable' if variance < 0 else 'on track'} "
            f"by approximately € {variance:,.0f}, which is about {variance_pct:,.1f}% "
            "relative to the total budget. Departments with the largest current "
            "variances are likely to create the most risk next period and should "
            "be reviewed in more detail."
        )

        focus_areas: List[str] = []
        for row in top:
            dept = row.get("department", "Unknown department")
            v = float(row.get("variance_total", 0.0))
            direction = "above budget" if v > 0 else "below budget" if v < 0 else "on budget"
            focus_areas.append(
                f"{dept}: currently about € {abs(v):,.0f} {direction}. "
                "Prioritise a deep-dive review and consider tightening or reallocating budget next period."
            )

        if not focus_areas:
            focus_areas.append(
                "Overall variance is small; maintain current controls but continue monitoring key departments."
            )

        return ForecastResult(
            mode="rule_based_forecast",
            narrative=narrative,
            focus_areas=focus_areas,
        )

    # ---------------- LLM-BASED ----------------
    def _run_llm_forecast(self, summary_dict: Dict[str, Any]) -> ForecastResult:
        aggregate = summary_dict.get("aggregate", [])

        total_budget = sum(float(a.get("budget_total", 0.0)) for a in aggregate)
        total_actual = sum(float(a.get("actual_total", 0.0)) for a in aggregate)
        variance = total_actual - total_budget

        # Build a compact department-level table as text
        lines = []
        for row in aggregate:
            dept = row.get("department", "Unknown department")
            b = float(row.get("budget_total", 0.0))
            a = float(row.get("actual_total", 0.0))
            v = float(row.get("variance_total", 0.0))
            lines.append(
                f"- {dept}: budget € {b:,.0f}, actual € {a:,.0f}, variance € {v:,.0f}"
            )
        dept_block = "\n".join(lines)

        system_prompt = (
            "You are a senior FP&A forecasting analyst. "
            "Given current-period budget vs actual data, you must:\n"
            "1) Write a short forward-looking narrative (2–3 sentences) "
            "about risk and direction for the next period.\n"
            "2) Provide 4–6 specific focus recommendations for finance leadership.\n"
            "Use only the information given. Do NOT invent new numeric values."
        )

        user_prompt = (
            f"Total budget this period: € {total_budget:,.0f}\n"
            f"Total actual spend this period: € {total_actual:,.0f}\n"
            f"Total variance (actual - budget): € {variance:,.0f}\n\n"
            f"Department-level summary:\n{dept_block}\n\n"
            "Now provide:\n"
            "A) A concise forward-looking narrative.\n"
            "B) A bulleted list of recommended focus areas for next period."
        )

        resp = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )

        text = resp.choices[0].message.content.strip()

        # Very simple parsing: narrative = non-bullet lines, focus_areas = bullet lines
        narrative_lines: List[str] = []
        focus_areas: List[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("-", "*", "•")):
                focus_areas.append(stripped.lstrip("-*• ").strip())
            else:
                narrative_lines.append(stripped)

        narrative = " ".join(narrative_lines)
        if not narrative:
            narrative = (
                "Based on the current variances, several departments are likely to "
                "continue driving overspend risk next period unless corrective actions are taken."
            )

        if not focus_areas:
            focus_areas = [
                "Review top overspending departments and agree concrete corrective actions.",
                "Reforecast next period’s spend using updated run-rates and operational plans.",
            ]

        focus_areas = focus_areas[: self.config.max_focus_items]

        return ForecastResult(
            mode="llm_forecast",
            narrative=narrative,
            focus_areas=focus_areas,
        )

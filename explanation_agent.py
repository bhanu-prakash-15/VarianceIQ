from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
import os
import textwrap

import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env once
load_dotenv()


# ---------- CONFIG & RESULT ----------

@dataclass
class ExplanationConfig:
    use_llm: bool = False
    max_output_tokens: int = 700
    temperature: float = 0.2


@dataclass
class ExplanationResult:
    mode: str                 # "llm" or "rule_based"
    narrative: str
    bullet_points: List[str]


# ---------- EXPLANATION AGENT ----------

class ExplanationAgent:
    """
    Explanation Agent that turns numeric variance JSON into CFO-ready text.

    - LLM mode via Azure GPT-4o-mini (resource: Bhanu-Prakash15)
    - Rule-based fallback if env vars or network fail
    """

    def __init__(self, config: Optional[ExplanationConfig] = None):
        self.cfg = config or ExplanationConfig()
        self.client: Optional[AzureOpenAI] = None
        self.deployment: Optional[str] = None

        if self.cfg.use_llm:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            key = os.getenv("AZURE_OPENAI_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

            if endpoint and key and deployment:
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=key,
                    api_version=api_version,
                )
                self.deployment = deployment
                print(f"[ExplanationAgent] Azure LLM enabled, deployment={deployment}")
            else:
                print("[ExplanationAgent] Missing Azure env vars, using rule-based mode.")
                self.cfg.use_llm = False

    # ---------- PUBLIC API ----------

    def run(self, summary_dict: Dict[str, Any]) -> ExplanationResult:
        if self.client is not None and self.deployment is not None and self.cfg.use_llm:
            try:
                return self._run_llm(summary_dict)
            except Exception as e:
                print(f"[ExplanationAgent] LLM call failed, fallback to rule-based. Error: {e}")

        # Fallback or non-LLM mode
        return self._run_rule_based(summary_dict)

    def run_from_json_file(self, path: str) -> ExplanationResult:
        with open(path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        return self.run(summary)

    # ---------- LLM MODE ----------

    def _build_prompt(self, s: Dict[str, Any]) -> str:
        """Builds the user prompt sent to GPT-4o-mini."""
        summary_json = json.dumps(s, default=str)[:12000]

        prompt = textwrap.dedent(
            f"""
            You are a senior FP&A analyst.

            You are given structured budget vs actual variance analysis in JSON form.
            Your job is to:
            1. Write a clear 2–3 paragraph narrative suitable for a CFO.
            2. Then provide 3–6 bullet points with the key drivers and takeaways.
            3. Do NOT make up new numbers that are not implied by the JSON.

            Here is the JSON:

            ```json
            {summary_json}
            ```
            """
        )
        return prompt

    def _run_llm(self, s: Dict[str, Any]) -> ExplanationResult:
        """Call Azure GPT-4o-mini and parse the response."""
        if self.client is None or self.deployment is None:
            return self._run_rule_based(s)

        prompt = self._build_prompt(s)

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cautious FP&A analyst. "
                        "Write concise, accurate variance explanations. "
                        "Never fabricate financial figures."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.cfg.max_output_tokens,
            temperature=self.cfg.temperature,
        )

        # ✅ FIX: Correct way to access content with new SDK
        try:
            msg = response.choices[0].message
            content = getattr(msg, "content", str(msg))
        except Exception as e:
            print("[ExplanationAgent] Failed to parse Azure response:", e)
            return self._run_rule_based(s)

        narrative, bullets = self._split_narrative_and_bullets(content)

        return ExplanationResult(
            mode="llm",
            narrative=narrative,
            bullet_points=bullets,
        )

    # ---------- RULE-BASED MODE ----------

    def _run_rule_based(self, s: Dict[str, Any]) -> ExplanationResult:
        """Deterministic, non-LLM explanation (good fallback)."""
        meta = s.get("metadata", {})
        agg = s.get("aggregate", [])
        li = s.get("line_items", [])

        agg_df = pd.DataFrame(agg)
        li_df = pd.DataFrame(li)

        row_count = meta.get("row_count", len(li_df))
        abs_th = meta.get("materiality_abs", 0.0)
        pct_th = meta.get("materiality_pct", 0.0)

        if not agg_df.empty:
            agg_df["variance_total"] = agg_df["variance_total"].astype(float)
            unfav = agg_df[agg_df["variance_total"] > 0].sort_values("variance_total", ascending=False)
            fav = agg_df[agg_df["variance_total"] < 0].sort_values("variance_total", ascending=True)
        else:
            unfav = fav = pd.DataFrame()

        narrative_parts = [
            f"Across {row_count:,} line items, the system applied a materiality threshold of "
            f"{abs_th:,.0f} or {pct_th*100:.1f}% to identify significant variances."
        ]

        if not unfav.empty:
            top = unfav.head(2)
            desc = " and ".join(
                f"{r['department']} (≈ {r['variance_total']:,.0f})" for _, r in top.iterrows()
            )
            narrative_parts.append(f"The largest unfavorable variances occurred in {desc}.")

        if not fav.empty:
            top = fav.head(2)
            desc = " and ".join(
                f"{r['department']} (≈ {r['variance_total']:,.0f})" for _, r in top.iterrows()
            )
            narrative_parts.append(f"Major favorable variances were seen in {desc}.")

        bullets: List[str] = []

        if not li_df.empty and "material" in li_df.columns:
            material_df = li_df[li_df["material"]]
            bullets.append(f"{len(material_df):,} line items were marked as material.")

            if not material_df.empty and "drivers" in material_df.columns:
                driver_counts: Dict[str, int] = {}
                for drivers in material_df["drivers"]:
                    for d in drivers:
                        driver_counts[d] = driver_counts.get(d, 0) + 1

                if driver_counts:
                    top_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)[:4]
                    bullets.append(
                        "Most common drivers among material items: "
                        + ", ".join(f"{k} ({v})" for k, v in top_drivers)
                    )
        else:
            bullets.append("No material line items were identified under the current thresholds.")

        bullets.append("These structured insights can be used to support executive decision-making.")

        narrative = " ".join(narrative_parts)
        return ExplanationResult(
            mode="rule_based",
            narrative=narrative,
            bullet_points=bullets,
        )

    # ---------- UTILS ----------

    def _split_narrative_and_bullets(self, text: str) -> (str, List[str]):
        """
        Split mixed text into a narrative section and bullet points.
        Works whether the LLM already formatted bullets or not.
        """
        lines = text.strip().splitlines()
        narrative_lines: List[str] = []
        bullet_lines: List[str] = []

        for line in lines:
            s = line.strip()
            if s.startswith(("-", "*", "•")):
                bullet_lines.append(s.lstrip("-*• ").strip())
            else:
                narrative_lines.append(s)

        narrative = " ".join(narrative_lines).strip()

        if not bullet_lines and narrative:
            # If the LLM didn't format bullets explicitly, approximate from sentences
            bullet_lines = [p.strip() for p in narrative.split(".") if p.strip()][:4]

        return narrative, bullet_lines

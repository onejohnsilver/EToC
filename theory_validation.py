#!/usr/bin/env python3
"""
theory_validation.py

Validation layer for the Evolutionary Survival Theory of Consciousness.

Purpose
-------
This file tests whether the engine reproduces the theory's predicted patterns
across many trials, seeds, stress levels, and ablations.

What it checks:
    - does higher stress increase the value of recursion / social modeling?
    - do deeper architectures outperform survival-only baselines?
    - do memory and identity continuity improve stability over time?
    - do the same trends repeat across randomized runs?

This is the scientific minimum test:
    Does the engine replicate the theory's predicted dynamics?

Outputs
-------
    - CSV of per-trial metrics
    - CSV of aggregated summary metrics
    - optional stress-separation plots if matplotlib is available

Run examples:
    python theory_validation.py --trials 50 --steps 40 --output-dir validation_out
    python theory_validation.py --trials 100 --stress-levels 0.1 0.4 0.7 0.9 --presets full_theory survival_only no_recursion no_social
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import csv
import math
from pathlib import Path
import random
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from core_ablation import PRESETS, AblationConfig
from core_environment import EnvironmentEngine, EnvironmentEvent
from core_simulation import AblationSimulation
from core_metrics import summarize_state, summarize_traces


# ============================================================
# Config / results
# ============================================================


@dataclass(frozen=True)
class TrialConfig:
    preset: str
    stress_level: float
    steps: int
    seed: int
    mode: str = "stress"
    event_name: Optional[str] = None


@dataclass
class TrialResult:
    preset: str
    stress_level: float
    steps: int
    seed: int
    final_environment_stress: float
    final_environment_threat: float
    final_environment_uncertainty: float

    agent_a_survival: float
    agent_a_stability: float
    agent_a_prediction: float
    agent_a_affect: float
    agent_a_self: float
    agent_a_social: float
    agent_a_recursion: float
    agent_a_experience: float
    agent_a_consciousness: float
    agent_a_identity: float
    agent_a_overall: float

    agent_b_survival: float
    agent_b_stability: float
    agent_b_prediction: float
    agent_b_affect: float
    agent_b_self: float
    agent_b_social: float
    agent_b_recursion: float
    agent_b_experience: float
    agent_b_consciousness: float
    agent_b_identity: float
    agent_b_overall: float

    avg_agent_a_consciousness: float
    avg_agent_b_consciousness: float
    avg_agent_a_identity: float
    avg_agent_b_identity: float
    avg_agent_a_survival_loss: float
    avg_agent_b_survival_loss: float

    last_agent_a_recursion: float
    last_agent_b_recursion: float
    last_agent_a_social: float
    last_agent_b_social: float
    last_agent_a_self: float
    last_agent_b_self: float

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


# ============================================================
# Trial execution
# ============================================================


def build_simulation(preset: str, seed: int) -> AblationSimulation:
    if preset not in PRESETS:
        raise KeyError(f"Unknown preset: {preset}")
    return AblationSimulation(preset_name=preset, seed=seed)


def run_trial(config: TrialConfig) -> TrialResult:
    sim = build_simulation(config.preset, config.seed)

    # Create a simple stress schedule: the environment is held near the target stress level
    # while still retaining some natural drift and uncertainty.
    script = []
    for _ in range(config.steps):
        mode = config.mode if config.mode else "stress"
        # drive the world by repeating a mode; the environment engine will drift and add noise
        script.append({"mode": mode})

    # Push the environment to the requested stress level before the run begins.
    sim.environment.state.stress = max(0.0, min(1.0, config.stress_level))
    sim.environment.state.volatility = max(0.0, min(1.0, 0.35 + 0.40 * config.stress_level))
    sim.environment.state.uncertainty = max(0.0, min(1.0, 0.25 + 0.45 * config.stress_level))
    sim.environment.state.scarcity = max(0.0, min(1.0, 0.15 + 0.35 * config.stress_level))
    sim.environment.state.social_pressure = max(0.0, min(1.0, 0.10 + 0.40 * config.stress_level))

    result = sim.run(steps=config.steps, script=script)

    # Final summaries.
    summary_a = result.final_summary_a or summarize_state(
        sim.agent_a.state.engine_state,
        sim.agent_a.updater.memory_manager.identity_summary(),
    )
    summary_b = result.final_summary_b or summarize_state(
        sim.agent_b.state.engine_state,
        sim.agent_b.updater.memory_manager.identity_summary(),
    )

    # Memory-based averages.
    traces_a = sim.agent_a.recent_memories(64)
    traces_b = sim.agent_b.recent_memories(64)
    avg_a = summarize_traces(traces_a)
    avg_b = summarize_traces(traces_b)

    return TrialResult(
        preset=config.preset,
        stress_level=config.stress_level,
        steps=config.steps,
        seed=config.seed,
        final_environment_stress=sim.environment.state.stress,
        final_environment_threat=sim.environment.state.threat_level,
        final_environment_uncertainty=sim.environment.state.uncertainty,
        agent_a_survival=summary_a.survival_score,
        agent_a_stability=summary_a.stability_score,
        agent_a_prediction=summary_a.prediction_score,
        agent_a_affect=summary_a.affect_score,
        agent_a_self=summary_a.self_model_score,
        agent_a_social=summary_a.social_score,
        agent_a_recursion=summary_a.recursion_score,
        agent_a_experience=summary_a.experience_score,
        agent_a_consciousness=summary_a.consciousness_score,
        agent_a_identity=summary_a.identity_score,
        agent_a_overall=summary_a.overall_adaptation_score,
        agent_b_survival=summary_b.survival_score,
        agent_b_stability=summary_b.stability_score,
        agent_b_prediction=summary_b.prediction_score,
        agent_b_affect=summary_b.affect_score,
        agent_b_self=summary_b.self_model_score,
        agent_b_social=summary_b.social_score,
        agent_b_recursion=summary_b.recursion_score,
        agent_b_experience=summary_b.experience_score,
        agent_b_consciousness=summary_b.consciousness_score,
        agent_b_identity=summary_b.identity_score,
        agent_b_overall=summary_b.overall_adaptation_score,
        avg_agent_a_consciousness=float(avg_a.get("avg_consciousness_index", 0.0)),
        avg_agent_b_consciousness=float(avg_b.get("avg_consciousness_index", 0.0)),
        avg_agent_a_identity=float(sim.agent_a.updater.memory_manager.identity_summary().identity_stability),
        avg_agent_b_identity=float(sim.agent_b.updater.memory_manager.identity_summary().identity_stability),
        avg_agent_a_survival_loss=float(avg_a.get("avg_survival_loss", 0.0)),
        avg_agent_b_survival_loss=float(avg_b.get("avg_survival_loss", 0.0)),
        last_agent_a_recursion=sim.agent_a.state.engine_state.recursive_integration,
        last_agent_b_recursion=sim.agent_b.state.engine_state.recursive_integration,
        last_agent_a_social=sim.agent_a.state.engine_state.social_model_depth,
        last_agent_b_social=sim.agent_b.state.engine_state.social_model_depth,
        last_agent_a_self=sim.agent_a.state.engine_state.self_model_depth,
        last_agent_b_self=sim.agent_b.state.engine_state.self_model_depth,
    )


# ============================================================
# Experiment design
# ============================================================


def make_trials(
    presets: Sequence[str],
    stress_levels: Sequence[float],
    trials: int,
    steps: int,
    seed: int,
    mode: str,
) -> List[TrialConfig]:
    rng = random.Random(seed)
    trial_configs: List[TrialConfig] = []
    for preset in presets:
        for stress in stress_levels:
            for _ in range(trials):
                trial_configs.append(
                    TrialConfig(
                        preset=preset,
                        stress_level=float(stress),
                        steps=steps,
                        seed=rng.randint(0, 10**9),
                        mode=mode,
                    )
                )
    rng.shuffle(trial_configs)
    return trial_configs


def run_experiment(trials: Sequence[TrialConfig]) -> pd.DataFrame:
    rows = []
    total = len(trials)
    for i, cfg in enumerate(trials, start=1):
        try:
            result = run_trial(cfg)
            rows.append(result.as_dict())
        except Exception as exc:
            rows.append(
                {
                    "preset": cfg.preset,
                    "stress_level": cfg.stress_level,
                    "steps": cfg.steps,
                    "seed": cfg.seed,
                    "error": str(exc),
                }
            )
        if i % max(1, total // 20) == 0 or i == total:
            print(f"Progress: {i}/{total}")
    df = pd.DataFrame(rows)
    return df


# ============================================================
# Analysis helpers
# ============================================================


def safe_mean(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce")
    return float(s.mean()) if len(s.dropna()) else float("nan")


def safe_std(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce")
    return float(s.std(ddof=0)) if len(s.dropna()) else float("nan")


def confidence_interval_mean(series: pd.Series) -> Tuple[float, float, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return float("nan"), float("nan"), float("nan")
    m = float(s.mean())
    sd = float(s.std(ddof=0))
    se = sd / math.sqrt(len(s)) if len(s) > 0 else float("nan")
    ci = 1.96 * se if len(s) > 0 else float("nan")
    return m, m - ci, m + ci


def summarize_group(df: pd.DataFrame, group_cols: Sequence[str], metric_cols: Sequence[str]) -> pd.DataFrame:
    grouped = df.groupby(list(group_cols), dropna=False)
    rows = []
    for keys, sub in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {col: key for col, key in zip(group_cols, keys)}
        row["n"] = len(sub)
        for metric in metric_cols:
            row[f"{metric}_mean"] = safe_mean(sub[metric])
            row[f"{metric}_std"] = safe_std(sub[metric])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(list(group_cols)).reset_index(drop=True)


def add_comparison_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if {"agent_a_consciousness", "agent_b_consciousness"}.issubset(out.columns):
        out["consciousness_gap_a_minus_b"] = out["agent_a_consciousness"] - out["agent_b_consciousness"]
    if {"agent_a_overall", "agent_b_overall"}.issubset(out.columns):
        out["overall_gap_a_minus_b"] = out["agent_a_overall"] - out["agent_b_overall"]
    if {"agent_a_identity", "agent_b_identity"}.issubset(out.columns):
        out["identity_gap_a_minus_b"] = out["agent_a_identity"] - out["agent_b_identity"]
    if {"agent_a_recursion", "agent_b_recursion"}.issubset(out.columns):
        out["recursion_gap_a_minus_b"] = out["agent_a_recursion"] - out["agent_b_recursion"]
    return out


def summarize_validation(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    df = add_comparison_columns(df)

    metric_cols = [
        "agent_a_survival",
        "agent_a_stability",
        "agent_a_prediction",
        "agent_a_affect",
        "agent_a_self",
        "agent_a_social",
        "agent_a_recursion",
        "agent_a_experience",
        "agent_a_consciousness",
        "agent_a_identity",
        "agent_a_overall",
        "agent_b_survival",
        "agent_b_stability",
        "agent_b_prediction",
        "agent_b_affect",
        "agent_b_self",
        "agent_b_social",
        "agent_b_recursion",
        "agent_b_experience",
        "agent_b_consciousness",
        "agent_b_identity",
        "agent_b_overall",
        "avg_agent_a_consciousness",
        "avg_agent_b_consciousness",
        "avg_agent_a_identity",
        "avg_agent_b_identity",
        "avg_agent_a_survival_loss",
        "avg_agent_b_survival_loss",
        "last_agent_a_recursion",
        "last_agent_b_recursion",
        "last_agent_a_social",
        "last_agent_b_social",
        "last_agent_a_self",
        "last_agent_b_self",
    ]

    if "consciousness_gap_a_minus_b" in df.columns:
        metric_cols += ["consciousness_gap_a_minus_b", "overall_gap_a_minus_b", "identity_gap_a_minus_b", "recursion_gap_a_minus_b"]

    by_preset = summarize_group(df, ["preset"], metric_cols)
    by_stress = summarize_group(df, ["stress_level"], metric_cols)
    by_preset_stress = summarize_group(df, ["preset", "stress_level"], metric_cols)

    # Keep the most interpretable subset for the main summary.
    focus_cols = [
        "agent_a_consciousness",
        "agent_b_consciousness",
        "agent_a_identity",
        "agent_b_identity",
        "agent_a_overall",
        "agent_b_overall",
        "agent_a_recursion",
        "agent_b_recursion",
        "agent_a_social",
        "agent_b_social",
        "agent_a_self",
        "agent_b_self",
        "avg_agent_a_survival_loss",
        "avg_agent_b_survival_loss",
        "consciousness_gap_a_minus_b",
        "overall_gap_a_minus_b",
        "identity_gap_a_minus_b",
        "recursion_gap_a_minus_b",
    ]
    focus_cols = [c for c in focus_cols if c in df.columns]
    overall = summarize_group(df, [], focus_cols) if False else pd.DataFrame(
        [{
            col: safe_mean(df[col]) if col in df.columns else float("nan")
            for col in focus_cols
        } | {"n": len(df)}]
    )

    return {
        "overall": overall,
        "by_preset": by_preset,
        "by_stress": by_stress,
        "by_preset_stress": by_preset_stress,
    }


def rank_presets(df: pd.DataFrame, metric: str = "agent_b_consciousness") -> pd.DataFrame:
    if metric not in df.columns:
        raise KeyError(f"Metric not found: {metric}")
    out = (
        df.groupby("preset", dropna=False)[metric]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values("mean", ascending=False)
        .reset_index(drop=True)
    )
    return out


def stress_slope(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Estimate a simple linear slope of a metric versus stress level per preset."""
    rows = []
    for preset, sub in df.groupby("preset", dropna=False):
        sub = sub[["stress_level", metric]].dropna()
        if len(sub) < 2:
            continue
        x = sub["stress_level"].astype(float).to_numpy()
        y = sub[metric].astype(float).to_numpy()
        x_mean = float(x.mean())
        y_mean = float(y.mean())
        denom = float(((x - x_mean) ** 2).sum())
        slope = float(((x - x_mean) * (y - y_mean)).sum() / denom) if denom > 0 else float("nan")
        rows.append({"preset": preset, "metric": metric, "slope": slope, "n": len(sub)})
    return pd.DataFrame(rows).sort_values("slope", ascending=False).reset_index(drop=True)


# ============================================================
# Plotting
# ============================================================


def maybe_make_plots(df: pd.DataFrame, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipping plots")
        return

    df = add_comparison_columns(df)

    # Plot 1: consciousness versus stress by preset
    fig = plt.figure()
    for preset, sub in df.groupby("preset"):
        grouped = sub.groupby("stress_level")["agent_b_consciousness"].mean().reset_index()
        plt.plot(grouped["stress_level"], grouped["agent_b_consciousness"], marker="o", label=preset)
    plt.xlabel("Stress level")
    plt.ylabel("Agent B consciousness (mean)")
    plt.title("Consciousness vs stress")
    plt.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "consciousness_vs_stress.png", dpi=150)
    plt.close(fig)

    # Plot 2: recursion versus stress by preset
    fig = plt.figure()
    for preset, sub in df.groupby("preset"):
        grouped = sub.groupby("stress_level")["agent_b_recursion"].mean().reset_index()
        plt.plot(grouped["stress_level"], grouped["agent_b_recursion"], marker="o", label=preset)
    plt.xlabel("Stress level")
    plt.ylabel("Agent B recursion (mean)")
    plt.title("Recursion vs stress")
    plt.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "recursion_vs_stress.png", dpi=150)
    plt.close(fig)

    # Plot 3: social versus stress by preset
    fig = plt.figure()
    for preset, sub in df.groupby("preset"):
        grouped = sub.groupby("stress_level")["agent_b_social"].mean().reset_index()
        plt.plot(grouped["stress_level"], grouped["agent_b_social"], marker="o", label=preset)
    plt.xlabel("Stress level")
    plt.ylabel("Agent B social score (mean)")
    plt.title("Social modeling vs stress")
    plt.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "social_vs_stress.png", dpi=150)
    plt.close(fig)


# ============================================================
# CLI
# ============================================================


def parse_float_list(values: Sequence[str]) -> List[float]:
    return [float(v) for v in values]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation experiments for the theory engine.")
    parser.add_argument("--trials", type=int, default=20, help="Trials per preset per stress level.")
    parser.add_argument("--steps", type=int, default=30, help="Simulation steps per trial.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed.")
    parser.add_argument(
        "--stress-levels",
        nargs="*",
        default=[0.1, 0.3, 0.5, 0.7, 0.9],
        help="Stress levels to test.",
    )
    parser.add_argument(
        "--presets",
        nargs="*",
        default=["full_theory", "survival_only", "no_recursion", "no_social", "no_self_model", "no_affect"],
        help="Ablation presets to compare.",
    )
    parser.add_argument("--mode", type=str, default="stress", help="Environment mode used during validation runs.")
    parser.add_argument("--output-dir", type=str, default="validation_out", help="Directory for CSVs and plots.")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stress_levels = [float(x) for x in args.stress_levels]
    presets = list(args.presets)

    print("Building trial list...")
    trials = make_trials(
        presets=presets,
        stress_levels=stress_levels,
        trials=args.trials,
        steps=args.steps,
        seed=args.seed,
        mode=args.mode,
    )
    print(f"Total trials: {len(trials)}")

    print("Running experiment...")
    df = run_experiment(trials)
    raw_path = output_dir / "validation_trials.csv"
    df.to_csv(raw_path, index=False)
    print(f"Saved raw trial data to {raw_path}")

    summary = summarize_validation(df)
    for name, sub in summary.items():
        path = output_dir / f"summary_{name}.csv"
        sub.to_csv(path, index=False)
        print(f"Saved {name} summary to {path}")

    # Rank by the most theory-relevant metric.
    if "agent_b_consciousness" in df.columns:
        ranking = rank_presets(df, "agent_b_consciousness")
        ranking_path = output_dir / "preset_ranking_by_consciousness.csv"
        ranking.to_csv(ranking_path, index=False)
        print(f"Saved ranking to {ranking_path}")
        print("\nPreset ranking by mean Agent B consciousness:")
        print(ranking.to_string(index=False))

        slope_table = stress_slope(df, "agent_b_consciousness")
        slope_path = output_dir / "preset_stress_slope_consciousness.csv"
        slope_table.to_csv(slope_path, index=False)
        print(f"Saved stress slope table to {slope_path}")
        print("\nStress slope by preset (Agent B consciousness):")
        print(slope_table.to_string(index=False))

    if not args.no_plots:
        maybe_make_plots(df, output_dir)
        print("Saved plots if matplotlib was available.")

    # Quick interpretive indicators.
    df = add_comparison_columns(df)
    if {"consciousness_gap_a_minus_b", "stress_level"}.issubset(df.columns):
        gap_by_stress = df.groupby("stress_level")["consciousness_gap_a_minus_b"].mean().reset_index()
        gap_path = output_dir / "consciousness_gap_by_stress.csv"
        gap_by_stress.to_csv(gap_path, index=False)
        print(f"Saved gap-by-stress table to {gap_path}")
        print("\nMean consciousness gap (A - B) by stress:")
        print(gap_by_stress.to_string(index=False))

    print("\nValidation complete.")
    print("Main question to inspect: do deeper architectures separate more strongly as stress rises?")


if __name__ == "__main__":
    main()

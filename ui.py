#!/usr/bin/env python3
"""
ui.py

Interactive front end and diagnostics layer for the full theory engine.
"""

from __future__ import annotations

import argparse
import traceback
from typing import Any, Dict, List, Optional


def safe_imports() -> Dict[str, Any]:
    modules: Dict[str, Any] = {}
    module_names = [
        "core_types", "core_math", "core_update", "core_constraints",
        "core_memory", "core_ablation", "core_metrics", "core_environment",
        "core_agents", "core_simulation",
    ]
    for name in module_names:
        try:
            modules[name] = __import__(name)
        except Exception as exc:
            print(f"[IMPORT ERROR] {name} failed to import: {exc}")
            raise
    return modules


def print_header(preset: str, steps: int, seed: int, interactive: bool) -> None:
    print("=" * 72)
    print("Evolutionary Survival Theory Engine")
    print(f"preset={preset} | steps={steps} | seed={seed} | interactive={interactive}")
    print("=" * 72)


def print_help() -> None:
    print(
        """
Commands:
  help                     show this help
  status                   show current environment and agent summaries
  calm                     move environment toward calm
  stress                   increase environmental stress
  crisis                   sharply increase stress and volatility
  recover                  reduce stress and restore recovery
  event <name>             trigger a preset event
  feed A / feed B          provide support to agent A or B
  help A / help B          stronger support to agent A or B
  threaten A / threaten B  apply threat to agent A or B
  isolate A / isolate B    social isolation
  ignore A / ignore B      mild social neglect
  tune <A/B> <param> <val> manual modifier override (caution/curiosity)
  step                     advance one neutral step
  quit                     exit

Preset events:
  alarm, food_abundance, predator, social_bond, rejection, scarcity_crisis, stabilize
""".strip()
    )


def print_simulation_snapshot(sim) -> None:
    summary = sim.summarize()
    print("\nENVIRONMENT")
    print(summary["environment"])
    print("\nAGENT A (Profile: {})".format(sim.agent_a.profile.name))
    print(summary["agent_a"])
    print("\nAGENT B (Profile: {})".format(sim.agent_b.profile.name))
    print(summary["agent_b"])
    print("\nLAYER RANKING A")
    print(sim.layer_ranking("a"))
    print("\nLAYER RANKING B")
    print(sim.layer_ranking("b"))


def print_agent_dialogue(sim) -> None:
    print("\nA says:", sim.agent_a.speak())
    print("B says:", sim.agent_b.speak())
    print("A report:", sim.agent_a.generate_report())
    print("B report:", sim.agent_b.generate_report())


def smoke_test(seed: Optional[int], preset: str, steps: int, profile_a: str = "active_inf", profile_b: str = "recursive") -> Any:
    """Run a short end-to-end validation test of the full code stack."""
    from core_types import TheoryInputs, TheoryWeights
    from core_environment import EnvironmentEngine
    from core_agents import AgentEngine
    from core_ablation import PRESETS
    from core_simulation import AblationSimulation
    from core_metrics import summarize_state

    if preset not in PRESETS:
        raise KeyError(f"Unknown preset: {preset}")

    print("[OK] Core modules imported")

    weights = TheoryWeights()
    env = EnvironmentEngine(seed=seed)
    
    # MODULAR FACTORY ASSIGNMENT
    agent_a = AgentEngine(name="A", profile_name=profile_a, seed=seed)
    agent_b = AgentEngine(name="B", profile_name=profile_b, seed=None if seed is None else seed + 1)

    print(f"[OK] Instantiated Agent A ({profile_a}) & Agent B ({profile_b})")

    _ = TheoryInputs(
        homeostatic_deviation=0.15, environmental_stress=0.25, prediction_target=0.50,
        observed_state=0.45, social_threat=0.20, social_support=0.40, language_support=0.10,
        action_cost=0.05, memory_depth=0.10, self_consistency=0.50, external_uncertainty=0.20,
    )
    
    sim = AblationSimulation(preset_name=preset, agent_a=agent_a, agent_b=agent_b, seed=seed)
    result = sim.run(
        steps=steps,
        script=[
            {"mode": "calm"},
            {"mode": "stress", "event": "alarm", "user_action_a": "feed", "user_action_b": "ignore"},
            {"mode": "crisis", "event": "predator", "user_action_a": "threaten", "user_action_b": "help"},
        ],
    )

    print("[OK] Simulation sandbox ran successfully")
    return sim


def run_interactive(sim) -> None:
    from core_environment import get_event
    print_help()
    print_simulation_snapshot(sim)

    while True:
        try:
            raw = input("\nengine> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        tokens = raw.lower().split()
        cmd = tokens[0]

        try:
            if cmd in {"quit", "exit"}:
                break
            elif cmd == "help":
                print_help()
                continue
            elif cmd == "status":
                print_simulation_snapshot(sim)
                print_agent_dialogue(sim)
                continue
            elif cmd == "step":
                sim.step()
            elif cmd in {"calm", "stress", "crisis", "recover"}:
                sim.step(mode=cmd)
            elif cmd == "event":
                if len(tokens) < 2:
                    print("Usage: event <name>")
                    continue
                sim.step(event=get_event(tokens[1]))
            elif cmd in {"feed", "help", "threaten", "isolate", "ignore"}:
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Specify A or B, e.g. 'feed A'")
                    continue
                ua = raw.strip()
                if tokens[1] == "a":
                    sim.step(user_action_a=ua)
                else:
                    sim.step(user_action_b=ua)
            # ─── NEW: LIVE ALLOSTATIC TUNING OVERRIDES ───
            elif cmd == "tune":
                if len(tokens) < 4 or tokens[1] not in {"a", "b"}:
                    print("Usage: tune <A/B> <caution/curiosity> <value>")
                    continue
                
                target_agent = sim.agent_a if tokens[1] == "a" else sim.agent_b
                param = tokens[2].lower()
                
                try:
                    val = float(tokens[3])
                    if param == "caution" and hasattr(target_agent.state, "caution"):
                        target_agent.state.caution = val
                        print(f"  [TUNE] Agent {tokens[1].upper()} Caution manually forced to {val}")
                    elif param == "curiosity" and hasattr(target_agent.state, "curiosity"):
                        target_agent.state.curiosity = val
                        print(f"  [TUNE] Agent {tokens[1].upper()} Curiosity manually forced to {val}")
                    else:
                        print(f"  [ERROR] Unknown or unmodifiable state property: '{param}'")
                except ValueError:
                    print("  [ERROR] Tuning value must be a floating-point number (e.g., 0.85)")
            else:
                print("Unknown command. Type 'help' for options.")
                continue

            print_simulation_snapshot(sim)
            print_agent_dialogue(sim)
        except Exception as exc:
            print("\n[STEP ERROR] The engine encountered a problem during this command.")
            print(f"Error: {exc}")
            traceback.print_exc()


def main() -> None:
    parser = argparse.ArgumentParser(description="Front end for the theory engine.")
    parser.add_argument("--steps", type=int, default=3, help="Number of steps for smoke test.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed.")
    parser.add_argument("--preset", type=str, default="full_theory", help="Ablation preset name.")
    parser.add_argument("--profile_a", type=str, default="active_inf", help="Profile for Agent A.")
    parser.add_argument("--profile_b", type=str, default="recursive", help="Profile for Agent B.")
    parser.add_argument("--interactive", action="store_true", help="Enter interactive command mode.")
    args = parser.parse_args()

    print_header(args.preset, args.steps, args.seed, args.interactive)

    try:
        safe_imports()
        sim = smoke_test(seed=args.seed, preset=args.preset, steps=args.steps, profile_a=args.profile_a, profile_b=args.profile_b)

        if args.interactive:
            run_interactive(sim)
        else:
            print("\nStartup check passed. Run with `--interactive` to play live with the metrics.")

    except Exception as exc:
        print(f"\n[FAIL] Engine failed startup. Error: {exc}")
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
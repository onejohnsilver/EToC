#!/usr/bin/env python3
"""
ui.py

Interactive front end and diagnostics layer for the EToC engine.
Optimized for Operator testing of Allostatic Load and Orthogonal Costing.
"""

from __future__ import annotations

import argparse
import traceback
from typing import Any, Dict, Optional

def safe_imports() -> Dict[str, Any]:
    modules: Dict[str, Any] = {}
    module_names = [
        "core_types", "core_math", "core_update", "core_constraints",
        "core_memory", "core_ablation", "core_metrics", "core_environment",
        "core_agents", "core_simulation", "core_allostasis",
    ]
    for name in module_names:
        try:
            modules[name] = __import__(name)
        except Exception as exc:
            print(f"[IMPORT ERROR] {name} failed to import: {exc}")
            raise
    return modules

def print_header(preset: str, seed: int) -> None:
    print("=" * 72)
    print("Evolutionary Survival Theory Engine - Diagnostic Sandbox")
    print(f"Preset: {preset} | Seed: {seed} | Mode: Operator Control")
    print("=" * 72)

def print_help() -> None:
    print(
        """
Commands:
  help                     Show this help menu
  status                   Show full environment and agent summaries
  emotions <A/B>           View the current emotion labels and affect values for an agent
  salience <A/B>           [NEW] View the Salience Bank and current Allostatic Load
  identity <A/B>           [NEW] View affectively weighted Identity Summary & Coherence
  inspect <A/B> <layer>    Deep dive into a specific Literal layer (e.g., 'survival')
  speak <A/B>              Hear the agent's current narrative statement
  calm / stress / crisis   Shift the environmental baseline
  recover                  Reduce stress and restore recovery
  event <name>             Trigger a preset environmental event
  feed / help <A/B>        Provide support to a specific agent
  threaten / isolate <A/B> Apply targeted stress to a specific agent
  cost <A/B> <value>       [UPDATED] Inject extreme orthogonal cost (pain) to trigger Salience
  tune <A/B> <param> <val> Manual state override
  step [N]                 Advance the simulation by N steps (default 1)
  quit                     Exit the sandbox

Repeat counts:
  Add an optional numeric suffix to most simulation-driving commands to run them multiple times.
  Examples: crisis 3, event predator 2, threaten A 4

Preset events:
  alarm, food_abundance, predator, social_bond, rejection, scarcity_crisis, stabilize
""".strip()
    )

def print_simulation_snapshot(sim) -> None:
    summary = sim.summarize()
    print("\n[ ENVIRONMENT STATE ]")
    print(summary.get("environment", "No environment data"))
    print("\n[ AGENT A ] (Profile: {})".format(sim.agent_a.profile.name if hasattr(sim.agent_a, "profile") else "Unknown"))
    print(summary.get("agent_a", "No agent data"))
    print("\n[ AGENT B ] (Profile: {})".format(sim.agent_b.profile.name if hasattr(sim.agent_b, "profile") else "Unknown"))
    print(summary.get("agent_b", "No agent data"))
    if hasattr(sim.agent_a, "get_emotions") and hasattr(sim.agent_b, "get_emotions"):
        print("\n[ EMOTIONAL CONTEXT ]")
        emotions_a = sim.agent_a.get_emotions()
        emotions_b = sim.agent_b.get_emotions()
        print(f"  A: {', '.join(emotions_a['emotion_labels'])} | primary: {emotions_a['primary_emotion']}")
        print(f"  B: {', '.join(emotions_b['emotion_labels'])} | primary: {emotions_b['primary_emotion']}")

def print_agent_dialogue(sim) -> None:
    print("\n[ COMMUNICATIONS ]")
    if hasattr(sim.agent_a, "speak"):
        print("A Outward:", sim.agent_a.speak())
        print("A Internal Report:", sim.agent_a.generate_report())
    if hasattr(sim.agent_b, "speak"):
        print("B Outward:", sim.agent_b.speak())
        print("B Internal Report:", sim.agent_b.generate_report())

def get_memory_manager(agent: Any) -> Any:
    """Safely extract the MemoryManager from the agent's updater architecture."""
    if hasattr(agent, "updater") and hasattr(agent.updater, "memory_manager"):
        return agent.updater.memory_manager
    # Fallback if architecture is nested differently
    if hasattr(agent, "engine") and hasattr(agent.engine, "updater"):
        return agent.engine.updater.memory_manager
    return None

def print_emotions(sim, target_agent: str) -> None:
    agent = sim.agent_a if target_agent == "a" else sim.agent_b
    if not hasattr(agent, "get_emotions"):
        print(f"\n[ERROR] Agent {target_agent.upper()} does not expose emotion labels.")
        return
    data = agent.get_emotions()
    print(f"\n[ EMOTIONS | AGENT {target_agent.upper()} ]")
    print(f"  primary_emotion: {data['primary_emotion']}")
    print(f"  labels: {', '.join(data['emotion_labels'])}")
    print(f"  affect_valence: {data['affect_valence']:.3f}")
    print(f"  affect_arousal: {data['affect_arousal']:.3f}")
    print(f"  trust_in_other: {data['trust_in_other']:.3f}")
    print(f"  confidence: {data['confidence']:.3f}")
    print(f"  self_model_depth: {data['self_model_depth']:.3f}")
    print(f"  social_model_depth: {data['social_model_depth']:.3f}")

def print_salience(sim, target_agent: str) -> None:
    agent = sim.agent_a if target_agent == "a" else sim.agent_b
    mm = get_memory_manager(agent)
    
    if not mm:
        print(f"\n[ERROR] Could not locate MemoryManager on Agent {target_agent.upper()}")
        return

    traces = mm.salient_traces()
    print(f"\n[ SALIENCE BANK | AGENT {target_agent.upper()} ]")
    if not traces:
        print("  [CLEAR] No traumatic memories stored. Allostatic load is 0.00")
        return
        
    for t in traces:
        print(f"  Step {t.step_index:03d} | Survival Loss: {t.survival_loss:.2f} | Pred Error: {t.prediction_error:.2f} | Subjective: {t.subjective_experience:.2f}")
    
    load = sum(t.survival_loss + t.prediction_error for t in traces) / (2.0 * len(traces))
    print(f"  --> Current Anticipatory Allostatic Load: {load:.3f}")

def print_identity(sim, target_agent: str) -> None:
    agent = sim.agent_a if target_agent == "a" else sim.agent_b
    mm = get_memory_manager(agent)
    
    if not mm:
        print(f"\n[ERROR] Could not locate MemoryManager on Agent {target_agent.upper()}")
        return
        
    identity = mm.identity_summary()
    print(f"\n[ IDENTITY SUMMARY | AGENT {target_agent.upper()} ]")
    print(f"  Stability:         {identity.identity_stability:.3f}")
    print(f"  Continuity:        {identity.continuity_strength:.3f}")
    print(f"  Coherence:         {identity.coherence:.3f}")
    print(f"  Threat History:    {identity.threat_history:.3f}")
    print(f"  Trust History:     {identity.trust_history:.3f}")
    print(f"  Self Narrative:    {identity.self_narrative_strength:.3f}")
    print(f"  Social Narrative:  {identity.social_narrative_strength:.3f}")

def parse_repeat_count(tokens: list[str], repeatable: set[str]) -> tuple[list[str], int, bool]:
    if len(tokens) > 1 and tokens[-1].isdigit() and tokens[0] in repeatable:
        count = int(tokens[-1])
        if count > 1:
            return tokens[:-1], count, True
    return tokens, 1, False


def inspect_layer(sim, target_agent: str, layer_name: str) -> None:
    agent = sim.agent_a if target_agent == "a" else sim.agent_b
    try:
        layer_data = agent.get_layer_state(layer_name) 
        print(f"\n[ INSPECTING {layer_name.upper()} | AGENT {target_agent.upper()} ]")
        for key, value in layer_data.items():
            print(f"  {key}: {value}")
    except AttributeError:
        print(f"\n[INSPECT] Agent {target_agent.upper()} does not currently expose layer states directly.")
    except Exception as exc:
        print(f"\n[INSPECT ERROR] Could not retrieve layer '{layer_name}'. {exc}")

def initialize_sandbox(seed: Optional[int], preset: str, profile_a: str, profile_b: str) -> Any:
    from core_types import TheoryInputs, TheoryWeights
    from core_environment import EnvironmentEngine
    from core_agents import AgentEngine
    from core_ablation import PRESETS
    from core_simulation import AblationSimulation

    if preset not in PRESETS:
        raise KeyError(f"Unknown preset: {preset}")

    print("[SYSTEM] Core modules imported.")
    env = EnvironmentEngine(seed=seed)
    agent_a = AgentEngine(name="A", profile_name=profile_a, seed=seed)
    agent_b = AgentEngine(name="B", profile_name=profile_b, seed=None if seed is None else seed + 1)
    print(f"[SYSTEM] Instantiated Agent A ({profile_a}) & Agent B ({profile_b}).")
    
    sim = AblationSimulation(preset_name=preset, agent_a=agent_a, agent_b=agent_b, seed=seed)
    print("[SYSTEM] Sandbox initialized. Awaiting operator input.")
    return sim

def run_interactive(sim) -> None:
    from core_environment import get_event
    print_help()
    print_simulation_snapshot(sim)

    while True:
        try:
            raw = input("\noperator> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTerminating session.")
            break

        if not raw:
            continue

        tokens = raw.lower().split()
        cmd = tokens[0]
        repeatable = {"step", "calm", "stress", "crisis", "recover", "event", "feed", "help", "threaten", "isolate", "ignore"}
        tokens, repeat_count, count_removed = parse_repeat_count(tokens, repeatable)
        raw_no_count = raw if not count_removed else raw.rsplit(" ", 1)[0]

        try:
            if cmd in {"quit", "exit"}:
                break
            elif cmd == "help" and len(tokens) == 1:
                print_help()
                continue
            elif cmd == "status":
                print_simulation_snapshot(sim)
                print_agent_dialogue(sim)
                continue
            elif cmd == "emotions":
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Usage: emotions <A/B>")
                    continue
                print_emotions(sim, tokens[1])
                continue
            elif cmd == "salience":
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Usage: salience <A/B>")
                    continue
                print_salience(sim, tokens[1])
                continue
            elif cmd == "identity":
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Usage: identity <A/B>")
                    continue
                print_identity(sim, tokens[1])
                continue
            elif cmd == "inspect":
                if len(tokens) < 3 or tokens[1] not in {"a", "b"}:
                    print("Usage: inspect <A/B> <layer_name>")
                    continue
                inspect_layer(sim, tokens[1], tokens[2])
                continue
            elif cmd == "step":
                steps = repeat_count if cmd == "step" else (int(tokens[1]) if len(tokens) > 1 else 1)
                for _ in range(steps):
                    sim.step()
                print(f"[STEP] Advanced {steps} step(s).")
            elif cmd in {"calm", "stress", "crisis", "recover"}:
                for _ in range(repeat_count):
                    sim.step(mode=cmd)
                print(f"[ENVIRONMENT] Shifted to {cmd.upper()} for {repeat_count} step(s).")
            elif cmd == "event":
                if len(tokens) < 2:
                    print("Usage: event <name>")
                    continue
                for _ in range(repeat_count):
                    sim.step(event=get_event(tokens[1]))
                print(f"[ENVIRONMENT] Triggered event: {tokens[1].upper()} for {repeat_count} step(s).")
            elif cmd == "speak":
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Usage: speak <A/B>")
                    continue
                agent = sim.agent_a if tokens[1] == "a" else sim.agent_b
                print(f"[SPEAK] Agent {tokens[1].upper()}: {agent.speak()}")
            elif cmd in {"feed", "help", "threaten", "isolate", "ignore"}:
                if len(tokens) < 2 or tokens[1] not in {"a", "b"}:
                    print("Specify A or B, e.g. 'threaten A'")
                    continue
                ua = raw_no_count.strip()
                if tokens[1] == "a":
                    for _ in range(repeat_count):
                        sim.step(user_action_a=ua)
                else:
                    for _ in range(repeat_count):
                        sim.step(user_action_b=ua)
                print(f"[ACTION] Executed '{cmd}' for agent {tokens[1].upper()} {repeat_count} time(s).")
            elif cmd == "cost":
                if len(tokens) < 3 or tokens[1] not in {"a", "b"}:
                    print("Usage: cost <A/B> <float_value>")
                    continue
                target_agent = sim.agent_a if tokens[1] == "a" else sim.agent_b
                val = float(tokens[2])
                
                # OPERATOR UPGRADE: Shock the system state directly so the MemoryManager 
                # catches it on the VERY NEXT step, guaranteeing it locks into the Salience Bank.
                if hasattr(target_agent, "state"):
                    target_agent.state.survival_loss = val
                    target_agent.state.prediction_error = val
                    target_agent.state.subjective_experience = val
                    print(f"[ORTHOGONAL STRIKE] Agent {tokens[1].upper()} state violently disrupted. Run 'step' to process trauma.")
                else:
                    print("[ERROR] Could not inject cost. Agent missing 'state' attribute.")
            elif cmd == "tune":
                if len(tokens) < 4 or tokens[1] not in {"a", "b"}:
                    print("Usage: tune <A/B> <param> <value>")
                    continue
                
                target_agent = sim.agent_a if tokens[1] == "a" else sim.agent_b
                param = tokens[2].lower()
                
                try:
                    val = float(tokens[3])
                    if hasattr(target_agent.state, param):
                        setattr(target_agent.state, param, val)
                        print(f"[TUNE] Agent {tokens[1].upper()} '{param}' manually forced to {val}")
                    else:
                        print(f"[ERROR] Unknown or unmodifiable state property: '{param}'")
                except ValueError:
                    print("[ERROR] Tuning value must be a floating-point number (e.g., 0.85)")
            else:
                print("Unknown command. Type 'help' for options.")
                continue

            if cmd not in {"inspect", "status", "help", "salience", "identity"}:
                print_agent_dialogue(sim)

        except Exception as exc:
            print("\n[FATAL ERROR] Engine desync during command execution.")
            print(f"Details: {exc}")
            traceback.print_exc()

def main() -> None:
    parser = argparse.ArgumentParser(description="Operator Diagnostics Front End for EToC.")
    parser.add_argument("--seed", type=int, default=7, help="Random deterministic seed.")
    parser.add_argument("--preset", type=str, default="full_theory", help="Ablation configuration preset.")
    parser.add_argument("--profile_a", type=str, default="active_inf", help="Cognitive profile for Agent A.")
    parser.add_argument("--profile_b", type=str, default="recursive", help="Cognitive profile for Agent B.")
    args = parser.parse_args()

    print_header(args.preset, args.seed)

    try:
        safe_imports()
        sim = initialize_sandbox(seed=args.seed, preset=args.preset, profile_a=args.profile_a, profile_b=args.profile_b)
        run_interactive(sim)
    except Exception as exc:
        print(f"\n[FAIL] Sandbox failed to initialize. Details: {exc}")
        traceback.print_exc()
        raise SystemExit(1)

if __name__ == "__main__":
    main()
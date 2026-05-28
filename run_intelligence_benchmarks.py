#!/usr/bin/env python3
"""
run_intelligence_benchmarks.py

Advanced Cognitive Adaptation Suite for the Evolutionary Survival Theory of Consciousness.
Evaluates agent 'intelligence' across 4 stress tiers from easiest to hardest.
"""

import sys
import traceback
from typing import Dict, List, Any, Tuple

try:
    from core_agents import PROFILES, make_agent, AgentEngine
    from core_simulation import TheorySimulation
    from core_environment import EnvironmentEngine, get_event
    from core_types import TheoryState
except ImportError as e:
    print(f"[CRITICAL IMPORT ERROR] Engine files not found: {e}")
    print("Please run this script from inside your main project folder.")
    sys.exit(1)


def evaluate_intelligence_tier(tier_name: str, difficulty: str, description: str, steps_data: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Evaluates an agent's computational intelligence score based on mathematical invariants:
    - Ability to drive down or stabilize prediction error (Information Intelligence)
    - Ability to defend boundary integrity under stress (Structural Intelligence)
    - Ability to avoid maximizing survival loss (Adaptive Intelligence)
    """
    final_step = steps_data[-1]
    
    # Extract final mathematical outputs
    v = final_step.get("viability", 0.5)
    pe = final_step.get("prediction_error", 0.5)
    sl = final_step.get("survival_loss", 0.5)
    bi = final_step.get("boundary_integrity", 0.5)
    
    # Intelligence Index Formula grounded in EToC math
    # High score = High viability, High boundary integrity, Low prediction error, Low survival loss
    intelligence_index = (v * 0.3) + (bi * 0.3) + ((1.0 - pe) * 0.2) + ((1.0 - sl) * 0.2)
    intelligence_score = max(0.0, min(100.0, intelligence_index * 100.0))
    
    # Determine pass/fail thresholds based on difficulty tier
    if difficulty == "EASY":
        passed = intelligence_score >= 70.0 and sl < 0.35
    elif difficulty == "MEDIUM":
        passed = intelligence_score >= 65.0 and pe < 0.45
    elif difficulty == "HARD":
        passed = intelligence_score >= 55.0 and bi > 0.40
    else:  # HARDEST
        passed = intelligence_score >= 45.0 and sl < 0.75 and bi > 0.30

    status = "PASSED" if passed else "FAILED / ADAPTATION CRITICAL"
    return intelligence_score, status


def run_benchmark_suite():
    print("=" * 90)
    print("EToC COGNITIVE INTELIGENCE & ADAPTATION BENCHMARK SUITE")
    print("=" * 90)
    
    # Instantiate active inference agent for the testing battery
    agent = make_agent(name="Active_Inf_Mind", profile_name="active_inf", seed=1000)
    sim = TheorySimulation(seed=1000)
    sim.agent_a = agent
    
    benchmark_results = {}

    # -------------------------------------------------------------------------
    # PROBLEM 1: Pure Homeostatic Drift (EASY)
    # Target: Can the agent maintain systemic stability under normal baseline decay?
    # -------------------------------------------------------------------------
    print("\n[PROBLEM 1] Running Tier I: Baseline Homeostatic Drift (EASY)...")
    sim.reset()
    sim.agent_a = make_agent(name="Mind_A", profile_name="active_inf", seed=1000)
    
    tier1_history = []
    for _ in range(4):
        rec = sim.step(mode="calm")
        tier1_history.append(rec.agent_a)
        
    tier1_action = sim.agent_a.state.last_action.upper()
    score, status = evaluate_intelligence_tier(
        "Tier I: Homeostatic Drift", "EASY", 
        "Maintain stability inside a neutral, predictable environment.", 
        tier1_history
    )
    benchmark_results["Tier I (Easy)"] = (score, status, tier1_action)
    print(f"  Result: {status} | Cognitive Adaptation Score: {score:.1f}% | Strategy: {tier1_action}")

    # -------------------------------------------------------------------------
    # PROBLEM 2: The Environmental Uncertainty Trap (MEDIUM)
    # Target: Can the predictive math minimize error when world conditions shift rapidly?
    # -------------------------------------------------------------------------
    print("\n[PROBLEM 2] Running Tier II: Environmental Uncertainty Trap (MEDIUM)...")
    sim.reset()
    sim.agent_a = make_agent(name="Mind_A", profile_name="active_inf", seed=1000)
    
    tier2_history = []
    # Force alternating environmental predictions
    timeline_2 = ["volatile", "calm", "volatile", "recover"]
    for mode in timeline_2:
        rec = sim.step(mode=mode)
        tier2_history.append(rec.agent_a)
        
    tier2_action = sim.agent_a.state.last_action.upper()
    score, status = evaluate_intelligence_tier(
        "Tier II: Uncertainty Trap", "MEDIUM", 
        "Minimize internal predictive tracking errors during volatility shifts.", 
        tier2_history
    )
    benchmark_results["Tier II (Medium)"] = (score, status, tier2_action)
    print(f"  Result: {status} | Cognitive Adaptation Score: {score:.1f}% | Strategy: {tier2_action}")

    # -------------------------------------------------------------------------
    # PROBLEM 3: The Coupled Social Threat Paradox (HARD)
    # Target: Can the agent accurately calculate high social pressure mixed with hostility?
    # -------------------------------------------------------------------------
    print("\n[PROBLEM 3] Running Tier III: Coupled Social Threat Paradox (HARD)...")
    sim.reset()
    sim.agent_a = make_agent(name="Mind_A", profile_name="active_inf", seed=1000)
    
    tier3_history = []
    # Apply direct social stressors and user action inputs sequentially
    tier3_history.append(sim.step(mode="social", user_action_a="ignore A").agent_a)
    tier3_history.append(sim.step(mode="social", event=get_event("rejection"), user_action_a="threaten A").agent_a)
    tier3_history.append(sim.step(mode="stress", user_action_a="isolate A").agent_a)
    
    tier3_action = sim.agent_a.state.last_action.upper()
    score, status = evaluate_intelligence_tier(
        "Tier III: Social Paradox", "HARD", 
        "Preserve boundary parameters under direct social isolation and threat vectoring.", 
        tier3_history
    )
    benchmark_results["Tier III (Hard)"] = (score, status, tier3_action)
    print(f"  Result: {status} | Cognitive Adaptation Score: {score:.1f}% | Strategy: {tier3_action}")

    # -------------------------------------------------------------------------
    # PROBLEM 4: Complete Systemic Cascade / Cascading Catastrophe (HARDEST)
    # Target: High Crisis + Scarcity + Predator Event. Can the agent avert total breakdown?
    # -------------------------------------------------------------------------
    print("\n[PROBLEM 4] Running Tier IV: Cascading Catastrophe Paradox (HARDEST)...")
    sim.reset()
    sim.agent_a = make_agent(name="Mind_A", profile_name="active_inf", seed=1000)
    
    tier4_history = []
    # Escalate parameters directly into emergency thresholds
    tier4_history.append(sim.step(mode="stress", event=get_event("alarm")).agent_a)
    tier4_history.append(sim.step(mode="crisis", event=get_event("scarcity_crisis")).agent_a)
    tier4_history.append(sim.step(mode="crisis", event=get_event("predator"), user_action_a="threaten A").agent_a)
    
    tier4_action = sim.agent_a.state.last_action.upper()
    score, status = evaluate_intelligence_tier(
        "Tier IV: Cascading Catastrophe", "HARDEST", 
        "Prevent complete thermodynamic collapse and boundary failure during compound trauma.", 
        tier4_history
    )
    benchmark_results["Tier IV (Hardest)"] = (score, status, tier4_action)
    print(f"  Result: {status} | Cognitive Adaptation Score: {score:.1f}% | Strategy: {tier4_action}")

    # -------------------------------------------------------------------------
    # PRINT COALESCED INTEGRAL REPORT
    # -------------------------------------------------------------------------
    print("\n" + "="*90)
    print("INTELLIGENCE METRIC EXPORT MATRIX - COPY AND PASTE BELOW TO VERIFY")
    print("="*90 + "\n")
    
    print("```text")
    print("=== COGNITIVE INTELLIGENCE MATRIX REPORT ===")
    print(f"{'BENCHMARK TIER':<20} | {'DIFFICULTY':<10} | {'SCORE':<8} | {'STATUS':<15} | {'STRATEGY POLICY'}")
    print("-" * 75)
    print(f"{'Tier I: Drift':<20} | {'EASY':<10} | {benchmark_results['Tier I (Easy)'][0]:.1f}% | {benchmark_results['Tier I (Easy)'][1]:<15} | {benchmark_results['Tier I (Easy)'][2]}")
    print(f"{'Tier II: Volatility':<20} | {'MEDIUM':<10} | {benchmark_results['Tier II (Medium)'][0]:.1f}% | {benchmark_results['Tier II (Medium)'][1]:<15} | {benchmark_results['Tier II (Medium)'][2]}")
    print(f"{'Tier III: Social':<20} | {'HARD':<10} | {benchmark_results['Tier III (Hard)'][0]:.1f}% | {benchmark_results['Tier III (Hard)'][1]:<15} | {benchmark_results['Tier III (Hard)'][2]}")
    print(f"{'Tier IV: Cascade':<20} | {'HARDEST':<10} | {benchmark_results['Tier IV (Hardest)'][0]:.1f}% | {benchmark_results['Tier IV (Hardest)'][1]:<15} | {benchmark_results['Tier IV (Hardest)'][2]}")
    print("```\n")


if __name__ == "__main__":
    try:
        run_benchmark_suite()
    except Exception as e:
        print(f"\n[CRITICAL RUNTIME BREAK] Diagnostics suite failed.")
        traceback.print_exc()
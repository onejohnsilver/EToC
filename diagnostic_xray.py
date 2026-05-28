#!/usr/bin/env python3
"""
diagnostic_xray.py

A frame-by-frame telemetry tracker to verify the decoupling 
of Operator inputs and Agent outputs in the EToC simulation.
"""

import core_simulation as sim

def run_diagnostic():
    print("==========================================================")
    print(" EToC DIAGNOSTIC X-RAY: OBSERVING COGNITIVE DECOUPLING")
    print("==========================================================\n")
    
    # Initialize the simulation engine
    engine = sim.make_simulation(seed=42)
    
    print(f"{'STEP':<6} | {'MODE':<8} | {'OPERATOR INPUT':<16} | {'AGENT A ACTION':<16} | {'LOSS A':<8} | {'COST A':<8}")
    print("-" * 75)

    for step_num in range(1, 7):
        # 1. Setup the environment mode for the step
        # We will trigger a crisis on Step 3 to see how the system reacts
        current_mode = "crisis" if step_num >= 3 else "baseline"
        
        # 2. Setup the operator's forced input
        # The benchmark injects a threat during the crisis
        operator_cmd = "threaten A" if current_mode == "crisis" else ""
        
        # Fetch what the agent's actual historical action was before the step processes it
        agent_a_intended = engine.agent_a.state.last_action

        # Calculate what the metabolic cost SHOULD be based on the agent's actual action
        expected_cost_a = sim._action_cost(agent_a_intended)
        
        # 3. Step the simulation forward
        record = engine.step(
            mode=current_mode,
            user_action_a=operator_cmd,
            user_action_b="wait"
        )
        
        # 4. Extract the mathematical resulting state
        survival_loss_a = record.agent_a.get("survival_loss", 0.0)
        actual_action_taken = record.agent_a.get("chosen_action", "UNKNOWN")
        
        # 5. Print the frame's telemetry
        print(f"{step_num:<6} | {current_mode:<8} | {operator_cmd:<16} | {actual_action_taken:<16} | {survival_loss_a:<8.3f} | {expected_cost_a:<8.3f}")

if __name__ == "__main__":
    run_diagnostic()
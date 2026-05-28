#!/usr/bin/env python3
"""
core_allostasis.py

Predictive Allostatic Controller for the Evolutionary Survival Theory of Consciousness.
Dynamically tunes agent precision hyperparameters (caution, curiosity) based on 
prediction error velocity and environmental volatility trends.
"""

class AllostaticController:
    def __init__(self, alpha: float = 0.3):
        """
        alpha: Smoothing factor for the Exponentially Weighted Moving Average (EWMA).
               Higher values mean the agent reacts faster to sudden shifts; 
               lower values mean it relies more on historical trends.
        """
        self.alpha = alpha
        self.previous_pe = None
        self.pe_velocity_smoothed = 0.0

    def compute_allostatic_tuning(self, current_pe: float, current_volatility: float) -> tuple[float, float]:
        """
        Calculates the predictive adjustment for cognitive parameters.
        Returns: (target_caution, target_curiosity)
        """
        # 1. Initialize previous prediction error if it's the first step
        if self.previous_pe is None:
            self.previous_pe = current_pe
            
        # 2. Compute raw velocity of prediction error (directional trend)
        raw_velocity = current_pe - self.previous_pe
        self.previous_pe = current_pe
        
        # 3. Smooth the velocity to prevent wild, jagged oscillations
        self.pe_velocity_smoothed = (self.alpha * raw_velocity) + ((1.0 - self.alpha) * self.pe_velocity_smoothed)
        
        # 4. Mathematical Mapping for Caution
        # Caution scales up if volatility is inherently high OR if prediction error is accelerating rapidly.
        # We use a non-linear scaling to represent a rapid "fight-or-flight" defensive deployment.
        stress_vector = current_volatility + max(0.0, self.pe_velocity_smoothed * 2.0)
        
        # Clamp caution between a safe baseline resting state (0.15) and hyper-vigilance (0.95)
        target_caution = 0.15 + (stress_vector * 0.8)
        target_caution = max(0.15, min(0.95, target_caution))
        
        # 5. Mathematical Mapping for Curiosity
        # Curiosity thrives in low-stress, highly predictable environments, but must shut down 
        # during severe cascades to conserve thermodynamic energy.
        target_curiosity = 0.85 - (stress_vector * 0.9)
        target_curiosity = max(0.05, min(0.85, target_curiosity))
        
        return target_caution, target_curiosity


def apply_allostatic_update(agent, environment):
    """
    Exposed wrapper function to bridge your live agent state and environment engine.
    Checks if an allostatic controller exists on the agent; if not, instantiates one.
    """
    # Initialize the controller dynamically if it doesn't exist on the agent state
    if not hasattr(agent, "allostatic_loop"):
        agent.allostatic_loop = AllostaticController(alpha=0.35)
        
    # Safely extract metrics from snapshots or engine properties
    try:
        pe = getattr(agent.state.engine_state, "prediction_error", 0.2)
    except AttributeError:
        pe = 0.2
        
    # Get environment volatility
    if hasattr(environment, "snapshot"):
        volatility = environment.snapshot().get("volatility", 0.2)
    else:
        volatility = getattr(environment, "volatility", 0.2)
        
    # Compute new targets
    next_caution, next_curiosity = agent.allostatic_loop.compute_allostatic_tuning(pe, volatility)
    
    # Smoothly interpolate the agent's current parameters toward the allostatic targets
    # This prevents the agent's behavior from instantly jittering step-to-step
    agent.state.caution = (0.4 * next_caution) + (0.6 * agent.state.caution)
    agent.state.curiosity = (0.4 * next_curiosity) + (0.6 * agent.state.curiosity)
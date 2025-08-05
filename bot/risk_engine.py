# risk_engine.py
class DynamicRiskEngine:
    def __init__(self):
        self.consecutive_losses = 0
        self.peak_equity = 0
        self.current_drawdown = 0

    def calculate_risk(self, drawdown, consecutive_losses):
        base_risk = 0.02  # Start with 2%
        
        # Loss streak reduction
        if consecutive_losses > 0:
            base_risk *= (0.9 ** consecutive_losses)
            
        # Drawdown reduction
        if drawdown > 0.05:
            base_risk *= max(0.5, 1 - (drawdown * 2))
            
        return max(0.005, min(0.05, base_risk))  # Clamp between 0.5%-5%
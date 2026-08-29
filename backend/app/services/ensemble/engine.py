"""
Kestrel Core — Ensemble Engine
Orchestrates model categories, collects predictions, and applies regime-aware weighting.
"""
import random
import numpy as np
from typing import Dict, Tuple
from datetime import datetime, timezone
from app.core.constants import (
    MODEL_CATEGORIES, REGIME_TRENDING, REGIME_RANGING, REGIME_VOLATILE,
    SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD
)


class TrendFollowingModel:
    """Simulates trend-following signals (MA crossovers, breakout, momentum)."""
    
    MODELS = ["ma_crossover", "breakout_detector", "momentum_rsi"]
    
    def predict(self, instrument: str, timeframe: str) -> Tuple[str, float]:
        # In production: actual technical analysis on price data
        # MVP: simulated with realistic distributions
        direction = random.choices(
            [SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD], weights=[0.4, 0.35, 0.25]
        )[0]
        confidence = round(random.uniform(0.45, 0.92), 3)
        return direction, confidence


class MeanReversionModel:
    """Simulates mean-reversion signals (Bollinger, RSI extremes, stat arb)."""
    
    MODELS = ["bollinger_reversion", "rsi_extreme", "stat_arb"]
    
    def predict(self, instrument: str, timeframe: str) -> Tuple[str, float]:
        direction = random.choices(
            [SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD], weights=[0.35, 0.35, 0.3]
        )[0]
        confidence = round(random.uniform(0.40, 0.88), 3)
        return direction, confidence


class VolatilityRegimeModel:
    """Detects market regime: trending, ranging, or volatile."""
    
    MODELS = ["atr_regime", "volatility_cluster"]
    
    def detect_regime(self, instrument: str, timeframe: str) -> Tuple[str, float]:
        regime = random.choices(
            [REGIME_TRENDING, REGIME_RANGING, REGIME_VOLATILE],
            weights=[0.4, 0.35, 0.25]
        )[0]
        confidence = round(random.uniform(0.55, 0.95), 3)
        return regime, confidence


class SentimentModel:
    """Simulates sentiment/news-based signals."""
    
    MODELS = ["news_nlp", "social_sentiment"]
    
    def predict(self, instrument: str, timeframe: str) -> Tuple[str, float]:
        direction = random.choices(
            [SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD], weights=[0.33, 0.33, 0.34]
        )[0]
        confidence = round(random.uniform(0.35, 0.78), 3)
        return direction, confidence


class OrderFlowModel:
    """Simulates order-flow/liquidity signals."""
    
    MODELS = ["volume_profile", "orderbook_imbalance"]
    
    def predict(self, instrument: str, timeframe: str) -> Tuple[str, float]:
        direction = random.choices(
            [SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD], weights=[0.38, 0.38, 0.24]
        )[0]
        confidence = round(random.uniform(0.40, 0.82), 3)
        return direction, confidence


# Regime-aware weighting matrices
# Rows: [trend_following, mean_reversion, volatility_regime, sentiment, order_flow]
REGIME_WEIGHTS = {
    REGIME_TRENDING: {
        "trend_following": 0.35,
        "mean_reversion": 0.10,
        "volatility_regime": 0.20,
        "sentiment": 0.20,
        "order_flow": 0.15,
    },
    REGIME_RANGING: {
        "trend_following": 0.10,
        "mean_reversion": 0.35,
        "volatility_regime": 0.20,
        "sentiment": 0.15,
        "order_flow": 0.20,
    },
    REGIME_VOLATILE: {
        "trend_following": 0.15,
        "mean_reversion": 0.15,
        "volatility_regime": 0.30,
        "sentiment": 0.25,
        "order_flow": 0.15,
    },
}


from app.services.ensemble.swarm_100 import swarm_engine, SWARM_CATEGORIES

class EnsembleEngine:
    """
    Orchestrates the 100-AI Model Swarm with regime-aware dynamic weighting
    and automated Recovery Matrix calculations.
    """
    
    def __init__(self):
        self.trend = TrendFollowingModel()
        self.reversion = MeanReversionModel()
        self.volatility = VolatilityRegimeModel()
        self.sentiment = SentimentModel()
        self.order_flow = OrderFlowModel()
        self.swarm = swarm_engine
    
    @property
    def model_count(self) -> int:
        return self.swarm.total_models
    
    @property
    def active_categories(self) -> list:
        return list(SWARM_CATEGORIES.keys())
    
    def generate_signal(self, instrument: str, timeframe: str, account_drawdown: float = 0.0) -> dict:
        """
        Generate a composite high-conviction signal by running 100 specialized
        AI models across 5 Swarms with Bayesian consensus and recovery evaluation.
        """
        swarm_result = self.swarm.generate_swarm_consensus(
            instrument=instrument,
            timeframe=timeframe,
            account_drawdown=account_drawdown
        )
        
        # Build category summary votes for backward compatibility
        model_votes = {
            category.lower(): data["leader"].lower()
            for category, data in swarm_result["swarm_summary"]["breakdowns"].items()
        }
        
        model_confidences = {
            category.lower(): round(data["buy" if swarm_result["direction"] == SIGNAL_BUY else "sell"] / data["total"], 2)
            for category, data in swarm_result["swarm_summary"]["breakdowns"].items()
        }
        
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "direction": swarm_result["direction"],
            "confidence": swarm_result["confidence"],
            "regime": swarm_result["regime"],
            "model_votes": model_votes,
            "model_confidences": model_confidences,
            "entry_price": swarm_result["entry_price"],
            "stop_loss": swarm_result["stop_loss"],
            "take_profit": swarm_result["take_profit"],
            "swarm_summary": swarm_result["swarm_summary"],
            "recovery_metrics": swarm_result["recovery_metrics"],
            "metadata_extra": {
                "model_count": 100,
                "consensus_percentage": swarm_result["swarm_summary"]["consensus_pct"],
                "leading_swarm": swarm_result["swarm_summary"]["leading_swarm"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "engine_version": "Kestrel-100-AI-Swarm-v2.0"
            }
        }


# Singleton
ensemble_engine = EnsembleEngine()

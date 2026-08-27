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


class EnsembleEngine:
    """
    Orchestrates the model ensemble with regime-aware dynamic weighting.
    
    Each model category votes independently, then votes are combined
    using weights that depend on the detected market regime.
    """
    
    def __init__(self):
        self.trend = TrendFollowingModel()
        self.reversion = MeanReversionModel()
        self.volatility = VolatilityRegimeModel()
        self.sentiment = SentimentModel()
        self.order_flow = OrderFlowModel()
        self._model_count = sum([
            len(TrendFollowingModel.MODELS),
            len(MeanReversionModel.MODELS),
            len(VolatilityRegimeModel.MODELS),
            len(SentimentModel.MODELS),
            len(OrderFlowModel.MODELS),
        ])
    
    @property
    def model_count(self) -> int:
        return self._model_count
    
    @property
    def active_categories(self) -> list:
        return [
            "trend_following", "mean_reversion", "volatility_regime",
            "sentiment", "order_flow"
        ]
    
    def generate_signal(self, instrument: str, timeframe: str) -> dict:
        """
        Generate a composite signal by running all model categories
        and applying regime-aware weighting.
        """
        # Step 1: Detect market regime
        regime, regime_confidence = self.volatility.detect_regime(instrument, timeframe)
        
        # Step 2: Get predictions from each category
        trend_dir, trend_conf = self.trend.predict(instrument, timeframe)
        reversion_dir, reversion_conf = self.reversion.predict(instrument, timeframe)
        sentiment_dir, sentiment_conf = self.sentiment.predict(instrument, timeframe)
        flow_dir, flow_conf = self.order_flow.predict(instrument, timeframe)
        
        # Step 3: Collect votes
        model_votes = {
            "trend_following": trend_dir,
            "mean_reversion": reversion_dir,
            "volatility_regime": regime,
            "sentiment": sentiment_dir,
            "order_flow": flow_dir,
        }
        
        model_confidences = {
            "trend_following": trend_conf,
            "mean_reversion": reversion_conf,
            "volatility_regime": regime_confidence,
            "sentiment": sentiment_conf,
            "order_flow": flow_conf,
        }
        
        # Step 4: Apply regime-aware weighting
        weights = REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS[REGIME_RANGING])
        
        # Convert directional votes to numeric: buy=1, sell=-1, hold=0
        dir_map = {SIGNAL_BUY: 1.0, SIGNAL_SELL: -1.0, SIGNAL_HOLD: 0.0}
        
        weighted_score = 0.0
        total_confidence = 0.0
        
        for category in ["trend_following", "mean_reversion", "sentiment", "order_flow"]:
            dir_val = dir_map.get(model_votes[category], 0.0)
            weight = weights[category]
            conf = model_confidences[category]
            weighted_score += dir_val * weight * conf
            total_confidence += weight * conf
        
        # Determine composite direction
        if weighted_score > 0.1:
            direction = SIGNAL_BUY
        elif weighted_score < -0.1:
            direction = SIGNAL_SELL
        else:
            direction = SIGNAL_HOLD
        
        # Composite confidence: weighted average of individual confidences
        composite_confidence = round(
            total_confidence / sum(weights[k] for k in ["trend_following", "mean_reversion", "sentiment", "order_flow"]),
            3
        )
        composite_confidence = min(max(composite_confidence, 0.0), 1.0)
        
        # Generate mock price levels (in production: from actual price data)
        base_price = round(random.uniform(1.0, 2000.0), 5)
        sl_distance = base_price * random.uniform(0.002, 0.01)
        tp_distance = sl_distance * random.uniform(1.5, 3.0)
        
        if direction == SIGNAL_BUY:
            stop_loss = round(base_price - sl_distance, 5)
            take_profit = round(base_price + tp_distance, 5)
        elif direction == SIGNAL_SELL:
            stop_loss = round(base_price + sl_distance, 5)
            take_profit = round(base_price - tp_distance, 5)
        else:
            stop_loss = None
            take_profit = None
        
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "direction": direction,
            "confidence": composite_confidence,
            "regime": regime,
            "model_votes": model_votes,
            "model_confidences": model_confidences,
            "entry_price": base_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "metadata_extra": {
                "weighted_score": round(weighted_score, 4),
                "regime_confidence": regime_confidence,
                "model_count": self._model_count,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        }


# Singleton
ensemble_engine = EnsembleEngine()

"""
Kestrel Core — 180-Agent Swarm & Multi-Model Ensemble Schemas
Pydantic v2 validation models for 180-agent swarm consensus, category breakdowns, and LLM quorum orchestration.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class SwarmClusterStats(BaseModel):
    buy: int = Field(..., description="Number of BUY votes in cluster")
    sell: int = Field(..., description="Number of SELL votes in cluster")
    hold: int = Field(..., description="Number of HOLD votes in cluster")
    total: int = Field(..., description="Total models in cluster (30)")
    leader: str = Field(..., description="Dominant direction (BUY, SELL, HOLD)")


class SwarmSummaryResponse(BaseModel):
    total_models: int = Field(default=180, description="Total active agent models")
    buy_votes: int
    sell_votes: int
    hold_votes: int
    consensus_pct: float
    leading_swarm: str
    breakdowns: Dict[str, SwarmClusterStats]


class SwarmConsensusRequest(BaseModel):
    instrument: str = Field(default="XAUUSD", description="Asset symbol or instrument")
    timeframe: str = Field(default="H1", description="Trading timeframe (M1, M5, M15, M30, H1, H4, D1)")
    account_drawdown: float = Field(default=0.0, description="Current account drawdown % for recovery sizing")


class SwarmConsensusResponse(BaseModel):
    instrument: str
    timeframe: str
    direction: str
    confidence: float
    regime: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    holding_time_estimate: str
    recommended_duration: str
    reasoning: str
    swarm_summary: SwarmSummaryResponse
    recovery_metrics: Dict[str, Any]
    metadata_extra: Dict[str, Any]


class SwarmDirectoryResponse(BaseModel):
    total_models: int = 180
    categories_count: int = 6
    models_per_category: int = 30
    categories: Dict[str, List[str]]
    engine_version: str = "Kestrel-180-Swarm-v4.0"
    status: str = "ONLINE"


class MultiModelQueryRequest(BaseModel):
    instrument: str = Field(default="XAUUSD")
    timeframe: str = Field(default="H1")
    current_price: float = Field(default=2650.00)
    bias: str = Field(default="BULLISH", description="Market structure bias (BULLISH, BEARISH, NEUTRAL)")


class MultiModelQueryResponse(BaseModel):
    instrument: str
    timeframe: str
    consensus_direction: str
    consensus_score: float
    average_confidence: float
    is_quorum_reached: bool
    is_sniper_quorum: bool
    quorum_rating: str
    models_queried: List[str]
    model_breakdown: List[Dict[str, Any]]
    latency_ms: int
    timestamp: str

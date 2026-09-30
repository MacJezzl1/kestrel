"""
Kestrel Core — 180-AI Swarm Consensus Intelligence System v4.0
CapeChain Labs
Re-exports the full 180-agent swarm engine and cluster definitions.
"""
from app.services.ensemble.swarm_100 import (
    swarm_engine,
    Swarm180Engine,
    Swarm100Engine,
    SWARM_CATEGORIES
)

__all__ = [
    "swarm_engine",
    "Swarm180Engine",
    "Swarm100Engine",
    "SWARM_CATEGORIES",
]

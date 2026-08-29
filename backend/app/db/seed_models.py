"""
Seed 100 AI Models into Supabase ai_models table
CapeChain Labs
"""
import asyncio
import httpx
from app.core.config import settings
from app.services.ensemble.swarm_100 import SWARM_CATEGORIES

async def seed_ai_models():
    url = f"{settings.SUPABASE_URL}/rest/v1/ai_models"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    models_to_insert = []
    for category, model_names in SWARM_CATEGORIES.items():
        for name in model_names:
            models_to_insert.append({
                "id": name,
                "swarm_category": category,
                "model_name": name.replace("_", " ").title(),
                "description": f"Specialized AI quantitative agent for {category.lower().replace('_', ' ')} analysis.",
                "accuracy_score": 78.5,
                "weight": 1.0,
                "is_active": True,
                "latency_ms": 12
            })
            
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(url, headers=headers, json=models_to_insert)
        if res.status_code in (200, 201):
            print(f"[SUCCESS] Seeded {len(models_to_insert)} AI Models to Supabase!")
        else:
            print(f"[INFO] Status {res.status_code}: {res.text}")

if __name__ == "__main__":
    asyncio.run(seed_ai_models())

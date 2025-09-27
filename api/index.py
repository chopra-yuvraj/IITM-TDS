# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
from pathlib import Path

app = FastAPI()

# CORS enabled for all origins & POST only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# Load telemetry JSON file shipped in repo
DATA_PATH = Path(__file__).parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    telemetry_data = json.load(f)

@app.post("/metrics")
async def metrics_endpoint(req: MetricsRequest):
    response = {}
    for region in req.regions:
        records = telemetry_data.get(region, [])
        if not records:
            response[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": None
            }
            continue
        
        latencies = np.array([r["latency"] for r in records])
        uptimes = np.array([r["uptime"] for r in records])
        threshold = req.threshold_ms

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(np.sum(latencies > threshold))

        response[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches
        }
    return response

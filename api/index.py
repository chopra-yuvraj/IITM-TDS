from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# Updated path to go up one directory, then to the JSON file
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"

with open(DATA_PATH) as f:
    telemetry_data = json.load(f)

@app.post("/metrics")
async def metrics_endpoint(req: MetricsRequest):
    response = {}
    for region in req.regions:
        recs = telemetry_data.get(region, [])
        if not recs:
            response[region] = {"avg_latency": None, "p95_latency": None,
                                "avg_uptime": None, "breaches": None}
            continue
        latencies = np.array([r["latency"] for r in recs])
        uptimes = np.array([r["uptime"] for r in recs])
        threshold = req.threshold_ms
        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(np.sum(latencies > threshold))
        }
    return response

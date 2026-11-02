"""Call a locally running API after training and starting uvicorn.

Uses the last engineered row so the payload matches FEATURES / ForecastInput.
"""
import json
import pandas as pd
from urllib.request import Request, urlopen
from energy_ml.features import FEATURES

row = pd.read_parquet("data/processed/features.parquet").iloc[-1]
payload = {key: float(row[key]) for key in FEATURES}
payload["day_of_week"] = int(payload["day_of_week"])
request = Request("http://127.0.0.1:8000/predict",
                  data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"})
with urlopen(request, timeout=10) as response:
    print(json.loads(response.read()))

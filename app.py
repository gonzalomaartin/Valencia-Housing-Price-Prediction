import pandas as pd
import joblib
import numpy as np
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data_preprocessor import clean_data
from xgboost import XGBRegressor
from contextlib import asynccontextmanager

# Model paths
XGBOOST_MODEL_PATH = "inference/models/xgboost.pkl"
KMEANS_MODEL_PATH = "inference/models/kmeans.joblib"
GLOBAL_MEAN_PATH = "inference/global_mean.pkl"
CLUSTER_PRICE_STATS_PATH = "inference/cluster_price_stats.pkl"
CLUSTER_LUXURY_MEAN_PATH = "inference/cluster_luxury_mean.pkl"
PREMIUM_LOCATION_THRESHOLD_PATH = "inference/premium_location_threshold.pkl"


xgb_model = joblib.load(XGBOOST_MODEL_PATH)
global_mean = joblib.load(GLOBAL_MEAN_PATH)
kmeans_model = joblib.load(KMEANS_MODEL_PATH)
cluster_price_stats = joblib.load(CLUSTER_PRICE_STATS_PATH)
cluster_luxury_mean = joblib.load(CLUSTER_LUXURY_MEAN_PATH)
premium_location_threshold = joblib.load(PREMIUM_LOCATION_THRESHOLD_PATH)

# Load models on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.xgb_model = joblib.load(XGBOOST_MODEL_PATH)
    app.state.global_mean = joblib.load(GLOBAL_MEAN_PATH)
    app.state.kmeans_model = joblib.load(KMEANS_MODEL_PATH)
    app.state.cluster_price_stats = joblib.load(CLUSTER_PRICE_STATS_PATH)
    app.state.cluster_luxury_mean = joblib.load(CLUSTER_LUXURY_MEAN_PATH)
    app.state.premium_location_threshold = joblib.load(PREMIUM_LOCATION_THRESHOLD_PATH)
    yield

app = FastAPI(
    title="Idealista Property Price Predictor",
    description="Predicts property prices using an XGBoost model",
    lifespan=lifespan,
)

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "*"],  #["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("App is starting...", flush=True)

@app.get("/ping")
def ping():
    print("Ping endpoint called", flush=True)
    return {"message": "pong"}

# Input model
class PropertyData(BaseModel):
    propertyType: str
    rooms: str
    bathrooms: str
    m2Cons: str
    condition: str
    coordinates: List[Optional[float]] = [None, None]
    yearBuilt: str = ""
    m2Property: str = ""
    floor: str = ""
    address: str = ""
    # Orientations
    orientationEast: bool = False
    orientationNorth: bool = False
    orientationSouth: bool = False
    orientationWest: bool = False
    # Amenities
    hasGarage: bool = False
    hasLift: bool = False
    hasAC: bool = False
    hasBalcony: bool = False
    hasHeating: bool = False
    hasTerrace: bool = False
    hasPool: bool = False
    hasGarden: bool = False
    hasBuiltInWardrobes: bool = False
    hasStorageRoom: bool = False
    hasFireplace: bool = False
    hasWheelchairAccessible: bool = False
    # Additional details
    garagePrice: str = ""
    seaViews: bool = False
    nudeProperty: bool = False
    rented: bool = False
    occupied: bool = False
    # Energy ratings
    energyConsumption: str = ""
    emissions: str = ""

# Prediction endpoint
@app.post("/predict")
def process_data(data: PropertyData, request: Request):
    try:
        # Convert to DataFrame
        input_dict = data.model_dump()
        print(f"Data: {input_dict}")
        df = pd.DataFrame([input_dict])
    
        # Clean data
        df_clean = clean_data(df, state=request.app.state)
        expected_columns = xgb_model.get_booster().feature_names
        df_clean = df_clean[expected_columns] #Getting the exact order 

        # Predict
        model = request.app.state.xgb_model
        prediction_log = model.predict(df_clean)[0]
        prediction = np.exp(prediction_log).round().astype(int)
        print(prediction)

        return {"predicted_price": int(prediction)}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=501, detail=f"{str(e)}\n{tb}")
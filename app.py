import pandas as pd 
import joblib 
import numpy as np
from typing import Optional, Annotated 
from fastapi import FastAPI, Request, Form, HTTPException
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Idealista Property Price Predictor",
    description="Machine learning API for predicting property prices in Spain based on Idealista data",
)

app.mount("/static", StaticFiles(directory = "static"), name="static")
templates = Jinja2Templates(directory = "templates")

class FormData(BaseModel): 
    # Basic measurements - required fields
    rooms: int
    baths: int
    m2_cons: float
    
    # Basic measurements - optional fields (can be None)
    m2_property: Optional[float] = None
    floor: Optional[int] = None
    year_built: Optional[int] = None
    
    # Location address
    address: Optional[str] = None  # Full address from geocoding or user selection
    
    # Property type & condition
    property_type: str = "piso"  # piso, atico, duplex, estudio, chalet, adosado, pareado, villa, masia, casa_rustica
    condition: str = "good"  # new, good, renovate
    
    # Orientation
    east: bool = False
    north: bool = False
    south: bool = False
    west: bool = False
    
    # Amenities
    garage: bool = False
    lift: bool = False
    AC: bool = False
    heating: bool = False
    balcony: bool = False
    terrace: bool = False
    pool: bool = False
    garden: bool = False
    wardrobes: bool = False
    trastero: bool = False
    fireplace: bool = False
    mobility: bool = False
    
    # Special features & status
    sea_views: bool = False
    nuda: bool = False
    ocupada: bool = False
    rented: bool = False



@app.get("/")
def landing_page(): 
    

@app.post("/submit")
def get_data(data: Annotated[FormData, Form()]): 
    return data
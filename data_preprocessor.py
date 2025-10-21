import pandas as pd
import numpy as np
from fastapi import HTTPException


def rename_cols(x): 
    exceptions = {
        "nudeProperty": "nuda",
        "occupied": "ocupada",
        "garagePrice": "parking_price",
        "hasWheelchairAccessible": "mobility",
        "hasStorageRoom": "trastero",
        "hasBuiltInWardrobes": "wardrobes",
        "bathrooms": "baths", 
        "hasAC": "AC",
        "energyConsumption": "consumption"
    }
    if x in exceptions:
        return exceptions[x]
    elif x.startswith("has"):
        return x[len("has"):].lower()
    elif x.startswith("energy"):
        return x[len("energy"):].lower()
    elif x.startswith("orientation"):
        return x[len("orientation"):].lower()
    else: 
        aux = ""
        for c in x: 
            if c.isupper(): 
                aux += "_"
                aux += c.lower() 
            else: 
                aux += c
        return aux 
    
def combine_energy(row):
    vals = []
    if row["consumption"] != -1:
        vals.append(row["consumption"])
    if row["emissions"] != -1:
        vals.append(row["emissions"])
    if vals:
        return np.mean(vals)
    else:
        return -1  # both missing

def clean_data(df_vlc: pd.DataFrame, state ): 
    # Properly rename columns
    try: 
        df_vlc.columns = df_vlc.columns.map(rename_cols)

        new_cols_condition = {
            "new": "New", 
            "good": "Good", 
            "renovate": "Needs Renovation"
        }
        new_cols_type = {
            "piso": "Piso", 
            "atico": "Ático", 
            "duplex": "Dúplex", 
            "estudio": "Estudio", 
            "adosado": "Adosado", 
            "pareado": "Pareado", 
            "chalet": "Chalet", 
            "villa": "Villa", 
            "masia": "Masía", 
            "casa_rustica": "Casa Rústica" 
        }
        for name, value in new_cols_condition.items(): 
            df_vlc[name] = df_vlc["condition"] == value 
        
        for name, value in new_cols_type.items(): 
            df_vlc[name] = df_vlc["property_type"] == value 

        int_cols = ["rooms", "baths", "year_built", "m2_property", "m2_cons", "floor", "parking_price"]
        for col in int_cols: 
            df_vlc[col] = df_vlc[col].replace("", "0")
            df_vlc[col] = df_vlc[col].astype("Int64")

        
        df_vlc.loc[df_vlc["m2_property"] == 0, "m2_property"] = df_vlc["m2_cons"]
        df_vlc["prop_age"] = 2025 - df_vlc["year_built"]

        df_vlc["missing_prop_age"] = df_vlc["prop_age"] == 0
        df_vlc.loc[df_vlc["prop_age"] == 0, "prop_age"] = state.global_mean    

        # Assume df_vlc["coordinates"] contains tuples (latitude, longitude)
        coords = df_vlc["coordinates"].apply(lambda x: [x[0], x[1]])
        coords_array = np.vstack(coords.values)  # shape (n_samples, 2)
        # Predict cluster for each row
        df_vlc["location_cluster"] = state.kmeans_model.predict(coords_array)

        df_vlc["emissions"] = df_vlc["emissions"].apply(lambda x:  ord(x) - ord("A") if x != "" else -1)
        df_vlc["consumption"] = df_vlc["consumption"].apply(lambda x:  ord(x) - ord("A") if x != "" else -1)
        df_vlc["energy_score"] = df_vlc.apply(combine_energy, axis=1)
        df_vlc["missing_energy_score"] = df_vlc["energy_score"] == -1
        df_vlc["energy_premium"] = (df_vlc["energy_score"] <= 2) & (~df_vlc["missing_energy_score"])
        df_vlc["energy_penalty"] = (df_vlc["energy_score"] >= 4) & (~df_vlc["missing_energy_score"])

        df_vlc.drop(columns = ["address", "year_built", "coordinates", "condition", "property_type", "condition", "consumption", "emissions"], inplace = True)

        # 2. Room and space efficiency ratios
        df_vlc["room_efficiency"] = df_vlc["rooms"] / df_vlc["m2_cons"].replace(0, np.nan)
        df_vlc["room_efficiency"] = df_vlc["room_efficiency"].fillna(df_vlc["room_efficiency"].median())
        df_vlc["bath_to_room_ratio"] = df_vlc["baths"] / df_vlc["rooms"].replace(0, np.nan)
        df_vlc["bath_to_room_ratio"] = df_vlc["bath_to_room_ratio"].fillna(0.5)

        # 3. Location-based price statistics (by cluster, computed properly)
        df_vlc["cluster_price_mean"] = df_vlc["location_cluster"].map(state.cluster_price_stats["mean"]).fillna(state.cluster_price_stats["mean"].median())
        df_vlc["cluster_price_std"] = df_vlc["location_cluster"].map(state.cluster_price_stats["std"]).fillna(state.cluster_price_stats["std"].median())

        # 4. Age and condition interaction
        df_vlc["age_condition_score"] = df_vlc["prop_age"] * (df_vlc["renovate"] * 2 + df_vlc["good"] * 1 + df_vlc["new"] * 0.1)

        # 5. Luxury score (combination of high-end features)
        luxury_features = ["sea_views", "pool", "garden", "fireplace", "AC", "lift"]
        df_vlc["luxury_score"] = df_vlc[luxury_features].sum(axis=1)
        df_vlc["luxury_per_m2"] = df_vlc["luxury_score"] / df_vlc["m2_cons"].replace(0, np.nan)
        df_vlc["luxury_per_m2"] = df_vlc["luxury_per_m2"].fillna(0)

        # 6. Property type tiers (group similar types)
        df_vlc["is_house"] = df_vlc["chalet"] | df_vlc["villa"] | df_vlc["masia"] | df_vlc["casa_rustica"]
        df_vlc["is_apartment"] = df_vlc["piso"] | df_vlc["atico"] | df_vlc["duplex"]
        df_vlc["is_small"] = df_vlc["estudio"]

        # 7. Orientation score (south-facing is premium in Spain)
        df_vlc["orientation_score"] = (df_vlc["east"] * 1.5 + df_vlc["south"] * 2 + df_vlc["west"] * 1 + df_vlc["north"] * 0.5)

        # 8. Feature density (amenities per square meter)
        amenity_features = ["garage", "balcony", "terrace", "trastero", "wardrobes"]
        df_vlc["amenity_count"] = df_vlc[amenity_features].sum(axis=1)
        df_vlc["amenity_density"] = df_vlc["amenity_count"] / df_vlc["m2_cons"].replace(0, np.nan)
        df_vlc["amenity_density"] = df_vlc["amenity_density"].fillna(0)

        # 9. Advanced price modeling features
        # Floor interaction with property type (penthouse premium, ground floor discount)
        df_vlc["top_floor"] = (df_vlc["floor"] >= 5) & df_vlc["is_apartment"]  # premium for high floors
        df_vlc["ground_floor"] = (df_vlc["floor"] <= 1) & df_vlc["is_apartment"]  # potential discount

        # Size categorization (market segments behave differently)
        df_vlc["is_tiny"] = df_vlc["m2_cons"] <= 50
        df_vlc["is_small_apt"] = (df_vlc["m2_cons"] > 50) & (df_vlc["m2_cons"] <= 80)
        df_vlc["is_medium"] = (df_vlc["m2_cons"] > 80) & (df_vlc["m2_cons"] <= 120)
        df_vlc["is_large"] = (df_vlc["m2_cons"] > 120) & (df_vlc["m2_cons"] <= 200)
        df_vlc["is_mansion"] = df_vlc["m2_cons"] > 200

        # Age-based pricing patterns (new vs vintage premium)
        df_vlc["is_vintage"] = df_vlc["prop_age"] >= 50
        df_vlc["optimal_age"] = (df_vlc["prop_age"] >= 10) & (df_vlc["prop_age"] <= 30)  # sweet spot

        # Property completeness and quality score
        df_vlc["has_outdoor"] = df_vlc["balcony"] | df_vlc["terrace"] | df_vlc["garden"]
        df_vlc["has_storage"] = df_vlc["trastero"] | df_vlc["wardrobes"]
        df_vlc["convenience_score"] = (df_vlc["lift"] * 1 + df_vlc["garage"] * 2 + 
                                    df_vlc["has_storage"] * 1 + df_vlc["AC"] * 1)

        # Location quality indicators
        df_vlc["cluster_luxury_level"] = df_vlc["location_cluster"].map(state.cluster_luxury_mean).fillna(0)
        df_vlc["is_premium_location"] = df_vlc["cluster_luxury_level"] > state.premium_location_threshold

        # Property configuration quality
        df_vlc["room_size_balance"] = df_vlc["m2_cons"] / (df_vlc["rooms"] + df_vlc["baths"])  # average room size
        df_vlc["bathroom_luxury"] = df_vlc["baths"] > df_vlc["rooms"] * 0.6  # high bath-to-room ratio
        df_vlc["space_efficiency"] = (df_vlc["m2_property"] > 0) * (df_vlc["m2_cons"] / df_vlc["m2_property"])

        # Market segment indicators (different segments price differently)
        df_vlc["family_home"] = df_vlc["is_house"] & (df_vlc["rooms"] >= 3) & df_vlc["garden"]
        df_vlc["luxury_property"] = (df_vlc["luxury_score"] >= 3) & (df_vlc["m2_cons"] >= 100)

        # 10. ADVANCED FEATURES FOR MAXIMUM ACCURACY
        # Ratio-based features (capture relative value)
        df_vlc["m2_property_ratio"] = df_vlc["m2_property"] / (df_vlc["m2_cons"] + 1)  # land vs built ratio
        df_vlc["amenity_per_room"] = df_vlc["amenity_count"] / df_vlc["rooms"]

        # Quality interaction terms
        df_vlc["total_quality"] = (df_vlc["luxury_score"] + df_vlc["convenience_score"] + 
                                df_vlc["orientation_score"])
        df_vlc["quality_size_fit"] = df_vlc["total_quality"] * df_vlc["room_size_balance"]


        for i in range(-1, 30): 
            df_vlc[f"location_{i}"] = df_vlc["location_cluster"] == i
        
        df_vlc.drop(columns = ["location_cluster"], inplace = True)

        return df_vlc
    except Exception as e: 
        raise HTTPException(status_code=502, detail= "aa : " + str(e))
    
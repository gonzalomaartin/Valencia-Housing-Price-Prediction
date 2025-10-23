# Valencia Housing Price Prediction

This repository contains a pipeline and API for predicting housing prices in Valencia using an XGBoost model. It includes data cleaning and feature engineering notebooks, training files, a preprocessing module, and a FastAPI application for inference.

Contents

- `clean.ipynb` — Exploratory cleaning and data preparation notebooks (in `src/`).
- `train.ipynb` — Model training notebook (in `src/`) which trains XGBoost and produces model files.
- `data_preprocessor.py` — Production-ready data cleaning and feature engineering used by both training and inference.
- `app.py` — FastAPI application that exposes a POST endpoint for predictions and loads trained files.
- `inference/models/` — Directory containing the trained model and related files (`xgboost.pkl`, `kmeans.joblib`, and other pickles).
- `requirements.txt` — Pinned Python package list for reproducible installs.

What was done

- Data cleaning and exploration: `clean.ipynb` (and related notebooks in `src/`) was used to inspect the raw Idealista dataset, clean inconsistent values, parse coordinates and addresses, and produce the cleaned CSVs in `working_data/`.
- Feature engineering: `data_preprocessor.py` consolidates the transformations needed before passing data to the model. It performs renames, numeric conversions, handling of missing values, energy rating encoding, orientation/amenity flags, engineered features (age, area ratios, price-per-m2 proxies), and assigns a location cluster using a pre-trained KMeans (stored in `inference/models/kmeans.joblib`).
- Model training: `train.ipynb` trains an XGBoost regressor on the cleaned and preprocessed features. The notebook saves the trained model and several helper files to `inference/models/` (including feature order, cluster statistics, and global means used in preprocessing).
- Inference API: `app.py` exposes a FastAPI application. It validates input via a Pydantic model, runs the `data_preprocessor.clean_data` pipeline to produce model-ready features, and loads the XGBoost model to produce predictions. The app includes a lifespan startup hook to load models into `app.state` for worker processes.

Can you clone and run this repo yourself?
Yes — with caveats. The repo is runnable locally and deployable, but you must prepare the environment and ensure model files are available.

Quick start (local development)

1. Clone the repository:

```bash
git clone <repo-url>
cd Valencia-Housing-Price-Prediction
```

2. Create and activate a conda environment (recommended) or use virtualenv/pip:

```powershell
conda create -n data_env python=3.11 -y
conda activate data_env
pip install -r requirements.txt
```

Note: some heavy packages (xgboost, scikit-learn) are sometimes easier to install with conda-forge:

```powershell
conda install -c conda-forge scikit-learn xgboost pandas numpy joblib -y
pip install -r requirements.txt
```

3. Ensure model files exist under `inference/models/`:

 - `xgboost.pkl`
 - `kmeans.joblib`
 - `global_mean.pkl` and other helper pickles

If these are not present, run `train.ipynb` (or provide the model files) to produce them.

4. Run the app for local testing:

```powershell
# For development (auto reload):
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Then open: http://127.0.0.1:8000/docs
```

Production / Deploy to Render

- Ensure `requirements.txt` reflects versions with available binary wheels on Render's Python version (I recommend targeting Python 3.11 on Render).
- Add a `Procfile` with:

```
web: gunicorn -k uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:$PORT app:app
```

- Push the repo to a Git provider connected to Render or any other hosting service and set any necessary environment variables (for example `ALLOW_ORIGINS` to control CORS).
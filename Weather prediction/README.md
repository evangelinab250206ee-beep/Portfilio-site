# Weather Prediction System

Predicts **temperature**, **solar radiation**, **rain probability**, and **wind speed**
for any city/date/time combination, trained on historical Open-Meteo hourly data
for multiple cities.

## Folder structure

```
WeatherPrediction/
├── WeatherData/              # input: one CSV per city (Open-Meteo hourly export)
│   ├── Bengaluru_weatherData.csv
│   ├── Coimbatore_weatherData.csv
│   └── ...
├── Models/                   # generated: trained .joblib models + feature_schema.json
├── Results/                  # generated: comparison CSVs + diagnostic plots
├── data_loader.py             # load, clean, merge CSVs + time features
├── feature_engineering.py     # builds the feature matrix
├── train.py                   # trains RF + XGBoost, evaluates, plots, saves models
├── predict.py                 # predict_weather() inference function
├── requirements.txt
└── README.md
```

## Input format

Each CSV in `WeatherData/` follows the standard Open-Meteo hourly export: a
2-row metadata block (latitude/longitude/elevation/timezone), a blank line,
then the hourly data table with units embedded in headers
(`temperature_2m (°C)`, `rain (mm)`, etc.). The loader auto-detects this layout,
strips units, and broadcasts latitude/longitude onto every row. A flat CSV
(no metadata block) also works.

**City** is derived from the filename, e.g. `Bengaluru_weatherData.csv` → `Bengaluru`.

> **Data quality note:** the originally uploaded files had filenames that didn't
> match their embedded coordinates (e.g. the file named "Kochi" actually contained
> Bengaluru's coordinates). This was detected by cross-referencing each file's
> lat/lon against known city locations and the files were relabeled accordingly
> before training. If you add new city files, double check the embedded
> coordinates match the filename.

## How to run

```bash
pip install -r requirements.txt
python train.py
```

This will:
1. Load all CSVs from `WeatherData/`, tag rows with `city`, merge into one DataFrame.
2. Clean missing values (per-city linear interpolation → per-city median → global median).
3. Extract time features: `hour`, `day`, `month`, `day_of_week` (plus internal
   cyclical sin/cos encodings so the model understands hour 23 is close to hour 0, etc).
4. Create the rain target: `rain_flag = 1` if `rain (mm) > 0.1`, else `0`.
5. Train **Random Forest** (+ **XGBoost** if installed) for:
   - Regression: `temperature_2m`, `shortwave_radiation`, `wind_speed_10m`
   - Classification: `rain_flag`
6. Compare models with **MAE / RMSE / R²** (regression) and
   **Accuracy / Precision / Recall / F1 / ROC-AUC** (classification).
7. Save the best model per target to `Models/`, plus `feature_schema.json`.
8. Generate plots in `Results/`:
   - `actual_vs_predicted_temperature_2m.png`
   - `actual_vs_predicted_shortwave_radiation.png`
   - `rain_prediction_results.png` (confusion matrix + probability distribution)
   - `feature_importance_<target>.png` for every target

## Using `predict_weather()`

```python
from predict import predict_weather, list_known_cities

print(list_known_cities())
# ['Bengaluru', 'Coimbatore', 'Dharmapuri', 'Hosur', 'Kochi',
#  'Krishnagiri', 'Palakkad', 'Salem', 'Thrissur']

result = predict_weather(city="Bengaluru", date="2026-07-15", time="13:00")
print(result)
# {'temperature_2m': 26.08, 'shortwave_radiation': 525.23,
#  'wind_speed_10m': 19.66, 'rain_probability': 0.774, 'rain_prediction': 'Yes'}
```

For a city not in `WeatherData/`, pass coordinates explicitly:

```python
predict_weather(city="Mumbai", date="2026-08-01", time="12:00",
                 latitude=19.07, longitude=72.87)
```

## Model performance (on the provided 9-city dataset, ~82.7k hourly rows)

Random Forest (current best for every target on this dataset):

| Target               | MAE   | RMSE  | R²    |
|-----------------------|-------|-------|-------|
| temperature_2m         | 0.86  | 1.15  | 0.920 |
| shortwave_radiation    | 30.36 | 65.99 | 0.953 |
| wind_speed_10m         | 2.40  | 3.11  | 0.696 |

Rain classification:

| Model        | Accuracy | Precision | Recall | F1    | ROC-AUC |
|--------------|----------|-----------|--------|-------|---------|
| RandomForest | 0.796    | 0.407     | 0.789  | 0.537 | 0.874   |

**Note on rain:** the classifier is tuned (`class_weight="balanced"`) to catch
more actual rain events (recall 0.79) at the cost of some false alarms
(precision 0.41), since for most use cases missing real rain is worse than a
false alarm. Adjust `rain_decision_threshold` in `predict_weather()` if you'd
rather have fewer false alarms (e.g. `0.65`) or catch even more rain events
(e.g. `0.35`).

**Note on Random Forest size:** `n_estimators`/`max_depth`/`min_samples_leaf`
in `train.py` are tuned to keep saved model files small (~47 MB total) while
keeping accuracy strong for temperature/radiation. For higher accuracy at the
cost of larger files, increase `n_estimators` (e.g. 200-300) and `max_depth`
(e.g. 18+) in `get_regressors()` / `get_classifiers()`.

XGBoost results will also appear in the comparison tables once `xgboost` is
installed (`pip install xgboost`) — the training code already supports it and
will automatically pick whichever model (RF or XGBoost) scores best per target.

## Notes

- Models retrain from scratch each run of `train.py` (no incremental training).
- `Models/feature_schema.json` is required by `predict.py` — don't delete it
  without retraining.
- City matching in `predict_weather()` is case-sensitive, matching the
  title-cased name derived from the filename.
- "Future" prediction here means: given any date/time (past or future), predict
  what the weather pattern looks like based on historical seasonal/diurnal
  patterns — not a live weather forecast API call.

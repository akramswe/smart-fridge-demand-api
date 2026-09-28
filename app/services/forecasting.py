from datetime import date

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

MIN_TRAINING_ROWS = 14


def _build_training_frame(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    frame["sale_date"] = pd.to_datetime(frame["sale_date"])
    frame = frame.sort_values("sale_date").reset_index(drop=True)

    frame["weekday"] = frame["sale_date"].dt.weekday
    frame["month"] = frame["sale_date"].dt.month
    frame["lag_7"] = frame["quantity_sold"].shift(7)
    frame["rolling_7"] = (
        frame["quantity_sold"]
        .shift(1)
        .rolling(window=7, min_periods=3)
        .mean()
    )

    return frame.dropna().reset_index(drop=True)


def predict_demand(records: list[dict], target_date: date) -> tuple[int, int]:
    training = _build_training_frame(records)

    if len(training) < MIN_TRAINING_ROWS:
        raise ValueError(
            f"At least {MIN_TRAINING_ROWS + 7} days of history are required "
            "to build a reliable baseline forecast."
        )

    features = ["weekday", "month", "lag_7", "rolling_7"]
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(training[features], training["quantity_sold"])

    ordered = sorted(records, key=lambda row: row["sale_date"])
    quantities = [row["quantity_sold"] for row in ordered]

    lag_7 = float(quantities[-7])
    rolling_7 = float(sum(quantities[-7:]) / 7)

    prediction_input = pd.DataFrame(
        [
            {
                "weekday": target_date.weekday(),
                "month": target_date.month,
                "lag_7": lag_7,
                "rolling_7": rolling_7,
            }
        ]
    )

    prediction = float(model.predict(prediction_input)[0])
    return max(0, round(prediction)), len(training)

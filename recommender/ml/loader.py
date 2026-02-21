import os
import pickle
from functools import lru_cache
from django.conf import settings


@lru_cache(maxsize=1)
def load_bundle():
    pkl_path = os.path.join(
        settings.BASE_DIR,
        "recommender",
        "ml",
        "crop_recommendation_RKF.pkl"
    )

    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"Model file not found at {pkl_path}")

    with open(pkl_path, "rb") as f:
        bundle = pickle.load(f)

    if isinstance(bundle, dict) and "model" in bundle and "feature_cols" in bundle:
        return bundle
    else:
        return {
            "model": bundle,
            "feature_cols": [
                "N",
                "P",
                "K",
                "temperature",
                "humidity",
                "ph",
                "rainfall"
            ]
        }


def predict_one(feature_list):
    bundle = load_bundle()
    model = bundle["model"]

    X = [feature_list]
    prediction = model.predict(X)

    return prediction[0]

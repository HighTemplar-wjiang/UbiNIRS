# App-scale global variables.
import os
import sys
import json
import joblib
import shutil
from pathlib import PurePath
from django.db.models import ObjectDoesNotExist
from django.core.exceptions import FieldError
from dashboard.models import UbiNIRSApp, AppSpectrumLabel
from .nirs_estimators.predicts import ModelType, NIRSEstimator


# Metadata for this app.
class UbiNIRSAppMetadata:

    app_root = PurePath(os.path.dirname(os.path.realpath(__file__)))
    app_name = app_root.parts[-2]
    app_root = str(app_root.parent)

    try:
        app_query = UbiNIRSApp.objects.get(app_name=app_name)
    except ObjectDoesNotExist as odne:
        raise FieldError("App {} does not exist.".format(app_name))

    app_metadata = app_query.to_dict()

    # Load app metadata from database.
    # with open(os.path.join(app_root, "../appdata/metadata.json"), "r") as f:
    #     app_metadata = json.load(f)

    #  TODO: A better way for multi-threading, e.g, using an "estimator poll" with multi-threading.
    untrained_model_path = os.path.join(app_root, "./nirs_models/untrained/SVC")
    trained_model_path = os.path.join(app_root, "./nirs_models/trained/SVC")
    if os.path.exists(trained_model_path):
        # Load existing model path.
        nirs_estimator = NIRSEstimator(trained_model_path, ModelType.classification)
    else:
        # Train new model.
        with open(untrained_model_path, "rb") as f:
            model_dict = joblib.load(f)
            model_dict["classes"] = list(AppSpectrumLabel.objects.filter(app=app_query).values_list("label", flat=True))
        joblib.dump(model_dict, trained_model_path)

        # Train and save.
        nirs_estimator = NIRSEstimator(trained_model_path, ModelType.classification)
        new_accuracy, _ = nirs_estimator.train_new_model_and_evaluate()
        nirs_estimator.confirm_new_data(True, True)
        print("[INFO] New model trained for app {}, accuracy = {}.".format(app_name, new_accuracy))


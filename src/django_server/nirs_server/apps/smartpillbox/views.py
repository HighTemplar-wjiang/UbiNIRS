import sys
import json
import numpy as np
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest
from .utils.globals import UbiNIRSAppMetadata
from dashboard.models import UbiNIRSApp, AppTestLog


# Return metadata to the client.
def metadata(request):
    return JsonResponse(UbiNIRSAppMetadata.app_metadata)


# Return classes.
def classes(request):
    if request.method == "GET":
        model_classes = list(UbiNIRSAppMetadata.nirs_estimator.get_classes())
        return JsonResponse({"classes": model_classes})


# Perform predictions and return results.
@csrf_exempt
def results(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST method is accepted for sending data.")

    # Get train / test mode.
    transaction_number = request.GET.get("transaction_number", None)
    mode = request.GET.get("mode", None)
    deviceid = request.GET.get("androidid", None)
    if (mode is None) or (deviceid is None) or (transaction_number is None):
        return HttpResponseBadRequest("Request must contain mode, androidid and transaction_number parameters.")

    # Update number of visits.
    app_row = UbiNIRSApp.objects.filter(pk=UbiNIRSAppMetadata.app_metadata["app_id"])
    app_row.update(app_visits=F("app_visits") + 1)

    # Get spectrum data.
    json_data = json.loads(request.body)
    try:
        wavelength = json_data["wavelength"]
        intensity_spectrum = json_data["intensity_spectrum"]
        reference_spectrum = json_data["reference_spectrum"]

        spectrum = np.array(intensity_spectrum) / np.array(reference_spectrum)
    except KeyError as ke:
        return HttpResponseBadRequest("Invalid JSON format.")

    # For testing / using the model.
    if mode == "test":

        # Get result.
        estimator_results = UbiNIRSAppMetadata.nirs_estimator.predict(spectrum)
        result_label = estimator_results["predicts"]["classification"]["class"]

        # Save train data.
        UbiNIRSAppMetadata.nirs_estimator.add_posted_data(
            wavelength, intensity_spectrum, reference_spectrum, result_label, "test", deviceid, transaction_number)

        # Add extra process to display result if needed.
        result_class = result_label

        return render(request, "results.html",
                      {"class": result_class,
                       "probability": estimator_results["predicts"]["classification"]["probability"],
                       "label": result_label,
                       })
    elif mode == "train":
        # Get training label.
        try:
            label = json_data["label"]

            # Add data to the model.
            UbiNIRSAppMetadata.nirs_estimator.add_posted_data(
                wavelength, intensity_spectrum, reference_spectrum, label, "train", deviceid, transaction_number)

            # Re-train the model whenever possible.
            new_accuracy, current_accuracy = UbiNIRSAppMetadata.nirs_estimator.train_new_model_and_evaluate()

            # Return new accuracy.
            return render(request, "evaluations.html",
                          {"new_accuracy": new_accuracy,
                           "current_accuracy": current_accuracy,
                           })

        except KeyError as ke:
            return HttpResponseBadRequest("Invalid JSON format.")

    else:
        # Wrong parameter.
        return HttpResponseBadRequest("Unknown parameter mode={}.".format(mode))


# Give instructions.
def instructions(request):
    status = request.GET.get("status", "init")
    mode = request.GET.get("mode", "test")

    if mode == "test":
        # Give initial instructions.
        if status == "init":
            response = render(request, "instructions.html",
                              {"can_scan": "true",
                               "title": "Identifying Your Object",
                               "instructions":
                                   '''
                                   <h2>Step 1</h2>
                                   <p>Put the object on the scanning window. Attach the flat surface with the window if possible. </p>
                                   <h2>Step 2</h2>
                                   <p>Push the "SCAN" button.</p>
                                   ''', })
            response["NIRS-Can-Scan"] = "true"
            response["New-Transaction"] = "true"
            return response
        else:
            pass
    elif mode == "train":
        if status == "init":
            response = render(request, "instructions.html",
                              {"can_scan": "true",
                               "title": "Training Your App",
                               "instructions":
                                   '''
                                   <h2>Step 1</h2>
                                   <p>Select the label for your training data.</p>
                                   <h2>Step 2</h2>
                                   <p>Put the object that matches your label on the scanning window. Attach the flat surface with the window if possible. </p>
                                   <h2>Step 3</h2>
                                   <p>Push the "SCAN" button.</p>
                                   ''', })
            response["NIRS-Can-Scan"] = "true"
            return response
    else:
        return HttpResponseBadRequest("Invalid parameter mode={}.".format(mode))


# Handle feedback.
def feedback(request):

    mode = request.GET.get("mode", None)
    answer = request.GET.get("answer", None)
    label = request.GET.get("label", None)
    transaction_number = request.GET.get("transaction_number", None)
    device_id = request.GET.get("androidid", None)

    # No such parameter.
    if (answer is None) or (mode is None) or (transaction_number is None) or (device_id is None):
        return HttpResponseBadRequest("Request URL must include answer, label, mode, transaction_number and device_id.")

    if mode == "train":
        # Confirm or delete the last data.
        if answer == "yes":
            UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(True, True)
            return render(request, "confirm.html",
                          {"confirm_message": "Your data and model have been updated."})

        elif answer == "no":
            UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(False, True)
            return render(request, "confirm.html",
                          {"confirm_message": "Your data and model remain unchanged."})

        else:
            return HttpResponseBadRequest("Invalid parameter answer={}.".format(answer))

    elif mode == "test":

        # Note: all test data are saved no matter confirmed or not.
        new_log = AppTestLog(
            test_transaction_number=transaction_number,
            app_id=UbiNIRSAppMetadata.app_metadata["app_id"],
            test_device_id=device_id,
            test_result=label,
        )

        if answer == "yes":
            save_filename = UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(True, False)
            new_log.test_feedback = True

        elif answer == "no":
            save_filename = UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(False, False)
            new_log.test_feedback = False

        else:
            return HttpResponseBadRequest("Invalid parameter answer={}.".format(answer))

        new_log.test_filename = save_filename
        new_log.save()

        return render(request, "feedback.html")
    else:
        return HttpResponseBadRequest("Invalid parameter mode={}.".format(mode))


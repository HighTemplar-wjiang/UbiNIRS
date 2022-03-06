import os
import json
import numpy as np
from datetime import datetime
from django.conf import settings
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest, HttpResponseServerError
from .utils.globals import UbiNIRSAppMetadata
from dashboard.models import UbiNIRSApp, AppTestLog
from .sequences import participant_sequence_generators, participant_completion_flags, participant_current_items
from .models import Wrap, GlutenTestLog


# Return metadata to the client.
def metadata(request):
    return JsonResponse(UbiNIRSAppMetadata.app_metadata)


# Return classes.
def classes(request):
    if request.method == "GET":
        model_classes = UbiNIRSAppMetadata.nirs_estimator.get_classes()
        return JsonResponse({"classes": model_classes})


# Give instructions.
def instructions(request):
    status = request.GET.get("status", "init")
    mode = request.GET.get("mode", "test")
    transaction_number = request.GET.get("transaction_number", None)
    participant_id = request.GET.get("participant", None)
    session = request.GET.get("session", None)
    current_time = datetime.utcnow()

    if (transaction_number is None) or (session is None):
        return HttpResponseBadRequest("Required parameter: transaction_number")

    if mode == "test":
        # Give initial instructions.
        if status == "init":

            # New database row.
            try:
                if GlutenTestLog.objects.filter(transaction_num=transaction_number).exists():
                    # Item exists. Continue session.
                    pass
                else:
                    # Create a new instance.
                    # Get next sample in the sequence.
                    try:
                        if participant_completion_flags[participant_id]:
                            next_item = next(participant_sequence_generators[participant_id][session])
                            participant_current_items[participant_id] = next_item
                            participant_completion_flags[participant_id] = False
                        else:
                            next_item = participant_current_items[participant_id]
                        print("Next condition: {}".format(next_item))
                    except StopIteration as si:
                        print("The end for participant {}.".format(participant_id))
                        return HttpResponse(
                            "<h2>That's the end of current session, thank you for your participation!</h2>")

                    new_log = GlutenTestLog(transaction_num=transaction_number,
                                            participant_id=participant_id,
                                            sample_id=next_item["Sample id"],
                                            inspection_result=None,
                                            scanned_result=None,
                                            visualization_method=next_item["Visualization method"],
                                            probability=None,
                                            trust_flag=None,
                                            session=session,
                                            label_language=next_item["Label language"],
                                            started_time=current_time)
                    new_log.save()

                # Generate normal response.
                response = render(request, os.path.join(UbiNIRSAppMetadata.template_root, "instructions.html"),
                                  {"can_scan": "false",
                                   "title": "Step 1 - Inspection",
                                   "sample_id": next_item["Sample id"],
                                   "instructions":
                                       """
                                       <h3>1. Inspect the wrap and its package.</h3>
                                       <br />
                                       <h3>2. Do you think it is gluten-free?</h3>
                                       <big><big><h1><a href="inspection/?answer=yes">&emsp;Yes&emsp;</a>&emsp;
                                       <a href="inspection/?answer=no">&emsp;No&emsp;</a></h1></big></big>
                                       """})
                response["NIRS-Can-Scan"] = "false"
                response["New-Transaction"] = "false"
                return response

            except Exception as e:
                print(e)
                return HttpResponseServerError("Server has an exception.")
        else:
            # Not implemented yet.
            pass
    elif mode == "train":
        if status == "init":
            response = render(request, os.path.join(UbiNIRSAppMetadata.template_root, "instructions.html"),
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


# Deal with inspection results.
def inspection(request):
    inspection_result = request.GET.get("answer", None)
    transaction_number = request.GET.get("transaction_number", None)
    participant_id = request.GET.get("participant", None)
    current_time = datetime.utcnow()

    # Sanity check.
    if (inspection_result is None) or (transaction_number is None) or (participant_id is None):
        return HttpResponseBadRequest("Insufficient parameters.")

    # Update record.
    try:
        db_row = GlutenTestLog.objects.get(transaction_num=transaction_number)

        # Data sanity check.
        if db_row.participant_id != participant_id:
            return HttpResponseBadRequest("Participant unmatched!")

        # Modify log.
        db_row.inspection_result = True if inspection_result.lower() == "yes" else False
        db_row.inspected_time = current_time
        db_row.save()

        # Construct response.
        response = render(request, os.path.join(UbiNIRSAppMetadata.template_root, "instructions.html"),
                          {"can_scan": "true",
                           "title": "Step 2 - Scan",
                           "sample_id": participant_current_items[participant_id]["Sample id"],
                           "instructions":
                               """
                               <br />
                               <h4>1. Find any transparent part in the wrap.</h4>
                               <br />
                               <h4>2. Put the wrap on the NIRS scanner, align the transparent part with the scanning window.</h4>
                               <br />
                               <h4>3. Push the "SCAN" button.</h4>
                               """})
        response["NIRS-Can-Scan"] = "true"
        response["New-Transaction"] = "false"
        return response

    except Exception as e:
        # Here catch all exception to prevent from server down.
        print(e)
        return HttpResponseServerError("Server has an exception.")


# Perform predictions and return results.
@csrf_exempt
def results(request):

    current_time = datetime.utcnow()

    if request.method != "POST":
        return HttpResponseBadRequest("Only POST method is accepted for sending data.")

    # Get train / test mode.
    transaction_number = request.GET.get("transaction_number", None)
    mode = request.GET.get("mode", None)
    deviceid = request.GET.get("androidid", None)
    participant_id = request.GET.get("participant", None)
    if (mode is None) or (deviceid is None) or (transaction_number is None) or (participant_id is None):
        return HttpResponseBadRequest(
            "Request must contain mode, androidid, transaction_number and participant_id parameters.")

    # Update number of visits.
    app_row = UbiNIRSApp.objects.filter(pk=UbiNIRSAppMetadata.app_metadata["app_id"])
    app_row.update(app_visits=F("app_visits") + 1)

    # Get spectrum data.
    json_data = json.loads(request.body)
    try:
        wavelength = json_data["wavelength"]
        intensity_spectrum = json_data["intensity_spectrum"]
        reference_spectrum = json_data["reference_spectrum"]

        spectrum = UbiNIRSAppMetadata.nirs_estimator._transform(
            intensity_spectrum=intensity_spectrum, reference_spectrum=reference_spectrum)
        # spectrum = np.array(intensity_spectrum) / np.array(reference_spectrum)
    except KeyError as ke:
        return HttpResponseBadRequest("Invalid JSON format.")

    # For testing / using the model.
    if mode == "test":

        # Get result.
        estimator_results = UbiNIRSAppMetadata.nirs_estimator.predict(spectrum)
        result_label = estimator_results["predicts"]["classification"]["class"]
        result_probability = estimator_results["predicts"]["classification"]["probability"]

        # Save test data.
        UbiNIRSAppMetadata.nirs_estimator.add_posted_data(
            wavelength, intensity_spectrum, reference_spectrum, result_label, "test", deviceid, transaction_number)

        # Generate probability visualization.
        # Get visualization method.
        visualization_method = GlutenTestLog.objects.get(transaction_num=transaction_number).visualization_method
        fig_ax = UbiNIRSAppMetadata.nirs_estimator.visualize_probability(result_probability,
                                                                         method=visualization_method)
        folder_name = participant_id
        result_file_name = ""
        if fig_ax is not None:
            # Save fig.
            fig, ax = fig_ax
            folder_path = os.path.join(settings.STATIC_OUTPUT, folder_name)
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            result_file_name = "{}_result.png".format(transaction_number)
            fig.savefig(os.path.join(folder_path, result_file_name), bbox_inches="tight")

        # Add extra process to display result if needed.
        result_display_class = result_label.replace("-", " ")

        # Update database record.
        try:
            db_row = GlutenTestLog.objects.get(transaction_num=transaction_number)

            # Sanity check.
            if db_row.participant_id != participant_id:
                raise Exception("Participant unmatched.")

            # Execute updating.
            db_row.scanned_result = result_label
            db_row.probability = result_probability
            db_row.scanned_time = current_time
            db_row.save()

            # Probability display.
            probability_display = ""
            if visualization_method.lower() == "baseline":
                probability_display = "Chance of being correct: <br /><br />{:.0f}%".format(result_probability * 100)
            else:
                probability_display = "Chance of being correct: "

            return render(request, os.path.join(UbiNIRSAppMetadata.template_root, "results.html"),
                          {"title": "Step 3 - Scanning result",
                           "class": result_display_class,
                           "probability": probability_display,
                           "result_img": os.path.join(folder_name, result_file_name),
                           "label": result_label,
                           })
        except Exception as e:
            print(e)
            return HttpResponseServerError("Server has an exception.")

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
            return render(request, os.path.join(UbiNIRSAppMetadata.template_root, "evaluations.html"),
                          {"title": "Training result",
                           "label": label,
                           "new_accuracy": new_accuracy,
                           "current_accuracy": current_accuracy,
                           })

        except KeyError as ke:
            return HttpResponseBadRequest("Invalid JSON format.")

    else:
        # Wrong parameter.
        return HttpResponseBadRequest("Unknown parameter mode={}.".format(mode))


# Handle feedback.
def feedback(request):
    """Received a feedback from the client."""
    mode = request.GET.get("mode", None)
    answer = request.GET.get("answer", None)
    label = request.GET.get("label", None)
    transaction_number = request.GET.get("transaction_number", None)
    device_id = request.GET.get("androidid", None)
    participant_id = request.GET.get("participant", None)
    current_time = datetime.utcnow()

    # No such parameter.
    if (answer is None) or (mode is None) or (transaction_number is None) or (
            device_id is None) or (label is None) or (participant_id is None):
        return HttpResponseBadRequest(
            "Request URL must include answer, label, mode, transaction_number, device_id and participant_id.")

    if mode == "train":
        # Confirm or delete the last data.
        if answer == "yes":
            UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(True, True)
            return render(request, os.path.join(UbiNIRSAppMetadata.template_root, "confirm.html"),
                          {"confirm_message": "Your data and model have been updated."})

        elif answer == "no":
            UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(False, True)
            return render(request, os.path.join(UbiNIRSAppMetadata.template_root, "confirm.html"),
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

        trust_flag = None
        if answer == "yes":
            trust_flag = True
        elif answer == "no":
            trust_flag = False
        else:
            return HttpResponseBadRequest("Invalid parameter answer={}.".format(answer))

        # Update.
        save_filename = UbiNIRSAppMetadata.nirs_estimator.confirm_new_data(trust_flag, False)
        new_log.test_feedback = trust_flag
        new_log.test_filename = save_filename
        new_log.save()

        # Update study log.
        try:
            db_row = GlutenTestLog.objects.get(transaction_num=transaction_number)

            # Sanity check.
            if db_row.participant_id != participant_id:
                raise(Exception("Participant unmatched!"))

            # Execute update.
            db_row.trust_flag = trust_flag
            db_row.feedback_time = current_time
            db_row.save()

            # Set current sample as complete.
            participant_completion_flags[participant_id] = True

            return render(request, os.path.join(UbiNIRSAppMetadata.template_root, "feedback.html"))
        except Exception as e:
            print(e)
            return HttpResponseServerError("Server has an exception.")
    else:
        return HttpResponseBadRequest("Invalid parameter mode={}.".format(mode))


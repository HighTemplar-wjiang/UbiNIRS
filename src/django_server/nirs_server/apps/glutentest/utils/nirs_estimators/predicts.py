# Generic estimators for either classification or regression.
import os
import re
import time
import joblib
import numpy as np
import scipy.signal
import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from sklearn.exceptions import NotFittedError
from enum import Enum


class ModelType(Enum):
    """Enumerator for types of pre-trained nirs_models."""
    classification = 1
    regression = 2


class NIRSEstimator:
    """Master class for either classifier or regressor.
       Sanity check should be performed outside the class."""

    # Regular expression for matching files.
    re_filename = re.compile("^(?P<label>.*?)_(?P<identifier>.*?)\.csv")

    # Colors for all methods.
    color_map = mpl.cm.get_cmap("bone")
    color_norm = Normalize(vmin=-0.2, vmax=1.3, clip=True)
    correct_color = color_map(color_norm(0))
    wrong_color = color_map(color_norm(1))

    def __init__(self, pretrained_model_path: str, untrained_model_path: str, model_type: ModelType):
        """Loading the pre-trained model."""
        self.model_type = model_type
        self.model_dir = os.path.join("/".join(pretrained_model_path.split("/")[:-1]), "../")
        self.model_path = pretrained_model_path
        self.untrained_model_path = untrained_model_path

        with open(pretrained_model_path, "rb") as f:
            saved_model = joblib.load(f)
        self.model = saved_model["model"]

        # Temporary data for training.
        self.candidate_model = None
        self.cached_data_reference = None
        self.cached_file_path = ""

        if self.model_type == ModelType.classification:
            self.classes = saved_model["classes"]

        # Load pre-sampled data for online-training if exists.
        raw_data, all_labels = self._load_data(os.path.join(self.model_dir, "./data/"),
                                               including_presampled=True, including_posted=True)

        # Perform pre-processing.
        transformed_data = [self._transform(spectrum[:, 1], spectrum[:, 2]) for spectrum in raw_data]

        # Set data.
        all_data = [self._preprocess(spectrum) for spectrum in transformed_data]
        all_labels = all_labels

        # Sort data w.r.t. labels.
        self.data_bins = {}
        for idx, label in enumerate(all_labels):
            if label in self.data_bins.keys():
                self.data_bins[label].append(all_data[idx])
            else:
                self.data_bins[label] = [all_data[idx]]

        pass

    def _load_data(self, datapath, including_presampled=True, including_posted=False):
        """Load pre-sampled data for training."""

        loaded_data = []
        loaded_labels = []

        # Get the list of all files.
        all_filenames = []
        if including_presampled:
            all_presampled_filenames = os.listdir(os.path.join(datapath, "reference"))
            all_filenames += list(zip(all_presampled_filenames, ["reference"] * len(all_presampled_filenames)))
        if including_posted:
            all_posted_filenames = os.listdir(os.path.join(datapath, "train"))
            all_filenames += list(zip(all_posted_filenames, ["train"] * len(all_posted_filenames)))

        for filename, prefix in all_filenames:
            # print(filename)
            re_result = self.re_filename.match(filename)
            if re_result:
                label = re_result.group("label")
                cur_data = np.loadtxt(os.path.join(os.path.join(datapath, prefix), filename), delimiter=",")

                loaded_data.append(cur_data)
                loaded_labels.append(label)

        return np.array(loaded_data), np.array(loaded_labels)

    def _quality_check(self, spectrum):
        """Check if the spectrum is qualified for classification."""

        # Apply Savitzky-Golay filter.
        spectrum_smooth = scipy.signal.savgol_filter(spectrum, window_length=21, polyorder=3)

        # Computing smoothness index.
        smoothness_index = 1 / np.mean(np.sum(np.abs((spectrum_smooth - spectrum) / spectrum)))

        return smoothness_index

    def _transform(self, intensity_spectrum, reference_spectrum):
        """Transform spectrum to reflectance, absorbance, or another."""
        # return np.array(intensity_spectrum) / np.array(reference_spectrum)
        return -np.log10(np.array(intensity_spectrum) / np.array(reference_spectrum))

    def _preprocess(self, spectrum):
        """Perform pre-processing step."""
        # Apply filtering.
        spectrum_processed = scipy.signal.savgol_filter(spectrum, window_length=21, polyorder=3)

        # Take gradient.
        spectrum_processed = np.gradient(spectrum_processed)

        # Slice.
        spectrum_processed = spectrum_processed[25:200]

        return spectrum_processed

    def _balanced_sample(self, shuffle=False):
        """Sample data with balanced labels."""
        # Find min count.
        min_count = -1
        min_count_class = ""
        for key, values in self.data_bins.items():
            cur_count = len(values)
            if min_count == -1:
                min_count = cur_count
                min_count_class = key
            elif cur_count < min_count:
                min_count = cur_count
                min_count_class = key

        # Re-sampling.
        sampled_data = []
        sampled_labels = []
        for key, values in self.data_bins.items():
            if shuffle:
                np.random.shuffle(values)
            sampled_data += values[:min_count]
            sampled_labels += [key] * min_count

        return sampled_data, sampled_labels, min_count_class

    def _evaluate_model(self, model, data, labels):
        """Evaluate nirs_models."""
        predicted_labels = model.predict(data)
        accuracy = np.mean(predicted_labels == labels)

        return accuracy

    def get_classes(self):
        """Return the classes for this model."""
        return self.classes

    def add_posted_data(self, wavelength, intensity_spectrum, reference_spectrum, label,
                        folder, device_id, transaction_number):
        """Append train data to the instance and save the data to a csv file."""
        # Transform and filter new data.
        new_data = self._preprocess(self._transform(intensity_spectrum, reference_spectrum))
        new_label = label

        # Add train data to instance.
        # self.all_data = np.concatenate((self.all_data, [wavelength, intensity_spectrum, reference_spectrum]), axis=0)
        # self.all_labels = np.concatenate((self.all_labels, [label]), axis=0)
        if label in self.data_bins.keys():
            # Shuffle.
            np.random.shuffle(self.data_bins[label])
            # Add data.
            self.data_bins[label] = [new_data] + self.data_bins[label]
            self.cached_data_reference = self.data_bins[label]
        else:
            self.data_bins[label] = [new_data]

        # Save train raw data to file.
        microsec = int(time.time() * 1e6)
        filename = "{}_{}_{}_{}".format(label, microsec, device_id, transaction_number)
        self.cached_file_path = os.path.join(self.model_dir, "./data/{}/{}.csv".format(folder, filename))
        with open(self.cached_file_path, "w") as f:
            np.savetxt(f,
                       np.transpose(np.array([wavelength, intensity_spectrum, reference_spectrum])),
                       fmt="%.2f", delimiter=",")

        return filename

    def train_new_model_and_evaluate(self):
        """Train a new model and evaluate."""
        with open(self.untrained_model_path, "rb") as f:
            new_model = joblib.load(f)["model"]

        # Get train data.
        train_data, train_labels, min_count_class = self._balanced_sample()

        # Check if each label has at least one data point.
        if len(train_labels) == 0:
            return "(Spectrum for {} required.)".format(min_count_class), ""

        try:
            current_accuracy = self._evaluate_model(self.model, train_data, train_labels)
        except NotFittedError as nfe:
            current_accuracy = "(Not trained)"

        # Training new model and save.
        new_model.fit(train_data, train_labels)
        self.candidate_model = new_model

        # Evaluating new nirs_models.
        new_accuracy = self._evaluate_model(new_model, train_data, train_labels)

        return new_accuracy, current_accuracy

    def confirm_new_data(self, is_confirmed, is_training):
        """Replace model, save data if confirmed."""

        saved_filename = self.cached_file_path.split("/")[-1]
        if is_training:
            if is_confirmed:
                # Activate new model when training.
                if self.candidate_model:
                    self.model = self.candidate_model

                    # Save the new model.
                    new_model = {
                        "model": self.model,
                        "classes": self.classes,
                    }
                    joblib.dump(new_model, self.model_path)

            else:
                # When training, delete wrong training data.
                # Remove cached data and file.
                if isinstance(self.cached_data_reference, list):
                    self.cached_data_reference.pop(0)
                if os.path.isfile(self.cached_file_path):
                    os.remove(self.cached_file_path)

        # Clear references.
        self.cached_data_reference = None
        self.cached_file_path = ""
        self.candidate_model = None

        return saved_filename

    def online_training(self, training_data):
        """
        Online training with new dataset.
        Re-train the model when necessary.
        """
        # TODO: Online training for specific nirs_models (RF, SGD).
        pass

    @staticmethod
    def _framing_probability(positive_probability):
        """
        Framing possibility.
        ref: https://serialmentor.com/dataviz/visualizing-uncertainty.html
        """
        fig, ax = plt.subplots(figsize=(4, 4), dpi=200)

        # Set limits.
        ax.set_xlim([0, 10])
        ax.set_ylim([0, 10])

        # Set and hide ticks.
        ax.set_xticks(range(0, 10))
        ax.set_yticks(range(0, 10))
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.xaxis.set_ticks_position("none")
        ax.yaxis.set_ticks_position("none")
        ax.set_frame_on(False)

        # Grid.
        ax.grid(True, which="major", axis="both", color="w", linewidth=2)

        # Generating image data.
        num_positive = int(np.floor(100 * positive_probability))
        num_negative = int(100 - num_positive)
        prob_img = [0] * num_positive + [1] * num_negative
        np.random.shuffle(prob_img)
        prob_img = np.array(prob_img).reshape(10, 10)
        values = [0, 1]

        # Show.
        extent = (0, 10, 0, 10)
        im = ax.imshow(prob_img, extent=extent, cmap="bone", norm=NIRSEstimator.color_norm, interpolation="none")

        # Add legend.
        labels = ["Correct", "Wrong"]
        # labels = ["Wrong", "Correct"]
        colors = [NIRSEstimator.color_map(NIRSEstimator.color_norm(value)) for value in values]
        patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(values))]
        ax.legend(ncol=2, handles=patches, bbox_to_anchor=(1, -0.12), loc="lower right", borderaxespad=0.,
                  fontsize="large", fancybox=False, edgecolor="black")

        return fig, ax

    # Scaling probability.
    @staticmethod
    def _scaling_probability(probability):
        # Stacked Bar chart.
        fig, ax = plt.subplots(figsize=(5, 0.5), dpi=400)
        bars = []

        # Set limits.
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])

        # Set ticks.
        # x_tick_numbers = np.arange(0, 1.0 + 1e-3, 0.2)
        # ax.set_xticks(x_tick_numbers)
        # ax.set_xticklabels(["{:2.0f}%".format(prob * 100) for prob in x_tick_numbers])
        ax.set_xticks([])
        ax.set_yticks([])

        # Correct bar.
        ax.barh(0, width=probability, height=1.0, left=0, align="edge", color=NIRSEstimator.correct_color,
                label="Correct")
        # ax.text(probability / 2, 0.5, "Correct", color="white", ha="center", va="center", fontsize="xx-large")

        # Wrong bar.
        ax.barh(0, width=1.0 - probability, height=1.0, left=probability, align="edge", color=NIRSEstimator.wrong_color,
                label="Wrong")

        # Legend.
        ax.legend(ncol=2, bbox_to_anchor=(1, -1.5), loc="lower right", borderaxespad=0., fontsize="large",
                  fancybox=False, edgecolor="black")

        return fig, ax

    def visualize_probability(self, probability, method):
        """Visualize the probability."""
        method = method.lower()

        if method == "frame":
            return self._framing_probability(probability)

        elif method == "baseline":
            return None

        elif method == "scale":
            return self._scaling_probability(probability)

        else:
            print("[ERROR] Available methods: {}.".format("framing, color, scale"))
            return None

    def predict(self, spectrum):
        """Get prediction results from the model."""

        # Quality check.
        quality_score = self._quality_check(spectrum)

        # Pre-processing.
        spectrum_processed = self._preprocess(spectrum)

        # Shaping.
        spectrum_processed = np.expand_dims(
            spectrum_processed, 0) if len(spectrum_processed.shape) == 1 else spectrum_processed

        # Running the model.
        classification_results = {}
        regression_results = 0
        if self.model_type == ModelType.classification:
            predicts = self.model.predict(spectrum_processed)[0]
            predicts_probabilities = self.model.predict_proba(spectrum_processed)
            classification_results = {"class": predicts, "probability": predicts_probabilities.max()}
        else:
            regression_results = self.model.predict(spectrum_processed)

        # Structuring the results.
        results = {
            "quality_score": quality_score,
            "predicts": {
                "classification": classification_results,
                "regression": regression_results,
            }
        }

        return results


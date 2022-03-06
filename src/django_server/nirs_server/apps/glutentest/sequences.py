# Participant sequences.
import os
import numpy as np
import pandas as pd
from .utils.globals import UbiNIRSAppMetadata


def participant_condition_generator(current_participant, df_sequences, session_number):
    """Generator to generate a sequence for a specific participant."""
    current_participant_sequence = df_sequences[
        (df_sequences["Participant"] == current_participant) & (df_sequences["Session number"] == session_number)]

    for condition in current_participant_sequence.iterrows():
        yield condition[1].to_dict()


def load_participant_sequences(filepath):
    """Read participant sheet."""
    with open(filepath, "r") as f:
        df = pd.read_csv(f)

    return df


# Load participant sequences.
df_all_sequences = load_participant_sequences(os.path.join(UbiNIRSAppMetadata.app_root, "pregen/sequences.csv"))

# Create participant sequence generators and status.
participant_current_items = {}
participant_completion_flags = {}
participant_sequence_generators = {}
for participant in df_all_sequences["Participant"].unique():
    current_participant_generators = {}
    for session_number in df_all_sequences["Session number"].unique():
        current_participant_generators[str(session_number)] = participant_condition_generator(
            participant, df_all_sequences, session_number)
    participant_current_items[participant] = None
    participant_completion_flags[participant] = True
    participant_sequence_generators[participant] = current_participant_generators

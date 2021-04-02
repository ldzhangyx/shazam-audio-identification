import yaml
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
from pydub import AudioSegment
from utils import *
import os
import database_op

from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (binary_erosion,
                                      generate_binary_structure,
                                      iterate_structure)

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def generate_fingerprint(file_path):
    # 0. pre-precessing
    file_name = os.path.split(file_path)[-1]
    channels = read_op(file_path)

    # 1. hash
    file_hash = string_hash(file_path)

    # 2. calculate fingerprint
    fingerprints = fingerprint_op(channels, fs = config['DATABASE_FS'])

    # 3. insert log into database
    database_op.add_song(file_name, file_hash)
    for fingerprint in fingerprints:
        database_op.add_fingerprint(file_name,
                                    fingerprint=fingerprint[0],
                                    offset=fingerprint[1])


def recognize(file_path):
    channels = read_op(file_path)
    fingerprints = fingerprint_op(channels, fs=config['QUERY_FS'])

    # 1. match hashes
    all_matches = list()
    for fingerprint in fingerprints:
        matches = database_op.find_match_fingerprints(
            fingerprint=[fingerprint[0]],
            offset=fingerprint[1])
        all_matches.extend(matches)

    # 2. rank
    top_list = rank_results(all_matches)

    return top_list


def rank_results(all_matches, topK=3):
    counter = dict()
    for match in all_matches:
        if match not in counter.keys():
            counter[match] = 1
        else:
            counter[match] += 1
    counter_k = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    counter_k = counter_k[:topK]
    # print(counter_k)
    name_k = [i[0][0] for i in counter_k]

    return name_k


def read_op(file_path):
    audio_file = AudioSegment.from_file(file_path)
    data = np.fromstring(audio_file.raw_data, np.int16)
    channels = []
    for chn in range(audio_file.channels):
        channels.append(data[chn::audio_file.channels])
    return channels


def fingerprint_op(channels, fs):
    fingerprints = set()
    channel_amount = len(channels)
    for index, channel in enumerate(channels, start=1):
        # hashes = fingerprint(channel, Fs=fs)
        arr2D = mlab.specgram(
            channel,
            NFFT=config['DEFAULT_WINDOW_SIZE'],
            Fs=fs,
            window=mlab.window_hanning,
            noverlap=int(config['DEFAULT_WINDOW_SIZE']
                         * config['DEFAULT_OVERLAP_RATIO']))[0]

        arr2D = 10 * np.log10(arr2D, out=np.zeros_like(arr2D), where=(arr2D != 0))
        local_maxima = get_2D_peaks(arr2D, plot=False)
        fingerprint_hash = audio_hash(local_maxima, config['DEFAULT_FAN_VALUE'])

        fingerprints |= set(fingerprint_hash)

        return fingerprints


def get_2D_peaks(arr2D, plot=True, amp_min=config['DEFAULT_AMP_MIN']):
    """
    Extract maximum peaks from the spectogram matrix (arr2D).

    :param arr2D: matrix representing the spectogram.
    :param plot: for plotting the results.
    :param amp_min: minimum amplitude in spectrogram in order to be considered a peak.
    :return: a list composed by a list of frequencies and times.
    """
    struct = generate_binary_structure(2, config['CONNECTIVITY_MASK'])

    neighborhood = iterate_structure(struct, config['PEAK_NEIGHBORHOOD_SIZE'])

    # find local maxima using our filter mask
    local_max = maximum_filter(arr2D, footprint=neighborhood) == arr2D

    # Applying erosion, the dejavu documentation does not talk about this step.
    background = (arr2D == 0)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    # Boolean mask of arr2D with True at peaks (applying XOR on both matrices).
    detected_peaks = local_max != eroded_background

    # extract peaks
    amps = arr2D[detected_peaks]
    freqs, times = np.where(detected_peaks)

    # filter peaks
    amps = amps.flatten()

    # get indices for frequency and time
    filter_idxs = np.where(amps > amp_min)

    freqs_filter = freqs[filter_idxs]
    times_filter = times[filter_idxs]

    if plot:
        # scatter of the peaks
        fig, ax = plt.subplots()
        ax.imshow(arr2D, aspect=0.1)
        ax.scatter(times_filter, freqs_filter, s=10, c='black')
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return list(zip(freqs_filter, times_filter))

# generate_fingerprint("database_recordings/classical.00000.wav")

from hashlib import sha1
import yaml
from operator import itemgetter
import hashlib
from functools import reduce

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

def string_hash(file_path: str, block_size: int = 2**20):
    """ Small function to generate a hash to uniquely generate
    a file. Inspired by MD5 version here:
    http://stackoverflow.com/a/1131255/712997

    Works with large files.

    :param file_path: path to file.
    :param block_size: read block size.
    :return: a hash in an hexagesimal string form.
    """
    s = sha1()
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(block_size)
            if not buf:
                break
            s.update(buf)
    return s.hexdigest().upper()


def audio_hash(peaks, fan_value):
    """
    Hash list structure:
       sha1_hash[0:FINGERPRINT_REDUCTION]    time_offset
        [(e05b341a9b77a51fd26, 32), ... ]

    :param peaks: list of peak frequencies and times.
    :param fan_value: degree to which a fingerprint can be paired with its neighbors.
    :return: a list of hashes with their corresponding offsets.
    """
    # frequencies are in the first position of the tuples
    idx_freq = 0
    # times are in the second position of the tuples
    idx_time = 1

    if config['PEAK_SORT']:
        peaks.sort(key=itemgetter(1))

    hashes = []
    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if (i + j) < len(peaks):

                freq1 = peaks[i][idx_freq]
                freq2 = peaks[i + j][idx_freq]
                t1 = peaks[i][idx_time]
                t2 = peaks[i + j][idx_time]
                t_delta = t2 - t1

                if config['MIN_HASH_TIME_DELTA'] <= t_delta <= config['MAX_HASH_TIME_DELTA']:
                    h = hashlib.sha1(f"{str(freq1)}|{str(freq2)}|{str(t_delta)}".encode('utf-8'))

                    hashes.append((h.hexdigest()[0:config['FINGERPRINT_REDUCTION']], t1))

    return hashes

def evaluate(queries, results):
    rank_results = list()
    precision_results = 0
    for i in range(len(queries)):
        query_id = queries.split('.')[1][:5]
        results_id = [result.split('.')[1] for result in results]
        if query_id in results_id:
            rank = results_id.index(query_id) + 1
            precision_results += 1
        else:
            rank = 4
    rank_reciprocal = [1/i for i in rank_results]
    rank = reduce(lambda x, y: x + y, rank_reciprocal)
    precision = precision_results / (len(queries)+1)

    return rank, precision
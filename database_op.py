import sqlite3
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def create_database():
    """
    Database Structure:

    +-----------+------+
    |   Songs   |      |
    +-----------+------+
    | id        | int  |
    | song name | text |
    | filehash  | text |
    +-----------+------+
    +--------------+------+
    | Fingerprints |      |
    +--------------+------+
    | id           | int  |
    | song name    | int  |
    | fingerprint  | text |
    | offset       | int  |
    +--------------+------+
    """
    conn = sqlite3.connect(config['database_dir'])
    c = conn.cursor()
    c.execute('''
    CREATE TABLE song(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_name TEXT,
    filehash TEXT
    );
    ''')
    conn.commit()

    c.execute('''
    CREATE TABLE fingerprints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_name TEXT,
    fingerprint TEXT,
    offset INTEGER
    );
    ''')
    conn.commit()
    conn.close()


# create_database()

def reset_database():
    conn = sqlite3.connect(config['database_dir'])
    c = conn.cursor()
    c.execute('''
    DELETE from song;
    ''')
    c.execute('''
    DELETE from fingerprints;
    ''')
    conn.commit()
    conn.close()


def add_song(song_name, filehash):
    conn = sqlite3.connect(config['database_dir'])
    c = conn.cursor()
    c.execute('''
    INSERT INTO song (song_name, filehash) VALUES (?, ?);
    ''', (song_name, filehash))
    conn.commit()
    conn.close()

# add_song('123.wav', '13212321')


def add_fingerprint(song_name, fingerprint, offset):
    conn = sqlite3.connect(config['database_dir'])
    c = conn.cursor()
    c.execute('''
    INSERT INTO fingerprints (song_name, fingerprint, offset) VALUES (?, ?, ?);
    ''', (song_name, fingerprint, offset))
    conn.commit()
    conn.close()


def find_match_fingerprints(fingerprint, offset):
    conn = sqlite3.connect(config['database_dir'])
    c = conn.cursor()
    c.execute('''
    SELECT * FROM fingerprints WHERE fingerprint = (?);
    ''', fingerprint)
    records = c.fetchall()
    final_records = list()
    for i, record in enumerate(records):
        bias = offset - int.from_bytes(record[3], 'little')
        song_name = record[1]
        final_records.append((song_name, bias))
    conn.close()

    return final_records

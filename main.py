import yaml
import os
import database_op
import fingerprint
import utils

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

database_recordings_dir = config['database_recordings_dir']
query_recordings_dir = config['query_recordings_dir']

# generate database
if not os.path.exists(config['database_dir']):
    database_op.create_database()
else:
    if config['reset']:
        database_op.reset_database() # reset all data, optional

# generate fingerprint
# for i, file_name in enumerate(os.listdir(config['database_recordings_dir'])):
#     file_path = os.path.join(config['database_recordings_dir'], file_name)
#     fingerprint.generate_fingerprint(file_path)


# recognition
queries = os.listdir(config['query_recordings_dir'])
results = list()
for i, file_name in enumerate(queries):
    file_path = os.path.join(config['query_recordings_dir'], file_name)
    result = fingerprint.recognize(file_path)
    results.append(result)
    # write file
    with open(config['results_file'], 'w+') as f:
        result_format = f'{file_name}\t{result[0]}\t{result[1]}\t{result[2]}\n'
        print(result_format)
        f.write(result_format)


# evaluation
rank, precision = utils.evaluate(queries, results)
print(f"rank: {rank}; precision: {precision}.")
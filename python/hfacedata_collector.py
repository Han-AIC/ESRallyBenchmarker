import os 
import yaml 
import pandas as pd 
from data_acquisition import Scraper, DocumentController
from elastic_interface import ESBulkIndexer
import yaml 
import sys
import numpy as np
from datasets import load_dataset

path = str(sys.argv[1])
with open(f'{path}/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

initial_url = config['huggingface_settings']['starting_url']
# scraper=Scraper()
# dc=DocumentController() 

# document_objects = scraper.scrape_with_depth(initial_url, 
#                                              max_depth=config['scrape_settings']['max_depth'],
#                                              max_docs=config['scrape_settings']['max_docs'])
# scrape_filepath=config['storage_settings']['scrape_filepath']
# dc.save_dicts_to_csv(document_objects, f'{path}/{scrape_filepath}')


def save_dataset_as_csv(dataset_name, output_csv):
    # Load the dataset
    dataset = load_dataset(dataset_name)
    
    # Combine all splits into a single DataFrame
    combined_df = pd.DataFrame()
    for split in dataset.keys():
        split_df = pd.DataFrame(dataset[split])
        combined_df = pd.concat([combined_df, split_df], ignore_index=True)
    
    # Save the combined DataFrame as a CSV file
    combined_df.to_csv(output_csv, index=False)
    print(f"Dataset '{dataset_name}' saved as '{output_csv}'.")

# Example usage
scrape_filepath=config['storage_settings']['scrape_filepath']
save_dataset_as_csv(initial_url, f'{path}/{scrape_filepath}')



cloud_id=config['cloud_creds']['id']
username=config['cloud_creds']['username']
password=config['cloud_creds']['password']
credentials=(username, password)

conn=ESBulkIndexer(cloud_id=cloud_id, 
                  credentials=credentials)

def get_es_field_type(dtype):
    if np.issubdtype(dtype, np.integer):
        return 'integer'
    elif np.issubdtype(dtype, np.floating):
        return 'float'
    elif np.issubdtype(dtype, np.bool_):
        return 'boolean'
    elif np.issubdtype(dtype, np.datetime64):
        return 'date'
    else:
        return 'text'

df=pd.read_csv(f'{path}/{scrape_filepath}')
df=df.dropna()
df['id'] = range(len(df))

data_list=df.to_dict(orient='records')
index_name=config['huggingface_settings']['index_name']
properties = {
    col: {"type": get_es_field_type(dtype)} for col, dtype in df.dtypes.items()
}

index_config = {
    "settings": {
        "number_of_shards": config['es_settings']['number_of_shards'],
        "number_of_replicas": config['es_settings']['number_of_replicas']
    },
    "mappings": {
        "properties": properties
    }
}


conn.create_es_index(index_name=index_name, es_configuration=index_config)
conn.bulk_upload_documents(index_name=index_name, documents=data_list)


# Create a timestamped folder in the ./logs/ directory
# timestamp = str(sys.argv[2])
# log_dir = f'{path}/logs/{timestamp}'

# # Save configuration settings to a file
# config_log_path = os.path.join(log_dir, 'config.yaml')
# with open(config_log_path, 'w', encoding='utf-8') as f:
#     yaml.dump(config, f)
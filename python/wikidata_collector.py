import os 
import yaml 
import pandas as pd 
from data_acquisition import Scraper, DocumentController
from elastic_interface import ESBulkIndexer
import yaml 
import sys

path = str(sys.argv[1])
with open(f'{path}/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

initial_url = config['wikiscrape_settings']['starting_url']
scraper=Scraper()
dc=DocumentController() 

document_objects = scraper.scrape_with_depth(initial_url, 
                                             max_depth=config['wikiscrape_settings']['max_depth'],
                                             max_docs=config['wikiscrape_settings']['max_docs'])
scrape_filepath=config['storage_settings']['scrape_filepath']
dc.save_dicts_to_csv(document_objects, f'{path}/{scrape_filepath}')

cloud_id=config['cloud_creds']['id']
username=config['cloud_creds']['username']
password=config['cloud_creds']['password']
credentials=(username, password)

conn=ESBulkIndexer(cloud_id=cloud_id, 
                  credentials=credentials)

df=pd.read_csv(f'{path}/{scrape_filepath}')
df=df.dropna()
df['id'] = df['url']

data_list=df.to_dict(orient='records')
index_name=config['wikiscrape_settings']['index_name']
index_config={
                "settings": {
                "number_of_shards": config['es_settings']['number_of_shards'],
                "number_of_replicas": config['es_settings']['number_of_replicas']
                },
                "mappings": {
                "properties": {
                    col: {
                    "type": "text"
                    } for col in df.columns
                }
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
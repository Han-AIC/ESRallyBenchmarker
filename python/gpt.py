

SAMPLE_REPORT='''
### ESRally Benchmark Report Analysis for dvitel-geo Dataset

#### Summary

This report presents the performance and health metrics of an Elasticsearch cluster based on the ESRally benchmark using the dvitel-geo dataset. Here, key metrics such as indexing, merging, refresh, and flush times, garbage collection (GC) activity, memory usage, and throughput are evaluated. The implications for the cluster’s health and performance are discussed based on these metrics.

#### Indexing Performance

- **Cumulative Indexing Time of Primary Shards**: 
  - Total: 0.0097 min
  - Min: 0 min
  - Median: 0 min
  - Max: 0.00445 min

  The cluster's primary shards exhibited minimal cumulative indexing times, with the maximum time being very low at approximately 0.00445 minutes. This indicates efficient indexing operations for the relatively small dataset (880 rows).

- **Indexing Throttle Time**:
  - All values (Min, Median, Max) are 0 min.

  There was no throttling observed during indexing, implying that the cluster had sufficient resources to handle the load without backpressure.

#### Merging Operations

- **Cumulative Merge Time of Primary Shards**:
  - Total: 0.00455 min
  - Min: 0 min
  - Median: 0 min
  - Max: 0.00275 min

  Merge operations were minimal and completed quickly, with a maximum cumulative merge time of 0.00275 minutes across primary shards.

- **Cumulative Merge Count of Primary Shards**:
  - Total: 12 merges

#### Refresh Operations

- **Cumulative Refresh Time of Primary Shards**:
  - Total: 0.07948 min
  - Max: 0.03935 min

  The refresh operations, necessary for making the indexed documents searchable, were conducted efficiently with a total time of about 0.07948 minutes.

- **Cumulative Refresh Count of Primary Shards**:
  - Total: 2763 refresh operations

#### Flush Operations

- **Cumulative Flush Time of Primary Shards**:
  - Total: 0.12275 min
  - Max: 0.0617 min

  Flush operations, which help ensure transactional integrity, were efficient with a total time of approximately 0.12275 minutes.

- **Cumulative Flush Count of Primary Shards**:
  - Total: 431 flush operations

#### Garbage Collection

- **Young Gen GC Time and Count**: 0 s, 0 counts
- **Old Gen GC Time and Count**: 0 s, 0 counts

  The absence of any garbage collection activity suggests that the heap memory was sufficiently provisioned for the task, preventing any need for GC during the benchmark.

#### Memory Usage

- **Heap Memory Usage**:
  - For segments, doc values, norms, points, and stored fields: 0 MB

  No memory was specifically allocated for these components during the benchmark, indicating either efficient memory usage or the small size of the dataset allowing for such metrics to remain zero.

#### Storage and Segment Metrics

- **Store Size**: 0.00197 GB
- **Translog Size**: 0.00047 GB
- **Segment Count**: 49 segments

#### Ingest Pipeline

- **Ingest Pipeline Count, Time, Failed**: All values are 0.

  No ingest pipelines were configured or utilized during this benchmark.

#### Throughput and Latency

- **Throughput (bulk)**:
  - Min: 8474.53 docs/s
  - Mean: 8474.53 docs/s
  - Median: 8474.53 docs/s
  - Max: 8474.53 docs/s

  The throughput is consistent at 8474.53 documents per second, indicating stable performance.

- **Latency (bulk)**:
  - 50th percentile: 43.38 ms
  - 100th percentile: 53.65 ms

  The latency metrics show quick processing times, with the 100th percentile just above 50 ms.

- **Service Time (bulk)**:
  - 50th percentile: 43.38 ms
  - 100th percentile: 53.65 ms

- **Error Rate (bulk)**: 0%

  The absence of errors during the bulk tasks indicates a reliable operation under the given load.

#### Implications

1. **Efficient Indexing and Query Performance**: The low cumulative times and throttle times for indexing operations suggest that the cluster can handle this dataset efficiently, likely due to its small size.
   
2. **Resource Utilization**: Memory and GC metrics indicate that the cluster had ample resources to handle the workload without requiring garbage collection. This points to well-provisioned hardware or a workload that does not heavily stress the system.
   
3. **Stable Throughput**: Consistent throughput values imply that the operations are stable and predictable. 

4. **Low Error Rate**: A 0% error rate in bulk operations suggests that there are no operational issues affecting data ingest.

5. **Potential Scalability**: Given the efficient handling of the current workload with minimal resource strains, the cluster should scale well with larger datasets, although increased indexing and query loads should be similarly tested.

In conclusion, the Elasticsearch cluster demonstrates healthy performance and efficient resource utilization for the given dvitel-geo dataset. Continued monitoring and additional testing with larger datasets would help ensure ongoing performance and scalability.

'''

import os 
import sys
import openai
import yaml
from bs4 import BeautifulSoup

from data_acquisition import Webscraper
scraper=Webscraper()

log_path=sys.argv[1] 
track_path=sys.argv[2] 

with open(f'{log_path}/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

openai.api_key = config['openai']['api_key']

with open(f'{log_path}/report.md', 'rt') as f: 
    report=f.read() 

with open(f'{track_path}/track.json', 'rt') as f: 
    track=f.read() 

if config['scrape_mode'] == 'hface':
    doc=scraper.fetch_html(config['huggingface_settings']['full_url'])
    soup = BeautifulSoup(doc['content'], 'html.parser')
    dataset_description=soup.text
else: 
    dataset_description='The dataset is a collection of wikipedia articles in plaintext.'

system_prompt=f'''
You are an analysis engine for ElasticSearch ESRally benchmarker. 
ESRally has just executed a track run on a remote elasticsearch instance. 
It has done so using custom data.

Here is a sample report. I would like you to follow its style when you write your report later:
{SAMPLE_REPORT}
Remember that this sample you saw is just a sample and its contents DO NOT reflect the actual report. That will come later.

Here is the dataset description:
{dataset_description}

Here is the track.json that defines the custom track:
{track}

You will receive a report. Please write a comprehensive analysis of the report and what the implications may be for the health and performance of the elasticsearch cluster. 
Do not waste time on explanations or background. Focus only on writing the report and nothing more. Be maximally detailed and comprehensive. 
Make sure to consider the implications of the data that was used and what it may mean for ElasticSearch applications built using the cluster that was benchmarked. Include that discussion in your report.
Please consider the specific operations defined in track.json. Together with the data set, what do they reveal about the cluster? Factor in datatypes and subject matter. Factor in the size of the dataset.
Length is not an issue. Be as lengthy as required to convey all the detail possible.

Here is the report of results from ESRally: 
{report}
'''

prompt=f'''
Please write the report now.
'''


# Call OpenAI's API to get a response
prompt='Hello'
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
)

# Extract the assistant's message
assistant_message = response['choices'][0]['message']['content']

save_path=f'{log_path}/gpt_report.md'
with open(save_path, 'w', encoding='utf-8') as file:
    file.write(assistant_message)
import os 
import sys
import pandas as pd
import matplotlib.pyplot as plt

def visualize_esrally_report(report, save_path):
    # Convert the report text into a pandas DataFrame
    data = [line.split('|')[1:-1] for line in report.strip().split('\n')]
    columns = [col.strip() for col in data[0]]
    rows = [[col.strip() for col in row] for row in data[1:]]

    df = pd.DataFrame(rows, columns=columns)
    
    # Convert the 'Value' column to numeric, forcing errors to NaN for non-numeric entries
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

    # Separate the data into categories based on the metric names
    indexing_metrics = df[df['Metric'].str.contains('indexing', case=False)]
    merge_metrics = df[df['Metric'].str.contains('merge', case=False)]
    refresh_metrics = df[df['Metric'].str.contains('refresh', case=False)]
    flush_metrics = df[df['Metric'].str.contains('flush', case=False)]
    gc_metrics = df[df['Metric'].str.contains('GC', case=False)]
    storage_metrics = df[df['Metric'].str.contains('size|Segment count', case=False)]
    heap_metrics = df[df['Metric'].str.contains('Heap', case=False)]
    ingest_metrics = df[df['Metric'].str.contains('Ingest', case=False)]

    # Helper function to create bar plots
    def plot_metrics(metrics_df, title):
        plt.figure(figsize=(10, 6))
        plt.barh(metrics_df['Metric'], metrics_df['Value'], color='skyblue')
        plt.xlabel('Value')
        plt.title(title)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        # Save the plot to the specified path
        plt.savefig(os.path.join(save_path, f"{title}.png"))
        plt.close()

    os.makedirs(save_path, exist_ok=True)
    # Plot each category
    plot_metrics(indexing_metrics, 'Indexing Metrics')
    plot_metrics(merge_metrics, 'Merge Metrics')
    plot_metrics(refresh_metrics, 'Refresh Metrics')
    plot_metrics(flush_metrics, 'Flush Metrics')
    plot_metrics(gc_metrics, 'Garbage Collection Metrics')
    plot_metrics(storage_metrics, 'Storage Metrics')
    plot_metrics(heap_metrics, 'Heap Usage Metrics')
    plot_metrics(ingest_metrics, 'Ingest Pipeline Metrics')


base_path=str(sys.argv[1])
report_path=f'{base_path}/report.md'
save_path=f'{base_path}/viz/'

with open(report_path, 'rt') as f: 
    data=f.read() 

visualize_esrally_report(data, save_path)



# Sleeping to allow ES To update itself
path=$(pwd -P)
timestamp=$(date +"%Y%m%d_%H%M%S")
log_dir="$path/logs/$timestamp"
log_track_path="$log_dir/track.json"
log_config_path="$log_dir/config.yaml"
config_file="$path/config.yaml"
wikipython_script_path="$path/python/wikidata_collector.py"
hfacepython_script_path="$path/python/hfacedata_collector.py"
viz_script_path="$path/python/visualize_report.py"
gpt_script_path="$path/python/gpt.py"
ui_path="$path/python/ui.py"
scrape_mode=$(yq e '.scrape_mode' "$config_file")

mkdir -p "$log_dir"
cp $config_file $log_config_path


if [ "$scrape_mode" == "wiki" ]; then
    python $wikipython_script_path $path $timestamp
else
    python $hfacepython_script_path $path $timestamp
fi

sleep 3

if [ "$scrape_mode" == "wiki" ]; then
    track_name=$(yq e '.esrally_wiki.track_name' "$config_file")
    target_hosts=$(yq e '.esrally_wiki.target_hosts' "$config_file")
    client_options=$(yq e '.esrally_wiki.client_options' "$config_file")
    indices=$(yq e '.esrally_wiki.indices' "$config_file")
    output_path=$(yq e '.esrally_wiki.output_path' "$config_file")
    track_path=$(yq e '.esrally_wiki.track_path' "$config_file")
    pipeline=$(yq e '.esrally_wiki.pipeline' "$config_file")
else
    track_name=$(yq e '.esrally_hface.track_name' "$config_file")
    target_hosts=$(yq e '.esrally_hface.target_hosts' "$config_file")
    client_options=$(yq e '.esrally_hface.client_options' "$config_file")
    indices=$(yq e '.esrally_hface.indices' "$config_file")
    output_path=$(yq e '.esrally_hface.output_path' "$config_file")
    track_path=$(yq e '.esrally_hface.track_path' "$config_file")
    pipeline=$(yq e '.esrally_hface.pipeline' "$config_file")
fi


full_track_path="$path/$track_path"


# Define the commands
create_track_command=(
    esrally create-track
    --track "$track_name"
    --target-hosts "$target_hosts"
    --client-options "$client_options"
    --indices "$indices"
    --output-path "$path/$output_path"
)

race_command=(
    esrally race
    --track-path "$full_track_path"
    --target-hosts "$target_hosts"
    --client-options "$client_options"
    --pipeline "$pipeline"
    --report-file "$log_dir/report.md"
    --kill-running-processes
)

# Execute the create track command
"${create_track_command[@]}"
python $ui_path $full_track_path

# Execute the race command
"${race_command[@]}"

python $viz_script_path $log_dir
python $gpt_script_path $log_dir $full_track_path 
cp $full_track_path/track.json $log_track_path

# if [ -d "$path/$track_path" ]; then
#     rm -rf "$path/$track_path"s
#     echo "Deleted directory: $path/$track_path" 
# else
#     echo "Directory not found: $path/$track_path"
# fi
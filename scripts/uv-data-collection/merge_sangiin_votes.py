import json
import os
import glob

def merge_json_files(directory, output_filename="all_sangiin_votes.json"):
    merged_data = {}
    json_files = glob.glob(os.path.join(directory, "tmp*.json"))

    print(f"Found JSON files: {json_files}") # Debug print

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded data from {file_path}: {data}") # Debug print
                merged_data.update(data)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    output_path = os.path.join(directory, output_filename)
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(merged_data, outfile, ensure_ascii=False, indent=4)
    print(f"すべてのJSONファイルが {output_path} にまとめられました。")

    # Delete individual JSON files after merging
    for file_path in json_files:
        try:
            os.remove(file_path)
            print(f"削除しました: {file_path}")
        except Exception as e:
            print(f"ファイルの削除中にエラーが発生しました {file_path}: {e}")

if __name__ == "__main__":
    merge_json_files("/Users/hironeko/Work/private/new-jp-search/")
#!/usr/bin/python

import os
import sys
import argparse
import json
from datetime import datetime
from dateutil.parser import parse
import subprocess

def get_metadata(filename):
    command = ["exiftool", "-json", filename]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        metadata = result.stdout
        return metadata
    else:
        raise Exception(f"Failed to get metadata for {filename}")

def rename_media_files(input_path, output_path=None, keep_original=False):
    if output_path is None:
        output_path = input_path

    for root, dirs, files in os.walk(input_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                metadata = get_metadata(filepath)
                print(metadata)
                json_data = json.loads(metadata)[0]  # Assumes exiftool returns metadata as a list of dictionaries
                
                if 'MediaCreateDate' in json_data:
                    date = json_data['MediaCreateDate']
                elif 'CreateDate' in json_data:
                    date = json_data['CreateDate']
                # elif 'Whatsapp' in json_data:
                #     date = 
                else:
                    date = json_data['FileModifyDate']
                parsed_date = parse(date)
                new_filename = parsed_date.strftime("%Y%m%d_%H%M%S") + os.path.splitext(filename)[1]
                new_filepath = os.path.join(output_path, new_filename)
                os.rename(filepath, new_filepath)
                
                if keep_original:
                    shutil.copy2(filepath, os.path.join(output_path, filename))
                    
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Rename media files based on their EXIF data")
    parser.add_argument("-i", "--input_path", help="Path to the folder containing the media files")
    parser.add_argument("-o", "--output-path", help="Path to the output folder (default is input folder)")
    parser.add_argument("-k", "--keep-original", action="store_true", help="Keep original files in addition to renaming")
    args = parser.parse_args()

    input_path = args.input_path
    output_path = args.output_path
    keep_original = args.keep_original

    if not os.path.isdir(input_path):
        print("Error: Input path is not a directory.")
        sys.exit(1)

    if output_path and not os.path.isdir(output_path):
        print("Error: Output path is not a directory.")
        sys.exit(1)

    rename_media_files(input_path, output_path, keep_original)

if __name__ == "__main__":
    main()

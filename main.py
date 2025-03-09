#!/usr/bin/python

import os
import sys
import argparse
import json
from datetime import datetime
from dateutil.parser import parse
import subprocess
import shutil
import re

def get_metadata(filename):
    command = ["exiftool", "-json", filename]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        metadata = result.stdout
        return metadata
    else:
        raise Exception(f"Failed to get metadata for {filename}")

def extract_timestamp_from_filename(filename):
    match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename)
    if match:
        year, month, day, hour, minute, second = match.groups()
        timestamp = f"{year}:{month}:{day} {hour}:{minute}:{second}"
        return timestamp
    else:
        return None
    
def rename_media_files(input_path, output_path=None, keep_original=False, force=False):
    if output_path is None:
        output_path = input_path

    for root, dirs, files in os.walk(input_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                metadata = get_metadata(filepath)
                print(metadata)
                json_data = json.loads(metadata)[0]  # Assumes exiftool returns metadata as a list of dictionaries
            except Exception as e:                
                json_data = None
                print(f"Error exctracting metadata from file {filepath}: {e}")    

            if os.path.getsize(filepath) > 0:
                try:
                    dtparse_format = "%Y:%m:%d %H:%M:%S"
                    if json_data is None:
                        date = extract_timestamp_from_filename(filepath)
                    elif 'DateTimeOriginal' in json_data:
                        date = json_data['DateTimeOriginal']
                    elif 'CreateDate' in json_data:
                        date = json_data['CreateDate']
                    elif 'ModifyDate' in json_data:
                        date = json_data['ModifyDate']
                    elif 'FileModifyDate' in json_data:
                        date = json_data['FileModifyDate'] #2025:03:02 23:03:50+00:00
                        dtparse_format = "%Y:%m:%d %H:%M:%S%z"

                    else:
                        date = extract_timestamp_from_filename(filepath)
                    
                    # parsed_date = parse(date)
                    # Custom parsing format
                    parsed_date = datetime.strptime(date, dtparse_format)

                    new_filename = parsed_date.strftime("%Y%m%d_%H%M%S") + os.path.splitext(filename)[1]
                    new_filepath = os.path.join(output_path, new_filename)
                    
                    if keep_original:
                        if os.path.exists(new_filepath) and not force:
                            print(f"Skipping {filename}: File already exists. New name: {new_filepath}")                        
                        else:
                            shutil.copy2(filepath, new_filepath)
                    else:
                        if os.path.exists(new_filepath) and not force:
                            print(f"Skipping {filename}: File already exists. New name: {new_filepath}")
                            # os.remove(filepath)
                            os.rename(filepath, "___" + new_filepath)
                        else:
                            os.rename(filepath, new_filepath)
                        
                except Exception as e:
                    print(f"Error moving/renaming file {filepath}: {e}")
            else:
                print(f"Filesize is zero on file: {filepath}")  

def main():
    parser = argparse.ArgumentParser(description="Rename media files based on their EXIF data")
    parser.add_argument("-i", "--input-path", required=True, help="Path to the folder containing the media files")
    parser.add_argument("-o", "--output-path", required=False, help="Path to the output folder (default is input folder)")
    parser.add_argument("-k", "--keep-original", action="store_true", help="Keep original files in addition to renaming")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing files")
    args = parser.parse_args()

    input_path = args.input_path
    output_path = args.output_path
    keep_original = args.keep_original
    force = args.force

    if not os.path.isdir(input_path):
        print("Error: Input path is not a directory.")
        sys.exit(1)

    if output_path and not os.path.isdir(output_path):
        print("Error: Output path is not a directory.")
        sys.exit(1)

    rename_media_files(input_path, output_path, keep_original, force)

if __name__ == "__main__":
    main()

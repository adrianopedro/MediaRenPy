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
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    # percent = ("{0:.2f}").format(100 * (iteration / float(total)))
    percent = 100 * (iteration / float(total))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent:.2f}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def rename_media_files(input_path, output_path=None, keep_original=False, force=False, debug=False):
    if output_path is None:
        output_path = input_path

    total = sum([len(files) for r, d, files in os.walk(input_path)])
    i = 0
    printProgressBar(i, total, prefix = 'Progress:', suffix = 'Complete', length = 50)

    for root, dirs, files in os.walk(input_path):
        for filename in files:
            i += 1
            printProgressBar(i, total, prefix = 'Progress:', suffix = 'Complete', length = 50)
            filepath = os.path.join(root, filename)
            try:
                metadata = get_metadata(filepath)
                if debug:
                    print(metadata)
                json_data = json.loads(metadata)[0]  # Assumes exiftool returns metadata as a list of dictionaries
            except Exception as e:                
                json_data = None
                print(f"Error exctracting metadata from file {filepath}: {e}")    

            if os.path.getsize(filepath) > 0 and "mrp" not in filepath:
                try:
                    datesfound = []
                    dtparse_format = "%Y:%m:%d %H:%M:%S"
                    # date = extract_timestamp_from_filename(filepath)
                    # parsed_date = datetime.strptime(date, dtparse_format)
                    # datesfound.append(parsed_date)

                    if json_data is None:
                        date = extract_timestamp_from_filename(filepath)
                        parsed_date = datetime.strptime(date, dtparse_format)
                        datesfound.append(parsed_date)
                    if json_data and 'DateTimeOriginal' in json_data and json_data['DateTimeOriginal'] != "":
                        date = json_data['DateTimeOriginal']
                        print(date)
                        parsed_date = datetime.strptime(date, dtparse_format)
                        datesfound.append(parsed_date)
                    if json_data and 'CreateDate' in json_data and json_data['CreateDate'] != "":
                        date = json_data['CreateDate']
                        parsed_date = datetime.strptime(date, dtparse_format)
                        datesfound.append(parsed_date)
                    if json_data and 'ModifyDate' in json_data and json_data['ModifyDate'] != "":
                        date = json_data['ModifyDate']
                        parsed_date = datetime.strptime(date, dtparse_format)
                        datesfound.append(parsed_date)
                    if json_data and 'FileModifyDate' in json_data and json_data['FileModifyDate'] != "":
                        date = json_data['FileModifyDate'] #2025:03:02 23:03:50+00:00
                        dtparse_format = "%Y:%m:%d %H:%M:%S%z"
                        parsed_date = datetime.strptime(date, dtparse_format).replace(tzinfo=None)
                        datesfound.append(parsed_date)
                    if json_data and 'CreationDate' in json_data and json_data['CreationDate'] != "":
                        date = json_data['CreationDate'] #2025:03:02 23:03:50+00:00
                        dtparse_format = "%Y:%m:%d %H:%M:%S%z"
                        parsed_date = datetime.strptime(date, dtparse_format).replace(tzinfo=None)
                        datesfound.append(parsed_date)
                  
                        
                    #Find the oldest date in datesfound list and use it as the new filename                                    
                    parsed_date = min(datesfound)  

                    new_filename = parsed_date.strftime("%Y%m%d_%H%M%S") + "_mrp" + os.path.splitext(filename)[1]
                    new_filepath = os.path.join(output_path, new_filename)
                    
                    if keep_original:
                        if os.path.exists(new_filepath) and not force:
                            if debug:
                                print(f"Skipping {filename}: File already exists. New name: {new_filepath}")                        
                        else:
                            shutil.copy2(filepath, new_filepath)
                    else:
                        if os.path.exists(new_filepath) and not force:
                            if debug:
                                print(f"Skipping {filename}: File already exists. New name: {new_filepath}")
                            os.remove(filepath)
                            # new_filepath = os.path.join(output_path, "__fae__" + new_filename)
                            # os.rename(filepath, new_filepath)
                        else:
                            os.rename(filepath, new_filepath)
                        
                except Exception as e:
                    print(f"Error moving/renaming file {filepath}: {e}")
            else:
                if debug:
                    print(f"Filesize is zero on file or already processed: {filepath}")  

def main():
    parser = argparse.ArgumentParser(description="Rename media files based on their EXIF data")
    parser.add_argument("-i", "--input-path", required=True, help="Path to the folder containing the media files")
    parser.add_argument("-o", "--output-path", required=False, help="Path to the output folder (default is input folder)")
    parser.add_argument("-k", "--keep-original", action="store_true", help="Keep original files in addition to renaming")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing files")
    parser.add_argument("-d", "--debug", action="store_true", help="Show debug data")
    args = parser.parse_args()

    input_path      = args.input_path
    output_path     = args.output_path
    keep_original   = args.keep_original
    force           = args.force
    debug           = args.debug

    if not os.path.isdir(input_path):
        print("Error: Input path is not a directory.")
        sys.exit(1)

    if output_path and not os.path.isdir(output_path):
        print("Error: Output path is not a directory.")
        sys.exit(1)

    rename_media_files(input_path, output_path, keep_original, force, debug)

if __name__ == "__main__":
    main()

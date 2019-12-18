from argparse import ArgumentParser
from enum import Enum
import csv
import shutil
import os
from datetime import date
from multiprocessing import Pool
from exif import batchExif, get_exif_create_date, best_guess_date, write_date, DATE_FORMAT_STRING, fallback_write_date_mov, fallback_write_date_xmp
from common import getListOfFiles

parser = ArgumentParser(description='🔥 in that metadata', epilog='so that metadata can\'t 🔥 you') # how poetic. can you tell i've never written a Python CLI before?
subparsers = parser.add_subparsers(help='commands', dest='command')

scan_parser = subparsers.add_parser('scan_dir', help='Recursively scan a directory for assets')
scan_parser.add_argument('scan_dir', type=str, help='The directory to recursively scan for assets')
scan_parser.add_argument('--dated-csv', type=str, default='dated.csv', help='the output CSV for assets without dates (defaults to dated.csv)')
scan_parser.add_argument('--dateless-csv', type=str, default='dateless.csv', help='the output CSV for assets with dates (defaults to dateless.csv)')

process_dateless_parser = subparsers.add_parser('guess_dates', help='Go through CSV and get best guess metadata for each file')
process_dateless_parser.add_argument('csv', type=str, help='The CSV')
process_dateless_parser.add_argument('--output-csv', type=str, default='best_guess_dates.csv', help='the output CSV')

write_dates_parser = subparsers.add_parser('write_dates', help='Take a CSV of (file_path, timestamp) and write to those file\'s metadata')
write_dates_parser.add_argument('csv', type=str, help='CSV of (file_path, timestamp)')

write_dates_non_jpeg_parser = subparsers.add_parser('write_dates_non_jpeg', help='Take a CSV of (file_path, timestamp) and write to those file\'s metadata, after filtering out the jpeg files. This was required because my first attempt (`exiftool -AllDates=`) only worked correctly for the JPEGs')
write_dates_non_jpeg_parser.add_argument('csv', type=str, help='CSV of (file_path, timestamp)')

sort_csv_parser = subparsers.add_parser('sort_csv', help='Takes a CSV with one column per line and writes out a version with rows sorted alphabetically')
sort_csv_parser.add_argument('csv', type=str, help='CSV to sort')
sort_csv_parser.add_argument('--output', type=str, default='sorted.csv', help='where to write the data')

move_files = subparsers.add_parser('move_files_from_csv', help='Moves a list of files from a CSV to a specified directory')
move_files.add_argument('csv', type=str, help='the list of files to move')
move_files.add_argument('target_dir', type=str, help='directory to move the list of files to')

args = parser.parse_args()

if args.command == 'scan_dir':
    print(f"scanning {args.scan_dir}")
    files = getListOfFiles(args.scan_dir)
    exif_data = batchExif(files)
    assert(len(files) == len(exif_data))

    dateless_files, dated_files = [], []
    for i, file_path in enumerate(files):
        if get_exif_create_date(exif_data[i]) is None:
            dateless_files.append(file_path)
        else:
            dated_files.append(file_path)
    print(f"found {len(dated_files)} assets with dates, {len(dateless_files)} without")

    with open(args.dated_csv, 'w') as dated, open(args.dateless_csv, 'w') as dateless:
        print(f"writing to {args.dated_csv} and {args.dateless_csv} respectively")
        csv.writer(dated).writerows([[file] for file in dated_files])
        csv.writer(dateless, delimiter='\n').writerows([[file] for file in dateless_files])

elif args.command == 'guess_dates':
    print(f"guessing dates from {args.csv}")
    to_write = {}
    with open(args.csv, 'r') as input_csv:
        for row in csv.reader(input_csv, delimiter='\n'):
            guess = best_guess_date(row[0], to_write)
            iso_6709_guess = date.strftime(guess, DATE_FORMAT_STRING)
            print(f"{row[0]} - {iso_6709_guess}")
            to_write[row[0]] = iso_6709_guess
    
    with open(args.output_csv, 'w') as output_csv:
        csv.writer(output_csv).writerows([[key, to_write[key]] for key in to_write])

elif args.command == 'write_dates':
    with open(args.csv, 'r') as input_csv:
        rows = list(csv.reader(input_csv))
        print(f"preparing to write to {len(rows)} files")
        with Pool(processes=20) as pool:
            pool.map(write_date, rows)

elif args.command == 'write_dates_non_jpeg':
    with open(args.csv, 'r') as input_csv:
        rows = list(csv.reader(input_csv))
        for row in filter(lambda x: not (x[0].lower().endswith('jpg') or x[0].lower().endswith('jpeg') or x[0].lower().endswith('tif')), rows):
            known = ['gif', 'mp4', 'mov', 'png']
            assert(any(map(lambda x: row[0].lower().endswith(x), known)))
            if row[0].lower().endswith('gif'):
                fallback_write_date_xmp(row)
            elif row[0].lower().endswith('mp4') or row[0].lower().endswith('mov'):
                fallback_write_date_mov(row)
            elif row[0].lower().endswith('png'):
                fallback_write_date_xmp(row)
            else:
                AssertionError('wut')

elif args.command == 'sort_csv':
    with open(args.csv, 'r') as input_csv:
        data = [line for line in csv.reader(input_csv)]
        with open(args.output, 'w') as output_csv:
            data.sort()
            csv.writer(output_csv).writerows(data)

elif args.command == 'move_files_from_csv':
    with open(args.csv, 'r') as input_csv:
        for line in csv.reader(input_csv):
            shutil.move(line[0], os.path.join(args.target_dir, os.path.basename(line[0])))
            print(line[0], ' -> ', f"{os.path.join(args.target_dir, os.path.basename(line[0]))}")

else:
    AssertionError('wut')
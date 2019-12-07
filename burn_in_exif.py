from argparse import ArgumentParser
from enum import Enum
import csv
from exif import batchExif, get_exif_create_date
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

args = parser.parse_args()

if args.command == 'scan_dir':
    print(f"scanning {args.scan_dir}")
    files = getListOfFiles(args.scan_dir)
    exif_data = batchExif(files)
    assert(len(files) == len(exif_data))

    dateless_files, dated_files = [], []
    for i, file_path in enumerate(files):
        if get_exif_create_date(exif_data[i]) is False:
            dateless_files.append(file_path)
        else:
            dated_files.append(file_path)
    print(f"found {len(dated_files)} assets with dates, {len(dateless_files)} without")

    with open(args.dated_csv, 'w') as dated, open(args.dateless_csv, 'w') as dateless:
        print(f"writing to {args.dated_csv} and {args.dateless_csv} respectively")
        csv.writer(dated, delimiter='\n').writerows([dated_files])
        csv.writer(dateless, delimiter='\n').writerows([dateless_files])

elif args.command == 'guess_dates':
    print(f"guessing dates from {args.csv}")
else:
    AssertionError('wut')
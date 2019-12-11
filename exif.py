import exiftool
import pathlib
from common import getListOfFiles
import datetime

SOURCE_FILE_TAG = 'SourceFile'
FOLDER_DATE_FORMAT_STRING = '%B %d, %Y' # reads "April 1, 2015"
DATE_FORMAT_STRING = '%Y:%m:%d %H:%M:%S' # reads "2015:04:01 08:50:15"

def exifOnFile(file_path):
    with exiftool.ExifTool() as et:
        return et.get_metadata(file_path)

def batchExif(list_of_files):
    with exiftool.ExifTool() as et:
        if list_of_files == []:
            return
        return et.get_metadata_batch(list_of_files)

batch_write_et = exiftool.ExifTool()
def write_date(date_string, file_path):
    with exiftool.ExifTool() as et:
        et.execute(
            '-AllDates={}'.format(date_string).encode('utf-8'),
            file_path.encode('utf-8')
        )

"""
Anecdotally, it looks like Photos treats the date metadata of different types distinctly.
My own experience is that EXIF:{DateTimeOriginal, CreateDate, ModifyDate} are ignored for PNG files... Problematic, I know
My strategy is the following:
JPEG files store their datetime tags in EXIF:{DateTimeOriginal, CreateDate, ModifyDate}, in the DATE_FORMAT_STRING format, timezone information is stored in the '-hh:mm' format in [fill in the 2 keys]
PNG files use XMP:DateCreated, and don't look like they store time zone data... This makes some sense because it looks like most screenshots are PNGs, but I wish the iOS engineers made screenshots more metadata rich
MOV/mp4 files use QuickTime:{MediaCreateDate, MediaModifyDate, TrackCreateDate, TrackModifyDate, CreateDate, ModifyDate} in the same format as the JPEG tags do, and then also store a composite in  QuickTime:{CreationDate, ContentCreateDate} with the time zone (2014:06:04 16:22:29-04:00)
"""
def _get_exif_create_date(exif_dict):
    jpeg_tags = ['EXIF:DateTimeOriginal', 'EXIF:CreateDate', 'EXIF:ModifyDate']
    png_tag = 'XMP:DateCreated'
    mov_tags = ['QuickTime:' + suffix for suffix in ['CreateDate', 'ModifyDate', 'MediaCreateDate', 'MediaModifyDate', 'TrackCreateDate', 'TrackModifyDate']]

    if any([t in exif_dict for t in jpeg_tags]):
        assert(all([t in exif_dict for t in jpeg_tags])), exif_dict
        assert (exif_dict[SOURCE_FILE_TAG].lower().endswith('jpeg') or exif_dict[SOURCE_FILE_TAG].lower().endswith('jpg')), exif_dict[SOURCE_FILE_TAG]
        return exif_dict[jpeg_tags[0]]

    if png_tag in exif_dict:
        assert exif_dict[SOURCE_FILE_TAG].lower().endswith('png'), exif_dict[SOURCE_FILE_TAG]
        return exif_dict[png_tag]

    if any([t in exif_dict for t in mov_tags]):
        for t in mov_tags: # the tags are in order of best tag. return the first match found
            if t in exif_dict:
                return exif_dict[t] 

    return None

def get_exif_create_date(exif_dict):
    as_string = _get_exif_create_date(exif_dict)
    if as_string is None:
        return None
    else:
        return datetime.datetime.strptime(as_string, DATE_FORMAT_STRING)
    

"""
Cases
    a: IF the prev and next file in the directory have dates, return the average of the two dates
    b: IF the prev exists, return prev+1sec
    c: IF the next exists, return next-1sec
    d: General fallback: Grab the date from the parent folder name, return noon on that day
"""
def best_guess_date(file_path):
    parent_dir_name = pathlib.Path(file_path).parts[-2]
    files_in_dir = sorted(getListOfFiles(pathlib.Path(file_path).parent))
    exif_of_files_in_dir = batchExif(files_in_dir)
    
    cur_file_index = files_in_dir.index(file_path)
    
    prev_date = None
    if cur_file_index != 0:
        prev_date = get_exif_create_date(exif_of_files_in_dir[cur_file_index - 1])

    next_date = None
    if cur_file_index != (len(files_in_dir) - 1):
        next_date = get_exif_create_date(exif_of_files_in_dir[cur_file_index + 1])

    if prev_date is not None and next_date is not None: # a
        return prev_date + abs((prev_date - next_date) / 2)
    elif prev_date is not None: # b
        return prev_date + datetime.timedelta(seconds=1)
    elif next_date is not None: # c
        return next_date - datetime.timedelta(seconds=1)
    else: # d
        date_from_parent_dir_name = parent_dir_name.split(' ')[-3:]
        day = datetime.datetime.strptime(' '.join(date_from_parent_dir_name), FOLDER_DATE_FORMAT_STRING)
        return day + datetime.timedelta(hours=12)

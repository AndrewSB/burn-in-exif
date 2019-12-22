import exiftool
import pathlib
from common import getListOfFiles, safe_list_subscript
import datetime
import mac_tag
import subprocess

SOURCE_FILE_TAG = 'SourceFile'
FOLDER_DATE_FORMAT_STRING = '%B %d, %Y' # reads "April 1, 2015"
DATE_FORMAT_STRING = '%Y:%m:%d %H:%M:%S' # reads "2015:04:01 08:50:15"
TIF_DATE_FORMAT_STRING = '%Y:%m:%d' # reads "2015:04:01"
TIF_TIME_FORMAT_STRING = '%H:%M:%S%z' # reads "04:15:43". Concat a "-07:00" onto the end to match the expected spec

jpeg_tags = ['EXIF:DateTimeOriginal', 'EXIF:CreateDate', 'EXIF:ModifyDate']
png_tag = 'XMP:DateCreated'
tif_time_tag = 'IPTC:TimeCreated'
tif_date_tag = 'IPTC:DateCreated'
mov_tags = ['QuickTime:CreateDate', 'QuickTime:ModifyDate', 'QuickTime:MediaCreateDate', 'QuickTime:MediaModifyDate'] + ['Track1:' + suffix for suffix in ['MediaCreateDate', 'MediaModifyDate', 'TrackCreateDate', 'TrackModifyDate']]

def exifOnFile(file_path):
    with exiftool.ExifTool() as et:
        return et.get_metadata(file_path)

def batchExif(list_of_files):
    with exiftool.ExifTool() as et:
        if list_of_files == []:
            return
        return et.get_metadata_batch(list_of_files)

def write_date(row):
    file_path = row[0]
    date_string = row[1]
    date_string_with_ca_timezone = date_string + '-07:00'
    file_extension_specific_flags = []
    low = file_path.lower()
    print(f"{file_path} <= {date_string}")

    mac_tag.add('Pink', file_path)

    failures = []

    # special processing for videos -- the et flags are much longer, pyexiftool kept complaining with parsing/formatting errors. just using subprocess instead
    if low.endswith('mp4') or low.endswith('mov'):
        retcode = subprocess.call(['exiftool', '-overwrite_original', '-m', *[u'-%s=%s' % (tag, date_string) for tag in mov_tags], '-QuickTime:Keywords=guessed_date', file_path])
        if retcode != 0:
            return [file_path, retcode]
        else:
            return

    if low.endswith('jpeg') or low.endswith('jpg'):
        file_extension_specific_flags.append('-AllDates={}'.format(date_string).encode('utf-8'))
    elif low.endswith('png'):
        file_extension_specific_flags.append('-{}={}'.format(png_tag, date_string_with_ca_timezone).encode('utf-8'))
    elif low.endswith('tif'):
        date_object = datetime.datetime.strptime(date_string, DATE_FORMAT_STRING)
        file_extension_specific_flags += [
            '-{}={}'.format(tif_date_tag, datetime.datetime.strftime(date_object, TIF_DATE_FORMAT_STRING)).encode('utf-8'),
            '-{}={}-07:00'.format(tif_time_tag, datetime.datetime.strftime(date_object, TIF_TIME_FORMAT_STRING)).encode('utf-8')        
        ]
    elif low.endswith('gif'):
        print(f"GIF no-op!!! {file_path}") # can't figure out if apple reads EXIF from a GIF. Going to manually edit the few gifs I have
        return
    else:
        assert(False), row[0]
    with exiftool.ExifTool() as et:
        GUESSED_DATE = 'guessed_date'
        ret = et.execute(
            *(['-overwrite_original'.encode('utf-8')] +
            file_extension_specific_flags +
            [f"-IPTC:Keywords={GUESSED_DATE}".encode('utf-8'), f"-XMP:Subject={GUESSED_DATE}".encode('utf-8'),
            file_path.encode('utf-8')])
        )
        print(ret)
        if b'error' in ret:
            return [file_path, ret]

"""
Anecdotally, it looks like Photos treats the date metadata of different types distinctly.
My own experience is that EXIF:{DateTimeOriginal, CreateDate, ModifyDate} are ignored for PNG files... Problematic, I know
My strategy is the following:
JPEG files store their datetime tags in EXIF:{DateTimeOriginal, CreateDate, ModifyDate}, in the DATE_FORMAT_STRING format, timezone information is stored in the '-hh:mm' format in [fill in the 2 keys]
PNG files use XMP:DateCreated, and don't look like they store time zone data... This makes some sense because it looks like most screenshots are PNGs, but I wish the iOS engineers made screenshots more metadata rich
MOV/mp4 files use QuickTime:{MediaCreateDate, MediaModifyDate, TrackCreateDate, TrackModifyDate, CreateDate, ModifyDate} in the same format as the JPEG tags do, and then also store a composite in  QuickTime:{CreationDate, ContentCreateDate} with the time zone (2014:06:04 16:22:29-04:00)
"""
def _get_exif_create_date(exif_dict):
    if any([t in exif_dict for t in jpeg_tags]):
        assert (exif_dict[SOURCE_FILE_TAG].lower().endswith('jpeg') or exif_dict[SOURCE_FILE_TAG].lower().endswith('jpg')), exif_dict[SOURCE_FILE_TAG]
        value = exif_dict.get(jpeg_tags[0], exif_dict.get(jpeg_tags[1], exif_dict.get(jpeg_tags[2])))
        assert(value is not None), exif_dict
        return value

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
        try:
            return datetime.datetime.strptime(as_string, DATE_FORMAT_STRING)
        except:
            print('would have crashed processing', exif_dict[SOURCE_FILE_TAG], as_string) # a few values were stored as 0000:00:00 00:00:00, which is invalid. They're caught here
            return None

"""
Cases
    a: IF the prev and next file in the directory have dates, return the average of the two dates
    b: IF the prev exists, return prev+1sec
    c: IF the next exists, return next-1sec
    d: General fallback: Grab the date from the parent folder name, return noon on that day
"""
def best_guess_date(file_path, pending_writes):
    parent_dir_name = pathlib.Path(file_path).parts[-2]
    files_in_dir = sorted(getListOfFiles(pathlib.Path(file_path).parent))
    exif_of_files_in_dir = batchExif(files_in_dir)
    cur_file_index = files_in_dir.index(file_path)
    
    prev_date = None
    maybe_prev_date_string = pending_writes.get(safe_list_subscript(files_in_dir, cur_file_index - 1))
    if maybe_prev_date_string is not None:
        prev_date = datetime.datetime.strptime(maybe_prev_date_string, DATE_FORMAT_STRING)
    if prev_date is None and safe_list_subscript(exif_of_files_in_dir, cur_file_index - 1) is not None:
        prev_date = get_exif_create_date(exif_of_files_in_dir[cur_file_index - 1])

    next_date = None
    maybe_next_date_string = pending_writes.get(safe_list_subscript(files_in_dir, cur_file_index + 1))
    if maybe_next_date_string is not None:
        datetime.datetime.strptime(maybe_next_date_string, DATE_FORMAT_STRING)
    if next_date is None and safe_list_subscript(exif_of_files_in_dir, cur_file_index + 1) is not None:
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

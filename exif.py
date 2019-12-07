import exiftool


SOURCE_FILE_TAG = 'SourceFile'
DATE_FORMAT_STRING = ''

"""
Anecdotally, it looks like Photos treats the date metadata of different types distinctly.
My own experience is that EXIF:{DateTimeOriginal, CreateDate, ModifyDate} are ignored for PNG files... Problematic, I know
My strategy is the following:
JPEG files store their datetime tags in EXIF:{DateTimeOriginal, CreateDate, ModifyDate}, in the DATE_FORMAT_STRING format, timezone information is stored in the '-hh:mm' format in [fill in the 2 keys]
PNG files use XMP:DateCreated, and don't look like they store time zone data... This makes some sense because it looks like most screenshots are PNGs, but I wish the iOS engineers made screenshots more metadata rich
MOV/mp4 files use QuickTime:{MediaCreateDate, MediaModifyDate, TrackCreateDate, TrackModifyDate, CreateDate, ModifyDate} in the same format as the JPEG tags do, and then also store a composite in  QuickTime:{CreationDate, ContentCreateDate} with the time zone (2014:06:04 16:22:29-04:00)
"""
def get_exif_create_date(exif_dict):
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

    return False

def exifOnFile(file_path):
    with exiftool.ExifTool() as et:
        return et.get_metadata(file_path)

def batchExif(list_of_files):
    with exiftool.ExifTool() as et:
        if list_of_files == []:
            return
        return et.get_metadata_batch(list_of_files)
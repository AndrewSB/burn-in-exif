import sys
import os
import exiftool


HAS_EXIF = []
DOESNT_HAVE_EXIF = []


def recursiveWalk(walk_dir, file_lambda, list_of_files_in_dir_lambda):
    for root, subdirs, files in os.walk(walk_dir):
        files = [f for f in files if not f[0] == '.']
        subdirs[:] = [d for d in subdirs if not d[0] == '.']

        for filename in files:
            file_path = os.path.join(root, filename)
            file_lambda(file_path)

        list_of_files_in_dir_lambda([os.path.join(root, f) for f in files])
        
        for subdir in subdirs:
            subdir_path = os.path.join(root, subdir)
            recursiveWalk(subdir_path, file_lambda, list_of_files_in_dir_lambda)


def process(file_path, exifDictionary):
    global HAS_EXIF
    global DOESNT_HAVE_EXIF
    d = exifDictionary
    assert(file_path == d['SourceFile'])

    if get_exif_create_date(d) == False:
        DOESNT_HAVE_EXIF.append(file_path)
    else:
        HAS_EXIF.append(file_path)

def exifOnFile(file_path):
    with exiftool.ExifTool() as et:
        process(file_path, et.get_metadata(file_path))


def exifOnDir(list_of_files):
    global HAS_EXIF
    global DOESNT_HAVE_EXIF
    with exiftool.ExifTool() as et:
        if list_of_files == []:
            return
        else:
            metadatas = et.get_metadata_batch(list_of_files)
            for d in metadatas:
                process(d['SourceFile'], d)

def import_exif_file(file_path):
    with exiftool.ExifTool() as et:
        d = et.get_metadata(file_path)
        explain_missing_exif(file_path)
        # print(file_path, get_exif_create_date(d))
        # at this point, we'd instruct the AWS machine to move this somewhere so it can be downloaded by our client in batch for importing

def explain_missing_exif(file_path):
    if is_live_photo_pair(file_path):
        print('yay')
    else:
        print('crie')

    with exiftool.ExifTool() as et:
        d = et.get_metadata(file_path)
        # print(file_path, d)

def is_live_photo_pair(file_path):
    filename = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(filename)[0]
    candidate = os.path.join(os.path.dirname(file_path), filename_without_extension)

    print(candidate)
    return False

def get_exif_create_date(exif_dict):
    d = exif_dict
    if "EXIF:DateTimeOriginal" in d or "EXIF:CreateDate" in d:
        assert(d['EXIF:DateTimeOriginal'] == d['EXIF:CreateDate'])
        assert('QuickTime:MediaCreateDate' not in d)
        return d['EXIF:DateTimeOriginal']

    if 'QuickTime:MediaCreateDate' in d:
        assert(d['QuickTime:CreateDate'] == d['QuickTime:MediaCreateDate'])
        return d['QuickTime:MediaCreateDate']
    
    return False

if __name__ == "__main__":   
    assert(len(sys.argv) == 2) # as in python3 listAssets.py filepath
    walk_dir = sys.argv[1]
    print('searching in', walk_dir)

    recursiveWalk(walk_dir, lambda x: None, lambda list_of_files_in_dir: exifOnDir(list_of_files_in_dir))
    print("with exif date:", len(HAS_EXIF))
    for path in HAS_EXIF:
        import_exif_file(path)
    print("without exif date:", len(DOESNT_HAVE_EXIF))
    # for path in DOESNT_HAVE_EXIF:
    #     explain_missing_exif(path)

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

    if "EXIF:DateTimeOriginal" in d or "EXIF:CreateDate" in d:
        HAS_EXIF.append(file_path)
        assert(d['EXIF:DateTimeOriginal'] == d['EXIF:CreateDate'])
    else:
        DOESNT_HAVE_EXIF.append(file_path)


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


if __name__ == "__main__":   
    assert(len(sys.argv) == 1)
    print('searching in', sys.argv[0])

    walk_dir = sys.argv[0]
    recursiveWalk(walk_dir, lambda x: None, lambda list_of_files_in_dir: exifOnDir(list_of_files_in_dir))
    print("with exif date:", len(HAS_EXIF))
    print("without exif date:", len(DOESNT_HAVE_EXIF))

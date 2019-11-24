import sys
import os
import shutil
from listAssets import recursiveWalk, exifOnDir, HAS_EXIF, DOESNT_HAVE_EXIF
# import listAssets


def move_file(file_path, file_parent_common_prefix, target_dir):
    common_prefix = os.path.commonprefix([file_path, file_parent_common_prefix])
    common_prefix_dirlen = len(os.path.normpath(common_prefix).split(os.sep))
    file_to_place_into_target = os.path.normpath(file_path).split(os.sep)[common_prefix_dirlen:]
    result = os.path.join(target_dir, *file_to_place_into_target)

    print("moving", file_path, "to", result)
    os.makedirs(os.path.dirname(result), exist_ok=True)
    shutil.copy2(file_path, result)


if __name__ == "__main__":
    argv = sys.argv[1:]
    assert(len(argv) == 2) # as in python3 move-conformed-assets.py dirToScan dirToExportTo
    walk_dir = argv[0]; export_dir = argv[1]
    print('searching in', walk_dir, "moving to", export_dir)

    recursiveWalk(walk_dir, lambda x: None, lambda files_in_dir: exifOnDir(files_in_dir))
    print("with exif date:", len(HAS_EXIF))
    for path in HAS_EXIF:
        move_file(path, walk_dir, export_dir)
    print("without exif date:", len(DOESNT_HAVE_EXIF))



import sys
# from .listAssets import recursiveWalk, exifOnDir, HAS_EXIF, DOESNT_HAVE_EXIF
import listAssets


def move_file(file_path, target_dir):
    print("would move", file_path, "to", target_dir)


if __name__ == "__main__":
    argv = sys.argv[1:]
    assert(len(argv) == 2)
    print('searching in', argv[0], "moving to", argv[1])

    walk_dir = argv[0]
    listAssets.recursiveWalk(walk_dir, lambda x: None, lambda files_in_dir: listAssets.exifOnDir(files_in_dir))
    print("with exif date:", len(listAssets.HAS_EXIF))
    print("without exif date:", len(listAssets.DOESNT_HAVE_EXIF))



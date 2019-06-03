# burn-in-exif

A set of python utilities I wrote to be able to transfer EXIF data (primary "Create Date") from copies of assets, or the file system

## Strategy
I have one directory with all the assets, with about 50% valid, and 50% missing EXIF data.

Some of the assets are iOS live photo pairs - i.e. a .mov file, and a .jpeg file. Those need to first be removed from the corpus and reconsituted -- I believe they have 100% valid EXIF data in the jpeg file.

For the 50% missing, I have 2 heuristics to backfill the correct data:
1. I have a seperate directory, with completely different file names of compressed assets, some of the assets in there are versions of the assets missing EXIF data, will copy from there
2. For the assets still remaining, the folders which contain the assets have a date on them -- I can probably use that date to estimate the EXIF date to noon on the day the folder name mentions. For these assets, I'll tag them and store them somewhere knowing that their dates are wrong, so if I ever get additional signal I can recompute for these ones

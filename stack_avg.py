#!/usr/bin/python3
#
# Version: 2023.09.11
# Author: Serhiy Kobyakov


import os
import sys
import glob
import cv2 as cv


def print_usage():
    usage_str = """The script combines (averages) several images into one.
Input images may be 8- or 16-bit images.

Usage: stack_avg.py [images list]

Example: stack_avg.py *.tif
"""
    print(usage_str)
    sys.exit(1)


class AvgImages:
    """average number of images and save result into separate file"""
    def __init__(self, images_list, averaged_image_fname):
        print(f"Averaging {len(images_list)} images...", end='', flush=True)

        # rolling average the images
        out_image = cv.imread(images_list[0], cv.IMREAD_UNCHANGED)
        # convert the image to 16bit if the input is 8bit
        # if out_image.dtype == 'uint8':
        #     out_image = out_image.astype('uint16') * 257
        print(out_image.dtype)
        for i in range(1, len(images_list)):
            img = cv.imread(images_list[i], cv.IMREAD_UNCHANGED)
            # convert the image to 16bit if the input is 8bit
            # if img.dtype == 'uint8':
            #     img = img.astype('uint16') * 257
            alpha = 1.0 / float(i + 1)
            # print(str(round(1 - alpha, 4)).ljust(6), str(round(alpha, 4)).ljust(6))
            print(".", end='', flush=True)
            out_image = cv.addWeighted(img, alpha, out_image, 1 - alpha, 0.0)
        cv.imwrite(averaged_image_fname, out_image)
        print("done")


if __name__ == '__main__':

    output_fname = ''
    fnames = []
    for arg in sys.argv[1:]:
        if arg == "--help":
            print_usage()
        if os.path.exists(arg):
            # append image file to images list
            fnames.append(arg)

    if len(fnames) < 2:
        print("\n****Error: at least two images must be given as input!\n")
        sys.exit(1)

    # get the filename of the first jpg image in the directory
    # and use this filename (adding suffix) for the output image
    jpegs = sorted(glob.glob(('*.jpg')))
    if len(jpegs) > 0:
        output_fname = jpegs[0][:-4] + "_averaged.tif"
    else:
        output_fname = "00_averaged.tif"

    # do the job!
    AvgImages(fnames, output_fname)

    # restore metadata from the first jpg
    if os.path.isfile(output_fname) and len(jpegs) > 0:
        os.system(f"exiftool -TagsFromFile {jpegs[0]} \"-all:all>all:all\" --Orientation -overwrite_original {output_fname} > /dev/null 2>&1")
        os.system(f"mv {output_fname} ..")

#!/usr/bin/python3
#
# Version: 2023.09.08
# Author: Serhiy Kobyakov


import os
import sys
import glob
import cv2 as cv
import numpy as np


class AvgImages:
    """average number of images and save result into separate file"""
    def __init__(self, images_list, averaged_image_fname):
        print(f"Averaging {len(images_list)} images...", end='', flush=True)

        # rolling average images
        out_image = cv.imread(images_list[0], cv.IMREAD_UNCHANGED)
        for i in range(1, len(images_list)):
            img = cv.imread(images_list[i], cv.IMREAD_UNCHANGED)
            alpha = 1.0 / float(i + 1)
            # print(str(round(1 - alpha, 4)).ljust(6), str(round(alpha, 4)).ljust(6))
            print(".", end='', flush=True)
            out_image = cv.addWeighted(img, alpha, out_image, 1 - alpha, 0.0)
        cv.imwrite(averaged_image_fname, out_image)

        # width, height = cv.imread(images_list[0], cv.IMREAD_COLOR).shape[:2]
        # print(f"\noutimage: {width}x{height}")
        # out_image = np.zeros((width, height, 3), np.uint16)
        # for i in range(1, len(images_list)):
        #     img = cv.imread(images_list[i], cv.IMREAD_COLOR)
        #     print("img: ", type(img), img.dtype)
        #     out_image += img
        # out_image_16bit = (np.round(out_image / len(images_list))).astype(np.uint16)
        # # out_image_16bit = out_image.astype(np.uint16)
        # cv.imwrite(averaged_image_fname, out_image_16bit)
        print("done")


if __name__ == '__main__':

    output_fname = ''
    read_output_fname = False
    fnames = []
    for arg in sys.argv[1:]:
        if read_output_fname:
            output_fname = arg
            read_output_fname = False
            continue

        if arg[0] == '-':
            if arg == '-o':
                read_output_fname = True
            else:
                print(f"** Error: unknown argument: {arg}")
        elif os.path.exists(arg):
            # append image file to images list
            fnames.append(arg)

    if len(fnames) == 0:
        print("\n****Error: no image is given as input!\n")
        sys.exit(1)

    jpegs = sorted(glob.glob(('*.jpg')))

    if len(jpegs) > 0:
        output_fname = jpegs[0][:-4] + "_averaged.tif"
    else:
        output_fname = "00_averaged.tif"

    # print(output_fname)

    AvgImages(fnames, output_fname)

    # restore metadata
    if os.path.isfile(output_fname) and len(jpegs) > 0:
        os.system(f"exiftool -TagsFromFile {jpegs[0]} \"-all:all>all:all\" --Orientation -overwrite_original {output_fname} > /dev/null 2>&1")
        os.system(f"mv {output_fname} ..")

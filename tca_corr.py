#!/usr/bin/python3
# Version: 2023.07.21
# Author: Serhiy Kobyakov

import math
import os
import subprocess
import sys


class TCA_Corr:
    """Perform transverse chromatic aberration (TCA) correction on given image"""

    # maximum allowed channel shift in pixels (visible to the naked eye)
    # above which we need to correct image for TCA
    TCA_MAX_SHIFT = 0.45

    IMG_FNAME = ''
    IMGW = ''
    IMGH = ''
    THER = ''
    INPLACE = ''
    TCA_LINE = ''

    def __init__(self, img_fname, inplace):
        self.IMG_FNAME = img_fname
        self.INPLACE = inplace
        self.IMGW, self.IMGH = self.get_image_size()
        print(f"\nImage: {self.IMG_FNAME}, {self.IMGW}x{self.IMGH}")
        self.THER = math.sqrt(pow(self.IMGW / 2, 2) + pow(self.IMGH / 2, 2))
        # print(f"theR: {self.THER}")
        # self.TCA_LINE = subprocess.check_output('tca_correct -o abcv {0}'.format(self.IMG_FNAME), shell=True).decode('ascii').strip()
        self.TCA_LINE = subprocess.check_output('tca_correct -o v {0}'.format(self.IMG_FNAME), shell=True).decode(
            'ascii').strip()
        # print(self.TCA_LINE)

        if self.tca_correction_required():
            self.do_correct_tca()

    def get_image_size(self):
        sizeline = subprocess.check_output('exiftool -ImageSize -s -s -s {0}'.format(self.IMG_FNAME), shell=True).decode(
                'ascii').strip()
        return int(sizeline.split("x")[0]), int(sizeline.split("x")[1])

    def tca_correction_required(self):
        """check if CA correction required"""
        tca_str = self.TCA_LINE.replace(' -b ', ':')
        rr = abs(1 - 1 / float(tca_str.split(':')[3]))
        rb = abs(1 - 1 / float(tca_str.split(':')[-1]))

        print(f"Red channel shift:  {round(self.THER * rr, 2)} px")
        print(f"Blue channel shift: {round(self.THER * rb, 2)} px")

        if (self.THER * rr > self.TCA_MAX_SHIFT) or (self.THER * rb > self.TCA_MAX_SHIFT):
            print("the image shows visible TCA and it will be corrected")
            return True
        else:
            print("the image doesn't need TCA correction")
            return False

    def do_correct_tca(self):
        """correct CA and backup image"""
        fname, fext_with_dot = os.path.splitext(self.IMG_FNAME)
        fext_with_dot = fext_with_dot.lower()
        tca_corr_fname = fname + "_tca_corr"

        if fext_with_dot == ".jpg":
            os.system('fulla ' + self.TCA_LINE + ' -o ' + tca_corr_fname + fext_with_dot + ' --compression=100 ' + self.IMG_FNAME + ' > /dev/null 2>&1')
        elif fext_with_dot == ".tif" or fext_with_dot == ".tiff":
            os.system('fulla ' + self.TCA_LINE + ' -o ' + tca_corr_fname + fext_with_dot + ' ' + self.IMG_FNAME + ' > /dev/null 2>&1')
        else:
            print(f"***Error: unknown image extension: {fext_with_dot}!")
            exit(1)

        if self.INPLACE:
            if os.path.isfile(tca_corr_fname + fext_with_dot):
                os.system(f"mv {tca_corr_fname + fext_with_dot} {self.IMG_FNAME}")


def print_usage():
    usage_str = """The script estimates TCA correction parameters for every given image individually
and corrects the images accordingly (in case if image needs correction) using given instructions.
The script is a front-end for tca_correct and fulla from hugin repository. You have to install hugin to use this script.

Usage: tca_corr.py [options] [images list]

Example: tca_corr.py -inplace *.jpg

Options:
    -inplace (-i):  edit images inplace; substitute input image with the corrected one
"""
    print(usage_str)
    sys.exit(1)


if __name__ == "__main__":

    # check if fulla and tca_correct are installed
    fulla_output = subprocess.check_output('fulla --help | grep fulla', shell=True).decode('ascii').strip()
    if len(fulla_output) == 0:
        print("\n Please install hugin in order to use this script!\n")
    tca_correct_output = subprocess.check_output('tca_correct --help | grep tca_correct', shell=True).decode('ascii').strip()
    if len(tca_correct_output) == 0:
        print("\n Please install hugin in order to use this script!\n")

    inplace = False
    fnames = []
    for arg in sys.argv[1:]:
        if arg == "--help":
            print_usage()
        elif arg == "-inplace" or arg == "-i":
            inplace = True
        elif os.path.exists(arg):
            # append image file to images list
            fnames.append(arg)
        else:
            print(f"\n****Error: unknown option: {arg}!\n")
            print_usage()

    if len(fnames) == 0:
        print("\n****Error: no images given!")
        print_usage()

    for fname in fnames:
        corr = TCA_Corr(fname, inplace)

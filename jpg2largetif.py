#!/usr/bin/python3

import os
import sys
import subprocess


def print_usage():
    usage_str = """The script converts jpg images to 16-bit tiffs
preserving metadata information.

Usage: jpg2largetif [images list]

Example: jpg2largetif.py *.jpg

Warning: for now the scripts works onl
"""
    print(usage_str)
    sys.exit(1)


def file_is_jpeg(filename) -> bool:
    '''Check if the argument is existing jpg file'''
    output = ''
    if os.path.exists(filename):
        cmd = "exiftool -FileType -s -s -s " + filename
        output = subprocess.check_output(cmd, shell=True).decode('ascii').strip()

    if output == 'JPEG':
        return True
    else:
        return False

def convert_to_ltif(jpg_file):
    '''Convert jpg to tif'''
    tif_file = '{0}.tif'.format(jpg_file[:-4])
    if not os.path.isfile(tif_file):
        command = 'convert {0} -auto-orient -resize 200% -depth 16 -alpha On {1} >/dev/null 2>&1'.format(jpg_file, tif_file)
        os.system(command)
        print('.', end='', flush=True)
        command = "exiftool -TagsFromFile {0} -all:all\>all:all --Orientation -overwrite_original {1} >/dev/null 2>&1".format(jpg_file, tif_file)
        os.system(command)
    print('.', end='', flush=True)


if __name__ == "__main__":

    jpg_files = []

    for arg in sys.argv[1:]:
        if arg == "--help":
            print_usage()
        elif file_is_jpeg(arg):
            # append image file to images list
            jpg_files.append(arg)
        else:
            print(f"\n****Error: unknown option: {arg}!\n")
            print_usage()

    if len(jpg_files) > 0:
        print(f"Converting {len(jpg_files)} images..", end='')

        for jpg_file in jpg_files:
            convert_to_ltif(jpg_file)

        print('done')

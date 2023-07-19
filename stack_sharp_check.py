#!/usr/bin/python3
# Version: 2023.07.19
# Author: Serhiy Kobyakov

# we don't have to blur source images
# below this sigma value
# to achieve reasonable sharpness estimation
min_sigma = 0.5

import os
import sys
import subprocess
from itertools import repeat
import cv2
import multiprocessing as mp
import statistics as stat
import matplotlib.pyplot as plt


def print_usage():
    usage_str = """The script estimates relative sharpness of similar images in working directory
And sort out the less sharp images by adding ".not_sharp_enough" extension to their file names.
    
Usage: stack_sharp_check.py [options] [images list]
    
Example: stack_sharp_check.py -plot-distribution *.tif
    
Options:
    -index (short: -i):       add the laplacian sharpness estimation as a prefix to the image
                              attention! this would change the images filenames
    -plot-distribution (-pd): save distribution plot of estimated values
"""
    print(usage_str)
    sys.exit(1)


def sigma_estimate(image_path):
    """Estimate sigma parameter of gaussian blur based on the image ISO.
    This estimation is purely empirical and tailored for my LG V30 camera images"""
    print('.', end='', flush=True)
    iso = int(subprocess.check_output(f"exiftool -ISO -n -s -s -s {image_path}", shell=True))
    print('.', end='', flush=True)
    return 3.5e-5 * pow(iso, 2) + 2e-3 * iso + 0.3


def get_sharpness_metric(*params):
    """Estimate image sharpness"""
    jpg_filepath, sigma = params[0], params[1]

    img = cv2.imread(jpg_filepath)
    imggray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # denoise and blur image if there is too much noise
    if sigma > min_sigma:
        # img_to_work = cv2.GaussianBlur(imggray, (3, 3), 0)
        img_to_work_0 = cv2.fastNlMeansDenoising(imggray, 0.4 * sigma)
        # print(f"img type: {img.dtype}, imggray type: {imggray.dtype}, img_to_work_0 type: {img_to_work_0.dtype}")
        # img_to_work = cv2.GaussianBlur(cv2.fastNlMeansDenoising(imggray, 15), (sigma, sigma), 0)
        img_to_work = cv2.GaussianBlur(img_to_work_0, (3, 3), sigma)
        print('*', end='', flush=True)
    else:
        img_to_work = imggray

    # save blurred image for testing purposes
    # cv2.imwrite(jpg_filepath + "_.jpg", img_to_work)

    variance = cv2.Laplacian(img_to_work, cv2.CV_64F, ksize=9).var()
    # variance = cv2.Laplacian(cv2.cvtColor(cv2.imread(jpg_filepath), cv2.COLOR_BGR2GRAY), cv2.CV_64F, ksize=9).var()
    # numpy.max(cv2.convertScaleAbs(cv2.Laplacian(gray, 3)))

    with open("0_sharp_check.csv", "a") as f:
        f.write(jpg_filepath + ";" + str(variance) + "\n")
        # f.write(str(variance) + "\n")
    print('.', end='', flush=True)


def make_and_save_distribution_plot(in_data, in_median, in_mean, in_stdev):
    f, ax = plt.subplots(figsize=(12, 8))
    # f = plt.figure(figsize=(12, 8))
    plt.hist(in_data, bins=30)

    # add vertical lines
    plt.axvline(x=in_median, color='green', label='median')
    plt.axvline(x=in_mean, color='blue', label='median')
    plt.axvline(x=in_mean - 3 * in_stdev, color='blue', label='median')

    # get plot limits
    ymin, ymax = ax.get_ylim()
    xmin, xmax = ax.get_xlim()

    # labels for vertical lines
    plt.text(in_median + (xmax - xmin)/150, ymax * 0.9, 'median', color='green', rotation=90)
    plt.text(in_mean + (xmax - xmin)/150, ymax/40, 'mean', color='blue', rotation=90)
    plt.text((in_mean - 3 * in_stdev) + (xmax - xmin)/150, ymax / 40, 'mean - 3 stdev', color='blue', rotation=90)

    plt.title("sharpness distribution")
    plt.ylabel("Frequency")
    plt.xlabel("Laplacian sharpness estimation (arb. units)")
    f.tight_layout()
    plt.savefig('0_sharpness_distribution.png')


if __name__ == "__main__":
    if mp.cpu_count() > 2:
        nproc = round(mp.cpu_count() * 3 / 4)
    else:
        nproc = 2

    nproc = 2

    # remove auxiliary data file if exists
    fname_aux = "0_sharp_check.csv"
    if os.path.exists(fname_aux):
        os.remove(fname_aux)

    # process the command line arguments
    index_images = False
    save_distribution_plot = False
    fnames = []
    for arg in sys.argv[1:]:
        if arg[0] == '-':
            if arg[1:] == "index" or arg[1:] == "i":
                # add sharpness estimation as a prefix to each image
                # so it would be easier to find the sharpest one and blurred one
                index_images = True
            if arg[1:] == "plot-distribution" or arg[1:] == "pd":
                # remove less the least sharp images
                # so only the sharpest remain
                save_distribution_plot = True
            else:
                print(f"\n****Error: unknown option: {arg}!\n")
                print_usage()
        if os.path.exists(arg):
            # append image file to images list
            fnames.append(arg)

    nfiles = len(fnames)

    if nfiles == 0:
        print("\n****Error: no image is given as input!\n")
        print_usage()

    # img = cv2.imread(fnames[0])
    print(f"Checking {nfiles} images for sharpness..", end='', flush=True)
    first_image_sigma = sigma_estimate(fnames[0])

    pool = mp.Pool(processes=nproc)
    # pool.map(get_sharpness_metric, iter(fnames))
    pool.starmap(get_sharpness_metric, zip(fnames, repeat(first_image_sigma)))
    pool.close()
    pool.join()
    print('done', flush=True)

    # read results from data file
    res = []
    with open(fname_aux, "r") as f:
        lines = f.readlines()
        for line in lines:
            if len(line) > 0:
                res.append((line.strip().split(';')[0], float(line.strip().split(';')[1])))

    # sort results
    res_s = sorted(res, key=lambda kv: kv[1])

    # estimate statistical parameters of sharpness distribution
    # try to exclude outliers by popping the least shap values from list
    n_imgs_removed_from_stat_calc = 0
    while True:
        sh_list = [x[1] for x in res_s[n_imgs_removed_from_stat_calc:]]
        median = stat.median(sh_list)
        mean = stat.mean(sh_list)
        st_dev = stat.pstdev(sh_list)
        print(f"mean:  {mean}\nmedian:{median}\n{abs((median - mean) / mean)}\n\n")
        # escape cycle when mean - median difference is less than 1%
        if abs((median - mean) / mean) < 0.01:
            break
        else:
            # if mean - median difference is more than 5%:
            # decrease number of images in the list
            n_imgs_removed_from_stat_calc += 1

    if save_distribution_plot:
        make_and_save_distribution_plot([x[1] for x in res], median, mean, st_dev)

    for val in res_s:
        # add laplacian sharpness estimation as a prefix to the image
        # useful for testing purpouses
        # allow to rank images by sharpness
        if index_images:
            index_str = "{:06.0F}".format(round(100 * val[1]))
            os.system(f"mv {val[0]} {index_str + '_' + val[0]}")
        # add extension to the least sharp images
        if val[1] < mean - 3 * st_dev:
            print(' ', val[0], "is blurred")
            os.system(f"mv {val[0]} {val[0]}.not_sharp_enough")

    # cleanup
    os.remove(fname_aux)

#!/usr/bin/python3
#
# Version: 2023.09.08
# Author: Serhiy Kobyakov


from __future__ import print_function
import os
import subprocess
import sys
import glob
from itertools import repeat
import multiprocessing as mp
import cv2
import numpy as np
from math import sqrt
 
MAX_FEATURES = 10000
GOOD_MATCH_PERCENT = 0.25

def save_keypoints(keypoints, imgfname_query):
    """save keypoints to file"""
    with open(imgfname_query + '.keypoints', "w") as f:
        for point in keypoints:
            p = str(point.pt[0]) + "," + str(point.pt[1]) + "," + str(point.size) + "," + str(point.angle) + "," +\
                str(point.response) + "," + str(point.octave) + "," + str(point.class_id) + "\n"
            f.write(p)


def load_keypoints(imgfname_query):
    """load keypoints from file"""
    keypoints = []
    lines = [line.strip() for line in open(imgfname_query + '.keypoints', "r")]
    for line in lines:
        lst = line.split(',')
        if len(lst) == 7:
            kp = cv2.KeyPoint(x=float(lst[0]), y=float(lst[1]), size=float(lst[2]), angle=float(lst[3]),
                              response=float(lst[4]), octave=int(lst[5]), class_id=int(lst[6]))
            keypoints.append(kp)
    return keypoints


def save_descriptors(descriptors, imgfname_query):
    """save descriptors to file"""
    np.save(imgfname_query + '.descriptors', descriptors)


def load_descriptors(imgfname_query):
    """load descriptors from file"""
    return np.load(imgfname_query + '.descriptors.npy')


def alignImages2(*imgfiles):
    """warp image fname_query so it is aligned to fname_train"""

    # train image - reference
    # query image - the one which must be transformed
    fname_train, fname_query = imgfiles[0], imgfiles[1]
    logstr = f"Train img: {fname_train}\nQuery img: {fname_query}\n\n"

    # read images
    im_query = cv2.imread(fname_query, cv2.IMREAD_COLOR)
    im_train = cv2.imread(fname_train, cv2.IMREAD_COLOR)

    # Convert images to grayscale
    im_queryGray = cv2.cvtColor(im_query, cv2.COLOR_BGR2GRAY)
    im_trainGray = cv2.cvtColor(im_train, cv2.COLOR_BGR2GRAY)
    print('.', end='', flush=True)

    # prepare gray image for processing
    #
    # check the difference between gaussian blur and adaptive noise reduction
    # print(f"fname_train: {fname_train} ")
    logstr += "Train img exposure time: " + \
              subprocess.check_output(f"exiftool -ExposureTime -s -s -s {fname_train}", shell=True).decode('ascii') +\
              "\n"
    expo = float(subprocess.check_output(f"exiftool -ExposureTime -n -s -s -s {fname_train}", shell=True))
    # print(f"fname_train: {fname_train}   expo: {expo}")
    kern_size = round(87.5 * expo - 1.6)
    if kern_size % 2 == 0:
        kern_size += 1

    if kern_size >= 3:
        # print(f"kernel size:", kern_size)
        im_queryGray = cv2.blur(im_queryGray, (7, 7))

    print('.', end='', flush=True)

    # Detect AKAZE features and compute descriptors.
    detector = cv2.AKAZE_create()
    kp_query, dscr_query = detector.detectAndCompute(im_queryGray, None)
    save_keypoints(kp_query, fname_query)
    save_descriptors(dscr_query, fname_query)
    logstr += f"found {len(kp_query)} keypoints in query img\n"

    # save image with all points
    # for debug purposes
    impoints = cv2.drawKeypoints(im_queryGray, kp_query, 0, (0, 0, 255),
                                 flags=cv2.DRAW_MATCHES_FLAGS_NOT_DRAW_SINGLE_POINTS)
    cv2.imwrite(fname_query + "_keypoints.jpg", impoints)

    if os.path.isfile(fname_train + '.keypoints') and os.path.isfile(fname_train + '.descriptors.npy'):
        kp_train = load_keypoints(fname_train)
        dscr_train = load_descriptors(fname_train)
        logstr += f"load {len(kp_train)} keypoints for train img from file\n"
    else:
        if kern_size >= 3:
            im_trainGray = cv2.blur(im_trainGray, (7, 7))
        kp_train, dscr_train = detector.detectAndCompute(im_trainGray, None)
        # print(f"\ndscr_train type: {type(dscr_train)}   shape: {dscr_train.shape}   {dscr_train.dtype}\n")
        logstr += f"found {len(kp_train)} keypoints in train img\n"

        if os.path.isfile('mask.png'):
            img_map = cv2.imread('mask.png', cv2.IMREAD_COLOR)

            good_kp = []  # List of "good keypoint"
            good_dsk = []  # List of "good descriptors"

            for k, d in zip(kp_train, dscr_train):
                x, y = k.pt
                if img_map[round(y / 2), round(x / 2)][2] == 0:
                    good_kp.append(k)  # Append keypoint to a list of "good keypoint".
                    good_dsk.append(d)  # Append descriptor to a list of "good descriptors".

            kp_train, dscr_train = good_kp, np.asarray(good_dsk, dtype=np.uint8)
            logstr += f"{len(kp_train)} keypoints left after filter using mask\n"

        save_keypoints(kp_train, fname_train)
        save_descriptors(dscr_train, fname_train)

        # save image with all points
        # for debug purposes
        impoints = cv2.drawKeypoints(im_trainGray, kp_train, 0, (0, 0, 255),
                                     flags=cv2.DRAW_MATCHES_FLAGS_NOT_DRAW_SINGLE_POINTS)
        cv2.imwrite(fname_train + "_keypoints.jpg", impoints)
    print('.', end='', flush=True)

    # Match features
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    # matcher = cv2.BFMatcher(cv2.NORM_L1, crossCheck=False)
    all_matches = matcher.knnMatch(dscr_query, dscr_train, k=2)
    print('.', end='', flush=True)
    logstr += f"{len(all_matches)} matches has been found between images\n"

    # Refine keypoints 1
    good_matches_1, kp_1_query, kp_1_train = refine_keypoints_1(all_matches,
                                                                 im_query,
                                                                 kp_query,
                                                                 im_train,
                                                                 kp_train,
                                                                 fname_query,
                                                                 distance_k=0.9,
                                                                 drawkp=False)
    print('.', end='', flush=True)
    logstr += f"{len(good_matches_1)} matches left after first refinement\n"

    # Find homography
    query_pts = np.float32([kp_query[m.queryIdx].pt for m in good_matches_1]).reshape(-1, 1, 2)
    train_pts = np.float32([kp_train[m.trainIdx].pt for m in good_matches_1]).reshape(-1, 1, 2)
    h, mask = cv2.findHomography(query_pts, train_pts, cv2.RANSAC, 5.0)
    print('.', end='', flush=True)

    # Refine keypoints 2
    good_matches_2, kp_2_query, kp_2_train = refine_keypoints_2(im_query,
                                                                kp_1_query,
                                                                im_train,
                                                                kp_1_train,
                                                                fname_query,
                                                                h,
                                                                inlier_threshold=12.5,
                                                                drawkp=False)
    print('.', end='', flush=True)
    logstr += f"{len(good_matches_2)} matches left after second refinement\n"

    # Find homography
    query_pts2 = np.float32([kp_2_query[m.queryIdx].pt for m in good_matches_2]).reshape(-1, 1, 2)
    train_pts2 = np.float32([kp_2_train[m.trainIdx].pt for m in good_matches_2]).reshape(-1, 1, 2)
    h2, mask = cv2.findHomography(query_pts2, train_pts2, cv2.RANSAC, 5.0)
    print('.', end='', flush=True)


    # save homography for debug purposes
    # with open("matches_" + fname_query + "_homography.txt", "w") as f:
    #     f.write(str(h) + "\n")
    #     f.write(str(h2))

    # Use homography to warp the image
    height, width, channels = im_train.shape

    # export the image with alpha channel
    # im_queryReg = cv2.warpPerspective(cv2.imread(fname_query, cv2.IMREAD_UNCHANGED), h2, (width, height))
    # cv2.imwrite('al_' + fname_query + '.tif', im_queryReg)

    # print(f"\nkp_query: {type(kp_query)} of {len(kp_query)} items")
    # print(f"query_pts2: {type(query_pts2)} of {len(query_pts2)} items")
    # print(f"kp_train: {type(kp_train)} of {len(kp_train)} items")
    # print(f"train_pts2: {type(train_pts2)} of {len(train_pts2)} items")

    # Draw matches
    # imMatches = cv2.drawMatches(im_query, kp_query, im_train, kp_train, good_matches_2, None)
    imMatches = cv2.drawMatches(im_query, kp_2_query, im_train, kp_2_train, good_matches_2, None)
    cv2.imwrite(fname_query + "_matches.jpg", imMatches)

    # export the transformed image
    # im_queryReg = cv2.warpPerspective(im_query, h2, (width, height))
    im_queryReg = cv2.warpPerspective(cv2.imread(fname_query, cv2.IMREAD_UNCHANGED), h2, (width, height))
    cv2.imwrite('al_' + fname_query + '.tif', im_queryReg)

    print('.', end='', flush=True)
    with open(fname_query + "_log.txt", "w") as f:
        f.write(logstr)


def refine_keypoints_1(all_matches, im_query, kp_query, im_train, kp_train, fname_query, distance_k=0.9, drawkp=True):
    """refine keypoins based on their distance difference"""
    # Apply ratio test
    kp_1_query = []
    kp_1_train = []
    matches_for_draw = []
    good_matches_1 = []
    for m, n in all_matches:
        if m.distance < distance_k * n.distance:
            kp_1_query.append(kp_query[m.queryIdx])
            kp_1_train.append(kp_train[m.trainIdx])
            good_matches_1.append(m)
            if drawkp:
                matches_for_draw.append([m])

    # Draw matches
    if drawkp:
        imMatches = cv2.drawMatchesKnn(im_query, kp_query, im_train, kp_train, matches_for_draw, None)
        cv2.imwrite("matches_" + fname_query + "_1.jpg", imMatches)

    return good_matches_1, kp_1_query, kp_1_train


def refine_keypoints_2(im_query, kp_1_query, im_train, kp_1_train, fname_query, h, inlier_threshold=15.0, drawkp=True):
    """refine keypoints based on distance between them after wrapping the query points using homography"""
    # https://docs.opencv.org/3.4/db/d70/tutorial_akaze_matching.html
    kp_2_query = []
    kp_2_train = []
    good_matches_2 = []
    if drawkp:
        matches_for_draw2 = []
    for i, m in enumerate(kp_1_query):
        if kp_distance(m.pt, kp_1_train[i].pt, h) < inlier_threshold:
            good_matches_2.append(cv2.DMatch(len(kp_2_query), len(kp_2_train), 0))
            kp_2_query.append(kp_1_query[i])
            kp_2_train.append(kp_1_train[i])
            if drawkp:
                matches_for_draw2.append([cv2.DMatch(len(kp_2_query), len(kp_2_train), 0)])

    # Draw refined matches
    if drawkp:
        im_matches = cv2.drawMatchesKnn(im_query, kp_2_query, im_train, kp_2_train, matches_for_draw2, None)
        cv2.imwrite("matches_" + fname_query + "_2.jpg", im_matches)

    return good_matches_2, kp_2_query, kp_2_train


def kp_distance(pt_query, pt_train, h):
    col = np.ones((3, 1), dtype=np.float64)
    col[0:2, 0] = pt_query
    col = np.dot(h, col)
    col /= col[2, 0]
    # dist = sqrt(pow(col[0, 0] - pt_train[0], 2) + pow(col[1, 0] - pt_train[1], 2))
    return sqrt(pow(col[0, 0] - pt_train[0], 2) + pow(col[1, 0] - pt_train[1], 2))


if __name__ == '__main__':
    # if mp.cpu_count() > 2:
    #     nproc = round(mp.cpu_count() / 4)
    # else:
    #     nproc = 1

    # memory used:
    #
    # 16 Mp jpegs (tiffs x4= 64 Mp), nproc=8: 60 Gb
    # 30 Mp jpegs (tiffs x4= 120 Mp), nproc=4:
    nproc = 8


    # process the command line arguments
    fnames = []
    for arg in sys.argv[1:]:
        if os.path.exists(arg):
            # append image file to images list
            fnames.append(arg)

    fnames = sorted(fnames)
    # remove from the list aligned images if they may get into unintentionally
    fnames = [x for x in fnames if x.find("al_") < 0]

    fname_train = fnames.pop(0)
    # copy first image, so it may be averaged with the others
    os.popen('cp ' + fname_train + ' ' + 'al_000.tif')

    # log image size
    p = subprocess.Popen("exiftool -ImageSize al_000.tif > large_tiff_image_size.log", stdout=subprocess.PIPE, shell=True)

    print("Aligning images...", end='', flush=True)

    # start monitoring memory usage
    # cmd = "cat /proc/meminfo | grep 'MemAvailable' > stack_align_mem.log; while true; do cat /proc/meminfo | grep 'MemFree' >> stack_align_mem.log; echo; sleep 1; done"
    cmd = "cat /proc/meminfo | grep 'MemAvailable' > stack_align_mem.log; while true; do cat /proc/meminfo | grep 'MemFree' >> stack_align_mem.log; sleep 1; done"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    # align first image in queue so keypoints would be saved into file
    alignImages2(fname_train, fnames.pop(0))
    pool = mp.Pool(processes=nproc)
    pool.starmap(alignImages2, zip(repeat(fname_train), fnames))
    pool.close()
    pool.join()

    # stop monitoring memory usage
    p.terminate()

    os.popen('rm *.keypoints')
    os.popen('rm *.descriptors.npy')
    os.popen('rm *_log.txt')
    # os.popen('rm *matches.jpg')

    print('done', flush=True)

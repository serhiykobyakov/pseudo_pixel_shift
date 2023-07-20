# Superresolution
using your cell phone camera and free software

Some technical background is necessary to use this software. And also you'll need:
* smartphone with camera
* PC with Linux (or Windows if you can adapt the scripts for this system)
* Imagemagick, Python (along with OpenCV) installed

Superresolution is an image manipulation technique which allow to improve the image quality (increase resolution, decrease noise level) in comparison to the image camera produce. In general, there are two ways we can get a superresolution: use AI on single image or average a stack of multiple images. This project uses the latter approach.

Before we go into details, there are merits and demerits of the superresolution technique:

| Advantages | Disadvantages |
| ----------- | ----------- |
| More megapixels :) | Only static scenes (there may be pedestrians or moving cars as long as there are static objects in the frame) |
| More fine details compared to the camera native images | Requires extra efforts compared to point and shoot | 
| Less noise compared to the camera native images | |
| You are using your cell phone which is always with you ;) ||

## Motivation and project scope

My motivation is based on two desires:
* get better images using my cellphone camera. (it is irrational, I know, please don't question this aspect)
* do the above using what I already have with no additional investments in licenses and hardware

There is [well known article which describes how to get superresolution images](https://petapixel.com/2015/02/21/a-practical-guide-to-creating-superresolution-photos-with-photoshop/), but photoshop is a part of the process there. I want to use free software in this project, so my workflow will be a bit different.

On the highest level it is a two-step process:
* get a lot of images using smartphone
* process them using PC

Shooting jpegs would be the most convenient way of getting images out of camera since the camera can take care of white balace, exposition and even HDR processing of the output images. This means less postprocesing work later. Contemporary cameras are really great with this, so in postprocessing you'll need to make a really cosmetic actions. Yes, jpegs are 8-bit images and raws can deliver more bits, but shooting raw means more postprocessing later. There are pros and cons in both approaches, but let me focus on jpegs here.

It is important to take care of some settings on smartphone:
* switch noise reduction off (noise reduction smoothes out subtle details which we are interested in)
* switch image sharping off (sharping causes artifacts and we don't want it)
* set image quality to 100% (you'll get heavy images but we need as much quality as we can get)
* use native camera resolution for output images
* use fastest possible burst mode during shooting

## Installation

Install Python 3.\
Put scripts into filder which is in your PATH list.

## How it works

1. Get few tenth of images shooting the same scene.
Point your cellphone camera at the scene you want to capture while holding your camera in hands. Don't use tripod!.\ Hold your camera as still as it is possible.\
Capture as many images as it is possible.\ Use jpeg format to save images, use the best quality possible in settings.\ 50 images and avove is enough for single scene.\

2. Copy your images on your PC, separate each scene in individual folders so in each folder you have a stack of images (images of the same scene). Check for blurred images in folder using command:
```
stack_sharp_check.py *.jpg
```
The script will separate sharp images from a blurred ones by adding ".not_sharp_enough" to the latter.


## Results

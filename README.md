# Superresolution
using your cell phone camera and free software
---

Superresolution is an image manipulation technique which allow to improve the image quality (increase resolution, decrease noise level) in comparison to the image camera produce. In general, there are two ways we can get a superresolution: use AI on single image or average a stack of multiple images. This project uses the latter approach.

Some technical background is necessary to use this software. And also you'll need:
* smartphone with camera
* PC with Linux (or Windows if you can adapt the scripts for this OS)
* Imagemagick, Python (along with OpenCV) installed

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
* average them using PC

Shooting jpegs is be the most convenient way of getting images out of camera since the camera can take care of white balace, exposition and even HDR processing of the output images. Contemporary cameras are really great with this, so in postprocessing you'll need to make a subtle corrections. Yes, jpegs are 8-bit images and raws can deliver more bits, but using raw requires extra memory and CPU time in later postprocessing. There are pros and cons in both approaches, but let me focus on jpegs here.

## Camera settings and software installation

It is important to take care about some camera settings on smartphone:
* switch noise reduction off (noise reduction smoothes out subtle details which we are interested in)
* switch image sharping off (sharping causes artifacts and we don't want it)
* set image quality to 100% (you'll get heavy images but we need as much quality as we can get)
* use native camera resolution for output images
* use fastest possible burst mode during shooting

On your PC:
* install Python 3
* install hugin (we only need fulla and tca_correct available in command line)
* put scripts into filder which is in your PATH list so you can use them

## How it works

1. Get few tenth of images shooting the same scene.
Point your cellphone camera at the scene you want to capture while holding your camera in hands. Don't use tripod!. Hold your camera as still as it is possible. Capture as many images as it is possible. Use jpeg format to save images, use the best quality possible in settings. 50 images and above is enough for single scene.

2. Copy your images on your PC, separate each scene in individual folders so in each folder you have a stack of images (images of the same scene). Check for blurred images in folder using command:
   ```
   stack_sharp_check.py *.jpg
   ```
   The script will separate sharp images from a blurred ones by adding ".not_sharp_enough" to the latter.

3. Decide which image will be used to training (the first image to which all the rest will be corrected). The image must not cointain distracted objects ob the foreground such as pedestrians or cars passing on). If it is not the first image in the folder sorted by the filename - rename it so it will be the first when sorting files alphabetically.

4. You may also make a mask (mask.png) - transparent (with alpha channel on) png image where moving objects are masked using red color. IT can be easily done using gimp: open your first image in gimp, create new layer with alpha channel on top of the image and paint with red color on trees, cars and pedestrians - every objects which can chage their positions from image to image. Save only the upper transparent layer with mask as "mask.png" to the folder with images. Mask creation is optional, but if there are a lot of moving objects in your images - further alignment can be baffled by them and the resulting imege will not be as crisply sharp as it can be.

5. Upscale images 2x in size and save them into 16-bit tiffs:
   ```
   jpg2largetif.py *.jpg
   ```
6. Correct images for transverse chromatic aberration (TCA) if it is necessary:
   ```
   tca_corr.py -inplace *.tif
   ```


## Results



## Some final thoughts

#### Sharpness estimation (stack_sharp_check.py)
Laplacian variance of image is a good estimator of image sharpness. It works perfectly on clean images. Unfortunately, digital noise also affects the variance directly. The more noise - the larger the variance. At some point (large noise, high ISO values) noise contribution to the variance becomes larger than the sharpness of the image.

It is not a trivial task to distinguish which part of the laplacian variance is due to image sharpness and which is due to noise. For now I haven't find a reasonable solution to this problem.

To supress the noise contribution to the laplacian variance I use iso-calibrated noise reduction prior to the variance estimation. It doesn't eliminate the problem completely but it works surprisingly well, so I trust the script with separating blurred images from sharp ones.

The iso calibration is simply the sigma estimation which is used to denoise image. I made it empirically for my LG V30 camera's images, so if you have better camera - you may need to correct the sigma estimation routine.




# Supplement-to-nhess-2022-21
This repository contains supplementary codes for the paper "Using Sentinel-1 radar amplitude time series to constrain the timings of individual landslides: a step towards understanding the controls on monsoon-triggered landsliding" Burrows, K., Marc, O. and Remy, D. 2022. Natural Hazards and Earth Systems Sciences.
The scripts are as follows:

(a) Google earth engine script (Javascript) "Supplement-to-Burrows-NHESS-2022.js" This needs to be run for each co-event SAR image, producing a file containing the median amplitude, standard deviation, shadow pixel amplitude and bright pixel amplitude for every landslide.

(b) Python script  "gee-preprocess-1.py" to organise outputs from (a) into inputs for (c)

(c) Python script "get_landslide_dates_2.py" to identify landslide timings for each method and combine these to obtain an overall timing for each landslide

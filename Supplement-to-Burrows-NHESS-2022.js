//Script to obtain SAR amplitude statistics for pixels inside a landslide polygon, similar "background" pixels, "shadow" pixels and "bright" pixels
//Supplement to Burrows et al. 2022, NHESS Discussions
//This script should be run for each co-event image in your time period of interest as well as the last image acquired before this

//Path to the angular slope correction module from Vollrath et al. 2020. https://doi.org/10.3390/rs12111867
var slope_lib = require('path/to/module:slope_correction_module');
//Module available from https://github.com/ESA-PhiLab/radiometric-slope-correction
//This module needs to be modified as follows before it can be used with our script:
//Line 117 (Conversion to dB) .select(['VV','VH']) changed to .select(['VV'])
//This allows the module to work for Sentinel-1 images that are available only in single-pol mode - useful when looking at events occurring early in the lifetime of the satellite.
//Line 124 changed from: 
//to: return gamma0_flatDB.addBands(mask).copyProperties(image), gamma0_flat.select(['VV']).addBands(mask).copyProperties(image);
//This allows the script to return the pixel values before their conversion to decibels, which we need to calculate e.g. the mean

//Define area of interest
//This can either be drawn straight onto the map or defined as a polygon
var AOI=geometry

//Load landslide inventory (uploaded shp file)
//var landslides = ee.FeatureCollection('path/to/landslide_inventory');
//The 'tag' variable should be an attribute of the shp file which labels each landslide polygon in your inventory
//This needs to exist before you start - if your dataset does not have a suitable attribute, you need to add it in QGIS or using geopandas or similar
//The labels need to start with a letter not a number e.g. 'landslide234' not '234'
//every polygon needs to have a different label
var tag = 'object_id'
//plot landslides on map
Map.centerObject(AOI, 10);
Map.addLayer(landslides)

//Load Sentinel-1 imagery - only use VV polarisation
var polarisation='VV'
var imvv = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(AOI)
//Filter by date - needs to include images before and after your time period of interest
    .filterDate('YYYY-MM-DD','YYYY-MM-DD')
//It is easiest to check which orbits cover your area of interest beforehand and then specify
//One way to do this is to comment out this line and check the properties of the images returned by GEE 
//Each orbit needs to be processed separately. There should be at least one ascending and one descending available.
    .filter(ee.Filter.eq('relativeOrbitNumber_start',83))
    .filter(ee.Filter.and(
      ee.Filter.listContains('transmitterReceiverPolarisation', polarisation),
      ee.Filter.eq('instrumentMode', 'IW')
    ))//.map(function(image){return image.clip(AOI)});

//Filter SAR images to obtain the result before, during and after the rainfall event    
var pre_event = imvv.filterDate('YYYY-MM-DD', 'YYYY-MM-DD').select(polarisation,'angle')
print('Number of pre-event Sentinel-1 images', pre_event.size());
var post_event = imvv.filter(ee.Filter.date('YYYY-MM-DD','YYYY-MM-DD')).select(polarisation,'angle')//,'2017-03-31')
print('Number of post-event Sentinel-1 images', post_event.size());
var co_event = imvv.filter(ee.Filter.date('YYYY-MM-DD','YYYY-MM-DD')).select(polarisation,'angle')
print('Number of co-event Sentinel-1 images', co_event.size());
print(co_event)
print(pre_event)
print(post_event)
var date = '20180610'//This is just a label for the file name

//If you are looking early in the lifetime of the satellite (i.e. 2014-2015) and you have landslides that lie near the edges of SAR scenes, it is worth checking that the images look normal.
//If there are any that look suspicious, these can be removed from the pre-event or post-event time series using the following command:
//var bad_date_filter=ee.Filter.date('YYYY-MM-DD','YYYY-MM-DD')
//var pre_event=pre_event.filter(bad_date_filter.not())

//Apply radiometric calibration from Vollrath (2020) to pre-event and post-event time series
var pre_event, pre_event_power = slope_lib.slope_correction(
    pre_event);
var post_event, post_event_power = slope_lib.slope_correction(
    post_event);

//Calculate mean A and mean dA of pre-event images (RapidSAR method)
//All of these calculations use amplitude without decibel scaling
//mean A
var pre_event_amp_power = pre_event_power.mean()
//var pre_event_std = pre_event_power.reduce({reducer: ee.Reducer.stdDev()});
//Delta A
var subtracted = pre_event_power.map(function (image) {
    return image.subtract(pre_event_amp_power)
})
var pre_event_ampdiff = ee.Image(subtracted.mean());

//For shadow, subtract pre_event from post_event (shadows should have -4.5dB drop)
var pre_event_amp = pre_event.median()
var post_event_amp = post_event.median()
var pp_diff = ee.Image(post_event_amp.subtract(pre_event_amp))
//plot these on the map to have a look
Map.addLayer(pp_diff,{min:-10,max:10},'pp_diff')
Map.addLayer(pre_event_amp,{min:-15,max:0},'pre-event')

print('co-event image')
//apply radiometric calibration to co-event image
var co_event, co_event_power = slope_lib.slope_correction(co_event);
//create image 1 - a mosaic of the co-event images covering your AOI
var image1=ee.Image(co_event.mosaic())
print(image1)
print(co_event_power)
var image1_power=ee.Image(co_event_power.mosaic())
print(image1_power)
//Plot this on the map to have a look
Map.addLayer(image1,{min:-15,max:0},'co-event')

//Load Sentinel-2 imagery for NDVI mask
//Define a time period of pre-event Sentinel-2 images
var s2imagespre = ee.ImageCollection('COPERNICUS/S2').filter(ee.Filter.date('2017-01-01','2017-12-31'))
var addNDVI = function(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('nd');
  return image.addBands(ndvi);
};
var withNDVI = s2imagespre.map(addNDVI);
// Make a "greenest" pixel composite.
var imagepre_ndvi = withNDVI.qualityMosaic('nd').select('nd')

//Alternatively load Landsat data for events prior to Sentinel-2 launch (late June 2015)
//e.g. using 2014 Annual greenest pixel composite from Landsat-8 (suitable for landslides in 2015))
//var landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_ANNUAL_GREENEST_TOA')
//                  .filterDate('2014-01-01', '2014-12-31')
//var imagepre=landsat.first()
//var imagepre_ndvi=imagepre.normalizedDifference(['B5','B4']);

//add to map
var visParams_ndvi = {min: -1, max: 1, palette: ['blue', 'white', 'green']};
Map.addLayer(imagepre_ndvi,visParams_ndvi,'Pre-event NDVI')

//Obtain shadow pixels
var shadowmask4p5 = pp_diff.lt(-4.5)
var image1_sh_masked4p5 = ee.Image(image1.mask(shadowmask4p5))
print(image1_sh_masked4p5)
//Obtain bright pixels
var brightmask5 = pp_diff.gt(5.0)
var image1_br_masked5 = ee.Image(image1.mask(brightmask5))
print(image1_br_masked5)

//generate a mask made up of the landslide polygons
var maskls = ee.Image.constant(1).clip(landslides.geometry()).mask().not()
//Define a function to calculate the landslide, background and shadow values for each landslide polygon
var LBS = function(landslide){
  //Define a buffer region around each landslide - The background area is between 30 and 500 m from the polygon
  var lsbuffered = landslide.buffer({distance: 500});
  var ls_buffered_closeish = landslide.buffer({distance:30});
  var lsbuffered_close = landslide.buffer({distance:20});
  var lsbuffer = lsbuffered.difference(ls_buffered_closeish);
  //use percentiles to mask dissimilar pixels and landslide polygons from the buffer region
  var u_lim = ee.Number(pre_event_amp_power.reduceRegion({geometry:landslide.geometry(),reducer: ee.Reducer.percentile([95.0]),scale:10}).get(polarisation))
  var l_lim = ee.Number(pre_event_amp_power.reduceRegion({geometry:landslide.geometry(), reducer: ee.Reducer.percentile([5.0]),scale: 10}).get(polarisation))
  var u_lim_d = ee.Number(pre_event_ampdiff.reduceRegion({geometry:landslide.geometry(),reducer: ee.Reducer.percentile([95.0]),scale:10}).get(polarisation))
  var l_lim_d = ee.Number(pre_event_ampdiff.reduceRegion({geometry:landslide.geometry(),reducer: ee.Reducer.percentile([5.0]),scale: 10}).get(polarisation))
  var ulim_ndvi = ee.Number(imagepre_ndvi.reduceRegion({reducer: ee.Reducer.percentile([95.0]),geometry: landslide.geometry(),scale: 10}).get('nd'));
  var llim_ndvi = ee.Number(imagepre_ndvi.reduceRegion({reducer: ee.Reducer.percentile([5.0]),geometry: landslide.geometry(), scale: 10}).get('nd'));
  //generate masks based on these percentiles
  var mask3 = ee.Image(pre_event_ampdiff).lt(u_lim_d);
  var mask4 = ee.Image(pre_event_ampdiff).gt(l_lim_d);
  var mask1 = ee.Image(pre_event_amp_power).lt(u_lim);
  var mask2 = ee.Image(pre_event_amp_power).gt(l_lim);
  var mask1ndvi = imagepre_ndvi.lt(ulim_ndvi);
  var mask2ndvi = imagepre_ndvi.gt(llim_ndvi);
  //apply masks to image1: the co-event mosaic to identify the background pixels for each landslide
  var image1_masked = image1.updateMask(mask1).updateMask(mask2).updateMask(mask3).updateMask(mask4).updateMask(mask1ndvi).updateMask(mask2ndvi).updateMask(maskls);
  var median_lsbuffer = ee.Number(image1_masked.reduceRegion({geometry:lsbuffer.geometry(), reducer: ee.Reducer.median(), scale: 10}).get(polarisation))
  var median_ls = ee.Number(image1.reduceRegion({geometry:landslide.geometry(),reducer: ee.Reducer.median(),scale:10}).get(polarisation))
  var std_ls = ee.Number(image1.reduceRegion({geometry:landslide.geometry(),reducer: ee.Reducer.stdDev(),scale:10}).get(polarisation))
  var median_ls_20 = ee.Number(image1.reduceRegion({geometry:lsbuffered_close.geometry(),reducer: ee.Reducer.median(),scale:10}).get(polarisation))
  var std_ls_20 = ee.Number(image1.reduceRegion({geometry:lsbuffered_close.geometry(),reducer: ee.Reducer.stdDev(), scale: 10}).get(polarisation))
  var median_shadow4p5 = ee.Number(image1_sh_masked4p5.reduceRegion({geometry:lsbuffered_close.geometry(), reducer: ee.Reducer.median(),scale:10}).get(polarisation))
  var median_br5 = ee.Number(image1_br_masked5.reduceRegion({geometry:lsbuffered_close.geometry(), reducer: ee.Reducer.median(), scale:10}).get(polarisation))
//record the number of unmasked pixels in the landslide
  var ls_count = ee.Number(image1_masked.reduceRegion({geometry:lsbuffered_close.geometry(),reducer:ee.Reducer.count(),scale:10}).get(polarisation))
//record the number of unmasked pixels in the shadow zone
  var shadow_count4p5 = ee.Number(image1_sh_masked4p5.reduceRegion({geometry:lsbuffered_close.geometry(), reducer: ee.Reducer.count(),scale:10}).get(polarisation))
  var br_count5 = ee.Number(image1_br_masked5.reduceRegion({geometry:lsbuffered_close.geometry(), reducer: ee.Reducer.count(),scale:10}).get(polarisation))
//Set the date here to be the co-event date you're generating the information for - in this case 10th July 2018
//Each metric will be assigned to each landslide polygon.
  return landslide.select([tag]).set({'20180610ls': median_ls}).set({'20180610ls_20':median_ls_20}).set({'20180610b': median_lsbuffer}).set({'20180610std':std_ls}).set({'20180610std_20':std_ls_20}).set({'20180610sh4p5':median_shadow4p5}).set({'20180610br5':median_br5}).set({'lscount':ls_count}).set({'shadowcount4p5':shadow_count4p5}).set({'brcount':br_count5})
}

//Need to filter out landslides which do not contain any unmasked pixels
//Define a counter function to check how many unmasked pixels lie in each landslide polygon
var counter = function(landslide){
  var count_this=image1.reduceRegion({geometry:landslide.geometry(),reducer:ee.Reducer.count(),scale:10}).get(polarisation)
  return landslide.select([tag]).set({'counts_unmasked':count_this})
}
//map counter function over all landslides
var ls_count = landslides.map(counter)
//filter to remove landslides that contain less than 10 unmasked SAR pixels
var ls_filt=ls_count.filterMetadata('counts_unmasked','greater_than',9)

//second filter to remove (rare and on very edge of scenes) landslides that are not covered by the pre-event images
//Seems to not be needed unless images acquired in 2014 / early 2015 are used.
//var counter_pre = function(landslide){
//  var count_this=pre_event_amp.reduceRegion({geometry:landslide.geometry(),reducer:ee.Reducer.count(),scale:10}).get(polarisation)
//  return landslide.select([tag]).set({'counts_unmasked_pre':count_this})
//}
//var ls_filt_count=ls_filt.map(counter_pre)
//var ls_filt = ls_filt_count.filterMetadata('counts_unmasked_pre','greater_than',5)

//Map LBS function over filtered landslides
var lsLBS = ls_filt.map(LBS);

//advise to include the co-event image date and the orbit number in your filename
var filename='chosen-filename.csv'
//Export data in csv format to a directory in your google drive
Export.table.toDrive({
  collection: lsLBS, 
    description: filename, 
  fileFormat: 'CSV',
  folder: 'directory'
});

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 15:34:20 2018

@author: mcdeid
"""

import arcpy
import os
import datetime
import re

def matchHUC(string, HUCval=12):
    """Return the first 12digit value within a string"""
    match = re.search(r'\D(\d{' + str(HUCval) + '})(?!\d)', string)
    return match.group(1)

def clipdemsbyhuc(dems_to_clip, huc12shppath, hucfield='HUC_12', saveoutput_inplace=False,
                  ext='.tif', postscript='_clp'):
    """Use matchHUC() to determine current HUC and make selection. This will
    save the output to the current arcpy workspace unless you set
    saveoutput_inplace to True.
    
    Parameters:
        dems_to_clip : list
            List of paths to the rasters to be clipped. If saveoutput_inplace
            is set to True, then this list MUST include the FULL PATH fo the
            rasters.
        huc12shppath : str
            Path to polygon feature that contains HUC12 polygons.
        saveoutput_inplace : bool
            False: Saves output to current arcpy workspace
            True: Saves output at the location of the source raster"""
    start = datetime.datetime.now()
    clippeddems = []
    huc_lyr = arcpy.MakeFeatureLayer_management(huc12shppath, 'lyr')
    orig_workspace = arcpy.env.workspace
    ttl = len(dems_to_clip)
    with open('cliplog.txt','w') as log:
        for i, f in enumerate(dems_to_clip):
            log.write('Processing: {}\n'.format(str(f)))
            head, tail = os.path.split(f)
            if saveoutput_inplace == False:
                filename, old_ext = os.path.splitext(tail)
            if saveoutput_inplace == True:
                arcpy.env.workspace = head
    #        huc = huclist[i]
            huc = matchHUC(head)
            sql = '"' + hucfield + '" = \'' + str(huc) + '\''
#            log.write(sql)
            arcpy.SelectLayerByAttribute_management('lyr',"NEW_SELECTION",sql)
            if arcpy.Describe('lyr'): #test for selection
                if saveoutput_inplace == True:
                    clippeddem = arcpy.Clip_management(f, '#', os.path.join(tail, filename) + postscript + ext,
                                                       huc_lyr, '#', 'ClippingGeometry')
                else:
                    clippeddem = arcpy.Clip_management(f, '#', filename + postscript + ext,
                                                       huc_lyr, '#', 'ClippingGeometry')
                clippeddems.append(str(clippeddem)) #append path of result
            completed = i+1
            remaining = ttl-completed
            elapsed = datetime.datetime.now()-start
            average = elapsed/completed
            timeremaining = average*remaining
            log.write('{} files remaining. Est. time to completion: {}\n'.format(str(remaining),str(timeremaining)))
        arcpy.Delete_management('lyr')
        arcpy.env.workspace = orig_workspace
        return clippeddems
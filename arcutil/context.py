# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 10:57:51 2018

@author: mcdeid

Credit: These functions were put together by Nick Santos 
(https://github.com/nickrsan) after some community discussion in The Spatial
Community (http://thespatialcommunity.org/).

Description: Arcpy context managers for temporarily checking out an extension, changing the 
overwrite state, and setting the arcpy workspace environment.
"""

import arcpy
from contextlib import contextmanager

@contextmanager
def extension(name):
    """ Safely use ArcGIS extensions """
    if arcpy.CheckExtension(name) == u"Available":
        status = arcpy.CheckOutExtension(name)
        yield status
    else:
        raise RuntimeError("%s license isn't available" % name)
    arcpy.CheckInExtension(name)

@contextmanager
def overwritestate(state):
    """ Temporarily set the ``overwriteOutput`` env variable. """
    orig_state = arcpy.env.overwriteOutput
    arcpy.env.overwriteOutput = bool(state)
    yield state
    arcpy.env.overwriteOutput = orig_state

@contextmanager
def workspace(path):
    """ Temporarily set the ``workspace`` env variable. """
    orig_workspace = arcpy.env.workspace
    arcpy.env.workspace = path
    yield path
    arcpy.env.workspace = orig_workspace

@contextmanager
def deconflict_scratchworkspace():
    """ Check if scratchWorkspace is same as workspace, if it is, set
    scratchWorkspace to scratchFolder location temporarily"""
    orig_scratch = arcpy.env.scratchWorkspace
    if orig_scratch == arcpy.env.workspace:
        arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
    yield arcpy.env.scratchWorkspace
    arcpy.env.scratchWorkspace = orig_scratch
    
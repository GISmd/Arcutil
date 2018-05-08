# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 13:03:31 2017

@author: mcdeid
"""
import arcpy
import os

def addrastertomxd(mxdpath, rasterlist):
    """Adds all the files in a list to the specified mxd.
    
    http://gis.stackexchange.com/questions/12464/adding-raster-layer-without-lyr-file-using-arcpy"""
    mxd = arcpy.mapping.MapDocument(mxdpath)
    dataframe = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    for i, f in enumerate(rasterlist):
        print i
        result = arcpy.MakeRasterLayer_management(f, f + '_lyr')
        lyr = result.getOutput(0)
        arcpy.mapping.AddLayer(dataframe, lyr, 'AUTO_ARRANGE')
    mxd.save()
    del mxd

def get_unique_values(layer, column_name):
    """Returns a list of the unique values of a given field
    
    Ref: https://gis.stackexchange.com/questions/208430/trying-to-extract-a-list-of-unique-values-from-a-field-using-python"""
    with arcpy.da.SearchCursor(layer, [column_name]) as cursor:
        return sorted({row[0] for row in cursor})

def validateFeatureClasses(fcs):
    """Take a list of feature classes (fcs), return False and the list of fcs
    that failed if failed. Otherwise return True and an empty list."""
    invalid = []
    validity = True
    for fc in fcs:
        if not arcpy.Exists(fc):
            invalid.append(fc)
            validity = False
    return validity, invalid

def collectMatchingFeatures(output_dir, output_gdb_name, input_fcs, field, vals, sr=''):
    """Given an output geodatabase or folder, a list of feature classes, a target 
    fieldname, and a target value, itereate through feature classes, select
    all features within each feature class that matches the target value within
    the target field, and place all matching features into a feature dataset 
    named after the current value. 
    
    Issue:
        Losing spatial reference...
    
    Params:
        output_dir : str
            String representation of the target output directory
        output_gdb_name : str
            String representation of the desired output file geodatabase name,
            with or without the file extension
        input_fcs : list
            List of string representations of valid feature classes
        field : string
            String representation of the desired field for matching values
        vals : list
            List of strings you want to match, must be strings
        sr : str
            See arcpy.CreateFeatureDataset_management docstring for what is 
            allowed. If no spatial_reference is provided, then the 
            spatial_reference of the first feature class will be assumed"""
    validresult, invalids = validateFeatureClasses(input_fcs)
    if validresult:
        if not output_gdb_name[-3:] == 'gdb':
            output_gdb_name += '.gdb'
        arcpy.CreateFileGDB_management(output_dir, output_gdb_name)
        lyrs = []
        for fc in input_fcs:
            lyrs.append(arcpy.MakeFeatureLayer_management(fc,os.path.split(fc)[1]+'_lyr'))
        if not sr:
            sr = arcpy.Describe(lyrs[0]).spatialReference
        with open('log.txt', 'w') as log:
            for val in vals:
                print('{}'.format(val))
                log.write('{}\n'.format(val))
                where = '"{}" = \'{}\''.format(field,val)
                log.write(where + '\n')
                fd = arcpy.CreateFeatureDataset_management(os.path.join(output_dir,output_gdb_name),
                                                           val,sr)
                for lyr in lyrs:
                    fc_out = os.path.join(fd[0],os.path.split(str(lyr))[1][:-4]+'_'+val)
                    log.write(fc_out + '\n')
                    try:    
                        arcpy.SelectLayerByAttribute_management(lyr,'NEW_SELECTION',where)
                        arcpy.CopyFeatures_management(lyr,fc_out)
                    except:
                        log.write('arcpy.Select_analysis failed on {}\n'.format(lyr))
                        continue
                    arcpy.SelectLayerByAttribute_management(lyr,'CLEAR_SELECTION')
    else:
        print('Oops! The following feature classes may not exists.:')
        for x in invalids:
            print('x')

def add_mapping(field_name, mapping_existing, mapping_new):
    """Adds field_name to mapping. A helper function for
    reorder_fields_by_fieldname and reorder_fields_by_index
    
    Modified from: 
        http://joshwerts.com/blog/2014/04/17/arcpy-reorder-fields/"""
    mapping_index = mapping_existing.findFieldMapIndex(field_name)
    # required fields (OBJECTID, etc) will not be in existing mappings
    # they are added automatically
    if mapping_index != -1:
        field_map = mapping_existing.fieldMappings[mapping_index]
        mapping_new.addFieldMap(field_map)
#    return mapping_new

def reorder_fields_by_fieldname(table, out_table, field_order, add_missing=True):
    """Source: http://joshwerts.com/blog/2014/04/17/arcpy-reorder-fields/

    Reorders fields in input featureclass/table:
        - table: input table (fc, table, layer, etc)
        - out_table : output table (fc, table, layer, etc)
        - field_order:   order of fields (objectid, shape not necessary)
        - add_missing:   add missing fields to end if True (leave out if False)
        - -> path to output table"""
    fields_existing = arcpy.ListFields(table)
    field_names_existing = [field.name for field in fields_existing]
    mapping_existing = arcpy.FieldMappings()
    mapping_existing.addTable(table)
    mapping_new = arcpy.FieldMappings()
    # add user fields from field_order
    for field_name in field_order:
        if field_name not in field_names_existing:
            raise Exception("Field: {0} not in {1}".format(field_name, table))
        add_mapping(field_name, mapping_existing, mapping_new)
    # add missing fields at end
    if add_missing:
        fields_missing = [f for f in field_names_existing if f not in field_order]
        for field_name in fields_missing:
            add_mapping(field_name, mapping_existing, mapping_new)
    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(table, out_table, mapping_new)
    return out_table

def reorder_fields_by_index(table, out_table, field_order, add_missing=True):
    """A modification Josh Werts' reorder function 
    (http://joshwerts.com/blog/2014/04/17/arcpy-reorder-fields/)
    
    Params:
        table : feature class, table, layer, etc...
            The input table
        out_table : feature class, table, layer, etc...
            The output table
        field_order : list of integers
            List containing the indexes of the fields in the order that you desire
        add_missing : bool
            Will append any fields missing from field_order to the end of the
            out_table if True. If False, do not append the missing fields"""
    fields_existing = arcpy.ListFields(table)
    field_names_existing = [field.name for field in fields_existing]
#    field_names_new = []
#    for i in field_order:
#        field_names_new.append(field_names_existing[i])
    field_names_new = [field_names_existing[i] for i in field_order]
    mapping_existing = arcpy.FieldMappings()
    mapping_existing.addTable(table)
    mapping_new = arcpy.FieldMappings()
    for field_name in field_names_new:
        if field_name not in field_names_existing:
            raise Exception("Field: {0} not in {1}".format(field_name, table))
        add_mapping(field_name, mapping_existing, mapping_new)
    # add missing fields at end
    if add_missing:
        fields_missing = [f for f in field_names_existing if f not in field_order]
        for field_name in fields_missing:
            add_mapping(field_name, mapping_existing, mapping_new)
    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(table, out_table, mapping_new)
#    return out_table, field_names_new, field_names_existing, mapping_new

def update_mosaic_statistics(mosaic_dataset):
    arcpy.management.CalculateStatistics(mosaic_dataset)
    arcpy.management.BuildPyramidsandStatistics(mosaic_dataset, 'INCLUDE_SUBDIRECTORIES', 'BUILD_PYRAMIDS', 'CALCULATE_STATISTICS')
    arcpy.RefreshCatalog(mosaic_dataset)
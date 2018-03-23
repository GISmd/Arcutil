# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 09:28:06 2016

@author: mcdeid

This module is a collection of useful utilities that I've put together from
various sources (mostly stackoverflow). This module specifically avoids use
of the arcpy library. May consider creating a arcpyutilities module for arcpy
related vague functions.
"""

import os
import collections
import sys
import subprocess
import math
import win32clipboard
import datetime
import Tkinter
import tkFileDialog
import re
#import tkSimpleDialog

'''http://gis.stackexchange.com/questions/158753/managing-environment-variables-in-arcpy/158754#158754'''

def addtoclipboard(text):
    """Input needs to be string."""
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()

def startdatetime():
    """Returns a string in format YYYYMMDD_HHMM"""
    start = datetime.datetime.now()
    startdatetime = start.strftime("%Y%m%d") + "_" + start.strftime("%H%M")
    return(startdatetime)

def find_file_by_type(file_extension, directory=''):
    """Searches recursively within the given directory for all files with the 
    given file extension and returns a list of their filepaths.
    
    To do:
        - Some stuff
        - Probably some other stuff too
        - Oh yeah, I remember now. Wait no... uhh
        - """
    if not file_extension[0] == '.':
        file_extension = '.' + file_extension
    if directory == '':
        root = Tkinter.Tk()
        directory = tkFileDialog.askdirectory(parent = root, initialdir = "/", title = 'Please Select a Directory')
        root.withdraw()
        os.chdir(directory)
    targetfiles = []
    for root, dirs, filenames in os.walk(directory):
        for name in filenames:
            if os.path.splitext(name)[1] == file_extension:
                targetfiles.append(os.path.join(root,name))
    if len(targetfiles) > 0:
        print('{} {} files found'.format(str(len(targetfiles)),file_extension))
        return targetfiles
    else:
        print('No {} file found'.format(file_extension))
        return targetfiles

def matchHUC(string, HUCval=12):
    """Return the first 12digit value within a string"""
    match = re.search(r'\D(\d{' + str(HUCval) + '})(?!\d)', string)
    return match.group(1)

def str_iterable_to_SQLstr(iterable, field, copy_to_clipboard=True):
    """Take an iterable of strings, like a set or list, convert it to a formatted
    SQL OR selected string intended for ArcMap selection. The result will select
    all the records that contain a match.
    
    Param:
        iterable : list or set
            This is the iterable containing the values that you want to select
            for
        field : str
            String name for the field that you want to select in.
        copy_to_clipboard : bool
            If false, will input the SQL string into the clipboard
    Returns:
        sql : str
            Formatted string that can be 
            
    Example: "DEP_ID" = '07020009_10002' OR
            
    To do:
        - [x] Allow selection by strings, integer, and doubles.
    """
    if all(isinstance(x, str) for x in iterable):
        string = "' OR \"{}\" = \'"
        front = "\"{}\" = '"
        end = "'"
    elif all(isinstance(x, (int, float, int)) for x in iterable):
        string = " OR \"{}\" = "
        iterable = [str(x) for x in iterable]
        front = "\"{}\" = "
        end = ''
    else:
        raise TypeError("elements in iterable must be either all strings or all numbers (int, float, long)")
    sql = string.format(field).join(iterable)
    sql = front.format(field) + sql + end
    if copy_to_clipboard==True:
        addtoclipboard(sql)
        return sql
    else:
        return sql

def csvs_to_listoflists(csv_list):
    """Take a list of CSVs, and read them into a list of lists. Ideally, all of
    the CSVs would have the same format, but technically this would work if they
    did not."""
    txt = ''
    for csv in csv_list:
        with open(csv, 'r') as myfile:
            myfile.readline()
            txt += myfile.read()
    list_of_lists = [x.split(',')[1:] for x in txt.split('\n')[:-1]]
    return list_of_lists, txt

def splitcsv(fname, outname, id_field=4, maximum_rows=1e6, header_exists=True):
    """UNFINISHED: Takes an input csv, splits into csvs of maximum rows without splitting
    up an id_field.
    """
    with open(fname, 'r') as myfile:
        if header_exists == True:
            header = myfile.readline()
        else:
            header = None
        lines = myfile.readlines()
    for x in range(0, int(math.ceil(len(lines)/1.0e6))):
        None
    return lines

def append_filename(csv, csv_file, merged_file):
    'Helper function for merge_csvs()'
    fulltext = csv_file.read()
    lines = fulltext.split('\n')[:-1]
    fixed_lines = [os.path.splitext(os.path.basename(csv))[0] + ',' + x for x in lines]
    newtext = '\n'.join(fixed_lines) + '\n'
    merged_file.write(newtext)

def merge_csvs(csv_list, output_name, include_inputname_as_column=False, min_rows=3):
    """Takes a list of CSVs, grabs the first line of the first CSV for the header
    of the merged CSV and then appends all additional CSVs to a new one.
    
    NOTE: Assumes CSVs are identical in format.
    
    Parameters:
        csv_list : list
            It's a list, of csvs.
        output_name : str
            Not just a name, a path. Yup, you heard it here first.
        include_inputname_as_column : bool
            Set to True if you want to include the source filename in the first
            column of the output.
        min_rows : int
            Minimum number of rows for a given file to be invluded in the merged output.
    
    """
    progress = 'Merging {} out of {}: {}'
    l = len(csv_list)
    # Modify csv list and remove ones that don't meet requirement
    pruned_csvs = []
    for csv in csv_list:
        with open(csv, 'r') as f:
            if len(f.read().split('\n')) >= min_rows:
                pruned_csvs.append(csv)
            else:
                print("{} didn't meet minimum number of rows ({})".format(csv, str(min_rows)))
    with open(output_name, 'w') as merged_file:
        if include_inputname_as_column==False:
            for i, csv in enumerate(pruned_csvs):
                with open(csv,'r') as csv_file:
                    print(progress.format(str(i + 1),l, csv))
                    if i == 0: # Include first line
#                        with open(csv, 'r') as csv_file:
                        merged_file.write(csv_file.read())
                    else:
#                        with open(csv, 'r') as csv_file:
                        csv_file.readline()
                        merged_file.write(csv_file.read())
        else:
            for i, csv in enumerate(pruned_csvs):
                print(progress.format(str(i + 1),l, csv))
                with open(csv, 'r') as csv_file:
                    if i == 0: # Include first line for the first file
                        merged_file.write('filename,' + csv_file.readline())
                        append_filename(csv, csv_file, merged_file)
                    else:
                        csv_file.readline()
                        append_filename(csv, csv_file, merged_file)
    print('merge_csvs() completed successfully. Output: {}'.format(output_name))

def findmissing(expectedlist, foundlist):
    """Compare two lists and output lists of items that are not included
    
    Parameters:
        expectedlist, foundlist
    
    Returns:
        not_in_expected : list
            list of items not in expectedlist
        not_in_found : list
            list of items not in foundlist"""
    expected = collections.Counter(expectedlist)
    found = collections.Counter(foundlist)
    #found_not_in_expected = 
    not_in_found = list((found - expected).elements())
    not_in_expected = list((expected - found).elements())
    return not_in_expected, not_in_found

def return_chopped_list(inputlist, left_index=0, right_index=64):
    """Input a list of strings and return a new list of strings that have
    been sliced by the left and right index values (int).
    """
    newlist = []
    for item in inputlist:
        newlist.append(item[left_index:right_index])
    return newlist
    
def openfolder(path):
    if sys.platform == 'darwin':
        subprocess.check_call(['open', '--', path])
    elif sys.platform == 'linux2':
        subprocess.check_call(['xdg-open', '--', path])
    elif sys.platform == 'win32':
        subprocess.check_call(['explorer', path])
    else:
        print('Failed to identify operating system')

def showFolderTree(path,show_files=False,indentation=2,file_output=False):
    """
    Shows the content of a folder in a tree structure.
    path -(string)- path of the root folder we want to show.
    show_files -(boolean)-  Whether or not we want to see files listed.
                            Defaults to False.
    indentation -(int)- Indentation we want to use, defaults to 2.   
    file_output -(string)-  Path (including the name) of the file where we want
                            to save the tree.
    """
    
    tree = []
    
    if not show_files:
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = ' '*indentation*(level)
            tree.append('{}{}/'.format(indent,os.path.basename(root)))
    
    if show_files:
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = ' '*indentation*(level)
            tree.append('{}{}/'.format(indent,os.path.basename(root)))    
            for f in files:
                subindent=' ' * indentation * (level+1)
                tree.append('{}{}'.format(subindent,f))
    
    if file_output:
        output_file = open(file_output,'w')
        for line in tree:
            output_file.write(line)
    else:
        # Default behaviour: print on screen.
        for line in tree:
            print(line)

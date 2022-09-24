"""
This python file is used to create maps scenario files from the AAA maps database
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyproj import *
from math import *
geodesic = Geod(ellps='WGS84')


"""
Settings
"""


# name of final export if manually selecting
scenariofilename = 'app'

# set all maps on or off  in processing
loadallmaps = 0 # 1 for yes 0 for no

#radial resolution of lines that form circle
#bluesky uses 5 deg natively but LVNL uses 10 deg
#cache issues in Bluesky may arise if resolution is set too fine
circleresolution = 10 #deg

dwarslijn_lengte = 1

#set location of map and points file
pointsfile = 'pnts_v7310.txt'
mapfile = 'maps_v7310.txt'


"""
Static functions
"""


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a)) * 0.539956803


def great_circle(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    return 6371 * 0.539956803 * (
        acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
    )


# define float checker for map id's
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def analyse_maps(mapfile):
    # create empty dataframe for processing
    map_df = pd.DataFrame(columns=('Map','Description','MapID','Start','End', 'Load?'))
    map_df.MapID.astype('object')

    # start counter that verifies all maps are processed
    mapverify = 0

    # open designated mapfile, runs through all lines
    # if map is detected line is processed (by being split) and verification counter is updated
    with open(mapfile) as f:
        for index, line in enumerate(f):
            if line[0:3] == 'MAP':
                mapverify += 1
                temp_list = line.split(' ')

                # if/else detects if line is of regular variety ending on \n, otherwise it has to be processed differently
                # example line: ['MAP', 'A04__L', 'version', '1', '18-07-2007', '', 'Approach', 'line', 'EHAM', 'rwy', '04', 'Lines', '', 'AAA', 'map-id', '-26-', '', '\n']

                # if line ends on \n description until map id are saved (7th entry until second to last)
                if temp_list[-1] == '\n':
                    tempstr = ''
                    for s in temp_list[6:-2]:
                        tempstr += s+' '
                    # tempdf filled in following way: mapname, description, mapid, line where map starts
                    # tempdf saved in mapdf
                    if is_number(temp_list[-3][1:-1]) == True:
                        temp_df = pd.DataFrame([temp_list[1], tempstr, temp_list[-3][1:-1], index+1], index=('Map','Description','MapID','Start'))
                    else:
                        temp_df = pd.DataFrame([temp_list[1], tempstr, index+1], index=('Map','Description','Start'))
                    map_df = map_df.append(temp_df.T)


                # if line DOES NOT end on \n last entry is stuck together with \n, for example 26\n, so has to be split
                else:
                    # \n dropped from last entry
                    # description until map id are saved (7th entry until last)
                    temp_list[-1] = temp_list[-1].replace('\n','')
                    tempstr = ''
                    for s in temp_list[6:]:
                        tempstr += s+' '
                    # checks if last entry is a map id
                    # if it is it is added to tempdf and tempdf filled in following way: mapname, description, mapid, line where map starts
                    # otherwise tempdf filled in following way: mapname, description, line where map starts
                    # tempdf saved in mapdf
                    if is_number(temp_list[-1]) == True:
                        temp_df = pd.DataFrame([temp_list[1], tempstr, temp_list[-1], index+1], index=('Map','Description','MapID','Start'))
                    else:
                        temp_df = pd.DataFrame([temp_list[1], tempstr, index+1], index=('Map','Description','Start'))
                    map_df = map_df.append(temp_df.T)

    # adds map end line to dataframe by looking ahead at next map start line
    # for last map, end line is document lenght
    for i in range(len(map_df)-1):
        map_df.iloc[i,4] = map_df.iloc[i+1,3]-1
    map_df.iloc[-1,4] = index

    # set if all maps shoud (not) be loaded based on setting at script beginning
    map_df['Load?'][:] = loadallmaps

    # checks if all maps have been processed correctly
    # if not, raises error
    if mapverify != len(map_df):
        print('not all maps loaded correctly')

    #s et map name to be index
    map_df = map_df.set_index('Map')

    # dataframe saved to excel
    map_df.to_excel('maps.xlsx')

    return map_df


# read excel incase manual selection of maps was done
map_df = pd.read_excel('maps.xlsx', index_col='Map')


def analyse_points(pointsfile):
    # this block transforms points txt to usuable database

    # open designated pointsfile
    file = open(pointsfile, 'r')

    # create empty lists for waypoint and respective latitude and longitude
    waypoint = []
    lat = []
    lon = []

    # skip first two lines
    file.readline()
    file.readline()
    # run thorugh document
    line = file.readline()
    while line:
        # create temporary placeholders for processing
        waypoint_temp = line[0:12]
        lat_temp = line[12:24]
        lon_temp = line[24:36]

        # clean up spaces
        waypoint_temp = waypoint_temp.replace(' ', '')
        lat_temp = lat_temp.replace(' ', '')
        lon_temp = lon_temp.replace(' ', '')

        # append lists with relevant data
        waypoint.append(waypoint_temp)
        lat.append(lat_temp)
        lon.append(lon_temp)

        # read next line
        line = file.readline()

        # create basic dataframe from lists
    points = pd.DataFrame([waypoint, lat, lon], index=('waypoint', 'lat', 'lon')).T

    # process latitude
    # latitude given in N/S format, needs to be +/-
    for i in range(len(points)):
        if points.lat[i][-1] == 'N':
            points.lat[i] = points.lat[i][:-1]
        elif points.lat[i][-1] == 'S':
            points.lat[i] = points.lat[i][:-1]
            points.lat[i] = '-' + points.lat[i]
        else:
            print(points.lat[i])
            raise Exception("Latitude format incorrect")

    # process longitude
    # longitude given in E/W format, needs to be +/-
    for i in range(len(points)):
        if points.lon[i][-1] == 'E':
            points.lon[i] = points.lon[i][:-1]
        elif points.lon[i][-1] == 'W':
            points.lon[i] = points.lon[i][:-1]
            points.lon[i] = '-' + points.lon[i]
        else:
            print(points.lon[i])
            raise Exception("Longitude format incorrect")

            # lat/lon given as degrees, needs to be decimal
    # entries split and processed
    for i in range(len(points)):
        lat_0 = points.lat[i][0:2]
        lat_1 = points.lat[i][2:4]
        lat_2 = points.lat[i][4:]
        points.lat[i] = float(lat_0) + float(lat_1) / 60 + float(lat_2) / 3600

        if points.lon[i][0] == '-':
            lon_0 = points.lon[i][1:4]
            lon_1 = points.lon[i][4:6]
            lon_2 = points.lon[i][6:]
            points.lon[i] = -float(lon_0) - float(lon_1) / 60 - float(lon_2) / 3600
        else:
            lon_0 = points.lon[i][0:3]
            lon_1 = points.lon[i][3:5]
            lon_2 = points.lon[i][5:]
            points.lon[i] = float(lon_0) + float(lon_1) / 60 + float(lon_2) / 3600

    # wrapround protection
    for i in range(len(points)):
        if points.lon[i] > 180:
            points.lon[i] = points.lon[i] - 360

    # set waypoints to be index for later lookup
    points = points.set_index('waypoint')

    # save points database as excel file
    points.to_excel('points.xlsx')

    return points


def line_select_name(name, map_df):
    map_df.iloc[id, 4] = 1

    # this block determines which lines in the map file need to be processed by the parser

    # start with empty list
    read_lines = []

    # basic processing by adding lines of selected maps to list
    for i in range(len(map_df)):
        if map_df.iloc[i, 4] == 1:
            for j in range(map_df.iloc[i, 3] - map_df.iloc[i, 2] + 1):
                read_lines.append(j + map_df.iloc[i, 2] - 1)

    # some maps contain submaps, which are other maps which need to be added at this step in the process
    # code runs through lines designated before and lists what submaps are used
    # submap name looked up in maps table and lines added if not already present
    # process repeated in case of submaps in submaps (probably not needed but better to err on safe side)
    submaps = []
    with open(mapfile) as f:
        for index, line in enumerate(f):
            if index in read_lines:
                if line.replace(' ', '')[0:6] == 'SubMap':
                    submapname = line.split(" ")[-1]
                    submaps.append(submapname.replace('\n', ''))

    for i in range(len(submaps)):
        for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
            if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
                read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

    with open(mapfile) as f:
        for index, line in enumerate(f):
            if index in read_lines:
                if line.replace(' ', '')[0:6] == 'SubMap':
                    submapname = line.split(" ")[-1]
                    submaps.append(submapname.replace('\n', ''))

    for i in range(len(submaps)):
        for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
            if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
                read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

    #  list with line numbers sorted to improve performance in parser
    read_lines.sort()

    return read_lines


def line_select_id(name, map_df):
    for i in range(len(map_df)):
        if str(float(name)) == str(map_df.iloc[i, 1]):
            map_df.iloc[i, 4] = 1

    # this block determines which lines in the map file need to be processed by the parser

    # start with empty list
    read_lines = []

    # basic processing by adding lines of selected maps to list
    for i in range(len(map_df)):
        if map_df.iloc[i, 4] == 1:
            for j in range(map_df.iloc[i, 3] - map_df.iloc[i, 2] + 1):
                read_lines.append(j + map_df.iloc[i, 2] - 1)

    # some maps contain submaps, which are other maps which need to be added at this step in the process
    # code runs through lines designated before and lists what submaps are used
    # submap name looked up in maps table and lines added if not already present
    # process repeated in case of submaps in submaps (probably not needed but better to err on safe side)
    submaps = []
    with open(mapfile) as f:
        for index, line in enumerate(f):
            if index in read_lines:
                if line.replace(' ', '')[0:6] == 'SubMap':
                    submapname = line.split(" ")[-1]
                    submaps.append(submapname.replace('\n', ''))

    for i in range(len(submaps)):
        for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
            if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
                read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

    with open(mapfile) as f:
        for index, line in enumerate(f):
            if index in read_lines:
                if line.replace(' ', '')[0:6] == 'SubMap':
                    submapname = line.split(" ")[-1]
                    submaps.append(submapname.replace('\n', ''))

    for i in range(len(submaps)):
        for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
            if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
                read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

    #  list with line numbers sorted to improve performance in parser
    read_lines.sort()

    return read_lines


# this block determines which lines in the map file need to be processed by the parser

# start with empty list
read_lines = []

# basic processing by adding lines of selected maps to list
for i in range(len(map_df)):
    if map_df.iloc[i, 4] == 1:
        for j in range(map_df.iloc[i, 3] - map_df.iloc[i, 2] + 1):
            read_lines.append(j + map_df.iloc[i, 2] - 1)

# some maps contain submaps, which are other maps which need to be added at this step in the process
# code runs through lines designated before and lists what submaps are used
# submap name looked up in maps table and lines added if not already present
# process repeated in case of submaps in submaps (probably not needed but better to err on safe side)
submaps = []
with open(mapfile) as f:
    for index, line in enumerate(f):
        if index in read_lines:
            if line.replace(' ', '')[0:6] == 'SubMap':
                submapname = line.split(" ")[-1]
                submaps.append(submapname.replace('\n', ''))

for i in range(len(submaps)):
    for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
        if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
            read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

with open(mapfile) as f:
    for index, line in enumerate(f):
        if index in read_lines:
            if line.replace(' ', '')[0:6] == 'SubMap':
                submapname = line.split(" ")[-1]
                submaps.append(submapname.replace('\n', ''))

for i in range(len(submaps)):
    for j in range(map_df.loc[submaps[i]][3] - map_df.loc[submaps[i]][2] + 1):
        if j + map_df.loc[submaps[i]][2] - 1 not in read_lines:
            read_lines.append(j + map_df.loc[submaps[i]][2] - 1)

#  list with line numbers sorted to improve performance in parser
read_lines.sort()


def basic_processing(mapfile, read_lines):
    # this block processes map file to bluesky commands
    line_base = pd.DataFrame(columns=('coord_1', 'coord_2', 'split_sign'))
    circ_df = pd.DataFrame(columns=(
    'coord_1', 'radius', 'start', 'stop', 'arclength', 'lat_1', 'lon_1', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2'))
    mark_base = pd.DataFrame(columns=('coord_1', 'coord_2', 'mark_dist', 'split_sign'))

    # set variables for circle processing as this is spread over multiple lines
    circ_temp1 = 0
    circ_temp2 = 0
    lynbeg_cont = 0
    mrkbeg_cont = 0
    tempvarcontlinemrk = ''

    # start going through mapfile
    with open(mapfile) as f:
        for index, line in enumerate(f):
            # if statement checks if line has been set to read above
            if index in read_lines:

                # blocks below contain different processing of lines
                # they are:
                # 1 new line
                # 2 continuation of line
                # 3 arc/circle
                # 4 others that are currently unused
                ###############################################################

                # 1 new line
                # if LynBeg is detected at start of line following it is a new line
                # line is split on - between points and coordinates are cleaned up

                if line.replace(' ', '')[0:6] == 'LynBeg':

                    looplist1 = []
                    looplist2 = []
                    looplist3 = []

                    line2 = line.replace('LynBeg', '').replace('\n', '').replace(' ', '').replace('>', '-')

                    line = line.replace('LynBeg', '')
                    line = line.replace('\n', '')
                    line = line.replace(' ', '')

                    points_line = line2.split('-')

                    if points_line[-1] != '':
                        for i in range(len(points_line) - 1):
                            looplist1.append(points_line[i])
                            looplist2.append(points_line[i + 1])
                            looplist3.append(line.split(points_line[i])[1][0:1])
                        lynbeg_cont = 0

                    else:
                        if line != '':
                            tempvarcontline = [points_line[-2], line.replace(' ', '').split(points_line[-2])[1]]
                            for i in range(len(points_line) - 2):
                                looplist1.append(points_line[i])
                                looplist2.append(points_line[i + 1])
                                looplist3.append(line.split(points_line[i])[1][0:1])
                            lynbeg_cont = 1
                        else:
                            lynbeg_cont = 0

                    temp_df = pd.DataFrame([looplist1, looplist2, looplist3],
                                           index=('coord_1', 'coord_2', 'split_sign'))
                    line_base = line_base.append(temp_df.T)

                    mrkbeg_cont = 0

                ###############################################################

                # 2 continuation of line
                # check for continuation of line
                # last entry of coordinates is added to start of processing list as line needs to be drawn from there to coordinate at start of new line
                elif lynbeg_cont == 1:

                    looplist1 = []
                    looplist2 = []
                    looplist3 = []

                    line2 = line.replace('LynBeg', '').replace('\n', '').replace(' ', '').replace('>', '-')

                    line = line.replace('LynBeg', '')
                    line = line.replace('\n', '')
                    line = line.replace(' ', '')

                    points_line = line2.split('-')

                    looplist1.append(tempvarcontline[0])
                    looplist2.append(points_line[0])
                    looplist3.append(tempvarcontline[1])

                    if points_line[-1] != '':
                        for i in range(len(points_line) - 1):
                            looplist1.append(points_line[i])
                            looplist2.append(points_line[i + 1])
                            looplist3.append(line.split(points_line[i])[1][0:1])
                        lynbeg_cont = 0

                    else:
                        if line != '':
                            tempvarcontline = [points_line[-2], line.replace(' ', '').split(points_line[-2])[1]]
                            for i in range(len(points_line) - 2):
                                looplist1.append(points_line[i])
                                looplist2.append(points_line[i + 1])
                                looplist3.append(line.split(points_line[i])[1][0:1])
                            lynbeg_cont = 1
                        else:
                            lynbeg_cont = 0

                    temp_df = pd.DataFrame([looplist1, looplist2, looplist3],
                                           index=('coord_1', 'coord_2', 'split_sign'))
                    line_base = line_base.append(temp_df.T)

                    mrkbeg_cont = 0

                ###############################################################

                # 3 arc/circle

                # defines arc/circle coordinates
                # at start circ_temp1 and circ_temp2 should be 0
                # these variables are needed because needed info from arc/circle is spread over 3 lines

                # start process for circle if start is detected
                # temp lists are reset at start
                elif line.replace(' ', '')[0:6] == 'StlCir':
                    looplistcirc1 = []
                    looplistcirc2 = []
                    looplistcirc3 = []
                    looplistcirc4 = []

                    # add coordinate at center to list
                    temp_a = line.replace(' ', '').split(":")[-1]
                    looplistcirc1.append(temp_a.replace('\n', ''))

                    # set first variable to 1
                    circ_temp1 = 1

                # if first variable is 1
                elif circ_temp1 == 1:
                    # set first variable to 0, second variable to 1
                    circ_temp1 = 0
                    circ_temp2 = 1

                    # read out start and stop angle of arc (from north, clockwise)
                    if line.split(' ')[-1] == '\n':
                        tempstart = line.split(' ')[-4]
                        tempstop = line.split(' ')[-2]
                    else:
                        tempstart = line.split(' ')[-3]
                        tempstop = line.split(' ')[-1]
                    # add start and stop angle to list
                    looplistcirc3.append(float(tempstart.replace(',', '')))
                    looplistcirc4.append(float(tempstop.replace('\n', '')))

                # if second variable is 1
                elif circ_temp2 == 1:
                    # set second variable to 0
                    circ_temp2 = 0
                    # read out radius
                    temp_b = line.replace(' ', '').split(':')[1].split(',')[0]
                    # add radius to temp var
                    looplistcirc2.append(temp_b.replace('start', ''))

                    # add values to temp df for appending
                    temp_df = pd.DataFrame([looplistcirc1, looplistcirc2, looplistcirc3, looplistcirc4],
                                           index=('coord_1', 'radius', 'start', 'stop'))

                    # append to main circle dataframe
                    circ_df = circ_df.append(temp_df.T)

                    # variable set to 0 as line wont continue
                    lynbeg_cont = 0
                    mrkbeg_cont = 0

                ###############################################################

                elif line.replace(' ', '')[0:6] == 'MrkBeg':
                    lynbeg_cont = 0
                    if line.replace(' ', '').replace('\n', '').split(' ')[0][-2] == '1':
                        mark_dist = 10  # dist in NM!
                        mrkbeg_cont = 1
                    elif line.replace(' ', '').replace('\n', '').split(' ')[0][-1] == '2':
                        mark_dist = 2  # dist in NM!
                        mrkbeg_cont = 1
                    else:
                        print('Distance between marks not recognized')

                elif mrkbeg_cont == 1:

                    looplist1 = []
                    looplist2 = []
                    looplist3 = []
                    looplist4 = []

                    line2 = line.replace('*-', '*>').replace('_-', '*>').replace('_>', '*>').replace('\n', '').replace(
                        ' ', '')

                    points_linemrk = line2.split('*>')

                    if tempvarcontlinemrk != '':
                        looplist1.append(tempvarcontlinemrk[0])
                        looplist2.append(points_linemrk[0])
                        looplist3.append(mark_dist)
                        looplist4.append(tempvarcontlinemrk[1])

                    if points_linemrk[-1] != '':
                        tempvarcontlinemrk = ''
                        mrkbeg_cont = 0
                        for i in range(len(points_linemrk) - 1):
                            looplist1.append(points_linemrk[i])
                            looplist2.append(points_linemrk[i + 1])
                            looplist3.append(mark_dist)
                            looplist4.append(line.replace(' ', '').split(points_linemrk[i])[1][0:2])
                    else:
                        tempvarcontlinemrk = [points_linemrk[-2],
                                              line.replace(' ', '').replace('\n', '').split(points_linemrk[-2])[1]]
                        for i in range(len(points_linemrk) - 2):
                            looplist1.append(points_linemrk[i])
                            looplist2.append(points_linemrk[i + 1])
                            looplist3.append(mark_dist)
                            looplist4.append(line.replace(' ', '').split(points_linemrk[i])[1][0:2])

                    temp_df = pd.DataFrame([looplist1, looplist2, looplist3, looplist4],
                                           index=('coord_1', 'coord_2', 'mark_dist', 'split_sign'))
                    mark_base = mark_base.append(temp_df.T)

                # 4 others that are currently unused
                # includes markings and text on map, which is currently not implemented

                ###############################################################

                elif line.replace(' ', '')[0:6] == 'SymStr':
                    # variable set to 0 as line wont continue
                    lynbeg_cont = 0
                    mrkbeg_cont = 0

                elif line.replace(' ', '')[0:6] == 'String':
                    # variable set to 0 as line wont continue
                    lynbeg_cont = 0
                    mrkbeg_cont = 0

    ###############################################################
    line_base = line_base.reset_index(drop=True)
    circ_df = circ_df.reset_index(drop=True)
    mark_base = mark_base.reset_index(drop=True)

    return line_base, circ_df, mark_base


def write_scn(remove_graphics, line_df, circtoline_df, mark_lines, mark_markers, name):
    # combine line and circle commands with basic starting commands
    commands = pd.concat(
        [remove_graphics, line_df['BLUESKYCOMMAND'], circtoline_df['BLUESKYCOMMAND'], mark_lines['BLUESKYCOMMAND'],
         mark_markers['BLUESKYCOMMAND']])
    # reset index as index comes from both lists
    commands = commands.reset_index(drop=True)

    # combine given scenario file with extension
    scenariofile = str(name) + '.scn'
    # write scenario file
    np.savetxt('mapid/' + scenariofile, commands, fmt="%s")

    # combine line and circle commands with basic starting commands
    commands2 = pd.concat(
        [remove_graphics, line_df['BLUESKYCOMMAND2'], circtoline_df['BLUESKYCOMMAND2'], mark_lines['BLUESKYCOMMAND2'],
         mark_markers['BLUESKYCOMMAND2']])
    # reset index as index comes from both lists
    commands2 = commands2.reset_index(drop=True)

    # combine given scenario file with extension
    scenariofile2 = 'del_' + str(name) + '.scn'
    # write scenario file
    np.savetxt('mapid/' + scenariofile2, commands2, fmt="%s")


def process_lines(df, name):
    target = pd.DataFrame(
        columns=('coord_1', 'coord_2', 'lat_1', 'lon_1', 'lat_2', 'lon_2', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2'))
    df = df.reset_index(drop=True)

    looplist1 = []
    looplist2 = []
    for i in range(len(df)):
        if df.split_sign[i] == '-':
            looplist1.append(df.coord_1[i])
            looplist2.append(df.coord_2[i])

    temp_df = pd.DataFrame([looplist1, looplist2], index=('coord_1', 'coord_2'))
    target = target.append(temp_df.T)

    # processes all lines that have to be drawn
    # looks up lat and lon of 2 coords and puts them in dataframe
    for i in range(len(target)):
        target['lat_1'][i] = points.loc[target['coord_1'][i]].lat
        target['lon_1'][i] = points.loc[target['coord_1'][i]].lon
        target['lat_2'][i] = points.loc[target['coord_2'][i]].lat
        target['lon_2'][i] = points.loc[target['coord_2'][i]].lon

        # turn lats and lons into string that can be processed by bluesky into a line
        target['BLUESKYCOMMAND'][i] = '0:00:00.00>LINE ' + 'LINE' + str(name) + '_' + str(i + 1) + ' ' + str(
            target['lat_1'][i]) + ',' + str(target['lon_1'][i]) + ',' + str(target['lat_2'][i]) + ',' + str(
            target['lon_2'][i])
        target['BLUESKYCOMMAND2'][i] = '0:00:00.00>DEL ' + 'LINE' + str(name) + '_' + str(i + 1)

    return target


def process_circles(df, name, circleresolution):
    circtoline_df = pd.DataFrame(columns=('lat_1', 'lon_1', 'lat_2', 'lon_2', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2'))
    df = df.reset_index(drop=True)

    # processes all arcs/circles that have to be drawn
    # loops through all entries
    for k in range(len(df)):
        # calculates arclength
        # if actlength is negative it runs through 0 so it is added to 360
        df['arclength'][k] = df['stop'][k] - df['start'][k]
        if df['arclength'][k] < 0:
            df['arclength'][k] = 360 + df['arclength'][k]

        # lat and lon of center coordinate calculated
        df['lat_1'][k] = points.loc[df['coord_1'][k]].lat
        df['lon_1'][k] = points.loc[df['coord_1'][k]].lon

        # lat and lon of center loaded
        lat0 = df['lat_1'][k]
        lon0 = df['lon_1'][k]

        # set flat earth correction and set circle radius to meters
        coslatinv = 1.0 / np.cos(np.deg2rad(lat0))
        Rcircle = float(df['radius'][k]) * 1852

        # start list with angles based on arclength
        # first entry is 0 as for n lines to be drawn n+1 points need to be present
        angles = [0]

        # empty list started for lats and lons of points on arc
        latCircle = []
        lonCircle = []

        # checks if arclength is an integer of the resolution
        # if it is there is no need to make custom angle segments
        if np.floor(df['arclength'][k] / circleresolution) == np.ceil(df['arclength'][k] / circleresolution):
            # for amount of line segments append to list
            for i in range(int(np.ceil(df['arclength'][k] / circleresolution))):
                angles.append(circleresolution * (i + 1))

        # if it is not round amount of needed segments up and subtract 2* circleresolution
        # then split remainder in 2 and put at start and end
        else:
            anglepart = (df['arclength'][k] - (
                        (np.ceil(df['arclength'][k] / circleresolution) - 2) * circleresolution)) / 2
            for i in range(int(np.ceil(df['arclength'][k] / circleresolution))):
                if i == 0:
                    angles.append(anglepart)
                elif i == range(int(np.ceil(df['arclength'][k] / circleresolution)))[-1]:
                    angles.append(df['arclength'][k])
                else:
                    angles.append(anglepart + (circleresolution * (i)))

        # calculate lat and lon for point that will constitute lines of arc
        for i in range(len(angles)):
            latCircle.append(lat0 + np.rad2deg(
                Rcircle * np.sin(np.deg2rad(-df['start'][k] + 90) - np.deg2rad(angles[i])) / Rearth))  # [deg]
            lonCircle.append(lon0 + np.rad2deg(Rcircle * np.cos(
                np.deg2rad(-df['start'][k] + 90) - np.deg2rad(angles[i])) * coslatinv / Rearth))  # [deg]

        # create empty lists for loop and append 2 lat and lons to dataframe

        looplist1 = []
        looplist2 = []
        looplist3 = []
        looplist4 = []

        for i in range(len(latCircle) - 1):
            looplist1.append(latCircle[i])
            looplist2.append(latCircle[i + 1])
            looplist3.append(lonCircle[i])
            looplist4.append(lonCircle[i + 1])

        temp_df = pd.DataFrame([looplist1, looplist3, looplist2, looplist4], index=('lat_1', 'lon_1', 'lat_2', 'lon_2'))
        circtoline_df = circtoline_df.append(temp_df.T)

    # reset index for loop
    circtoline_df = circtoline_df.reset_index(drop=True)

    for i in range(len(circtoline_df)):
        # turn lats and lons into string that can be processed by bluesky into a line
        circtoline_df['BLUESKYCOMMAND'][i] = '0:00:00.00>LINE ' + 'LINE_FROMCIRC' + str(name) + '_' + str(
            i + 1) + ' ' + str(circtoline_df['lat_1'][i]) + ',' + str(circtoline_df['lon_1'][i]) + ',' + str(
            circtoline_df['lat_2'][i]) + ',' + str(circtoline_df['lon_2'][i])
        circtoline_df['BLUESKYCOMMAND2'][i] = '0:00:00.00>DEL ' + 'LINE_FROMCIRC' + str(name) + '_' + str(i + 1)

    return circtoline_df


def process_markers(df, name):
    mark_lines = pd.DataFrame(
        columns=('coord_1', 'coord_2', 'lat_1', 'lon_1', 'lat_2', 'lon_2', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2'))
    markers_base = pd.DataFrame(
        columns=('coord_1', 'coord_2', 'lat_1', 'lon_1', 'lat_2', 'lon_2', 'mark_dist', 'distance'))
    mark_markers = pd.DataFrame(columns=(
    'latcent', 'loncent', 'heading', 'lat_1', 'lon_1', 'lat_2', 'lon_2', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2'))

    df = df.reset_index(drop=True)

    looplist1a = []
    looplist2a = []

    looplist1b = []
    looplist2b = []
    looplist3b = []

    for i in range(len(df)):
        if df.split_sign[i] == '*-' or df.split_sign[i] == '_-':
            looplist1a.append(df.coord_1[i])
            looplist2a.append(df.coord_2[i])

        if df.split_sign[i] == '*-' or df.split_sign[i] == '*>':
            looplist1b.append(df.coord_1[i])
            looplist2b.append(df.coord_2[i])
            looplist3b.append(df.mark_dist[i])

    temp_df = pd.DataFrame([looplist1a, looplist2a], index=('coord_1', 'coord_2'))
    mark_lines = mark_lines.append(temp_df.T)
    mark_lines = mark_lines.reset_index(drop=True)

    temp_df = pd.DataFrame([looplist1b, looplist2b, looplist3b], index=('coord_1', 'coord_2', 'mark_dist'))
    markers_base = markers_base.append(temp_df.T)
    markers_base = markers_base.reset_index(drop=True)

    for i in range(len(mark_lines)):
        mark_lines['lat_1'][i] = points.loc[mark_lines['coord_1'][i]].lat
        mark_lines['lon_1'][i] = points.loc[mark_lines['coord_1'][i]].lon
        mark_lines['lat_2'][i] = points.loc[mark_lines['coord_2'][i]].lat
        mark_lines['lon_2'][i] = points.loc[mark_lines['coord_2'][i]].lon

        mark_lines['BLUESKYCOMMAND'][i] = '0:00:00.00>LINE ' + 'MRKLINE' + str(name) + '_' + str(i + 1) + ' ' + str(
            mark_lines['lat_1'][i]) + ',' + str(mark_lines['lon_1'][i]) + ',' + str(mark_lines['lat_2'][i]) + ',' + str(
            mark_lines['lon_2'][i])
        mark_lines['BLUESKYCOMMAND2'][i] = '0:00:00.00>DEL ' + 'MRKLINE' + str(name) + '_' + str(i + 1)

    for i in range(len(markers_base)):
        # mark_markers = pd.DataFrame(columns=('coord_1','coord_2','lat_1','lon_1','lat_2','lon_2','mark_dist','latcent','loncent','heading','BLUESKYCOMMAND','BLUESKYCOMMAND2'))
        markers_base['lat_1'][i] = points.loc[markers_base['coord_1'][i]].lat
        markers_base['lon_1'][i] = points.loc[markers_base['coord_1'][i]].lon
        markers_base['lat_2'][i] = points.loc[markers_base['coord_2'][i]].lat
        markers_base['lon_2'][i] = points.loc[markers_base['coord_2'][i]].lon

        fwd_azimuth, back_azimuth, distance = geodesic.inv(markers_base['lon_1'][i], markers_base['lat_1'][i],
                                                           markers_base['lon_2'][i], markers_base['lat_2'][i])
        markers_base['distance'][i] = distance / (1852)

        npts_temp = np.floor((distance / 1852) / markers_base['mark_dist'][i])

        r = geodesic.fwd_intermediate(markers_base['lon_1'][i], markers_base['lat_1'][i], fwd_azimuth, npts=npts_temp,
                                      del_s=markers_base['mark_dist'][i] * 1852)

        looplist1 = []
        looplist2 = []
        looplist3 = []
        looplist4 = []
        looplist5 = []
        looplist6a = []
        looplist6b = []
        looplist6c = []
        looplist6d = []

        for j in range(int(np.floor(
                great_circle(markers_base['lat_1'][i], markers_base['lon_1'][i], markers_base['lat_2'][i],
                             markers_base['lon_2'][i]) / markers_base['mark_dist'][i]))):

            if fwd_azimuth < 0:
                looplist1.append(fwd_azimuth + 360)
            else:
                looplist1.append(fwd_azimuth)

            looplist2.append(r.lats[j])
            looplist3.append(r.lons[j])

            r2 = geodesic.fwd_intermediate(r.lons[j], r.lats[j], fwd_azimuth + 90, npts=1, del_s=1852 / 2)
            r3 = geodesic.fwd_intermediate(r.lons[j], r.lats[j], fwd_azimuth - 90, npts=1, del_s=1852 / 2)

            looplist4.append(
                '0:00:00.00>LINE ' + 'MARKER' + str(name) + '_markno' + str(j + 1) + ' ' + str(r2.lats[0]) + ',' + str(
                    r2.lons[0]) + ',' + str(r3.lats[0]) + ',' + str(r3.lons[0]))
            looplist5.append('0:00:00.00>DEL ' + 'MARKER' + str(name) + '_markno' + str(j + 1))
            looplist6a.append(str(r2.lats[0]))
            looplist6b.append(str(r2.lons[0]))
            looplist6c.append(str(r3.lats[0]))
            looplist6d.append(str(r3.lons[0]))

        temp_df = pd.DataFrame(
            [looplist1, looplist2, looplist3, looplist4, looplist5, looplist6a, looplist6b, looplist6c, looplist6d],
            index=(
            'heading', 'latcent', 'loncent', 'BLUESKYCOMMAND', 'BLUESKYCOMMAND2', 'lat_1', 'lon_1', 'lat_2', 'lon_2'))
        mark_markers = mark_markers.append(temp_df.T)

    return mark_lines, mark_markers


if __name__ == '__main__':

    map_df = analyse_maps(mapfile)

    points = analyse_points(pointsfile)

    uniqueids = map_df.MapID.unique()[pd.notnull(map_df.MapID.unique())]
    for id in range(len(uniqueids)):
        name = int(uniqueids[id])
        map_df = pd.read_excel('maps.xlsx', index_col='Map')

        read_lines = line_select_id(name, map_df)

        line_base, circ_df, mark_base = basic_processing(mapfile, read_lines)

        ###############################################################

        # add basic commands for every map
        # removes waypoints, airports and geo map
        # last two entries set position and zoom
        #     templist = ['0:00:00.00>SWRAD WPT','0:00:00.00>SWRAD APT','0:00:00.00>SWRAD GEO','PAN EHAM', 'ZOOM 0.5']
        templist = []
        remove_graphics = pd.DataFrame(templist)

        line_df = process_lines(line_base, name)

        circtoline_df = process_circles(circ_df, name, circleresolution)

        mark_lines, mark_markers = process_markers(mark_base, name)

        write_scn(remove_graphics, line_df, circtoline_df, mark_lines, mark_markers, name)

    for id in range(len(map_df)):
        name = str(map_df.index[id])
        map_df = pd.read_excel('maps.xlsx', index_col='Map')

        read_lines = line_select_name(name, map_df)

        line_base, circ_df, mark_base = basic_processing(mapfile, read_lines)

        ###############################################################

        # add basic commands for every map
        # removes waypoints, airports and geo map
        # last two entries set position and zoom
        #     templist = ['0:00:00.00>SWRAD WPT','0:00:00.00>SWRAD APT','0:00:00.00>SWRAD GEO','PAN EHAM', 'ZOOM 0.5']
        templist = []
        remove_graphics = pd.DataFrame(templist)

        line_df = process_lines(line_base, name)

        circtoline_df = process_circles(circ_df, name, circleresolution)

        mark_lines, mark_markers = process_markers(mark_base, name)

        write_scn(remove_graphics, line_df, circtoline_df, mark_lines, mark_markers, name)
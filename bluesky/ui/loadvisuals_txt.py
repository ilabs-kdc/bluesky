"""
Load visual data from text files.

Created by: Original BlueSky version
"""

from bluesky.navdatabase.loadnavdata_txt import thresholds, thrpoints
from bluesky.ui import palette
import os
from zipfile import ZipFile
import numpy as np
import bluesky as bs
from bluesky import settings

REARTH_INV = 1.56961231e-7

# Default settings and palette
palette.set_default_colours(
    polys=(0, 255, 255)
)

# used for calculating the vertices of the runways as well as the threshold boxes
def dlatlon(lat0, lon0, lat1, lon1, width):
    # calculate distance between ends of runways / threshold boxes
    flat_earth = np.cos(0.5 * np.radians(lat0 + lat1))
    lx = lat1 - lat0
    ly = (lon1 - lon0) * flat_earth
    l = np.sqrt(lx * lx + ly * ly)
    wx = ly / l * 0.5 * width
    wy = -lx / l * 0.5 * width
    dlat = np.degrees(wx * REARTH_INV)
    dlon = np.degrees(wy * REARTH_INV / flat_earth)

    # store the vertice information per runway /threshold box
    vertices = [lat0 + dlat, lon0 + dlon,
                lat0 - dlat, lon0 - dlon,
                lat1 + dlat, lon1 + dlon,
                lat0 - dlat, lon0 - dlon,
                lat1 + dlat, lon1 + dlon,
                lat1 - dlat, lon1 - dlon]

    return vertices


def threshold_vertices(lat, lon, bearing):
    ''' Generate threshold vectices for given runway threshold data. '''
    d_box = 20.0 * REARTH_INV  # m
    width_box = 30  # m

    # bearing in opposite direction
    opp_bearing = np.radians((np.degrees(bearing) + 180) % 360)

    # get points at both ends of the boxes around the threshold point
    # (zebra crossing)
    latbox0, lonbox0 = thrpoints(lat, lon, d_box, bearing)
    latbox1, lonbox1 = thrpoints(lat, lon, d_box, opp_bearing)

    # calculate vertices of threshold box
    vertices = dlatlon(np.degrees(latbox0), np.degrees(lonbox0), np.degrees(latbox1),
                       np.degrees(lonbox1), width_box)

    return vertices


def load_coastline_txt():
    # -------------------------COASTLINE DATA----------------------------------
    # Init geo (coastline)  data and convert pen up/pen down format of
    # coastlines to numpy arrays with lat/lon
    coast = []
    clat = clon = 0.0
    with open(os.path.join(settings.navdata_path, 'coastlines.dat'), 'r') as f:
        print("Reading coastlines.dat")
        for line in f:
            line = line.strip()
            if not (line == "" or line[0] == '#'):
                arg = line.split()
                if len(arg) == 3:
                    lat, lon = float(arg[1]), float(arg[2])
                    if arg[0] == 'D':
                        coast.append([clat, clon, lat, lon])
                    clat, clon = lat, lon
    # Sort the line segments by longitude of the first vertex
    coastvertices = np.array(
        sorted(coast, key=lambda a_entry: a_entry[1]), dtype=np.float32)
    coastindices = np.zeros(361)
    coastlon = coastvertices[:, 1]
    for i in range(0, 360):
        coastindices[i] = np.searchsorted(coastlon, i - 180) * 2
    coastvertices.resize((int(coastvertices.size / 2), 2))
    del coast
    return coastvertices, coastindices


def load_basemap_txt(atcmode):
    """
    Function: Load the LVNL base map from text file (for APP or ACC)
    Args:
        atcmode: ATC mode [string]
    Returns:

    Created by: Bob van Dillen
    Date: 17-9-2022
    """

    # Dictonaries to store the data
    lines = dict()
    dashedlines = dict()
    dottedlines = dict()
    points = dict()

    # Get file names
    if atcmode.upper() == 'APP':
        filename = ['252']
    elif atcmode.upper() == 'ACC':
        filename = ['751', '752']

    # Open the files
    for file in filename:
        with open(os.path.join('scenario/LVNL/Maps/mapid', '' + file + '.scn'), 'r') as f:
            for line in f:
                # Edit scenario file to simple strings
                line = line.replace('>', ' ')
                line = line.replace(',', ' ')
                line = line.strip()
                arg = line.split()
                del arg[0]  # delete command time stamp

                # Check if there is something to draw
                if not (line == "" or line[0] == '#' or arg[0] == 'COLOR'):

                    # Capital letters
                    arg[0] = arg[0].upper()

                    # Dashed line
                    if arg[0] == 'DASHEDLINE':
                        # Get the coordinates
                        vbuf_dashed = np.array([float(arg[2]), float(arg[3]), float(arg[4]), float(arg[5])],
                                               dtype=np.float32)

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_dashed) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        dashedlines[arg[1]] = (vbuf_dashed, colorbuf)

                    # Dotted line
                    elif arg[0] == 'DOTTEDLINE':
                        # Get the coordinates
                        vbuf_dotted = np.array([float(arg[2]), float(arg[3]), float(arg[4]), float(arg[5])],
                                               dtype=np.float32)

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_dotted) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        dottedlines[arg[1]] = (vbuf_dotted, colorbuf)

                    # Lines
                    elif arg[0][-4:] == 'LINE':
                        # Get teh coordinates
                        data = np.array(arg[2:], dtype=np.float32)
                        # Process the coordinates
                        vbuf_line = np.empty(2 * len(data-4), dtype=np.float32)
                        vbuf_line[0::4] = data[0:-2:2]  # lat
                        vbuf_line[1::4] = data[1:-2:2]  # lon
                        vbuf_line[2::4] = data[2::2]  # lat
                        vbuf_line[3::4] = data[3::2]  # lon

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_line) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        lines[arg[1]] = (vbuf_line, colorbuf)

                    # Polys
                    elif arg[0][-4:] == 'POLY':
                        # Get the coordinates
                        data = np.array(arg[2:], dtype=np.float32)
                        # Process the coordinates
                        vbuf_poly = np.empty(2 * len(data), dtype=np.float32)
                        vbuf_poly[0::4] = data[0::2]   # lat
                        vbuf_poly[1::4] = data[1::2]   # lon
                        vbuf_poly[2:-2:4] = data[2::2]  # lat
                        vbuf_poly[3:-3:4] = data[3::2]  # lon
                        vbuf_poly[-2:] = data[0:2]

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_poly) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        lines[arg[1]] = (vbuf_poly, colorbuf)

                    # Box
                    elif arg[0] == 'BOX':
                        # Convert box coordinates into polyline list
                        # BOX: 0 = lat0, 1 = lon0, 2 = lat1, 3 = lon1 , use bounding box
                        data = np.array([arg[2], arg[3],
                                         arg[2], arg[5],
                                         arg[4], arg[5],
                                         arg[4], arg[3]], dtype=np.float32)
                        vbuf_box = np.empty(2 * len(data), dtype=np.float32)
                        vbuf_box[0::4] = data[0::2]  # lat
                        vbuf_box[1::4] = data[1::2]  # lon
                        vbuf_box[2:-2:4] = data[2::2]  # lat
                        vbuf_box[3:-3:4] = data[3::2]  # lon
                        vbuf_box[-2:] = data[0:2]

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_box) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        lines[arg[1]] = (vbuf_box, colorbuf)

                    # Circle
                    elif arg[0] == 'CIRCLE':
                        # Input data is latctr,lonctr,radius[nm]
                        # Convert circle into polyline list

                        # Circle parameters
                        Rearth = 6371000.0  # radius of the Earth [m]
                        numPoints = 72  # number of straight line segments that make up the circrle

                        # Inputs
                        lat0 = float(arg[2])  # latitude of the center of the circle [deg]
                        lon0 = float(arg[3])  # longitude of the center of the circle [deg]
                        Rcircle = float(arg[4]) * 1852.0  # radius of circle [NM]

                        # Compute flat Earth correction at the center of the experiment circle
                        coslatinv = 1.0 / np.cos(np.deg2rad(lat0))

                        # compute the x and y coordinates of the circle
                        angles = np.linspace(0.0, 2.0 * np.pi, numPoints)  # ,endpoint=True) # [rad]

                        # Calculate the circle coordinates in lat/lon degrees.
                        # Use flat-earth approximation to convert from cartesian to lat/lon.
                        latCircle = lat0 + np.rad2deg(Rcircle * np.sin(angles) / Rearth)  # [deg]
                        lonCircle = lon0 + np.rad2deg(Rcircle * np.cos(angles) * coslatinv / Rearth)  # [deg]

                        # make the data array in the format needed to plot circle
                        data = np.empty(2 * numPoints, dtype=np.float32)  # Create empty array
                        data[0::2] = latCircle  # Fill array lat0,lon0,lat1,lon1....
                        data[1::2] = lonCircle

                        # Process the coordinates
                        vbuf_circle = np.empty(2 * len(data), dtype=np.float32)
                        vbuf_circle[0::4] = data[0::2]  # lat
                        vbuf_circle[1::4] = data[1::2]  # lon
                        vbuf_circle[2:-2:4] = data[2::2]  # lat
                        vbuf_circle[3:-3:4] = data[3::2]  # lon
                        vbuf_circle[-2:] = data[0:2]

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_circle) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        lines[arg[1]] = (vbuf_circle, colorbuf)

                    # Points
                    elif arg[0] == 'POINT':
                        # Get the coordinates
                        vbuf_points = np.array([float(arg[2]), float(arg[3])], dtype=np.float32)

                        # Define the color
                        defclr = tuple(palette.polys) + (255,)
                        colorbuf = np.array(len(vbuf_points) // 2 * defclr, dtype=np.uint8)

                        # Save the data
                        points[arg[1]] = (vbuf_points, colorbuf)

                # Colour
                if arg[0] == 'COLOR':
                    objects = [lines, dashedlines, dottedlines, points]

                    # Loop over object types
                    for obj in objects:
                        data = obj.get(arg[1])

                        # Find data
                        if data:
                            # Add the colour
                            defclr = (int(arg[2]), int(arg[3]), int(arg[4]), 255)
                            colorbuf = np.array(len(data[0]) // 2 * defclr, dtype=np.uint8)

                            obj[arg[1]] = (data[0], colorbuf)

    return lines, dashedlines, dottedlines, points


def load_mapsline_txt(args):
    """
    Function: Loads init map lines/points data and convert format to arrays with name, shape, coordinates and color

    Args: name of the map file
    Returns: name, shape, coordinates, color

    Created by: Mitchell de Keijzer
    Date: 01-04-2022

    """
    names = []
    shapes = []
    coords = []
    colors = []
    tbar_maps = ['NIRSI', 'GALIS', 'RANGEBAR', 'SOKS2']
    if args in tbar_maps:
        path = 'T-bar'
    else:
        path = 'mapid'
    # Load scenario map file
    with open(os.path.join('scenario/LVNL/Maps', '' + path + '', '' + args + '.scn'), 'r') as f:
        for line in f:
            # Edit scenario file to simple strings
            line = line.replace('>', ' ')
            line = line.replace(',', ' ')
            line = line.strip()
            arg = line.split()
            del arg[0]  # delete command time stamp
            if not (line == "" or line[0] == '#' or arg[0] == 'COLOR'):
                names.append(arg[1])
                shapes.append(arg[0])
                if arg[0] == 'POINT':
                    coords.append([float(arg[2]), float(arg[3])])
                else:
                    coords.append([float(arg[2]), float(arg[3]), float(arg[4]), float(arg[5])])
                colors.append(None)
            # If a specific color is given, replace None with the correct color code
            if arg[0] == 'COLOR':
                index = names.index(arg[1])
                colors[index] = (int(arg[2]), int(arg[3]), int(arg[4]))
    name = names
    shape = shapes
    coordinates = coords
    color = colors
    del names, shapes, coords, colors
    return name, shape, coordinates, color


# Only try this if BlueSky is started in qtgl gui mode
if bs.gui_type == 'qtgl':
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QProgressDialog
    from bluesky.ui.polytools import PolygonSet, BoundingBox


    class ProgressBar():
        def __init__(self, text):
            if QApplication.instance() is None:
                self.dialog = None
                print(text)
            else:
                self.dialog = QProgressDialog(text, 'Cancel', 0, 100)
                self.dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
                self.dialog.show()

        def update(self, value):
            if self.dialog:
                self.dialog.setValue(value)
                QApplication.processEvents()
            else:
                print('Progress: %.2f%% done' % value)

        def close(self):
            if self.dialog:
                self.dialog.close()


    """ Load static data for GUI from files such as airport, shapes, etc."""


    def load_aptsurface_txt():
        """ Read airport data from navigation database files"""
        pb = ProgressBar(
            'Binary buffer file not found, or file out of date: Constructing vertex buffers from geo data.')

        runways = []
        rwythr = []
        asphalt = PolygonSet()
        concrete = PolygonSet()
        cur_poly = asphalt
        apt_indices = []
        apt_ctr_lat = []
        apt_ctr_lon = []
        apt_bb = BoundingBox()
        count = 0
        bytecount = 0
        zfile = ZipFile(os.path.join(settings.navdata_path, 'apt.zip'))
        fsize = float(zfile.getinfo('apt.dat').file_size)
        print("Reading apt.dat from apt.zip")
        with zfile.open('apt.dat', 'r') as f:
            for line in f:
                bytecount += len(line)
                # Check how far we are
                count += 1
                if count % 1000 == 0:
                    pb.update((bytecount / fsize * 100.0))

                elems = line.decode(encoding="ascii", errors="ignore").strip().split()
                if not elems:
                    continue

                # 1: AIRPORT
                if elems[0] in ['1', '16', '17']:  # 1=airport, 16=seaplane base, 17=heliport
                    cur_poly.end()
                    # Store the starting vertices for this apt, [0, 0] if this is the first apt
                    if apt_indices:
                        start_indices = [apt_indices[-1][0] + apt_indices[-1][1],
                                         apt_indices[-1][2] + apt_indices[-1][3]]
                    else:
                        start_indices = [0, 0]

                    if asphalt.bufsize() // 2 > start_indices[0] or concrete.bufsize() // 2 > start_indices[1]:
                        apt_indices.append([
                            start_indices[0],
                            asphalt.bufsize() // 2 - start_indices[0],
                            start_indices[1],
                            concrete.bufsize() // 2 - start_indices[1]
                        ])

                        center = apt_bb.center()
                        apt_ctr_lat.append(center[0])
                        apt_ctr_lon.append(center[1])

                    # Reset the boundingbox
                    apt_bb = BoundingBox()
                    continue

                # 100: LAND RUNWAY
                if elems[0] == '100':
                    width = float(elems[1])
                    # Only asphalt and concrete runways
                    if int(elems[2]) > 2:
                        continue
                    # rwy_lbl = (elems[8], elems[17])

                    lat0 = float(elems[9])
                    lon0 = float(elems[10])
                    offset0 = float(elems[11])

                    lat1 = float(elems[18])
                    lon1 = float(elems[19])
                    offset1 = float(elems[20])

                    # runway vertices
                    runways.extend(dlatlon(lat0, lon0, lat1, lon1, width))

                    # threshold information: ICAO code airport, Runway identifier,
                    # latitude, longitude, bearing
                    # vertices: gives vertices of the box around the threshold

                    # opposite runways are on the same line. RWY1: 8-11, RWY2: 17-20
                    # Hence, there are two thresholds per line
                    # thr0: First lat0 and lon0 , then lat1 and lat1, offset=[11]
                    # thr1: First lat1 and lat1 , then lat0 and lon0, offset=[20]
                    thr0 = thresholds(np.radians(lat0), np.radians(lon0), np.radians(lat1), np.radians(lon1), offset0)
                    vertices0 = threshold_vertices(*thr0)
                    thr1 = thresholds(np.radians(lat1), np.radians(lon1), np.radians(lat0), np.radians(lon0), offset1)
                    vertices1 = threshold_vertices(*thr1)
                    rwythr.extend(vertices0)
                    rwythr.extend(vertices1)

                    continue

                # 110: TAXIWAY/PAVEMENT: Start of polygon contour
                if elems[0] == '110':
                    cur_poly.end()
                    if elems[1] == '1':
                        cur_poly = asphalt
                        cur_poly.begin()
                    elif elems[1] == '2':
                        cur_poly = concrete
                        cur_poly.begin()
                    continue

                # 130: AIRPORT BOUNDARY
                if elems[0] == '130':
                    cur_poly.end()
                    continue

                controlpoint = None
                # Straight line (111) or bezier line (112) in contour
                if elems[0] == '111' or elems[0] == '112':
                    vertex = np.array((float(elems[1]), float(elems[2]), 0.0))
                    apt_bb.update(vertex)

                    if cur_poly.in_poly:
                        if elems[0] == '112':
                            controlpoint = np.array((float(elems[3]), float(elems[4]), 0.0))

                        cur_poly.addVertex(vertex, controlpoint)

                # Straight (113) or bezier (114) contour endpoint
                elif elems[0] == '113' or elems[0] == '114':
                    vertex = np.array((float(elems[1]), float(elems[2]), 0.0))
                    apt_bb.update(vertex)

                    if cur_poly.in_poly:
                        if elems[0] == '114':
                            controlpoint = np.array((float(elems[3]), float(elems[4]), 0.0))

                        cur_poly.addVertex(vertex, controlpoint)

                        cur_poly.endContour()

                else:
                    cur_poly.end()

        # calculate the location of the runway thresholds

        # Clean up:
        cur_poly.end()
        start_indices = [apt_indices[-1][0] + apt_indices[-1][1],
                         apt_indices[-1][2] + apt_indices[-1][3]]

        if asphalt.bufsize() > start_indices[0] or concrete.bufsize() > start_indices[1]:
            apt_indices.append([
                start_indices[0],
                int(asphalt.bufsize() / 2) - start_indices[0],
                start_indices[1],
                int(concrete.bufsize() / 2) - start_indices[1]
            ])

            center = apt_bb.center()
            apt_ctr_lat.append(center[0])
            apt_ctr_lon.append(center[1])

        # Store in binary pickle file
        vbuf_asphalt = np.array(asphalt.vbuf, dtype=np.float32)
        vbuf_concrete = np.array(concrete.vbuf, dtype=np.float32)
        vbuf_runways = np.array(runways, dtype=np.float32)
        vbuf_rwythr = np.array(rwythr, dtype=np.float32)
        apt_ctr_lat = np.array(apt_ctr_lat)
        apt_ctr_lon = np.array(apt_ctr_lon)
        apt_indices = np.array(apt_indices)

        # Close the progress dialog
        pb.close()

        # return the data
        return vbuf_asphalt, vbuf_concrete, vbuf_runways, vbuf_rwythr, apt_ctr_lat, apt_ctr_lon, apt_indices

''' I/O Client implementation for the QtGL gui. '''
import socket

from PyQt5.QtCore import QTimer
import numpy as np

from bluesky.ui.loadvisuals import load_maplines
from bluesky import settings
from bluesky.ui import palette
from bluesky.ui.polytools import PolygonSet
from bluesky.ui.qtgl.customevents import ACDataEvent, RouteDataEvent
from bluesky.network.client import Client
from bluesky.core import Signal
from bluesky.tools.aero import ft
from bluesky.tools.files import findfile


# TID test
import bluesky as bs
from bluesky.ui.qtgl import console
from bluesky.tools import misc

settings.set_variable_defaults(atc_mode='BLUESKY')

# Globals
UPDATE_ALL = ['SHAPE', 'TRAILS', 'CUSTWPT', 'PANZOOM', 'ECHOTEXT']
ACTNODE_TOPICS = [b'ACDATA', b'PLOT*', b'ROUTEDATA*']
loaded_maps = []

class GuiClient(Client):
    """
    Edited by: Mitchell de Keijzer
    Date: 04-05-2022
    Changed: Added following methods (origin tid.py) for multiposition purposes
        clear():            Clear variables
        update_cmdline():   Update the command line
        exq():              Execute commandline
        exqcmd():           Execute a command
        clr():              Clear command
        cor():              Correct command
        setcmd():           Set a command
        changecmd():        Change the current command
        setarg():           Set an argument
        addarg():           Add an argument
        addchar():          Add a character
    """


    def __init__(self):
        super().__init__(ACTNODE_TOPICS)
        self.nodedata = dict()
        self.ref_nodedata = nodeData()
        self.discovery_timer = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)
        self.subscribe(b'SIMINFO')
        self.subscribe(b'TRAILS')
        self.subscribe(b'PLOT' + self.client_id)
        self.subscribe(b'ROUTEDATA' + self.client_id)

        # Signals
        self.actnodedata_changed = Signal('actnodedata_changed')


        # TID
        self.cmdslst = []
        self.argslst = []

        self.iact = 0

    def clear(self):
        """
        Function: Clear variables
        Args: -
        Returns: -
        """

        self.cmdslst = []
        self.argslst = []

        self.iact = 0

    def update_cmdline(self):
        """
        Function: Update the command line
        Args: -
        Returns: -
        """

        actdata = self.get_nodedata()
        id_select = console.Console._instance.id_select
        print('update cmdline id selected:', id_select)

        cmdline = id_select.strip() + ' ; '

        # Loop over commands
        for cmd, args in zip(self.cmdslst, self.argslst):
            cmdline += cmd
            # Loop over arguments for this command
            for arg in args:
                cmdline += ' ' + arg

            cmdline += ' ; '

        cmdline = cmdline[:-3]  # Remove last ' ; '

        # Set the command line
        console.Console._instance.set_cmdline(cmdline, 1)

    def exq(self):

        """
        Function: Execute commandline

        Edited by: Mitchell de Keijzer
        Date: 13-05-2022
        Changed: UCO connected to IP Address
        """

        actdata = bs.net.get_nodedata()
        id_select = console.Console._instance.id_select
        IPaddr = socket.gethostbyname(socket.gethostname())

        # Check if an aircraft is selected
        if id_select:
            idx = misc.get_indices(actdata.acdata.id, id_select)[0]
            # Check if selected aircraft is UCO
            if actdata.acdata.uco[idx] == IPaddr[-11:] or 'UCO' in self.cmdslst:  # or actdata.acdata.uco[idx]:

                cmdline = ''

                # Loop over commands
                for cmd, args in zip(self.cmdslst, self.argslst):
                    if cmd == 'EFL':
                        cmd = 'ALT'
                        addfl = True
                    else:
                        addfl = False

                    if cmd == 'UCO':
                        cmdline += id_select + ' ' + cmd + ' ' + IPaddr[-11:]
                    else:
                        cmdline += id_select + ' ' + cmd

                    # Loop over arguments for this command
                    for arg in args:
                        if addfl:
                            cmdline += ' FL' + arg
                        else:
                            cmdline += ' ' + arg

                    cmdline += ' ; '

                cmdline = cmdline[:-3]  # Remove last ' ; '

                # Stack the command line
                console.Console._instance.stack(cmdline)
            else:
                bs.scr.echo(id_select+' not UCO')
        else:
            bs.scr.echo('No aircraft selected')

        # Clear
        self.clear()

        # Empty command line
        console.Console._instance.set_cmdline('')

    @staticmethod
    def exqcmd(cmd, arg=''):
        """
        Function: Execute a command
        Args:
            cmd:    command [str]
            arg:    argument [str]
        Returns: -
        """

        cmd = cmd.strip().upper()
        arg = arg.strip()

        # Selected aircraft
        actdata = bs.net.get_nodedata()
        id_select = console.Console._instance.id_select

        # Check if an aircraft is selected
        if id_select:
            # Command line
            cmdline = id_select + ' ' + cmd + ' ' + arg
            cmdline = cmdline.strip()

            # Stack the command
            console.Console._instance.stack(cmdline)
        else:
            bs.scr.echo('No aircraft selected')

    def clr(self):
        """
        Function: Clear command
        Args: -
        Returns: -
        """

        self.argslst[self.iact] = ['']

        # Set the command line
        self.update_cmdline()

    def cor(self):
        """
        Function: Correct command
        Args: -
        Returns: -
        """

        # Clear
        self.clear()

        # Update the command line
        console.Console._instance.set_cmdline('')
    #
    def setcmd(self, cmd):
        """
        Function: Set a command
        Args:
            cmd:    command [str]
        Returns: -
        """

        cmd = cmd.strip().upper()

        if cmd in self.cmdslst:
            # Get index
            self.iact = self.cmdslst.index(cmd)
        else:
            # Unfinished previous command
            if len(self.cmdslst) != 0 and self.cmdslst[self.iact] not in ['UCO', 'REL'] and self.argslst[self.iact] == [
                '']:
                self.cmdslst[self.iact] = cmd
                self.argslst[self.iact] = ['']
            # Finished previous command
            else:
                # Append new command
                self.cmdslst.append(cmd)
                self.argslst.append([''])

                # Index
                self.iact = len(self.cmdslst) - 1

        # Update command line
        self.update_cmdline()

    def changecmd(self, cmd):
        """
        Function: Change the current command
        Args:
            cmd:    command [str]
        Returns: -
        """

        cmd = cmd.strip().upper()

        # Change command
        self.cmdslst[self.iact] = cmd
        # Clear arguments
        self.argslst[self.iact] = ['']

        # Update command line
        self.update_cmdline()

    def setarg(self, arg, argn):
        """
        Function: Set an argument
        Args:
            arg:    argument [str]
            argn:   argument number (1, 2, ..., n) [int]
        Returns: -
        """

        # Set the argument
        self.argslst[self.iact][argn - 1] = arg.strip()

        # Update command line
        self.update_cmdline()

    def addarg(self, arg):
        """
        Function: Add an argument
        Args:
            arg:    argument [str]
        Returns: -
        """

        # Append argument
        self.argslst[self.iact].append(arg.strip())

        # Update command line
        self.update_cmdline()

    def addchar(self, char):
        """
        Function: Add a character
        Args:
            char:   character [str]
        Returns: -
        """

        # Append character
        self.argslst[self.iact][-1] += char.strip()

        # Update command line
        self.update_cmdline()

    # --------------------------- NORMAL ------------------------

    def start_discovery(self):
        super().start_discovery()
        self.discovery_timer = QTimer()
        self.discovery_timer.timeout.connect(self.discovery.send_request)
        self.discovery_timer.start(3000)

    def stop_discovery(self):
        self.discovery_timer.stop()
        self.discovery_timer = None
        super().stop_discovery()

    def stream(self, name, data, sender_id):
        """
        Function Guiclient stream handler.
        Args:
            name:       Name of the stream [bytes]
            data:       Stream data [dict]
            sender_id:  Sender ID [bytes]
        Returns -

        Created by: Original BlueSky version
        """
        changed = ''
        actdata = self.get_nodedata(sender_id)
        if name == b'ACDATA':
            actdata.setacdata(data)
            changed = name.decode('utf8')
        elif name.startswith(b'ROUTEDATA'):
            actdata.setroutedata(data)
            changed = 'ROUTEDATA'
        elif name == b'TRAILS':
            actdata.settrails(**data)
            changed = name.decode('utf8')

        if sender_id == self.act and changed:
            self.actnodedata_changed.emit(sender_id, actdata, changed)

        super().stream(name, data, sender_id)

    def echo(self, text, flags=None, sender_id=None):
        """
        Function: Overloaded Client.echo function.
        Args:
            text:       Text to echo [str]
            flags:      Flags [int]
            sender_id:  Sender ID [bytes]

        Created by: Original BlueSky version
        """

        sender_data = self.get_nodedata(sender_id)
        sender_data.echo(text, flags)
        # If sender_id is None this is an echo command originating from the gui user, and therefore also meant for the active node
        sender_id = sender_id or self.act
        if sender_id == self.act:
            self.actnodedata_changed.emit(sender_id, sender_data, ('ECHOTEXT',))

    def event(self, name, data, sender_id):
        """
        Function: Guiclient event handler.
        Args:
            name:       Name of the event [bytes]
            data:       The data [dict]
            sender_id:  Sender ID [bytes]
        Returns: -

        Created by: Original BlueSky version

        Edited by: Mitchell de Keijzer
        Date: 07-04-2022, 04-05-2022
        Changed:
            1) added the MAP flag to b'DISPLAYFLAG
            2) eventname b'TIDCOMMANDS' added
        """

        sender_data = self.get_nodedata(sender_id)
        data_changed = []
        if name == b'RESET':
            sender_data.clear_scen_data()
            data_changed = list(UPDATE_ALL)
            # Clear the loaded maps
            loaded_maps.clear()

        elif name == b'SHAPE':
            sender_data.update_poly_data(**data)
            data_changed.append('SHAPE')

        elif name == b'COLOR':
            sender_data.update_color_data(**data)
            if 'polyid' in data:
                data_changed.append('SHAPE')

        elif name == b'DEFWPT':
            sender_data.defwpt(**data)
            data_changed.append('CUSTWPT')

        elif name == b'DISPLAYFLAG':
            sender_data.setflag(**data)

            if data['flag'] == 'ATCMODE':
                data_changed.append('ATCMODE')
                # Get IP-address
                IP = socket.gethostbyname(socket.gethostname())
                # Connect the IP-address to the ATC mode
                bs.stack.stack("ATCIP "+data['args']+" "+IP[-11:])

            elif data['flag'] == 'GUITRAFDATA':
                data_changed.append('GUITRAFDATA')
                sender_data.guitrafdata['cmd'] = data['args']['cmd']
                sender_data.guitrafdata['data'] = data['args']['data']

            elif data['flag'] == 'MAP':
                # Check if file exists
                if not findfile(data['args']+'.scn', 'scenario/LVNL/Maps'):
                    self.echo('MAPTOGGLE MAP: File not found')
                    return

                data_changed.append('MAP')

                # Check if map is already loaded, and therefore should be deleted
                if data['args'] in loaded_maps:
                    loaded_maps.remove(data['args'])
                    name, shape, coordinate, color = load_maplines(data['args'])
                    for d in range(len(name)):
                        sender_data.update_poly_data(name[d], shape[d], None, None)

                # Load map
                else:
                    loaded_maps.append(data['args'])
                    if sender_data.show_maplines:
                        name, shape, coordinate, color = load_maplines(data['args'])
                        for i in range(len(name)):
                            sender_data.update_poly_data(name[i], shape[i], coordinate[i], color[i])

        elif name == b'ECHO':
            data_changed.append('ECHOTEXT')

        elif name == b'PANZOOM':
            sender_data.panzoom(**data)
            data_changed.append('PANZOOM')

        elif name == b'SIMSTATE':
            sender_data.siminit(**data)
            data_changed = list(UPDATE_ALL)

        elif name == b'TIDCOMMANDS':
            sender_data.setflag(**data)
            # --- TID commands ---
            if data['flag'] == 'EXQ':
                self.exq()
            if data['flag'] == 'CMD':
                self.setcmd(data['args'])
            if data['flag'] == 'CHCMD':
                self.changecmd(data['args'])
            if data['flag'] == 'ARG':
                self.addarg(data['args'])
            if data['flag'] == 'SETARG':
                self.setarg(data['args'], 1)
            if data['flag'] == 'CHAR':
                self.addchar(data['args'])
            if data['flag'] == 'COR':
                self.cor()
            if data['flag'] == 'CLR':
                self.clr()
        else:
            super().event(name, data, sender_id)

        if sender_id == self.act and data_changed:
            self.actnodedata_changed.emit(sender_id, sender_data, data_changed)

    def actnode_changed(self, newact):
        self.actnodedata_changed.emit(newact, self.get_nodedata(newact), UPDATE_ALL)

    def get_nodedata(self, nodeid=None):
        nodeid = nodeid or self.act
        if not nodeid:
            return self.ref_nodedata

        data = self.nodedata.get(nodeid)
        if not data:
            # If this is a node we haven't addressed yet: create dataset and
            # request node settings
            self.nodedata[nodeid] = data = nodeData()
            self.send_event(b'GETSIMSTATE', target=nodeid)

        return data


class nodeData:
    def __init__(self, route=None):
        # Stack window
        self.echo_text = ''
        self.stackcmds = dict()
        self.stacksyn = dict()

        # Display pan and zoom
        self.pan = [0.0, 0.0]
        self.zoom = 1.0
        self.screenrange = None

        self.naircraft = 0
        self.acdata = ACDataEvent()
        self.routedata = RouteDataEvent()

        # GUI traffic data event
        self.guitrafdata = {'cmd': None, 'data': None}

        # Per-scenario data
        self.clear_scen_data()

        # Network route to this node
        self._route = route

    def setacdata(self, data):
        self.acdata = ACDataEvent(data)
        self.naircraft = len(self.acdata.lat)

    def setroutedata(self, data):
        self.routedata = RouteDataEvent(data)

    def settrails(self, swtrails, traillat0, traillon0, traillat1, traillon1):
        if not swtrails:
            self.traillat0 = []
            self.traillon0 = []
            self.traillat1 = []
            self.traillon1 = []
        else:
            self.traillat0.extend(traillat0)
            self.traillon0.extend(traillon0)
            self.traillat1.extend(traillat1)
            self.traillon1.extend(traillon1)

    def clear_scen_data(self):
        # Clear all scenario-specific data for sender node
        self.polys = dict()
        self.dotted = dict()
        self.dashed = dict()
        self.points = dict()
        self.custacclr = dict()
        self.custgrclr = dict()
        self.custwplbl = ''
        self.custwplat = np.array([], dtype=np.float32)
        self.custwplon = np.array([], dtype=np.float32)

        self.linemap = dict()
        self.dashmap = dict()
        self.dotmap = dict()
        self.pointmap = dict()

        # Filteralt settings
        self.filteralt = False

        # Create trail data
        self.traillat0 = []
        self.traillon0 = []
        self.traillat1 = []
        self.traillon1 = []

        # Reset transition level
        self.translvl = 4500.*ft

        # Display flags
        self.show_coast    = True
        self.show_traf     = True
        self.show_trail    = True
        self.show_pz       = False
        self.show_fir      = True
        self.show_lbl      = 2
        self.show_poly     = 1  # 0=invisible, 1=outline, 2=fill
        self.ssd_all       = False
        self.ssd_conflicts = False
        self.ssd_ownship   = set()
        self.atcmode       = settings.atc_mode.upper()
        self.show_maplines   = True
        # Display flags based on ATC mode
        self.set_atcmode(settings.atc_mode.upper())

    def siminit(self, shapes, **kwargs):
        self.__dict__.update(kwargs)
        for shape in shapes:
            self.update_poly_data(**shape)

    def panzoom(self, pan=None, zoom=None, absolute=True, screenrange=None):
        """
        Function: Pan or zoom the radar screen
        Args:
            pan:            Pan coordinates [tuple]
            zoom:           Zoom factor [float]
            absolute:       Absolute zoom switch [bool]
            screenrange:    Range of the screen [float]
        Returns: -

        Created by: Original BlueSky version
        """
        if pan:
            if absolute:
                self.pan  = list(pan)
            else:
                self.pan[0] += pan[0]
                self.pan[1] += pan[1]
        if zoom:
            self.zoom = zoom * (1.0 if absolute else self.zoom)
        if screenrange:
            self.screenrange = screenrange

    def update_color_data(self, color, acid=None, groupid=None, polyid=None):
        """
        Function: Update the color
        Args:
            color:      Color [tuple]
            acid:       Aircraft ID [str]
            groupid:    Group ID [str]
            polyid:     Polygon ID [str]
        Returns: -

        Created by: Original BlueSky version
        """

        if acid:
            self.custacclr[acid] = tuple(color)
        elif groupid:
            self.custgrclr[groupid] = tuple(color)
        else:
            # Polys
            if polyid in self.polys:
                contourbuf, fillbuf, colorbuf = self.polys.get(polyid)
                color = tuple(color) + (255,)
                colorbuf = np.array(len(contourbuf) // 2 * color, dtype=np.uint8)
                self.polys[polyid] = (contourbuf, fillbuf, colorbuf)
            # Dashed lines
            elif polyid in self.dashed:
                contourbuf, fillbuf, colorbuf = self.dashed.get(polyid)
                color = tuple(color) + (255,)
                colorbuf = np.array(len(contourbuf) // 2 * color, dtype=np.uint8)
                self.dashed[polyid] = (contourbuf, fillbuf, colorbuf)
            # Dotted lines
            elif polyid in self.dotted:
                contourbuf, fillbuf, colorbuf = self.dotted.get(polyid)
                color = tuple(color) + (255,)
                colorbuf = np.array(len(contourbuf) // 2 * color, dtype=np.uint8)
                self.dotted[polyid] = (contourbuf, fillbuf, colorbuf)
            # Points
            elif polyid in self.points:
                contourbuf, fillbuf, colorbuf = self.points.get(polyid)
                color = tuple(color) + (255,)
                colorbuf = np.array(len(contourbuf) // 2 * color, dtype=np.uint8)
                self.points[polyid] = (contourbuf, fillbuf, colorbuf)

    def update_poly_data(self, name, shape='', coordinates=None, color=None):
        """
        Function: Update the data for map lines/points
        Args:
            name        :   name of the line [str]
            shape       :   shape of the line (normal/dotted/dashed/point) [str]
            coordinates :   lat/lon coordinates [list]
            color       :   color code [tuple]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 7-4-2022
        """

        if coordinates is not None:
            # We're either updating a polygon, or deleting it. In both cases
            # we remove the current one.
            self.polys.pop(name, None)
            self.dotted.pop(name, None)
            self.dashed.pop(name, None)
            self.points.pop(name, None)

            # Break up polyline list of (lat,lon)s into separate line segments
            if shape == 'LINE' or shape[:4] == 'POLY':
                # Input data is list or array: [lat0,lon0,lat1,lon1,lat2,lon2,lat3,lon3,..]
                newdata = np.array(coordinates, dtype=np.float32)

            elif shape == 'BOX':
                # Convert box coordinates into polyline list
                # BOX: 0 = lat0, 1 = lon0, 2 = lat1, 3 = lon1 , use bounding box
                newdata = np.array([coordinates[0], coordinates[1],
                                 coordinates[0], coordinates[3],
                                 coordinates[2], coordinates[3],
                                 coordinates[2], coordinates[1]], dtype=np.float32)

            elif shape == 'CIRCLE':
                # Input data is latctr,lonctr,radius[nm]
                # Convert circle into polyline list

                # Circle parameters
                Rearth = 6371000.0             # radius of the Earth [m]
                numPoints = 72                 # number of straight line segments that make up the circrle

                # Inputs
                lat0 = coordinates[0]              # latitude of the center of the circle [deg]
                lon0 = coordinates[1]              # longitude of the center of the circle [deg]
                Rcircle = coordinates[2] * 1852.0  # radius of circle [NM]

                # Compute flat Earth correction at the center of the experiment circle
                coslatinv = 1.0 / np.cos(np.deg2rad(lat0))

                # compute the x and y coordinates of the circle
                angles    = np.linspace(0.0, 2.0 * np.pi, numPoints)   # ,endpoint=True) # [rad]

                # Calculate the circle coordinates in lat/lon degrees.
                # Use flat-earth approximation to convert from cartesian to lat/lon.
                latCircle = lat0 + np.rad2deg(Rcircle * np.sin(angles) / Rearth)  # [deg]
                lonCircle = lon0 + np.rad2deg(Rcircle * np.cos(angles) * coslatinv / Rearth)  # [deg]

                # make the data array in the format needed to plot circle
                newdata = np.empty(2 * numPoints, dtype=np.float32)  # Create empty array
                newdata[0::2] = latCircle  # Fill array lat0,lon0,lat1,lon1....
                newdata[1::2] = lonCircle

            elif shape == 'DOTTEDLINE' or shape == 'DASHEDLINE':
                newdata = np.array(coordinates, dtype=np.float32)

            elif shape == 'POINT':
                newdata = np.array(coordinates, dtype=np.float32)  # [lat, lon]

            # Create polygon contour buffer
            # Distinguish between an open and a closed contour.
            # If this is a closed contour, add the first vertex again at the end
            # and add a fill shape
            if shape == 'DOTTEDLINE' or shape == 'DASHEDLINE':
                contourbuf = np.array(newdata, dtype=np.float32)
                fillbuf = np.array([], dtype=np.float32)
            elif shape[-4:] == 'LINE':
                contourbuf = np.empty(2 * len(newdata) - 4, dtype=np.float32)
                contourbuf[0::4]   = newdata[0:-2:2]  # lat
                contourbuf[1::4]   = newdata[1:-2:2]  # lon
                contourbuf[2::4] = newdata[2::2]  # lat
                contourbuf[3::4] = newdata[3::2]  # lon
                fillbuf = np.array([], dtype=np.float32)
            elif shape == 'POINT':
                contourbuf = np.array(newdata, dtype=np.float32)
                fillbuf = np.array([], dtype=np.float32)
            else:
                contourbuf = np.empty(2 * len(newdata), dtype=np.float32)
                contourbuf[0::4]   = newdata[0::2]  # lat
                contourbuf[1::4]   = newdata[1::2]  # lon
                contourbuf[2:-2:4] = newdata[2::2]  # lat
                contourbuf[3:-3:4] = newdata[3::2]  # lon
                contourbuf[-2:]    = newdata[0:2]
                pset = PolygonSet()
                pset.addContour(newdata)
                fillbuf = np.array(pset.vbuf, dtype=np.float32)

            # Define color buffer for outline
            defclr = tuple(color or palette.polys) + (255,)
            colorbuf = np.array(len(contourbuf) // 2 * defclr, dtype=np.uint8)

            # Store new or updated polygon by name, and concatenated with the
            # other polys
            if shape == 'POINT':
                self.points[name] = (contourbuf, fillbuf, colorbuf)
            elif shape == 'DOTTEDLINE':
                self.dotted[name] = (contourbuf, fillbuf, colorbuf)
            elif shape == 'DASHEDLINE':
                self.dashed[name] = (contourbuf, fillbuf, colorbuf)
            else:
                self.polys[name] = (contourbuf, fillbuf, colorbuf)

        # If no coordinates are given, it means that the shape must be switched off by deleting the shape
        else:
            if name in self.points:
                del self.points[name]
            elif name in self.dotted:
                del self.dotted[name]
            elif name in self.dashed:
                del self.dashed[name]
            elif name in self.polys:
                del self.polys[name]

    def defwpt(self, name, lat, lon):
        self.custwplbl += name[:10].ljust(10)
        self.custwplat = np.append(self.custwplat, np.float32(lat))
        self.custwplon = np.append(self.custwplon, np.float32(lon))

    def setflag(self, flag, args=None):
        # Switch/toggle/cycle radar screen features e.g. from SWRAD command
        if flag == 'SYM':
            # For now only toggle PZ
            self.show_pz = not self.show_pz
        # Coastlines
        elif flag == 'GEO':
            self.show_coast = not self.show_coast

        # FIR boundaries
        elif flag == 'FIR':
            self.show_fir = not self.show_fir

        # Airport: 0 = None, 1 = Large, 2= All
        elif flag == 'APT':
            self.show_apt = not self.show_apt

        # Airport details (runways, taxiways, pavements)
        elif flag == 'APTDETAILS':
            self.show_aptdetails = not self.show_aptdetails

        # Waypoint: 0 = None, 1 = VOR, 2 = also WPT, 3 = Also terminal area wpts
        elif flag == 'VOR' or flag == 'WPT' or flag == 'WP' or flag == 'NAV':
            self.show_wpt = not self.show_wpt

        # Satellite image background on/off
        elif flag == 'SAT':
            self.show_map = not self.show_map

        # Satellite image background on/off
        elif flag == 'TRAF':
            self.show_traf = not self.show_traf

        elif flag == 'TRAIL' or flag == 'TRAILS':
            self.show_trail = not self.show_trail

        elif flag == 'POLY':
            self.show_poly = 0 if self.show_poly == 2 else self.show_poly + 1

        elif flag == 'LABEL':
            # Cycle aircraft label through detail level 0,1,2
            if args==None:
                self.show_lbl = (self.show_lbl+1)%3

            # Or use the argument if it is an integer
            else:
                try:
                    self.show_lbl = min(2,max(0,int(args)))
                except:
                    self.show_lbl = (self.show_lbl + 1) % 3

        elif flag == 'SSD':
            self.show_ssd(args)

        elif flag == 'FILTERALT':
            # First argument is an on/off flag
            if args[0]:
                self.filteralt = args[1:]
            else:
                self.filteralt = False

        elif flag == 'HISTORY':
            self.show_histsymb = not self.show_histsymb

        elif flag == 'ATCMODE':
            # Set ATC mode
            self.atcmode = args
            settings.atc_mode = args
            # Load new palette
            palette.init()
            # Display flags
            self.set_atcmode(args)

        elif flag == 'MAPALL':
            self.show_maplines = not self.show_maplines

    def echo(self, text='', flags=0):
        if text:
            self.echo_text += ('\n' + text)

    def show_ssd(self, arg):
        if 'ALL' in arg:
            self.ssd_all      = True
            self.ssd_conflicts = False
        elif 'CONFLICTS' in arg:
            self.ssd_all      = False
            self.ssd_conflicts = True
        elif 'OFF' in arg:
            self.ssd_all      = False
            self.ssd_conflicts = False
            self.ssd_ownship = set()
        else:
            remove = self.ssd_ownship.intersection(arg)
            self.ssd_ownship = self.ssd_ownship.union(arg) - remove

    def set_atcmode(self, atcmode):
        """
        Function: Set the display properties for the ATC mode
        Args:
            atcmode:    ATC mode [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 7-2-2022
        """

        if atcmode.upper() == 'APP':
            self.show_map = False
            self.show_coast = False
            self.show_histsymb = True
            self.show_aptdetails = False
            self.show_wpt = 1
            self.show_wptlbl = False
            self.show_apt = 0
            self.show_aptlbl = False
        elif atcmode.upper() == 'ACC':
            self.show_map = False
            self.show_coast = False
            self.show_histsymb = True
            self.show_aptdetails = False
            self.show_wpt = 1
            self.show_wptlbl = False
            self.show_apt = 0
            self.show_aptlbl = False
        elif atcmode.upper() == 'TWR':
            self.show_map = False
            self.show_coast = False
            self.show_histsymb = False
            self.show_aptdetails = True
            self.show_wpt = 1
            self.show_wptlbl = False
            self.show_apt = 0
            self.show_aptlbl = False
        else:
            self.show_map = True
            self.show_coast = True
            self.show_histsymb = False
            self.show_aptdetails = True
            self.show_wpt = 1
            self.show_wptlbl = True
            self.show_apt = 1
            self.show_aptlbl = True

def getIPAddresses():
    from ctypes import Structure, windll, sizeof
    from ctypes import POINTER, byref
    from ctypes import c_ulong, c_uint, c_ubyte, c_char
    MAX_ADAPTER_DESCRIPTION_LENGTH = 128
    MAX_ADAPTER_NAME_LENGTH = 256
    MAX_ADAPTER_ADDRESS_LENGTH = 11
    class IP_ADDR_STRING(Structure):
        pass
    LP_IP_ADDR_STRING = POINTER(IP_ADDR_STRING)
    IP_ADDR_STRING._fields_ = [
        ("next", LP_IP_ADDR_STRING),
        ("ipAddress", c_char * 16),
        ("ipMask", c_char * 16),
        ("context", c_ulong)]
    class IP_ADAPTER_INFO (Structure):
        pass
    LP_IP_ADAPTER_INFO = POINTER(IP_ADAPTER_INFO)
    IP_ADAPTER_INFO._fields_ = [
        ("next", LP_IP_ADAPTER_INFO),
        ("comboIndex", c_ulong),
        ("adapterName", c_char * (MAX_ADAPTER_NAME_LENGTH + 4)),
        ("description", c_char * (MAX_ADAPTER_DESCRIPTION_LENGTH + 4)),
        ("addressLength", c_uint),
        ("address", c_ubyte * MAX_ADAPTER_ADDRESS_LENGTH),
        ("index", c_ulong),
        ("type", c_uint),
        ("dhcpEnabled", c_uint),
        ("currentIpAddress", LP_IP_ADDR_STRING),
        ("ipAddressList", IP_ADDR_STRING),
        ("gatewayList", IP_ADDR_STRING),
        ("dhcpServer", IP_ADDR_STRING),
        ("haveWins", c_uint),
        ("primaryWinsServer", IP_ADDR_STRING),
        ("secondaryWinsServer", IP_ADDR_STRING),
        ("leaseObtained", c_ulong),
        ("leaseExpires", c_ulong)]
    GetAdaptersInfo = windll.iphlpapi.GetAdaptersInfo
    GetAdaptersInfo.restype = c_ulong
    GetAdaptersInfo.argtypes = [LP_IP_ADAPTER_INFO, POINTER(c_ulong)]
    adapterList = (IP_ADAPTER_INFO * 10)()
    buflen = c_ulong(sizeof(adapterList))
    rc = GetAdaptersInfo(byref(adapterList[0]), byref(buflen))
    if rc == 0:
        for a in adapterList:
            adNode = a.ipAddressList
            while True:
                ipAddr = adNode.ipAddress
                if ipAddr:
                    yield ipAddr
                adNode = adNode.contents
                # adNode = adNode.next
                if not adNode:
                    break


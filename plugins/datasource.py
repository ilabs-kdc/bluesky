""" Feed aircraft states data to simulation from data source """

import os
import numpy as np
import bluesky as bs
from bluesky import core, stack
from bluesky.tools import livetraffic, misc, vemmisread
from bluesky.stack import simstack

### Initialization function of the plugin
def init_plugin():
    ''' Plugin initialisation function. '''
    # Instantiate class
    datasource = DataSource()

    # Configuration parameters
    config = {
        # The name of the plugin
        'plugin_name':     'DATASOURCE',

        # The type of the plugin
        'plugin_type':     'sim',
        }

    return config


"""
Classes
"""


class DataSource(core.Entity):
    """
    Class definition: Take data from data source and feed to simulation
    Methods:
        reset():            Reset variables
        setreplay():        Replay scenario from data source
        setlive():          Load live data into BlueSky
        setinitial():       Take initial aircraft positions from data source
        update_trackdata(): Update the track data for the current simulation time

    Created by: Bob van Dillen
    Date: 14-1-2022
    """

    def __init__(self):
        super().__init__()

        self.sourcenames = []
        self.sourceupdate = np.array([], dtype=np.bool_)
        self.datasource = []

    def reset(self):
        """
        Function: Reset variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        super().reset()

        self.sourcenames = []
        self.sourceupdate = np.array([], dtype=np.bool_)
        self.datasource = []

    @stack.command(name='SOURCES',)
    def getsources(self):
        """
        Function: Get the active sources
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 1-2-2022
        """

        echostr = 'Current data sources: '
        for source in self.sourcenames:
            echostr += source+', '
        echostr = echostr.strip(', ')
        bs.scr.echo(echostr)

    @stack.command(name='REPLAY', brief='REPLAY DATATYPE FOLDER (DATE [dd-mm-yyyy] TIME [HH:MM:SS])')
    def setreplay(self, datatype: 'txt', folder: 'txt', date0: 'txt' = '', time0: 'txt' = ''):
        """
        Function: Replay scenario from data source
        Args:
            datatype:   data type [str]
            folder:     folder name [str]
            date0:      start date [str]
            time0:      start time [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Convert inputs
        datatype = datatype.upper()
        folder = folder.lower()
        datapath = os.getcwd() + "\\scenario\\" + folder

        # --------------- Check inputs ---------------
        # Data type
        if datatype not in ['VEMMIS']:
            return False, 'REPLAY: Data type not supported'

        # Other inputs
        succes, message = check_inputs(path=datapath, files=datatype, date=date0, time=time0)
        if not succes:
            return False, 'REPLAY: ' + message

        # --------------- Access data ---------------
        # Get data type
        if datatype == 'VEMMIS':
            self.sourcenames.append('VEMMIS-'+folder)
            self.sourceupdate = np.append(self.sourceupdate, True)
            self.datasource.append(vemmisread.VEMMISSource())

        # Get commands data
        commands, commandstime = self.datasource[-1].replay(datapath, date0, time0)
        simstack.stack_commands(commandstime, commands)

    @stack.command(name='PLAYBACK', brief='PLAYBACK DATATYPE FOLDER (DATE [dd-mm-yyyy] TIME [HH:MM:SS])')
    def setplayback(self, datatype: str, folder: str = '', date0: str = '', time0: str = ''):
        """
        Function: Take initial aircraft positions from data source
        Args:
            datatype:   data type [str]
            folder:     folder name [str]
            date0:      start date [str]
            time0:      start time [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Convert inputs
        datatype = datatype.upper()
        folder = folder.lower()
        datapath = os.getcwd() + "\\scenario\\" + folder

        # --------------- Check inputs ---------------
        # Data type
        if datatype not in ['VEMMIS']:
            return False, 'PLAYBACK: Data type not supported'

        # Other inputs
        succes, message = check_inputs(path=datapath, files=datatype, date=date0, time=time0)
        if not succes:
            return False, 'PLAYBACK: ' + message

        # --------------- Access data ---------------
        # Get data type
        if datatype == 'VEMMIS':
            self.sourcenames.append('VEMMIS-'+folder)
            self.sourceupdate = np.append(self.sourceupdate, False)
            self.datasource.append(vemmisread.VEMMISSource())

        # Get commands data
        commands, commandstime = self.datasource[-1].playback(datapath, date0, time0)
        simstack.stack_commands(commandstime, commands)

    @stack.command(name='LIVE', brief='LIVE DATATYPE')
    def setlive(self, datatype: str):
        """
        Function: Load live data into BlueSky
        Args:
            datatype:   data type [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 15-1-2022
        """

        # --------------- Check inputs ---------------
        # Data type
        if datatype.upper() not in ['OPENSKY']:
            return False, 'LIVE: Data type not supported'

        # --------------- Access data ---------------
        # Get data type
        if datatype.upper() == 'OPENSKY':
            self.sourcenames.append('OPENSKY')
            self.sourceupdate = np.append(self.sourceupdate, True)
            self.datasource.append(livetraffic.OpenSkySource())

        # Get commands data
        commands, commandstime = self.datasource[-1].live()
        simstack.stack_commands(commandstime, commands)

    @core.timed_function(name='datafeed', dt=0.5)
    def update_trackdata(self):
        """
        Function: Update the track data for the current simulation time
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        # Indices of data sources that need to provide updates
        isourceupdate = np.nonzero(self.sourceupdate)[0]

        # Check if update is needed
        if len(isourceupdate) == 0:
            return

        # Create commands
        cmds = []

        # Create track data
        trackdata = {'id': [],
                     'lat': np.array([]),
                     'lon': np.array([]),
                     'hdg': np.array([]),
                     'alt': np.array([]),
                     'gs': np.array([])}

        # Get data for all data sources
        # Indices of the sources that need to provide updates
        for i in isourceupdate:
            running, cmdsi, ids, lat, lon, hdg, alt, gs = self.datasource[i].update_trackdata(bs.sim.simt)

            # Add to commands
            cmds += cmdsi

            # Add to track data
            trackdata['id'] += ids
            trackdata['lat'] = np.append(trackdata['lat'], lat)
            trackdata['lon'] = np.append(trackdata['lon'], lon)
            trackdata['hdg'] = np.append(trackdata['hdg'], hdg)
            trackdata['alt'] = np.append(trackdata['alt'], alt)
            trackdata['gs'] = np.append(trackdata['gs'], gs)

            # Check status
            if not running:
                self.sourcenames.pop(i)
                self.sourceupdate = np.delete(self.sourceupdate, i)
                self.datasource.pop(i)

        # Send trackdata
        if len(trackdata['id']) > 0:
            bs.traf.trafdatafeed.trackdata = trackdata

        # Stack commands
        for cmd in cmds:
            bs.stack.stack(cmd)


"""
Static functions
"""


def check_inputs(path=None, files=None, date=None, time=None):
    """
    Function: Check if inputs are valid
    Args:
        path:       folder input [str]
        files:      files check (insert data type) [str]
        date:       date [str]
        time:       time [str]
    Returns:
        True/False: Inputs are correct/incorrect [bool]
        string:     Message [str]

    Created by: Bob van Dillen
    Date: 26-1-2022
    """

    # Check folder input
    if path:
        if not os.path.isdir(path):
            path = path.replace("\\scenario\\", "\\scenario\\LVNL\\Data\\")
            if not os.path.isdir(path):
                return False, 'Folder does not exist'

    # Check files
    if files and path:
        if not files_check(files, path):
            return False, 'Folder does not contain all required files'

    # Check date input
    if date:
        date = date.split('-')
        if len(date) != 3:
            return False, 'Invalid date'
        for item in date:
            if not item.isnumeric():
                return False, 'Invalid date'

    # Check time input
    if time:
        time = time.split(':')
        if len(time) != 3:
            return False, 'Invalid time'
        for item in time:
            if not item.isnumeric():
                return False, 'Invalid time'

    return True, ''


def files_check(datatype, datapath):
    """
    Function: Check if the folder contains the required files
    Args:
        datatype:   data type [str]
        datapath:   path to the folder [str]
    Returns:
        True/False: True if required files are present, else False [bool]

    Created by: Bob van Dillen
    Date: 14-1-2022
    """

    file_array = np.array([])

    if datatype.upper() == 'VEMMIS':
        for root, dirs, files in os.walk(datapath):
            for file in files:
                if file.upper().startswith('FLIGHTS'):
                    file_array = np.append(file_array, 'FLIGHTS')
                elif file.upper().startswith('FLIGHTTIMES'):
                    file_array = np.append(file_array, 'FLIGHTTIMES')
                elif file.upper().startswith('TRACK'):
                    file_array = np.append(file_array, 'TRACK')

        if len(file_array) == 3 and len(np.unique(file_array)) == 3:
            return True

    return False

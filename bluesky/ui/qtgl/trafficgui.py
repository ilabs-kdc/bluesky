"""
Python file to store and process GUI traffic variables

Created by: Bob van Dillen
Date: 23-99-2022
"""

import numpy as np
import bluesky as bs
from bluesky import settings

ac_size = settings.ac_size
text_size = settings.text_size

class TrafficData:
    """
    Definition: Store and process GUI traffic data
    Methods:
        actdata_changed():      Process incoming traffic data
        set_trafficdata():      Process incoming events
        update_trafficdata():   Update the GUI traffic variables

    Created by: Bob van Dillen
    Date: 23-9-2022
    """
    def __init__(self):
        # Previous callsigns
        self.id_prev = []

        # Variables
        self.labelpos       = np.array([])
        self.leaderlinepos  = np.array([])
        self.mlabel         = np.array([])
        self.mlabelpos      = np.array([])
        self.rel            = np.array([])
        self.ssrlabel       = np.array([])
        self.tracklabel     = np.array([])
        self.uco            = np.array([])

        # Defaults
        self.labelpos_default       = np.array([50., 0.])
        self.leaderlinepos_default  = np.array([0., 0., 50., 0.])
        self.mlabel_default         = False
        self.mlabelpos_default      = np.array([-8 * 0.8 * text_size - ac_size, 0.5 * ac_size])
        self.rel_default            = False
        self.ssrlabel_default       = False
        self.tracklabel_default     = True
        self.uco_default            = False

        bs.net.actnodedata_changed.connect(self.actdata_changed)

    def actdata_changed(self, nodeid, nodedata, changed_elems):
        """
        Function: Process incoming traffic data
        Args:
            nodeid:         ID of the Node [bytes]
            nodedata:       The Node data [class]
            changed_elems:  The changed elements [list]
        Returns: -

        Created by: Bob van Dillen
        Date: 23-9-2022
        """

        if 'ACDATA' in changed_elems:
            self.update_trafficdata(nodedata)
        if 'GUITRAFDATA' in changed_elems:
            self.set_trafficdata(nodedata)

    def set_trafficdata(self, data):
        """
        Function Process incoming events
        Args:
            data:   New data [class]
        Returns: -

        Created by: Bob van Dillen
        Date: 23-9-2022
        """

        if data.guitrafdata['cmd'] == 'TRACKLABEL':
            idx = data.acdata.id.index(data.guitrafdata['data'])
            self.tracklabel[idx] = not self.tracklabel[idx]

    def initial_labelpos(self, data, i):
        """
        Function: Compute the offset for the initial label position
        Args:
            data:   aircraft data [dict]
            i:      index for data [int]
        Returns:
            labelpos:   offsets x and y [list]

        Created by: Ajay Kumbhar
        Date:

        Note: Enable data.arr conditions only for GMPEOR scenario
        """

        #   #   Enable data.rwy for normal cases
        if data.rwy[i] in ['18R', '18R_E']:
            labelpos = np.array([-125, 0])  # -125
        else:
            labelpos = np.array([50, 0])

        #   #   Enable data.arr only for GMPEOR scenario
        # if data.arr[i] in ['ATP18R', 'RIV18R', 'RIV18REOR', 'SUG18R', 'SUG18REOR']:
        #     labelpos = [-150, 0]  # -125
        # else:
        #     labelpos = [80, 0]  # 50  #75 for R indication

        return labelpos

    def initial_micropos(self, data, i):
        """
        Function: Compute the offset for the initial microlabel position
        Args:
            data:   aircraft data [dict]
            i:      index for data [int]
        Returns:
            labelpos:   offsets x and y [list]

        Created by: Ajay Kumbhar
        Date:

        Note: Enable data.arr conditions only for GMPEOR scenario
        """
        ac_size = settings.ac_size
        text_size = settings.text_size

        #   #   Enable data.rwy for normal cases
        if data.rwy[i] in ['18C', '18C_E']:
            mlabelpos = [2 * 0.8 * text_size - ac_size, 0.5 * ac_size]
        else:
            mlabelpos = [-8 * 0.8 * text_size - ac_size, 0.5 * ac_size]  # -3

        #   #   Enable data.arr only for GMPEOR scenario
        # if data.arr[i] in ['ATP18C', 'ATP18CEOR', 'RIV18C', 'SUG18C']:
        #     mlabelpos = [2 * 0.8 * text_size - ac_size, 0.5 * ac_size]  # 2   #0.5-y
        # else:
        #     mlabelpos = [-8 * 0.8 * text_size - ac_size, 0.5 * ac_size]  # -3

        return mlabelpos

    def update_trafficdata(self, actdata):
        """
        Function: Update the GUI traffic variables
        Args:
            actdata:    New data [class]
        Returns: -

        Created by: Bob van Dillen
        Date: 23-9-2022
        """

        data = actdata.acdata

        # Check if aircraft are created or deleted
        if data.id != self.id_prev:

            # Get callsigns of created aircraft
            idcreate = np.setdiff1d(data.id, self.id_prev).tolist()

            # Loop over GUI traffic variables
            for varname in self.__dict__:

                # Check if it is a GUI traffic variables
                if varname in ['id_prev'] or varname[-8:] == '_default':
                    continue

                # Get variable data
                var = self.__dict__[varname]

                # Check for list
                if isinstance(var, list):
                    # Create new variable data
                    varnext = [0]*len(data.id)
                else:
                    # Check shape default value
                    if isinstance(self.__dict__[varname+'_default'], np.ndarray):
                        # Create new variable data
                        varnext = np.zeros((len(data.id), len(self.__dict__[varname+'_default'])))
                    else:
                        # Create new variable data
                        varnext = np.zeros(len(data.id))

                # Loop over aircraft
                for acid in data.id:
                    # Get current index
                    idx = data.id.index(acid)
                    # Check if aircraft is created
                    if acid in idcreate:
                        # Set to default value
                        if varname == 'labelpos':
                            varnext[idx] = self.initial_labelpos(data, idx)
                        elif varname == 'leaderlinepos':
                            offset = self.initial_labelpos(data, idx)
                            varnext[idx] = leaderline_vertices(actdata, offset[0], offset[1], idx)
                        elif varname == 'mlabelpos':
                            varnext[idx] = self.initial_micropos(data, idx)
                        else:
                            varnext[idx] = self.__dict__[varname+'_default']
                    else:
                        # Get previous index
                        idx_prev = self.id_prev.index(acid)
                        # Set to previous value
                        varnext[idx] = var[idx_prev]

                # Set new variable data
                self.__dict__[varname] = varnext

            # Save callsigns
            self.id_prev = data.id


"""
Static Functioms
"""


def leaderline_vertices(actdata, offsetx, offsety, i):
    """
    Function: Compute the vertices for the leader line
    Args:
        actdata:    node data [class]
        offsetx:    label offset x pixel coordinates [int]
        offsety:    label offset y pixel coordinates [int]
    Returns: -

    Created by: Bob van Dillen
    Date: 23-2-2022
    """

    # Sizes
    ac_size = settings.ac_size
    text_size = settings.text_size
    text_width = text_size
    text_height = text_size * 1.2307692307692308

    # APP
    if actdata.atcmode == 'APP':
        block_size = (4*text_height, 7*text_width)
    # ACC
    elif actdata.atcmode == 'ACC':
        block_size = (4*text_height, 8*text_width)
    # TWR
    else:
        block_size = (3*text_height, 8*text_width)

    # Compute the angle
    angle = np.arctan2(offsety, offsetx)

    if not actdata.acdata.tracklbl[i]:
        vertices = [0, 0, 0, 0]
    # Label is on top of aircaft symbol
    elif -block_size[1] <= offsetx <= 0 and -text_height <= offsety <= 3*text_height:
        vertices = [0, 0, 0, 0]
    # Label is to the right of the aircraft symbol
    elif offsetx >= 0:
        vertices = [ac_size*np.cos(angle), ac_size*np.sin(angle), offsetx, offsety]
    # Label is above the aircraft symbol
    elif offsetx >= -block_size[1] and offsety >= 0:
        vertices = [ac_size*np.cos(angle), ac_size*np.sin(angle), offsetx+0.5*block_size[1], offsety-3*text_height]
    # Label is below the aircraft symbol
    elif offsetx >= -block_size[1] and offsety <= 0:
        vertices = [ac_size*np.cos(angle), ac_size*np.sin(angle), offsetx+0.5*block_size[1], offsety+text_height]
    # Label is to the left of the aircraft sym
    elif offsetx < 0:
        vertices = [ac_size*np.cos(angle), ac_size*np.sin(angle), offsetx+block_size[1], offsety]
    # For safety every other situation
    else:
        vertices = [0, 0, 0, 0]

    return vertices

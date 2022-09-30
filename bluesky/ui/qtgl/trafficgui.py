"""
Python file to store and process GUI traffic variables

Created by: Bob van Dillen
Date: 23-99-2022
"""

import numpy as np
import bluesky as bs


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
        self.rel            = np.array([])
        self.ssrlabel       = np.array([])
        self.tracklabel     = np.array([])
        self.uco            = np.array([])

        # Defaults
        self.labelpos_default       = np.array([50., 0.])
        self.leaderlinepos_default  = np.array([0., 0., 50., 0.])
        self.mlabel_default         = False
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
            self.update_trafficdata(nodedata.acdata)
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
            idx = data.guitrafdata['data']
            self.tracklabel[idx] = not self.tracklabel[idx]

    def update_trafficdata(self, data):
        """
        Function: Update the GUI traffic variables
        Args:
            data: New data [class]
        Returns: -

        Created by: Bob van Dillen
        Date: 23-9-2022
        """

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

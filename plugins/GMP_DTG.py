""" Add the DTG to the label for the GMP concept along the route """

import numpy as np
import bluesky as bs
from bluesky import core, stack
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros


### Initialization function of the plugin
def init_plugin():
    ''' Plugin initialisation function. '''

    dtg = GMP()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'GMP',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'gui',
        }

    # init_plugin() should always return a configuration dict.
    return config


'''
Classes
'''


class GMP(core.Entity):
    """
    Definition: Class used to initialize and update DTG to T-Bar points
    Methods:
        showdtg():      Initialize the DTG label
        update_tbar():  Update T-Bar graphics
    """

    def __init__(self):
        super().__init__()
        self.initialized = False
        self.gmplbl = None

        # Set update function
        bs.net.actnodedata_changed.connect(self.update_gmp)

    @stack.command(name='SHOWDTG',)
    def showdtg(self):
        """
        Function: Initialize the DTG label
        Args: -
        Returns: -

        Created by: Ajay Kumbhar
        Date:
        """

        # Check if we need to initialize
        if not self.initialized:
            # Get current node data
            actdata = bs.net.get_nodedata()

            # Class to access Traffic graphics
            self.gmplbl = Traffic()

            # Initialize plugin label
            self.gmplbl.plugin_init(blocksize=(3, 2), position=(2, 8))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 3*' '
                rawlabel += 3*' '

            self.gmplbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.gmplbl.show_pluginlabel = not self.gmplbl.show_pluginlabel

    def update_gmp(self, nodeid, nodedata, changed_elems):
        """
        Function: Update GMP graphics
        Args:
            nodeid:         Node identifier []
            nodedata:       Node data [class]
            changed_elems:  Changed elements [list]
        Returns: -

        Created by: Ajay Kumbhar
        Date: 25-2-2022
        """

        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update DTG label
                rawlabel = ''

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    dtg_route = nodedata.acdata.dtg_route[idx]
                    tracklbl = nodedata.acdata.tracklbl[idx]
                    if tracklbl and dtg_route != 0. and acid == console.Console._instance.id_select:
                        rawlabel += '%-3s' % leading_zeros(dtg_route)[:3]
                    else:
                        rawlabel += 3*2*' '
                self.gmplbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))


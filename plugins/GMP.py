""" Add the DTG to the label for the GMP concept till touchdown point """

import numpy as np
import bluesky as bs
from bluesky import core, stack
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros
from bluesky.tools import geo


### Initialization function of the plugin
def init_plugin():
    # ''' Plugin initialisation function. '''

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
    Definition: Class used to initialize and update DTG till touchdown point for GMP Scenario
    Methods:
        showdtg():      Initialize the DTG label
        update_tbar():  Update GMP graphics
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
            self.gmplbl.plugin_init(blocksize=(3, 1), position=(2, 8))

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
        Date:
        """

        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update DTG label
                rawlabel = ''

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    dtg = nodedata.acdata.dtg[idx]
                    tracklbl = nodedata.acdata.tracklbl[idx]
                    if tracklbl and dtg != 0. and acid == console.Console._instance.id_select:
                        rawlabel += '%-3s' % leading_zeros(dtg)[:3]
                    else:
                        rawlabel += 3*' '
                self.gmplbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))
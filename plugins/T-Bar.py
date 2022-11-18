""" Add the DTG to the label for the T-Bar concept """

import numpy as np
import bluesky as bs
from bluesky import core, stack
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl.gltraffic import Traffic, leading_zeros


### Initialization function of the plugin
def init_plugin():
    ''' Plugin initialisation function. '''

    dtg = TBar()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'TBAR',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'gui',
        }

    # init_plugin() should always return a configuration dict.
    return config


'''
Classes
'''


class TBar(core.Entity):
    """
    Definition: Class used to initialize and update DTG to T-Bar points
    Methods:
        showdtg():      Initialize the DTG label
        update_tbar():  Update T-Bar graphics
    """

    def __init__(self):
        super().__init__()
        self.initialized = False
        self.tbarlbl = None

        # Set update function
        bs.net.actnodedata_changed.connect(self.update_tbar)

    @stack.command(name='SHOWDTG',)
    def showdtg(self):
        """
        Function: Initialize the DTG label
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 25-2-2022
        """

        # Check if we need to initialize
        if not self.initialized:
            # Get current node data
            actdata = bs.net.get_nodedata()

            # Class to access Traffic graphics
            self.tbarlbl = Traffic()

            # Initialize plugin label
            self.tbarlbl.plugin_init(blocksize=(3, 1), position=(2, 7))

            # Update label with current data
            rawlabel = ''
            for idx in range(len(actdata.acdata.id)):
                rawlabel += 3*' '

            self.tbarlbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))

            # Initialization completed
            self.initialized = True
        else:
            self.tbarlbl.show_pluginlabel = not self.tbarlbl.show_pluginlabel

    def update_tbar(self, nodeid, nodedata, changed_elems):
        """
        Function: Update T-Bar graphics
        Args:
            nodeid:         Node identifier []
            nodedata:       Node data [class]
            changed_elems:  Changed elements [list]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-2-2022
        """

        if self.initialized:
            if 'ACDATA' in changed_elems:
                # Update DTG label
                rawlabel = ''

                for idx in range(len(nodedata.acdata.id)):
                    acid = nodedata.acdata.id[idx]
                    dtg = nodedata.acdata.dtg[idx]
                    tracklbl = self.tbarlbl.trafdata.tracklabel[idx]
                    if tracklbl and dtg != 0. and acid == console.Console._instance.id_select:
                        rawlabel += '%-3s' % leading_zeros(dtg)[:3]
                    else:
                        rawlabel += 3*' '
                self.tbarlbl.pluginlbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))


"""
This python file is used to create history symbols for aircraft

Created by: Bob van Dillen
Date: 17-12-2021
"""

import numpy as np
import bluesky as bs
from bluesky.core import Entity, timed_function
from bluesky.tools import misc


class HistorySymbols(Entity):
    """
    Class definition: Histroy symbols for aircraft
    Methods:
        clear():    Reset variables
        update():   Update the history symbols
        update_history():   Update the history locations
        setHistory():       Enable/Disable history symbols

    Created by: Bob van Dillen
    Date: 17-12-2021
    """

    def __init__(self):
        super().__init__()

        self.nsymb = 4

        self.histlat = np.array([])
        self.histlon = np.array([])

        self.t_prev = 0.

        if bs.settings.screendt < 3.:
            self.maxdeltat = 3.
        else:
            self.maxdeltat = bs.settings.screendt

        with self.settrafarrays():
            self.swhistory = np.array([], dtype=bool)

            self.lat1 = np.array([])
            self.lon1 = np.array([])

            self.lat2 = np.array([])
            self.lon2 = np.array([])

            self.lat3 = np.array([])
            self.lon3 = np.array([])

            self.lat4 = np.array([])
            self.lon4 = np.array([])

            self.lat5 = np.array([])
            self.lon5 = np.array([])

            self.lat6 = np.array([])
            self.lon6 = np.array([])

            self.lat7 = np.array([])
            self.lon7 = np.array([])

            self.lat8 = np.array([])
            self.lon8 = np.array([])

    def reset(self):
        """
        Function: Reset variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 20-12-2021
        """

        super().reset()

        self.nsymb = 4

        self.histlat = np.array([])
        self.histlon = np.array([])

        self.t_prev = 0.

    @timed_function(name='historysymbols', dt=0.2)
    def update(self):
        """
        Function: Update the history symbols
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 20-12-2021
        """

        if self.nsymb > 0:
            # Get latitudes and longitudes for all history symbols
            if self.nsymb >= 1:
                self.histlat = self.lat1
                self.histlon = self.lon1
            if self.nsymb >= 2:
                self.histlat = np.append(self.histlat, self.lat2)
                self.histlon = np.append(self.histlon, self.lon2)
            if self.nsymb >= 3:
                self.histlat = np.append(self.histlat, self.lat3)
                self.histlon = np.append(self.histlon, self.lon3)
            if self.nsymb >= 4:
                self.histlat = np.append(self.histlat, self.lat4)
                self.histlon = np.append(self.histlon, self.lon4)
            if self.nsymb >= 5:
                self.histlat = np.append(self.histlat, self.lat5)
                self.histlon = np.append(self.histlon, self.lon5)
            if self.nsymb >= 6:
                self.histlat = np.append(self.histlat, self.lat6)
                self.histlon = np.append(self.histlon, self.lon6)
            if self.nsymb >= 7:
                self.histlat = np.append(self.histlat, self.lat7)
                self.histlon = np.append(self.histlon, self.lon7)
            if self.nsymb == 8:
                self.histlat = np.append(self.histlat, self.lat8)
                self.histlon = np.append(self.histlon, self.lon8)
            self.histlat = self.histlat[self.histlat != 0.]
            self.histlon = self.histlon[self.histlon != 0.]

            # Data feed traffic
            if len(bs.traf.trafdatafeed.datafeedids) > 0:
                itrafdatafeed = misc.get_indices(bs.traf.id, bs.traf.trafdatafeed.datafeedids)
                # Data feed traffic that received an update
                itrafnew = np.nonzero(bs.traf.trafdatafeed.lastupdate <= 0.2)[0]
                itrafdatafeed_new = np.intersect1d(itrafdatafeed, itrafnew, assume_unique=True)
            else:
                itrafdatafeed = np.array([])
                itrafdatafeed_new = np.array([])

            # Simulated traffic
            deltat = bs.sim.simt - self.t_prev
            if deltat >= self.maxdeltat:
                itraf_new = np.setdiff1d(np.arange(bs.traf.ntraf), itrafdatafeed)
                self.t_prev = bs.sim.simt
            else:
                itraf_new = np.array([])

            # Merge indices and update history
            i_new = np.append(itrafdatafeed_new, itraf_new)
            i_new = i_new.astype(np.int32)

            # Every other position gets a history symbol
            i_swhistory = np.nonzero(self.swhistory)[0]
            i_update = np.intersect1d(i_new, i_swhistory)
            self.swhistory[i_new] = ~self.swhistory[i_new]

            # OPENSKY traffic always gets an update
            iopensky = misc.get_indices(bs.traf.trafdatafeed.source, 'OPENSKY')
            iopensky_new = np.intersect1d(i_new, iopensky)
            i_update = np.union1d(i_update, iopensky_new)

            # Update the history symbols
            self.update_history(i_update)
        else:
            self.histlat = np.array([])
            self.histlon = np.array([])

    def update_history(self, indices):
        """
        Function: Update the history locations
        Args:
            indices:    indices of the update
        Returns: -

        Created by: Bob van Dillen
        Date: 20-12-2021
        """

        self.lat8[indices] = self.lat7[indices]
        self.lon8[indices] = self.lon7[indices]

        self.lat7[indices] = self.lat6[indices]
        self.lon7[indices] = self.lon6[indices]

        self.lat6[indices] = self.lat5[indices]
        self.lon6[indices] = self.lon5[indices]

        self.lat5[indices] = self.lat4[indices]
        self.lon5[indices] = self.lon4[indices]

        self.lat4[indices] = self.lat3[indices]
        self.lon4[indices] = self.lon3[indices]

        self.lat3[indices] = self.lat2[indices]
        self.lon3[indices] = self.lon2[indices]

        self.lat2[indices] = self.lat1[indices]
        self.lon2[indices] = self.lon1[indices]

        self.lat1[indices] = bs.traf.lat[indices]
        self.lon1[indices] = bs.traf.lon[indices]

    def setHistory(self, nsymbols):
        """
        Function: Enable/Disable history symbols
        Args:
            nsymbols:   argument [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 23-12-2021
        """

        if 0 <= nsymbols <= 8:
            self.nsymb = nsymbols
        else:
            return False, 'HISTORY: Number of symbols should be between 0 and 8'

        return True

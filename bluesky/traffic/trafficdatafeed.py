"""
This python file contains a class which is used to update the aircraft states from a data source

Created by: Bob van Dillen
Date: 13-1-2022
"""

import copy
import numpy as np
import bluesky as bs
from bluesky import stack
from bluesky.core import Entity
from bluesky.tools import aero, geo, misc


"""
Classes
"""


class TrafficDataFeed(Entity):
    """
    Class definition: Update aircraft states from data source
    Methods:
        reset():                Reset variables
        create():               Create an aircraft
        delete():               Delete an aircraft
        update():               Perform an update (step)
        update_fromtrackdata(): Update aircraft states from data source
        update_fromtrafprev():  Update aircraft states from previous aircraft states
        update_speed():         Calculate the different speeds
        store_prev():           Store the previous aircraft states
        indices_update():       Get the indices for the traffic arrays and the trackdata
        setdatafeed():          Add aircraft to datafeed mode
        uco():                  Stop taking the aircraft state from data sources (simulate the aircraft)

    Created by: Bob van Dillen
    Date: 13-1-2022
    """

    def __init__(self):
        super().__init__()

        # Dictionary containing the track data
        self.trackdata = dict()
        # Dictionary containing the previous aircraft states
        self.trafprev = dict()
        # List with callsigns which state is updated from data source
        self.datafeedids = []

        with self.settrafarrays():
            self.datafeed = np.array([], dtype=bool)
            self.source = []
            self.lastupdate = np.array([])  # Time since the last update

    def reset(self):
        """
        Function: Reset variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        super().reset()

        self.trackdata = dict()
        self.trafprev = dict()
        self.datafeedids = []

    def create(self, n=1):
        """
        Function: Create an aircraft
        Args:
            n:  number of aircraft
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        super().create(n)

        # Store current state
        self.store_prev()

    def delete(self, idx):
        """
        Function: Delete an aircraft
        Args:
            idx:    indices for traffic arrays
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        ids = np.array(bs.traf.id)[idx]

        for acid in ids:
            # Check if this callsign was updated from data
            if acid in self.datafeedids:
                self.datafeedids.remove(acid)

        super().delete(idx)

    def update(self):
        """
        Function: Perform an update (step)
        Args: -
        Returns: -

        Remark: Slicing is used for accessing the track data ([i0: im])

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        # Check if there are aircraft
        if len(self.datafeedids) == 0:
            return

        # Check if new data is available
        if self.trackdata:
            # ---------- Update from data source ----------
            # Get indices for traffic arrays, track data and data feed ids
            itraf_update, itrackdata_update, idatafeed_update = self.indices_update(self.trackdata['id'])
            # Update from data source
            self.update_fromtrackdata(itraf_update, itrackdata_update)

            # ---------- Update from previous aircraft states ----------
            # Get indices for traffic arrays and previous aircraft states
            itraf_prev = misc.get_indices(bs.traf.id, np.delete(self.datafeedids, idatafeed_update))
            iprev = misc.get_indices(self.trafprev['id'], np.delete(self.datafeedids, idatafeed_update))
            # Update from previous aircraft states
            self.update_fromtrafprev(itraf_prev, iprev)

            # ---------- Aftermath ----------
            self.lastupdate[itraf_update] = 0.
            self.lastupdate[itraf_prev] += bs.sim.simdt
            self.store_prev()
            self.trackdata = dict()
        else:
            # Get indices for traffic arrays and previous aircraft states
            itraf_prev = misc.get_indices(bs.traf.id, self.datafeedids)
            iprev = misc.get_indices(self.trafprev['id'], self.datafeedids)
            # Update from previous aircraft states
            self.update_fromtrafprev(itraf_prev, iprev)
            # Update last update time
            self.lastupdate[itraf_prev] += bs.sim.simdt

        # Update other speeds (wind)
        self.update_speed()

    def update_fromtrackdata(self, itraf_update, itrackdata_update):
        """
        Function: Update aircraft states from data source
        Args:
            itraf_update:       indices for traffic arrays [list, array]
            itrackdata_update:  indices for trackdata [list, array]
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        bs.traf.distflown[itraf_update] += np.array(geo.kwikdist_matrix(bs.traf.lat[itraf_update],
                                                                        bs.traf.lon[itraf_update],
                                                                        self.trackdata['lat'][itrackdata_update],
                                                                        self.trackdata['lon'][itrackdata_update])*aero.nm,
                                                    dtype=np.float32)

        bs.traf.lat[itraf_update] = self.trackdata['lat'][itrackdata_update]
        bs.traf.lon[itraf_update] = self.trackdata['lon'][itrackdata_update]
        bs.traf.hdg[itraf_update] = self.trackdata['hdg'][itrackdata_update]
        bs.traf.alt[itraf_update] = self.trackdata['alt'][itrackdata_update]
        bs.traf.gs[itraf_update] = self.trackdata['gs'][itrackdata_update]

    def update_fromtrafprev(self, itraf_prev, iprev):
        """
        Function: Update aircraft states from previous aircraft states
        Args:
            itraf_prev: indices for traffic arrays [list, array]
            iprev:      indices for previous traffic arrays [list, array]
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        bs.traf.lat[itraf_prev] = self.trafprev['lat'][iprev]
        bs.traf.lon[itraf_prev] = self.trafprev['lon'][iprev]
        bs.traf.hdg[itraf_prev] = self.trafprev['hdg'][iprev]
        bs.traf.alt[itraf_prev] = self.trafprev['alt'][iprev]
        bs.traf.gs[itraf_prev] = self.trafprev['gs'][iprev]

    def update_speed(self):
        """
        Function: Update speed variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 1-12-2021
        """

        # Get indices for traffic arrays
        itraf = misc.get_indices(bs.traf.id, self.datafeedids)

        # No wind
        if bs.traf.wind.winddim == 0:
            # Decompose ground speed
            bs.traf.gsnorth[itraf] = bs.traf.gs[itraf]*np.cos(np.radians(bs.traf.hdg[itraf]))
            bs.traf.gseast[itraf] = bs.traf.gs[itraf]*np.sin(np.radians(bs.traf.hdg[itraf]))

            # Determine true airspeed
            bs.traf.tas[itraf] = bs.traf.gs[itraf]

            # Determine calibrated airspeed
            bs.traf.cas[itraf] = aero.vtas2cas(bs.traf.tas[itraf], bs.traf.alt[itraf])

            # Determine mach
            bs.traf.M[itraf] = aero.vtas2mach(bs.traf.tas[itraf], bs.traf.alt[itraf])

            # Determine track
            bs.traf.trk[itraf] = bs.traf.hdg[itraf]

        # Wind
        else:
            # Decompose ground speed
            bs.traf.gsnorth[itraf] = bs.traf.gs[itraf]*np.cos(np.radians(bs.traf.hdg[itraf]))
            bs.traf.gseast[itraf] = bs.traf.gs[itraf]*np.sin(np.radians(bs.traf.hdg[itraf]))

            # Wind when airborn
            applywind = bs.traf.alt[itraf] > 50.*aero.ft

            # Get wind data
            # bs.traf.windnorth[itraf], bs.traf.windeast[itraf] = bs.traf.wind.getdata(bs.traf.lat[itraf],
            #                                                                          bs.traf.lon[itraf],
            #                                                                          bs.traf.alt[itraf])

            # Determine true airspeed
            tasnorth = bs.traf.gsnorth[itraf] - bs.traf.windnorth[itraf]*applywind
            taseast = bs.traf.gseast[itraf] - bs.traf.windeast[itraf]*applywind
            bs.traf.tas[itraf] = np.sqrt(tasnorth*tasnorth + taseast*taseast)

            # Determine calibrated airspeed
            bs.traf.cas[itraf] = aero.vtas2cas(bs.traf.tas[itraf], bs.traf.alt[itraf])

            # Determine mach
            bs.traf.M[itraf] = aero.vtas2mach(bs.traf.tas[itraf], bs.traf.alt[itraf])

            # Determine track
            bs.traf.trk[itraf] = np.logical_not(applywind)*bs.traf.hdg[itraf] +\
                                 applywind*np.degrees(np.arctan2(bs.traf.gseast[itraf], bs.traf.gsnorth[itraf])) % 360.

    def store_prev(self):
        """
        Function: Store the previous aircraft states
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        self.trafprev['id'] = copy.deepcopy(bs.traf.id)
        self.trafprev['lat'] = copy.deepcopy(bs.traf.lat)
        self.trafprev['lon'] = copy.deepcopy(bs.traf.lon)
        self.trafprev['hdg'] = copy.deepcopy(bs.traf.hdg)
        self.trafprev['alt'] = copy.deepcopy(bs.traf.alt)
        self.trafprev['gs'] = copy.deepcopy(bs.traf.gs)
        self.trafprev['distflown'] = copy.deepcopy(bs.traf.distflown)

    def indices_update(self, ids_trackdata):
        """
        Function: Get the indices for the traffic arrays and the trackdata
        Args:
            ids_trackdata:  callsigns with available data [array]
        Returns:
            itraf_update:       index track data update for the traffic arrays [array]
            itrackdata_update:  index for the trackdata [array]
            itraf_prev:         index previous update for the traffic arrays [array]
            iprev:              index previous update for prev arrays [array]

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        # Get callsigns that need an update and index for trackdata
        ids_update, ireplay, itrackdata_update = np.intersect1d(self.datafeedids, ids_trackdata, return_indices=True)
        # Get index for traffic arrays
        itraf_update = misc.get_indices(bs.traf.id, ids_update)

        return itraf_update, itrackdata_update, ireplay

    @stack.command(name='SETDATAFEED', brief='SETDATAFEED CALLSIGN (SOURCE)')
    def setdatafeed(self, idx: 'acid', source: str = ''):
        """
        Function: Add aircraft to datafeed mode
        Args:
            idx:    index for traffic arrays [int]
            source: source [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 13-1-2022
        """

        acid = bs.traf.id[idx]
        if acid not in self.datafeedids:
            self.datafeedids.append(acid)
            self.datafeed[idx] = True
            self.source[idx] = source
        else:
            return False, acid+' state already taken from data source'

    @stack.command(name='SETSIM', brief='SETSIM CALLSIGN')
    def setsimulation(self, idx: 'acid'):
        """
        Function: Add aircraft to simulation mode
        Args:
            idx:    index for traffic arrays [int]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 12-5-2022
        """
        acid = bs.traf.id[idx]

        if acid in self.datafeedids:
            self.datafeedids.remove(acid)
            self.datafeed[idx] = False
            self.source[idx] = ''
        else:
            return False, acid+' already in simulation'


    def uco(self, idx):
        """
        Function: Stop taking the aircraft state from data sources (simulate the aircraft)
        Args:
            idx:    index for traffic arrays
        Returns: -

        Created by: Bob van Dillen
        Date: 14-1-2022
        """

        acid = bs.traf.id[idx]
        if acid in self.datafeedids:
            self.datafeed[idx] = False
            self.source[idx] = ''
            self.datafeedids.remove(acid)
            bs.stack.stackbase.del_scencmds(idx)

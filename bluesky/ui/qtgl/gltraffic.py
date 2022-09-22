''' Traffic OpenGL visualisation. '''
import socket

import numpy as np
import itertools
import bluesky as bs
from bluesky import settings
from bluesky.tools import geo, misc
from bluesky.tools.aero import ft, nm, kts
from bluesky.ui import palette
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl import glhelpers as glh
from bluesky import stack

# Register settings defaults
settings.set_variable_defaults(
    text_size=13,
    ac_size=16,
    asas_vmin=200.0,
    asas_vmax=500.0
)

palette.set_default_colours(
    aircraft=(0, 255, 0),
    conflict=(255, 160, 0),
    route=(255, 0, 255),
    trails=(0, 255, 255)
)

# Static defines
MAX_NAIRCRAFT       = 10000
MAX_NCONFLICTS      = 25000
MAX_ROUTE_LENGTH    = 500
ROUTE_SIZE          = 500
TRAILS_SIZE         = 1000000


class Traffic(glh.RenderObject, layer=100):
    ''' Traffic OpenGL object. '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialized    = False
        self.route_acid     = ''
        self.asas_vmin      = settings.asas_vmin
        self.asas_vmax      = settings.asas_vmax

        # --------------- Label position ---------------

        self.id_prev        = []
        self.labelpos       = np.array([], dtype=np.float32)
        self.leaderlinepos  = np.array([], dtype=np.float32)
        bs.Signal('labelpos').connect(self.update_labelpos)

        # --------------- Aircraft data ---------------

        self.hdg            = glh.GLBuffer()
        self.rpz            = glh.GLBuffer()
        self.lat            = glh.GLBuffer()
        self.lon            = glh.GLBuffer()

        self.latuacc         = glh.GLBuffer()   # lat_UCO_ACC
        self.lonuacc         = glh.GLBuffer()
        self.latuapp         = glh.GLBuffer()   # lat_UCO_APP
        self.lonuapp         = glh.GLBuffer()
        self.latutwr         = glh.GLBuffer()   # lat_UCO_TWR
        self.lonutwr         = glh.GLBuffer()

        self.alt            = glh.GLBuffer()
        self.tas            = glh.GLBuffer()
        self.color          = glh.GLBuffer()

        self.coloruacc      = glh.GLBuffer()    # color_UCO_ACC
        self.coloruapp      = glh.GLBuffer()    # color_UCO_APP
        self.colorutwr      = glh.GLBuffer()    # color_UCO_TWR
        self.asasn          = glh.GLBuffer()
        self.asase          = glh.GLBuffer()
        self.histsymblat    = glh.GLBuffer()
        self.histsymblon    = glh.GLBuffer()

        # --------------- Label data ---------------

        self.lbl        = glh.GLBuffer()
        self.lbl_lvnl   = glh.GLBuffer()
        self.ssrlbl     = glh.GLBuffer()
        self.mlbl       = glh.GLBuffer()

        self.lbloffset  = glh.GLBuffer()
        self.mlbloffset = glh.GLBuffer()

        # --------------- Aircraft objects ---------------

        self.ssd            = glh.VertexArrayObject(glh.gl.GL_POINTS, shader_type='ssd')
        self.protectedzone  = glh.Circle()
        self.ac_symbol      = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)

        self.acs_lvnlacc     = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)
        self.acs_lvnluacc    = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)
        self.acs_lvnluapp    = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)
        self.acs_lvnlutwr    = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)

        self.hist_symbol    = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)
        self.cpalines       = glh.VertexArrayObject(glh.gl.GL_LINES)
        self.route          = glh.VertexArrayObject(glh.gl.GL_LINES)
        self.routelbl       = glh.Text(settings.text_size, (12, 2))
        self.rwaypoints     = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)
        self.traillines     = glh.VertexArrayObject(glh.gl.GL_LINES)

        # --------------- Label objects ---------------

        self.aclabels       = glh.Text(settings.text_size, (8, 3))  # Default label BlueSky
        self.aclabels_lvnl  = glh.Text(settings.text_size, (8, 4))  # LVNL label
        self.ssrlabels      = glh.Text(0.95*settings.text_size, (7, 3))
        self.microlabels    = glh.Text(0.95*settings.text_size, (7, 1))   #3

        self.leaderlines    = glh.Line()

        # --------------- Plugin Variables ---------------
        self.show_pluginlabel = False
        self.pluginlabelpos   = None
        self.pluginlbloffset  = None
        self.pluginlbl        = None
        self.pluginlabel      = None

        # --------------- Plugin Variables ---------------
        self.show_tbar_ac = False
        self.tbar_labelpos = None
        self.tbar_lbloffset = None
        self.tbar_lbl = None
        self.tbar_label = None

        self.tbar_ac = None
        self.tbar_lat = None
        self.tbar_lon = None

        bs.net.actnodedata_changed.connect(self.actdata_changed)

    def create(self):
        ac_size     = settings.ac_size
        text_size   = settings.text_size
        text_width  = text_size
        text_height = text_size*1.2307692307692308
        wpt_size    = settings.wpt_size

        # --------------- Aircraft data ---------------

        self.hdg.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.lat.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.lon.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)

        self.latuacc.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw) # create attributes
        self.lonuacc.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.latuapp.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.lonuapp.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.latutwr.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.lonutwr.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)

        self.alt.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.tas.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.color.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)

        self.coloruacc.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.coloruapp.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.colorutwr.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)

        self.asasn.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.asase.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.rpz.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.histsymblat.create(MAX_NAIRCRAFT * 16, glh.GLBuffer.StreamDraw)
        self.histsymblon.create(MAX_NAIRCRAFT * 16, glh.GLBuffer.StreamDraw)

        # --------------- Label data ---------------

        self.lbl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.lbl_lvnl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.ssrlbl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.mlbl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)

        self.lbloffset.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.mlbloffset.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)

        # --------------- SSD ---------------

        self.ssd.create(lat1=self.lat, lon1=self.lon, alt1=self.alt,
                        tas1=self.tas, trk1=self.hdg)
        self.ssd.set_attribs(selssd=MAX_NAIRCRAFT, instance_divisor=1,
                             datatype=glh.gl.GL_UNSIGNED_BYTE, normalize=True)
        self.ssd.set_attribs(lat0=self.lat, lon0=self.lon,
                             alt0=self.alt, tas0=self.tas,
                             trk0=self.hdg, asasn=self.asasn,
                             asase=self.asase, instance_divisor=1)

        self.protectedzone.create(radius=1.0)
        self.protectedzone.set_attribs(lat=self.lat, lon=self.lon, scale=self.rpz,
                                       color=self.color, instance_divisor=1)

        # --------------- Aircraft symbols ---------------

        acvertices = np.array([(0.0, 0.5 * ac_size), (-0.5 * ac_size, -0.5 * ac_size),
                               (0.0, -0.25 * ac_size), (0.5 * ac_size, -0.5 * ac_size)],
                              dtype=np.float32)
        self.ac_symbol.create(vertex=acvertices)
        self.ac_symbol.set_attribs(lat=self.lat, lon=self.lon, color=self.color, orientation=self.hdg,
                                   instance_divisor=1)  #default - BlueSky

        acv_lvnlacc = np.array([(-0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, 0.5 * ac_size),
                                   (0.5 * ac_size, -0.5 * ac_size),
                                   (-0.5 * ac_size, 0.5 * ac_size),
                                   (-0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, 0.5 * ac_size),
                                   (-0.5 * ac_size, 0.5 * ac_size)],
                                  dtype=np.float32)  # a square with diagonals - ACC MODE
        self.acs_lvnlacc.create(vertex=acv_lvnlacc)
        self.acs_lvnlacc.set_attribs(lat=self.lat, lon=self.lon, color=self.color,
                                   instance_divisor=1)

        acv_lvnluacc = np.array([(-0.375 * ac_size, 0 * ac_size),
                                   (-0.375 * ac_size, -0.5 * ac_size),
                                   (-0.375 * ac_size, 0 * ac_size),
                                   (0.375 * ac_size, 0 * ac_size),
                                   (0.375 * ac_size, -0.5 * ac_size),
                                   (0.375 * ac_size, 0 * ac_size),
                                   (0.125 * ac_size, 0.5 * ac_size),
                                   (-0.125 * ac_size, 0.5 * ac_size),
                                   (-0.375 * ac_size, 0 * ac_size),
                                   (0.375 * ac_size, 0 * ac_size)],
                                    dtype=np.float32)  # A - UCO at ACC

        self.acs_lvnluacc.create(vertex=acv_lvnluacc)
        self.acs_lvnluacc.set_attribs(lat=self.latuacc, lon=self.lonuacc, color=self.coloruacc,
                                       instance_divisor=1)

        acv_lvnluapp = np.array([(0.5 * ac_size, 0.433 * ac_size),
                                (-0.5 * ac_size, 0.433 * ac_size),
                                (0 * ac_size, -0.433 * ac_size)],
                                dtype=np.float32) # triangle - UCO at APP

        self.acs_lvnluapp.create(vertex=acv_lvnluapp)
        self.acs_lvnluapp.set_attribs(lat=self.latuapp, lon=self.lonuapp, color=self.coloruapp,
                                     instance_divisor=1)

        # --------------- History symbols ---------------

        histsymbol_size = 2
        self.hist_symbol.create(vertex=np.array([(histsymbol_size/2, histsymbol_size/2),
                                                 (-histsymbol_size/2, histsymbol_size/2),
                                                 (-histsymbol_size/2, -histsymbol_size/2),
                                                 (histsymbol_size/2, -histsymbol_size/2)], dtype=np.float32))
        self.hist_symbol.set_attribs(lat=self.histsymblat, lon=self.histsymblon,
                                     color=palette.aircraft, instance_divisor=1)

        # --------------- Aircraft labels ---------------

        self.aclabels.create(self.lbl, self.lat, self.lon, self.color,
                             (ac_size, -0.5 * ac_size), instanced=True)
        self.aclabels_lvnl.create(self.lbl_lvnl, self.lat, self.lon, self.color,
                                  self.lbloffset, instanced=True)
        self.ssrlabels.create(self.ssrlbl, self.lat, self.lon, self.color,
                              (ac_size, -1.1*ac_size), instanced=True)
        # self.microlabels.create(self.mlbl, self.lat, self.lon, self.color,
        #                         (-3*0.8*text_size-ac_size, 0.5*ac_size), instanced=True)  # 2*0.8*text_size-ac_size (RIGHT SIDE)
        self.microlabels.create(self.mlbl, self.lat, self.lon, self.color,
                                self.mlbloffset, instanced=True)

        # --------------- Leader lines ---------------

        self.leaderlines.create(vertex=MAX_NAIRCRAFT*4, lat=MAX_NAIRCRAFT*4, lon=MAX_NAIRCRAFT*4,
                                color=MAX_NAIRCRAFT*4)

        # --------------- CPA lines ---------------

        self.cpalines.create(vertex=MAX_NCONFLICTS * 16, color=palette.conflict, usage=glh.GLBuffer.StreamDraw)

        # --------------- Aircraft Route ---------------

        self.route.create(vertex=ROUTE_SIZE * 8, color=palette.route, usage=glh.gl.GL_DYNAMIC_DRAW)

        self.routelbl.create(ROUTE_SIZE * 24, ROUTE_SIZE * 4, ROUTE_SIZE * 4,
                             palette.route, (wpt_size, 0.5 * wpt_size), instanced=True)

        rwptvertices = np.array([(-0.2 * wpt_size, -0.2 * wpt_size),
                                 (0.0,            -0.8 * wpt_size),
                                 (0.2 * wpt_size, -0.2 * wpt_size),
                                 (0.8 * wpt_size,  0.0),
                                 (0.2 * wpt_size,  0.2 * wpt_size),
                                 (0.0,             0.8 * wpt_size),
                                 (-0.2 * wpt_size,  0.2 * wpt_size),
                                 (-0.8 * wpt_size,  0.0)], dtype=np.float32)
        self.rwaypoints.create(vertex=rwptvertices, color=palette.route)
        self.rwaypoints.set_attribs(lat=self.routelbl.lat, lon=self.routelbl.lon, instance_divisor=1)

        # --------------- Aircraft Trails ---------------

        self.traillines.create(vertex=TRAILS_SIZE * 16, color=palette.trails)
        self.initialized = True

    def draw(self):
        ''' Draw all traffic graphics. '''
        # Get data for active node
        actdata = bs.net.get_nodedata()

        if actdata.naircraft == 0 or not actdata.show_traf:
            return

        # Send the (possibly) updated global uniforms to the buffer
        self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_LATLON)
        self.shaderset.enable_wrap(False)

        self.route.draw()
        self.cpalines.draw()
        self.traillines.draw()

        # --- DRAW THE INSTANCED AIRCRAFT SHAPES ------------------------------
        # update wrap longitude and direction for the instanced objects
        self.shaderset.enable_wrap(True)

        # PZ circles only when they are bigger than the A/C symbols
        if actdata.show_pz and actdata.zoom >= 0.15:
            self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_METERS)
            self.protectedzone.draw(n_instances=actdata.naircraft)

        self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_SCREEN)

        # Draw traffic symbols
        if actdata.atcmode == 'BLUESKY':
            self.ac_symbol.draw(n_instances=actdata.naircraft)
        else:
            if actdata.atcmode == 'APP':
                if actdata.naircraft - len(draw_uco(actdata.acdata.uco)) != 0:
                    self.acs_lvnluacc.draw(n_instances=actdata.naircraft - len(draw_uco(actdata.acdata.uco)))
                if len(draw_uco(actdata.acdata.uco)) != 0:
                    self.acs_lvnluapp.draw(n_instances=len(draw_uco(actdata.acdata.uco)))
            elif actdata.atcmode == 'ACC':
                self.acs_lvnlacc.draw(n_instances=actdata.naircraft)
            if self.tbar_ac is not None and self.show_tbar_ac:
                self.tbar_ac.draw(n_instances=actdata.naircraft)

        # Draw history symbols
        if actdata.show_histsymb and len(actdata.acdata.histsymblat) != 0:
            self.hist_symbol.draw(n_instances=len(actdata.acdata.histsymblat))

        # Draw route labels
        if self.routelbl.n_instances:
            self.rwaypoints.draw(n_instances=self.routelbl.n_instances)
            self.routelbl.draw()

        # Draw traffic labels
        if actdata.atcmode == 'BLUESKY':
            if actdata.show_lbl >= 1:
                self.aclabels.draw(n_instances=actdata.naircraft)
        else:
            self.aclabels_lvnl.draw(n_instances=actdata.naircraft)
            self.ssrlabels.draw(n_instances=actdata.naircraft)
            self.microlabels.draw(n_instances=actdata.naircraft)
            if self.pluginlabel is not None and self.show_pluginlabel:
                self.pluginlabel.draw(n_instances=actdata.naircraft)
            if self.tbar_label is not None and self.show_tbar_ac:
                self.tbar_label.draw(n_instances=actdata.naircraft)

            self.leaderlines.draw()

        # Draw SSD
        if actdata.ssd_all or actdata.ssd_conflicts or len(actdata.ssd_ownship) > 0:
            ssd_shader = glh.ShaderSet.get_shader('ssd')
            ssd_shader.bind()
            glh.gl.glUniform3f(ssd_shader.uniforms['Vlimits'].loc, self.asas_vmin **
                           2, self.asas_vmax ** 2, self.asas_vmax)
            glh.gl.glUniform1i(ssd_shader.uniforms['n_ac'].loc, actdata.naircraft)
            self.ssd.draw(vertex_count=actdata.naircraft,
                          n_instances=actdata.naircraft)

    def actdata_changed(self, nodeid, nodedata, changed_elems):
        ''' Process incoming traffic data. '''
        if 'ACDATA' in changed_elems:
            self.update_aircraft_data(nodedata.acdata)
        if 'ROUTEDATA' in changed_elems:
            self.update_route_data(nodedata.routedata)
        if 'TRAILS' in changed_elems:
            self.update_trails_data(nodedata.traillat0,
                                    nodedata.traillon0,
                                    nodedata.traillat1,
                                    nodedata.traillon1)
        if 'ATCMODE' in changed_elems:
            self.hist_symbol.set_attribs(color=palette.aircraft)

    def update_trails_data(self, lat0, lon0, lat1, lon1):
        ''' Update GPU buffers with route data from simulation. '''
        if not self.initialized:
            return
        self.glsurface.makeCurrent()
        self.traillines.set_vertex_count(len(lat0))
        if len(lat0) > 0:
            self.traillines.update(vertex=np.array(
                    list(zip(lat0, lon0,
                             lat1, lon1)), dtype=np.float32))

    def update_route_data(self, data):
        ''' Update GPU buffers with route data from simulation. '''
        if not self.initialized:
            return
        self.glsurface.makeCurrent()
        actdata = bs.net.get_nodedata()

        self.route_acid = data.acid
        if data.acid != "" and len(data.wplat) > 0:
            nsegments = len(data.wplat)
            data.iactwp = min(max(0, data.iactwp), nsegments - 1)
            self.routelbl.n_instances = nsegments
            self.route.set_vertex_count(2 * nsegments)
            routedata = np.empty(4 * nsegments, dtype=np.float32)
            routedata[0:4] = [data.aclat, data.aclon,
                              data.wplat[data.iactwp], data.wplon[data.iactwp]]

            routedata[4::4] = data.wplat[:-1]
            routedata[5::4] = data.wplon[:-1]
            routedata[6::4] = data.wplat[1:]
            routedata[7::4] = data.wplon[1:]

            self.route.update(vertex=routedata)
            wpname = ''
            for wp, alt, spd in zip(data.wpname, data.wpalt, data.wpspd):
                if alt < 0. and spd < 0.:
                    txt = wp[:12].ljust(24)  # No second line
                else:
                    txt = wp[:12].ljust(12)  # Two lines
                    if alt < 0:
                        txt += "-----/"
                    elif alt > actdata.translvl:
                        FL = int(round((alt / (100. * ft))))
                        txt += "FL%03d/" % FL
                    else:
                        txt += "%05d/" % int(round(alt / ft))

                    # Speed
                    if spd < 0:
                        txt += "--- "
                    elif spd > 2.0:
                        txt += "%03d" % int(round(spd / kts))
                    else:
                        txt += "M{:.2f}".format(spd)  # Mach number

                wpname += txt.ljust(24)  # Fill out with spaces
            self.routelbl.update(texdepth=np.array(wpname.encode('ascii', 'ignore')),
                                 lat=np.array(data.wplat, dtype=np.float32),
                                 lon=np.array(data.wplon, dtype=np.float32))
        else:
            self.route.set_vertex_count(0)
            self.routelbl.n_instances = 0

    def update_aircraft_data(self, data):
        ''' Update GPU buffers with new aircraft simulation data. '''
        if not self.initialized:
            return

        self.glsurface.makeCurrent()
        actdata = bs.net.get_nodedata()
        IP = socket.gethostbyname(socket.gethostname())
        ac_size = settings.ac_size
        text_size = settings.text_size

        # Filer on altitude     # BUG       # NEVER EXECUTED
        if actdata.filteralt:
            idx         = np.where((data.alt >= actdata.filteralt[0]) * (data.alt <= actdata.filteralt[1]))
            data.lat    = data.lat[idx]
            data.lon    = data.lon[idx]
            data.selhdg = data.selhdg[idx]
            data.trk    = data.trk[idx]
            data.selalt = data.selalt[idx]
            data.alt    = data.alt[idx]
            data.tas    = data.tas[idx]
            data.vs     = data.vs[idx]
            data.rpz    = data.rpz[idx]
            data.type   = data.type[idx]

        naircraft           = len(data.lat)
        actdata.translvl    = data.translvl
        # self.asas_vmin = data.vmin # TODO: array should be attribute not uniform
        # self.asas_vmax = data.vmax

        if naircraft == 0:
            self.cpalines.set_vertex_count(0)
        else:
            for i in range(naircraft):
                if actdata.acdata.alt[i] < actdata.translvl:
                    # print (actdata.acdata.rel[i])
                    actdata.acdata.rel[i] = True
                    # actdata.acdata.uco[i] = IP[-11:]
                    # stack ('REL ', actdata.acdata.id[i])
                    # cmd = 'REL' + ' ' + actdata.acdata.id[i]
                    # stack.stack(cmd)
                # print(actdata.acdata.rel[i])

            iuco = misc.get_indices(actdata.acdata.uco, IP[-11:])  #ip address
            self.lat.update(np.array(data.lat, dtype=np.float32))
            self.lon.update(np.array(data.lon, dtype=np.float32))
            self.latuacc.update(np.array(remove_data(data.lat, iuco), dtype=np.float32))
            self.lonuacc.update(np.array(remove_data(data.lon, iuco), dtype=np.float32))
            self.latuapp.update(np.array(data.lat[iuco], dtype=np.float32))
            self.lonuapp.update(np.array(data.lon[iuco], dtype=np.float32))

            self.hdg.update(np.array(data.trk, dtype=np.float32))
            self.alt.update(np.array(data.alt, dtype=np.float32))
            self.tas.update(np.array(data.tas, dtype=np.float32))
            self.rpz.update(np.array(data.rpz, dtype=np.float32))
            self.histsymblat.update(np.array(data.histsymblat, dtype=np.float32))
            self.histsymblon.update(np.array(data.histsymblon, dtype=np.float32))

            if hasattr(data, 'asasn') and hasattr(data, 'asase'):
                self.asasn.update(np.array(data.asasn, dtype=np.float32))
                self.asase.update(np.array(data.asase, dtype=np.float32))

            # CPA lines to indicate conflicts
            ncpalines   = np.count_nonzero(data.inconf)
            cpalines    = np.zeros(4 * ncpalines, dtype=np.float32)
            self.cpalines.set_vertex_count(2 * ncpalines)

            # Labels
            rawlabel    = ''
            rawlabel_lvnl = ''
            rawmlabel   = ''
            rawssrlabel = ''

            # Label position
            if data.id != self.id_prev:
                idchange = True
                idcreate = np.setdiff1d(data.id, self.id_prev).tolist()
            else:
                idchange = False
                idcreate = []
            labelpos      = np.empty((min(naircraft, MAX_NAIRCRAFT), 2), dtype=np.float32)
            leaderlinepos = np.empty((min(naircraft, MAX_NAIRCRAFT), 4), dtype=np.float32)
            mlabelpos     = np.empty((min(naircraft, MAX_NAIRCRAFT), 2), dtype=np.float32)

            # Colors
            color       = np.empty((min(naircraft, MAX_NAIRCRAFT), 4), dtype=np.uint8)

            selssd      = np.zeros(naircraft, dtype=np.uint8)
            confidx     = 0

            # Loop over aircraft
            zdata = zip(data.gs, data.id, data.inconf, data.ingroup, data.lat, data.lon, data.tcpamax, data.trk)
            for i, (gs, acid, inconf, ingroup, lat, lon, tcpa, trk) in enumerate(zdata):
                # ac_size = settings.ac_size
                # text_size = settings.text_size
                # Check for maximum aircraft
                if i >= MAX_NAIRCRAFT:
                    break

                # Labels
                if actdata.atcmode == 'BLUESKY':
                    rawlabel += baselabel(actdata, data, i)
                else:
                    if actdata.atcmode == 'APP':
                        label, mlabel, ssrlabel = applabel(actdata, data, i)
                        rawlabel_lvnl += label
                        rawmlabel     += mlabel
                        rawssrlabel   += ssrlabel
                    elif actdata.atcmode == 'ACC':
                        label, mlabel, ssrlabel = acclabel(actdata, data, i)
                        rawlabel_lvnl += label
                        rawmlabel     += mlabel
                        rawssrlabel   += ssrlabel
                    elif actdata.atcmode == 'TWR':
                        label, mlabel, ssrlabel = twrlabel(actdata, data, i)
                        rawlabel_lvnl += label
                        rawmlabel     += mlabel
                        rawssrlabel   += ssrlabel

                    # Label position
                    if idchange:
                        if acid in idcreate:
                            labelpos[i] = initial_labelpos(data, i)
                            offsetx, offsety = labelpos[i]
                            leaderlinepos[i] = leaderline_vertices(actdata, offsetx, offsety)
                        else:
                            i_prev = self.id_prev.index(acid)
                            labelpos[i] = self.labelpos[i_prev]

                            if data.tracklbl[i]:
                                leaderlinepos[i] = leaderline_vertices(actdata, labelpos[i][0], labelpos[i][1])
                            else:
                                leaderlinepos[i] = [0, 0, 0, 0]
                    else:
                        labelpos[i] = self.labelpos[i]

                        if data.tracklbl[i]:
                            leaderlinepos[i] = leaderline_vertices(actdata, labelpos[i][0], labelpos[i][1])

                        else:
                            leaderlinepos[i] = [0, 0, 0, 0]

                    # Microlabel position
                    mlabelpos[i] = initial_micropos(data, i)

                # Colours
                if inconf:
                    if actdata.ssd_conflicts:
                        selssd[i] = 255
                    color[i, :] = palette.conflict + (255,)
                    lat1, lon1 = geo.qdrpos(lat, lon, trk, tcpa * gs / nm)
                    cpalines[4 * confidx: 4 * confidx +
                             4] = [lat, lon, lat1, lon1]
                    confidx += 1
                # Selected aircraft
                elif actdata.atcmode != 'BLUESKY' and acid == console.Console._instance.id_select:
                    rgb = (218, 218, 0) + (255,)
                    color[i, :] = rgb
                else:
                    # Get custom color if available, else default
                    rgb = palette.aircraft
                    if ingroup:
                        for groupmask, groupcolor in actdata.custgrclr.items():
                            if ingroup & groupmask:
                                rgb = groupcolor
                                break
                    rgb = actdata.custacclr.get(acid, rgb)
                    color[i, :] = tuple(rgb) + (255,)

                #  Check if aircraft is selected to show SSD
                if actdata.ssd_all or acid in actdata.ssd_ownship:
                    selssd[i] = 255

            if len(actdata.ssd_ownship) > 0 or actdata.ssd_conflicts or actdata.ssd_all:
                self.ssd.update(selssd=selssd)

            self.cpalines.update(vertex=cpalines)

            self.color.update(color)
            self.coloruapp.update(np.array(color[iuco], dtype=np.uint8))
            self.coloruacc.update(np.array(remove_data(color, iuco), dtype=np.uint8))


            # BlueSky default label (ATC mode BLUESKY)
            if actdata.atcmode == 'BLUESKY':
                self.lbl.update(np.array(rawlabel.encode('utf8'), dtype=np.string_))
            # LVNL labels
            else:
                # Update track label
                self.lbl_lvnl.update(np.array(rawlabel_lvnl.encode('utf8'), dtype=np.string_))
                # Update SSR label
                self.ssrlbl.update(np.array(rawssrlabel.encode('utf8'), dtype=np.string_))
                # Update micro label
                self.mlbl.update(np.array(rawmlabel.encode('utf8'), dtype=np.string_))

                #Label position
                self.labelpos = labelpos
                self.id_prev = data.id
                self.lbloffset.update(np.array(self.labelpos, dtype=np.float32))
                self.mlabelpos = mlabelpos
                self.mlbloffset.update(np.array(self.mlabelpos, dtype=np.float32))

                if self.pluginlbloffset is not None:
                    self.pluginlbloffset.update(np.array(self.labelpos+self.pluginlabelpos, dtype=np.float32))

                # Leader line update
                self.leaderlinepos = leaderlinepos
                self.leaderlines.update(vertex=self.leaderlinepos, lat=data.lat, lon=data.lon, color=color)
            
            # If there is a visible route, update the start position
            if self.route_acid in data.id:
                idx = data.id.index(self.route_acid)
                self.route.vertex.update(np.array([data.lat[idx], data.lon[idx]], dtype=np.float32))

    def update_labelpos(self, x, y):
        """
        Function: Update the label position for the selected aircraft
        Args:
            x:  Cursor x pixel coordinate
            y:  Cursor y pixel coordinate
        Returns: -

        Created by: Bob van Dillen
        Date: 22-2-2022
        """

        # Sizes
        ac_size = settings.ac_size
        text_size = settings.text_size
        text_width = text_size
        text_height = text_size * 1.2307692307692308
        block_size = (4*text_height, 8*text_width)

        # Node data
        actdata = bs.net.get_nodedata()

        # Get index selected aircraft
        idx = misc.get_indices(actdata.acdata.id, console.Console._instance.id_select)

        # Check if selected aircraft exists
        if len(idx) != 0 and actdata.acdata.tracklbl[idx]:
            idx = idx[0]

            # Get cursor position change
            dx = x - self.glsurface.prevmousepos[0]
            dy = y - self.glsurface.prevmousepos[1]

            # Add cursor position change to label position
            self.labelpos[idx][0] += dx
            self.labelpos[idx][1] -= dy

            # Update label offset
            self.lbloffset.update(np.array(self.labelpos, dtype=np.float32))
            if self.pluginlbloffset is not None:
                self.pluginlbloffset.update(np.array(self.labelpos+self.pluginlabelpos, dtype=np.float32))

            # Leader lines
            self.leaderlinepos[idx] = leaderline_vertices(actdata, self.labelpos[idx][0], self.labelpos[idx][1])

            self.leaderlines.update(vertex=self.leaderlinepos)

    def plugin_init(self, blocksize=None, position=None):
        """
        Function: Initialize and create plugin buffers and attributes
        Args:
            blocksize:  Label block size [tuple]
            position:   Text position (line (y), character (x))  [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-2-2022
        """

        self.glsurface.makeCurrent()

        # Sizes
        ac_size = settings.ac_size
        text_size = settings.text_size
        text_width = text_size
        text_height = text_size * 1.2307692307692308

        # Process position
        self.pluginlabelpos = np.array([position[1]*text_width, -position[0]*text_height], dtype=np.float32)

        # Initialize
        self.pluginlbl       = glh.GLBuffer()
        self.pluginlbloffset = glh.GLBuffer()
        self.pluginlabel     = glh.Text(settings.text_size, blocksize)

        # Create
        self.pluginlbl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.pluginlbloffset.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.pluginlabel.create(self.pluginlbl, self.lat, self.lon, self.color, self.pluginlbloffset, instanced=True)

        # Update position
        if len(self.labelpos) != 0:
            self.pluginlbloffset.update(np.array(self.labelpos+self.pluginlabelpos, dtype=np.float32))

        # Draw
        self.show_pluginlabel = True

    def plugin_rangebar(self, blocksize=None, position=None):
        """
        Function: Initialize and create t-bar rangebar plugin buffers and attributes
        Args:
            blocksize:  Label block size [tuple]
            position:   Text position (line (y), character (x))  [tuple]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 22-3-2022
        """
        self.glsurface.makeCurrent()
        actdata = bs.net.get_nodedata()
        naircraft = len(actdata.acdata.id)
        tbar_labelpos = np.empty((min(naircraft, MAX_NAIRCRAFT), 2), dtype=np.float32)

        # Sizes
        ac_size = settings.ac_size
        text_size = settings.text_size
        text_width = text_size
        text_height = text_size * 1.2307692307692308

        acverticeslvnl = np.array([(-0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, 0.5 * ac_size),
                                   (0.5 * ac_size, -0.5 * ac_size),
                                   (-0.5 * ac_size, 0.5 * ac_size),
                                   (-0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, -0.5 * ac_size),
                                   (0.5 * ac_size, 0.5 * ac_size),
                                   (-0.5 * ac_size, 0.5 * ac_size)],
                                  dtype=np.float32)  # a square with diagonal

        # Initialize t-bar ac
        self.tbar_ac = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)
        self.tbar_lat = glh.GLBuffer()
        self.tbar_lon = glh.GLBuffer()

        # Initialize t-bar label
        self.tbar_labelpos = np.array([], dtype=np.float32)
        self.tbar_lbl = glh.GLBuffer()
        self.tbar_lbloffset = glh.GLBuffer()
        self.tbar_label = glh.Text(settings.text_size, blocksize)

        # Create t-bar aircraft
        self.tbar_lon.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.tbar_lat.create(MAX_NAIRCRAFT * 4, glh.GLBuffer.StreamDraw)
        self.tbar_ac.create(vertex=acverticeslvnl)
        self.tbar_ac.set_attribs(lat=self.tbar_lat, lon=self.tbar_lon, color=self.color, instance_divisor=1)

        # Create t-bar label
        self.tbar_lbl.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.tbar_lbloffset.create(MAX_NAIRCRAFT * 24, glh.GLBuffer.StreamDraw)
        self.tbar_label.create(self.tbar_lbl, self.tbar_lat, self.tbar_lon, self.color, self.tbar_lbloffset,
                               instanced=True)

        # Update
        for i in range(len(actdata.acdata.id)):
            tbar_labelpos[i] = [-position[1]*text_width, position[0]*text_height]
        self.tbar_labelpos = tbar_labelpos
        self.tbar_lbloffset.update(np.array(self.tbar_labelpos, dtype=np.float32))

        # Draw
        self.show_tbar_ac = True

"""
Static functions
"""

def baselabel(actdata, data, i):
    """
    Function: Create base label
    Args:
        actdata:    node data [class]
        data:       aircraft data [class]
        i:          index for data [int]
    Returns:
        rawlabel:   label string [str]

    Created by: Bob van Dillen
    Date: 13-1-2022
    """

    # Empty label
    label = ''

    label += '%-8s' % data.id[i][:8]
    if actdata.show_lbl == 2:
        if data.alt[i] <= data.translvl:
            label += '%-5d' % int(data.alt[i] / ft + 0.5)
        else:
            label += 'FL%03d' % int(data.alt[i] / ft / 100. + 0.5)
        vsarrow = 30 if data.vs[i] > 0.25 else 31 if data.vs[i] < -0.25 else 32
        label += '%1s  %-8d' % (chr(vsarrow),
                                int(data.cas[i] / kts + 0.5))
    else:
        label += 2*8*' '
    return label


def applabel(actdata, data, i):
    """
    Function: Create approach label
    Args:
        actdata:    node data [class]
        data:       aircraft data [class]
        i:          index for data [int]
    Returns:
        label:      track label string [str]
        mlabel:     micro label string [str]
        ssrlabel:   ssr label string [str]

    Created by: Bob van Dillen
    Date: 21-12-2021
    """

    IP = socket.gethostbyname(socket.gethostname())

    # Empty labels
    label    = ''
    mlabel   = ''
    ssrlabel = ''

    # Track label
    if data.tracklbl[i]:
        # Line 1
        label += '%-8s' % data.id[i][:8]

        # Line 2
        label += '%-3s' % leading_zeros(data.alt[i]/ft/100)[-3:]
        if actdata.acdata.alt[i] < actdata.translvl:
            label += '%-1s' % 'A'
        else:
            label += '%-1s' % ' '
        if data.uco[i] == IP[-11:] and data.selalt[i] != 0:
            label += '%-3s' % leading_zeros(data.selalt[i]/ft/100)[-3:]
        else:
            label += '%-3s' % '   '
        label += '%-1s' % ' '

        # Line 3
        label += '%-4s' % str(data.type[i])[:4]
        if data.uco[i] == IP[-11:] and data.selhdg[i] != 0:
            label += '%-3s' % leading_zeros(data.selhdg[i])[:3]
        elif data.flighttype[i] == 'INBOUND':
            label += '%-3s' % data.arr[i].replace('ARTIP', 'ATP')[:3]
        elif data.flighttype[i] == 'OUTBOUND':
            label += '%-3s' % data.sid[i][:3]
        else:
            label += '%-3s' % '   '
        label += '%-1s' % ' '

        # Line 4
        label += '%-3s' % leading_zeros(data.gs[i]/kts)[:3]
        if data.wtc[i].upper() == 'H' or data.wtc[i].upper() == 'J':
            label += '%-1s' % str(data.wtc[i])[:1]
        else:
            label += '%-1s' % ' '
        if data.uco[i] == IP[-11:] and data.selspd[i] != 0:
            label += '%-3s' % leading_zeros(data.selspd[i]/kts)[:3]
        else:
            label += '%-3s' % 'SPD'
        label += '%-1s' % ' '
    else:
        label += 8*4*' '

    # Micro label   #elif is tried for gmp eor
    if data.mlbl[i]:
        if data.flighttype[i].upper() == 'OUTBOUND':
            mlabel += '      '+chr(30)   #30
        elif (len(data.rwy[i]) == 3) and ((data.rwy[i] in ['18R', '18R_E']) or ((data.arr[i] in ['ATP18R', 'RIV18R', 'RIV18REOR', 'SUG18R', 'SUG18REOR']))):
            mlabel += '%-7s' % ('    ' + data.rwy[i][:7])
        elif (len(data.rwy[i]) == 5) and ((data.rwy[i] in ['18R', '18R_E']) or data.arr[i] in ['ATP18R', 'RIV18R', 'RIV18REOR', 'SUG18R', 'SUG18REOR']):
            mlabel += '%-7s' % ('  '+data.rwy[i][:7])
        elif (len(data.rwy[i]) == 2):
            mlabel += '%-7s' % ('     ' + data.rwy[i][:7])
        else:
            mlabel += '%-7s' % data.rwy[i][:7]
    else:
        mlabel += 7*' '

    # SSR label
    ssrlbl = data.ssrlbl[i].split(';')
    # Mode A
    if 'A' in ssrlbl and data.ssr[i] != 0:
        ssrlabel += '%-7s' % str(data.ssr[i])[:7]
    else:
        ssrlabel += 7*' '
    # Mode C
    if 'C' in ssrlbl:
        ssrlabel += '%-3s' % leading_zeros(data.alt[i]/ft/100)[:3]
        if data.alt[i] < actdata.translvl:
            ssrlabel += '%-4s' % 'A   '
        else:
            ssrlabel += '%-4s' % '    '
    else:
        ssrlabel += 7*' '

    # ACID
    if 'ACID' in ssrlbl:
        ssrlabel += '%-7s' % data.id[i][:7]
    else:
        ssrlabel += 7 * ' '

    return label, mlabel, ssrlabel


def acclabel(actdata, data, i):
    """
    Function: Create acc label
    Args:
        actdata:    node data [class]
        data:       aircraft data [class]
        i:          index for data [int]
    Returns:
        label:      track label string [str]
        mlabel:     micro label string [str]
        ssrlabel:   ssr label string [str]

    Created by: Bob van Dillen
    Date: 21-12-2021
    """

    IP = socket.gethostbyname(socket.gethostname())

    # Empty labels
    label    = ''
    ssrlabel = ''
    mlabel   = ''

    # Track label
    if data.tracklbl[i]:
        # Line 1
        label += '%-8s' % data.id[i][:8]

        # Line 2
        label += '%-3s' % leading_zeros(data.alt[i]/ft/100)[-3:]
        if data.alt[i] < actdata.translvl:
            label += '%-1s' % 'A'
        else:
            label += '%-1s' % ' '
        if data.uco[i] == IP[-11:] and data.selalt[i] != 0:
            label += '%-3s' % leading_zeros(data.selalt[i]/ft/100)[-3:]
        else:
            label += '%-3s' % '   '
        label += '%-1s' % ' '

        # Line 3
        label += '%-3s' % '...'
        label += '%-1s' % ' '
        label += '%-3s' % leading_zeros(data.gs[i]/kts)[:3]
        if data.wtc[i].upper() == 'H' or data.wtc[i].upper() == 'J':
            label += '%-1s' % str(data.wtc[i])[:1]
        else:
            label += '%-1s' % ' '

        # Line 4
        if data.uco[i] == IP[-11:] and data.selspd[i] != 0:
            label += '%-1s' % 'I'
            label += '%-3s' % leading_zeros(data.selspd[i]/kts)[:3]
        else:
            label += '%-4s' % '    '
        label += '%-4s' % data.type[i][:4]
    else:
        label += 8*4*' '

    # Micro label
    if data.mlbl[i]:
        if data.flighttype[i].upper() == 'INBOUND':
            mlabel += '  '+chr(31)
        else:
            mlabel += 3*' '
    else:
        mlabel += 3*' '

    # SSR label
    ssrlbl = data.ssrlbl[i].split(';')
    # ACID
    if 'ACID' in ssrlbl:
        ssrlabel += '%-7s' % data.id[i][:7]
    else:
        ssrlabel += 7*' '
    # Mode A
    if 'A' in ssrlbl and data.ssr[i] != 0:
        ssrlabel += '%-7s' % str(data.ssr[i])[:7]
    else:
        ssrlabel += 7*' '
    # Mode C
    if 'C' in ssrlbl:
        ssrlabel += '%-3s' % leading_zeros(data.alt[i]/ft/100)[:3]
        if data.alt[i] < actdata.translvl:
            ssrlabel += '%-4s' % 'A   '
        else:
            ssrlabel += '%-4s' % '    '
    else:
        ssrlabel += 7*' '

    return label, mlabel, ssrlabel


def twrlabel(actdata, data, i):
    """
    Function: Create acc label
    Args:
        actdata:    node data [dict]
        data:       aircraft data [dict]
        i:          index for data [int]
    Returns:
        label:      track label string [str]
        mlabel:     micro label string [str]
        ssrlabel:   ssr label string [str]

    Created by: Bob van Dillen
    Date: 21-12-2021
    """

    # Empty label
    label    = ''
    mlabel   = ''
    ssrlabel = ''

    # Line 1
    label += '%-8s' % data.id[i][:8]
    if actdata.show_lbl == 2:
        # Line 2
        if data.flighttype[i] == "INBOUND":
            label += 8*' '
        else:
            label += '%-5s' % data.sid[i][:5]
            label += ' '
            label += '%-2s' % data.rwy[i][-2:]
        # Line 3
        label += '%-8s' % data.type[i][:8]
        # Line 4
        label += 8*' '
    else:
        label += 8*4*' '

    mlabel += 3*1*' '
    ssrlabel += 7*3*' '

    return label, mlabel, ssrlabel


def leading_zeros(number):
    """
    Function: Add leading zeros to number string (e.g. 005)
    Args:
        number: number to be displayed [int, float]
    Returns:
        number: number with leading zeros [str]

    Created by: Bob van Dillen
    Date: 16-12-2021
    """

    if number < 0:
        number = 0
    if number < 9.5:
        return '00'+str(round(number))
    elif number < 99.5:
        return '0'+str(round(number))
    else:
        return str(round(number))


def leaderline_vertices(actdata, offsetx, offsety):
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

    # Label is on top of aircaft symbol
    if -block_size[1] <= offsetx <= 0 and -text_height <= offsety <= 3*text_height:
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

def draw_uco(uco): # for instances
    """
    Function: Returns aircrafts that are UCO
    Args:
        uco:    uco array [array with str dtype]
    Returns:
        uco:    uco array [array with str dtype]

    Created by: Ajay Kumbhar
    Date:
    """
    IP = socket.gethostbyname(socket.gethostname())
    uco = [i for i in uco if i == IP]
    return uco

def remove_data(data,idx): # for attributes
    """
    Function: Deletes the data for flights under UCO
    Args:
        data:   Data Array such as lat/lon [array]
        idx:    Index of data need to be deleted [int]
    Returns:
        data:   Updated Data Array such as lat/lon/color [array]

    Created by: Ajay Kumbhar
    Date:
    """
    data = np.delete(data, idx, axis=0)
    return data

def initial_labelpos(data, i):
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
        labelpos = [-125, 0]  # -125
    else:
        labelpos = [50, 0]

    #   #   Enable data.arr only for GMPEOR scenario
    # if data.arr[i] in ['ATP18R', 'RIV18R', 'RIV18REOR', 'SUG18R', 'SUG18REOR']:
    #     labelpos = [-150, 0]  # -125
    # else:
    #     labelpos = [80, 0]  # 50  #75 for R indication

    return labelpos

def initial_micropos(data, i):
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
        mlabelpos = [-8 * 0.8 * text_size - ac_size, 0.5 * ac_size]   #-3

    #   #   Enable data.arr only for GMPEOR scenario
    # if data.arr[i] in ['ATP18C', 'ATP18CEOR', 'RIV18C', 'SUG18C']:
    #     mlabelpos = [2 * 0.8 * text_size - ac_size, 0.5 * ac_size]  # 2   #0.5-y
    # else:
    #     mlabelpos = [-8 * 0.8 * text_size - ac_size, 0.5 * ac_size]  # -3

    return mlabelpos
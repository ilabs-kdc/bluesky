''' BlueSky OpenGL radar view. '''
from os import path
from ctypes import c_float, c_int, Structure
import numpy as np

from PyQt5.QtCore import Qt, QEvent, QT_VERSION

import bluesky as bs
from bluesky.core import Signal
from bluesky.ui import palette
from bluesky.ui.qtgl import glhelpers as glh
from bluesky.ui.radarclick import radarclick
from bluesky.ui.qtgl import console
from bluesky import settings
from bluesky.tools import geo
from .gltraffic import Traffic
from .glmap import Map
from .glnavdata import Navdata
from .glpoly import Poly
from .gltiledmap import TiledMap
# Register settings defaults
settings.set_variable_defaults(gfx_path='data/graphics')
# Register palette defaults
palette.set_default_colours(background=(179, 179, 179))

# Qt smaller than 5.6.2 needs a different approach to pinch gestures
CORRECT_PINCH = False
if QT_VERSION <= 0x050600:
    import platform
    CORRECT_PINCH = platform.system() == 'Darwin'


class RadarShaders(glh.ShaderSet):
    ''' Shaderset for the radar view. '''
    # Vertex type enum: Individual vertices can correspond to lat/lon coordinates, screen coordinates, or meters.
    VERTEX_IS_LATLON, VERTEX_IS_METERS, VERTEX_IS_SCREEN = list(range(3))
    def __init__(self, parent):
        super().__init__(parent)

        class GlobalData(Structure):
            _fields_ = [("wrapdir", c_int), ("wraplon", c_float), ("panlat", c_float), ("panlon", c_float),
                        ("zoom", c_float), ("screen_width", c_int), ("screen_height", c_int), ("vertex_scale_type", c_int)]
        self.data = GlobalData()

    def create(self):
        super().create()
        self.set_shader_path(path.join(settings.gfx_path, 'shaders'))
        # Load all shaders for this shader set
        self.load_shader('normal', 'radarwidget-normal.vert',
                         'radarwidget-color.frag')
        self.load_shader('textured', 'radarwidget-normal.vert',
                         'radarwidget-texture.frag')
        self.load_shader('tiled', 'radarwidget-normal.vert',
                         'radarwidget-tiled.frag')
        self.load_shader('text', 'radarwidget-text.vert',
                         'radarwidget-text.frag')
        self.load_shader('dashed', 'radarwidget-dashed.vert',
                         'radarwidget-dashed.frag')
        self.load_shader('ssd', 'ssd.vert', 'ssd.frag', 'ssd.geom')

    def set_wrap(self, wraplon, wrapdir):
        self.data.wrapdir = wrapdir
        self.data.wraplon = wraplon

    def set_pan_and_zoom(self, panlat, panlon, zoom):
        self.data.panlat = panlat
        self.data.panlon = panlon
        self.data.zoom = zoom

    def set_win_width_height(self, w, h):
        self.data.screen_width = w
        self.data.screen_height = h

    def enable_wrap(self, flag=True):
        if not flag:
            wrapdir = self.data.wrapdir
            self.data.wrapdir = 0
            self.update_ubo('global_data', self.data, 0, 4)
            self.data.wrapdir = wrapdir
        else:
            self.update_ubo('global_data', self.data, 0, 4)

    def set_vertex_scale_type(self, vertex_scale_type):
        self.data.vertex_scale_type = vertex_scale_type
        self.update_ubo('global_data', self.data)


class RadarWidget(glh.RenderWidget):
    ''' The BlueSky radar view. '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.prevwidth = self.prevheight = 600
        self.panlat = 0.0
        self.panlon = 0.0
        self.zoom = 1.0
        self.ar = 1.0
        self.flat_earth = 1.0
        self.wraplon = int(-999)
        self.wrapdir = int(0)
        self.initialized = False

        self.panzoomchanged = False
        self.labelposchanged = False
        self.mousedragged = False
        self.mousepos = (0, 0)
        self.prevmousepos = (0, 0)

        self.shaderset = RadarShaders(self)
        self.set_shaderset(self.shaderset)

        # Add default objects
        self.addobject(Map(parent=self))
        self.addobject(Traffic(parent=self))
        self.addobject(Navdata(parent=self))
        self.addobject(Poly(parent=self))

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.grabGesture(Qt.PanGesture)
        self.grabGesture(Qt.PinchGesture)
        # self.grabGesture(Qt.SwipeGesture)
        self.setMouseTracking(True)

        # Signals and slots
        bs.net.actnodedata_changed.connect(self.actdata_changed)
        self.mouse_event = Signal('radarmouse')
        self.panzoom_event = Signal('panzoom')
        self.labelpos_event = Signal('labelpos')


    def actdata_changed(self, nodeid, nodedata, changed_elems):
        ''' Update buffers when a different node is selected, or when
            the data of the current node is updated. '''

        # Update pan/zoom
        if 'PANZOOM' in changed_elems:
            self.panzoom(pan=nodedata.pan, zoom=nodedata.zoom, absolute=True, screenrange=nodedata.screenrange)
        if 'ATCMODE' in changed_elems:
            if nodedata.atcmode == 'APP':
                self.panzoom(pan=[52.309, 4.764], absolute=True, screenrange=36.)
                self.set_background()
            if nodedata.atcmode == 'ACC':
                self.panzoom(pan=[52.309, 4.764], absolute=True, screenrange=120.)
                self.set_background()
            if nodedata.atcmode == 'TWR':
                self.panzoom(pan=[52.309, 4.764], absolute=True, screenrange=2.)
                self.set_background()

    def initializeGL(self):
        """Initialize OpenGL, VBOs, upload data on the GPU, etc."""
        super().initializeGL()

        # Set initial values for the global uniforms
        self.shaderset.set_wrap(self.wraplon, self.wrapdir)
        self.shaderset.set_pan_and_zoom(self.panlat, self.panlon, self.zoom)

        # background color
        rgb_background = palette.background
        glh.gl.glClearColor(rgb_background[0]/255, rgb_background[1]/255, rgb_background[2]/255, 0)
        glh.gl.glEnable(glh.gl.GL_BLEND)
        glh.gl.glBlendFunc(glh.gl.GL_SRC_ALPHA, glh.gl.GL_ONE_MINUS_SRC_ALPHA)

        self.initialized = True

    def set_background(self, color=None):
        """
        Function: Change the background color
        Args:
            color:  red, blue, green, color [tuple]
        Returns: -

        Create by: Bob van Dillen
        Date: 21-2-2022
        """

        self.makeCurrent()

        # Define color
        if color:
            rgb_background = color
        else:
            rgb_background = palette.background

        # Set the background color (r,b,g in range [0, 1]
        glh.gl.glClearColor(rgb_background[0]/255, rgb_background[1]/255, rgb_background[2]/255, 0)
        glh.gl.glEnable(glh.gl.GL_BLEND)
        glh.gl.glBlendFunc(glh.gl.GL_SRC_ALPHA, glh.gl.GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport."""
        # update the window size

        # Calculate zoom so that the window resize doesn't affect the scale, but only enlarges or shrinks the view
        zoom = float(self.prevwidth) / float(width)
        origin = (width / 2, height / 2)

        # Update width, height, and aspect ratio
        self.prevwidth, self.prevheight = width, height
        self.ar = float(width) / max(1, float(height))
        self.shaderset.set_win_width_height(width, height)

        # Update zoom
        self.panzoom(zoom=zoom, origin=origin)

    def pixelCoordsToGLxy(self, x, y):
        """Convert screen pixel coordinates to GL projection coordinates (x, y range -1 -- 1)
        """
        # GL coordinates (x, y range -1 -- 1)
        glx = (2.0 * x / self.prevwidth - 1.0)
        gly = -(2.0 * y / self.prevheight - 1.0)
        return glx, gly

    def pixelCoordsToLatLon(self, x, y):
        """Convert screen pixel coordinates to lat/lon coordinates
        """
        glx, gly = self.pixelCoordsToGLxy(x, y)

        # glxy   = zoom * (latlon - pan)
        # latlon = pan + glxy / zoom
        lat = self.panlat + gly / (self.zoom * self.ar)
        lon = self.panlon + glx / (self.zoom * self.flat_earth)
        return lat, lon

    def GLxyTopixelCoords(self, glx, gly):
        """
        Function: Convert GL projection coordinates to screen pixel coordinates
        Args:
            glx:    GL projection x coordinate [float]
            gly:    GL projection y coordinate [float]
        Returns:
            x:      screen pixel x coordinate [float]
            y:      screen pixel y coordinate [float]

        Created by: Bob van Dillen
        Date: 18-2-2022
        """

        x = ((glx + 1.0)*self.prevwidth)/2.0
        y = ((-gly + 1.0)*self.prevheight)/2.0

        return x, y

    def LatLonTopixelCoords(self, lat, lon):
        """
        Function: Convert lat/lon coordinates to screen pixel coordinates
        Args:
            lat:    latitude [float]
            lon:    longitude [float]
        Returns:
            x:      screen pixel x coordinate [float]
            y:      screen pixel y coordinate [float]

        Created by: Bob van Dillen
        Date: 18-2-2022
        """

        gly = (lat - self.panlat)*(self.zoom * self.ar)
        glx = (lon - self.panlon)*(self.zoom * self.flat_earth)

        x, y = self.GLxyTopixelCoords(glx, gly)

        return x, y

    def viewportlatlon(self):
        ''' Return the viewport bounds in lat/lon coordinates. '''
        return (self.panlat + 1.0 / (self.zoom * self.ar),
                self.panlon - 1.0 / (self.zoom * self.flat_earth),
                self.panlat - 1.0 / (self.zoom * self.ar),
                self.panlon + 1.0 / (self.zoom * self.flat_earth))

    def panzoom(self, pan=None, zoom=None, origin=None, absolute=False, screenrange=None):
        if not self.initialized:
            return False

        if pan:
            # Absolute pan operation
            if absolute:
                self.panlat = pan[0]
                self.panlon = pan[1]
            # Relative pan operation
            else:
                self.panlat += pan[0]
                self.panlon += pan[1]

            # Don't pan further than the poles in y-direction
            self.panlat = min(max(self.panlat, -90.0 + 1.0 /
                                  (self.zoom * self.ar)), 90.0 - 1.0 / (self.zoom * self.ar))

            # Update flat-earth factor and possibly zoom in case of very wide windows (> 2:1)
            self.flat_earth = np.cos(np.deg2rad(self.panlat))
            self.zoom = max(self.zoom, 1.0 / (180.0 * self.flat_earth))

        if zoom:
            if absolute:
                # Limit zoom extents in x-direction to [-180:180], and in y-direction to [-90:90]
                self.zoom = max(
                    zoom, 1.0 / min(90.0 * self.ar, 180.0 * self.flat_earth))
            else:
                prevzoom = self.zoom
                glx, gly = self.pixelCoordsToGLxy(
                    *origin) if origin else (0, 0)
                self.zoom *= zoom

                # Limit zoom extents in x-direction to [-180:180], and in y-direction to [-90:90]
                self.zoom = max(self.zoom, 1.0 / min(90.0 *
                                                     self.ar, 180.0 * self.flat_earth))

                # Correct pan so that zoom actions are around the mouse position, not around 0, 0
                # glxy / zoom1 - pan1 = glxy / zoom2 - pan2
                # pan2 = pan1 + glxy (1/zoom2 - 1/zoom1)
                self.panlon = self.panlon - glx * \
                    (1.0 / self.zoom - 1.0 / prevzoom) / self.flat_earth
                self.panlat = self.panlat - gly * \
                    (1.0 / self.zoom - 1.0 / prevzoom) / self.ar

            # Don't pan further than the poles in y-direction
            self.panlat = min(max(self.panlat, -90.0 + 1.0 /
                                  (self.zoom * self.ar)), 90.0 - 1.0 / (self.zoom * self.ar))

            # Update flat-earth factor
            self.flat_earth = np.cos(np.deg2rad(self.panlat))

        if screenrange:
            # Get maximum latitude and longitude
            latmax = geo.qdrpos(self.panlat, self.panlon, 0, screenrange)[0]
            lonmax = geo.qdrpos(self.panlat, self.panlon, 90, screenrange)[1]

            # Determine zoom
            zoomlat = 1 / ((latmax - self.panlat) * self.ar)
            zoomlon = 1 / ((lonmax - self.panlon) * np.cos(np.radians(self.panlat)))

            self.zoom = min(zoomlat, zoomlon)

        # Check for necessity wrap-around in x-direction
        self.wraplon = -999.9
        self.wrapdir = 0
        if self.panlon + 1.0 / (self.zoom * self.flat_earth) < -180.0:
            # The left edge of the map has passed the right edge of the screen: we can just change the pan position
            self.panlon += 360.0
        elif self.panlon - 1.0 / (self.zoom * self.flat_earth) < -180.0:
            # The left edge of the map has passed the left edge of the screen: we need to wrap around to the left
            self.wraplon = float(
                np.ceil(360.0 + self.panlon - 1.0 / (self.zoom * self.flat_earth)))
            self.wrapdir = -1
        elif self.panlon - 1.0 / (self.zoom * self.flat_earth) > 180.0:
            # The right edge of the map has passed the left edge of the screen: we can just change the pan position
            self.panlon -= 360.0
        elif self.panlon + 1.0 / (self.zoom * self.flat_earth) > 180.0:
            # The right edge of the map has passed the right edge of the screen: we need to wrap around to the right
            self.wraplon = float(
                np.floor(-360.0 + self.panlon + 1.0 / (self.zoom * self.flat_earth)))
            self.wrapdir = 1

        self.shaderset.set_wrap(self.wraplon, self.wrapdir)

        # update pan and zoom on GPU for all shaders
        self.shaderset.set_pan_and_zoom(self.panlat, self.panlon, self.zoom)
        # Update pan and zoom in centralized nodedata
        bs.net.get_nodedata().panzoom((self.panlat, self.panlon), self.zoom)
        self.panzoom_event.emit(False)
        return True

    def event(self, event):
        ''' Event handling for input events. '''
        if event.type() == QEvent.Wheel:
            # For mice we zoom with control/command and the scrolwheel
            if event.modifiers() & Qt.ControlModifier:
                origin = (event.pos().x(), event.pos().y())
                zoom = 1.0
                try:
                    if event.pixelDelta():
                        # High resolution scroll
                        zoom *= (1.0 + 0.01 * event.pixelDelta().y())
                    else:
                        # Low resolution scroll
                        zoom *= (1.0 + 0.001 * event.angleDelta().y())
                except AttributeError:
                    zoom *= (1.0 + 0.001 * event.delta())
                self.panzoomchanged = True
                return self.panzoom(zoom=zoom, origin=origin)

            # For touchpad scroll (2D) is used for panning
            else:
                try:
                    dlat = 0.01 * event.pixelDelta().y() / (self.zoom * self.ar)
                    dlon = -0.01 * event.pixelDelta().x() / (self.zoom * self.flat_earth)
                    self.panzoomchanged = True
                    return self.panzoom(pan=(dlat, dlon))
                except AttributeError:
                    pass

        # For touchpad, pinch gesture is used for zoom
        elif event.type() == QEvent.Gesture:
            pan = zoom = None
            dlat = dlon = 0.0
            for g in event.gestures():
                if g.gestureType() == Qt.PinchGesture:
                    event.accept(g)
                    zoom = g.scaleFactor() * (zoom or 1.0)
                    if CORRECT_PINCH:
                        zoom /= g.lastScaleFactor()
                elif g.gestureType() == Qt.PanGesture:
                    event.accept(g)
                    if abs(g.delta().y() + g.delta().x()) > 1e-1:
                        dlat += 0.005 * g.delta().y() / (self.zoom * self.ar)
                        dlon -= 0.005 * g.delta().x() / (self.zoom * self.flat_earth)
                        pan = (dlat, dlon)
            if pan is not None or zoom is not None:
                self.panzoomchanged = True
                return self.panzoom(pan, zoom, self.mousepos)

        elif event.type() == QEvent.MouseButtonPress and (event.button() & Qt.LeftButton or event.button() & Qt.RightButton):
            self.mousedragged = False
            # For mice we pan with control/command and mouse movement.
            # Mouse button press marks the beginning of a pan
            self.prevmousepos = (event.x(), event.y())

        elif event.type() == QEvent.MouseButtonRelease and \
                event.button() & Qt.LeftButton and not self.mousedragged:
            lat, lon = self.pixelCoordsToLatLon(event.x(), event.y())
            actdata = bs.net.get_nodedata()
            tostack, tocmdline = radarclick(console.get_cmdline(), lat, lon,
                                            actdata.acdata, actdata.routedata, actdata)
            console.process_cmdline((tostack + '\n' + tocmdline) if tostack else tocmdline)

        elif event.type() == QEvent.MouseMove:
            self.mousedragged = True
            self.mousepos = (event.x(), event.y())
            if event.buttons() & Qt.RightButton:
                dlat = 0.003 * \
                    (event.y() - self.prevmousepos[1]) / (self.zoom * self.ar)
                dlon = 0.003 * \
                    (self.prevmousepos[0] - event.x()) / \
                    (self.zoom * self.flat_earth)
                self.prevmousepos = (event.x(), event.y())
                self.panzoomchanged = True
                return self.panzoom(pan=(dlat, dlon))
            elif event.buttons() & Qt.LeftButton:
                self.labelpos_event.emit(event.x(), event.y())
                self.prevmousepos = (event.x(), event.y())
                self.labelposchanged = True

        elif event.type() == QEvent.TouchBegin:
            # Accept touch start to enable reception of follow-on touch update and touch end events
            event.accept()

        # Update pan/zoom to simulation thread only when the pan/zoom gesture is finished
        elif (event.type() == QEvent.MouseButtonRelease or
              event.type() == QEvent.TouchEnd) and (self.panzoomchanged or self.labelposchanged):
            if self.panzoomchanged:
                self.panzoomchanged = False
                bs.net.send_event(b'PANZOOM', dict(pan=(self.panlat, self.panlon),
                                                   zoom=self.zoom, ar=self.ar, absolute=True))
                self.panzoom_event.emit(True)
            if self.labelposchanged:
                self.labelposchanged = False
                self.labelpos_event.emit(event.x(), event.y())
        else:
            return super().event(event)
        
        # If we get here, the event was a mouse/trackpad event. Emit it to interested children
        self.mouse_event.emit(event)

        # For all other events call base class event handling
        return True


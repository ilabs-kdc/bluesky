"""
BlueSky OpenGL line and polygon (areafilter) drawing.

Created by: Original BlueSky version
"""

import numpy as np
import bluesky as bs
from bluesky import settings
from bluesky.ui import palette
from bluesky.ui.qtgl import console
from bluesky.ui.qtgl import glhelpers as glh

# Default settings
settings.set_variable_defaults(
    interval_dotted=3,
    interval_dashed=10,
    point_size=3
)

# Default palette
palette.set_default_colours(
    polys=(0, 255, 255),
    previewpoly=(0, 204, 255)
) 

# Static defines
POLYPREV_SIZE = 100
POLY_SIZE = 2000


class Poly(glh.RenderObject, layer=-20):
    """
    Definition: Poly OpenGL object.
    Methods:
        create():           Create the OpenGL Objects and Buffers
        draw():             Draw the OpenGL Objects
        actdata_changed():  Update buffers when a different node is selected,
                            or when the data of the current node is updated.
        cmdline_stacked():  Check if the preview should be deactivated
        previewpoly():      Update the preview polygon

    Created by: Original BlueSky version

    Edited by: Mitchell de Keijzer
    Date: 08-04-2022
    Changed: added a new way of drawing lines and points for the maps without having to use scenario files, this way
            the maps are only loaded on the current gui
    Added:  self.maplines
            self.dottedlines
            self.dashedlines
            self.mappoints
            self.mappointslat
            self.mappointslon
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Polygon preview object
        self.polyprev = glh.VertexArrayObject(glh.gl.GL_LINE_LOOP)

        # Fixed polygons
        self.allpolys = glh.VertexArrayObject(glh.gl.GL_LINES)
        self.alldotted = glh.VertexArrayObject(glh.gl.GL_LINES, shader_type='dashed')
        self.alldashed = glh.VertexArrayObject(glh.gl.GL_LINES, shader_type='dashed')
        self.allpfill = glh.VertexArrayObject(glh.gl.GL_TRIANGLES)
        # Points
        self.allpoints = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)
        self.pointslat = glh.GLBuffer()
        self.pointslon = glh.GLBuffer()

        self.prevmousepos = (0, 0)

        bs.Signal('cmdline_stacked').connect(self.cmdline_stacked)
        bs.Signal('radarmouse').connect(self.previewpoly)
        bs.net.actnodedata_changed.connect(self.actdata_changed)

    def create(self):
        """
        Function: Create the OpenGL Objects and Buffers
        Args: -
        Returns: -

        Created by: Original BlueSky version
        """

        # --------------- Preview poly ---------------
        self.polyprev.create(vertex=POLYPREV_SIZE * 8,
                             color=palette.previewpoly, usage=glh.gl.GL_DYNAMIC_DRAW)

        # --------------- Polys ---------------
        self.allpolys.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)

        # --------------- Dotted lines ---------------
        self.alldotted.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)

        # --------------- Dashed lines ---------------
        self.alldashed.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)

        # --------------- Fills ---------------
        self.allpfill.create(vertex=POLY_SIZE * 24,
                             color=np.append(palette.polys, 50))

        # --------------- Points ---------------
        # OpenGL Buffers
        self.pointslat.create(POLY_SIZE * 16)
        self.pointslon.create(POLY_SIZE * 16)

        # Define vertices
        point_size = settings.point_size
        num_vert = 6
        angles = np.linspace(0., 2 * np.pi, num_vert)
        x = (point_size / 2) * np.sin(angles)
        y = (point_size / 2) * np.cos(angles)
        point_vert = np.empty((num_vert, 2), dtype=np.float32)
        point_vert.T[0] = x
        point_vert.T[1] = y

        # Define VAO
        self.allpoints.create(vertex=point_vert)
        self.allpoints.set_attribs(lat=self.pointslat, lon=self.pointslon, color=POLY_SIZE * 8,
                                   instance_divisor=1)

    def draw(self):
        """
        Function: Draw the OpenGL Objects
        Args: -
        Returns: -

        Created by: Original BlueSky version
        """

        actdata = bs.net.get_nodedata()

        # Send the (possibly) updated global uniforms to the buffer
        self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_LATLON)

        # --- DRAW THE MAP AND COASTLINES ---------------------------------------------
        # Map and coastlines: don't wrap around in the shader
        self.shaderset.enable_wrap(False)

        # --- DRAW PREVIEW SHAPE (WHEN AVAILABLE) -----------------------------
        self.polyprev.draw()

        # --- DRAW CUSTOM SHAPES (WHEN AVAILABLE) -----------------------------
        if actdata.show_poly > 0 and actdata.show_maplines:
            # Polys
            self.allpolys.draw()

            # Dashed and Dotted
            dashed_shader = glh.ShaderSet.get_shader('dashed')
            dashed_shader.bind()

            glh.gl.glUniform1f(dashed_shader.uniforms['dashSize'].loc, float(settings.interval_dotted))
            glh.gl.glUniform1f(dashed_shader.uniforms['gapSize'].loc, float(settings.interval_dotted))
            self.alldotted.draw()

            glh.gl.glUniform1f(dashed_shader.uniforms['dashSize'].loc, float(settings.interval_dashed))
            glh.gl.glUniform1f(dashed_shader.uniforms['gapSize'].loc, float(settings.interval_dashed))
            self.alldashed.draw()

            # Points (set vertex is screen size)
            self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_SCREEN)
            if len(actdata.points) != 0:
                self.allpoints.draw(n_instances=len(actdata.points))

            # Draw fills
            if actdata.show_poly > 1:
                self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_LATLON)
                self.allpfill.draw()

    def actdata_changed(self, nodeid, nodedata, changed_elems):
        """
        Function: Update buffers when a different node is selected, or when the data of the current node is updated.
        Args:
            nodeid:         ID of the Node [bytes]
            nodedata:       The Node data [class]
            changed_elems:  The changed elements [list]
        Returns: -

        Created by: Original BlueSky version
        """

        # Shape data change
        if 'SHAPE' in changed_elems or 'MAP' in changed_elems:
            # Make Current
            if nodedata.polys or nodedata.points or nodedata.dotted or nodedata.dashed:
                self.glsurface.makeCurrent()

            # Polys
            if nodedata.polys:
                contours, fills, colors = zip(*nodedata.polys.values())
                # Create contour buffer with color
                self.allpolys.update(vertex=np.concatenate(contours),
                                     color=np.concatenate(colors))
                # Create fill buffer
                self.allpfill.update(vertex=np.concatenate(fills))
            else:
                self.allpolys.set_vertex_count(0)
                self.allpfill.set_vertex_count(0)

            # Points
            if nodedata.points:
                # Retrieve data
                contours, fills, colors = zip(*nodedata.points.values())
                contours = np.concatenate(contours)
                # Update buffers
                self.pointslat.update(np.array(contours[::2], dtype=np.float32))
                self.pointslon.update(np.array(contours[1::2], dtype=np.float32))
                self.allpoints.update(color=np.concatenate(colors))

            # Dotted lines
            if nodedata.dotted:
                # Retrieve data
                contours, fills, colors = zip(*nodedata.dotted.values())
                contours = np.concatenate(contours)
                # Update object
                self.alldotted.update(vertex=np.array(contours, dtype=np.float32),
                                      color=np.concatenate(colors))
            else:
                self.alldotted.set_vertex_count(0)

            # Dashed lines
            if nodedata.dashed:
                # Retrieve data
                contours, fills, colors = zip(*nodedata.dashed.values())
                contours = np.concatenate(contours)

                # Update object
                self.alldashed.update(vertex=np.array(contours, dtype=np.float32),
                                      color=np.concatenate(colors))
            else:
                self.alldashed.set_vertex_count(0)

        # ATCMODE data change
        if 'ATCMODE' in changed_elems:
            self.allpfill.set_attribs(color=np.append(palette.polys, 50))
            self.polyprev.set_attribs(color=palette.previewpoly)

    def cmdline_stacked(self, cmd, args):
        """
        Function: Check if the preview should be deactivated
        Args:
            cmd:    The command [string]
            args:   The arguments [list]
        Returns: -

        Created by: Original BlueSky version
        """

        if cmd in ['AREA', 'BOX', 'POLY', 'POLYGON', 'CIRCLE', 'LINE', 'POLYLINE']:
            self.polyprev.set_vertex_count(0)

    def previewpoly(self, mouseevent):
        """
        Function: Update the preview polygon
        Args:
            mouseevent: The mouse event [QMouseEvent]
        Returns: -

        Created by: Original BlueSky version
        """

        if mouseevent.type() != mouseevent.MouseMove:
            return
        mousepos = (mouseevent.x(), mouseevent.y())
        # Check if we are updating a preview poly
        if mousepos != self.prevmousepos:
            cmd = console.get_cmd()
            nargs = len(console.get_args())
            if cmd in ['AREA', 'BOX', 'POLY', 'POLYLINE',
                        'POLYALT', 'POLYGON', 'CIRCLE', 'LINE'] and nargs >= 2:
                self.prevmousepos = mousepos
                try:
                    # get the largest even number of points
                    start = 0 if cmd == 'AREA' else 3 if cmd == 'POLYALT' else 1
                    end = ((nargs - start) // 2) * 2 + start
                    data = [float(v) for v in console.get_args()[start:end]]
                    data += self.glsurface.pixelCoordsToLatLon(*mousepos)
                    self.glsurface.makeCurrent()
                    if cmd is None:
                        self.polyprev.set_vertex_count(0)
                        return
                    if cmd in ['BOX', 'AREA']:
                        # For a box (an area is a box) we need to add two additional corners
                        polydata = np.zeros(8, dtype=np.float32)
                        polydata[0:2] = data[0:2]
                        polydata[2:4] = data[2], data[1]
                        polydata[4:6] = data[2:4]
                        polydata[6:8] = data[0], data[3]
                    else:
                        polydata = np.array(data, dtype=np.float32)

                    if cmd[-4:] == 'LINE':
                        self.polyprev.set_primitive_type(glh.gl.GL_LINE_STRIP)
                    else:
                        self.polyprev.set_primitive_type(glh.gl.GL_LINE_LOOP)

                    self.polyprev.update(vertex=polydata)

                except ValueError:
                    pass

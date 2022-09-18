"""
BlueSky OpenGL map object.

Created by: Original BlueSky version
"""

from os import path
import numpy as np

import bluesky as bs
from bluesky.ui import palette
from bluesky.ui.qtgl import glhelpers as glh
from bluesky.ui.loadvisuals import load_coastlines, load_basemap
from bluesky import settings

# Default settings and palette
settings.set_variable_defaults(
    gfx_path='data/graphics',
    atc_mode='BLUESKY',
    interval_dotted=3,
    interval_dashed=10,
    point_size=3
)

palette.set_default_colours(
    coastlines=(85, 85, 115)
)

# Static defines
POLY_SIZE = 2000

class Map(glh.RenderObject, layer=-100):
    """
    Definition: Radar screen map OpenGL object.
    Methods:
        create():           Create the Objects and Buffers
        draw():             Draw the Objects
        actdata_changed():  Update buffers when a different node is selected,
                            or when the data of the current node is updated.

    Created by: Original BlueSky version
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.map = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)
        self.maptrans = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)  # Transparant map
        self.coastlines = glh.VertexArrayObject(glh.gl.GL_LINES)
        self.coastindices = []
        self.vcount_coast = 0
        self.wraplon_loc = 0

        # LVNL Base Maps (for APP and ACC)
        self.basemap_lines = glh.VertexArrayObject(glh.gl.GL_LINES)
        self.basemap_dashed = glh.VertexArrayObject(glh.gl.GL_LINES, shader_type='dashed')
        self.basemap_dotted = glh.VertexArrayObject(glh.gl.GL_LINES, shader_type='dashed')
        #self.basemap_points = glh.VertexArrayObject(glh.gl.GL_TRIANGLE_FAN)

        bs.net.actnodedata_changed.connect(self.actdata_changed)

    def create(self):
        """
        Function: Create the OpenGL Objects and Buffers
        Args: -
        Returns: -

        Created by: Original BlueSky version
        """

        # ---------- Base Map ----------
        lines, dashedlines, dottedlines, points = load_basemap(settings.atc_mode)

        # Lines
        if lines:
            contours, colors = zip(*lines.values())
            self.basemap_lines.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)
            self.basemap_lines.update(vertex=np.concatenate(contours, dtype=np.float32),
                                      color=np.concatenate(colors))
        else:
            self.basemap_lines.set_vertex_count(0)

        # Dashed lines
        if dashedlines:
            contours, colors = zip(*dashedlines.values())
            self.basemap_dashed.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)
            self.basemap_dashed.update(vertex=np.concatenate(contours),
                                       color=np.concatenate(colors))
        else:
            self.basemap_dashed.set_vertex_count(0)

        # Dotted lines
        if dottedlines:
            contours, colors = zip(*dottedlines.values())
            self.basemap_dotted.create(vertex=POLY_SIZE * 16, color=POLY_SIZE * 8)
            self.basemap_dotted.update(vertex=np.concatenate(contours),
                                       color=np.concatenate(colors))
        else:
            self.basemap_dotted.set_vertex_count(0)

        # Points

        # ------- Coastlines -----------------------------
        coastvertices, self.coastindices = load_coastlines()
        self.coastlines.create(vertex=coastvertices, color=palette.coastlines)
        self.vcount_coast = len(coastvertices)

        # ---------- Map ----------
        mapvertices = np.array(
            [-90.0, 540.0, -90.0, -540.0, 90.0, -540.0, 90.0, 540.0], dtype=np.float32)
        texcoords = np.array(
            [1, 3, 1, 0, 0, 0, 0, 3], dtype=np.float32)
        self.wraplon_loc = glh.ShaderSet.get_shader(self.coastlines.shader_type).attribs['lon'].loc

        # Load and bind world texture
        max_texture_size = glh.gl.glGetIntegerv(glh.gl.GL_MAX_TEXTURE_SIZE)
        print('Maximum supported texture size: %d' % max_texture_size)
        for i in [16384, 8192, 4096]:
            if max_texture_size >= i:
                fname = path.join(settings.gfx_path,
                                  'world.%dx%d.dds' % (i, i // 2))
                fnametrans = path.join(settings.gfx_path,
                                       'transparent.%dx%d.dds' % (i, i // 2))
                print('Loading texture ' + fname)
                print('Loading texture ' + fnametrans)
                self.map.create(vertex=mapvertices,
                                texcoords=texcoords, texture=fname)
                self.maptrans.create(vertex=mapvertices,
                                     texcoords=texcoords, texture=fnametrans)
                break

    def draw(self, skipmap=False):
        """
        Function: Draw the OpenGL Objects
        Args: -
        Returns: -

        Created by: Original BlueSky version
        """

        # Send the (possibly) updated global uniforms to the buffer
        self.shaderset.set_vertex_scale_type(self.shaderset.VERTEX_IS_LATLON)

        actdata = bs.net.get_nodedata()

        # --- DRAW THE MAP AND COASTLINES ---------------------------------------------
        # Map and coastlines: don't wrap around in the shader
        self.shaderset.enable_wrap(False)

        # ---------- Base map ----------
        # Lines
        self.basemap_lines.draw()

        # Dashed and Dotted
        dashed_shader = glh.ShaderSet.get_shader('dashed')
        dashed_shader.bind()

        glh.gl.glUniform1f(dashed_shader.uniforms['dashSize'].loc, float(settings.interval_dashed))
        glh.gl.glUniform1f(dashed_shader.uniforms['gapSize'].loc, float(settings.interval_dashed))
        self.basemap_dashed.draw()

        glh.gl.glUniform1f(dashed_shader.uniforms['dashSize'].loc, float(settings.interval_dotted))
        glh.gl.glUniform1f(dashed_shader.uniforms['gapSize'].loc, float(settings.interval_dotted))
        self.basemap_dotted.draw()

        # ---------- Map ----------
        if not skipmap:
            if actdata.show_map:
                self.map.draw()
            else:
                self.maptrans.draw()

        # ---------- Coastlines ----------
        shaderset = glh.ShaderSet.selected
        if actdata.show_coast:
            if shaderset.data.wrapdir == 0:
                # Normal case, no wrap around
                self.coastlines.draw(
                    first_vertex=0, vertex_count=self.vcount_coast)
            else:
                self.coastlines.bind()
                shader = glh.ShaderProgram.bound_shader
                wrapindex = np.uint32(
                    self.coastindices[int(shaderset.data.wraplon) + 180])
                if shaderset.data.wrapdir == 1:
                    shader.setAttributeValue(self.wraplon_loc, 360.0)
                    self.coastlines.draw(
                        first_vertex=0, vertex_count=wrapindex)
                    shader.setAttributeValue(self.wraplon_loc, 0.0)
                    self.coastlines.draw(
                        first_vertex=wrapindex, vertex_count=self.vcount_coast - wrapindex)
                else:
                    shader.setAttributeValue(self.wraplon_loc, -360.0)
                    self.coastlines.draw(
                        first_vertex=wrapindex, vertex_count=self.vcount_coast - wrapindex)
                    shader.setAttributeValue(self.wraplon_loc, 0.0)
                    self.coastlines.draw(
                        first_vertex=0, vertex_count=wrapindex)

    def actdata_changed(self, nodeid, nodedata, changed_elems):
        """
        Function: Update buffers when a different node is selected, or when the data of the current node is updated.
        Args:
            nodeid:         ID of the Node [bytes]
            nodedata:       The Node data [class]
            changed_elems:  The changed elements [list]
        Returns: -

        Created by: Bob van Dillen
        """

        if 'ATCMODE' in changed_elems:
            self.coastlines.set_attribs(color=palette.coastlines)

            # ---------- Base Map ----------
            lines, dashedlines, dottedlines, points = load_basemap(settings.atc_mode)

            # Lines
            if lines:
                contours, colors = zip(*lines.values())
                self.basemap_lines.update(vertex=np.concatenate(contours, dtype=np.float32),
                                          color=np.concatenate(colors))
            else:
                self.basemap_lines.set_vertex_count(0)

            # Dashed lines
            if dashedlines:
                contours, colors = zip(*dashedlines.values())
                self.basemap_dashed.update(vertex=np.concatenate(contours),
                                           color=np.concatenate(colors))
            else:
                self.basemap_dashed.set_vertex_count(0)

            # Dotted lines
            if dottedlines:
                contours, colors = zip(*dottedlines.values())
                self.basemap_dotted.update(vertex=np.concatenate(contours),
                                           color=np.concatenate(colors))
            else:
                self.basemap_dotted.set_vertex_count(0)

            # Points


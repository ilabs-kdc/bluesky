#version 410
#define VERTEX_IS_LATLON 0
#define VERTEX_IS_METERS 1
#define VERTEX_IS_SCREEN 2
#define REARTH_INV 1.56961231e-7

// Uniform block of global data
layout (std140) uniform global_data {
int wrap_dir;           // Wrap-around direction
float wrap_lon;         // Wrap-around longitude
float panlat;           // Map panning coordinates [deg]
float panlon;           // Map panning coordinates [deg]
float zoom;             // Screen zoom factor [-]
int screen_width;       // Screen width in pixels
int screen_height;      // Screen height in pixels
int vertex_scale_type;  // Vertex scale type
};

// Inputs
layout (location = 0) in vec2 vertex;
layout (location = 1) in vec4 color;
layout (location = 2) in float lat;
layout (location = 3) in float lon;

// Outputs
flat out vec2 startPos_fs;
out vec2 vertPos_fs;
out vec4 color_fs;
out vec2 resolution;


void main()
{
	// Calculate correction parameters
	vec2 vAR = vec2(1.0, float(screen_width) / float(screen_height));
	vec2 flat_earth = vec2(cos(radians(panlat)), 1.0);

	// Vertex position and rotation calculations
	vec2 position = vec2(lon, lat);
	if (wrap_dir < 0 && position.x > wrap_lon) {
		position.x -= 360.0;
	} else if (wrap_dir > 0 && position.x < wrap_lon) {
		position.x += 360.0;
	}
	position -= vec2(panlon, panlat);

	vec4 pos;

	// Select vertex scale type
	switch (vertex_scale_type) {

		// Vertex coordinates are screen pixels, so correct for screen size
		case VERTEX_IS_SCREEN:
			vec2 vertex_out = vertex;
			vertex_out = vec2(2.0 * vertex_out.x / float(screen_width), 2.0 * vertex_out.y / float(screen_height));
			pos = vec4(vAR * zoom * flat_earth * position + vertex_out, 0.0, 1.0);

			gl_Position = pos;
			vertPos_fs = pos.xy / pos.w;
			startPos_fs = vertPos_fs;

			break;

		// Vertex coordinates in meters use a right-handed coordinate system, where the positive x-axis points to the north
		// The elements in each vertex therefore need to be flipped
		case VERTEX_IS_METERS:
			pos = vec4(vAR * zoom * (flat_earth * position + (degrees(vertex.yx * REARTH_INV))), 0.0, 1.0);

			gl_Position = pos;
			vertPos_fs = pos.xy / pos.w;
			startPos_fs = vertPos_fs;

			break;

		// Lat/lon vertex coordinates are flipped: lat is index 0, but screen y-axis, and lon is index 1, but screen x-axis
		case VERTEX_IS_LATLON:
		default:
			pos = vec4(vAR * zoom * flat_earth * (position + vertex.yx), 0.0, 1.0);

			gl_Position = pos;
			vertPos_fs = pos.xy / pos.w;
			startPos_fs = vertPos_fs;

			break;
	}

	// Colour
	color_fs = color;

	// Resolution
	resolution = vec2(float(screen_width), float(screen_height));

}

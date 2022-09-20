#version 410

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
flat in vec2 startPos_fs;
in vec2 vertPos_fs;
in vec4 color_fs;

// Outputs
out vec4 color_out;

// Uniform variables
//uniform vec2  resolution;
uniform float dashSize;
uniform float gapSize;


void main()
{
    // Length of the line to the actual fragment
    vec2 resolution = vec2(float(screen_width), float(screen_height));
    vec2  dir  = (vertPos_fs.xy-startPos_fs.xy) * resolution/2.0;
    float dist = length(dir);

    // Discard fragments on the gap
    if (fract(dist / (dashSize + gapSize)) > dashSize/(dashSize + gapSize))
        discard;

    // Color
    color_out = color_fs;
}

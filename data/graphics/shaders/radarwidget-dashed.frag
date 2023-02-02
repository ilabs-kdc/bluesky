#version 410

// Inputs
flat in vec2 startPos_fs;
in vec2 vertPos_fs;
in vec4 color_fs;
in vec2 resolution;

// Outputs
out vec4 color_out;

// Uniform variables
uniform float dashSize;
uniform float gapSize;


void main()
{
    // Length of the line to the actual fragment
    vec2  dir  = (vertPos_fs.xy-startPos_fs.xy) * (resolution/2.0);
    float dist = float(dir.length());

    // Discard fragments on the gap
    float a = dist/(dashSize + gapSize);
    float b = dashSize/(dashSize + gapSize);
    if (fract(a) > b)
    {
        return;
    }

    // Color
    color_out = color_fs;
}

#version 330 core

// Vertex inputs
flat in vec3 colorInterp;

out vec4 out_color;

void main() {
    // Use vertex color (interpolated across face, but looks flat per-face)
    out_color = vec4(colorInterp, 1.0);
}

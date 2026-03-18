#version 330 core
out vec4 outColor;

void main()
{
    float depth = gl_FragCoord.z;
    outColor = vec4(vec3(depth), 1.0);
}

// #version 330 core
// out vec4 outColor;

// void main()
// {
//     float depth = gl_FragCoord.z;
//     outColor = vec4(vec3(depth), 1.0);
// }

#version 330 core
out vec4 outColor;

uniform float near;
uniform float far;

float linearizeDepth(float depth)
{
    float z = depth * 2.0 - 1.0; // NDC
    return (2.0 * near * far) / (far + near - z * (far - near));
}

void main()
{
    float linearDepth = linearizeDepth(gl_FragCoord.z);
    float depth = (linearDepth - near) / (far - near);
    depth = clamp(depth, 0.0, 1.0);
    
    // Gamma correction for better visual contrast
    depth = pow(depth, 0.5);
    
    outColor = vec4(vec3(depth), 1.0);
}
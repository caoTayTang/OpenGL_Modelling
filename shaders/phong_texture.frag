#version 330 core

precision mediump float;
in vec3 normal_interp;  // Surface normal
in vec3 vert_pos;       // Vertex position
in vec3 color_interp;
in vec2 texcoord_interp;

uniform mat3 K_materials;
uniform mat3 I_light;
uniform float shininess; // Shininess
uniform vec3 light_pos; // Light position
uniform int mode;   // Rendering mode

uniform sampler2D uTexture;
uniform bool has_texture;

out vec4 fragColor;

void main() {
  // Get base color from texture or vertex color
  vec4 texColor = vec4(0.0);
  vec3 baseColor = color_interp;
  if (has_texture) {
    texColor = texture(uTexture, texcoord_interp);
    baseColor = mix(color_interp, texColor.rgb, texColor.a > 0.0 ? 1.0 : 0.0);
  }

  vec3 N = normalize(normal_interp);
  vec3 L = normalize(light_pos - vert_pos);
  vec3 R = reflect(-L, N);      // Reflected light vector
  vec3 V = normalize(-vert_pos); // Vector to viewer

  // Diffuse component
  float NdotL = max(dot(N, L), 0.0);

  // Specular component
  float specAngle = max(dot(R, V), 0.0);
  float specular = pow(specAngle, shininess);

  // Ambient + Diffuse + Specular
  vec3 ambient = K_materials[2] * I_light[2];  // ambient * material_ambient
  vec3 diffuse = K_materials[0] * I_light[0] * NdotL;  // diffuse * light_diffuse * NdotL
  vec3 specular_contrib = K_materials[1] * I_light[1] * specular;  // specular * light_specular

  vec3 lighting = ambient + diffuse + specular_contrib;

  // Combine lighting with base color
  vec3 rgb = lighting * baseColor;

  // Mode 0: pure lighting
  // Mode 1: lighting + color
  // Mode 2: texture only
  if (mode == 0) {
    fragColor = vec4(rgb, 1.0);
  } else if (mode == 1) {
    fragColor = vec4(0.5 * rgb + 0.5 * baseColor, 1.0);
  } else {
    fragColor = vec4(texColor.rgb, 1.0);
  }
}

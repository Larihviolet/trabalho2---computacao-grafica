#version 330 core

uniform vec3 groundColor;
uniform sampler2D grassTexture;
uniform bool hasTexture;
in vec2 uv;
out vec4 fragmentColor;

void main() {
    vec3 color = groundColor;
    if (hasTexture) color *= texture(grassTexture, uv).rgb;
    fragmentColor = vec4(color, 1.0);
}

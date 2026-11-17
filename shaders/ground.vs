#version 330 core

layout (location = 0) in vec3 position;

uniform mat4 view;
uniform mat4 projection;
uniform float tileSize;
out vec2 uv;
out vec3 worldPosition;

void main() {
    uv = position.xz / tileSize;
    worldPosition = position;
    gl_Position = projection * view * vec4(position, 1.0);
}

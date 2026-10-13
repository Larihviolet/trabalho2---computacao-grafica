#version 330 core

layout (location = 0) in vec3 position;

uniform mat4 view;
uniform mat4 projection;
uniform float tileSize;
out vec2 uv;

void main() {
    uv = position.xz / tileSize;
    gl_Position = projection * view * vec4(position, 1.0);
}

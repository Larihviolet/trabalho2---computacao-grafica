#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 textureCoordinate;
layout (location = 2) in vec3 normal;
layout (location = 3) in vec3 vertexColor;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
out vec2 uv;
out vec3 worldNormal;
out vec3 surfaceColor;
out vec3 worldPosition;
void main() {
    uv = textureCoordinate;
    surfaceColor = vertexColor;
    worldPosition = (model * vec4(position, 1.0)).xyz;
    worldNormal = mat3(transpose(inverse(model))) * normal;
    gl_Position = projection * view * vec4(worldPosition, 1.0);
}

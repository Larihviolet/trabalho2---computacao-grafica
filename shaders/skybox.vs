#version 330 core

out vec2 screenPosition;

void main() {
    // Um triângulo cobre a tela inteira, sem VBO ou malha de cubo.
    vec2 position = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2) * 2.0 - 1.0;
    screenPosition = position;
    gl_Position = vec4(position, 1.0, 1.0);
}

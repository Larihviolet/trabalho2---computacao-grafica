#version 330 core
uniform vec3 markerColor;
out vec4 fragmentColor;

void main() {
    fragmentColor = vec4(markerColor, 1.0);
}
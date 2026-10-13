#version 330 core

in vec2 screenPosition;
out vec4 fragmentColor;

uniform mat4 inverseProjection;
uniform mat3 inverseViewRotation;
uniform samplerCube skybox;

void main() {
    vec4 viewPosition = inverseProjection * vec4(screenPosition, 1.0, 1.0);
    vec3 direction = normalize(inverseViewRotation * (viewPosition.xyz / viewPosition.w));
    fragmentColor = texture(skybox, direction);
}

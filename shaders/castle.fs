#version 330 core
in vec2 uv;
in vec3 worldNormal;
uniform vec3 baseColor;
uniform bool hasTexture;
uniform sampler2D diffuseMap;
out vec4 fragmentColor;
void main() {
    vec3 color = baseColor;
    if (hasTexture) color *= texture(diffuseMap, uv).rgb;
    float light = 0.4 + 0.6 * max(dot(normalize(worldNormal), normalize(vec3(0.4, 1.0, 0.6))), 0.0);
    fragmentColor = vec4(color * light, 1.0);
}

#version 330 core
in vec2 uv;
in vec3 worldNormal;
in vec3 surfaceColor;
uniform vec3 baseColor;
uniform bool hasTexture;
uniform sampler2D diffuseMap;
uniform float alphaCutoff;
out vec4 fragmentColor;
void main() {
    vec3 color = baseColor * surfaceColor;
    if (hasTexture) {
        vec4 texel = texture(diffuseMap, uv);
        if (texel.a < alphaCutoff) discard;
        color *= texel.rgb;
    }
    float light = 0.4 + 0.6 * max(dot(normalize(worldNormal), normalize(vec3(0.4, 1.0, 0.6))), 0.0);
    fragmentColor = vec4(color * light, 1.0);
}

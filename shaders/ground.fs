#version 330 core

uniform vec3 groundColor;
uniform sampler2D grassTexture;
uniform bool hasTexture;
in vec2 uv;
in vec3 worldPosition;
uniform vec3 lightPosition;
uniform vec3 lightDirection;
uniform vec3 lightColor;
uniform float innerCutoff;
uniform float outerCutoff;
uniform vec3 sunDirection;
uniform vec3 sunColor;
uniform float sunIntensity;
uniform vec2 sunExclusionCenter;
uniform float sunExclusionRadius;
uniform float sunExclusionMinHeight;
uniform float sunExclusionMaxHeight;
out vec4 fragmentColor;

void main() {
    vec3 color = groundColor;
    if (hasTexture) color *= texture(grassTexture, uv).rgb;
    vec3 toLight = lightPosition - worldPosition;
    float distanceToLight = length(toLight);
    vec3 lightDir = normalize(toLight);
    float theta = dot(normalize(lightDirection), -lightDir);
    float cone = clamp((theta - outerCutoff) / (innerCutoff - outerCutoff), 0.0, 1.0);
    float attenuation = 1.0 / (1.0 + 0.007 * distanceToLight +
                               0.0002 * distanceToLight * distanceToLight);
    float diffuse = max(dot(vec3(0.0, 1.0, 0.0), lightDir), 0.0);
    bool insideTower = worldPosition.y >= sunExclusionMinHeight &&
                       worldPosition.y <= sunExclusionMaxHeight &&
                       distance(worldPosition.xz, sunExclusionCenter) <= sunExclusionRadius;
    float sunDiffuse = insideTower ? 0.0 :
                       max(dot(vec3(0.0, 1.0, 0.0),
                               normalize(sunDirection)), 0.0);
    vec3 illumination = vec3(0.22) +
                        lightColor * diffuse * cone * attenuation * 2.5 +
                        sunColor * sunDiffuse * sunIntensity;
    fragmentColor = vec4(color * illumination, 1.0);
}

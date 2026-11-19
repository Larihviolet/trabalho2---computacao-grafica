#version 330 core

uniform vec3 groundColor;
uniform sampler2D grassTexture;
uniform bool hasTexture;
in vec2 uv;
in vec3 worldPosition;
uniform vec3 lightPosition;
uniform vec3 lightDirection;
uniform vec3 lightColor;
uniform vec3 angelLightPosition;
uniform vec3 angelLightDirection;
uniform vec3 angelLightColor;
uniform float angelInnerCutoff;
uniform float angelOuterCutoff;
uniform vec3 viewPos;
uniform float ks;
uniform float ns;
uniform bool diffuseEnabled;
uniform bool specularEnabled;
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
    vec3 normal = vec3(0.0, 1.0, 0.0);
    vec3 viewDir = normalize(viewPos - worldPosition);
    float diffuseFactor = max(dot(normal, lightDir), 0.0);
    float diffuse = diffuseEnabled ? diffuseFactor : 0.0;
    vec3 reflectDir = reflect(-lightDir, normal);
    float specularFactor = specularEnabled && diffuseFactor > 0.0
        ? pow(max(dot(viewDir, reflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 specular = ks * specularFactor * lightColor * cone * attenuation * 2.5;
    vec3 toAngelLight = angelLightPosition - worldPosition;
    float angelDistance = length(toAngelLight);
    vec3 angelLightDir = normalize(toAngelLight);
    float angelTheta = dot(normalize(angelLightDirection), -angelLightDir);
    float angelCone = clamp((angelTheta - angelOuterCutoff) /
                            (angelInnerCutoff - angelOuterCutoff), 0.0, 1.0);
    float angelAttenuation = 1.0 / (1.0 + 0.007 * angelDistance +
                                   0.0002 * angelDistance * angelDistance);
    float angelDiffuseFactor = max(dot(normal, angelLightDir), 0.0);
    float angelDiffuse = diffuseEnabled ? angelDiffuseFactor : 0.0;
    vec3 angelReflectDir = reflect(-angelLightDir, normal);
    float angelSpecularFactor = specularEnabled && angelDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, angelReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 angelSpecular = ks * angelSpecularFactor * angelLightColor *
                         angelCone * angelAttenuation * 2.5;
    bool insideTower = worldPosition.y >= sunExclusionMinHeight &&
                       worldPosition.y <= sunExclusionMaxHeight &&
                       distance(worldPosition.xz, sunExclusionCenter) <= sunExclusionRadius;
    vec3 sunLightDir = normalize(sunDirection);
    float sunDiffuseFactor = max(dot(normal, sunLightDir), 0.0);
    float sunDiffuse = !insideTower && diffuseEnabled ? sunDiffuseFactor : 0.0;
    vec3 sunReflectDir = reflect(-sunLightDir, normal);
    float sunSpecularFactor = !insideTower && specularEnabled && sunDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, sunReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 sunSpecular = ks * sunSpecularFactor * sunColor * sunIntensity;
    vec3 illumination = vec3(0.22) +
                        lightColor * diffuse * cone * attenuation * 2.5 +
                        specular +
                        angelLightColor * angelDiffuse * angelCone * angelAttenuation * 2.5 +
                        angelSpecular +
                        sunColor * sunDiffuse * sunIntensity +
                        sunSpecular;
    fragmentColor = vec4(color * illumination, 1.0);
}

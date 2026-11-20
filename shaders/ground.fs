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
uniform vec3 demonLightPosition;
uniform vec3 demonLightColor;
uniform float demonLightRange;
uniform vec3 viewPos;
// ka, kd, ks e ns são os coeficientes do material deste piso.
uniform float ka;
uniform float kd;
uniform float ks;
uniform float ns;
uniform bool ambientEnabled;
uniform bool diffuseEnabled;
uniform bool specularEnabled;
uniform bool spotlightEnabled;
uniform bool demonLightEnabled;
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
    float cone = spotlightEnabled
        ? clamp((theta - outerCutoff) / (innerCutoff - outerCutoff), 0.0, 1.0)
        : 0.0;
    float attenuation = 1.0 / (1.0 + 0.007 * distanceToLight +
                               0.0002 * distanceToLight * distanceToLight);
    vec3 normal = vec3(0.0, 1.0, 0.0);
    vec3 viewDir = normalize(viewPos - worldPosition);
    float diffuseFactor = max(dot(normal, lightDir), 0.0);
    bool insideTower = worldPosition.y >= sunExclusionMinHeight &&
                       worldPosition.y <= sunExclusionMaxHeight &&
                       distance(worldPosition.xz, sunExclusionCenter) <= sunExclusionRadius;
    float diffuse = diffuseEnabled ? kd * diffuseFactor : 0.0;
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
    float angelDiffuse = diffuseEnabled ? kd * angelDiffuseFactor : 0.0;
    vec3 angelReflectDir = reflect(-angelLightDir, normal);
    float angelSpecularFactor = specularEnabled && angelDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, angelReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 angelSpecular = ks * angelSpecularFactor * angelLightColor *
                         angelCone * angelAttenuation * 2.5;
    vec3 toDemonLight = demonLightPosition - worldPosition;
    float demonDistance = length(toDemonLight);
    float demonRangeFade = max(1.0 - demonDistance / demonLightRange, 0.0);
    float demonAttenuation = demonLightEnabled && insideTower &&
                             demonDistance < demonLightRange
        ? demonRangeFade * demonRangeFade /
          (1.0 + 0.09 * demonDistance + 0.032 * demonDistance * demonDistance)
        : 0.0;
    vec3 demonLightDir = demonDistance > 0.0001
        ? toDemonLight / demonDistance
        : normal;
    float demonDiffuseFactor = max(dot(normal, demonLightDir), 0.0);
    float demonDiffuse = diffuseEnabled ? kd * demonDiffuseFactor : 0.0;
    vec3 demonReflectDir = reflect(-demonLightDir, normal);
    float demonSpecularFactor = specularEnabled && demonDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, demonReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 demonContribution = demonLightColor *
        (demonDiffuse + ks * demonSpecularFactor) * demonAttenuation * 2.5;
    vec3 sunLightDir = normalize(sunDirection);
    float sunDiffuseFactor = max(dot(normal, sunLightDir), 0.0);
    float sunDiffuse = !insideTower && diffuseEnabled ? kd * sunDiffuseFactor : 0.0;
    vec3 sunReflectDir = reflect(-sunLightDir, normal);
    float sunSpecularFactor = !insideTower && specularEnabled && sunDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, sunReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 sunSpecular = ks * sunSpecularFactor * sunColor * sunIntensity;
    vec3 ambient = ambientEnabled ? vec3(0.22 * ka) : vec3(0.0);
    vec3 illumination = ambient +
                        lightColor * diffuse * cone * attenuation * 2.5 +
                        specular +
                        angelLightColor * angelDiffuse * angelCone * angelAttenuation * 2.5 +
                        angelSpecular +
                        demonContribution +
                        sunColor * sunDiffuse * sunIntensity +
                        sunSpecular;
    fragmentColor = vec4(color * illumination, 1.0);
}

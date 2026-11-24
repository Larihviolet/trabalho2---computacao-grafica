#version 330 core
const int LIGHTING_EXTERIOR = 0;
const int LIGHTING_INTERIOR = 1;
const int LIGHTING_MIXED = 2;
in vec2 uv;
in vec3 worldNormal;
in vec3 surfaceColor;
in vec3 worldPosition;
uniform vec3 baseColor;
uniform bool hasTexture;
uniform sampler2D diffuseMap;
uniform float alphaCutoff;
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
// kd, ks e ns são os coeficientes do material enviados por objeto.
uniform float kd;
uniform float ks;
uniform float ns;
uniform bool ambientEnabled;
uniform bool diffuseEnabled;
uniform bool specularEnabled;
uniform bool spotlightEnabled;
uniform bool demonLightEnabled;
uniform bool demonCircleGlow;
uniform float innerCutoff;
uniform float outerCutoff;
uniform vec3 sunDirection;
uniform vec3 sunColor;
uniform float sunIntensity;
uniform vec2 towerVolumeCenter;
uniform float towerVolumeRadius;
uniform float towerVolumeMinHeight;
uniform float towerVolumeMaxHeight;
uniform float interiorAmbientIntensity;
uniform float exteriorAmbientIntensity;
uniform int lightingZone;
out vec4 fragmentColor;
void main() {
    vec3 color = baseColor * surfaceColor;
    if (hasTexture) {
        vec4 texel = texture(diffuseMap, uv);
        if (texel.a < alphaCutoff) discard;
        color *= texel.rgb;
    }
    bool insideTower = worldPosition.y >= towerVolumeMinHeight &&
                       worldPosition.y <= towerVolumeMaxHeight &&
                       distance(worldPosition.xz, towerVolumeCenter) <= towerVolumeRadius;
    bool interiorSurface = lightingZone == LIGHTING_INTERIOR ||
                           (lightingZone == LIGHTING_MIXED && insideTower);
    bool exteriorSurface = lightingZone == LIGHTING_EXTERIOR ||
                           (lightingZone == LIGHTING_MIXED && !insideTower);
    vec3 toLight = lightPosition - worldPosition;
    float distanceToLight = length(toLight);
    vec3 lightDir = normalize(toLight);
    float theta = dot(normalize(lightDirection), -lightDir);
    float cone = spotlightEnabled && interiorSurface
        ? clamp((theta - outerCutoff) / (innerCutoff - outerCutoff), 0.0, 1.0)
        : 0.0;
    float attenuation = 1.0 / (1.0 + 0.007 * distanceToLight +
                               0.0002 * distanceToLight * distanceToLight);
    vec3 normal = normalize(worldNormal);
    vec3 viewDir = normalize(viewPos - worldPosition);
    float diffuseFactor = max(dot(normal, lightDir), 0.0);
    float diffuse = diffuseEnabled && spotlightEnabled && interiorSurface
        ? kd * diffuseFactor
        : 0.0;
    vec3 reflectDir = reflect(-lightDir, normal);
    float specularFactor = specularEnabled && spotlightEnabled &&
                           interiorSurface && diffuseFactor > 0.0
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
    float angelDiffuse = diffuseEnabled && exteriorSurface
        ? kd * angelDiffuseFactor
        : 0.0;
    vec3 angelReflectDir = reflect(-angelLightDir, normal);
    float angelSpecularFactor = specularEnabled && exteriorSurface &&
                                angelDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, angelReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 angelSpecular = ks * angelSpecularFactor * angelLightColor *
                         angelCone * angelAttenuation * 2.5;
    vec3 toDemonLight = demonLightPosition - worldPosition;
    float demonDistance = length(toDemonLight);
    float demonRangeFade = max(1.0 - demonDistance / demonLightRange, 0.0);
    float demonAttenuation = demonLightEnabled && interiorSurface &&
                             demonDistance < demonLightRange
        ? demonRangeFade * demonRangeFade /
          (1.0 + 0.09 * demonDistance + 0.032 * demonDistance * demonDistance)
        : 0.0;
    vec3 demonLightDir = demonDistance > 0.0001
        ? toDemonLight / demonDistance
        : normal;
    float demonDiffuseFactor = max(dot(normal, demonLightDir), 0.0);
    float demonDiffuse = diffuseEnabled && interiorSurface
        ? kd * demonDiffuseFactor
        : 0.0;
    vec3 demonReflectDir = reflect(-demonLightDir, normal);
    float demonSpecularFactor = specularEnabled && interiorSurface &&
                                demonDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, demonReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 demonContribution = demonLightColor *
        (demonDiffuse + ks * demonSpecularFactor) * demonAttenuation * 2.5;
    vec3 sunLightDir = normalize(sunDirection);
    float sunDiffuseFactor = max(dot(normal, sunLightDir), 0.0);
    float sunDiffuse = exteriorSurface && diffuseEnabled
        ? kd * sunDiffuseFactor
        : 0.0;
    vec3 sunReflectDir = reflect(-sunLightDir, normal);
    float sunSpecularFactor = exteriorSurface && specularEnabled &&
                              sunDiffuseFactor > 0.0
        ? pow(max(dot(viewDir, sunReflectDir), 0.0), max(ns, 1.0))
        : 0.0;
    vec3 sunSpecular = ks * sunSpecularFactor * sunColor * sunIntensity;
    vec3 ambient = vec3(0.0);
    if (ambientEnabled) {
        if (interiorSurface) ambient += vec3(interiorAmbientIntensity);
        if (exteriorSurface) ambient += vec3(exteriorAmbientIntensity);
    }
    vec3 illumination = ambient +
                        lightColor * diffuse * cone * attenuation * 2.5 +
                        specular +
                        angelLightColor * angelDiffuse * angelCone * angelAttenuation * 2.5 +
                        angelSpecular +
                        demonContribution +
                        sunColor * sunDiffuse * sunIntensity +
                        sunSpecular +
                        (demonCircleGlow && demonLightEnabled
                            ? demonLightColor * 0.65
                            : vec3(0.0));
    fragmentColor = vec4(color * illumination, 1.0);
}

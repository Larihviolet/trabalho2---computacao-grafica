#version 330 core

in vec2 out_texture;
in vec3 out_fragPos;
in vec3 out_normal;

out vec4 fragmentColor;

uniform vec3 lightPos;
uniform vec3 viewPos;
uniform float ka;
uniform float kd;
uniform float ks;
uniform float ns;
uniform sampler2D samplerTexture;

void main() {
    vec3 norm = normalize(out_normal);
    vec3 lightDir = normalize(lightPos - out_fragPos);
    vec3 viewDir = normalize(viewPos - out_fragPos);
    vec3 reflectDir = reflect(-lightDir, norm);

    vec3 ambient = vec3(ka);
    float diffuseFactor = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = kd * diffuseFactor * vec3(1.0);
    float specularFactor = pow(max(dot(viewDir, reflectDir), 0.0), max(ns, 1.0));
    vec3 specular = ks * specularFactor * vec3(1.0);
    vec3 texel = texture(samplerTexture, out_texture).rgb;

    fragmentColor = vec4((ambient + diffuse + specular) * texel, 1.0);
}
# Lápides atrás da torre e estátua em órbita, com recursos compartilhados.

from pathlib import Path
import ctypes

import glm
import numpy as np
from OpenGL.GL import *

from obj_model import ObjModel


def _make_sphere_vertices(latitude_segments=16, longitude_segments=24):
    vertices = []
    for latitude in range(latitude_segments):
        lat0 = -np.pi / 2.0 + np.pi * latitude / latitude_segments
        lat1 = -np.pi / 2.0 + np.pi * (latitude + 1) / latitude_segments
        for longitude in range(longitude_segments):
            lon0 = 2.0 * np.pi * longitude / longitude_segments
            lon1 = 2.0 * np.pi * (longitude + 1) / longitude_segments

            def point(lat, lon):
                normal = (np.cos(lat) * np.cos(lon), np.sin(lat),
                          np.cos(lat) * np.sin(lon))
                uv = (longitude / longitude_segments, latitude / latitude_segments)
                return (*normal, *uv, *normal, 1.0, 1.0, 1.0)

            p00 = point(lat0, lon0)
            p01 = point(lat0, lon1)
            p10 = point(lat1, lon0)
            p11 = point(lat1, lon1)
            vertices.extend((p00, p10, p11, p00, p11, p01))
    return np.asarray(vertices, dtype=np.float32)


class Graveyard:
    def __init__(self, center=(0.0, -30.0), ground_height=-2.0,
                 orbit_radius=10.0, orbit_speed=12.0):
        if orbit_radius <= 0:
            raise ValueError("O raio da órbita deve ser positivo.")
        root = Path(__file__).resolve().parent / "objetos"
        self.center = center
        self.ground_height = ground_height
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = 0.0
        self.angel_movement_enabled = True
        self.stone = ObjModel(root / "graveyard_stone" / "graveyard_stone.obj",
                              height=1.8, ground_height=0.0, center=(0.0, 0.0))
        self.stone_models = []
        rng = np.random.default_rng(17)
        # Três fileiras atrás da torre, com corredor central e pequenas variações.
        for distance in (16.0, 23.0, 30.0):
            for offset in (-9.0, -3.0, 3.0, 9.0):
                position = glm.vec3(center[0] + offset + rng.uniform(-0.3, 0.3),
                                    ground_height, center[1] - distance + rng.uniform(-0.4, 0.4))
                transform = glm.translate(glm.mat4(1.0), position)
                transform = glm.rotate(transform, float(rng.uniform(-0.12, 0.12)), glm.vec3(0, 1, 0))
                transform = glm.scale(transform, glm.vec3(float(rng.uniform(0.9, 1.1))))
                self.stone_models.append(np.array(transform, dtype=np.float32) @ self.stone.model)
        self.angel = ObjModel(root / "weeping_angel" / "weeping_angel.obj",
                              height=3.2, ground_height=0.0, center=(0.0, 0.0), rotation_z=90.0)
        self.angel_base = self.angel.model.copy()
        self.light_sphere_vertices = _make_sphere_vertices()
        self.light_sphere_vao = glGenVertexArrays(1)
        self.light_sphere_vbo = glGenBuffers(1)
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        previous_buffer = int(glGetIntegerv(GL_ARRAY_BUFFER_BINDING))
        try:
            glBindVertexArray(self.light_sphere_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.light_sphere_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.light_sphere_vertices.nbytes,
                         self.light_sphere_vertices, GL_STATIC_DRAW)
            stride = self.light_sphere_vertices.strides[0]
            for location, count, offset in ((0, 3, 0), (1, 2, 12), (2, 3, 20), (3, 3, 32)):
                glEnableVertexAttribArray(location)
                glVertexAttribPointer(location, count, GL_FLOAT, GL_FALSE, stride,
                                      ctypes.c_void_p(offset))
        finally:
            glBindVertexArray(previous_vao)
            glBindBuffer(GL_ARRAY_BUFFER, previous_buffer)
        self.light_sphere_vertex_count = len(self.light_sphere_vertices)
        self.update(0.0)

    def update(self, delta_time):
        # Usa o tempo entre quadros e reconstrói a matriz para evitar deriva na órbita.
        if self.angel_movement_enabled:
            self.orbit_angle = (self.orbit_angle + self.orbit_speed * max(float(delta_time), 0.0)) % 360.0
        angle = np.radians(self.orbit_angle)
        self.angel_position = (
            self.center[0] + self.orbit_radius * np.cos(angle),
            self.ground_height,
            self.center[1] + self.orbit_radius * np.sin(angle))
        transform = glm.translate(glm.mat4(1.0), glm.vec3(*self.angel_position))
        # Orienta a estátua na direção tangente à trajetória.
        transform = glm.rotate(transform, float(np.pi / 2.0 - angle), glm.vec3(0, 1, 0))
        self.angel.model = np.array(transform, dtype=np.float32) @ self.angel_base
        self.light_direction = (-float(np.sin(angle)), 0.0, float(np.cos(angle)))
        self.light_position = tuple(
            self.angel_position[index] + 0.65 * self.light_direction[index]
            for index in range(3))
        self.light_position = (self.light_position[0],
                               self.ground_height + 2.5,
                               self.light_position[2])

    def toggle_angel_movement(self):
        self.angel_movement_enabled = not self.angel_movement_enabled

    def draw(self, view, projection):
        self.stone.draw(view, projection, models=self.stone_models)
        self.angel.draw(view, projection)
        shader = self.angel.shader
        program = shader.getProgram()
        previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        try:
            shader.use()
            glUniformMatrix4fv(glGetUniformLocation(program, "view"), 1, GL_TRUE, view)
            glUniformMatrix4fv(glGetUniformLocation(program, "projection"), 1, GL_TRUE, projection)
            model = glm.translate(glm.mat4(1.0), glm.vec3(*self.light_position))
            model = glm.scale(model, glm.vec3(0.14))
            glUniformMatrix4fv(glGetUniformLocation(program, "model"), 1, GL_TRUE,
                               np.array(model, dtype=np.float32))
            glUniform3f(glGetUniformLocation(program, "baseColor"), 0.25, 0.75, 1.0)
            glUniform1i(glGetUniformLocation(program, "hasTexture"), GL_FALSE)
            glUniform1i(glGetUniformLocation(program, "emissive"), GL_TRUE)
            glBindVertexArray(self.light_sphere_vao)
            glDrawArrays(GL_TRIANGLES, 0, self.light_sphere_vertex_count)
        finally:
            glUniform1i(glGetUniformLocation(program, "emissive"), GL_FALSE)
            glBindVertexArray(previous_vao)
            glUseProgram(previous_program)

    def close(self):
        glDeleteBuffers(1, [self.light_sphere_vbo])
        glDeleteVertexArrays(1, [self.light_sphere_vao])
        self.stone.close()
        self.angel.close()

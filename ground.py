# Chão plano com textura repetida e recursos OpenGL próprios.

import ctypes
from pathlib import Path

import numpy as np
from PIL import Image
from OpenGL.GL import *

from shader_s import Shader


def _make_vertices(size, height, center, shape):
    half = size / 2.0
    if shape == "square":
        return np.array([
            (center[0] - half, height, center[1] - half),
            (center[0] - half, height, center[1] + half),
            (center[0] + half, height, center[1] + half),
            (center[0] - half, height, center[1] - half),
            (center[0] + half, height, center[1] + half),
            (center[0] + half, height, center[1] - half),
        ], dtype=np.float32)
    if shape == "circle":
        segments = 64
        angles = np.linspace(0.0, 2.0 * np.pi, segments + 1, dtype=np.float32)
        perimeter = np.column_stack((
            center[0] + half * np.cos(angles),
            np.full(segments + 1, height, dtype=np.float32),
            center[1] - half * np.sin(angles),
        ))
        vertices = np.empty((segments, 3, 3), dtype=np.float32)
        vertices[:, 0, :] = (center[0], height, center[1])
        vertices[:, 1, :] = perimeter[:-1]
        vertices[:, 2, :] = perimeter[1:]
        return vertices.reshape(-1, 3)
    raise ValueError("A forma do chão deve ser 'square' ou 'circle'.")


class Ground:
    def __init__(self, size=200.0, height=-2.0, color=(1.0, 1.0, 1.0),
                 texture_path=None, tile_size=4.0, center=(0.0, 0.0), shape="square"):
        if size <= 0:
            raise ValueError("O tamanho do chão deve ser positivo.")
        if tile_size <= 0:
            raise ValueError("O tamanho de repetição da textura deve ser positivo.")
        self.size = size
        self.height = height
        # Ler antes de criar recursos OpenGL permite falhar cedo se o arquivo faltar.
        image = None
        if texture_path is not None:
            with Image.open(texture_path) as source:
                image = source.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.color = color
        self.tile_size = tile_size
        self.texture = 0
        shader_dir = Path(__file__).resolve().parent / "shaders"
        self.shader = Shader(str(shader_dir / "ground.vs"),
                             str(shader_dir / "ground.fs"))
        vertices = _make_vertices(size, height, center, shape)
        self.vertex_count = len(vertices)
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        previous_buffer = int(glGetIntegerv(GL_ARRAY_BUFFER_BINDING))
        try:
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        finally:
            glBindVertexArray(previous_vao)
            glBindBuffer(GL_ARRAY_BUFFER, previous_buffer)
        program = self.shader.getProgram()
        self.view_location = glGetUniformLocation(program, "view")
        self.projection_location = glGetUniformLocation(program, "projection")
        self.color_location = glGetUniformLocation(program, "groundColor")
        self.tile_size_location = glGetUniformLocation(program, "tileSize")
        self.sampler_location = glGetUniformLocation(program, "grassTexture")
        self.has_texture_location = glGetUniformLocation(program, "hasTexture")
        if image is not None:
            self.texture = glGenTextures(1)
            previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_2D))
            try:
                glBindTexture(GL_TEXTURE_2D, self.texture)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, image.width, image.height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glGenerateMipmap(GL_TEXTURE_2D)
            finally:
                glBindTexture(GL_TEXTURE_2D, previous_texture)

    def draw(self, view, projection):
        previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        polygon_mode = glGetIntegerv(GL_POLYGON_MODE)
        active_texture = int(glGetIntegerv(GL_ACTIVE_TEXTURE))
        glActiveTexture(GL_TEXTURE0)
        previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_2D))
        try:
            self.shader.use()
            glUniformMatrix4fv(self.view_location, 1, GL_TRUE, view)
            glUniformMatrix4fv(self.projection_location, 1, GL_TRUE, projection)
            glUniform3f(self.color_location, *self.color)
            glUniform1f(self.tile_size_location, self.tile_size)
            glUniform1i(self.sampler_location, 0)
            glUniform1i(self.has_texture_location, bool(self.texture))
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        finally:
            glBindTexture(GL_TEXTURE_2D, previous_texture)
            glActiveTexture(active_texture)
            glBindVertexArray(previous_vao)
            glPolygonMode(GL_FRONT, int(polygon_mode[0]))
            glPolygonMode(GL_BACK, int(polygon_mode[1]))
            glUseProgram(previous_program)

    def close(self):
        # Liberar antes de encerrar o contexto OpenGL.
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        if self.texture:
            glDeleteTextures(1, [self.texture])
        glDeleteProgram(self.shader.getProgram())

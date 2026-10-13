# Fundo panorâmico por direções de visão, sem geometria de cubo.

from pathlib import Path

import numpy as np
from PIL import Image
from OpenGL.GL import *

from shader_s import Shader


def load_cross_faces(path):
    # Recorta uma cruz 4x3: esquerda, frente, direita, trás; cima e baixo.
    # Retorna RGB na ordem OpenGL: +X, -X, +Y, -Y, +Z, -Z.
    # Mantém as linhas na orientação da imagem, sem inversão vertical.
    with Image.open(path) as source:
        width, height = source.size
        if width % 4 or height % 3 or width // 4 != height // 3:
            raise ValueError("O cubemap deve ser uma cruz 4x3 com faces quadradas.")
        size = width // 4
        atlas = source.convert("RGB")
        cells = ((2, 1), (0, 1), (1, 0), (1, 2), (1, 1), (3, 1))
        return [atlas.crop((x * size, y * size, (x + 1) * size,
                            (y + 1) * size)) for x, y in cells]


class Skybox:
    def __init__(self, cubemap_path):
        faces = load_cross_faces(cubemap_path)
        shader_dir = Path(__file__).resolve().parent / "shaders"
        self.shader = Shader(str(shader_dir / "skybox.vs"),
                             str(shader_dir / "skybox.fs"))
        self.vao = glGenVertexArrays(1)
        self.texture = glGenTextures(1)
        previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP))
        alignment = int(glGetIntegerv(GL_UNPACK_ALIGNMENT))
        try:
            glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            for index, face in enumerate(faces):
                glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + index, 0,
                             GL_RGB8, face.width, face.height, 0,
                             GL_RGB, GL_UNSIGNED_BYTE, face.tobytes())
            for axis in (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R):
                glTexParameteri(GL_TEXTURE_CUBE_MAP, axis, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        finally:
            glPixelStorei(GL_UNPACK_ALIGNMENT, alignment)
            glBindTexture(GL_TEXTURE_CUBE_MAP, previous_texture)
        program = self.shader.getProgram()
        self.inverse_projection = glGetUniformLocation(program, "inverseProjection")
        self.inverse_view_rotation = glGetUniformLocation(program, "inverseViewRotation")
        self.sampler = glGetUniformLocation(program, "skybox")

    def draw(self, view, projection):
        # Desenha no plano distante e restaura o estado da cena.
        previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        depth_function = int(glGetIntegerv(GL_DEPTH_FUNC))
        depth_mask = bool(glGetBooleanv(GL_DEPTH_WRITEMASK))
        polygon_mode = glGetIntegerv(GL_POLYGON_MODE)
        active_texture = int(glGetIntegerv(GL_ACTIVE_TEXTURE))
        seamless = bool(glIsEnabled(GL_TEXTURE_CUBE_MAP_SEAMLESS))
        culling = bool(glIsEnabled(GL_CULL_FACE))
        glActiveTexture(GL_TEXTURE0)
        previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP))
        try:
            self.shader.use()
            glUniformMatrix4fv(self.inverse_projection, 1, GL_TRUE,
                               np.linalg.inv(projection).astype(np.float32))
            # Só a rotação: o céu permanece infinitamente distante.
            glUniformMatrix3fv(self.inverse_view_rotation, 1, GL_TRUE,
                               np.linalg.inv(view[:3, :3]).astype(np.float32))
            glUniform1i(self.sampler, 0)
            glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
            glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
            glDisable(GL_CULL_FACE)
            glDepthFunc(GL_LEQUAL)
            glDepthMask(GL_FALSE)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, 3)
        finally:
            glBindVertexArray(previous_vao)
            glBindTexture(GL_TEXTURE_CUBE_MAP, previous_texture)
            glActiveTexture(active_texture)
            glDepthFunc(depth_function)
            glDepthMask(depth_mask)
            glPolygonMode(GL_FRONT, int(polygon_mode[0]))
            glPolygonMode(GL_BACK, int(polygon_mode[1]))
            if not seamless:
                glDisable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
            if culling:
                glEnable(GL_CULL_FACE)
            glUseProgram(previous_program)

    def close(self):
        # Libera recursos enquanto o contexto OpenGL ainda está ativo.
        glDeleteTextures(1, [self.texture])
        glDeleteVertexArrays(1, [self.vao])
        glDeleteProgram(self.shader.getProgram())

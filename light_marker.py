"""Gera e desenha a esfera visÃ­vel que marca a posiÃ§Ã£o do holofote."""

import ctypes
from pathlib import Path

import numpy as np
from OpenGL.GL import *

from shader_s import Shader


def _sphere_vertices(sectors, stacks):
    """Gera triÃ¢ngulos unitÃ¡rios para uma esfera UV.

    Args:
        sectors: DivisÃµes angulares ao redor do eixo vertical.
        stacks: DivisÃµes ao longo do eixo vertical.

    Returns:
        Array float32 de posiÃ§Ãµes XYZ trianguladas.
    """
    vertices = []
    for stack in range(stacks):
        upper = np.pi * stack / stacks
        lower = np.pi * (stack + 1) / stacks
        for sector in range(sectors):
            left = 2.0 * np.pi * sector / sectors
            right = 2.0 * np.pi * (sector + 1) / sectors

            upper_left = (np.sin(upper) * np.cos(left), np.cos(upper),
                          np.sin(upper) * np.sin(left))
            upper_right = (np.sin(upper) * np.cos(right), np.cos(upper),
                           np.sin(upper) * np.sin(right))
            lower_left = (np.sin(lower) * np.cos(left), np.cos(lower),
                          np.sin(lower) * np.sin(left))
            lower_right = (np.sin(lower) * np.cos(right), np.cos(lower),
                           np.sin(lower) * np.sin(right))
            vertices.extend((upper_left, upper_right, lower_left,
                             upper_right, lower_right, lower_left))
    return np.asarray(vertices, dtype=np.float32)


class LightMarker:
    """Esfera colorida posicionada junto Ã  luz do holofote."""

    def __init__(self, position, color, radius=0.35, sectors=24, stacks=16):
        """Cria a esfera e envia sua malha para a GPU.

        Args:
            position: PosiÃ§Ã£o XYZ do marcador.
            color: Cor RGB do marcador.
            radius: Raio da esfera.
            sectors: DivisÃµes angulares da malha.
            stacks: DivisÃµes verticais da malha.

        Raises:
            ValueError: Se posiÃ§Ã£o, cor ou resoluÃ§Ã£o da malha forem invÃ¡lidas.
        """
        if radius <= 0.0:
            raise ValueError("O raio do marcador deve ser positivo.")
        if sectors < 3 or stacks < 2:
            raise ValueError("A malha esfÃ©rica precisa de pelo menos 3 setores e 2 faixas.")

        self.position = tuple(position)
        self.color = tuple(color)
        if len(self.position) != 3 or len(self.color) != 3:
            raise ValueError("A posiÃ§Ã£o e a cor do marcador devem ter trÃªs componentes.")

        self.model = np.eye(4, dtype=np.float32)
        self.model[:3, :3] *= radius
        self.model[:3, 3] = self.position

        shader_dir = Path(__file__).resolve().parent / "shaders"
        self.shader = Shader(str(shader_dir / "light_marker.vs"),
                             str(shader_dir / "light_marker.fs"))
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        vertices = _sphere_vertices(sectors, stacks)
        self.vertex_count = len(vertices)

        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        previous_buffer = int(glGetIntegerv(GL_ARRAY_BUFFER_BINDING))
        try:
            glBindVertexArray(self.vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                                  3 * ctypes.sizeof(ctypes.c_float), ctypes.c_void_p(0))
        finally:
            glBindVertexArray(previous_vao)
            glBindBuffer(GL_ARRAY_BUFFER, previous_buffer)

        program = self.shader.get_program()
        self.model_location = glGetUniformLocation(program, "model")
        self.view_location = glGetUniformLocation(program, "view")
        self.projection_location = glGetUniformLocation(program, "projection")
        self.color_location = glGetUniformLocation(program, "markerColor")

    def draw(self, view, projection):
        """Desenha o marcador com as matrizes de cÃ¢mera fornecidas.

        Args:
            view: Matriz de visualizaÃ§Ã£o 4x4.
            projection: Matriz de projeÃ§Ã£o 4x4.
        """
        previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        try:
            self.shader.use()
            glUniformMatrix4fv(self.model_location, 1, GL_TRUE, self.model)
            glUniformMatrix4fv(self.view_location, 1, GL_TRUE, view)
            glUniformMatrix4fv(self.projection_location, 1, GL_TRUE, projection)
            glUniform3f(self.color_location, *self.color)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        finally:
            glBindVertexArray(previous_vao)
            glUseProgram(previous_program)

    def close(self):
        """Libera o buffer, o VAO e o shader do marcador."""
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        glDeleteProgram(self.shader.get_program())

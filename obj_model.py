# Carregamento e renderização compartilhados pelos modelos OBJ da cena.

import ctypes
from pathlib import Path

import glm
import numpy as np
from PIL import Image
from OpenGL.GL import *

from shader_s import Shader


def load_obj(path):
    positions, uvs, normals, vertices, batches = [], [], [], [], []
    colors = []
    materials = {}
    current_material = None
    with path.open(encoding="utf-8", errors="replace") as source:
        for line in source:
            fields = line.split()
            if not fields or fields[0].startswith('#'):
                continue
            kind, values = fields[0], fields[1:]
            if kind == "mtllib":
                material = None
                with (path.parent / " ".join(values)).open() as library:
                    for entry in library:
                        parts = entry.split()
                        if not parts:
                            continue
                        if parts[0] == "newmtl":
                            material = materials.setdefault(parts[1], {})
                        elif material is not None and parts[0] == "Kd":
                            material['color'] = tuple(map(float, parts[1:4]))
                        elif material is not None and parts[0] == "map_Kd":
                            material['texture'] = path.parent / " ".join(parts[1:])
            elif kind == "v":
                positions.append(tuple(map(float, values[:3])))
                # OBJ pode guardar RGB depois das coordenadas XYZ.
                colors.append(tuple(map(float, values[3:6])) if len(values) >= 6 else (1.0, 1.0, 1.0))
            elif kind == "vt":
                uvs.append(tuple(map(float, values[:2])))
            elif kind == "vn":
                normals.append(tuple(map(float, values[:3])))
            elif kind == "usemtl":
                current_material = values[0]
            elif kind == "f":
                if not batches or batches[-1][2] != current_material:
                    batches.append([len(vertices), 0, current_material])
                # Triangula faces em leque a partir do primeiro vértice.
                for index in range(1, len(values) - 1):
                    for corner in (values[0], values[index], values[index + 1]):
                        indices = corner.split('/')
                        def resolve(items, value):
                            idx = int(value)
                            return items[idx - 1 if idx > 0 else idx]
                        position = resolve(positions, indices[0])
                        uv = resolve(uvs, indices[1]) if len(indices) > 1 and indices[1] else (0, 0)
                        normal = resolve(normals, indices[2]) if len(indices) > 2 and indices[2] else (0, 0, 0)
                        color = resolve(colors, indices[0])
                        vertices.append((*position, *uv, *normal, *color))
                        batches[-1][1] += 1
    data = np.array(vertices, dtype=np.float32)
    # Calcula normais de face quando o OBJ não fornece normais.
    triangles = data[:, :3].reshape(-1, 3, 3)
    face_normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(face_normals, axis=1, keepdims=True)
    face_normals /= np.maximum(lengths, 1e-8)
    missing = np.linalg.norm(data[:, 5:8], axis=1) < 1e-8
    data[missing, 5:8] = np.repeat(face_normals, 3, axis=0)[missing]
    return data, batches, materials


class ObjModel:
    def __init__(self, path, width=18.0, ground_height=-2.0, center=(0.0, -30.0), height=None,
                 rotation_x=0.0, rotation_z=0.0):
        vertices, self.batches, self.materials = load_obj(Path(path))
        if rotation_x:
            rotation = np.array(glm.rotate(glm.mat4(1.0), glm.radians(rotation_x), glm.vec3(1, 0, 0)))[:3, :3]
            vertices[:, :3] = vertices[:, :3] @ rotation.T
            vertices[:, 5:8] = vertices[:, 5:8] @ rotation.T
        if rotation_z:
            rotation = np.array(glm.rotate(glm.mat4(1.0), glm.radians(rotation_z), glm.vec3(0, 0, 1)))[:3, :3]
            vertices[:, :3] = vertices[:, :3] @ rotation.T
            vertices[:, 5:8] = vertices[:, 5:8] @ rotation.T
        minimum = vertices[:, :3].min(axis=0)
        maximum = vertices[:, :3].max(axis=0)
        extent = maximum - minimum
        dimension = extent[1] if height is not None else extent[0]
        target_size = height if height is not None else width
        if dimension <= 0 or target_size <= 0:
            raise ValueError("O modelo e seu tamanho devem ter dimensões positivas.")
        scale = target_size / dimension
        midpoint = (minimum + maximum) / 2
        transform = glm.translate(glm.mat4(1), glm.vec3(
            center[0] - midpoint[0] * scale,
            ground_height - minimum[1] * scale,
            center[1] - midpoint[2] * scale))
        self.model = np.array(glm.scale(transform, glm.vec3(scale)), dtype=np.float32)
        shaders = Path(__file__).resolve().parent / "shaders"
        self.shader = Shader(str(shaders / "model.vs"), str(shaders / "model.fs"))
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        previous_buffer = int(glGetIntegerv(GL_ARRAY_BUFFER_BINDING))
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        for location, count, offset in ((0, 3, 0), (1, 2, 12), (2, 3, 20), (3, 3, 32)):
            glEnableVertexAttribArray(location)
            glVertexAttribPointer(location, count, GL_FLOAT, GL_FALSE, vertices.strides[0], ctypes.c_void_p(offset))
        glBindVertexArray(previous_vao)
        glBindBuffer(GL_ARRAY_BUFFER, previous_buffer)
        self.textures = []
        previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_2D))
        for name, material in self.materials.items():
            texture_path = material.get('texture')
            if texture_path and texture_path.is_file():
                texture = glGenTextures(1)
                self.textures.append(texture)
                material['id'] = texture
                with Image.open(texture_path) as image:
                    image = image.convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    glBindTexture(GL_TEXTURE_2D, texture)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, image.width, image.height,
                                 0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
                glGenerateMipmap(GL_TEXTURE_2D)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            elif texture_path:
                print(f"Modelo: textura ausente {texture_path.name}; usando cor sólida ({name}).")
                material['color'] = (0.65, 0.62, 0.56)
        glBindTexture(GL_TEXTURE_2D, previous_texture)
        self.locations = {name: glGetUniformLocation(self.shader.getProgram(), name)
                          for name in ('model', 'view', 'projection', 'baseColor', 'hasTexture', 'diffuseMap', 'alphaCutoff')}

    def draw(self, view, projection, models=None, alpha_cutoff=0.0):
        previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
        previous_vao = int(glGetIntegerv(GL_VERTEX_ARRAY_BINDING))
        active_texture = int(glGetIntegerv(GL_ACTIVE_TEXTURE))
        polygon_mode = glGetIntegerv(GL_POLYGON_MODE)
        glActiveTexture(GL_TEXTURE0)
        previous_texture = int(glGetIntegerv(GL_TEXTURE_BINDING_2D))
        try:
            self.shader.use()
            for name, matrix in (('model', self.model), ('view', view), ('projection', projection)):
                glUniformMatrix4fv(self.locations[name], 1, GL_TRUE, matrix)
            glUniform1i(self.locations['diffuseMap'], 0)
            glUniform1f(self.locations['alphaCutoff'], alpha_cutoff)
            glBindVertexArray(self.vao)
            # As cópias compartilham a mesma malha, texturas e programa de sombreadores.
            for matrix in (models if models is not None else (self.model,)):
                glUniformMatrix4fv(self.locations['model'], 1, GL_TRUE, matrix)
                for start, count, name in self.batches:
                    material = self.materials.get(name, {})
                    texture = material.get('id', 0)
                    glUniform1i(self.locations['hasTexture'], bool(texture))
                    glUniform3f(self.locations['baseColor'], *material.get('color', (0.65, 0.62, 0.56)))
                    glBindTexture(GL_TEXTURE_2D, texture)
                    glDrawArrays(GL_TRIANGLES, start, count)
        finally:
            glBindVertexArray(previous_vao)
            glBindTexture(GL_TEXTURE_2D, previous_texture)
            glActiveTexture(active_texture)
            glPolygonMode(GL_FRONT, int(polygon_mode[0]))
            glPolygonMode(GL_BACK, int(polygon_mode[1]))
            glUseProgram(previous_program)

    def close(self):
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        if self.textures:
            glDeleteTextures(len(self.textures), self.textures)
        glDeleteProgram(self.shader.getProgram())

"""Constrói o cercado modular ao redor da torre."""

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


def _mesh_dimensions(path):
    """Calcula dimensões da malha a partir dos vértices OBJ.

    Args:
        path: Caminho do arquivo OBJ.

    Returns:
        Array NumPy com as dimensões X, Y e Z.

    Raises:
        ValueError: Se a malha não tiver dimensões positivas.
    """
    minimum = np.full(3, np.inf)
    maximum = np.full(3, -np.inf)
    with path.open(encoding="utf-8", errors="replace") as source:
        for line in source:
            fields = line.split()
            if fields and fields[0] == "v":
                vertex = np.asarray(tuple(map(float, fields[1:4])))
                minimum = np.minimum(minimum, vertex)
                maximum = np.maximum(maximum, vertex)
    dimensions = maximum - minimum
    if not np.all(np.isfinite(dimensions)) or np.any(dimensions <= 0.0):
        raise ValueError("O modelo do cercado deve ter dimensões positivas.")
    return dimensions


class Fence(ObjModel):
    """Cercado feito de instâncias de uma malha OBJ compartilhada."""

    def __init__(self, path=None, ground_height=-2.0, front_z=-17.5,
                 height=4.0, width_segments=5, depth_segments=9):
        """Carrega os módulos e posiciona os segmentos do cercado.

        Args:
            path: Caminho OBJ opcional dos módulos.
            ground_height: Altura do cercado.
            front_z: Coordenada Z da face frontal.
            height: Altura de cada módulo.
            width_segments: Número ímpar de módulos na largura.
            depth_segments: Número de módulos na profundidade.

        Raises:
            ValueError: Se dimensões ou contagens forem inválidas.
        """
        if height <= 0.0:
            raise ValueError("A altura do cercado deve ser positiva.")
        if width_segments < 3 or width_segments % 2 == 0:
            raise ValueError("A largura do cercado deve ter um número ímpar de módulos.")
        if depth_segments < 1:
            raise ValueError("A profundidade do cercado deve ter pelo menos um módulo.")

        if path is None:
            path = (Path(__file__).resolve().parent / "objetos" /
                    "fence_continuous" / "fence.obj")
        else:
            path = Path(path)

        dimensions = _mesh_dimensions(path)
        segment_length = dimensions[0] * height / dimensions[1]
        super().__init__(path, height=height, ground_height=ground_height,
                         center=(0.0, 0.0))

        half_width = width_segments * segment_length / 2.0
        back_z = front_z - depth_segments * segment_length
        self.models = []
        gate_index = width_segments // 2
        for index in range(width_segments):
            x = -half_width + (index + 0.5) * segment_length
            if index != gate_index:
                self.models.append(self._instance_model(x, front_z))
            self.models.append(self._instance_model(x, back_z))

        for index in range(depth_segments):
            z = front_z - (index + 0.5) * segment_length
            self.models.append(self._instance_model(-half_width, z, 90.0))
            self.models.append(self._instance_model(half_width, z, 90.0))

    def _instance_model(self, x, z, rotation_degrees=0.0):
        """Compõe a matriz de um módulo na posição e orientação indicadas.

        Args:
            x: Coordenada X do módulo.
            z: Coordenada Z do módulo.
            rotation_degrees: Rotação ao redor do eixo Y.

        Returns:
            Matriz de modelo float32.
        """
        transform = glm.translate(glm.mat4(1.0), glm.vec3(x, 0.0, z))
        if rotation_degrees:
            transform = glm.rotate(
                transform, glm.radians(rotation_degrees), glm.vec3(0.0, 1.0, 0.0))
        return np.array(transform, dtype=np.float32) @ self.model

    def draw(self, view, projection):
        """Desenha todos os segmentos do cercado.

        Args:
            view: Matriz de visualização 4x4.
            projection: Matriz de projeção 4x4.
        """
        super().draw(view, projection, models=self.models, cull_back_faces=True)

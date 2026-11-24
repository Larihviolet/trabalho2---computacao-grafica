"""Distribui cópias de um grupo de carvalhos usando malha compartilhada."""

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


class OakTrees:
    """Conjunto de árvores com transformações e materiais por instância."""

    def __init__(self, path=None, ground_height=-2.0, height=8.0, seed=42):
        """Carrega o grupo de árvores e distribui cópias determinísticas.

        Args:
            path: Caminho OBJ opcional do grupo de árvores.
            ground_height: Altura da base das árvores.
            height: Altura alvo do grupo.
            seed: Semente para pequenas variações de posição e escala.
        """
        if path is None:
            path = (Path(__file__).resolve().parent / "objetos" / "oak_trees" /
                    "oak_trees.obj")
        # O arquivo contém três árvores; cada cópia mantém esse grupo.
        self.asset = ObjModel(path, height=height, ground_height=0.0, center=(0.0, 0.0))
        rng = np.random.default_rng(seed)
        self.models = []
        # Faixas laterais preservam uma clareira para a torre e o caminho central.
        for z in (-65.0, -47.0, -29.0, -11.0, 20.0, 42.0):
            for x in (-40.0, -19.0, 19.0, 40.0):
                position = glm.vec3(x + rng.uniform(-3.0, 3.0), ground_height,
                                    z + rng.uniform(-3.0, 3.0))
                transform = glm.translate(glm.mat4(1.0), position)
                angle = float(rng.uniform(0, 2 * np.pi))
                transform = glm.rotate(transform, angle, glm.vec3(0, 1, 0))
                transform = glm.scale(transform, glm.vec3(float(rng.uniform(0.8, 1.2))))
                model = np.array(transform, dtype=np.float32) @ self.asset.model
                self.models.append(model)
        self.materials = None

    def draw(self, view, projection):
        """Desenha as árvores sem culling para preservar folhas planas.

        Args:
            view: Matriz de visualização 4x4.
            projection: Matriz de projeção 4x4.
        """
        # As folhas são planos visíveis dos dois lados; o canal alfa recorta seu contorno.
        self.asset.draw(
            view, projection, models=self.models, alpha_cutoff=0.5,
            materials=self.materials, cull_back_faces=False)

    def close(self):
        """Libera a malha e os recursos compartilhados das árvores."""
        self.asset.close()

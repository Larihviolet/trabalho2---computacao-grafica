# Distribuição de grupos de carvalhos com recursos compartilhados.

from pathlib import Path

import glm
import numpy as np
from OpenGL.GL import GL_CULL_FACE, glIsEnabled, glDisable, glEnable

from obj_model import ObjModel


class OakTrees:
    def __init__(self, path=None, ground_height=-2.0, height=8.0, seed=42):
        if path is None:
            path = Path(__file__).resolve().parent / "objetos" / "oak_trees" / "oak_trees.obj"
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
                transform = glm.rotate(transform, float(rng.uniform(0, 2 * np.pi)), glm.vec3(0, 1, 0))
                transform = glm.scale(transform, glm.vec3(float(rng.uniform(0.8, 1.2))))
                self.models.append(np.array(transform, dtype=np.float32) @ self.asset.model)

    def draw(self, view, projection):
        # As folhas são planos visíveis dos dois lados; o canal alfa recorta seu contorno.
        culling = bool(glIsEnabled(GL_CULL_FACE))
        glDisable(GL_CULL_FACE)
        try:
            self.asset.draw(view, projection, models=self.models, alpha_cutoff=0.5)
        finally:
            if culling:
                glEnable(GL_CULL_FACE)

    def close(self):
        self.asset.close()

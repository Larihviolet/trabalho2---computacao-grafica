# Objetos do ritual dentro da torre, com posições e tamanhos configuráveis.

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


def around_pivot(pivot, transform):
    # Mantém o ponto de apoio fixo durante rotação ou escala.
    translation = glm.translate(glm.mat4(1.0), glm.vec3(*pivot))
    inverse_translation = glm.translate(glm.mat4(1.0), -glm.vec3(*pivot))
    return np.array(translation * transform * inverse_translation, dtype=np.float32)


class TowerInterior:
    def __init__(self, center=(0.0, -30.0), floor_height=-2.0):
        root = Path(__file__).resolve().parent / "objetos"
        x, z = center
        self.circle = ObjModel(root / "demoncircle" / "demoncircle.obj",
                               width=3.2, ground_height=floor_height + 0.04, center=(x, z))
        self.witch = ObjModel(root / "witch" / "mona_fbx_with_textures.obj",
                              height=2.8, ground_height=floor_height,
                              center=(x + 2.4, z), rotation_x=90.0)
        self.wizard = ObjModel(root / "toadbert_the_wizard" / "toadbert_the_wizard_10th_sept_2020.obj",
                               height=2.8, ground_height=floor_height + 0.65, center=(x, z))
        self.objects = (self.circle, self.witch, self.wizard)
        self.circle_pivot = (x, floor_height + 0.04, z)
        self.wizard_pivot = (x, floor_height + 0.65, z)
        self.circle_base = self.circle.model.copy()
        self.wizard_base = self.wizard.model.copy()
        # O modelo corrigido olha para +Z; girar -90 graus o orienta para o círculo.
        rotation = glm.rotate(glm.mat4(1.0), glm.radians(-90.0), glm.vec3(0, 1, 0))
        self.witch.model = around_pivot((x + 2.4, floor_height, z), rotation) @ self.witch.model
        self.small_height = 0.35
        self.large_height = 2.8
        self.growth_duration = 2.5
        self.growth_progress = 0.0
        self.growing = False
        self.circle_angle = 0.0
        self.circle_speed = 30.0
        self.circle_rotation_enabled = True
        self.update(0.0)

    def toggle_wizard_size(self):
        # Pressionar novamente também permite inverter uma transição em andamento.
        self.growing = not self.growing

    def toggle_circle_rotation(self):
        self.circle_rotation_enabled = not self.circle_rotation_enabled

    def update(self, delta_time):
        elapsed = max(float(delta_time), 0.0)
        direction = 1.0 if self.growing else -1.0
        self.growth_progress = float(np.clip(
            self.growth_progress + direction * elapsed / self.growth_duration, 0.0, 1.0))
        # Interpolação suave, com limites exatos e sem acumular erro nas matrizes.
        progress = self.growth_progress
        eased = progress * progress * (3.0 - 2.0 * progress)
        height = self.small_height + (self.large_height - self.small_height) * eased
        scale = glm.scale(glm.mat4(1.0), glm.vec3(height / self.large_height))
        self.wizard.model = around_pivot(self.wizard_pivot, scale) @ self.wizard_base
        if self.circle_rotation_enabled:
            self.circle_angle = (self.circle_angle + self.circle_speed * elapsed) % 360.0
        rotation = glm.rotate(glm.mat4(1.0), glm.radians(self.circle_angle), glm.vec3(0, 1, 0))
        self.circle.model = around_pivot(self.circle_pivot, rotation) @ self.circle_base

    def draw(self, view, projection):
        for obj in self.objects:
            obj.draw(view, projection, alpha_cutoff=0.5)

    def close(self):
        for obj in self.objects:
            obj.close()

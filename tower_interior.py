#Configura e atualiza os objetos do ritual dentro da torre.

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


def around_pivot(pivot, transform):
    #Aplica uma transformação mantendo fixo o ponto de apoio.
    # A composição translada ao pivô, transforma e translada de volta.
    translation = glm.translate(glm.mat4(1.0), glm.vec3(*pivot))
    inverse_translation = glm.translate(glm.mat4(1.0), -glm.vec3(*pivot))
    return np.array(translation * transform * inverse_translation, dtype=np.float32)


class TowerInterior:
    #Modelos do círculo ritual, da bruxa e do mago dentro da torre.

    def __init__(self, center=(0.0, -30.0), floor_height=-2.0):
       #Carrega e posiciona os modelos internos da torre.

        root = Path(__file__).resolve().parent / "objetos"
        x, z = center
        self.circle = ObjModel(
            root / "demoncircle" / "demoncircle.obj",
            width=3.2, ground_height=floor_height + 0.04, center=(x, z))
        self.witch = ObjModel(
            root / "witch" / "mona_fbx_with_textures.obj",
            height=2.8, ground_height=floor_height,
            center=(x + 2.4, z), rotation_x=90.0)
        wizard_path = (
            root / "toadbert_the_wizard" /
            "toadbert_the_wizard_10th_sept_2020.obj")
        self.wizard = ObjModel(
            wizard_path, height=4.0,
            ground_height=floor_height + 0.65, center=(x, z))
        self.objects = (self.circle, self.witch, self.wizard)
        self.circle_pivot = (x, floor_height + 0.04, z)
        wizard_pivot = (x, floor_height + 0.65, z)
        self.circle_base = self.circle.model.copy()
        wizard_base = self.wizard.model.copy()
        # Mantém a escala inicial atual sem recalculá-la em todos os quadros.
        initial_scale = glm.scale(glm.mat4(1.0), glm.vec3(0.5))
        self.wizard.model = around_pivot(wizard_pivot, initial_scale) @ wizard_base
        # O modelo corrigido olha para +Z; girar -90 graus o orienta para o círculo.
        rotation = glm.rotate(glm.mat4(1.0), glm.radians(-90.0), glm.vec3(0, 1, 0))
        witch_pivot = (x + 2.4, floor_height, z)
        self.witch.model = around_pivot(witch_pivot, rotation) @ self.witch.model
        self.circle_angle = 0.0
        self.circle_speed = 30.0
        self.update(0.0)

    def update(self, delta_time):
        #Atualiza a rotação contínua do círculo ritual.
        #delta_time: Tempo desde a atualização anterior, em segundos.
        elapsed = max(float(delta_time), 0.0)
        self.circle_angle = (self.circle_angle + self.circle_speed * elapsed) % 360.0
        rotation = glm.rotate(
            glm.mat4(1.0), glm.radians(self.circle_angle), glm.vec3(0, 1, 0))
        self.circle.model = around_pivot(self.circle_pivot, rotation) @ self.circle_base

    def draw(self, view, projection):
       #Desenha o círculo, a bruxa e o mago.
        for obj in self.objects:
            obj.draw(view, projection, alpha_cutoff=0.5,
                     cull_back_faces=obj is not self.circle,
                     demon_circle_glow=obj is self.circle)

    def close(self):
        #Libera os recursos OpenGL dos objetos internos.
        for obj in self.objects:
            obj.close()

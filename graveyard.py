# Lápides atrás da torre e estátua em órbita, com recursos compartilhados.

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


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
        self.update(0.0)

    def update(self, delta_time):
        # Usa o tempo entre quadros e reconstrói a matriz para evitar deriva na órbita.
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

    def draw(self, view, projection):
        self.stone.draw(view, projection, models=self.stone_models)
        self.angel.draw(view, projection)

    def close(self):
        self.stone.close()
        self.angel.close()

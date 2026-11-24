#Distribui lápides e anima a posição orbital da estátua anjo.

from pathlib import Path

import glm
import numpy as np

from obj_model import ObjModel


class Graveyard:
    #Cena do cemitério com lápides instanciadas e uma luz móvel.

    def __init__(self, center=(0.0, -30.0), ground_height=-2.0,
                 orbit_radius=10.0, orbit_speed=12.0):
       #Cria as lápides, a estátua e o estado inicial da órbita.

        #Args:
            #center: Centro X e Z da torre e da órbita.
            #ground_height: Altura do chão.
            #orbit_radius: Raio da órbita da estátua.
            #orbit_speed: Velocidade angular em graus por segundo.

        if orbit_radius <= 0:
            raise ValueError("O raio da órbita deve ser positivo.")
        root = Path(__file__).resolve().parent / "objetos"
        self.center = center
        self.ground_height = ground_height
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = 0.0
        self.angel_movement_enabled = True
        self.stone = ObjModel(root / "graveyard_stone" / "graveyard_stone.obj",
                              height=1.8, ground_height=0.0, center=(0.0, 0.0))
        self.stone_models = []
        rng = np.random.default_rng(17)
        # Três fileiras atrás da torre, com corredor central e pequenas variações.
        for distance in (16.0, 23.0, 30.0):
            for offset in (-9.0, -3.0, 3.0, 9.0):
                position = glm.vec3(
                    center[0] + offset + rng.uniform(-0.3, 0.3),
                    ground_height,
                    center[1] - distance + rng.uniform(-0.4, 0.4),
                )
                transform = glm.translate(glm.mat4(1.0), position)
                rotation = float(rng.uniform(-0.12, 0.12))
                transform = glm.rotate(transform, rotation, glm.vec3(0, 1, 0))
                scale = float(rng.uniform(0.9, 1.1))
                transform = glm.scale(transform, glm.vec3(scale))
                model = np.array(transform, dtype=np.float32) @ self.stone.model
                self.stone_models.append(model)
        self.stone_materials = None
        angel_path = root / "weeping_angel" / "weeping_angel.obj"
        self.angel = ObjModel(
            angel_path, height=3.2, ground_height=0.0,
            center=(0.0, 0.0), rotation_z=90.0)
        self.angel_base = self.angel.model.copy()
        self.update(0.0)

    def update(self, delta_time):
        #Atualiza a órbita da estátua e a direção da luz associada.

        #Args:
            #delta_time: Tempo desde a atualização anterior, em segundos.
     
        # Usa o tempo entre quadros e reconstrói a matriz para evitar deriva na órbita.
        if self.angel_movement_enabled:
            elapsed = max(float(delta_time), 0.0)
            self.orbit_angle = (self.orbit_angle + self.orbit_speed * elapsed) % 360.0
        angle = np.radians(self.orbit_angle)
        self.angel_position = (
            self.center[0] + self.orbit_radius * np.cos(angle),
            self.ground_height,
            self.center[1] + self.orbit_radius * np.sin(angle))
        transform = glm.translate(glm.mat4(1.0), glm.vec3(*self.angel_position))
        # Orienta a estátua na direção tangente à trajetória.
        transform = glm.rotate(transform, float(np.pi / 2.0 - angle), glm.vec3(0, 1, 0))
        self.angel.model = np.array(transform, dtype=np.float32) @ self.angel_base
        self.light_direction = (-float(np.sin(angle)), 0.0, float(np.cos(angle)))
        self.light_position = tuple(
            self.angel_position[index] + 0.35 * self.light_direction[index]
            for index in range(3))
        self.light_position = (self.light_position[0],
                               self.ground_height + 2.5,
                               self.light_position[2])

    def toggle_angel_movement(self):
        #Alterna o movimento orbital da estátua.
        self.angel_movement_enabled = not self.angel_movement_enabled

    def draw(self, view, projection):
        #Desenha as lápides e a estátua anjo.
        self.stone.draw(view, projection, models=self.stone_models,
                        materials=self.stone_materials, cull_back_faces=True)
        self.angel.draw(view, projection)

    def close(self):
        #Libera os recursos OpenGL dos modelos do cemitério.
        self.stone.close()
        self.angel.close()

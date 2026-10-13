# Interface do castelo preservada para reutilização na cena.

from obj_model import ObjModel, load_obj


# Mantém o nome do carregador disponível para usos existentes.
load_castle = load_obj


class Castle(ObjModel):
    def __init__(self, path, width=18.0, ground_height=-2.0, center=(0.0, -30.0)):
        super().__init__(path, width=width, ground_height=ground_height, center=center)

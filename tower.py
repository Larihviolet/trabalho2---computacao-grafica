# Configuração da torre, usando a renderização compartilhada de modelos OBJ.

from pathlib import Path

from obj_model import ObjModel


class Tower(ObjModel):
    def __init__(self, path=None, height=16.0, ground_height=-2.0, center=(0.0, -30.0)):
        if path is None:
            path = Path(__file__).resolve().parent / "objetos" / "tower" / "4a61e4166fea6acd19165b47fd76fb3c.obj"
        super().__init__(path, height=height, ground_height=ground_height, center=center)

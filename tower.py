"""Modelo da torre principal renderizado pelo carregador OBJ compartilhado."""

from pathlib import Path

from obj_model import ObjModel


class Tower(ObjModel):
    """Torre dimensionada e posicionada na cena."""

    def __init__(self, path=None, height=16.0, ground_height=-2.0, center=(0.0, -30.0)):
        """Carrega a malha da torre e aplica sua escala e posição.

        Args:
            path: Caminho OBJ opcional; usa o recurso da cena por padrão.
            height: Altura desejada da torre.
            ground_height: Altura do ponto de apoio.
            center: Coordenadas X e Z do centro.
        """
        if path is None:
            path = (Path(__file__).resolve().parent / "objetos" / "tower" /
                    "4a61e4166fea6acd19165b47fd76fb3c.obj")
        super().__init__(
            path, height=height, ground_height=ground_height, center=center)

    def draw(self, view, projection):
        """Desenha a torre com descarte de faces traseiras."""
        super().draw(view, projection, cull_back_faces=True)

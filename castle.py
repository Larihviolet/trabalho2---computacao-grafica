"""Compatibilidade para carregar e instanciar modelos de castelo."""

from obj_model import ObjModel, load_obj


# Mantém o nome do carregador disponível para usos existentes.
load_castle = load_obj


class Castle(ObjModel):
    """Modelo OBJ de castelo com escala e posicionamento configuráveis."""

    def __init__(self, path, width=18.0, ground_height=-2.0, center=(0.0, -30.0)):
        """Carrega o castelo indicado.

        Args:
            path: Caminho do arquivo OBJ.
            width: Largura desejada do modelo.
            ground_height: Altura da base do modelo.
            center: Coordenadas X e Z do centro.
        """
        super().__init__(path, width=width, ground_height=ground_height, center=center)

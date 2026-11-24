"""Limita a posição da câmera aos limites físicos da cena."""

import glm


class CameraBounds:
    """Armazena os limites horizontal e vertical permitidos para a câmera."""

    def __init__(self, ground_size, ground_height, max_height=60.0,
                 edge_margin=0.25, floor_clearance=1.6):
        """Inicializa os limites a partir das dimensões do chão.

        Args:
            ground_size: Largura e profundidade do chão quadrado.
            ground_height: Altura do plano do chão.
            max_height: Altura máxima da câmera acima do chão.
            edge_margin: Distância horizontal mantida das bordas.
            floor_clearance: Altura mínima da câmera acima do chão.
        """
        if ground_size <= 0 or edge_margin < 0 or edge_margin >= ground_size / 2:
            raise ValueError("O chão deve comportar a margem da câmera.")
        if floor_clearance <= 0 or max_height <= floor_clearance:
            raise ValueError("O teto deve ficar acima da altura mínima da câmera.")
        self.horizontal_limit = ground_size / 2.0 - edge_margin
        self.min_y = ground_height + floor_clearance
        self.max_y = ground_height + max_height

    def constrain(self, position):
        """Restringe a posição aos limites e retorna um novo vetor.

        Args:
            position: Posição da câmera em coordenadas de mundo.

        Returns:
            Um vetor glm.vec3 dentro dos limites configurados.
        """
        # Limitar cada eixo permite deslizar pela borda sem atravessá-la.
        limit = self.horizontal_limit
        return glm.vec3(
            min(max(position.x, -limit), limit),
            min(max(position.y, self.min_y), self.max_y),
            min(max(position.z, -limit), limit))

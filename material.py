#Define os coeficientes de iluminação usados pelos materiais da cena.

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Material:
    #Coeficientes difuso, especular e de brilho de uma superfície.

    #Attributes:
      #  diffuse: Intensidade da reflexão difusa entre 0 e 1.
      #  specular: Intensidade da reflexão especular entre 0 e 1.
      #  shininess: Expoente positivo do brilho especular.

    diffuse: float
    specular: float
    shininess: float

    def __post_init__(self):
        #Valida os coeficientes após a criação do material.

        if not all(isfinite(value) for value in (
                self.diffuse, self.specular, self.shininess)):
            raise ValueError("Os parâmetros do material devem ser finitos.")
        if not 0.0 <= self.diffuse <= 1.0:
            raise ValueError("A reflexão difusa deve estar entre 0 e 1.")
        if not 0.0 <= self.specular <= 1.0:
            raise ValueError("A reflexão especular deve estar entre 0 e 1.")
        if self.shininess <= 0.0:
            raise ValueError("O expoente especular deve ser positivo.")

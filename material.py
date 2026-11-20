from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Material:
    diffuse: float
    specular: float
    shininess: float
    ambient: float = 1.0

    def __post_init__(self):
        if not all(isfinite(value) for value in (
                self.diffuse, self.specular, self.shininess, self.ambient)):
            raise ValueError("Os parâmetros do material devem ser finitos.")
        if not 0.0 <= self.diffuse <= 1.0:
            raise ValueError("A reflexão difusa deve estar entre 0 e 1.")
        if not 0.0 <= self.specular <= 1.0:
            raise ValueError("A reflexão especular deve estar entre 0 e 1.")
        if not 0.0 <= self.ambient <= 1.0:
            raise ValueError("A reflexão ambiente deve estar entre 0 e 1.")
        if self.shininess <= 0.0:
            raise ValueError("O expoente especular deve ser positivo.")


DEFAULT_MATERIAL = Material(diffuse=0.8, specular=0.2, shininess=32.0)

"""Compila, vincula e controla programas de shaders OpenGL."""

from pathlib import Path

from OpenGL.GL import *

class Shader:
    """Programa OpenGL vinculado a um par de shaders de vértice e fragmento."""

    def __init__(self, vertex_path: str, fragment_path: str):
        """Carrega, compila e vincula os arquivos de shader.

        Args:
            vertex_path: Caminho do shader de vértice, absoluto ou relativo.
            fragment_path: Caminho do shader de fragmento, absoluto ou relativo.

        Raises:
            RuntimeError: Se a compilação ou vinculação falhar.
        """
        shader_directory = Path(__file__).resolve().parent
        vertex_path = Path(vertex_path)
        fragment_path = Path(fragment_path)
        if not vertex_path.is_absolute():
            vertex_path = shader_directory / vertex_path
        if not fragment_path.is_absolute():
            fragment_path = shader_directory / fragment_path

        vertex_code = vertex_path.read_text(encoding="utf-8")
        fragment_code = fragment_path.read_text(encoding="utf-8")

        # Compila os estágios e vincula o programa usado pelos renderizadores.
        vertex = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex, vertex_code)
        glCompileShader(vertex)
        self.check_compile_errors(vertex, "VERTEX")
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment, fragment_code)
        glCompileShader(fragment)
        self.check_compile_errors(fragment, "FRAGMENT")
        self.program_id = glCreateProgram()
        glAttachShader(self.program_id, vertex)
        glAttachShader(self.program_id, fragment)
        glLinkProgram(self.program_id)
        self.check_compile_errors(self.program_id, "PROGRAM")
        glDeleteShader(vertex)
        glDeleteShader(fragment)


    def get_program(self):
        """Retorna o identificador do programa OpenGL.

        Returns:
            Identificador inteiro do programa.
        """
        return self.program_id
        
    def use(self) -> None:
        """Ativa este programa OpenGL para os próximos comandos de desenho."""
        glUseProgram(self.program_id)
        
    def check_compile_errors(self, shader: int, shader_type: str) -> None:
        """Verifica erros de compilação ou vinculação do shader.

        Args:
            shader: Identificador do shader ou programa OpenGL.
            shader_type: ``VERTEX``, ``FRAGMENT`` ou ``PROGRAM``.

        Raises:
            RuntimeError: Se o shader não compilar ou o programa não vincular.
        """
        if shader_type != "PROGRAM":
            success = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if not success:
                info_log = glGetShaderInfoLog(shader)
                raise RuntimeError(
                    "ERROR::SHADER_COMPILATION_ERROR of type: "
                    + shader_type + "\n" + info_log.decode(errors="replace"))
        else:
            success = glGetProgramiv(shader, GL_LINK_STATUS)
            if not success:
                info_log = glGetProgramInfoLog(shader)
                raise RuntimeError(
                    "ERROR::PROGRAM_LINKING_ERROR of type: "
                    + shader_type + "\n" + info_log.decode(errors="replace"))

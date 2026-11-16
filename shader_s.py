from pathlib import Path

from OpenGL.GL import *

class Shader:
    def __init__(self, vertexPath: str, fragmentPath: str):
        shader_directory = Path(__file__).resolve().parent
        vertex_path = Path(vertexPath)
        fragment_path = Path(fragmentPath)
        if not vertex_path.is_absolute():
            vertex_path = shader_directory / vertex_path
        if not fragment_path.is_absolute():
            fragment_path = shader_directory / fragment_path

        vertexCode = vertex_path.read_text(encoding="utf-8")
        fragmentCode = fragment_path.read_text(encoding="utf-8")

        # 2. compile shaders
        vertex = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex, vertexCode)
        glCompileShader(vertex)
        self.checkCompileErrors(vertex, "VERTEX")
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment, fragmentCode)
        glCompileShader(fragment)
        self.checkCompileErrors(fragment, "FRAGMENT")
        self.ID = glCreateProgram()
        glAttachShader(self.ID, vertex)
        glAttachShader(self.ID, fragment)
        glLinkProgram(self.ID)
        self.checkCompileErrors(self.ID, "PROGRAM")
        glDeleteShader(vertex)
        glDeleteShader(fragment)

    # get program
    # ------------------------------------------------------------------------
    def getProgram(self):
        return self.ID
        
    # activate the shader
    # ------------------------------------------------------------------------
    def use(self) -> None:
        glUseProgram(self.ID)
        
    # utility uniform functions
    # ------------------------------------------------------------------------
    def setBool(self, name: str, value: bool) -> None:
        glUniform1i(glGetUniformLocation(self.ID, name), int(value))
    # ------------------------------------------------------------------------
    def setInt(self, name: str, value: int) -> None:
        glUniform1i(glGetUniformLocation(self.ID, name), value)
    # ------------------------------------------------------------------------
    def setFloat(self, name: str, value: float) -> None:
        glUniform1f(glGetUniformLocation(self.ID, name), value)

    # utility function for checking shader compilation/linking errors.
    # ------------------------------------------------------------------------
    def checkCompileErrors(self, shader: int, type: str) -> None:
        if (type != "PROGRAM"):
            success = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if (not success):
                infoLog = glGetShaderInfoLog(shader)
                raise RuntimeError(
                    "ERROR::SHADER_COMPILATION_ERROR of type: "
                    + type + "\n" + infoLog.decode(errors="replace"))
        else:
            success = glGetProgramiv(shader, GL_LINK_STATUS)
            if (not success):
                infoLog = glGetProgramInfoLog(shader)
                raise RuntimeError(
                    "ERROR::PROGRAM_LINKING_ERROR of type: "
                    + type + "\n" + infoLog.decode(errors="replace"))
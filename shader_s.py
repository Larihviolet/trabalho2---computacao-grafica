from OpenGL.GL import *

class Shader:
    def __init__(self, vertexPath: str, fragmentPath: str):
        # 1. Lê o código dos sombreadores de vértices e fragmentos.
        try:
            # Abre os arquivos dos sombreadores.
            vShaderFile = open(vertexPath)
            fShaderFile = open(fragmentPath)
            
            # Lê o conteúdo dos arquivos como texto.
            vertexCode = vShaderFile.read()
            fragmentCode = fShaderFile.read()
            # Fecha os arquivos após a leitura.
            vShaderFile.close()
            fShaderFile.close()

            # 2. Compila os sombreadores.
            # Sombreador de vértices.
            vertex = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex, vertexCode)
            glCompileShader(vertex)
            self.checkCompileErrors(vertex, "VERTEX")
            # Sombreador de fragmentos.
            fragment = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment, fragmentCode)
            glCompileShader(fragment)
            self.checkCompileErrors(fragment, "FRAGMENT")
            # Cria o programa que combina os dois sombreadores.
            self.ID = glCreateProgram()
            glAttachShader(self.ID, vertex)
            glAttachShader(self.ID, fragment)
            glLinkProgram(self.ID)
            self.checkCompileErrors(self.ID, "PROGRAM")
            # Após a ligação ao programa, libera os sombreadores individuais.
            glDeleteShader(vertex)
            glDeleteShader(fragment)
        
        except IOError:
            print("ERROR::SHADER::FILE_NOT_SUCCESFULLY_READ")
            
        

    # Retorna o identificador do programa OpenGL.
    # ------------------------------------------------------------------------
    def getProgram(self):
        return self.ID
        
    # Ativa o programa de sombreadores.
    # ------------------------------------------------------------------------
    def use(self) -> None:
        glUseProgram(self.ID)
        
    # Funções auxiliares para enviar variáveis uniformes ao programa.
    # ------------------------------------------------------------------------
    def setBool(self, name: str, value: bool) -> None:
        glUniform1i(glGetUniformLocation(self.ID, name), int(value))
    # ------------------------------------------------------------------------
    def setInt(self, name: str, value: int) -> None:
        glUniform1i(glGetUniformLocation(self.ID, name), value)
    # ------------------------------------------------------------------------
    def setFloat(self, name: str, value: float) -> None:
        glUniform1f(glGetUniformLocation(self.ID, name), value)

    # Verifica erros de compilação dos sombreadores e de ligação do programa.
    # ------------------------------------------------------------------------
    def checkCompileErrors(self, shader: int, type: str) -> None:
        if (type != "PROGRAM"):
            success = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if (not success):
                infoLog = glGetShaderInfoLog(shader)
                print("ERROR::SHADER_COMPILATION_ERROR of type: " + type + "\n" + infoLog.decode() + "\n -- --------------------------------------------------- -- ")
        else:
            success = glGetProgramiv(shader, GL_LINK_STATUS)
            if (not success):
                infoLog = glGetProgramInfoLog(shader)
                print("ERROR::PROGRAM_LINKING_ERROR of type: " + type + "\n" + infoLog.decode() + "\n -- --------------------------------------------------- -- ")

                
    

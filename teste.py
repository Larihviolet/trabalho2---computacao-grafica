especular = False
#Importando os pacotes necessários
import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math
from pathlib import Path
from numpy import random
from PIL import Image

from shader_s import Shader

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

altura = 700
largura = 700

window = glfw.create_window(largura, altura, "Programa", None, None)

if (window == None):
    print("Failed to create GLFW window")
    glfwTerminate()
    
glfw.make_context_current(window)


fragmentShaderFile = "fragment_shader.fs"
ourShader = Shader("vertex_shader.vs", fragmentShaderFile)
ourShader.use()

program = ourShader.getProgram()
glUniform1i(glGetUniformLocation(program, "samplerTexture"), 0)
# Carregando Modelos (Vértices e Texturas) a partir de arquivos
glEnable(GL_TEXTURE_2D)
glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
glEnable( GL_BLEND )
glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
glEnable(GL_LINE_SMOOTH)


global vertices_list
vertices_list = []    
global textures_coord_list
textures_coord_list = []
global normals_list
normals_list = []


def load_model_from_file(filename):
    """Loads a Wavefront OBJ file. """
    objects = {}
    vertices = []
    normals = []
    texture_coords = []
    faces = []

    material = None

    # abre o arquivo obj para leitura
    for line in open(filename, "r"): ## para cada linha do arquivo .obj
        if line.startswith('#'): continue ## ignora comentarios
        values = line.split() # quebra a linha por espaço
        if not values: continue

        ### recuperando vertices
        if values[0] == 'v':
            vertices.append(values[1:4])

        ### recuperando normais
        if values[0] == 'vn':
            normals.append(values[1:4])

        ### recuperando coordenadas de textura
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])

        ### recuperando faces 
        elif values[0] in ('usemtl', 'usemat'):
            material = values[1]
        elif values[0] == 'f':
            face = []
            face_texture = []
            face_normals = []
            for v in values[1:]:
                w = v.split('/')
                face.append(int(w[0]))
                face_normals.append(int(w[2]))
                if len(w) >= 2 and len(w[1]) > 0:
                    face_texture.append(int(w[1]))
                else:
                    face_texture.append(0)

            faces.append((face, face_texture, face_normals, material))

    model = {}
    model['vertices'] = vertices
    model['texture'] = texture_coords
    model['faces'] = faces
    model['normals'] = normals ############ Novo!

    return model


def load_texture_from_file(img_textura):
    texture_id = glGenTextures(1)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    with Image.open(img_textura) as source:
        image = source.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, image.width, image.height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
    glGenerateMipmap(GL_TEXTURE_2D)
    return texture_id



'''
É possível encontrar, na Internet, modelos .obj cujas faces não sejam triângulos. Nesses casos, precisamos gerar triângulos a partir dos vértices da face.
A função abaixo retorna a sequência de vértices que permite isso. Créditos: Hélio Nogueira Cardoso e Danielle Modesti (SCC0650 - 2024/2).
'''
def circular_sliding_window_of_three(arr):
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result
    
def load_obj_and_texture(objFile, texturesByMaterial, rotation_x=0.0, target_height=None):
    modelo = load_model_from_file(objFile)

    if rotation_x:
        angle = math.radians(rotation_x)
        cosine, sine = math.cos(angle), math.sin(angle)
        rotation = np.array(
            ((1, 0, 0), (0, cosine, -sine), (0, sine, cosine)),
            dtype=np.float32)
        positions = np.asarray(modelo['vertices'], dtype=np.float32) @ rotation.T
        modelo['vertices'] = positions.tolist()
        modelo['normals'] = (
            np.asarray(modelo['normals'], dtype=np.float32) @ rotation.T).tolist()
    if target_height is not None:
        positions = np.asarray(modelo['vertices'], dtype=np.float32)
        minimum = positions.min(axis=0)
        maximum = positions.max(axis=0)
        dimension = maximum[1] - minimum[1]
        if dimension <= 0 or target_height <= 0:
            raise ValueError("A altura de destino do modelo deve ser positiva.")
        scale = target_height / dimension
        positions = (positions - (minimum + maximum) / 2) * scale
        positions[:, 1] += target_height / 2
        modelo['vertices'] = positions.tolist()

    texture_ids = {
        material: load_texture_from_file(texture_path)
        for material, texture_path in texturesByMaterial.items()
    }
    batches = []
    vertex_start = len(vertices_list)
    for face in modelo['faces']:
        material = face[3]
        if material not in texture_ids:
            if None not in texture_ids:
                raise ValueError(f"Textura não definida para o material {material!r}.")
            material = None
        batch_texture_id = texture_ids[material]
        batch_start = len(vertices_list)
        for vertice_id in circular_sliding_window_of_three(face[0]):
            vertices_list.append(modelo['vertices'][vertice_id - 1])
        for texture_index in circular_sliding_window_of_three(face[1]):
            textures_coord_list.append(modelo['texture'][texture_index - 1])
        for normal_id in circular_sliding_window_of_three(face[2]):
            normals_list.append(modelo['normals'][normal_id - 1])
        vertex_count = len(vertices_list) - batch_start
        if batches and batches[-1][2] == batch_texture_id:
            start, count, previous_texture = batches[-1]
            batches[-1] = (start, count + vertex_count, previous_texture)
        else:
            batches.append((batch_start, vertex_count, batch_texture_id))

    return vertex_start, len(vertices_list) - vertex_start, batches

# carrega caixa (modelo e texturas)
witch_dir = Path(__file__).resolve().parent / "objetos" / "witch"
witch_batches = load_obj_and_texture(
    witch_dir / "mona_fbx_with_textures.obj",
    {
        "material": witch_dir / "material.png",
        "material_1": witch_dir / "material_1.png",
        "material_2": witch_dir / "material_2.png",
        "material_3": witch_dir / "material_3.png",
    },
    rotation_x=90.0,
    target_height=3.0)[2]


ka = 1.0 # coeficiente de reflexao ambiente do modelo
kd = 0.9 # coeficiente de reflexao difusa do modelo
ks = 0.5 # coeficiente de reflexao especular do modelo


def desenha_witch(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):

    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)


    loc_ka = glGetUniformLocation(program, "ka") # recuperando localizacao da variavel ka na GPU
    glUniform1f(loc_ka, ka) ### envia ka pra gpu
    
    loc_kd = glGetUniformLocation(program, "kd") # recuperando localizacao da variavel kd na GPU
    glUniform1f(loc_kd, kd) ### envia kd pra gpu    
    

    if especular:
        ns = ns_inc # expoente de reflexao especular
        
        loc_ks = glGetUniformLocation(program, "ks") # recuperando localizacao da variavel ks na GPU
        glUniform1f(loc_ks, ks) ### envia ks pra gpu        
    
        loc_ns = glGetUniformLocation(program, "ns") # recuperando localizacao da variavel ns na GPU
        glUniform1f(loc_ns, ns) ### envia ns pra gpu        
           
    for start, count, texture_id in witch_batches:
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glDrawArrays(GL_TRIANGLES, start, count)


luz_dir = Path(__file__).resolve().parent / "objetos" / "luz"
luz_batches = load_obj_and_texture(
    luz_dir / "luz.obj", {None: luz_dir / "luz.png"})[2]

def desenha_luz(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):

    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)

    #### define parametros de iluminacao do modelo
    ka = 1 # coeficiente de reflexao ambiente do modelo
    kd = 1 # coeficiente de reflexao difusa do modelo
    
    
    loc_ka = glGetUniformLocation(program, "ka") # recuperando localizacao da variavel ka na GPU
    glUniform1f(loc_ka, ka) ### envia ka pra gpu
    
    loc_kd = glGetUniformLocation(program, "kd") # recuperando localizacao da variavel kd na GPU
    glUniform1f(loc_kd, kd) ### envia kd pra gpu    


    if especular:
        
        ks = 0 # coeficiente de reflexao especular do modelo
        ns = 1000.0 # expoente de reflexao especular
        
        loc_ks = glGetUniformLocation(program, "ks") # recuperando localizacao da variavel ks na GPU
        glUniform1f(loc_ks, ks) ### envia ns pra gpu        
        
        loc_ns = glGetUniformLocation(program, "ns") # recuperando localizacao da variavel ns na GPU
        glUniform1f(loc_ns, ns) ### envia ns pra gpu            
    
    loc_light_pos = glGetUniformLocation(program, "lightPos") # recuperando localizacao da variavel lightPos na GPU
    glUniform3f(loc_light_pos, t_x, t_y, t_z) ### posicao da fonte de luz
           
    for start, count, texture_id in luz_batches:
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glDrawArrays(GL_TRIANGLES, start, count)

buffer_VBO = glGenBuffers(3) ### Novo

vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
vertices['position'] = vertices_list


# Upload data
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
stride = vertices.strides[0]
offset = ctypes.c_void_p(0)
loc_vertices = glGetAttribLocation(program, "position")
glEnableVertexAttribArray(loc_vertices)
glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

textures = np.zeros(len(textures_coord_list), [("position", np.float32, 2)]) # duas coordenadas
textures['position'] = textures_coord_list


# Upload data
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[1])
glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
stride = textures.strides[0]
offset = ctypes.c_void_p(0)
loc_texture_coord = glGetAttribLocation(program, "texture_coord")

glEnableVertexAttribArray(loc_texture_coord)
glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)

normals = np.zeros(len(normals_list), [("position", np.float32, 3)]) # três coordenadas
normals['position'] = normals_list


# Upload coordenadas normals de cada vertice
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[2])
glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
stride = normals.strides[0]
offset = ctypes.c_void_p(0)
loc_normals_coord = glGetAttribLocation(program, "normals")
glEnableVertexAttribArray(loc_normals_coord)
glVertexAttribPointer(loc_normals_coord, 3, GL_FLOAT, False, stride, offset)
cameraPos   = glm.vec3(0.0,  0.0,  15.0);
cameraFront = glm.vec3(0.0,  0.0, -1.0);
cameraUp    = glm.vec3(0.0,  1.0,  0.0);

firstMouse = True
yaw   = -90.0	# yaw is initialized to -90.0 degrees since a yaw of 0.0 results in a direction vector pointing to the right so we initially rotate a bit to the left.
pitch =  0.0
lastX =  largura / 2.0
lastY =  altura / 2.0
fov   =  45.0

# timing
deltaTime = 0.0	# time between current frame and last frame
lastFrame = 0.0


firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  largura/2
lastY =  altura/2


def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode
    global ns_inc, ka, ks, kd

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    
    cameraSpeed = 50 * deltaTime
    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += cameraSpeed * cameraFront
    
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= cameraSpeed * cameraFront
    
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed

    if key == glfw.KEY_P and action == glfw.PRESS:
        polygonal_mode = not polygonal_mode

    if key == 85 and (action==1 or action==2): # tecla U - desliga/liga iluminacao ambiente 
        if ka == 0: ka=0.3
        else: ka=0

    if key == 73 and (action==1 or action==2): # tecla I - desliga/liga reflexao difusa
        if kd == 0: kd=0.5
        else: kd=0
        

def framebuffer_size_callback(window, largura, altura):

    # make sure the viewport matches the new window dimensions note that width and 
    # height will be significantly larger than specified on retina displays.
    glViewport(0, 0, largura, altura)

# glfw: whenever the mouse moves, this callback is called
# -------------------------------------------------------
def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch
   
    if (firstMouse):

        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos # reversed since y-coordinates go from bottom to top
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1 # change this value to your liking
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # make sure that when pitch is out of bounds, screen doesn't get flipped
    if (pitch > 89.0):
        pitch = 89.0
    if (pitch < -89.0):
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)

# glfw: whenever the mouse scroll wheel scrolls, this callback is called
# ----------------------------------------------------------------------
def scroll_callback(window, xoffset, yoffset):
    global fov

    fov -= yoffset
    if (fov < 1.0):
        fov = 1.0
    if (fov > 45.0):
        fov = 45.0
    
glfw.set_key_callback(window,key_event)
glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
glfw.set_cursor_pos_callback(window, mouse_callback)
glfw.set_scroll_callback(window, scroll_callback)

# tell GLFW to capture our mouse
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    
    angle = math.radians(angle)
    
    matrix_transform = glm.mat4(1.0) # instanciando uma matriz identidade
       
    # aplicando translacao (terceira operação a ser executada)
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))    
    
    # aplicando rotacao (segunda operação a ser executada)
    if angle!=0:
        matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))
    
    # aplicando escala (primeira operação a ser executada)
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))
    
    matrix_transform = np.array(matrix_transform)
    
    return matrix_transform

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
    mat_view = np.array(mat_view)
    return mat_view

def projection():
    global altura, largura
    # perspective parameters: fovy, aspect, near, far
    mat_projection = glm.perspective(glm.radians(fov), largura/altura, 0.1, 100.0)

    
    mat_projection = np.array(mat_projection)    
    return mat_projection

glfw.show_window(window)

glEnable(GL_DEPTH_TEST) ### importante para 3D
polygonal_mode = False 


ang = 0.1
ns_inc = 32


while not glfw.window_should_close(window):

    currentFrame = glfw.get_time()
    deltaTime = currentFrame - lastFrame
    lastFrame = currentFrame

    glfw.poll_events() 
       
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(0.2, 0.2, 0.2, 1.0)
    
    if polygonal_mode:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

    
    desenha_witch(0.0, 0, 1, 0, 0, 0, 0, 1, 1, 1)

    if especular: ang += 0.001
    desenha_luz(0, 0, 0, 4, math.cos(ang)*0.5, math.sin(ang)*0.5, 3.0, 0.1, 0.1, 0.1)
    
    mat_view = view()
    loc_view = glGetUniformLocation(program, "view")
    glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

    mat_projection = projection()
    loc_projection = glGetUniformLocation(program, "projection")
    glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    

    if especular:
        # atualizando a posicao da camera/observador na GPU para calculo da reflexao especular
        loc_view_pos = glGetUniformLocation(program, "viewPos") # recuperando localizacao da variavel viewPos na GPU (ESSA VARIAVEL ESTÁ NO SHADER DE FRAGMENTOS)
        glUniform3f(loc_view_pos, cameraPos[0], cameraPos[1], cameraPos[2]) ### posicao da camera/observador (x,y,z)
    
    glfw.swap_buffers(window)

glfw.terminate()
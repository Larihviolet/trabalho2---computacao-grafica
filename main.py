import glfw
from OpenGL.GL import *
import numpy as np
import glm

from tower import Tower
from tower_interior import TowerInterior
from oak_trees import OakTrees
from skybox import Skybox
from ground import Ground
from graveyard import Graveyard
from camera_bounds import CameraBounds
from pathlib import Path

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

altura = 700
largura = 700

window = glfw.create_window(largura, altura, "Programa", None, None)

if (window == None):
    print("Failed to create GLFW window")
    glfwTerminate()
    
glfw.make_context_current(window)



root = Path(__file__).resolve().parent
skybox = Skybox(root / "imagens" / "Skybox.png")
ground = Ground(size=200.0, height=-2.0,
                texture_path=root / "grass" / "2K" / "Poliigon_GrassPatchyGround_4585_BaseColor.jpg",
                tile_size=4.0)
tower = Tower(height=16.0, ground_height=-2.0)
interior = TowerInterior(floor_height=-2.0)
trees = OakTrees(ground_height=-2.0)
graveyard = Graveyard(ground_height=-2.0)
camera_bounds = CameraBounds(ground.size, ground.height, max_height=60.0)

# Posição, direção de observação e eixo vertical da câmera.
cameraPos   = glm.vec3(0.0, 5.0, 3.0)
cameraFront = glm.vec3(0.0, 0.0, -1.0)
cameraUp    = glm.vec3(0.0, 1.0, 0.0)

firstMouse = True
yaw   = -90.0  # O ângulo horizontal inicial aponta para o eixo Z negativo.
pitch =  0.0
lastX =  largura / 2.0
lastY =  altura / 2.0
fov   =  45.0

# Controle do tempo entre quadros.
deltaTime = 0.0  # Intervalo entre o quadro atual e o anterior.
lastFrame = 0.0


firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  largura/2
lastY =  altura/2


def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if key == glfw.KEY_E and action == glfw.PRESS:
        interior.toggle_wizard_size()
    
    cameraSpeed = 200 * deltaTime
    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += cameraSpeed * cameraFront
    
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= cameraSpeed * cameraFront
    
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
    cameraPos = camera_bounds.constrain(cameraPos)
        

def framebuffer_size_callback(window, width, height):
    global largura, altura

    # Ajusta a área de renderização e a proporção à resolução da janela.
    glViewport(0, 0, width, height)
    largura = max(width, 1)
    altura = max(height, 1)

# O GLFW chama esta função sempre que o mouse se move.
# -------------------------------------------------------
def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch
   
    if (firstMouse):

        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos  # Inverte o eixo vertical da janela para controlar a inclinação.
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1  # Sensibilidade da rotação da câmera ao movimento do mouse.
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # Limita a inclinação para impedir que a câmera vire de cabeça para baixo.
    if (pitch > 89.0):
        pitch = 89.0
    if (pitch < -89.0):
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)

# O GLFW chama esta função quando a roda do mouse é acionada.
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

# Captura o cursor para controlar a direção da câmera.
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
    mat_view = np.array(mat_view)
    return mat_view

def projection():
    global altura, largura
    # Parâmetros: campo de visão vertical, proporção, plano próximo e plano distante.
    mat_projection = glm.perspective(glm.radians(fov), largura/altura, 0.1, 100.0)


    # Exemplos para estudar os efeitos da projeção perspectiva.
    # Testar:
    #mat_projection = glm.perspective(glm.radians(45.0), largura/altura, 0.1, 40.0)
    #mat_projection = glm.perspective(glm.radians(45.0), largura/altura, 40, 60.0)
    #mat_projection = glm.perspective(glm.radians(45.0), largura/altura, 0.1, 100.0) #Original
    # Campo de visão menor amplia os objetos; campo maior mostra mais do cenário.
    #mat_projection = glm.perspective(glm.radians(10.0), largura/altura, 0.1, 100.0)
    #mat_projection = glm.perspective(glm.radians(90.0), largura/altura, 0.1, 100.0)


    
    mat_projection = np.array(mat_projection)    
    return mat_projection

glfw.show_window(window)

glEnable(GL_DEPTH_TEST) ### importante para 3D
   
while not glfw.window_should_close(window):

    currentFrame = glfw.get_time()
    deltaTime = currentFrame - lastFrame
    lastFrame = currentFrame

    glfw.poll_events() 
    cameraPos = camera_bounds.constrain(cameraPos)
    interior.update(deltaTime)
    graveyard.update(deltaTime)
       
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(1.0, 1.0, 1.0, 1.0)
    
    mat_view = view()
    mat_projection = projection()
    tower.draw(mat_view, mat_projection)
    interior.draw(mat_view, mat_projection)
    trees.draw(mat_view, mat_projection)
    graveyard.draw(mat_view, mat_projection)
    ground.draw(mat_view, mat_projection)
    skybox.draw(mat_view, mat_projection)
    
    glfw.swap_buffers(window)

tower.close()
interior.close()
trees.close()
graveyard.close()
skybox.close()
ground.close()
glfw.terminate()

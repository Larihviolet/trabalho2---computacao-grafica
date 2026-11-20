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
from material import Material

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
tower_ground = Ground(size=11.8, height=-1.99, center=(0.0, -30.0),
                      texture_path=root / "cobblestone" / "StoneBricksSplitface001_COL_2K.jpg",
                      tile_size=4.0, shape="circle")
tower = Tower(height=16.0, ground_height=-2.0)
interior = TowerInterior(floor_height=-2.0)
trees = OakTrees(ground_height=-2.0)
graveyard = Graveyard(ground_height=-2.0)
camera_bounds = CameraBounds(ground.size, ground.height, max_height=60.0)

# Materiais por objeto: ka, kd e ks controlam reflexões; ns controla o brilho.
material_profiles = {
    "tower": Material(0.68, 0.24, 40.0, ambient=0.70),
    "circle": Material(0.82, 0.10, 18.0, ambient=0.62),
    "witch": Material(0.76, 0.22, 36.0, ambient=0.65),
    "wizard": Material(0.78, 0.18, 30.0, ambient=0.68),
    "trees": Material(0.86, 0.06, 12.0, ambient=0.72),
    "stones": Material(0.72, 0.14, 24.0, ambient=0.65),
    "angel": Material(0.74, 0.30, 56.0, ambient=0.70),
    "ground": Material(0.90, 0.03, 10.0, ambient=0.82),
    "tower_ground": Material(0.76, 0.16, 28.0, ambient=0.66),
}
tower.material = material_profiles["tower"]
interior.circle.material = material_profiles["circle"]
interior.witch.material = material_profiles["witch"]
interior.wizard.material = material_profiles["wizard"]
trees.asset.material = material_profiles["trees"]
trees.materials = [
    Material(0.84 + 0.01 * (index % 3), 0.05 + 0.01 * (index % 2),
             12.0 + 2.0 * (index % 3), ambient=0.68 + 0.02 * (index % 3))
    for index in range(len(trees.models))
]
graveyard.stone.material = material_profiles["stones"]
graveyard.stone_materials = [
    Material(0.70 + 0.02 * (index % 3), 0.12 + 0.02 * (index % 2),
             20.0 + 4.0 * (index % 3), ambient=0.62 + 0.02 * (index % 3))
    for index in range(len(graveyard.stone_models))
]
graveyard.angel.material = material_profiles["angel"]
ground.material = material_profiles["ground"]
tower_ground.material = material_profiles["tower_ground"]

# Holofote fixo acima da torre, apontado para o chão.
spotlight_max_height = 10.0
spotlight_position = (0.0, spotlight_max_height, -30.0)
spotlight_direction = (0.0, -1.0, 0.0)
spotlight_color = (0.78, 0.86, 1.0)
spotlight_inner_cutoff = float(np.cos(np.radians(12.0)))
spotlight_outer_cutoff = float(np.cos(np.radians(20.0)))
sun_direction = (0.35, 0.85, 0.40)
sun_color = (1.0, 0.92, 0.78)
sun_intensity =0.10 #Intensidade da luz do sol (0.0 a 1.0). 
sun_intensity_step = 0.05
diffuse_enabled = True
specular_enabled = True
ambient_enabled = True
spotlight_enabled = True
demon_light_enabled = True
interior_lighting_step = 0

# Volume interno da torre em coordenadas de mundo (centro XZ e limites Y).
sun_exclusion_center = (0.0, -30.0)
sun_exclusion_radius = 3.5
sun_exclusion_min_height = -2.0
sun_exclusion_max_height = 14.0
# Luz vermelha do círculo: curta e confinada ao volume interno da torre.
demon_light_position = (
    interior.circle_pivot[0],
    interior.circle_pivot[1] + 0.35,
    interior.circle_pivot[2],
)
demon_light_color = (1.0, 0.02, 0.01)
demon_light_range = 16.0


def configure_lighting(shader):
    program = shader.getProgram()
    previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
    try:
        glUseProgram(program)
        glUniform3f(glGetUniformLocation(program, "lightPosition"), *spotlight_position)
        glUniform3f(glGetUniformLocation(program, "lightDirection"), *spotlight_direction)
        glUniform3f(glGetUniformLocation(program, "lightColor"), *spotlight_color)
        glUniform3f(glGetUniformLocation(program, "angelLightPosition"),
                    *graveyard.light_position)
        glUniform3f(glGetUniformLocation(program, "angelLightDirection"),
                    *graveyard.light_direction)
        glUniform3f(glGetUniformLocation(program, "angelLightColor"), 0.25, 0.75, 1.0)
        glUniform1f(glGetUniformLocation(program, "angelInnerCutoff"),
                    float(np.cos(np.radians(18.0))))
        glUniform1f(glGetUniformLocation(program, "angelOuterCutoff"),
                    float(np.cos(np.radians(28.0))))
        glUniform1f(glGetUniformLocation(program, "innerCutoff"), spotlight_inner_cutoff)
        glUniform1f(glGetUniformLocation(program, "outerCutoff"), spotlight_outer_cutoff)
        glUniform3f(glGetUniformLocation(program, "sunDirection"), *sun_direction)
        glUniform3f(glGetUniformLocation(program, "sunColor"), *sun_color)
        glUniform1f(glGetUniformLocation(program, "sunIntensity"), sun_intensity)
        glUniform2f(glGetUniformLocation(program, "sunExclusionCenter"),
                    *sun_exclusion_center)
        glUniform1f(glGetUniformLocation(program, "sunExclusionRadius"),
                    sun_exclusion_radius)
        glUniform1f(glGetUniformLocation(program, "sunExclusionMinHeight"),
                    sun_exclusion_min_height)
        glUniform1f(glGetUniformLocation(program, "sunExclusionMaxHeight"),
                    sun_exclusion_max_height)
        glUniform3f(glGetUniformLocation(program, "demonLightPosition"),
                    *demon_light_position)
        glUniform3f(glGetUniformLocation(program, "demonLightColor"),
                    *demon_light_color)
        glUniform1f(glGetUniformLocation(program, "demonLightRange"),
                    demon_light_range)
    finally:
        glUseProgram(previous_program)


scene_shaders = [tower.shader]
scene_shaders.extend(obj.shader for obj in interior.objects)
scene_shaders.extend((trees.asset.shader, graveyard.stone.shader, graveyard.angel.shader))
scene_shaders.extend((ground.shader, tower_ground.shader))
for scene_shader in scene_shaders:
    configure_lighting(scene_shader)

scene_uniforms = []
for shader in scene_shaders:
    program = shader.getProgram()
    scene_uniforms.append((
        program,
        glGetUniformLocation(program, "viewPos"),
        glGetUniformLocation(program, "diffuseEnabled"),
        glGetUniformLocation(program, "specularEnabled"),
        glGetUniformLocation(program, "ambientEnabled"),
        glGetUniformLocation(program, "spotlightEnabled"),
        glGetUniformLocation(program, "demonLightEnabled"),
        glGetUniformLocation(program, "sunIntensity"),
        glGetUniformLocation(program, "angelLightPosition"),
        glGetUniformLocation(program, "angelLightDirection"),
    ))

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
wireframe_mode = False


firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  largura/2
lastY =  altura/2


def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp, wireframe_mode
    global diffuse_enabled, specular_enabled, ambient_enabled
    global spotlight_enabled, demon_light_enabled, interior_lighting_step
    global sun_intensity

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if key == glfw.KEY_M and action == glfw.PRESS:
        graveyard.toggle_angel_movement()
    if key == glfw.KEY_F and action == glfw.PRESS:
        diffuse_enabled = not diffuse_enabled
        state = "ativada" if diffuse_enabled else "desativada"
        print(f"Iluminacao difusa {state} (F)")
    if key == glfw.KEY_G and action == glfw.PRESS:
        specular_enabled = not specular_enabled
        state = "ativada" if specular_enabled else "desativada"
        print(f"Iluminacao especular {state} (G)")
    # H alterna só a contribuição ambiente, sem desligar as outras luzes.
    if key == glfw.KEY_H and action == glfw.PRESS:
        ambient_enabled = not ambient_enabled
        state = "ativada" if ambient_enabled else "desativada"
        print(f"Iluminacao ambiente {state} (H)")
    if key == glfw.KEY_L and action == glfw.PRESS:
        interior_lighting_step = (interior_lighting_step + 1) % 4
        spotlight_enabled = interior_lighting_step in (0, 3)
        demon_light_enabled = interior_lighting_step in (0, 1)
        states = (
            "todas as luzes internas ativadas",
            "somente a luz vermelha do demoncircle ativada",
            "ambos os focos internos desativados",
            "somente o holofote branco da torre ativado",
        )
        print(f"{states[interior_lighting_step]} (L)")
    if key == glfw.KEY_PAGE_UP and action in (glfw.PRESS, glfw.REPEAT):
        previous_intensity = sun_intensity
        sun_intensity = min(1.0, sun_intensity + sun_intensity_step)
        if sun_intensity != previous_intensity:
            print(f"Intensidade do sol: {sun_intensity:.2f} (Page Up)")
    if key == glfw.KEY_PAGE_DOWN and action in (glfw.PRESS, glfw.REPEAT):
        previous_intensity = sun_intensity
        sun_intensity = max(0.0, sun_intensity - sun_intensity_step)
        if sun_intensity != previous_intensity:
            print(f"Intensidade do sol: {sun_intensity:.2f} (Page Down)")
    
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

    previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
    try:
        for (program, view_location, diffuse_location, specular_location,
             ambient_location, spotlight_location, demon_location,
             sun_intensity_location, angel_position_location,
             angel_direction_location) in scene_uniforms:
            glUseProgram(program)
            glUniform3f(view_location, cameraPos.x, cameraPos.y, cameraPos.z)
            glUniform1i(diffuse_location, int(diffuse_enabled))
            glUniform1i(specular_location, int(specular_enabled))
            glUniform1i(ambient_location, int(ambient_enabled))
            glUniform1i(spotlight_location, int(spotlight_enabled))
            glUniform1i(demon_location, int(demon_light_enabled))
            glUniform1f(sun_intensity_location, sun_intensity)
            glUniform3f(angel_position_location, *graveyard.light_position)
            glUniform3f(angel_direction_location, *graveyard.light_direction)
    finally:
        glUseProgram(previous_program)
    
    mat_view = view()
    mat_projection = projection()
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe_mode else GL_FILL)
    ground.draw(mat_view, mat_projection)
    tower_ground.draw(mat_view, mat_projection)
    tower.draw(mat_view, mat_projection)
    interior.draw(mat_view, mat_projection)
    trees.draw(mat_view, mat_projection)
    graveyard.draw(mat_view, mat_projection)
    skybox.draw(mat_view, mat_projection)
    
    glfw.swap_buffers(window)

tower.close()
interior.close()
trees.close()
graveyard.close()
skybox.close()
ground.close()
tower_ground.close()
glfw.terminate()

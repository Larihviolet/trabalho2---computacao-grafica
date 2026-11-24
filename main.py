
from pathlib import Path

import glfw
import glm
import numpy as np
from OpenGL.GL import *

from tower import Tower
from tower_interior import TowerInterior
from oak_trees import OakTrees
from skybox import Skybox
from ground import Ground
from graveyard import Graveyard
from camera_bounds import CameraBounds
from material import Material
from light_marker import LightMarker
from fence import Fence

LIGHTING_EXTERIOR = 0
LIGHTING_INTERIOR = 1
LIGHTING_MIXED = 2

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

window_height = 1400
window_width = 1400

window = glfw.create_window(window_width, window_height, "Programa", None, None)

if (window == None):
    print("Failed to create GLFW window")
    glfwTerminate()
    
glfw.make_context_current(window)


root = Path(__file__).resolve().parent
skybox = Skybox(root / "imagens" / "Skybox.png")
ground = Ground(size=200.0, height=-2.0,
                texture_path=(root / "grass" / "2K" /
                              "Poliigon_GrassPatchyGround_4585_BaseColor.jpg"),
                tile_size=4.0)
tower_ground = Ground(size=11.8, height=-1.99, center=(0.0, -30.0),
                      texture_path=(root / "cobblestone" /
                                    "StoneBricksSplitface001_COL_2K.jpg"),
                      tile_size=4.0, shape="circle")
tower = Tower(height=16.0, ground_height=-2.0)
fence = Fence(ground_height=-2.0, front_z=-17.5)
interior = TowerInterior(floor_height=-2.0)
trees = OakTrees(ground_height=-2.0)
graveyard = Graveyard(ground_height=-2.0)
camera_bounds = CameraBounds(ground.size, ground.height, max_height=60.0)

# Materiais por objeto: kd e ks controlam reflexões difusa e especular e ns controla o brilho.
material_profiles = {
    "tower": Material(0.68, 0.24, 12.0),
    "circle": Material(0.82, 0.40, 18.0),
    "witch": Material(0.76, 0.22, 36.0),
    "wizard": Material(0.80, 0.45, 50.0),
    "trees": Material(0.86, 0.06, 12.0),
    "stones": Material(0.75, 0.20, 18.0),
    "angel": Material(0.74, 0.35, 56.0),
    "ground": Material(0.90, 0.03, 10.0),
    "tower_ground": Material(0.76, 0.16, 28.0),
    "fence": Material(0.72, 0.30, 36.0),
}
tower.material = material_profiles["tower"]
interior.circle.material = material_profiles["circle"]
interior.witch.material = material_profiles["witch"]
interior.wizard.material = material_profiles["wizard"]
trees.asset.material = material_profiles["trees"]
trees.materials = [
    Material(0.84 + 0.01 * (index % 3), 0.05 + 0.01 * (index % 2),
             12.0 + 2.0 * (index % 3))
    for index in range(len(trees.models))
]
graveyard.stone.material = material_profiles["stones"]
graveyard.stone_materials = [
    Material(0.70 + 0.02 * (index % 3), 0.12 + 0.02 * (index % 2),
             20.0 + 4.0 * (index % 3))
    for index in range(len(graveyard.stone_models))
]
graveyard.angel.material = material_profiles["angel"]
ground.material = material_profiles["ground"]
tower_ground.material = material_profiles["tower_ground"]
fence.material = material_profiles["fence"]

# Luzes da cena: holofote da torre, luz do sol, luz vermelha do círculo ritual e luz da estátua.
spotlight_max_height = 10.0
spotlight_position = (0.0, spotlight_max_height, -30.0)
spotlight_direction = (0.0, -1.0, 0.0)
spotlight_color = (0.78, 0.86, 1.0)
spotlight_inner_cutoff = float(np.cos(np.radians(12.0)))
spotlight_outer_cutoff = float(np.cos(np.radians(20.0)))
# Luz do sol simulada como uma fonte direcional distante, com intensidade ajustável.
sun_direction = (0.35, 0.85, 0.40)
sun_color = (1.0, 0.92, 0.78)
sun_intensity =0.10 #Intensidade da luz do sol (0.0 a 1.0). 
sun_intensity_step = 0.05
interior_ambient_intensity = 0.15
exterior_ambient_intensity = 0.15
diffuse_enabled = True
specular_enabled = True
ambient_enabled = True
spotlight_enabled = True 
demon_light_enabled = True
interior_lighting_step = 0

# Volume interno aproximado da torre em coordenadas de mundo.
tower_volume_center = (0.0, -30.0)
tower_volume_radius = 3.5
tower_volume_min_height = -2.0
tower_volume_max_height = 14.0
# Luz vermelha do círculo: curta e confinada ao volume interno da torre.
demon_light_position = (
    interior.circle_pivot[0],
    interior.circle_pivot[1] + 0.35,
    interior.circle_pivot[2],
)
demon_light_color = (1.0, 0.02, 0.01)
demon_light_range = 20.0
light_marker = LightMarker(spotlight_position, spotlight_color)


def configure_lighting(shader, lighting_zone):
    #Define uniformes de iluminação estáticos na cena.

    program = shader.get_program()
    previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
    try:
        glUseProgram(program)
        glUniform3f(glGetUniformLocation(program, "lightPosition"), *spotlight_position)
        glUniform3f(
            glGetUniformLocation(program, "lightDirection"),
            *spotlight_direction)
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
        glUniform1f(
            glGetUniformLocation(program, "innerCutoff"),
            spotlight_inner_cutoff)
        glUniform1f(
            glGetUniformLocation(program, "outerCutoff"),
            spotlight_outer_cutoff)
        glUniform3f(glGetUniformLocation(program, "sunDirection"), *sun_direction)
        glUniform3f(glGetUniformLocation(program, "sunColor"), *sun_color)
        glUniform1f(glGetUniformLocation(program, "sunIntensity"), sun_intensity)
        glUniform2f(glGetUniformLocation(program, "towerVolumeCenter"),
                    *tower_volume_center)
        glUniform1f(glGetUniformLocation(program, "towerVolumeRadius"),
                    tower_volume_radius)
        glUniform1f(glGetUniformLocation(program, "towerVolumeMinHeight"),
                    tower_volume_min_height)
        glUniform1f(glGetUniformLocation(program, "towerVolumeMaxHeight"),
                    tower_volume_max_height)
        glUniform1f(glGetUniformLocation(program, "interiorAmbientIntensity"),
                    interior_ambient_intensity)
        glUniform1f(glGetUniformLocation(program, "exteriorAmbientIntensity"),
                    exterior_ambient_intensity)
        glUniform1i(glGetUniformLocation(program, "lightingZone"), lighting_zone)
        glUniform3f(glGetUniformLocation(program, "demonLightPosition"),
                    *demon_light_position)
        glUniform3f(glGetUniformLocation(program, "demonLightColor"),
                    *demon_light_color)
        glUniform1f(glGetUniformLocation(program, "demonLightRange"),
                    demon_light_range)
    finally:
        glUseProgram(previous_program)


scene_shaders = [(tower.shader, LIGHTING_MIXED)]
scene_shaders.extend((obj.shader, LIGHTING_INTERIOR) for obj in interior.objects)
scene_shaders.extend(
    (shader, LIGHTING_EXTERIOR)
    for shader in (trees.asset.shader, graveyard.stone.shader, graveyard.angel.shader,
                   ground.shader, tower_ground.shader, fence.shader)
)
for scene_shader, lighting_zone in scene_shaders:
    configure_lighting(scene_shader, lighting_zone)

scene_uniforms = []
scene_control_uniforms = []
for shader, _ in scene_shaders:
    program = shader.get_program()
    scene_uniforms.append((
        program,
        glGetUniformLocation(program, "viewPos"),
        glGetUniformLocation(program, "angelLightPosition"),
        glGetUniformLocation(program, "angelLightDirection"),
    ))
    scene_control_uniforms.append((
        program,
        glGetUniformLocation(program, "diffuseEnabled"),
        glGetUniformLocation(program, "specularEnabled"),
        glGetUniformLocation(program, "ambientEnabled"),
        glGetUniformLocation(program, "spotlightEnabled"),
        glGetUniformLocation(program, "demonLightEnabled"),
        glGetUniformLocation(program, "sunIntensity"),
    ))


def update_scene_controls():
    #Envia toggles e intensidade de luz aos programas da cena.

    #Os valores são estáticos entre eventos de teclado.
    previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
    try:
        for (program, diffuse_location, specular_location, ambient_location,
             spotlight_location, demon_location,
             sun_location) in scene_control_uniforms:
            glUseProgram(program)
            glUniform1i(diffuse_location, int(diffuse_enabled))
            glUniform1i(specular_location, int(specular_enabled))
            glUniform1i(ambient_location, int(ambient_enabled))
            glUniform1i(spotlight_location, int(spotlight_enabled))
            glUniform1i(demon_location, int(demon_light_enabled))
            glUniform1f(sun_location, sun_intensity)
    finally:
        glUseProgram(previous_program)

# Posição, direção de observação e eixo vertical da câmera.
camera_position = glm.vec3(0.0, 5.0, 3.0)
camera_front = glm.vec3(0.0, 0.0, -1.0)
camera_up = glm.vec3(0.0, 1.0, 0.0)

first_mouse = True
yaw = -90.0  
last_x = window_width / 2.0
last_y = window_height / 2.0
fov = 45.0

# Controle do tempo entre quadros.
delta_time = 0.0  # Intervalo entre o quadro atual e o anterior.
last_frame = 0.0


def key_event(window, key, scancode, action, mods):
    #Processa teclas da câmera, luzes e janela.
    global camera_position
    global diffuse_enabled, specular_enabled, ambient_enabled
    global spotlight_enabled, demon_light_enabled, interior_lighting_step
    global sun_intensity
    lighting_controls_changed = False

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if key == glfw.KEY_M and action == glfw.PRESS:
        graveyard.toggle_angel_movement()
    if key == glfw.KEY_F and action == glfw.PRESS:
        diffuse_enabled = not diffuse_enabled
        lighting_controls_changed = True
        state = "ativada" if diffuse_enabled else "desativada"
        print(f"Iluminacao difusa {state} (F)")
    if key == glfw.KEY_G and action == glfw.PRESS:
        specular_enabled = not specular_enabled
        lighting_controls_changed = True
        state = "ativada" if specular_enabled else "desativada"
        print(f"Iluminacao especular {state} (G)")
    # H alterna sÃ³ a contribuiÃ§Ã£o ambiente, sem desligar as outras luzes.
    if key == glfw.KEY_H and action == glfw.PRESS:
        ambient_enabled = not ambient_enabled
        lighting_controls_changed = True
        state = "ativada" if ambient_enabled else "desativada"
        print(f"Iluminacao ambiente {state} (H)")
    if key in (glfw.KEY_1, glfw.KEY_2, glfw.KEY_3, glfw.KEY_4) and action == glfw.PRESS:
        interior_lighting_step = key - glfw.KEY_1
        spotlight_enabled = interior_lighting_step in (0, 2)
        demon_light_enabled = interior_lighting_step in (0, 1)
        lighting_controls_changed = True
        states = (
            "todas as luzes internas ativadas",
            "somente a luz vermelha do demoncircle ativada",
            "somente o holofote branco da torre ativado",
            "ambos os focos internos desativados",
        )
        print(f"{states[interior_lighting_step]} ({interior_lighting_step + 1})")
    if key == glfw.KEY_PAGE_UP and action in (glfw.PRESS, glfw.REPEAT):
        previous_intensity = sun_intensity
        sun_intensity = min(1.0, sun_intensity + sun_intensity_step)
        if sun_intensity != previous_intensity:
            lighting_controls_changed = True
            print(f"Intensidade do sol: {sun_intensity:.2f} (Page Up)")
    if key == glfw.KEY_PAGE_DOWN and action in (glfw.PRESS, glfw.REPEAT):
        previous_intensity = sun_intensity
        sun_intensity = max(0.0, sun_intensity - sun_intensity_step)
        if sun_intensity != previous_intensity:
            lighting_controls_changed = True
            print(f"Intensidade do sol: {sun_intensity:.2f} (Page Down)")
    
    camera_speed = 200 * delta_time
    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_position += camera_speed * camera_front
    
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_position -= camera_speed * camera_front
    
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_right = glm.normalize(glm.cross(camera_front, camera_up))
        camera_position -= camera_right * camera_speed
        
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        camera_right = glm.normalize(glm.cross(camera_front, camera_up))
        camera_position += camera_right * camera_speed
    camera_position = camera_bounds.constrain(camera_position)
    if lighting_controls_changed:
        update_scene_controls()
        

def framebuffer_size_callback(window, width, height):
    #Atualiza viewport e dimensões após redimensionamento. 
    global window_width, window_height

    # Ajusta a área de renderização e a proporção à resolução da janela.
    glViewport(0, 0, width, height)
    window_width = max(width, 1)
    window_height = max(height, 1)

# O GLFW chama esta função sempre que o mouse se move.
def mouse_callback(window, xpos, ypos):
  #Atualiza a direção da câmera conforme o movimento do mouse.

    
    global camera_front, last_x, last_y, first_mouse, yaw, pitch
   
    if first_mouse:

        last_x = xpos
        last_y = ypos
        first_mouse = False

    xoffset = xpos - last_x
    yoffset = last_y - ypos  # Inverte o eixo vertical da janela para controlar a inclinação.
    last_x = xpos
    last_y = ypos

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
    camera_front = glm.normalize(front)

# O GLFW chama esta funÃ§Ã£o quando a roda do mouse Ã© acionada.
# ----------------------------------------------------------------------
def scroll_callback(window, xoffset, yoffset):
    #Ajusta o campo de visão em resposta à roda do mouse.

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
update_scene_controls()

# Captura o cursor para controlar a direção da câmera.
glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def view():
    #Calcula a matriz de visualização da câmera.

    matrix = glm.lookAt(camera_position, camera_position + camera_front, camera_up)
    return np.asarray(matrix, dtype=np.float32)

def projection():
    #Retorna a matriz de projeção em cache para a janela atual.
    global _projection_cache_key, _projection_cache
    cache_key = (fov, window_width, window_height)
    if cache_key != _projection_cache_key:
        # A projeção só muda quando o FOV ou o tamanho da janela muda.
        matrix = glm.perspective(
            glm.radians(fov), window_width / window_height, 0.1, 100.0)
        _projection_cache = np.asarray(matrix, dtype=np.float32)
        _projection_cache_key = cache_key
    return _projection_cache


_projection_cache_key = None
_projection_cache = None

glfw.show_window(window)

glEnable(GL_DEPTH_TEST)
glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

while not glfw.window_should_close(window):

    current_frame = glfw.get_time()
    delta_time = current_frame - last_frame
    last_frame = current_frame

    glfw.poll_events() 
    interior.update(delta_time)
    graveyard.update(delta_time)
       
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(1.0, 1.0, 1.0, 1.0)

    previous_program = int(glGetIntegerv(GL_CURRENT_PROGRAM))
    try:
        for (program, view_location, angel_position_location,
             angel_direction_location) in scene_uniforms:
            glUseProgram(program)
            glUniform3f(
                view_location,
                camera_position.x, camera_position.y, camera_position.z)
            glUniform3f(angel_position_location, *graveyard.light_position)
            glUniform3f(angel_direction_location, *graveyard.light_direction)
    finally:
        glUseProgram(previous_program)
    
    mat_view = view()
    mat_projection = projection()
    ground.draw(mat_view, mat_projection)
    tower_ground.draw(mat_view, mat_projection)
    fence.draw(mat_view, mat_projection)
    tower.draw(mat_view, mat_projection)
    interior.draw(mat_view, mat_projection)
    trees.draw(mat_view, mat_projection)
    graveyard.draw(mat_view, mat_projection)
    skybox.draw(mat_view, mat_projection)
    light_marker.draw(mat_view, mat_projection)
    
    glfw.swap_buffers(window)

tower.close()
interior.close()
trees.close()
graveyard.close()
skybox.close()
ground.close()
tower_ground.close()
fence.close()
light_marker.close()
glfw.terminate()

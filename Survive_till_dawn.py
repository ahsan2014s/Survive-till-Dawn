#!bin/python3

import sys
import time
import math
import random
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
try:
    import numpy as np
except ImportError:
    print("Numpy not found. Install it: pip install numpy")
    sys.exit(1)

# Game State Variables
window_width = 1280; 
window_height = 720; 
last_time = 0.0; 
game_start_time = 0.0; 
player_life = 5; 
game_score = 0; 
bullets_missed = 0; 
is_game_over = False
player_pos = [0.0, 6.0, 0.0]; 
player_rot_y = 0.0; 
player_speed = 15.0; 
player_rot_speed = 100.0
camera_pos = np.array([0.0, 0.0, 0.0]); 
camera_target = np.array([0.0, 0.0, 0.0]); 
camera_mode = 'THIRD_PERSON'
camera_third_person_radius = 10.0; 
camera_third_person_height = 5.0; 
camera_rot_y = 0.0; 
camera_pitch = -30.0
bullets = []; 
enemies = []; 
targeted_enemies_this_sweep = set() 
enemy_count = 5; 
grid_size = 50; 
respawn_delay = 0.35
key_states = {k: False for k in 'wasdcvk'}; 
special_key_states = {key: False for key in [100, 101, 102, 103]}
cheat_mode_active = False; 
auto_gun_follow_active = False
SURVIVAL_TIME_SECONDS = 600 # 10 minutes
time_remaining = SURVIVAL_TIME_SECONDS
player_won = False
LIGHT_DIRECTION = np.array([0.0, 1.0, 0.0], dtype=np.float32)
LIGHT_COLOR = np.array([1.0, 1.0, 1.0], dtype=np.float32)
AMBIENT_COLOR = np.array([0.1, 0.1, 0.1], dtype=np.float32)
SPECULAR_INTENSITY = 0.5
SHININESS = 32.0
MAX_PLAYER_HEALTH = 100.0
player_health = MAX_PLAYER_HEALTH
is_free_camera_active = False
ENEMY_BASE_DAMAGE = 5.0
ENEMY_DAMAGE_SCALING_FACTOR = 0.05 
is_boss_spawned = False
heal_items = []
HEAL_AMOUNT = 30.0
BULLET_DAMAGE = 10

OBSTACLES = [
    {
        'type': 'BOX',
        'pos': np.array([-20.0, 5.0, -15.0]),
        'size': np.array([12.0, 10.0, 15.0]) # Width, Height, Depth
    },
    {
        'type': 'CYLINDER',
        'pos': np.array([15.0, 0.0, 10.0]),
        'radius': 2.0,
        'height': 8.0
    },
    # To add a new tree, copy the entry above and change the 'pos'
    {
        'type': 'CYLINDER',
        'pos': np.array([-10.0, 0.0, 20.0]),
        'radius': 2.5,
        'height': 10.0
    },
]


# --- Utility Functions ---
def get_vector_from_angle(angle_deg):
    """Calculates a 2D direction vector using standard OpenGL conventions."""
    angle_rad = math.radians(angle_deg)
    return -math.sin(angle_rad), -math.cos(angle_rad)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """
    Renders a string at a specified 2D screen coordinate.
    Assumes an orthographic projection is already set up.
    """
    glRasterPos2f(x, y)
    for char in text: 
        glutBitmapCharacter(font, ord(char))

def lerp(v0, v1, t): 
    return v0 * (1.0 - t) + v1 * t

def draw_player():
    glPushMatrix() # begin wrap
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    
    if is_game_over:
        glRotatef(90, 0, 0, 1)
        glTranslatef(0, 0, 0)
        
    glRotatef(player_rot_y, 0, 1, 0)
    quad = gluNewQuadric()

    # BODY
    apply_phong_shading(np.array([0, 0.8, 0.0]), np.array([1, 0, 0]))
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 0.5*2, 0.5*2, 3.0, 20, 20) # top rad, bottom rad, height 
    glPopMatrix()

    # head
    apply_phong_shading(np.array([0.8, 0.6, 0.4]), np.array([0, 1, 0]))
    glPushMatrix()
    glTranslatef(0, 0.7*1.22+1.1, 0)
    glutSolidSphere(0.7*1.22, 20, 20)
    glPopMatrix()

    # arm and gun together
    glPushMatrix()
    glTranslatef(0, 1.2, -.9)
    glRotatef(90, 1, 0, 0)
    
    # Left Arm
    glPushMatrix(); 
    glTranslatef(-0.7, 0, 0); 
    glRotatef(-270, 0, 0, 1)
    glRotatef(-90, 0, 1, 0); 
    apply_phong_shading(np.array([0.8, 0.6, 0.4]), np.array([0, 1, 0])); 
    gluCylinder(quad, .16*1.32, .16*1.32, 1.5, 10, 10); 
    glPopMatrix()

    # Right Arm
    glPushMatrix()
    glTranslatef(0.7, 0, 0)
    glRotatef(-270, 0, 0, 1)
    glRotatef(-90, 0, 1, 0); 
    apply_phong_shading(np.array([0.8, 0.6, 0.4]), np.array([0, 1, 0])); 
    gluCylinder(quad, .16*1.32, .16*1.32, 1.5, 10, 10); 
    glPopMatrix()

    # Gun (Centered)
    glPushMatrix()
    glTranslatef(0, -1.0, 0)
    apply_phong_shading(np.array([0.2, 0.2, 0.2]), np.array([0, 0, 1]))
    glScalef(0.5, 2.0, 0.5)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix() # End of Arms and Gun assembly

    # Legs
    apply_phong_shading(np.array([0, 0, 0.8]), np.array([0, 1, 0]))
    # Left Leg
    glPushMatrix()
    glTranslatef(-0.3, -1.5, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 0.52*1.33, 0.2*1.33, 1.5, 10, 10)
    glPopMatrix()

    # Right Leg
    glPushMatrix()
    glTranslatef(0.3, -1.5, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 0.52*1.33, 0.2*1.33, 1.5, 10, 10)
    glPopMatrix()


    gluDeleteQuadric(quad)
    glPopMatrix() # end wrap


def draw_enemy(enemy):
    if enemy['state'] == 'ALIVE':
        # Arm rotation
        arm_rotation_angle = (time.perf_counter() * 250) % 360

        total_elapsed_time = time.perf_counter() - game_start_time
        scale = 1.0 + 0.1 * math.sin(total_elapsed_time * 5)
        
        glPushMatrix(); 
        glTranslatef(enemy['pos'][0], enemy['pos'][1], enemy['pos'][2])
        
        # Health Bar
        glPushMatrix()
        glTranslatef(0, 2.5, 0)
        cam_angle_to_use = camera_rot_y if is_free_camera_active else player_rot_y
        glRotatef(-cam_angle_to_use, 0, 1, 0)
        bar_width = 1.5; bar_height = 0.15
        current_health_width = bar_width * (max(0, enemy['health']) / enemy['max_health'])
        if current_health_width > 0:
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_QUADS); glVertex3f(-bar_width/2, 0, 0); glVertex3f(-bar_width/2 + current_health_width, 0, 0); glVertex3f(-bar_width/2 + current_health_width, bar_height, 0); glVertex3f(-bar_width/2, bar_height, 0); glEnd()
        if current_health_width < bar_width:
            red_start_x = -bar_width/2 + current_health_width
            glColor3f(0.0, 1.0, 0.0)
            glBegin(GL_QUADS); glVertex3f(red_start_x, 0, 0); glVertex3f(bar_width/2, 0, 0); glVertex3f(bar_width/2, bar_height, 0); glVertex3f(red_start_x, bar_height, 0); glEnd()
        glPopMatrix()

        # Enemy Body
        apply_phong_shading(np.array([1.0, 0.0, 0.0]), LIGHT_DIRECTION, is_shiny=True); 
        glPushMatrix(); 
        glScalef(scale, scale, scale); 
        glutSolidSphere(1.0, 20, 20); 
        glPopMatrix()
        apply_phong_shading(np.array([0.0, 0.0, 0.0]), np.array([0,0,1]), is_shiny=False); 
        glPushMatrix(); 
        glTranslatef(0, 0, 0.8 * scale); 
        glutSolidSphere(0.3, 10, 10); 
        glPopMatrix()

        # SPINNING ARMS AND MELEE WEAPONS
        quad = gluNewQuadric()
        
        # Left Arm
        glPushMatrix()
        glTranslatef(-1.2, 0.5, 0)
        # forward/backward swing
        glRotatef(arm_rotation_angle, 1, 0, 0) 
        apply_phong_shading(np.array([0.8, 0.1, 0.1]), LIGHT_DIRECTION)
        gluCylinder(quad, 0.15, 0.15, 1.0, 10, 10)
        glTranslatef(0, 0, 1.0)
        apply_phong_shading(np.array([0.5, 0.5, 0.5]), LIGHT_DIRECTION, is_shiny=True)
        glScalef(0.2, 0.2, 0.8)
        glutSolidCube(1.0)
        glPopMatrix()

        # Right Arm
        glPushMatrix()
        glTranslatef(1.2, 0.5, 0)
        glRotatef(arm_rotation_angle, 1, 0, 0)
        apply_phong_shading(np.array([0.8, 0.1, 0.1]), LIGHT_DIRECTION)
        gluCylinder(quad, 0.15, 0.15, 1.0, 10, 10)
        glTranslatef(0, 0, 1.0)
        #the melee weapon
        apply_phong_shading(np.array([0.5, 0.5, 0.5]), LIGHT_DIRECTION, is_shiny=True)
        glScalef(0.2, 0.2, 0.8)
        glutSolidCube(1.0)
        glPopMatrix() 
        
        gluDeleteQuadric(quad)
        
        glPopMatrix() # Final pop for the entire enemy


def draw_bullet(bullet):
    glPushMatrix(); 
    glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2]); 
    glColor3f(1.0, 1.0, 0.0); 
    glutSolidCube(0.3); 
    glPopMatrix()



def draw_grid_and_boundaries():
    glPushMatrix();
    ground_normal = np.array([0.0, 1.0, 0.0])
    
    glBegin(GL_QUADS)
    
    # Top-left quadrant (White)
    apply_phong_shading(np.array([1.0, 1.0, 1.0]), ground_normal)
    glVertex3f(-grid_size, 0, grid_size); glVertex3f(0, 0, grid_size); glVertex3f(0, 0, 0); glVertex3f(-grid_size, 0, 0)
    
    # Top-right quadrant (Purple)
    apply_phong_shading(np.array([0.5, 0.2, 0.8]), ground_normal)
    glVertex3f(0, 0, grid_size); glVertex3f(grid_size, 0, grid_size); glVertex3f(grid_size, 0, 0); glVertex3f(0, 0, 0)

    # Bottom-left quadrant (Purple)
    apply_phong_shading(np.array([0.5, 0.2, 0.8]), ground_normal)
    glVertex3f(-grid_size, 0, 0); glVertex3f(0, 0, 0); glVertex3f(0, 0, -grid_size); glVertex3f(-grid_size, 0, -grid_size)

    # Bottom-right quadrant (White)
    apply_phong_shading(np.array([1.0, 1.0, 1.0]), ground_normal)
    glVertex3f(0, 0, 0); glVertex3f(grid_size, 0, 0); glVertex3f(grid_size, 0, -grid_size); glVertex3f(0, 0, -grid_size)
    
    glEnd()

    wall_height = 5
    glColor3f(0.0, 1.0, 0.0); 
    glBegin(GL_QUADS); 
    glVertex3f(-grid_size, 0, grid_size); 
    glVertex3f(grid_size, 0, grid_size); 
    glVertex3f(grid_size, wall_height, grid_size); 
    glVertex3f(-grid_size, wall_height, grid_size); 
    glEnd()
    glColor3f(0.0, 0.0, 1.0); 
    glBegin(GL_QUADS); 
    glVertex3f(-grid_size, 0, -grid_size); 
    glVertex3f(grid_size, 0, -grid_size); 
    glVertex3f(grid_size, wall_height, -grid_size); 
    glVertex3f(-grid_size, wall_height, -grid_size); 
    glEnd()
    glColor3f(0.0, 1.0, 1.0); 
    glBegin(GL_QUADS); 
    glVertex3f(grid_size, 0, -grid_size); 
    glVertex3f(grid_size, 0, grid_size); 
    glVertex3f(grid_size, wall_height, grid_size); 
    glVertex3f(grid_size, wall_height, -grid_size); 
    glEnd()
    glBegin(GL_QUADS); 
    glVertex3f(-grid_size, 0, -grid_size); 
    glVertex3f(-grid_size, 0, grid_size); 
    glVertex3f(-grid_size, wall_height, grid_size); 
    glVertex3f(-grid_size, wall_height, -grid_size); 
    glEnd(); 
    glPopMatrix()


def draw_obstacles():
    """
    Draws all static obstacles defined in the global obstacle list,
    with full Phong shading applied.
    """
    quad = gluNewQuadric() 

    for obs in OBSTACLES:
        glPushMatrix()
        
        glTranslatef(obs['pos'][0], obs['pos'][1], obs['pos'][2])

        if obs['type'] == 'BOX':
            base_color = np.array([0.8, 0.7, 0.5])
            w, h, d = obs['size'][0]/2.0, obs['size'][1], obs['size'][2]/2.0
            
            glBegin(GL_QUADS)
            apply_phong_shading(base_color, [0, 0, 1]); glVertex3f(-w, -h, d); glVertex3f(w, -h, d); glVertex3f(w, h, d); glVertex3f(-w, h, d)
            # Back Face
            apply_phong_shading(base_color, [0, 0, -1]); glVertex3f(-w, -h, -d); glVertex3f(-w, h, -d); glVertex3f(w, h, -d); glVertex3f(w, -h, -d)
            # Top Face
            apply_phong_shading(base_color, [0, 1, 0]); glVertex3f(-w, h, -d); glVertex3f(-w, h, d); glVertex3f(w, h, d); glVertex3f(w, h, -d)
            # Bottom Face
            apply_phong_shading(base_color, [0, -1, 0]); glVertex3f(-w, -h, -d); glVertex3f(w, -h, -d); glVertex3f(w, -h, d); glVertex3f(-w, -h, d)
            # Right Face
            apply_phong_shading(base_color, [1, 0, 0]); glVertex3f(w, -h, -d); glVertex3f(w, h, -d); glVertex3f(w, h, d); glVertex3f(w, -h, d)
            # Left Face
            apply_phong_shading(base_color, [-1, 0, 0]); glVertex3f(-w, -h, -d); glVertex3f(-w, -h, d); glVertex3f(w, h, d); glVertex3f(-w, h, -d)
            glEnd()

            roof_color = np.array([0.6, 0.2, 0.2])
            roof_height = 6.0
            
            p_fr = np.array([w, h, d]); p_fl = np.array([-w, h, d]); p_br = np.array([w, h, -d]); p_bl = np.array([-w, h, -d])
            p_peak = np.array([0, h + roof_height, 0])

            v1 = p_br - p_fr; v2 = p_peak - p_fr
            roof_normal_right = np.cross(v1, v2)
            apply_phong_shading(roof_color, roof_normal_right, is_shiny=True)
            glBegin(GL_QUADS); glVertex3fv(p_fr); glVertex3fv(p_br); glVertex3fv(p_peak); glVertex3fv(p_peak); glEnd()

            v1 = p_fl - p_bl; v2 = p_peak - p_bl
            roof_normal_left = np.cross(v1, v2)
            apply_phong_shading(roof_color, roof_normal_left, is_shiny=True)
            glBegin(GL_QUADS); glVertex3fv(p_bl); glVertex3fv(p_fl); glVertex3fv(p_peak); glVertex3fv(p_peak); glEnd()

            apply_phong_shading(roof_color, [0, 0, 1])
            glBegin(GL_TRIANGLES); glVertex3fv(p_fl); glVertex3fv(p_fr); glVertex3fv(p_peak); glEnd()
            apply_phong_shading(roof_color, [0, 0, -1])
            glBegin(GL_TRIANGLES); glVertex3fv(p_br); glVertex3fv(p_bl); glVertex3fv(p_peak); glEnd()

        elif obs['type'] == 'CYLINDER':
            light_dir_xz = np.array([LIGHT_DIRECTION[0], 0, LIGHT_DIRECTION[2]])
            norm = np.linalg.norm(light_dir_xz)
            trunk_normal = light_dir_xz / norm if norm > 0.001 else np.array([1, 0, 0])
            
            apply_phong_shading(np.array([0.5, 0.35, 0.05]), trunk_normal)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quad, obs['radius'], obs['radius'], obs['height'], 20, 20)
            glPopMatrix()

            canopy_radius = obs['radius'] * 3.5 
            apply_phong_shading(np.array([0.1, 0.5, 0.1]), LIGHT_DIRECTION, is_shiny=True)
            glPushMatrix()
            glTranslatef(0, obs['height'] + canopy_radius - 1, 0) 
            glutSolidSphere(canopy_radius, 30, 30)
            glPopMatrix()

        glPopMatrix()
    
    gluDeleteQuadric(quad) 


def draw_hud():
    glMatrixMode(GL_PROJECTION); 
    glPushMatrix(); 
    glLoadIdentity(); 
    gluOrtho2D(0, window_width, 0, window_height); 
    glMatrixMode(GL_MODELVIEW); 
    glPushMatrix(); 
    glLoadIdentity(); 
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    
    # Text displays for Score and other info
    draw_text(10, window_height - 35, f"Game Score: {game_score}"); 
    draw_text(10, window_height - 50, f"Player Bullet Missed: {bullets_missed}")
    minutes = int(time_remaining) // 60
    seconds = int(time_remaining) % 60
    draw_text(window_width / 2 - 70, window_height - 30, f"Time Remaining: {minutes:02d}:{seconds:02d}")

    # Game Over / Win messages
    message = ""
    if player_won:
        message = "YOU SURVIVED! YOU WIN! (Press 'R' to Restart)"
    elif is_game_over:
        message = "GAME OVER! Press 'R' to Restart."
    if message:
        text_width = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in message)
        draw_text(window_width/2 - text_width/2, window_height/2, message)

    # Status indicators for cheats/camera
    if cheat_mode_active and not (player_won or is_game_over):
        glColor3f(0.0, 1.0, 0.0)
        draw_text(window_width - 150, window_height - 30, "CHEAT MODE ON")
    if is_free_camera_active:
        glColor3f(1.0, 0.8, 0.0)
        draw_text(window_width - 150, 10, "Free Camera (K)")
    
    # --- HEALTH BAR FIX: Using the User's "Segmented Bar" Logic ---
    health_bar_width = 200
    health_bar_height = 15
    health_bar_x = 10
    health_bar_y = window_height - 70

    # 1. Calculate the width of the current (green) health portion.
    #    The 'max(0, ...)' ensures the width doesn't become negative if health drops below zero.
    current_health_width = health_bar_width * (max(0, player_health) / MAX_PLAYER_HEALTH)

    # 2. Draw the GREEN portion of the bar, representing remaining health.
    #    This is drawn from the left edge up to the calculated width.
    if current_health_width > 0:
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(health_bar_x, health_bar_y)
        glVertex2f(health_bar_x + current_health_width, health_bar_y)
        glVertex2f(health_bar_x + current_health_width, health_bar_y - health_bar_height)
        glVertex2f(health_bar_x, health_bar_y - health_bar_height)
        glEnd()

    # 3. Draw the RED portion of the bar, representing lost health.
    #    This is drawn immediately to the right of the green portion.
    if current_health_width < health_bar_width:
        # The starting X position for the red bar is the ending X of the green bar.
        red_bar_start_x = health_bar_x + current_health_width
        
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(red_bar_start_x, health_bar_y)
        glVertex2f(health_bar_x + health_bar_width, health_bar_y) # End at the full bar width
        glVertex2f(health_bar_x + health_bar_width, health_bar_y - health_bar_height)
        glVertex2f(red_bar_start_x, health_bar_y - health_bar_height)
        glEnd()
    
    # Restore matrices
    glMatrixMode(GL_PROJECTION); 
    glPopMatrix(); 
    glMatrixMode(GL_MODELVIEW); 
    glPopMatrix()


def spawn_boss():
    global enemies
    boss = {
        'pos': np.array([0.0, 1.0, 0.0]), 
        'speed': 1.5, 
        'state': 'ALIVE', 
        'death_time': 0,
        'health': 300.0,
        'max_health': 300.0,
        'type': 'BOSS' 
    }
    respawn_enemy(boss)
    enemies.append(boss)

def draw_heal_items():
    for item in heal_items:
        glPushMatrix()
        glTranslatef(item['pos'][0], 1.5, item['pos'][2])
        apply_phong_shading(np.array([0.1, 0.9, 0.1]), LIGHT_DIRECTION, is_shiny=True)
        glutSolidSphere(0.7, 15, 15)
        glPopMatrix()

# game logic 
def fire_bullet():
    if is_game_over: 
        return
    dir_x, dir_z = get_vector_from_angle(player_rot_y); 
    spawn_dist = 2.5
    start_pos = [player_pos[0] + dir_x * spawn_dist, 4.0, player_pos[2] + dir_z * spawn_dist]
    bullets.append(
        {'pos': np.array(start_pos), 
        'vel': np.array([dir_x * 40.0, 0, dir_z * 40.0])})


def respawn_enemy(enemy):
    enemy['max_health'] *= 1.01
    # reset the enemy's current health
    enemy['health'] = enemy['max_health']
    enemy['state'] = 'ALIVE'; 
    enemy['pos'] = np.array([random.uniform(-grid_size + 2, grid_size - 2), 1.0, random.uniform(-grid_size + 2, grid_size - 2)])


def update_camera_smooth(dt):
    global camera_pos, camera_target, camera_rot_y, camera_pitch, camera_third_person_height
    
    if camera_mode == 'THIRD_PERSON':
        angle_to_use = camera_rot_y if is_free_camera_active else player_rot_y
        angle_rad = math.radians(angle_to_use)
        
        # --- CAMERA FIX: Changed '-' to '+' to place camera behind the player ---
        cam_x = player_pos[0] + camera_third_person_radius * math.sin(angle_rad)
        cam_z = player_pos[2] + camera_third_person_radius * math.cos(angle_rad)
        cam_y = player_pos[1] + camera_third_person_height
        
        target_cam_pos = np.array([cam_x, cam_y, cam_z])
        target_look_at = np.array([player_pos[0], player_pos[1], player_pos[2]])   
        
        transition_speed = 7.5 * dt
        camera_pos = lerp(camera_pos, target_cam_pos, transition_speed)
        camera_target = lerp(camera_target, target_look_at, transition_speed)
    else: # FIRST_PERSON
        dir_x, dir_z = get_vector_from_angle(player_rot_y)
        eye_y = player_pos[1] + 1.6
        eye_offset = 1.8
        eye_x = player_pos[0] + dir_x * eye_offset
        eye_z = player_pos[2] + dir_z * eye_offset
        camera_pos = np.array([eye_x, eye_y, eye_z])
        camera_target = np.array([eye_x + dir_x * 5, eye_y, eye_z + dir_z * 5])

    if camera_mode == 'THIRD_PERSON':
        if is_free_camera_active:
            if special_key_states[GLUT_KEY_LEFT]: 
                camera_rot_y -= player_rot_speed * 0.7 * dt
            if special_key_states[GLUT_KEY_RIGHT]: 
                camera_rot_y += player_rot_speed * 0.7 * dt
        
        if special_key_states[GLUT_KEY_UP]: 
            camera_third_person_height = min(40.0, camera_third_person_height + player_rot_speed * 0.5 * dt)
        if special_key_states[GLUT_KEY_DOWN]: 
            camera_third_person_height = max(5.0, camera_third_person_height - player_rot_speed * 0.5 * dt)


def is_position_colliding(x, z, radius):
    """Checks if a given 2D position is inside ANY obstacle in the global list."""
    for obs in OBSTACLES:
        if obs['type'] == 'BOX':
            half_w = obs['size'][0] / 2.0
            half_d = obs['size'][2] / 2.0
            if (obs['pos'][0] - half_w < x + radius and
                obs['pos'][0] + half_w > x - radius and
                obs['pos'][2] - half_d < z + radius and
                obs['pos'][2] + half_d > z - radius):
                return True
        
        elif obs['type'] == 'CYLINDER':
            dist_sq = (x - obs['pos'][0])**2 + (z - obs['pos'][2])**2
            if dist_sq < (obs['radius'] + radius)**2:
                return True

    return False

def is_bullet_colliding(bullet_pos):
    """Checks if a given 3D bullet position is inside ANY obstacle."""
    for obs in OBSTACLES:
        if obs['type'] == 'BOX':
            half_w = obs['size'][0] / 2.0
            half_h = obs['size'][1] / 2.0
            half_d = obs['size'][2] / 2.0
            if (abs(bullet_pos[0] - obs['pos'][0]) < half_w and
                abs(bullet_pos[1] - (obs['pos'][1] + half_h)) < half_h and
                abs(bullet_pos[2] - obs['pos'][2]) < half_d):
                return True 

        elif obs['type'] == 'CYLINDER':
            dist_sq = (bullet_pos[0] - obs['pos'][0])**2 + (bullet_pos[2] - obs['pos'][2])**2
            if dist_sq < obs['radius']**2 and 0 < bullet_pos[1] < obs['height']:
                return True

    return False


def update_player(dt):
    global player_pos, player_rot_y
    if is_game_over: return
    if key_states['a']: 
        player_rot_y += player_rot_speed * dt
    if key_states['d']: 
        player_rot_y -= player_rot_speed * dt
    
    move_dir = 0
    if key_states['w']: 
        move_dir = 1
    if key_states['s']: 
        move_dir = -1
        
    if move_dir != 0:
        dir_x, dir_z = get_vector_from_angle(player_rot_y)
        player_radius = 1.0
        next_pos_x = player_pos[0] + dir_x * player_speed * move_dir * dt
        next_pos_z = player_pos[2] + dir_z * player_speed * move_dir * dt

        if is_position_colliding(next_pos_x, player_pos[2], player_radius):
            next_pos_x = player_pos[0]
        if is_position_colliding(player_pos[0], next_pos_z, player_radius):
            next_pos_z = player_pos[2]
            
        player_pos[0] = next_pos_x
        player_pos[2] = next_pos_z

        player_pos[0] = max(-grid_size+1, min(grid_size-1, player_pos[0]))
        player_pos[2] = max(-grid_size+1, min(grid_size-1, player_pos[2]))


def update_bullets(dt):
    global bullets_missed
    bullets_to_keep = []
    
    for b in bullets:
        b['pos'] += b['vel'] * dt
        is_destroyed = is_bullet_colliding(b['pos'])
        
        if not is_destroyed and (abs(b['pos'][0]) >= grid_size or abs(b['pos'][2]) >= grid_size):
            bullets_missed += 1
            is_destroyed = True

        if not is_destroyed:
            bullets_to_keep.append(b)
            
    bullets[:] = bullets_to_keep


def update_enemies(dt):
    current_time = time.perf_counter() - game_start_time
    for e in enemies:
        if e['state'] == 'ALIVE' and not is_game_over:
            enemy_radius = 1.0
            vec_to_player = np.array([player_pos[0], 0, player_pos[2]]) - np.array([e['pos'][0], 0, e['pos'][2]])
            dist_to_player = np.linalg.norm(vec_to_player)
            
            if dist_to_player > 0.1:
                direction = vec_to_player / dist_to_player
                next_pos_x = e['pos'][0] + direction[0] * e['speed'] * dt
                next_pos_z = e['pos'][2] + direction[2] * e['speed'] * dt
                
                if not is_position_colliding(next_pos_x, next_pos_z, enemy_radius):
                    e['pos'][0] = next_pos_x
                    e['pos'][2] = next_pos_z
                else:
                    if not is_position_colliding(next_pos_x, e['pos'][2], enemy_radius):
                         e['pos'][0] = next_pos_x
                    elif not is_position_colliding(e['pos'][0], next_pos_z, enemy_radius):
                         e['pos'][2] = next_pos_z

        elif e['state'] == 'DEAD':
            if current_time - e['death_time'] > respawn_delay:
                respawn_enemy(e)


def update_cheat_mode(dt):
    global player_rot_y, targeted_enemies_this_sweep
    if not cheat_mode_active or is_game_over:
        if targeted_enemies_this_sweep:
            targeted_enemies_this_sweep.clear() 
        return
    alive_enemies = [e for e in enemies if e['state'] == 'ALIVE']
    if not alive_enemies: 
        return
    if len(targeted_enemies_this_sweep) >= len(alive_enemies):
        targeted_enemies_this_sweep.clear()
    available_targets = [e for e in alive_enemies if id(e) not in targeted_enemies_this_sweep]
    if not available_targets:
        return
    closest_enemy = min(available_targets, key=lambda e: np.linalg.norm(np.array(player_pos) - e['pos']))
    
    if closest_enemy:
        dx = closest_enemy['pos'][0] - player_pos[0]
        dz = closest_enemy['pos'][2] - player_pos[2]
        target_angle = math.degrees(math.atan2(-dx, -dz))
        angle_diff = (target_angle - player_rot_y + 180) % 360 - 180
        player_rot_y += angle_diff * 10 * dt
        if abs(angle_diff) < 5.0:
            fire_bullet()
            targeted_enemies_this_sweep.add(id(closest_enemy))

def update_lighting():
    global LIGHT_DIRECTION, LIGHT_COLOR, AMBIENT_COLOR

    time_of_day_cycle = 1.0 - (time_remaining / SURVIVAL_TIME_SECONDS)
    
    is_dawn = time_remaining < 120
    
    angle = time_of_day_cycle * math.pi 
    LIGHT_DIRECTION = np.array([math.cos(angle), math.sin(angle), -0.5], dtype=np.float32)
    LIGHT_DIRECTION /= np.linalg.norm(LIGHT_DIRECTION)

    color_noon = np.array([1.0, 1.0, 0.85]); color_sunset = np.array([1.0, 0.4, 0.2])
    color_night = np.array([0.2, 0.3, 0.5]); color_dawn = np.array([1.0, 0.6, 0.4])
    ambient_noon = np.array([0.3, 0.3, 0.3]); ambient_night = np.array([0.05, 0.05, 0.1])
    
    if is_dawn:
        dawn_factor = (120 - time_remaining) / 120.0
        LIGHT_COLOR = lerp(color_night, color_dawn, dawn_factor)
        AMBIENT_COLOR = lerp(ambient_night, ambient_noon, dawn_factor)
    elif time_of_day_cycle < 0.5:
        factor = time_of_day_cycle * 2.0
        LIGHT_COLOR = lerp(color_noon, color_sunset, factor)
        AMBIENT_COLOR = ambient_noon
    else:
        factor = (time_of_day_cycle - 0.5) * 2.0
        LIGHT_COLOR = lerp(color_sunset, color_night, factor)
        AMBIENT_COLOR = lerp(ambient_noon, ambient_night, factor)

    if LIGHT_DIRECTION[1] < 0:
        LIGHT_COLOR *= 0.3

def apply_phong_shading(base_color, normal, is_shiny=False):
    normal = np.array(normal, dtype=np.float32)
    norm = np.linalg.norm(normal)
    if norm < 0.001:
        glColor3fv(np.clip(base_color * AMBIENT_COLOR, 0.0, 1.0))
        return
    normal /= norm

    ambient = base_color * AMBIENT_COLOR
    diffuse_intensity = max(0.0, np.dot(LIGHT_DIRECTION, normal))
    diffuse = base_color * LIGHT_COLOR * diffuse_intensity
    specular = np.array([0.0, 0.0, 0.0])

    if is_shiny and diffuse_intensity > 0.0:
        view_dir = -camera_pos
        view_norm = np.linalg.norm(view_dir)
        if view_norm > 0.001:
            view_dir /= view_norm
            reflect_dir = 2 * np.dot(LIGHT_DIRECTION, normal) * normal - LIGHT_DIRECTION
            specular_angle = max(0.0, np.dot(view_dir, reflect_dir))
            specular = LIGHT_COLOR * SPECULAR_INTENSITY * (specular_angle ** SHININESS)

    glColor3fv(np.clip(ambient + diffuse + specular, 0.0, 1.0))

def check_collisions():
    global game_score, player_health, bullets, heal_items
    if is_game_over: 
        return
    
    current_time = time.perf_counter() - game_start_time
    bullets_after_hits = []
    for b in bullets:
        hit = False
        for e in enemies:
            if e['state'] == 'ALIVE' and math.sqrt((b['pos'][0] - e['pos'][0])**2 + (b['pos'][2] - e['pos'][2])**2) < 1.3:
                e['health'] -= BULLET_DAMAGE
                
                if e['health'] <= 0:
                    game_score += 10
                    e['state'] = 'DEAD'
                    e['death_time'] = current_time
                    if e.get('type') == 'BOSS':
                        heal_items.append({'pos': e['pos'].copy()})
                
                hit = True
                break
        
        if not hit:
            bullets_after_hits.append(b)
            
    bullets[:] = bullets_after_hits

    # --- Part 2: Enemy-to-Player Collisions ---
    for e in enemies:
        if e['state'] == 'ALIVE' and math.sqrt((player_pos[0] - e['pos'][0])**2 + (player_pos[2] - e['pos'][2])**2) < 2.0:
            time_passed = SURVIVAL_TIME_SECONDS - time_remaining
            damage_dealt = ENEMY_BASE_DAMAGE + (time_passed * ENEMY_DAMAGE_SCALING_FACTOR)
            
            player_health -= damage_dealt
            e['state'] = 'DEAD'
            e['death_time'] = current_time

    items_to_keep = []
    for item in heal_items:
        dist_to_player = math.sqrt((player_pos[0] - item['pos'][0])**2 + (player_pos[2] - item['pos'][2])**2)
        if dist_to_player < 2.0:
            player_health += HEAL_AMOUNT
            if player_health > MAX_PLAYER_HEALTH:
                player_health = MAX_PLAYER_HEALTH
        else:
            items_to_keep.append(item)
    heal_items[:] = items_to_keep


def check_game_over():
    global is_game_over, player_won
    if time_remaining <= 0 and not is_game_over:
        player_won = True
        is_game_over = True
    if player_health <= 0 and not player_won:
        is_game_over = True


def reset_game():
    # The global player_life has been removed as it's no longer used.
    global player_health, game_score, bullets_missed, is_game_over, player_pos, player_rot_y, bullets, enemies, player_won, time_remaining, game_start_time, last_time, is_boss_spawned, heal_items
    
    # --- FIX: Reset player_health to its maximum value ---
    player_health = MAX_PLAYER_HEALTH 
    
    game_score = 0; 
    bullets_missed = 0; 
    is_game_over = False
    player_pos = [0.0, 3.0, 0.0]; 
    player_rot_y = 0.0; 
    bullets.clear(); 
    enemies.clear()
    
    for _ in range(enemy_count):
        enemy = {
            'pos': np.array([0.0, 1.0, 0.0]), 
            'speed': random.uniform(2.0, 4.0), 
            'state': 'ALIVE', 
            'death_time': 0,
            'health': 50.0,
            'max_health': 50.0
        }
        respawn_enemy(enemy); 
        enemies.append(enemy)
        
    time_remaining = SURVIVAL_TIME_SECONDS
    player_won = False
    game_start_time = time.perf_counter()
    last_time = game_start_time

    is_boss_spawned = False
    heal_items.clear()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); 
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], camera_target[0], camera_target[1], camera_target[2], 0, 1, 0)
    
    draw_grid_and_boundaries()
    draw_obstacles() 
    draw_player()
    draw_heal_items()
    for enemy in enemies: draw_enemy(enemy)
    for bullet in bullets: draw_bullet(bullet)
        
    draw_hud(); 
    glutSwapBuffers()


def keyboard_down(key, x, y):
    global cheat_mode_active, auto_gun_follow_active, is_free_camera_active
    try:
        key_str = key.decode('utf-8').lower()
        key_states[key_str] = True
        if key_str == 'c': 
            cheat_mode_active = not cheat_mode_active
        if key_str == 'v' and cheat_mode_active: 
            auto_gun_follow_active = not auto_gun_follow_active
        if key_str == 'r' and is_game_over: 
            reset_game()
        if key_str == 'k': 
            is_free_camera_active = not is_free_camera_active
    except (UnicodeDecodeError, KeyError): pass

def keyboard_up(key, x, y):
    try: 
        key_states[key.decode('utf-8').lower()] = False
    except (UnicodeDecodeError, KeyError): 
        pass


def mouse_click(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN: fire_bullet()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN: 
        camera_mode = 'FIRST_PERSON' if camera_mode == 'THIRD_PERSON' else 'THIRD_PERSON'


def game_loop():
    global last_time, time_remaining, is_boss_spawned; 
    if not is_boss_spawned and time_remaining <= (SURVIVAL_TIME_SECONDS / 2):
        spawn_boss()
        is_boss_spawned = True
    current_time = time.perf_counter()
    dt = current_time - last_time
    if dt < 1/60.0: return
    last_time = current_time
    
    if not is_game_over:
        time_remaining -= dt
        update_player(dt)
        update_bullets(dt)
        update_enemies(dt)
        update_cheat_mode(dt)
        check_collisions()
    
    update_lighting()
    update_camera_smooth(dt)
    check_game_over()
    glutPostRedisplay()


def init():
    global last_time, game_start_time, camera_pos, camera_target
    glClearColor(0.0, 0.0, 0.0, 1.0); 
    glEnable(GL_DEPTH_TEST); 
    glViewport(0, 0, window_width, window_height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = window_width / window_height if window_height > 0 else 1
    gluPerspective(45.0, aspect_ratio, 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    reset_game()
    angle_rad = math.radians(camera_rot_y)
    cam_x = player_pos[0] + camera_third_person_radius * math.sin(angle_rad)
    cam_z = player_pos[2] + camera_third_person_radius * math.cos(angle_rad)
    cam_y = player_pos[1] + camera_third_person_height
    camera_pos = np.array([cam_x, cam_y, cam_z])
    camera_target = np.array(player_pos)
    game_start_time = time.perf_counter()
    last_time = game_start_time


def main():
    glutInit(sys.argv); 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH); 
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"3D Survival Game")
    init(); 
    glutDisplayFunc(display); 
    glutKeyboardFunc(keyboard_down); 
    glutKeyboardUpFunc(keyboard_up); 
    glutMouseFunc(mouse_click)
    glutIdleFunc(game_loop)
    print("Controls: W/S/A/D (Move), Mouse Left (Fire), Mouse Right (Toggle Camera)")
    print("K (Toggle Free Camera), C (Toggle Cheat), R (Reset Game)")
    glutMainLoop()

if __name__ == "__main__":
    main()
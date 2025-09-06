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
camera_third_person_radius = 15.0; 
camera_third_person_height = 5.0; 
camera_rot_y = 0.0; 
camera_pitch = -30.0
bullets = []; 
enemies = []; 

ranged_enemies = [] 
ranged_projectiles = []
# Healing Item State
healing_item_active = False
healing_item_x = 0.0
healing_item_z = 0.0
healing_spawn_timer = 0.0
healing_spawn_interval = random.uniform(1200, 1800)  # first spawn between 20-30 seconds
player_x, player_z = 0.0, 0.0
healing_item_x, healing_item_z = 0.0, 0.0
healing_item_active = False
player_health = 0
is_game_over = False
targeted_enemies_this_sweep = set() 
enemy_count = 5; 
grid_size = 100; 
respawn_delay = 0.35
key_states = {k: False for k in 'wasdcvk'}; 
special_key_states = {key: False for key in [100, 101, 102, 103]}
cheat_mode_active = False; 
auto_gun_follow_active = False
SURVIVAL_TIME_SECONDS = 120 # 2 minutes
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
SPAWN_INTERVAL = 10.0 
time_since_last_spawn = 0.0
PLAYER_SPAWN_BORDER = 20.0 
is_player_moving = False
GUN_OFFSET_RIGHT = -0.8
GUN_OFFSET_UP = 0.9     
GUN_OFFSET_FORWARD = 1.2
CAMERA_COLLISION_STEP = 0.5
ENEMY_ATTACK_COOLDOWN = 1.0
GROUND_PATCHES = []
ENEMY_COLLISION_RADIUS = 1.5 
ENEMY_SPEED_SCALING_FACTOR = 0.1
MAX_AMMO = 30
current_ammo = MAX_AMMO
RELOAD_TIME = 2.0
is_reloading = False
last_reload_time = 0.0
OBSTACLES = [
    {
        'type': 'HOUSE', # House
        'pos': np.array([-20.0, 0.0, -15.0]),
        'size': np.array([12.0, 10.0, 15.0]) 
    },
    {
        'type': 'TREE', # Tree
        'pos': np.array([15.0, 0.0, 10.0]),
        'radius': 5.0,
        'height': 15.0
    },
    {
        'type': 'TREE', # Tree
        'pos': np.array([-10.0, 0.0, 20.0]),
        'radius': 5.5,
        'height': 20.0
    }
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
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    
    if is_game_over and not player_won:
        glRotatef(90, 0, 0, 1)
        
    glRotatef(player_rot_y, 0, 1, 0)
    glRotatef(180, 0, 1, 0)
    quad = gluNewQuadric()

    walk_cycle_time = time.perf_counter() * 8  

    leg_swing_angle = math.sin(walk_cycle_time) * 35 if is_player_moving else 0
    arm_swing_angle = math.sin(walk_cycle_time) * 45 if is_player_moving else 0
    body_lean_angle = 15 if is_player_moving else 0

    glPushMatrix()
    glRotatef(body_lean_angle, 1, 0, 0)

    # Torso
    apply_phong_shading(np.array([0.1, 0.4, 0.1]), np.array([1, 0, 0])) 
    glPushMatrix()
    glTranslatef(0, 0.5, 0)
    glScalef(0.7, 1.0, 0.4)
    glutSolidCube(2.0)
    glPopMatrix()

    # Head
    glPushMatrix()
    glTranslatef(0, 1.8, 0)
    apply_phong_shading(np.array([0.9, 0.7, 0.6]), LIGHT_DIRECTION) # Skin tone
    glutSolidSphere(0.6, 20, 20)
    
    # Eyes
    apply_phong_shading(np.array([0.0, 0.0, 0.0]), LIGHT_DIRECTION) # Black
    glPushMatrix(); glTranslatef(0.2, 0.1, 0.5); glutSolidSphere(0.08, 10, 10); glPopMatrix() # Right eye
    glPushMatrix(); glTranslatef(-0.2, 0.1, 0.5); glutSolidSphere(0.08, 10, 10); glPopMatrix() # Left eye

    # Hair
    apply_phong_shading(np.array([0.2, 0.1, 0.1]), LIGHT_DIRECTION) # Brown hair
    glPushMatrix(); 
    glTranslatef(0, 0.5, 0.1); 
    glScalef(1.0, 0.8, 1.0); 
    glutSolidSphere(.85, 15, 15); 
    glPopMatrix()
    glPopMatrix() # End Head group

    # Left Arm
    glPushMatrix()
    glTranslatef(0.8, 1.0, 0) # Shoulder joint
    glRotatef(-arm_swing_angle, 1, 0, 0) # Apply walk cycle rotation
    apply_phong_shading(np.array([0.9, 0.7, 0.6]), LIGHT_DIRECTION) # Skin tone
    glScalef(0.3, 1.0, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()

    # Right Arm and Gun
    glPushMatrix()
    glTranslatef(-0.8, 1.0, 0) # Shoulder joint
    glRotatef(arm_swing_angle, 1, 0, 0) # Apply opposite walk cycle rotation
    
    # Arm
    glPushMatrix()
    apply_phong_shading(np.array([0.9, 0.7, 0.6]), LIGHT_DIRECTION) # Skin tone
    glScalef(0.3, 1.0, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()

    # Gun Model
    glTranslatef(0, -0.6, 0.5) # Position gun in hand
    apply_phong_shading(np.array([0.2, 0.2, 0.2]), LIGHT_DIRECTION)
    glPushMatrix(); glScalef(0.2, 0.4, 1.5); 
    glutSolidCube(1.0); glPopMatrix() # Body & Barrel
    glPushMatrix(); glTranslatef(0, -0.3, -0.2); 
    glScalef(0.2, 0.4, 0.2); 
    glutSolidCube(1.0); 
    glPopMatrix() # Grip
    glPopMatrix() # End Right Arm and Gun group

    glPopMatrix() # End Upper Body group

    # --- Legs ---
    apply_phong_shading(np.array([0.1, 0.2, 0.5]), LIGHT_DIRECTION) # Blue pants

    # Left Leg
    glPushMatrix()
    glTranslatef(-0.4, 0.5, 0) # Hip joint
    glRotatef(leg_swing_angle, 1, 0, 0) # Apply walk cycle
    glTranslatef(0, -0.75, 0)
    glPushMatrix(); glScalef(0.4, 1.5, 0.4); glutSolidCube(1.0); glPopMatrix() # Thigh
    glTranslatef(0, -0.75, 0)
    glRotatef(max(0, leg_swing_angle * -0.5), 1, 0, 0) # Knee bend
    glTranslatef(0, -0.75, 0)
    glPushMatrix(); glScalef(0.4, 1.5, 0.4); glutSolidCube(1.0); glPopMatrix() # Shin
    glPopMatrix()

    # Right Leg
    glPushMatrix()
    glTranslatef(0.4, 0.5, 0) # Hip joint
    glRotatef(-leg_swing_angle, 1, 0, 0) # Apply opposite walk cycle
    glTranslatef(0, -0.75, 0)
    glPushMatrix(); glScalef(0.4, 1.5, 0.4); glutSolidCube(1.0); glPopMatrix() # Thigh
    glTranslatef(0, -0.75, 0)
    glRotatef(max(0, -leg_swing_angle * -0.5), 1, 0, 0) # Knee bend
    glTranslatef(0, -0.75, 0)
    glPushMatrix(); glScalef(0.4, 1.5, 0.4); glutSolidCube(1.0); glPopMatrix() # Shin
    glPopMatrix()

    gluDeleteQuadric(quad)
    glPopMatrix()


def draw_enemy(enemy):
    if enemy['state'] == 'ALIVE':
        # Arm rotation
        arm_rotation_angle = (time.perf_counter() * 250*4) % 360

        total_elapsed_time = time.perf_counter() - game_start_time
        scale = 1.0 + 0.1 * math.sin(total_elapsed_time * 5)
        
        glPushMatrix(); 
        glTranslatef(enemy['pos'][0], enemy['pos'][1], enemy['pos'][2])
        glRotatef(enemy['rot_y'], 0, 1, 0)
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

        # spinning ARMS and MELEE WEAPONS
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
        
        glPopMatrix() 

    if enemy.get('glow_time', 0) > 0:
      glPushMatrix()
      glTranslatef(enemy['pos'][0], enemy['pos'][1] + 2.0, enemy['pos'][2])  # slightly above enemy
      glColor4f(1.0, 0.0, 0.0, 0.5)  # semi-transparent red
      glutSolidSphere(1.5, 20, 20)   # template-safe
      glPopMatrix()
      






def draw_bullet(bullet):
    glPushMatrix(); 
    glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2]); 
    glColor3f(1.0, 1.0, 0.0); 
    glutSolidCube(0.3); 
    glPopMatrix()


def draw_grid_and_boundaries():
    glPushMatrix()
    ground_normal = np.array([0.5, 0.35, 0.05])
    apply_phong_shading(np.array([0.2, 0.2, 0.1]), ground_normal)
    glBegin(GL_QUADS)
    glVertex3f(-grid_size, 0, -grid_size)
    glVertex3f(grid_size, 0, -grid_size)
    glVertex3f(grid_size, 0, grid_size)
    glVertex3f(-grid_size, 0, grid_size)
    glEnd()

    for patch in GROUND_PATCHES:
        glPushMatrix()
        glTranslatef(patch['pos'][0], patch['pos'][1], patch['pos'][2])
        glRotatef(patch['angle'], 0, 1, 0)
        apply_phong_shading(patch['color'][:3], ground_normal) 
        glColor3f(patch['color'][0], patch['color'][1], patch['color'][2])
        half_size = patch['size'] / 2
        glBegin(GL_QUADS)
        glVertex3f(-half_size, 0, -half_size)
        glVertex3f(half_size, 0, -half_size)
        glVertex3f(half_size, 0, half_size)
        glVertex3f(-half_size, 0, half_size)
        glEnd()
        glPopMatrix()

    wall_height = 50
    glColor3f(0.1, 0.1, 0.1); 
    glBegin(GL_QUADS); 
    glVertex3f(-grid_size, 0, grid_size); 
    glVertex3f(grid_size, 0, grid_size); 
    glVertex3f(grid_size, wall_height, grid_size); 
    glVertex3f(-grid_size, wall_height, grid_size); 
    glEnd()
    glBegin(GL_QUADS); 
    glVertex3f(-grid_size, 0, -grid_size); 
    glVertex3f(grid_size, 0, -grid_size); 
    glVertex3f(grid_size, wall_height, -grid_size); 
    glVertex3f(-grid_size, wall_height, -grid_size); 
    glEnd()
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
    quad = gluNewQuadric() 

    for obs in OBSTACLES:
        glPushMatrix()
        glTranslatef(obs['pos'][0], obs['pos'][1], obs['pos'][2])

        if obs['type'] == 'HOUSE': 
            base_color = np.array([0.8, 0.7, 0.5]) # Beige walls
            w, h, d = obs['size'][0]/2.0, obs['size'][1], obs['size'][2]/2.0
            
            # Walls 
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [0, 0, 1]); 
            glVertex3f(-w, 0, d); 
            glVertex3f(w, 0, d); 
            glVertex3f(w, h, d); 
            glVertex3f(-w, h, d); 
            glEnd()
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [0, 0, -1]); 
            glVertex3f(-w, 0, -d); 
            glVertex3f(-w, h, -d); 
            glVertex3f(w, h, -d); 
            glVertex3f(w, 0, -d); glEnd()
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [0, 1, 0]); 
            glVertex3f(-w, h, -d); 
            glVertex3f(-w, h, d); 
            glVertex3f(w, h, d); 
            glVertex3f(w, h, -d); glEnd()
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [0, -1, 0]); 
            glVertex3f(-w, 0, -d); 
            glVertex3f(w, 0, -d); 
            glVertex3f(w, 0, d); 
            glVertex3f(-w, 0, d); glEnd()
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [1, 0, 0]); 
            glVertex3f(w, 0, -d); 
            glVertex3f(w, h, -d); 
            glVertex3f(w, h, d); 
            glVertex3f(w, 0, d); 
            glEnd()
            glBegin(GL_QUADS); 
            apply_phong_shading(base_color, [-1, 0, 0]); 
            glVertex3f(-w, 0, -d); 
            glVertex3f(-w, 0, d); 
            glVertex3f(-w, h, d); 
            glVertex3f(-w, h, -d); 
            glEnd()

            # Roof
            roof_color = np.array([0.6, 0.2, 0.2]); 
            roof_height = 6.0
            p_fr = np.array([w, h, d]); 
            p_fl = np.array([-w, h, d]); 
            p_br = np.array([w, h, -d]); 
            p_bl = np.array([-w, h, -d]); 
            p_peak = np.array([0, h + roof_height, 0])
            apply_phong_shading(roof_color, np.cross(p_br - p_fr, p_peak - p_fr), True); 
            glBegin(GL_QUADS); 
            glVertex3fv(p_fr); 
            glVertex3fv(p_br); 
            glVertex3fv(p_peak); 
            glVertex3fv(p_peak); 
            glEnd()
            apply_phong_shading(roof_color, np.cross(p_fl - p_bl, p_peak - p_bl), True); 
            glBegin(GL_QUADS); 
            glVertex3fv(p_bl); 
            glVertex3fv(p_fl); 
            glVertex3fv(p_peak); 
            glVertex3fv(p_peak); 
            glEnd()

            apply_phong_shading(roof_color, [0, 0, 1]); 
            glBegin(GL_TRIANGLES); 
            glVertex3fv(p_fl); 
            glVertex3fv(p_fr); 
            glVertex3fv(p_peak); 
            glEnd()
            apply_phong_shading(roof_color, [0, 0, -1]); 
            glBegin(GL_TRIANGLES); 
            glVertex3fv(p_br); 
            glVertex3fv(p_bl); 
            glVertex3fv(p_peak); 
            glEnd()
            
            # Door
            apply_phong_shading(np.array([0.4, 0.2, 0.1]), [0, 0, 1])
            glPushMatrix(); 
            glTranslatef(0, 0, d + 0.01); 
            glScalef(6.0, 16.0, 0.1); 
            glutSolidCube(1.0); 
            glPopMatrix()
            # Window
            apply_phong_shading(np.array([0.1, 0.2, 0.4]), [0, 0, 1])
            glPushMatrix(); 
            glTranslatef(3.0, d + 0.01, 5.0); 
            glScalef(1.5, 1.5, 0.1); 
            glutSolidCube(1.0); 
            glPopMatrix()
            # Chimney
            apply_phong_shading(np.array([0.5, 0.1, 0.1]), [1, 0, 0])
            glPushMatrix(); 
            glTranslatef(w - 1, h + roof_height/2, 0); 
            glScalef(1, 4, 1); 
            glutSolidCube(1.0); glPopMatrix()

        elif obs['type'] == 'TREE': 
            apply_phong_shading(np.array([0.5, 0.35, 0.05]), [1, 0, 0]) 
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quad, obs['radius'], obs['radius'] * 0.8, obs['height'], 20, 20)
            glPopMatrix()

            canopy_base_y = obs['height']
            apply_phong_shading(np.array([0.1, 0.5, 0.1]), LIGHT_DIRECTION, is_shiny=True)
            glPushMatrix(); 
            glTranslatef(0, canopy_base_y, 0); 
            glutSolidSphere(obs['radius'] * 2.0, 15, 15); 
            glPopMatrix()
            glPushMatrix(); 
            glTranslatef(obs['radius'], canopy_base_y, 0); 
            glutSolidSphere(obs['radius'] * 1.8, 15, 15); 
            glPopMatrix()
            glPushMatrix(); 
            glTranslatef(-obs['radius'], canopy_base_y, 0); 
            glutSolidSphere(obs['radius'] * 1.5, 15, 15); 
            glPopMatrix()
            glPushMatrix(); 
            glTranslatef(0, canopy_base_y + obs['radius'], 0); 
            glutSolidSphere(obs['radius'] * 1.9, 15, 15); 
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
    if is_reloading:
        time_left = RELOAD_TIME - (time.perf_counter() - last_reload_time)
        draw_text(10, window_height - 50, f"Reloading... {max(0, time_left):.1f}s")
    else:
        draw_text(10, window_height - 50, f"Ammo: {current_ammo}/{MAX_AMMO}")
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

    health_bar_width = 200
    health_bar_height = 15
    health_bar_x = 10
    health_bar_y = window_height - 70

    current_health_width = health_bar_width * (max(0, player_health) / MAX_PLAYER_HEALTH)
    if current_health_width > 0:
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(health_bar_x, health_bar_y)
        glVertex2f(health_bar_x + current_health_width, health_bar_y)
        glVertex2f(health_bar_x + current_health_width, health_bar_y - health_bar_height)
        glVertex2f(health_bar_x, health_bar_y - health_bar_height)
        glEnd()

    if current_health_width < health_bar_width:

        red_bar_start_x = health_bar_x + current_health_width
        
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(red_bar_start_x, health_bar_y)
        glVertex2f(health_bar_x + health_bar_width, health_bar_y) # End at the full bar width
        glVertex2f(health_bar_x + health_bar_width, health_bar_y - health_bar_height)
        glVertex2f(red_bar_start_x, health_bar_y - health_bar_height)
        glEnd()
    
    glMatrixMode(GL_PROJECTION); 
    glPopMatrix(); 
    glMatrixMode(GL_MODELVIEW); 
    glPopMatrix()


def spawn_boss():
    global enemies
    boss = {
        'pos': np.array([0.0, 1.0, 0.0]), 
        'base_speed': 1.5, 
        'state': 'ALIVE', 
        'death_time': 0,
        'health': 300.0,
        'max_health': 300.0,
        'type': 'BOSS' 
    }
    respawn_enemy(boss)
    enemies.append(boss)




def fire_projectile(x, z):
    vec_to_player = np.array([player_pos[0] - x, 0, player_pos[2] - z])
    dist = np.linalg.norm(vec_to_player)
    dir = vec_to_player / dist if dist > 0 else np.array([0, 0, 1])
    ranged_projectiles.append({
        'pos': np.array([x, 1.5, z]),
        'vel': dir * 10.0   # slow-moving projectile
    })


def update_projectiles(dt):
    global player_health
    keep = []
    for p in ranged_projectiles:
        p['pos'] += p['vel'] * dt
        dist_to_player = np.linalg.norm(p['pos'] - np.array([player_pos[0], 1.5, player_pos[2]]))
        if dist_to_player < 1.5:
            player_health -= 10  # hit player
        elif abs(p['pos'][0]) < grid_size and abs(p['pos'][2]) < grid_size:
            keep.append(p)
    ranged_projectiles[:] = keep


def draw_projectiles():
    for p in ranged_projectiles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        # 🔴 Core fireball
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(0.3, 10, 10)
        # 🔴 Aura glow
        glColor4f(1.0, 0.0, 0.0, 0.3)
        glutSolidSphere(0.6, 15, 15)
        glPopMatrix()


def draw_healing_item():
    if healing_item_active:
        glPushMatrix()
        glTranslatef(healing_item_x, 0.5, healing_item_z)
        glColor3f(0.0, 1.0, 0.0)  # green cube
        glutSolidCube(1.0)
        glPopMatrix()




def fire_bullet():
    global current_ammo
    if is_game_over or is_reloading or current_ammo <= 0: 
        return

    current_ammo -= 1
    dir_x, dir_z = get_vector_from_angle(player_rot_y)
    right_x = dir_z
    right_z = -dir_x

    start_pos_x = player_pos[0]
    start_pos_z = player_pos[2]

    start_pos_x += right_x * GUN_OFFSET_RIGHT
    start_pos_z += right_z * GUN_OFFSET_RIGHT
    
    start_pos_x += dir_x * GUN_OFFSET_FORWARD
    start_pos_z += dir_z * GUN_OFFSET_FORWARD

    start_pos_y = player_pos[1] + GUN_OFFSET_UP

    start_pos = [start_pos_x, start_pos_y, start_pos_z]
    bullets.append({
        'pos': np.array(start_pos), 
        'vel': np.array([dir_x * 40.0, 0, dir_z * 40.0])
    })

def generate_ground_patches():
    """Creates a list of randomized quads to simulate a natural ground texture."""
    global GROUND_PATCHES
    GROUND_PATCHES.clear()
    patch_colors = [
        np.array([0.1, 0.3, 0.1, 0.6]),
        np.array([0.2, 0.4, 0.1, 0.5]), 
        np.array([0.3, 0.2, 0.1, 0.4])  
    ]
    for _ in range(40):
        patch = {
            'pos': np.array([random.uniform(-grid_size, grid_size), 0.1, random.uniform(-grid_size, grid_size)]),
            'size': random.uniform(10, 25),
            'angle': random.uniform(0, 360),
            'color': random.choice(patch_colors)
        }
        GROUND_PATCHES.append(patch)


def respawn_enemy(enemy):
    while True:
        spawn_x = random.uniform(-grid_size + 2, grid_size - 2)
        spawn_z = random.uniform(-grid_size + 2, grid_size - 2)

        if is_position_colliding(spawn_x, spawn_z, 1.5): 
            continue 

        dist_to_player = math.sqrt((player_pos[0] - spawn_x)**2 + (player_pos[2] - spawn_z)**2)
        if dist_to_player < PLAYER_SPAWN_BORDER:
            continue 

        enemy['pos'] = np.array([spawn_x, 1.0, spawn_z])
        break
    enemy['max_health'] *= 1.01
    # reset the enemy's current health
    enemy['health'] = enemy['max_health']
    enemy['state'] = 'ALIVE'; 
    enemy['pos'] = np.array([random.uniform(-grid_size + 2, grid_size - 2), 1.0, random.uniform(-grid_size + 2, grid_size - 2)])


def spawn_new_enemy():
    global enemies
    print(f"Spawning new enemy! Total count: {len(enemies) + 1}")
    new_enemy = {
        'pos': np.array([0.0, 1.0, 0.0]), 
        'base_speed': random.uniform(4.0, 7.0), 
        'state': 'ALIVE', 
        'death_time': 0,
        'health': 50.0,
        'max_health': 50.0,
        'rot_y': 0.0,
        'last_attack_time': 0.0
    }
    respawn_enemy(new_enemy) 
    enemies.append(new_enemy)

def spawn_ranged_enemy():
    attempts = 0                     # ← initialize safety counter
    while attempts < 50:             # ← try max 50 times
        spawn_x = random.uniform(-grid_size + 2, grid_size - 2)
        spawn_z = random.uniform(-grid_size + 2, grid_size - 2)
        if not is_position_colliding(spawn_x, spawn_z, 1.5):
            break                   # ← valid position found
        attempts += 1                # ← increment counter
    else:
        # fallback if no free spot found
        spawn_x, spawn_z = 0.0, 0.0

    enemy = {
    'pos': np.array([spawn_x, 1.0, spawn_z]),
    'health': 3,
    'max_health': 3,
    'state': 'ALIVE',
    'death_time': 0,
    'rot_y': 0.0,
    'cooldown': 0.0,
    'glow_time': 0.0
}


    ranged_enemies.append(enemy)

def update_camera_smooth(dt):
    global camera_pos, camera_target, camera_rot_y, camera_pitch, camera_third_person_height
    
    if camera_mode == 'THIRD_PERSON':
        angle_to_use = camera_rot_y if is_free_camera_active else player_rot_y
        angle_rad = math.radians(angle_to_use)
        ideal_cam_x = player_pos[0] + camera_third_person_radius * math.sin(angle_rad)
        ideal_cam_z = player_pos[2] + camera_third_person_radius * math.cos(angle_rad)
        ideal_cam_y = player_pos[1] + camera_third_person_height
        ideal_cam_pos = np.array([ideal_cam_x, ideal_cam_y, ideal_cam_z])
        player_head_pos = player_pos + np.array([0, 1.5, 0])
        cam_vector = ideal_cam_pos - player_head_pos
        cam_distance = np.linalg.norm(cam_vector)
        cam_direction = cam_vector / cam_distance if cam_distance > 0 else np.array([0,0,1])
        corrected_cam_pos = ideal_cam_pos 
        current_step = CAMERA_COLLISION_STEP
        while current_step < cam_distance:
            test_point = player_head_pos + cam_direction * current_step
            if is_camera_colliding(test_point):
                corrected_cam_pos = player_head_pos + cam_direction * (current_step - CAMERA_COLLISION_STEP)
                break 
            current_step += CAMERA_COLLISION_STEP

        target_cam_pos = corrected_cam_pos
        target_look_at = np.array([player_pos[0], player_pos[1] + 1.0, player_pos[2]]) 
        transition_speed = 15.0 * dt 
        camera_pos = lerp(camera_pos, target_cam_pos, transition_speed)
        camera_target = lerp(camera_target, target_look_at, transition_speed)

    else: 
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
        if obs['type'] == 'HOUSE':
            half_w = obs['size'][0] / 2.0
            half_d = obs['size'][2] / 2.0
            if (obs['pos'][0] - half_w < x + radius and
                obs['pos'][0] + half_w > x - radius and
                obs['pos'][2] - half_d < z + radius and
                obs['pos'][2] + half_d > z - radius):
                return True
        
        elif obs['type'] == 'TREE':
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

def is_camera_colliding(pos):
    if abs(pos[0]) >= grid_size - 1 or abs(pos[2]) >= grid_size - 1:
        return True
    if is_position_colliding(pos[0], pos[2], 0.2): 
        return True
    return False

def is_colliding_with_enemy(x, z, radius):
    """Checks if a given 2D position is colliding with ANY alive enemy."""
    for enemy in enemies:
        if enemy['state'] == 'ALIVE':
            dist_sq = (x - enemy['pos'][0])**2 + (z - enemy['pos'][2])**2
            if dist_sq < (radius + ENEMY_COLLISION_RADIUS)**2:
                return True 
    return False

def update_player(dt):
    global player_pos, player_rot_y, is_player_moving
    if is_game_over:
        is_player_moving = False
        return

    if key_states['a']: player_rot_y += player_rot_speed * dt
    if key_states['d']: player_rot_y -= player_rot_speed * dt
    move_dir = 0
    if key_states['w']: move_dir = 1
    if key_states['s']: move_dir = -1
    is_player_moving = (move_dir != 0)
        
    if is_player_moving:
        dir_x, dir_z = get_vector_from_angle(player_rot_y)
        player_radius = 1.0
        delta_x = dir_x * player_speed * move_dir * dt
        delta_z = dir_z * player_speed * move_dir * dt

        if is_position_colliding(player_pos[0] + delta_x, player_pos[2], player_radius):
            delta_x = 0
        
        if is_position_colliding(player_pos[0] + delta_x, player_pos[2] + delta_z, player_radius):
            delta_z = 0

        player_pos[0] += delta_x
        player_pos[2] += delta_z

        for enemy in enemies:
            if enemy['state'] == 'ALIVE':

                vec_to_player_x = player_pos[0] - enemy['pos'][0]
                vec_to_player_z = player_pos[2] - enemy['pos'][2]
                
                dist_sq = vec_to_player_x**2 + vec_to_player_z**2
                min_dist_sq = (player_radius + ENEMY_COLLISION_RADIUS)**2
                

                if dist_sq < min_dist_sq and dist_sq > 0:
                    dist = math.sqrt(dist_sq)

                    penetration_depth = (player_radius + ENEMY_COLLISION_RADIUS) - dist

                    push_direction_x = vec_to_player_x / dist
                    push_direction_z = vec_to_player_z / dist

                    player_pos[0] += push_direction_x * penetration_depth
                    player_pos[2] += push_direction_z * penetration_depth

        player_pos[0] = max(-grid_size+1, min(grid_size-1, player_pos[0]))
        player_pos[2] = max(-grid_size+1, min(grid_size-1, player_pos[2]))

def update_bullets(dt):
    global bullets_missed, game_score
    bullets_to_keep = []
    
    for b in bullets:
        b['pos'] += b['vel'] * dt
        destroyed = is_bullet_colliding(b['pos'])
        
        if destroyed:
            continue  # Skip keeping this bullet
        
        # Check collision with enemies
        hit_enemy = False
        for enemy in enemies:
            if enemy['state'] == 'ALIVE':
                dist_sq = np.sum((b['pos'] - enemy['pos'])**2)
                if dist_sq < (ENEMY_COLLISION_RADIUS + 0.3)**2:  # 0.3 ≈ bullet size
                    enemy['health'] -= BULLET_DAMAGE
                    hit_enemy = True
                    if enemy['health'] <= 0:
                        enemy['state'] = 'DEAD'
                        game_score += 10  # Add score for killing
                    break
        
        if hit_enemy:
            continue
        
        # Destroy bullets that go out of bounds
        if abs(b['pos'][0]) >= grid_size or abs(b['pos'][2]) >= grid_size:
            bullets_missed += 1
            continue
        
        bullets_to_keep.append(b)
    
    bullets[:] = bullets_to_keep



def update_enemies(dt):

    # Spawn timer logic
    global healing_spawn_timer 
    global healing_spawn_interval
    global healing_item_x
    global healing_item_z
    global healing_item_active
    healing_spawn_timer += 1
    if healing_spawn_timer >= healing_spawn_interval:
       healing_item_x = random.uniform(-10, 10)  # change to your map bounds
       healing_item_z = random.uniform(-10, 10)
       healing_item_active = True
       healing_spawn_timer = 0
       healing_spawn_interval = random.randint(1200, 1800)

    current_time = time.perf_counter() - game_start_time
    for e in enemies:
        if e['state'] == 'ALIVE' and not is_game_over:
            time_passed_in_game = SURVIVAL_TIME_SECONDS - time_remaining
            current_speed = e['base_speed'] + (time_passed_in_game * ENEMY_SPEED_SCALING_FACTOR)
            original_pos = e['pos'].copy()
            enemy_radius = 1.0
            vec_to_player = np.array([player_pos[0], 0, player_pos[2]]) - np.array([e['pos'][0], 0, e['pos'][2]])
            dist_to_player = np.linalg.norm(vec_to_player)
            
            if dist_to_player > 1.5:
                ideal_direction = vec_to_player / dist_to_player
                move_vector = ideal_direction * current_speed * dt
                next_pos_ideal = e['pos'] + move_vector

                if not is_position_colliding(next_pos_ideal[0], next_pos_ideal[2], enemy_radius):
                    e['pos'] = next_pos_ideal
                else:
                    left_probe_dir = np.array([-ideal_direction[2], 0, ideal_direction[0]])
                    right_probe_dir = np.array([ideal_direction[2], 0, -ideal_direction[0]])
                    next_pos_left = e['pos'] + left_probe_dir * current_speed * dt
                    if not is_position_colliding(next_pos_left[0], next_pos_left[2], enemy_radius):
                        e['pos'] = next_pos_left
                    else:
                        next_pos_right = e['pos'] + right_probe_dir * current_speed * dt
                        if not is_position_colliding(next_pos_right[0], next_pos_right[2], enemy_radius):
                            e['pos'] = next_pos_right

            movement_vector = e['pos'] - original_pos
            if np.linalg.norm(movement_vector) > 0.01:
                e['rot_y'] = math.degrees(math.atan2(movement_vector[0], movement_vector[2]))

        elif e['state'] == 'DEAD':
            if current_time - e['death_time'] > respawn_delay:
                respawn_enemy(e)
    for e in ranged_enemies:
     if e['state'] == 'ALIVE' and not is_game_over:
        if e['cooldown'] <= 0:
            fire_projectile(e['pos'][0], e['pos'][2])
            e['cooldown'] = 4.0
            e['glow_time'] = 0.5  # 🔴 flash red when firing
        else:
            e['cooldown'] -= dt
        if e['glow_time'] > 0:
            e['glow_time'] -= dt


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

    time_of_day_cycle = 1.0 - (max(0, time_remaining) / SURVIVAL_TIME_SECONDS)
    angle = time_of_day_cycle * math.pi 
    LIGHT_DIRECTION = np.array([math.cos(angle), math.sin(angle), -0.5], dtype=np.float32)
    LIGHT_DIRECTION /= np.linalg.norm(LIGHT_DIRECTION)

    color_sunset = np.array([1.0, 0.4, 0.2])
    color_night = np.array([0.2, 0.3, 0.5]) # Moonlight
    color_dawn = np.array([1.0, 0.6, 0.4])

    ambient_day = np.array([0.3, 0.3, 0.3])
    ambient_night = np.array([0.05, 0.05, 0.1])
    
    
    # Phase 1: Dusk (0% to 50% of the game)
    if time_of_day_cycle < 0.5:

        factor = time_of_day_cycle / 0.5 
        LIGHT_COLOR = lerp(color_sunset, color_night, factor)
        AMBIENT_COLOR = lerp(ambient_day, ambient_night, factor)

    # Deep Night (50% to 80% of the game)
    elif time_of_day_cycle < 0.8:
        LIGHT_COLOR = color_night
        AMBIENT_COLOR = ambient_night
        
    #  Dawn (80% to 100% of the game)
    elif time_of_day_cycle > 0.8:
        factor = (time_of_day_cycle - 0.8) / 0.2
        LIGHT_COLOR = lerp(color_night, color_dawn, factor)
        AMBIENT_COLOR = lerp(ambient_night, ambient_day, factor)

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
 
    global game_score, player_health, bullets, heal_items, is_game_over
    global healing_item_active, healing_item_x, healing_item_z, life  # ⚠ add this
    global player_x, player_z 
    if is_game_over: 
        return
    
    current_game_time = time.perf_counter() - game_start_time
    bullets_after_hits = []
    for b in bullets:
        hit = False
        for e in enemies:
            if e['state'] == 'ALIVE' and math.sqrt((b['pos'][0] - e['pos'][0])**2 + (b['pos'][2] - e['pos'][2])**2) < 1.3:
                e['health'] -= BULLET_DAMAGE
                if e['health'] <= 0:
                    game_score += 10
                    e['state'] = 'DEAD'
                    e['death_time'] = current_game_time
                    if e.get('type') == 'BOSS':
                        heal_items.append({'pos': e['pos'].copy()})
                hit = True
                break
        if not hit:
            bullets_after_hits.append(b)
    bullets[:] = bullets_after_hits

    for e in enemies:
        if e['state'] == 'ALIVE' and math.sqrt((player_pos[0] - e['pos'][0])**2 + (player_pos[2] - e['pos'][2])**2) < 2.5:
            if current_game_time - e.get('last_attack_time', 0) > ENEMY_ATTACK_COOLDOWN:
                e['last_attack_time'] = current_game_time
                time_passed_in_game = SURVIVAL_TIME_SECONDS - time_remaining
                damage_dealt = ENEMY_BASE_DAMAGE + (time_passed_in_game * ENEMY_DAMAGE_SCALING_FACTOR)
                player_health -= damage_dealt
    # Distance from player to healing item
    if healing_item_active:
        dx = player_pos[0] - healing_item_x
        dz = player_pos[2] - healing_item_z
        distance = (dx*dx + dz*dz)**0.5
        if distance <= 1.5:  # player touches the healing item
            life += 1          # player survives
            player_health = min(player_health + 5, MAX_PLAYER_HEALTH) # make sure player is alive
            healing_item_active = False
        else:
            # player didn't touch the healing item, dead
            player_health = 0
            is_game_over = True
            
    items_to_keep = []
    for item in heal_items:
        dist_to_player = math.sqrt((player_pos[0] - item['pos'][0])**2 + (player_pos[2] - item['pos'][2])**2)
        if dist_to_player < 2.0:
            player_health = min(MAX_PLAYER_HEALTH, player_health + HEAL_AMOUNT)
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
    global player_health, game_score, bullets_missed, is_game_over, player_pos, player_rot_y, bullets, enemies, player_won, time_remaining, game_start_time, last_time, is_boss_spawned, heal_items, is_reloading, current_ammo
    player_health = MAX_PLAYER_HEALTH 
    game_score = 0; 
    bullets_missed = 0; 
    is_game_over = False
    player_pos = [0.0, 3.0, 0.0]; 
    player_rot_y = 0.0; 
    bullets.clear(); 
    enemies.clear()
    
    for i in range(enemy_count):
        enemy = {
            'pos': np.array([0.0, 1.0, 0.0]), 
            'base_speed': random.uniform(4.0, 7.0), 
            'state': 'ALIVE', 
            'death_time': 0,
            'health': 50.0,
            'max_health': 50.0,
            'rot_y': 0.0,
            'last_attack_time': 0.0
        }
        respawn_enemy(enemy); 
        enemies.append(enemy)
    for i in range(2):  # number of ranged enemies
        spawn_ranged_enemy()
    
    time_remaining = SURVIVAL_TIME_SECONDS
    player_won = False
    game_start_time = time.perf_counter()
    last_time = game_start_time
    current_ammo = MAX_AMMO
    is_reloading = False

    is_boss_spawned = False
    heal_items.clear()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); 
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], camera_target[0], camera_target[1], camera_target[2], 0, 1, 0)
    
    draw_grid_and_boundaries()
    draw_obstacles() 
    draw_player()
    draw_healing_item()

    for enemy in enemies:
     if enemy.get('state') == 'ALIVE':  # safer than enemy['state']
        draw_enemy(enemy)

    for enemy in ranged_enemies:
        draw_enemy(enemy)
        draw_projectiles()
    
    for bullet in bullets: 
        draw_bullet(bullet)
    if healing_item_x is not None and healing_item_z is not None:
     glPushMatrix()
     glColor3f(0.0, 1.0, 0.0)  # green cube for healing
     glTranslatef(healing_item_x, 0.5, healing_item_z)
     glutSolidCube(1.0)
     glPopMatrix()
    
    draw_hud(); 
    glutSwapBuffers()


def keyboard_down(key, x, y):
    global cheat_mode_active, auto_gun_follow_active, is_free_camera_active, is_reloading, last_reload_time
    try:
        key_str = key.decode('utf-8').lower()
        key_states[key_str] = True
        if key_str == 'r' and not is_reloading and current_ammo < MAX_AMMO:
            is_reloading = True
            last_reload_time = time.perf_counter()
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
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN: 
        fire_bullet()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN: 
        camera_mode = 'FIRST_PERSON' if camera_mode == 'THIRD_PERSON' else 'THIRD_PERSON'


def game_loop():
    global last_time, time_remaining, is_boss_spawned, time_since_last_spawn, is_reloading, current_ammo; 
    if not is_boss_spawned and time_remaining <= (SURVIVAL_TIME_SECONDS / 2):
        spawn_boss()
        is_boss_spawned = True
    current_time = time.perf_counter()
    dt = current_time - last_time
    if dt < 1/60.0: return
    last_time = current_time
    if is_reloading:
        if time.perf_counter() - last_reload_time >= RELOAD_TIME:
            current_ammo = MAX_AMMO
            is_reloading = False 
    if not is_game_over:
        time_remaining -= dt
        update_player(dt)
        update_bullets(dt)
        update_enemies(dt)
        update_cheat_mode(dt)
        update_projectiles(dt)

        check_collisions()
        time_since_last_spawn += dt
        if time_since_last_spawn >= SPAWN_INTERVAL:
            spawn_new_enemy()
            time_since_last_spawn -= SPAWN_INTERVAL 
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
    generate_ground_patches()
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
    print("K (Toggle Free Camera), C (Toggle Cheat), R (Reload when alive/Reset Game when dead)")
    glutMainLoop()

if __name__ == "__main__":
    main()
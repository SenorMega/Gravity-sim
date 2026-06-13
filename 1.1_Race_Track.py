import pygame
import numpy as np
import sys
import random

# ==========================================
# 🌟 SIMULATION PARAMETERS 🌟
# ==========================================
N_OBJECTS = 400
G_CONSTANT = 0.5
SOFTENING = 5.0
DT = 0.5

# ==========================================
# 🌟 INITIALIZE PYGAME & WINDOW 🌟
# ==========================================
pygame.init()
info = pygame.display.Info()

# Start in windowed mode so you can see the terminal if needed
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Binary System & Race Track - SpaceMouse CAD")
clock = pygame.time.Clock()
is_fullscreen = False

# ==========================================
# 🌟 HARDWARE INIT: 3D SPACEMOUSE 🌟
# ==========================================
pygame.joystick.init()
spacemouse = None

for i in range(pygame.joystick.get_count()):
    joy = pygame.joystick.Joystick(i)
    joy.init()
    if joy.get_numaxes() >= 6:
        spacemouse = joy
        print(f"Hardware Connected: {joy.get_name()} with {joy.get_numaxes()} axes")
        break

if not spacemouse:
    print("No SpaceMouse detected. Defaulting to static camera.")

# Camera State Variables
cam_pan = np.array([WIDTH // 2, HEIGHT // 2], dtype=np.float64)
cam_zoom = 1.0
cam_pitch, cam_yaw, cam_roll = 0.0, 0.0, 0.0

# ==========================================
# 🌟 GENERATE 3D PARTICLES (BINARY + TRACK) 🌟
# ==========================================
pos = np.zeros((N_OBJECTS, 3))
vel = np.zeros((N_OBJECTS, 3))
mass = np.ones((N_OBJECTS, 1))
colors = [(255, 255, 255)] * N_OBJECTS

# --- 1. SETUP THE BINARY STARS ---
M_STAR = 2500
R_BINARY = 50  

# Calculate the perfect circular orbit speed for two equal masses
V_BINARY = np.sqrt(G_CONSTANT * M_STAR / (4 * R_BINARY))

# Star 1 (Right side, moving UP)
pos[0] = [R_BINARY, 0, 0]
vel[0] = [0, V_BINARY, 0]
mass[0] = M_STAR
colors[0] = (255, 200, 50)  # Yellow/Orange

# Star 2 (Left side, moving DOWN)
pos[1] = [-R_BINARY, 0, 0]
vel[1] = [0, -V_BINARY, 0]
mass[1] = M_STAR
colors[1] = (50, 200, 255)  # Blue

# --- 2. SETUP THE "RACE TRACK" DEBRIS DISK ---
track_particles = N_OBJECTS - 2
R_INNER = 220  # Inner edge of the track
R_OUTER = 450  # Outer edge of the track

angles = np.random.uniform(0, 2 * np.pi, track_particles)
radii = np.random.uniform(R_INNER, R_OUTER, track_particles)

# Calculate stable orbital velocity around the combined mass
M_TOTAL = 2 * M_STAR
speeds = np.sqrt(G_CONSTANT * M_TOTAL / radii)

for i in range(track_particles):
    idx = i + 2  # Offset by 2 to skip the central stars
    theta = angles[i]
    r = radii[i]
    v = speeds[i]
    
    # Position (X, Y, and a tiny bit of random Z to give the track thickness)
    pos[idx] = [r * np.cos(theta), r * np.sin(theta), random.uniform(-10, 10)]
    
    # Velocity (Tangent to the circle)
    vel[idx] = [-v * np.sin(theta), v * np.cos(theta), 0]
    
    mass[idx] = 1.0  
    colors[idx] = (random.randint(100, 255), random.randint(100, 255), random.randint(150, 255))

# ==========================================
# 🌟 FAST 3D PHYSICS ENGINE 🌟
# ==========================================
def get_accelerations_3d(p, m):
    x = p[:, 0:1] - p[:, 0]
    y = p[:, 1:2] - p[:, 1]
    z = p[:, 2:3] - p[:, 2]
    
    r_sq = x**2 + y**2 + z**2 + SOFTENING**2
    r_inv3 = 1.0 / (r_sq ** 1.5)
    
    ax = -G_CONSTANT * (x * r_inv3) @ m
    ay = -G_CONSTANT * (y * r_inv3) @ m
    az = -G_CONSTANT * (z * r_inv3) @ m
    
    return np.column_stack((ax[:, 0], ay[:, 0], az[:, 0]))

def rotate_3d(points, pitch, yaw, roll):
    Rx = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    Ry = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    Rz = np.array([[np.cos(roll), -np.sin(roll), 0], [np.sin(roll), np.cos(roll), 0], [0, 0, 1]])
    return points @ Rz.T @ Ry.T @ Rx.T

# ==========================================
# 🌟 MAIN LOOP 🌟
# ==========================================
# Motion trail setup
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill((0, 0, 0))
fade_surface.set_alpha(40) 

running = True
while running:
    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Toggle Fullscreen with 'F'
            elif event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    WIDTH, HEIGHT = info.current_w, info.current_h
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                else:
                    WIDTH, HEIGHT = 1280, 720
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                
                # Rebuild motion trail surface for new screen size
                fade_surface = pygame.Surface((WIDTH, HEIGHT))
                fade_surface.fill((0, 0, 0))
                fade_surface.set_alpha(40)

    # --- 1. PHYSICS STEP ---
    acc = get_accelerations_3d(pos, mass)
    vel += acc * DT
    pos += vel * DT

    # --- 2. SPACEMOUSE CAMERA CONTROLS ---
    if spacemouse:
        deadzone = 0.05
        
        # Grab raw axes (Swap these index numbers based on your earlier diagnostic test!)
        a0 = spacemouse.get_axis(0) # Default: Pan X
        a1 = spacemouse.get_axis(1) # Default: Pan Y
        a2 = spacemouse.get_axis(2) # Default: Zoom
        a3 = spacemouse.get_axis(3) # Default: Pitch
        a4 = spacemouse.get_axis(4) # Default: Roll
        a5 = spacemouse.get_axis(5) # Default: Yaw
        
        # Apply movements
        if abs(a0) > deadzone: cam_pan[0] -= a0 * 15
        if abs(a1) > deadzone: cam_pan[1] -= a1 * 15
        if abs(a2) > deadzone: 
            cam_zoom -= a2 * 0.02
            cam_zoom = max(0.1, min(cam_zoom, 10.0))
            
        if abs(a3) > deadzone: cam_pitch += a3 * 0.05
        if abs(a4) > deadzone: cam_roll += a4 * 0.05
        if abs(a5) > deadzone: cam_yaw += a5 * 0.05

    # --- 3. APPLY CAMERA MATRIX ---
    rotated_pos = rotate_3d(pos, cam_pitch, cam_yaw, cam_roll)
    screen_pos = (rotated_pos * cam_zoom) + np.array([cam_pan[0], cam_pan[1], 0])

    # --- 4. RENDER SCREEN ---
    screen.blit(fade_surface, (0, 0))

    # Depth sorting (furthest objects draw first)
    depth_order = np.argsort(screen_pos[:, 2])

    for i in depth_order:
        sx, sy, sz = screen_pos[i]
        
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            # Stars draw larger (radius 8), track particles draw smaller (radius 1 or 2)
            base_size = 8 if i < 2 else 2
            
            # Scale size based on Z-depth and Camera Zoom
            depth_scale = max(0.5, min(2.0, (sz + 1000) / 1000)) 
            final_size = int(base_size * cam_zoom * depth_scale)
            final_size = max(1, final_size) 
            
            pygame.draw.circle(screen, colors[i], (int(sx), int(sy)), final_size)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
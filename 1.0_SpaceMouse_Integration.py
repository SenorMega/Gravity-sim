import pygame
import numpy as np
import sys
import random

# ==========================================
# 🌟 SIMULATION PARAMETERS 🌟
# ==========================================
N_OBJECTS = 10
G_CONSTANT = 0.5
SOFTENING = 5.0
MAX_SPEED = 0.5
DT = 0.5
SAME_MASS = True

# Initialize Pygame
pygame.init()
info = pygame.display.Info()

# Start in windowed mode
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D N-Body Swarm - CAD Camera")
clock = pygame.time.Clock()

is_fullscreen = False  # Track our screen state

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

# Camera State Variables
cam_pan = np.array([WIDTH // 2, HEIGHT // 2], dtype=np.float64)
cam_zoom = 1.0
cam_pitch, cam_yaw, cam_roll = 0.0, 0.0, 0.0

# ==========================================
# 🌟 GENERATE 3D PARTICLES 🌟
# ==========================================
spawn_radius = HEIGHT // 3

# Generate a 3D "disk" (wide in X and Y, thin in Z)
angles = np.random.uniform(0, 2 * np.pi, N_OBJECTS)
radii = np.random.uniform(0, spawn_radius, N_OBJECTS)
pos_x = radii * np.cos(angles)
pos_y = radii * np.sin(angles)
pos_z = np.random.uniform(-spawn_radius // 10, spawn_radius // 10, N_OBJECTS)
pos = np.column_stack((pos_x, pos_y, pos_z))

# 3D Velocities
vel = np.random.uniform(-MAX_SPEED, MAX_SPEED, (N_OBJECTS, 3))

# Masses
if SAME_MASS:
    mass = np.ones((N_OBJECTS, 1)) * 3.0
else:
    mass = np.random.uniform(1, 5, (N_OBJECTS, 1))
    for _ in range(10): mass[random.randint(0, N_OBJECTS - 1)] = 50

# Colors
colors = [(random.randint(100, 255), random.randint(100, 255), random.randint(150, 255)) for _ in range(N_OBJECTS)]

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

# 3D Rotation Matrix Math
def rotate_3d(points, pitch, yaw, roll):
    # X-axis rotation
    Rx = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    # Y-axis rotation
    Ry = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    # Z-axis rotation
    Rz = np.array([[np.cos(roll), -np.sin(roll), 0], [np.sin(roll), np.cos(roll), 0], [0, 0, 1]])
    
    return points @ Rz.T @ Ry.T @ Rx.T

# ==========================================
# 🌟 MAIN LOOP 🌟
# ==========================================
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill((0, 0, 0))
fade_surface.set_alpha(40) 

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # 1. Physics Step
    acc = get_accelerations_3d(pos, mass)
    vel += acc * DT
    pos += vel * DT

    # 2. Read SpaceMouse (CAD Camera Controls)
    if spacemouse:
        axes_data = [round(spacemouse.get_axis(i), 2) for i in range(spacemouse.get_numaxes())]
        print(f"Raw Puck Data: {axes_data}")
        deadzone = 0.05
        
        # Panning (Pushing puck Left/Right/Up/Down)
        if abs(spacemouse.get_axis(0)) > deadzone: cam_pan[0] -= spacemouse.get_axis(0) * 15
        if abs(spacemouse.get_axis(1)) > deadzone: cam_pan[1] -= spacemouse.get_axis(1) * 15
        
        # Zooming (Pulling puck UP / Pushing puck DOWN)
        if abs(spacemouse.get_axis(2)) > deadzone: 
            cam_zoom -= spacemouse.get_axis(2) * 0.02
            cam_zoom = max(0.1, min(cam_zoom, 10.0)) # Prevent inverting or zooming to infinity
            
        # Rotation (Twisting and tilting the puck)
        if abs(spacemouse.get_axis(3)) > deadzone: cam_pitch += spacemouse.get_axis(3) * 0.05
        if abs(spacemouse.get_axis(4)) > deadzone: cam_roll += spacemouse.get_axis(4) * 0.05
        if abs(spacemouse.get_axis(5)) > deadzone: cam_yaw += spacemouse.get_axis(5) * 0.05

    # 3. Apply Camera Matrix to the 3D points
    rotated_pos = rotate_3d(pos, cam_pitch, cam_yaw, cam_roll)
    screen_pos = (rotated_pos * cam_zoom) + np.array([cam_pan[0], cam_pan[1], 0])

    # 4. Render Screen
    screen.blit(fade_surface, (0, 0))

    # Sort objects by their new Z-depth so things closer to the camera draw on top
    # We use argsort to get the indices from furthest (lowest Z) to closest (highest Z)
    depth_order = np.argsort(screen_pos[:, 2])

    for i in depth_order:
        sx, sy, sz = screen_pos[i]
        
        # Only draw if it's on screen
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            # Make objects further away slightly smaller to enhance the 3D effect
            base_size = 1 if mass[i][0] < 10 else 3
            depth_scale = max(0.5, min(2.0, (sz + 1000) / 1000)) 
            final_size = int(base_size * cam_zoom * depth_scale)
            final_size = max(1, final_size) # Never let size drop below 1 pixel
            
            pygame.draw.circle(screen, colors[i], (int(sx), int(sy)), final_size)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
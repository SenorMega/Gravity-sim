import pygame
import numpy as np
import sys
import random

# ==========================================
# 🌟 SIMULATION PARAMETERS 🌟
# ==========================================
N_OBJECTS = 50         # Number of particles
G_CONSTANT = 1.5        # Gravity strength
SOFTENING = 5.0         # Prevents infinite gravity/slingshots when particles touch
MAX_SPEED = 0.5         # Maximum random starting velocity
DT = 0.5                # Timestep per frame
SAME_MASS = True        # All particles have the same mass

# Initialize Pygame
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("N-Body Swarm")
clock = pygame.time.Clock()

# ==========================================
# 🌟 GENERATE RANDOM PARTICLES 🌟
# ==========================================
# Spawn them in a cluster near the center of the screen
center_x, center_y = WIDTH // 2, HEIGHT // 2
spawn_radius = HEIGHT // 3

# Random positions within a circle
angles = np.random.uniform(0, 2 * np.pi, N_OBJECTS)
radii = np.random.uniform(0, spawn_radius, N_OBJECTS)
pos_x = center_x + radii * np.cos(angles)
pos_y = center_y + radii * np.sin(angles)
pos = np.column_stack((pos_x, pos_y))

# Random low velocities
vel = np.random.uniform(-MAX_SPEED, MAX_SPEED, (N_OBJECTS, 2))

# ==========================================
# Generate Masses Based on Your Setting
# ==========================================
if SAME_MASS:
    # Every single particle gets an identical mass of 3
    mass = np.ones((N_OBJECTS, 1)) * 3.0
else:
    # Random masses with 10 heavy "black holes"
    mass = np.random.uniform(1, 5, (N_OBJECTS, 1))
    for _ in range(10): 
        mass[random.randint(0, N_OBJECTS - 1)] = 50

# Random neon colors for a cool visual
colors = []
for _ in range(N_OBJECTS):
    color = (random.randint(100, 255), random.randint(100, 255), random.randint(150, 255))
    colors.append(color)

# ==========================================
# 🌟 FAST PHYSICS ENGINE 🌟
# ==========================================
def get_accelerations(p, m):
    # This matrix math calculates the distance from EVERY particle to EVERY OTHER particle instantly
    x = p[:, 0:1] - p[:, 0]
    y = p[:, 1:2] - p[:, 1]
    
    r_sq = x**2 + y**2 + SOFTENING**2
    r_inv3 = 1.0 / (r_sq ** 1.5)
    
    # Calculate acceleration based on mass and distance
    ax = -G_CONSTANT * (x * r_inv3) @ m
    ay = -G_CONSTANT * (y * r_inv3) @ m
    
    return np.column_stack((ax[:, 0], ay[:, 0]))

# ==========================================
# 🌟 MAIN LOOP 🌟
# ==========================================
# Create a surface for the "motion trail" fade effect
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill((0, 0, 0))
fade_surface.set_alpha(30) # Lower number = longer trails

running = True
while running:
    # Exit handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Physics Step (Semi-Implicit Euler)
    acc = get_accelerations(pos, mass)
    vel += acc * DT
    pos += vel * DT

    # Render Screen (Draw the fade surface instead of filling pure black to create trails)
    screen.blit(fade_surface, (0, 0))

    # Draw the particles
    for i in range(N_OBJECTS):
        # Determine size based on mass
        size = 1 if mass[i][0] < 10 else 3
        pygame.draw.circle(screen, colors[i], (int(pos[i, 0]), int(pos[i, 1])), size)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
import pygame
import numpy as np
import sys
import math
import os
import random
from skyfield.api import load

# ==========================================
# 🌟 SET YOUR ASTRONOMICAL DATE HERE 🌟
# ==========================================
START_YEAR = 1977
START_MONTH = 9   
START_DAY = 5     
# ==========================================

# 1. Initialize Graphics
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Tilted Textured Solar System: {START_YEAR}-{START_MONTH}-{START_DAY}")
clock = pygame.time.Clock()

# 2. Simulation & Camera Constants
G = 2.0          
TIMESTEP = 0.2   
SOFTENING = 0.5
CENTER = np.array([WIDTH // 2, HEIGHT // 2], dtype=np.float32)

ZOOM = 0.45      
TILT = 0.35      
FPS = 30         # 30 FPS for high performance with image textures

def project_3d(sim_pos):
    rel_x = sim_pos[0] - CENTER[0]
    rel_y = sim_pos[1] - CENTER[1]
    screen_x = CENTER[0] + (rel_x * ZOOM)
    screen_y = CENTER[1] + (rel_y * ZOOM * TILT)
    return int(screen_x), int(screen_y)

# 3. Load NASA Ephemeris Data
print("Calculating planetary alignments...")
eph = load('de421.bsp')
sun_eph = eph['sun']
ts = load.timescale()
target_date = ts.utc(START_YEAR, START_MONTH, START_DAY)

skyfield_map = {
    "Mercury": 'mercury barycenter',
    "Venus": 'venus barycenter',
    "Earth": 'earth barycenter',
    "Mars": 'mars barycenter',
    "Jupiter": 'jupiter barycenter',
    "Saturn": 'saturn barycenter',
    "Uranus": 'uranus barycenter',
    "Neptune": 'neptune barycenter'
}

# 4. Core Planets Data
planet_data = [
    # Name      Mass     Dist   Fallback_Color    Size (Radius)
    ("Sun",     50000.0, 0,     (255, 220, 0),    10), 
    ("Mercury", 0.5,     45,    (160, 160, 160),  2),
    ("Venus",   3.0,     75,    (210, 180, 140),  3),
    ("Earth",   4.0,     110,   (60, 150, 255),   3),
    ("Mars",    0.8,     150,   (240, 90, 60),    2),
    ("Ceres",   0.05,    175,   (220, 220, 220),  1),
    ("Vesta",   0.02,    185,   (190, 190, 190),  1),
    ("Pallas",  0.02,    195,   (170, 170, 170),  1),
    ("Jupiter", 30.0,    230,   (220, 170, 130),  6),
    ("Saturn",  15.0,    310,   (210, 200, 150),  5),
    ("Uranus",  5.0,     370,   (160, 210, 210),  4),
    ("Neptune", 5.0,     420,   (60, 110, 245),   4)
]
NUM_PLANETS = len(planet_data)
p_mass = np.array([p[1] for p in planet_data], dtype=np.float32)

# ==========================================
# 🌟 CUSTOM PLANET SPRITE LOADER 🌟
# ==========================================
sprites = {}
for p in planet_data:
    name = p[0]
    radius = p[4]
    
    # Skip minor asteroids (they stay as tiny procedural dots)
    if name in ["Ceres", "Vesta", "Pallas"]:
        sprites[name] = None
        continue
        
    filename = f"3D_{name}.png"
    
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename).convert_alpha()
            diameter = int(radius * 2.5) 
            
            # Stretch Saturn AND Neptune horizontally to make their rings look wider
            if name in ["Saturn", "Neptune"]:
                img = pygame.transform.smoothscale(img, (int(diameter * 2.2), diameter))
            else:
                img = pygame.transform.smoothscale(img, (diameter, diameter))
                
            sprites[name] = img
            print(f"Successfully loaded {filename}")
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            sprites[name] = None
    else:
        print(f"Could not find {filename} in the folder.")
        sprites[name] = None

# ==========================================
# 🌟 PROBE SPRITE LOADER 🌟
# ==========================================
probe_sprites = []
for i in range(1, 3): 
    filename = f"3D_Voyager{i}.png"
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename).convert_alpha()
            # Scale them to 12x12 pixels so they are visible but smaller than planets
            img = pygame.transform.smoothscale(img, (12, 12))
            probe_sprites.append(img)
            print(f"Successfully loaded {filename}")
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            probe_sprites.append(None)
    else:
        print(f"Could not find {filename} in the folder.")
        probe_sprites.append(None)

# Initialize Planet Positions
p_pos = np.zeros((NUM_PLANETS, 2), dtype=np.float32)
p_vel = np.zeros((NUM_PLANETS, 2), dtype=np.float32)

for i, p in enumerate(planet_data):
    name, dist = p[0], p[2]
    if name == "Sun":
        p_pos[i] = CENTER
    else:
        if name in skyfield_map:
            body = eph[skyfield_map[name]]
            astrometric = sun_eph.at(target_date).observe(body)
            lat, lon, distance = astrometric.ecliptic_latlon()
            angle = lon.radians
        else:
            angle = random.uniform(0, 2 * math.pi)

        p_pos[i] = CENTER + np.array([dist * math.cos(angle), dist * math.sin(angle)])
        speed = np.sqrt((G * p_mass[0]) / dist)
        p_vel[i] = np.array([-speed * math.sin(angle), speed * math.cos(angle)], dtype=np.float32)

# Minor Bodies
ast_pos, ast_vel, ast_colors, ast_sizes = [], [], [], []
for _ in range(30): 
    r = np.random.uniform(170, 200)
    angle = np.random.uniform(0, 2 * math.pi)
    ast_pos.append(CENTER + np.array([r * math.cos(angle), r * math.sin(angle)]))
    speed = np.sqrt((G * p_mass[0]) / r)
    ast_vel.append(np.array([-speed * math.sin(angle), speed * math.cos(angle)]))
    ast_colors.append((100, 100, 110))
    ast_sizes.append(1)

ast_pos = np.array(ast_pos, dtype=np.float32)
ast_vel = np.array(ast_vel, dtype=np.float32)

# Space Probes (Launching from Earth)
earth_idx = 3
probe_pos = np.array([p_pos[earth_idx], p_pos[earth_idx]], dtype=np.float32)
probe_vel = np.array([[20.0, 35.0], [-25.0, 30.0]], dtype=np.float32) 
probe_colors = [(255, 50, 255), (0, 255, 255)] 

# Physics Functions
def get_planet_accel(pos, mass):
    a = np.zeros_like(pos)
    for i in range(NUM_PLANETS):
        d = pos - pos[i]
        r_sq = d[:, 0]**2 + d[:, 1]**2 + SOFTENING
        r3 = 1.0 / (np.sqrt(r_sq)**3)
        r3[i] = 0
        a[i, 0] = G * np.sum(mass * d[:, 0] * r3)
        a[i, 1] = G * np.sum(mass * d[:, 1] * r3)
    return a

def get_sun_only_accel(pos):
    d = CENTER - pos
    r_sq = d[:, 0]**2 + d[:, 1]**2 + SOFTENING
    r3 = 1.0 / (np.sqrt(r_sq)**3)
    a = np.zeros_like(pos)
    if len(pos) > 0:
        a[:, 0] = G * p_mass[0] * d[:, 0] * r3
        a[:, 1] = G * p_mass[0] * d[:, 1] * r3
    return a

p_acc = get_planet_accel(p_pos, p_mass)
ast_acc = get_sun_only_accel(ast_pos)
probe_acc = get_sun_only_accel(probe_pos)

# 7. Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # Physics Integration (Adjusted for 30FPS)
    ADJUSTED_TIMESTEP = TIMESTEP * 2 
    
    p_vel += 0.5 * p_acc * ADJUSTED_TIMESTEP
    if len(ast_pos) > 0: ast_vel += 0.5 * ast_acc * ADJUSTED_TIMESTEP
    probe_vel += 0.5 * probe_acc * ADJUSTED_TIMESTEP
    
    p_pos += p_vel * ADJUSTED_TIMESTEP
    if len(ast_pos) > 0: ast_pos += ast_vel * ADJUSTED_TIMESTEP
    probe_pos += probe_vel * ADJUSTED_TIMESTEP
    
    p_acc = get_planet_accel(p_pos, p_mass)
    ast_acc = get_sun_only_accel(ast_pos)
    probe_acc = get_sun_only_accel(probe_pos)
    
    p_vel += 0.5 * p_acc * ADJUSTED_TIMESTEP
    if len(ast_pos) > 0: ast_vel += 0.5 * ast_acc * ADJUSTED_TIMESTEP
    probe_vel += 0.5 * probe_acc * ADJUSTED_TIMESTEP

    # Render Screen
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) 
    fade.fill((0, 0, 0))
    screen.blit(fade, (0, 0))

    # Draw Asteroids
    for i in range(len(ast_pos)):
        sx, sy = project_3d(ast_pos[i])
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT: 
            pygame.draw.circle(screen, ast_colors[i], (sx, sy), ast_sizes[i])

    # =========================================================
    # 🌟 DEPTH SORTING (Z-INDEX) PLANETS & PROBES 🌟
    # =========================================================
    objects_to_draw = []
    
    # 1. Add all planets to the drawing queue
    for i in range(NUM_PLANETS):
        sx, sy = project_3d(p_pos[i])
        objects_to_draw.append({'type': 'planet', 'index': i, 'sx': sx, 'sy': sy, 'name': planet_data[i][0]})
        
    # 2. Add the Voyagers to the same drawing queue
    for i in range(len(probe_pos)):
        sx, sy = project_3d(probe_pos[i])
        objects_to_draw.append({'type': 'probe', 'index': i, 'sx': sx, 'sy': sy})
        
    # Sort EVERYTHING by Y position (sy) so things further back draw first
    objects_to_draw.sort(key=lambda p: p['sy'])

    # Draw them in perfect back-to-front order
    for obj in objects_to_draw:
        sx = obj['sx']
        sy = obj['sy']
        
        # Only draw if within bounds
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            if obj['type'] == 'planet':
                i = obj['index']
                sprite = sprites[obj['name']]
                if sprite:
                    rect = sprite.get_rect(center=(sx, sy))
                    screen.blit(sprite, rect)
                else:
                    pygame.draw.circle(screen, planet_data[i][3], (sx, sy), planet_data[i][4])
                    
            elif obj['type'] == 'probe':
                i = obj['index']
                sprite = probe_sprites[i] if i < len(probe_sprites) else None
                if sprite:
                    rect = sprite.get_rect(center=(sx, sy))
                    screen.blit(sprite, rect)
                else:
                    pygame.draw.circle(screen, probe_colors[i], (sx, sy), 1)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
# Single-file Python Super Mario Clone (No External Assets)
# Version: Added Title Screen

import pygame
import sys
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
BRIGHT_RED = (255, 0, 0)
BLUE = (100, 149, 237)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
YELLOW = (255, 223, 0)
GREEN = (0, 150, 0)
DARK_GREEN = (0, 100, 0)
GREY = (128, 128, 128)
DARK_GREY = (105, 105, 105)
POLE_COLOR = (192, 192, 192)
CLOUD_WHITE = (245, 245, 245)

# Physics constants
PLAYER_ACC = 0.5
PLAYER_FRICTION = -0.12
PLAYER_GRAVITY = 0.7
PLAYER_JUMP_STRENGTH = -15
PLAYER_MAX_FALL_SPEED = 10
ENEMY_SPEED = 1.5

# --- Helper Functions ---
def draw_text(surface, text, size, x, y, color=WHITE):
    try:
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(midtop=(x, y))
        surface.blit(text_surface, text_rect)
    except Exception as e:
        print(f"Error rendering font: {e}")

# --- Classes ---
# (Player, Platform, Enemy, Coin, Flag, Bush, Cloud, Camera classes remain unchanged)
# --- [Insert ALL class definitions from the previous version here] ---
class Player(pygame.sprite.Sprite):
    # (Player class remains largely the same as the previous version)
    def __init__(self):
        super().__init__()
        self.base_image = pygame.Surface((30, 40)); self.base_image.fill(RED)
        hat = pygame.Surface((20, 8)); hat.fill(BRIGHT_RED)
        self.base_image.blit(hat, (5, 2))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT - 100))
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.bottom)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.score = 0
        self.won = False

    def jump(self):
        if self.on_ground: self.vel.y = PLAYER_JUMP_STRENGTH; self.on_ground = False

    def move(self, direction):
        if direction == "LEFT": self.acc.x = -PLAYER_ACC
        elif direction == "RIGHT": self.acc.x = PLAYER_ACC

    def update(self, platforms):
        if self.won: self.vel.x = 0; return

        # Horizontal
        self.acc = pygame.math.Vector2(0, PLAYER_GRAVITY)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.move("LEFT")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.move("RIGHT")
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel.x += self.acc.x
        MAX_SPEED_X = 5
        if abs(self.vel.x) > MAX_SPEED_X: self.vel.x = MAX_SPEED_X * (1 if self.vel.x > 0 else -1)
        self.pos.x += self.vel.x + 0.5 * self.acc.x
        self.rect.centerx = round(self.pos.x)
        self.check_platform_collisions(platforms, 'horizontal')

        # Vertical
        self.vel.y += self.acc.y
        if self.vel.y > PLAYER_MAX_FALL_SPEED: self.vel.y = PLAYER_MAX_FALL_SPEED
        self.pos.y += self.vel.y + 0.5 * self.acc.y
        self.rect.bottom = round(self.pos.y)
        self.on_ground = False
        self.check_platform_collisions(platforms, 'vertical')

        # Sync
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.bottom

    def check_platform_collisions(self, platforms, direction):
        if direction == 'horizontal':
            hits = pygame.sprite.spritecollide(self, platforms, False)
            for platform in hits:
                if not getattr(platform, 'is_solid', True): continue
                if self.vel.x > 0: self.rect.right = platform.rect.left
                elif self.vel.x < 0: self.rect.left = platform.rect.right
                self.pos.x = self.rect.centerx; self.vel.x = 0

        if direction == 'vertical':
            hits = pygame.sprite.spritecollide(self, platforms, False)
            solid_hits = [p for p in hits if getattr(p, 'is_solid', True)]
            if not solid_hits: return

            if self.vel.y > 0: # Landing
                 solid_hits.sort(key=lambda p: p.rect.top)
                 landed_on = next((p for p in solid_hits if self.rect.bottom >= p.rect.top and self.rect.centery < p.rect.top + 15), None)
                 if landed_on: self.rect.bottom = landed_on.rect.top; self.pos.y = self.rect.bottom; self.vel.y = 0; self.on_ground = True
            elif self.vel.y < 0: # Ceiling
                 solid_hits.sort(key=lambda p: p.rect.bottom, reverse=True)
                 bumped = next((p for p in solid_hits if self.rect.top <= p.rect.bottom and self.rect.centery > p.rect.bottom - 15), None)
                 if bumped: self.rect.top = bumped.rect.bottom; self.pos.y = self.rect.bottom; self.vel.y = 0

    def check_enemy_collisions(self, enemies):
        if self.won: return False
        hits = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hits:
            prox = abs(self.rect.bottom - enemy.rect.top) < 15
            overlap = (self.rect.right > enemy.rect.left + 5 and self.rect.left < enemy.rect.right - 5)
            is_stomp = self.vel.y > 1 and prox and overlap
            if is_stomp:
                enemy.kill(); self.vel.y = PLAYER_JUMP_STRENGTH * 0.6; self.pos.y = self.rect.bottom
                self.on_ground = False; self.score += 100; print(f"Stomped! Score: {self.score}")
            else:
                 if not (self.vel.y < -1 and prox): # Avoid game over right after bounce
                    print(f"Hit by enemy! V:{self.vel}, P_bot:{self.rect.bottom}, E_top:{enemy.rect.top}")
                    return True # Game Over
        return False

    def check_coin_collisions(self, coins):
        if self.won: return
        hits = pygame.sprite.spritecollide(self, coins, True)
        self.score += len(hits) * 50
        if hits: print(f"Coin! Score: {self.score}")

    def check_goal_collision(self, goal_flag):
        if self.won: return False
        if pygame.sprite.collide_rect(self, goal_flag):
            print("Reached the flag! Level Complete!")
            self.won = True; self.score += 1000; return True
        return False

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        surface.blit(self.image, draw_rect)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=BROWN, is_solid=True):
        super().__init__()
        self.image = pygame.Surface((width, height)); self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_solid = is_solid

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH:
             surface.blit(self.image, draw_rect)

class Enemy(pygame.sprite.Sprite):
    # (Enemy class remains largely the same)
    def __init__(self, x, y, patrol_range=100):
        super().__init__()
        self.image = pygame.Surface((25, 25)); self.image.fill(DARK_BROWN)
        pygame.draw.circle(self.image, WHITE, (7, 10), 3)
        pygame.draw.circle(self.image, WHITE, (18, 10), 3)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.start_x = self.rect.left; self.patrol_range = patrol_range
        self.vel_x = ENEMY_SPEED; self.pos_x = float(self.rect.x)
        self.vel_y = 0; self.on_ground = False

    def update(self, platforms):
        # Horizontal
        self.pos_x += self.vel_x; self.rect.x = round(self.pos_x)
        left = self.start_x; right = self.start_x + self.patrol_range
        if (self.vel_x < 0 and self.rect.left <= left) or (self.vel_x > 0 and self.rect.right >= right):
             self.vel_x *= -1
             if self.vel_x > 0: self.rect.left = left + 1
             else: self.rect.right = right - 1
             self.pos_x = float(self.rect.x)
        # Vertical
        solids = [p for p in platforms if getattr(p, 'is_solid', True)]
        if not self.on_ground:
            self.vel_y += PLAYER_GRAVITY * 0.5
            if self.vel_y > PLAYER_MAX_FALL_SPEED * 0.5: self.vel_y = PLAYER_MAX_FALL_SPEED * 0.5
        self.rect.y += int(self.vel_y)
        # Collision
        self.on_ground = False; self.rect.y += 1
        hits = pygame.sprite.spritecollide(self, solids, False)
        self.rect.y -= 1
        if hits:
             hits.sort(key=lambda p: p.rect.top)
             landed = next((p for p in hits if self.rect.bottom >= p.rect.top and self.rect.centery < p.rect.top + 5), None)
             if landed: self.rect.bottom = landed.rect.top; self.vel_y = 0; self.on_ground = True

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH: surface.blit(self.image, draw_rect)

class Coin(pygame.sprite.Sprite):
    # (Coin class remains the same)
    def __init__(self, x, y):
        super().__init__()
        self.size = 15; self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2
        pygame.draw.circle(self.image, YELLOW, (center, center), center)
        pygame.draw.circle(self.image, BLACK, (center, center), center, 1)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH: surface.blit(self.image, draw_rect)

class Flag(pygame.sprite.Sprite):
    # (Flag class remains the same)
    def __init__(self, x, y):
        super().__init__()
        self.pole_height = 180; self.flag_width = 40; self.flag_height = 30; pole_width = 8
        self.image = pygame.Surface((self.flag_width + pole_width, self.pole_height), pygame.SRCALPHA)
        # Pole
        pole_rect = pygame.Rect(0, 0, pole_width, self.pole_height)
        pygame.draw.rect(self.image, POLE_COLOR, pole_rect)
        pygame.draw.circle(self.image, POLE_COLOR, (pole_width // 2, pole_width // 2), pole_width // 2)
        # Flag Head
        flag_points = [(pole_width, 10), (pole_width + self.flag_width, self.flag_height // 2 + 10), (pole_width, self.flag_height + 10)]
        pygame.draw.polygon(self.image, GREEN, flag_points)
        pygame.draw.polygon(self.image, BLACK, flag_points, 1)
        # Position
        self.rect = self.image.get_rect(bottomleft=(x, y))

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH: surface.blit(self.image, draw_rect)

class Bush(pygame.sprite.Sprite):
    """A simple decorative bush."""
    def __init__(self, x, y):
        super().__init__()
        width = random.randint(40, 70); height = random.randint(20, 35)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, DARK_GREEN, (0, height*0.2, width*0.6, height*0.8))
        pygame.draw.ellipse(self.image, GREEN, (width*0.3, 0, width*0.7, height*0.9))
        self.rect = self.image.get_rect(bottomleft=(x, y))

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH: surface.blit(self.image, draw_rect)

class Cloud(pygame.sprite.Sprite):
    """A simple decorative cloud."""
    def __init__(self, x, y):
        super().__init__()
        width = random.randint(60, 150); height = random.randint(30, 60)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        num_blobs = random.randint(3, 5)
        for _ in range(num_blobs):
            blob_w = random.uniform(0.3, 0.7) * width; blob_h = random.uniform(0.4, 0.8) * height
            blob_x = random.uniform(0, 1 - blob_w/width) * width; blob_y = random.uniform(0, 1 - blob_h/height) * height
            pygame.draw.ellipse(self.image, CLOUD_WHITE, (blob_x, blob_y, blob_w, blob_h))
        self.rect = self.image.get_rect(center=(x, y))
        self.drift_speed = random.uniform(-0.1, 0.1); self.true_x = float(x)

    def update(self): # Cloud drifting
         self.true_x += self.drift_speed; self.rect.centerx = round(self.true_x)

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.move(camera_offset_x, 0)
        if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH: surface.blit(self.image, draw_rect)

class Camera:
    # (Camera class remains the same)
    def __init__(self, level_width):
        self.level_width = level_width; self.camera_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    def update(self, target):
        if target.won: return
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        x = min(0, x); x = max(-(self.level_width - SCREEN_WIDTH), x)
        self.camera_rect.x = x
    def get_offset_x(self): return self.camera_rect.x


# --- Game Setup ---
# (setup_level function remains the same as the previous version)
def setup_level():
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    goal_flag_group = pygame.sprite.GroupSingle()
    background_decorations = pygame.sprite.Group() # NEW group for decor

    # --- Ground & Level Dimensions ---
    ground_y = SCREEN_HEIGHT - 40
    level_length = 12000
    hole_width = 150
    ground_segments = []
    current_x = 0
    segment_lengths = [1500, 2500, 1800, 3000] # Lengths before holes
    for length in segment_lengths:
        if current_x + length <= level_length:
             ground_segments.append(Platform(current_x, ground_y, length, 40))
             current_x += length + hole_width # Add hole width for next segment
        else: # Prevent overshoot
             ground_segments.append(Platform(current_x, ground_y, level_length - current_x, 40))
             current_x = level_length; break
    # Add final segment if needed
    if current_x < level_length:
         ground_segments.append(Platform(current_x, ground_y, level_length - current_x, 40))
    platforms.add(ground_segments)

    # --- Floating Platforms --- (Positions relative to new ground/holes)
    floating_platforms = [
        Platform(400, ground_y - 100, 150, 20), Platform(750, ground_y - 180, 100, 20), Platform(1100, ground_y - 120, 120, 20),
        Platform(1800, ground_y - 150, 80, 20), Platform(2200, ground_y - 220, 100, 20), Platform(2600, ground_y - 100, 150, 20),
        Platform(4500, ground_y - 160, 100, 20), Platform(4900, ground_y - 250, 120, 20), Platform(5300, ground_y - 100, 80, 20),
        Platform(8000, ground_y - 120, 150, 20), Platform(8500, ground_y - 200, 100, 60), Platform(9000, ground_y - 280, 120, 20),
        Platform(10000, ground_y - 100, 200, 20), Platform(10500, ground_y - 180, 150, 20), Platform(11000, ground_y - 250, 100, 20),
    ]
    platforms.add(floating_platforms)

    # --- Hills --- (Positions adjusted)
    # Hill 1
    hill1_x = 2000; platforms.add(Platform(hill1_x, ground_y-20, 250, 20), Platform(hill1_x+25, ground_y-40, 200, 20), Platform(hill1_x+50, ground_y-60, 150, 20), Platform(hill1_x+75, ground_y-80, 100, 20))
    # Hill 2
    hill2_x = 6000; platforms.add(Platform(hill2_x, ground_y-20, 150, 20), Platform(hill2_x+150, ground_y-40, 100, 40), Platform(hill2_x+250, ground_y-60, 100, 60), Platform(hill2_x+350, ground_y-40, 100, 40), Platform(hill2_x+450, ground_y-20, 150, 20))

    # --- Background Decorations ---
    # Bushes
    num_bushes = level_length // 300
    for i in range(num_bushes):
        bush_x = random.randint(i*300, (i+1)*300 - 50)
        is_over_hole = False; temp_x = 0
        for length in segment_lengths:
             hole_start = temp_x + length; hole_end = hole_start + hole_width
             if bush_x > hole_start and bush_x < hole_end: is_over_hole = True; break
             temp_x = hole_end
        if not is_over_hole and bush_x < level_length - 100: background_decorations.add(Bush(bush_x, ground_y))
    # Clouds
    num_clouds = level_length // 500
    for i in range(num_clouds):
         cloud_x = random.randint(i*500, (i+1)*500 - 100); cloud_y = random.randint(50, SCREEN_HEIGHT // 3)
         background_decorations.add(Cloud(cloud_x, cloud_y))

    # --- Enemies --- (Positions adjusted)
    level_enemies = [
        Enemy(600, ground_y, 100), Enemy(1000, ground_y, 150),
        Enemy(floating_platforms[4].rect.centerx-50, floating_platforms[4].rect.top, 50),
        Enemy(3000, ground_y, 200), Enemy(3500, ground_y, 100),
        Enemy(floating_platforms[7].rect.centerx-60, floating_platforms[7].rect.top, 60),
        Enemy(hill2_x + 300, ground_y - 80, 50), # On hill 2
        Enemy(8200, ground_y, 100), Enemy(8700, ground_y, 150),
        Enemy(floating_platforms[-2].rect.centerx-75, floating_platforms[-2].rect.top, 100),
        Enemy(11200, ground_y, 100),
    ]
    enemies.add(level_enemies)

    # --- Coins --- (Positions adjusted)
    level_coins = []
    for i in range(4): level_coins.append(Coin(450+i*30, ground_y-150))
    for i in range(5): level_coins.append(Coin(2300+i*30, ground_y-50))
    level_coins.append(Coin(floating_platforms[4].rect.centerx, floating_platforms[4].rect.top-30))
    level_coins.append(Coin(hill1_x + 125, ground_y-120))
    level_coins.append(Coin(hill2_x + 300, ground_y-100))
    for i in range(3): level_coins.append(Coin(floating_platforms[-3].rect.centerx-30+i*30, floating_platforms[-3].rect.top-30))
    for i in range(6): level_coins.append(Coin(9200+i*30, ground_y-50))
    coins.add(level_coins)

    # --- Castle and Flag ---
    castle_base_x = level_length - 500
    castle_width = 200; castle_height = 250
    platforms.add(Platform(castle_base_x, ground_y - castle_height, castle_width, castle_height, GREY, True))
    battlement_w=30; battlement_h=40
    for i in range(4): platforms.add(Platform(castle_base_x + i * (castle_width//4) + 5, ground_y - castle_height - battlement_h + 10, battlement_w, battlement_h, DARK_GREY, False))
    platforms.add(Platform(castle_base_x + castle_width//2 - 25, ground_y - 60, 50, 60, BLACK, False)) # Door
    flag_x = castle_base_x - 80 # Flag Left of castle
    the_flag = Flag(flag_x, ground_y)
    goal_flag_group.add(the_flag)

    level_width_actual = castle_base_x + castle_width + 100
    return platforms, enemies, coins, goal_flag_group, background_decorations, level_width_actual


# --- NEW: Title Screen Function ---
def show_title_screen(screen, clock):
    """Displays the title screen and waits for player action."""
    title_font_size = 80
    instr_font_size = 30
    title_y = SCREEN_HEIGHT // 4
    instr_y = SCREEN_HEIGHT // 2 + 50
    start_key = pygame.K_SPACE # Or pygame.K_RETURN

    waiting = True
    while waiting:
        screen.fill(BLUE) # Background color

        # Draw Title
        draw_text(screen, "Python Pseudo-Mario", title_font_size, SCREEN_WIDTH / 2, title_y, YELLOW)

        # Draw Instructions (could blink later)
        draw_text(screen, f"Press SPACE to Start", instr_font_size, SCREEN_WIDTH / 2, instr_y, WHITE)
        draw_text(screen, "Press ESC to Quit", instr_font_size, SCREEN_WIDTH / 2, instr_y + 40, WHITE)

        # Draw a simple ground line
        pygame.draw.line(screen, BROWN, (0, SCREEN_HEIGHT - 40), (SCREEN_WIDTH, SCREEN_HEIGHT - 40), 40)
        # Maybe draw a stationary player icon?
        temp_player_img = pygame.Surface((30, 40)); temp_player_img.fill(RED)
        temp_hat = pygame.Surface((20, 8)); temp_hat.fill(BRIGHT_RED)
        temp_player_img.blit(temp_hat, (5, 2))
        screen.blit(temp_player_img, (SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 40 - 40)) # Place on ground


        pygame.display.flip()
        clock.tick(FPS) # Keep ticking the clock

        # Event handling for title screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit() # Ensure pygame quits properly
                sys.exit() # Exit the program entirely
            if event.type == pygame.KEYDOWN:
                if event.key == start_key:
                    waiting = False # Stop waiting, start the game
                    return True     # Signal to start game
                if event.key == pygame.K_ESCAPE:
                    waiting = False # Stop waiting
                    return False    # Signal to quit game
    return False # Should technically not be reached, but safety default


# --- Main Game Function ---
def game_loop():
    pygame.init()
    try: pygame.font.init()
    except Exception as e: print(f"Font Error: {e}")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python Pseudo-Mario") # Reset caption
    clock = pygame.time.Clock()

    # --- Show Title Screen ---
    start_game = show_title_screen(screen, clock)
    if not start_game:
        pygame.quit()
        sys.exit()
    # --- End Title Screen Logic ---


    # --- Create Game Objects (Only if starting game) ---
    player = Player()
    platforms, enemies, coins, goal_flag_group, background_decorations, level_width = setup_level()
    player_group = pygame.sprite.GroupSingle(player)
    camera = Camera(level_width)

    running = True; game_over = False; level_complete = False

    # --- Main Game Loop ---
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if not game_over and not level_complete:
                    if event.key == pygame.K_UP or event.key == pygame.K_SPACE or event.key == pygame.K_w: player.jump()
                if event.key == pygame.K_r and (game_over or level_complete):
                     # Clean Restart
                     player = Player()
                     platforms, enemies, coins, goal_flag_group, background_decorations, level_width = setup_level()
                     player_group.add(player)
                     camera = Camera(level_width)
                     game_over = False; level_complete = False

        # --- Updates ---
        if not game_over and not level_complete:
            player_group.update(platforms)
            enemies.update(platforms)
            background_decorations.update()
            camera.update(player)
            # Interactions
            player.check_coin_collisions(coins)
            if player.check_enemy_collisions(enemies): game_over = True
            if goal_flag_group.sprite and player.check_goal_collision(goal_flag_group.sprite): level_complete = True
            # Fall Death
            if player.rect.top > SCREEN_HEIGHT + 200: game_over = True; print("Fell!")

        # --- Drawing ---
        screen.fill(BLUE)
        camera_offset_x = camera.get_offset_x()
        # Layers
        for sprite in background_decorations: sprite.draw(screen, camera_offset_x)
        for sprite in platforms: sprite.draw(screen, camera_offset_x)
        for sprite in coins: sprite.draw(screen, camera_offset_x)
        for sprite in enemies: sprite.draw(screen, camera_offset_x)
        if goal_flag_group.sprite: goal_flag_group.sprite.draw(screen, camera_offset_x)
        player.draw(screen, camera_offset_x)

        # --- UI / Messages ---
        draw_text(screen, f"Score: {player.score}", 30, SCREEN_WIDTH / 2, 10, BLACK)
        if level_complete:
             overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((50, 50, 50, 180)); screen.blit(overlay, (0,0))
             draw_text(screen, "LEVEL COMPLETE!", 72, SCREEN_WIDTH / 2, SCREEN_HEIGHT/3, YELLOW)
             draw_text(screen, f"Final Score: {player.score}", 40, SCREEN_WIDTH / 2, SCREEN_HEIGHT/2, WHITE)
             draw_text(screen, "Press 'R' to Restart or ESC", 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT*2/3, WHITE)
        elif game_over:
             overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((50, 50, 50, 180)); screen.blit(overlay, (0,0))
             draw_text(screen, "GAME OVER", 72, SCREEN_WIDTH/2, SCREEN_HEIGHT/3, BRIGHT_RED)
             draw_text(screen, f"Final Score: {player.score}", 40, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, WHITE)
             draw_text(screen, "Press 'R' to Restart or ESC", 30, SCREEN_WIDTH/2, SCREEN_HEIGHT*2/3, WHITE)

        # --- Display Update ---
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

# --- Start ---
if __name__ == '__main__':
    game_loop()

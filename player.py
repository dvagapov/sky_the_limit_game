import pygame
import math
import random

class Projectile:
    def __init__(self, x, y, projectile_type='arrow'):
        self.x = x
        self.y = y
        self.projectile_type = projectile_type
        self.speed = 12
        self.width = 20 if projectile_type == 'arrow' else 15
        self.height = 5 if projectile_type == 'arrow' else 15
        self.active = True
        
    def update(self):
        """Move projectile forward"""
        self.x += self.speed
        # Deactivate if off screen
        if self.x > 1000:  # Arbitrary far distance
            self.active = False
    
    def draw(self, screen, camera_x):
        """Draw projectile"""
        screen_x = self.x - camera_x
        
        if self.projectile_type == 'arrow':
            # Draw arrow
            pygame.draw.polygon(screen, (139, 69, 19), [
                (screen_x, self.y),
                (screen_x + self.width - 5, self.y - 3),
                (screen_x + self.width, self.y),
                (screen_x + self.width - 5, self.y + 3)
            ])
            pygame.draw.rect(screen, (101, 67, 33), (screen_x - 5, self.y - 1, 10, 2))
        else:  # fireball
            # Draw fireball with glow
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 100, 0, 100), (self.width // 2 + 5, self.height // 2 + 5), self.width // 2 + 5)
            screen.blit(glow_surface, (screen_x - 5, self.y - 5))
            pygame.draw.circle(screen, (255, 69, 0), (int(screen_x + self.width // 2), int(self.y + self.height // 2)), self.width // 2)
            pygame.draw.circle(screen, (255, 200, 0), (int(screen_x + self.width // 2), int(self.y + self.height // 2)), self.width // 4)
    
    def check_collision_with_box(self, box):
        """Check if projectile hits a box"""
        return (self.x < box.x + box.width and
                self.x + self.width > box.x and
                self.y < box.y + box.height and
                self.y + self.height > box.y)

class Player:
    # Superpower types (currently using 3 image-based characters)
    SUPERPOWERS = [
        {"name": "MAGIC CORGI", "key": "magic", "color": (138, 43, 226), "can_fly": True},
        {"name": "FIRE CORGI", "key": "fire", "color": (255, 69, 0), "effect": "fire"},
        {"name": "ARCHER CORGI", "key": "archer", "color": (50, 205, 50)}
    ]
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 40
        self.velocity_y = 0
        self.velocity_x = 0
        self.gravity = 0.8
        self.jump_strength = -15
        self.run_speed = 6
        self.max_speed = 10
        self.is_jumping = False
        self.color = (210, 140, 80)  # Corgi color (orange-brown)
        self.run_animation_frame = 0
        self.super_power = False
        self.super_power_timer = 0
        self.super_power_duration = 180  # 3 seconds at 60 FPS
        self.facing_right = True
        self.current_superpower = None
        self.particle_frame = 0
        self.base_speed_multiplier = 1.0  # Gradually increases over time
        self.blocked_by_edge = False  # True when stopped at platform edge
        self.skins = {}
        self._load_skins()
        self.projectiles = []  # List of active projectiles
        self.shoot_cooldown = 0  # Cooldown timer for shooting
        self.is_flying = False  # True when flying with magic power

    def _load_skins(self):
        """Load character sprites for superpowers if available."""
        # Magic corgi
        try:
            image = pygame.image.load("images/magic.png").convert_alpha()
            self.skins["magic"] = pygame.transform.smoothscale(image, (self.width * 2, self.height * 2))
        except (pygame.error, FileNotFoundError):
            self.skins["magic"] = None

        # Fire corgi
        try:
            image = pygame.image.load("images/fire.png").convert_alpha()
            self.skins["fire"] = pygame.transform.smoothscale(image, (self.width * 2, self.height * 2))
        except (pygame.error, FileNotFoundError):
            self.skins["fire"] = None

        # Archer corgi
        try:
            image = pygame.image.load("images/archer.png").convert_alpha()
            self.skins["archer"] = pygame.transform.smoothscale(image, (self.width * 2, self.height * 2))
        except (pygame.error, FileNotFoundError):
            self.skins["archer"] = None
        
    def jump(self):
        """Make the player jump"""
        if not self.is_jumping:
            self.velocity_y = self.jump_strength
            self.is_jumping = True
            self.blocked_by_edge = False  # Clear blocked state when jumping
    
    def fly(self):
        """Make the player fly upward (when magic power is active)"""
        if self.super_power and self.current_superpower and self.current_superpower.get("can_fly"):
            self.is_flying = True
            self.velocity_y = -8  # Upward force when flying
    
    def stop_flying(self):
        """Stop flying and allow gravity to take over"""
        self.is_flying = False
    
    def move_left(self):
        """Move the corgi left"""
        speed = self.run_speed
        if self.super_power and self.current_superpower and "speed_multiplier" in self.current_superpower:
            speed *= self.current_superpower["speed_multiplier"]
        self.velocity_x = -speed
        self.facing_right = False
    
    def move_right(self):
        """Move the corgi right"""
        speed = self.run_speed
        if self.super_power and self.current_superpower and "speed_multiplier" in self.current_superpower:
            speed *= self.current_superpower["speed_multiplier"]
        self.velocity_x = speed
        self.facing_right = True
    
    def stop_moving(self):
        """Stop horizontal movement"""
        self.velocity_x = 0
    
    def activate_super_power(self):
        """Activate super power mode with random type"""
        self.super_power = True
        self.super_power_timer = self.super_power_duration
        self.current_superpower = random.choice(self.SUPERPOWERS)
        self.particle_frame = 0
        self.shoot_cooldown = 0  # Reset shoot cooldown
    
    def _shoot_projectile(self, projectile_type, world_x):
        """Create a new projectile"""
        # Spawn projectile from front of player in world coordinates
        proj_x = world_x + self.width
        proj_y = self.y + self.height // 2
        self.projectiles.append(Projectile(proj_x, proj_y, projectile_type))
    
    def update(self, ground_height, screen_width=800, blocked=False, world_x=0):
        """Update player position and physics"""
        # Apply gravity (unless flying)
        if not self.is_flying:
            self.velocity_y += self.gravity
        self.y += self.velocity_y
        
        # Update blocked state
        if blocked and not self.is_jumping and not self.is_flying:
            self.blocked_by_edge = True
        elif not blocked:
            self.blocked_by_edge = False
        
        # Determine base horizontal speed (auto-running forward only)
        speed = self.run_speed * self.base_speed_multiplier
        if self.super_power and self.current_superpower and "speed_multiplier" in self.current_superpower:
            speed *= self.current_superpower["speed_multiplier"]
        
        # Stop if blocked by edge
        if self.blocked_by_edge:
            speed = 0
        
        self.velocity_x = speed  # Always run forward (right)
        self.facing_right = True

        # No horizontal position update here - handled by Game class in world coordinates
        
        # Auto-shoot projectiles when in archer or fire mode
        if self.super_power and self.current_superpower:
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
            else:
                key = self.current_superpower.get("key")
                if key == "archer":
                    self._shoot_projectile("arrow", world_x)
                    self.shoot_cooldown = 30  # Shoot every 0.5 seconds
                elif key == "fire":
                    self._shoot_projectile("fireball", world_x)
                    self.shoot_cooldown = 20  # Shoot faster for fireballs
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update()
            if not projectile.active:
                self.projectiles.remove(projectile)
        
        # Check if player is on ground
        if self.y >= ground_height - self.height:
            self.y = ground_height - self.height
            self.velocity_y = 0
            self.is_jumping = False
        
        # Update running animation (faster when moving)
        if abs(self.velocity_x) > 0:
            self.run_animation_frame += 2
        else:
            self.run_animation_frame += 0.5
        if self.run_animation_frame >= 60:
            self.run_animation_frame = 0
        
        # Update super power timer
        if self.super_power:
            self.super_power_timer -= 1
            self.particle_frame += 1
            if self.super_power_timer <= 0:
                self.super_power = False
                self.super_power_timer = 0
                self.current_superpower = None
                self.particle_frame = 0
    
    def draw(self, screen):
        """Draw the corgi dog on screen with superpower effects"""
        # Get current size (may be modified by Giant Mode)
        width = self.width
        height = self.height
        x = self.x
        y = self.y
        
        if self.super_power and self.current_superpower:
            if "size_multiplier" in self.current_superpower:
                size_mult = self.current_superpower["size_multiplier"]
                width = int(self.width * size_mult)
                height = int(self.height * size_mult)
                x = self.x - (width - self.width) // 2
                y = self.y - (height - self.height)
        
        # Draw background superpower effects FIRST (before body/sprite)
        if self.super_power and self.current_superpower:
            key = self.current_superpower.get("key")
            power_color = self.current_superpower["color"]
            
            # General glow for all superpowers
            glow_surface = pygame.Surface((width + 40, height + 40), pygame.SRCALPHA)
            pulse = abs(math.sin(self.particle_frame * 0.1))
            glow_alpha = int(100 + pulse * 100)
            glow_color = power_color + (glow_alpha,)
            pygame.draw.ellipse(glow_surface, glow_color, (0, 0, width + 40, height + 40))
            screen.blit(glow_surface, (x - 20, y - 20))
            
            # Magic effect - purple sparkles and stars
            if key == "magic":
                # Orbiting stars
                for i in range(8):
                    sparkle_angle = (self.particle_frame * 0.2 + i * math.pi / 4) % (math.pi * 2)
                    sparkle_x = x + width // 2 + math.cos(sparkle_angle) * (width // 2 + 15)
                    sparkle_y = y + height // 2 + math.sin(sparkle_angle) * (height // 2 + 15)
                    sparkle_size = 4 + abs(math.sin(self.particle_frame * 0.15 + i)) * 3
                    # Draw bright star shape
                    for j in range(5):
                        angle = sparkle_angle + j * (2 * math.pi / 5)
                        x1 = sparkle_x + math.cos(angle) * sparkle_size
                        y1 = sparkle_y + math.sin(angle) * sparkle_size
                        pygame.draw.circle(screen, (255, 200, 255), (int(x1), int(y1)), 3)
                    pygame.draw.circle(screen, (138, 43, 226), (int(sparkle_x), int(sparkle_y)), 4)
                
                # Magic aura rings
                for i in range(3):
                    ring_offset = (self.particle_frame + i * 20) % 60
                    ring_alpha = int(200 - ring_offset * 3)
                    if ring_alpha > 0:
                        ring_surface = pygame.Surface((width + 30 + ring_offset, height + 30 + ring_offset), pygame.SRCALPHA)
                        pygame.draw.ellipse(ring_surface, (200, 100, 255, ring_alpha), 
                                          (0, 0, width + 30 + ring_offset, height + 30 + ring_offset), 3)
                        screen.blit(ring_surface, (x - 15 - ring_offset // 2, y - 15 - ring_offset // 2))
                
                # Add trailing sparkles when flying
                if self.is_flying:
                    for i in range(6):
                        trail_x = x + width // 2 - i * 12 + random.randint(-3, 3)
                        trail_y = y + height + i * 8 + random.randint(-3, 3)
                        trail_alpha = int(200 - i * 30)
                        if trail_alpha > 0:
                            trail_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
                            pygame.draw.circle(trail_surface, (200, 100, 255, trail_alpha), (6, 6), 6)
                            pygame.draw.circle(trail_surface, (255, 255, 255, trail_alpha // 2), (6, 6), 3)
                            screen.blit(trail_surface, (trail_x - 6, trail_y - 6))
            
            # Fire effect - flames around the dog
            elif key == "fire":
                for i in range(5):
                    flame_offset = math.sin(self.particle_frame * 0.3 + i) * 10
                    flame_size = 8 + math.sin(self.particle_frame * 0.2 + i * 0.5) * 4
                    flame_x = x + (width // 5) * i + flame_offset
                    flame_y = y + height - 5
                    for j in range(3):
                        flame_color = (255, int(165 - j * 40), 0, 150)
                        glow = pygame.Surface((int(flame_size * 2), int(flame_size * 2)), pygame.SRCALPHA)
                        pygame.draw.circle(glow, flame_color, (int(flame_size), int(flame_size)), int(flame_size - j * 2))
                        screen.blit(glow, (flame_x - flame_size, flame_y - flame_size - j * 3))
            
            # Archer effect - green aura with arrow particles
            elif key == "archer":
                for i in range(3):
                    arrow_x = x - 10 - i * 20
                    arrow_y = y + height // 2 + math.sin(self.particle_frame * 0.15 + i) * 8
                    arrow_alpha = int(150 - i * 40)
                    # Draw mini arrow
                    arrow_surface = pygame.Surface((15, 5), pygame.SRCALPHA)
                    pygame.draw.polygon(arrow_surface, (50, 205, 50, arrow_alpha), [
                        (0, 2), (10, 0), (15, 2), (10, 4)
                    ])
                    screen.blit(arrow_surface, (arrow_x, arrow_y))

        # If this superpower has a dedicated sprite, draw it
        sprite_drawn = False
        if self.super_power and self.current_superpower:
            key = self.current_superpower.get("key")
            sprite = self.skins.get(key) if key else None
            if sprite is not None:
                draw_sprite = sprite
                if not self.facing_right:
                    draw_sprite = pygame.transform.flip(sprite, True, False)
                rect = draw_sprite.get_rect()
                sprite_x = x + width // 2 - rect.width // 2
                sprite_y = y + height - rect.height
                screen.blit(draw_sprite, (sprite_x, sprite_y))
                sprite_drawn = True
        
        # Draw the corgi body if no sprite was drawn
        if not sprite_drawn:
            # Get effect type for this superpower
            effect = self.current_superpower.get("effect", "") if self.super_power and self.current_superpower else ""
            
            # Fire effect - flames around the dog
            if effect == "fire":
                for i in range(5):
                    flame_offset = math.sin(self.particle_frame * 0.3 + i) * 10
                    flame_size = 8 + math.sin(self.particle_frame * 0.2 + i * 0.5) * 4
                    flame_x = x + (width // 5) * i + flame_offset
                    flame_y = y + height - 5
                    for j in range(3):
                        flame_color = (255, int(165 - j * 40), 0, 150)
                        glow = pygame.Surface((int(flame_size * 2), int(flame_size * 2)), pygame.SRCALPHA)
                        pygame.draw.circle(glow, flame_color, (int(flame_size), int(flame_size)), int(flame_size - j * 2))
                        screen.blit(glow, (flame_x - flame_size, flame_y - flame_size - j * 3))
            
            # Ice effect - snowflakes and ice crystals
            elif effect == "ice":
                for i in range(8):
                    angle = (self.particle_frame * 0.1 + i * (math.pi / 4)) % (math.pi * 2)
                    ice_x = x + width // 2 + math.cos(angle) * (width // 2 + 15)
                    ice_y = y + height // 2 + math.sin(angle) * (height // 2 + 15)
                    ice_color = (150, 220, 255, 200)
                    ice_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
                    pygame.draw.line(ice_surface, ice_color, (6, 0), (6, 12), 2)
                    pygame.draw.line(ice_surface, ice_color, (0, 6), (12, 6), 2)
                    pygame.draw.line(ice_surface, ice_color, (2, 2), (10, 10), 2)
                    pygame.draw.line(ice_surface, ice_color, (10, 2), (2, 10), 2)
                    screen.blit(ice_surface, (ice_x - 6, ice_y - 6))
            
            # Electric effect - lightning bolts
            elif effect == "electric":
                for i in range(4):
                    if self.particle_frame % 3 == 0:
                        bolt_start_x = x + random.randint(0, width)
                        bolt_start_y = y + random.randint(0, height)
                        for j in range(3):
                            bolt_end_x = bolt_start_x + random.randint(-15, 15)
                            bolt_end_y = bolt_start_y + random.randint(-15, 15)
                            pygame.draw.line(screen, (255, 255, 100), (bolt_start_x, bolt_start_y), (bolt_end_x, bolt_end_y), 2)
                            bolt_start_x, bolt_start_y = bolt_end_x, bolt_end_y
            
            # Rainbow effect - colorful trail
            elif effect == "rainbow":
                colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (139, 0, 255)]
                for i in range(6):
                    trail_offset = i * 5
                    color_idx = (i + self.particle_frame // 10) % len(colors)
                    trail_color = colors[color_idx] + (100,)
                    trail_surface = pygame.Surface((width + 10, height + 10), pygame.SRCALPHA)
                    pygame.draw.ellipse(trail_surface, trail_color, (0, 0, width + 10, height + 10))
                    screen.blit(trail_surface, (x - trail_offset - 5, y - 5))
        
        # Body color changes based on superpower
        if self.super_power and self.current_superpower:
            body_color = self.current_superpower["color"]
        else:
            body_color = self.color
        
        # Draw corgi body (elongated rectangle)
        pygame.draw.rect(screen, body_color, (x, y + height // 4, width, height * 3 // 4), border_radius=8)
        
        # Draw corgi head
        head_size = int(height // 2)
        pygame.draw.circle(screen, body_color, (int(x + width - head_size // 2), int(y + height // 3)), head_size)
        
        # Draw ears (pointy triangles)
        ear_color = (180, 120, 60) if not self.super_power else tuple([max(0, c - 30) for c in body_color])
        ear_offset = math.sin(self.run_animation_frame * 0.2) * 2
        ear_size = head_size // 2
        # Left ear
        pygame.draw.polygon(screen, ear_color, [
            (x + width - head_size, y + ear_offset),
            (x + width - head_size + ear_size // 2, y - ear_size + ear_offset),
            (x + width - head_size + ear_size, y + ear_offset)
        ])
        # Right ear
        pygame.draw.polygon(screen, ear_color, [
            (x + width - ear_size, y + ear_offset),
            (x + width - ear_size // 2, y - ear_size + ear_offset),
            (x + width, y + ear_offset)
        ])
        
        # Draw eyes
        eye_color = (0, 0, 0)
        eye_size = max(2, head_size // 6)
        pygame.draw.circle(screen, eye_color, (int(x + width - head_size), int(y + height // 3)), eye_size)
        pygame.draw.circle(screen, eye_color, (int(x + width - head_size // 4), int(y + height // 3)), eye_size)
        
        # Draw nose
        pygame.draw.circle(screen, (0, 0, 0), (int(x + width - head_size // 4), int(y + height // 2)), max(2, eye_size))
        
        # Draw white chest
        pygame.draw.ellipse(screen, (255, 255, 255), (x + width // 6, y + height // 3, width // 4, height // 2))
        
        # Draw running legs (animated)
        leg_color = (160, 100, 50) if not self.super_power else tuple([max(0, min(255, c - 50)) for c in body_color])
        leg_height = int(height // 5)
        leg_width = max(4, int(width // 12))
        
        # Leg animation
        leg_offset_1 = math.sin(self.run_animation_frame * 0.3) * 4
        leg_offset_2 = math.sin(self.run_animation_frame * 0.3 + math.pi) * 4
        
        # Front legs
        pygame.draw.rect(screen, leg_color, (x + width - width // 4, y + height - leg_offset_1, leg_width, leg_height))
        pygame.draw.rect(screen, leg_color, (x + width - width // 2.5, y + height - leg_offset_2, leg_width, leg_height))
        
        # Back legs
        pygame.draw.rect(screen, leg_color, (x + width // 6, y + height - leg_offset_2, leg_width, leg_height))
        pygame.draw.rect(screen, leg_color, (x + width // 12, y + height - leg_offset_1, leg_width, leg_height))
        
        # Draw tail (wagging)
        tail_angle = math.sin(self.run_animation_frame * 0.4) * 0.5
        tail_length = width // 6
        tail_end_x = x - tail_length * math.cos(tail_angle)
        tail_end_y = y + height // 3 + tail_length * math.sin(tail_angle)
        pygame.draw.line(screen, leg_color, (x, y + height // 3), (tail_end_x, tail_end_y), max(3, leg_width))
    
    def draw_projectiles(self, screen, camera_x):
        """Draw all active projectiles"""
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x)

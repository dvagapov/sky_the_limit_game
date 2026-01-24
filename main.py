import pygame
import sys
import random
from player import Player, Projectile

# Initialize Pygame
pygame.init()

class TerrainSegment:
    def __init__(self, x, segment_type, width=100, height=0, level=0):
        self.x = x
        self.segment_type = segment_type  # 'flat', 'mountain', 'pit', 'platform'
        self.width = width
        self.height = height  # Height for mountains, depth for pits
        self.level = level  # Platform level (0=ground, 1=mid, 2=high)
        
class Terrain:
    def __init__(self, ground_height):
        self.ground_height = ground_height
        self.segments = []
        self.camera_x = 0
        self.difficulty = 0
        self._generate_initial_terrain()
    
    def _generate_initial_terrain(self):
        """Generate initial terrain segments"""
        x = 0
        # Start with long flat ground for safe beginning
        self.segments.append(TerrainSegment(x, 'flat', 800, 0))
        x += 800
        
        # Generate segments ahead
        for _ in range(20):
            self._add_next_segment(x)
            x = self.segments[-1].x + self.segments[-1].width
    
    def _add_next_segment(self, x):
        """Add a terrain segment with difficulty-based weights"""
        # Adjust weights based on difficulty (0-10 scale)
        if self.difficulty < 2:
            # Easy (0-30 sec) - mostly flat, some platforms, no pits
            weights = [70, 10, 0, 20]  # flat, mountain, pit, platform
        elif self.difficulty < 5:
            # Medium (30-90 sec) - balanced with more platforms
            weights = [50, 20, 10, 20]
        elif self.difficulty < 8:
            # Hard (60-100 sec) - more obstacles and platforms
            weights = [30, 30, 15, 25]
        else:
            # Very hard (100+ sec) - challenging
            weights = [25, 30, 20, 25]
        
        segment_type = random.choices(
            ['flat', 'mountain', 'pit', 'platform'],
            weights=weights
        )[0]
        
        if segment_type == 'flat':
            width = random.randint(150, 300)  # Wider islands
            self.segments.append(TerrainSegment(x, 'flat', width, 0, 0))
        elif segment_type == 'mountain':
            width = random.randint(80, 150)
            height = random.randint(30, 80)
            self.segments.append(TerrainSegment(x, 'mountain', width, height, 0))
        elif segment_type == 'pit':
            width = random.randint(50, 100)  # Narrower pits
            self.segments.append(TerrainSegment(x, 'pit', width, 0, 0))
        else:  # platform
            # Create multi-level platforms
            num_steps = random.randint(2, 4)
            step_width = random.randint(60, 100)
            for i in range(num_steps):
                level = min(i, 2)  # Max 3 levels (0, 1, 2)
                self.segments.append(TerrainSegment(x + i * step_width, 'platform', step_width, 40 * (level + 1), level))
    
    def update(self, camera_x, difficulty=0):
        """Update terrain, generate new segments as needed"""
        self.camera_x = camera_x
        self.difficulty = difficulty
        
        # Remove segments that are far behind camera
        self.segments = [s for s in self.segments if s.x + s.width > camera_x - 200]
        
        # Generate new segments ahead
        if self.segments:
            last_segment = self.segments[-1]
            while last_segment.x + last_segment.width < camera_x + 1000:
                x = last_segment.x + last_segment.width
                self._add_next_segment(x)
                last_segment = self.segments[-1]
    
    def get_ground_y(self, x):
        """Get ground Y position at given X coordinate"""
        for segment in self.segments:
            if segment.x <= x < segment.x + segment.width:
                if segment.segment_type == 'flat':
                    return self.ground_height
                elif segment.segment_type == 'platform':
                    # Platform at specific level
                    return self.ground_height - segment.height
                elif segment.segment_type == 'mountain':
                    # Calculate slope position on mountain
                    rel_x = x - segment.x
                    if rel_x < segment.width / 2:
                        # Going up
                        progress = rel_x / (segment.width / 2)
                        return self.ground_height - (progress * segment.height)
                    else:
                        # Going down
                        progress = (rel_x - segment.width / 2) / (segment.width / 2)
                        return self.ground_height - segment.height + (progress * segment.height)
                else:  # pit
                    return self.ground_height + 200  # Far below (player falls)
        return self.ground_height
    
    def is_platform_edge_ahead(self, x, current_y, look_ahead=20):
        """Check if there's a platform edge ahead that's higher than current position"""
        current_ground = self.get_ground_y(x)
        ahead_ground = self.get_ground_y(x + look_ahead)
        
        # If ground ahead is significantly higher (more than 20 pixels), it's a blocking edge
        if ahead_ground < current_ground - 20:
            return True
        return False
    
    def draw(self, screen, camera_x, screen_width, screen_height):
        """Draw terrain segments"""
        for segment in self.segments:
            screen_x = segment.x - camera_x
            
            # Only draw if visible
            if screen_x + segment.width < -100 or screen_x > screen_width + 100:
                continue
            
            if segment.segment_type == 'flat':
                # Draw flat ground
                pygame.draw.rect(screen, (34, 139, 34), 
                               (screen_x, self.ground_height, segment.width, screen_height - self.ground_height))
            elif segment.segment_type == 'platform':
                # Draw platform at specific height
                platform_y = self.ground_height - segment.height
                platform_color = (100, 160, 100) if segment.level == 0 else (80, 140, 80) if segment.level == 1 else (60, 120, 60)
                pygame.draw.rect(screen, platform_color,
                               (screen_x, platform_y, segment.width, screen_height - platform_y))
                # Platform top edge
                pygame.draw.rect(screen, (70, 100, 70),
                               (screen_x, platform_y, segment.width, 5))
            elif segment.segment_type == 'mountain':
                # Draw mountain as triangle
                points = [
                    (screen_x, self.ground_height),
                    (screen_x + segment.width / 2, self.ground_height - segment.height),
                    (screen_x + segment.width, self.ground_height),
                    (screen_x + segment.width, screen_height),
                    (screen_x, screen_height)
                ]
                pygame.draw.polygon(screen, (100, 160, 100), points)
                # Mountain outline
                pygame.draw.lines(screen, (70, 120, 70), False, points[:3], 3)
            else:  # pit
                # Draw pit edges
                pygame.draw.rect(screen, (139, 69, 19), 
                               (screen_x - 5, self.ground_height, 5, 30))
                pygame.draw.rect(screen, (139, 69, 19), 
                               (screen_x + segment.width, self.ground_height, 5, 30))

class Box:
    def __init__(self, x, y, box_type='good'):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 0  # Boxes stay in place (world scrolls)
        self.box_type = box_type  # 'good' or 'bad'
        
        if box_type == 'good':
            self.color = (255, 215, 0)  # Yellow/gold box
            self.outline_color = (218, 165, 32)
        else:  # bad
            self.color = (20, 20, 20)  # Black box
            self.outline_color = (50, 50, 50)  # Dark gray outline
        
    def update(self):
        pass  # Boxes are stationary in world coordinates
        
    def draw(self, screen):
        # Draw box
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Draw box outline
        pygame.draw.rect(screen, self.outline_color, (self.x, self.y, self.width, self.height), 3)
        
        if self.box_type == 'good':
            # Draw big "!" exclamation mark
            font = pygame.font.Font(None, 36)
            text = font.render("!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
            screen.blit(text, text_rect)
        else:
            # Draw skull
            # Skull head (circle)
            pygame.draw.circle(screen, (200, 200, 200), (int(self.x + self.width // 2), int(self.y + 10)), 8)
            # Eye sockets (black)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x + self.width // 2 - 3), int(self.y + 9)), 2)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x + self.width // 2 + 3), int(self.y + 9)), 2)
            # Nose (small triangle)
            pygame.draw.polygon(screen, (0, 0, 0), [
                (self.x + self.width // 2, self.y + 12),
                (self.x + self.width // 2 - 2, self.y + 15),
                (self.x + self.width // 2 + 2, self.y + 15)
            ])
            # Crossbones (X shape)
            pygame.draw.line(screen, (200, 200, 200), (self.x + 7, self.y + 20), (self.x + 23, self.y + 26), 2)
            pygame.draw.line(screen, (200, 200, 200), (self.x + 23, self.y + 20), (self.x + 7, self.y + 26), 2)
    
    def check_collision(self, player):
        """Check if box collides with player"""
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GROUND_HEIGHT = 500

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GREEN = (34, 139, 34)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Sky's The Limit - Corgi Runner")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player(200, GROUND_HEIGHT)
        self.player.velocity_x = self.player.run_speed  # Start running right
        self.score = 0
        self.boxes_caught = 0
        self.game_speed = 5
        self.boxes = []
        self.box_spawn_timer = 0
        self.box_spawn_interval = 80  # Spawn more frequently
        self.terrain = Terrain(GROUND_HEIGHT)
        self.camera_x = 0
        self.player_world_x = 200  # Player's actual X position in world
        self.game_over = False
        self.difficulty_level = 0  # Tracks game difficulty progression
        self.game_time = 0  # Track game time in frames
        
    def handle_events(self):
        """Handle game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_over:
                    # Restart game
                    self.__init__()
                else:
                    # Click to jump
                    self.player.jump()
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    # Restart with any key
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.__init__()
                else:
                    # Space or Up arrow to jump (only if not already flying)
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        if not self.player.is_flying:
                            # Check if player has flying power
                            if self.player.super_power and self.player.current_superpower and self.player.current_superpower.get("can_fly"):
                                self.player.fly()
                            else:
                                self.player.jump()
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        # Handle continuous key state for flying
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            # Keep flying if magic power is active
            if self.player.super_power and self.player.current_superpower and self.player.current_superpower.get("can_fly"):
                self.player.fly()
        else:
            # Stop flying when key is released
            if self.player.is_flying:
                self.player.stop_flying()
            
        # Update player world position (only when not blocked)
        if not self.player.blocked_by_edge:
            self.player_world_x += self.player.velocity_x
        
        # Camera follows player (keep player in left third of screen)
        target_camera_x = self.player_world_x - 200
        self.camera_x = max(0, target_camera_x)
        
        # Get ground height at player position
        ground_y = self.terrain.get_ground_y(self.player_world_x + self.player.width / 2)
        
        # Check if there's a blocking platform edge ahead
        is_blocked = self.terrain.is_platform_edge_ahead(
            self.player_world_x + self.player.width,
            self.player.y,
            look_ahead=10
        )
        
        # Flying ignores blocking
        if self.player.is_flying:
            is_blocked = False
        
        # Update player with terrain-aware ground height and blocked state
        self.player.update(ground_y, SCREEN_WIDTH, is_blocked, self.player_world_x)
        
        # Clear blocked state if player successfully jumped over or is in the air
        if self.player.is_jumping or self.player.is_flying or self.player.y < ground_y - 10:
            self.player.blocked_by_edge = False
        
        # Check if player fell into pit
        if self.player.y > SCREEN_HEIGHT:
            # Game over
            self.game_over = True
            return
        
        # Track game time
        self.game_time += 1
        
        # Calculate difficulty based on game time (60 FPS)
        # 0-20 seconds = early (0-2)
        # 20-60 seconds = mid (3-5) 
        # 60-120 seconds = late (6-10)
        time_in_seconds = self.game_time / FPS
        if time_in_seconds < 20:
            # Early game: 0-20 seconds
            self.difficulty_level = int(time_in_seconds / 10)  # 0-2
        elif time_in_seconds < 60:
            # Mid game: 20-60 seconds
            self.difficulty_level = 2 + int((time_in_seconds - 20) / 13)  # 3-5
        else:
            # Late game: 60-120 seconds
            self.difficulty_level = min(10, 5 + int((time_in_seconds - 60) / 12))  # 6-10
        
        # Gradually increase player speed (max 1.8x base speed over 2 minutes)
        speed_multiplier = 1.0 + min(0.8, time_in_seconds / 120)  # Reaches 1.8x at 2 minutes
        self.player.base_speed_multiplier = speed_multiplier
        
        # Update terrain with difficulty
        self.terrain.update(self.camera_x, self.difficulty_level)
        
        # Spawn boxes in world coordinates
        self.box_spawn_timer += 1
        if self.box_spawn_timer >= self.box_spawn_interval:
            self.box_spawn_timer = 0
            # Spawn ahead of camera at ground level
            x_pos = self.camera_x + random.randint(500, 800)
            # Place box at jump height (slightly above ground)
            y_pos = GROUND_HEIGHT - random.randint(40, 120)
            
            # Bad box spawn rate increases with difficulty
            if self.difficulty_level < 2:
                # First 20 seconds - 10% bad boxes
                box_type = 'good' if random.random() < 0.9 else 'bad'
            elif self.difficulty_level < 5:
                # 20-60 seconds - 20% bad boxes
                box_type = 'good' if random.random() < 0.8 else 'bad'
            elif self.difficulty_level < 8:
                # 60-100 seconds - 30% bad boxes
                box_type = 'good' if random.random() < 0.7 else 'bad'
            else:
                # 100-120 seconds - 40% bad boxes
                box_type = 'good' if random.random() < 0.6 else 'bad'
            
            self.boxes.append(Box(x_pos, y_pos, box_type))
        
        # Update boxes
        for box in self.boxes[:]:
            box.update()
            
            # Check collision with projectiles
            for projectile in self.player.projectiles[:]:
                # Convert projectile world position for collision check
                if projectile.check_collision_with_box(box):
                    if box.box_type == 'bad':
                        # Projectile destroys bad box
                        if box in self.boxes:
                            self.boxes.remove(box)
                        projectile.active = False
                        if projectile in self.player.projectiles:
                            self.player.projectiles.remove(projectile)
                        break  # Exit projectile loop for this box
                    elif box.box_type == 'good' and projectile.projectile_type == 'arrow':
                        # Arrow hits good box - give points but no superpower
                        if box in self.boxes:
                            self.boxes.remove(box)
                        self.boxes_caught += 1
                        self.score = self.boxes_caught
                        projectile.active = False
                        if projectile in self.player.projectiles:
                            self.player.projectiles.remove(projectile)
                        break
            
            # Check collision with player (using world coordinates)
            box_screen_x = box.x - self.camera_x
            if (box_screen_x < self.player.x + self.player.width and
                box_screen_x + box.width > self.player.x and
                box.y < self.player.y + self.player.height and
                box.y + box.height > self.player.y):
                
                if box.box_type == 'good':
                    # Good box - give superpower
                    self.boxes.remove(box)
                    self.boxes_caught += 1
                    self.score = self.boxes_caught  # Score = boxes caught
                    self.player.activate_super_power()
                else:
                    # Bad box - game over
                    self.boxes.remove(box)
                    self.game_over = True
                    return
            
            # Remove boxes that are behind camera
            elif box.x < self.camera_x - 100:
                self.boxes.remove(box)
    
    def draw(self):
        """Draw everything on screen"""
        # Draw sky
        self.screen.fill(SKY_BLUE)
        
        # Draw terrain
        self.terrain.draw(self.screen, self.camera_x, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Draw boxes (with camera offset)
        for box in self.boxes:
            box_screen_x = box.x - self.camera_x
            temp_box = Box(box_screen_x, box.y, box.box_type)
            temp_box.draw(self.screen)
        
        # Draw player (at fixed screen position)
        self.player.draw(self.screen)
        
        # Draw projectiles
        self.player.draw_projectiles(self.screen, self.camera_x)
        
        # Draw superpower indicator
        if self.player.super_power and self.player.current_superpower:
            power_name = self.player.current_superpower["name"]
            power_color = self.player.current_superpower["color"]
            time_left = self.player.super_power_timer / FPS
            
            # Draw power name with background
            font_large = pygame.font.Font(None, 48)
            font_small = pygame.font.Font(None, 32)
            power_text = font_large.render(power_name, True, power_color)
            time_text = font_small.render(f"{time_left:.1f}s", True, WHITE)
            
            # Background box
            bg_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 50, 300, 80)
            bg_surface = pygame.Surface((300, 80), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (0, 0, 0, 150), (0, 0, 300, 80), border_radius=10)
            pygame.draw.rect(bg_surface, power_color + (200,), (0, 0, 300, 80), 3, border_radius=10)
            self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
            
            # Text
            power_rect = power_text.get_rect(center=(SCREEN_WIDTH // 2, 70))
            time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 105))
            self.screen.blit(power_text, power_rect)
            self.screen.blit(time_text, time_rect)
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        
        # Draw boxes caught
        boxes_text = font.render(f"Boxes: {self.boxes_caught}", True, BLACK)
        self.screen.blit(boxes_text, (10, 50))
        
        # Draw game time
        time_minutes = int(self.game_time / FPS / 60)
        time_seconds = int((self.game_time / FPS) % 60)
        time_text = font.render(f"Time: {time_minutes}:{time_seconds:02d}", True, BLACK)
        self.screen.blit(time_text, (10, 90))
        
        # Draw super power indicator
        if self.player.super_power and self.player.current_superpower:
            power_font = pygame.font.Font(None, 36)
            power_name = self.player.current_superpower["name"]
            power_color = self.player.current_superpower["color"]
            power_text = power_font.render(power_name, True, power_color)
            text_rect = power_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            # Add pulsing effect
            glow_surface = pygame.Surface((text_rect.width + 20, text_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, power_color + (100,), (0, 0, text_rect.width + 20, text_rect.height + 10), border_radius=10)
            self.screen.blit(glow_surface, (text_rect.x - 10, text_rect.y - 5))
            self.screen.blit(power_text, text_rect)
        
        # Draw instructions
        if self.score < FPS * 5:  # Show for first 5 seconds
            inst_font = pygame.font.Font(None, 22)
            inst_text1 = inst_font.render("Press SPACE to JUMP over mountains and pits!", True, BLACK)
            inst_text2 = inst_font.render("Catch YELLOW (!) boxes, avoid BLACK SKULL boxes!", True, (255, 0, 0))
            text_rect1 = inst_text1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            text_rect2 = inst_text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            self.screen.blit(inst_text1, text_rect1)
            self.screen.blit(inst_text2, text_rect2)
        
        # Draw game over screen
        if self.game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Game over text
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("GAME OVER!", True, (255, 50, 50))
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(game_over_text, text_rect)
            
            # Final stats
            stats_font = pygame.font.Font(None, 36)
            score_text = stats_font.render(f"Final Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(score_text, score_rect)
            
            distance_text = stats_font.render(f"Distance: {int(self.player_world_x)}", True, WHITE)
            distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            self.screen.blit(distance_text, distance_rect)
            
            boxes_text = stats_font.render(f"Boxes Caught: {self.boxes_caught}", True, WHITE)
            boxes_rect = boxes_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(boxes_text, boxes_rect)
            
            # Restart instructions
            restart_font = pygame.font.Font(None, 32)
            restart_text = restart_font.render("Press SPACE to Restart", True, (255, 255, 0))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

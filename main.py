import pygame
import sys
from player import Player

# Initialize Pygame
pygame.init()

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
        pygame.display.set_caption("Sky's The Limit - Runner Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player(100, GROUND_HEIGHT)
        self.score = 0
        self.game_speed = 5
        
    def handle_events(self):
        """Handle game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Click to jump
                self.player.jump()
            if event.type == pygame.KEYDOWN:
                # Space or Up arrow to jump
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.player.jump()
    
    def update(self):
        """Update game state"""
        self.player.update(GROUND_HEIGHT)
        self.score += 1
    
    def draw(self):
        """Draw everything on screen"""
        # Draw sky
        self.screen.fill(SKY_BLUE)
        
        # Draw ground
        pygame.draw.rect(self.screen, GREEN, (0, GROUND_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score // FPS}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        
        # Draw instructions
        if self.score < FPS * 3:  # Show for first 3 seconds
            inst_font = pygame.font.Font(None, 28)
            inst_text = inst_font.render("Click or Press SPACE to Jump!", True, BLACK)
            text_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(inst_text, text_rect)
        
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

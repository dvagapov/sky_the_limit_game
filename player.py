import pygame

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.velocity_y = 0
        self.gravity = 0.8
        self.jump_strength = -15
        self.is_jumping = False
        self.color = (255, 100, 100)  # Red color for player
        
    def jump(self):
        """Make the player jump"""
        if not self.is_jumping:
            self.velocity_y = self.jump_strength
            self.is_jumping = True
    
    def update(self, ground_height):
        """Update player position and physics"""
        # Apply gravity
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        
        # Check if player is on ground
        if self.y >= ground_height - self.height:
            self.y = ground_height - self.height
            self.velocity_y = 0
            self.is_jumping = False
    
    def draw(self, screen):
        """Draw the player on screen"""
        # Draw player as a rectangle
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw eyes
        eye_color = (255, 255, 255)
        eye_pupil = (0, 0, 0)
        
        # Left eye
        pygame.draw.circle(screen, eye_color, (int(self.x + 12), int(self.y + 15)), 5)
        pygame.draw.circle(screen, eye_pupil, (int(self.x + 13), int(self.y + 15)), 2)
        
        # Right eye
        pygame.draw.circle(screen, eye_color, (int(self.x + 28), int(self.y + 15)), 5)
        pygame.draw.circle(screen, eye_pupil, (int(self.x + 29), int(self.y + 15)), 2)

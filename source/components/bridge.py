import pygame as pg

class Bridge(pg.sprite.Sprite):
    def __init__(self, points):
        super().__init__()
        self.points = points
        self.segments = []
        self.create_segments()

    def create_segments(self):
        """Create rectangular segments for each point pair to represent the bridge."""
        for i in range(0, len(self.points) - 1, 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            width = abs(x2 - x1)
            height = abs(y2 - y1) or 1  # Ensure height is non-zero
            rect = pg.Rect(min(x1, x2), min(y1, y2), width, height)
            self.segments.append(rect)

    def update_points(self, new_points):
        """Update bridge points and recreate segments only if necessary."""
        if self.points == new_points:
            return  # Skip updates if points are unchanged
        self.points = new_points
        self.segments.clear()
        self.create_segments()

    def check_collision(self, player):
        """Efficiently check if the player collides with any relevant segment."""
        player_rect = player.rect
        for segment in self.segments:
            if player_rect.colliderect(segment):
                return segment
        return None


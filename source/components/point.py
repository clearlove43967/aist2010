import pygame as pg
from .. import setup, tools
from .. import constants as c

import pygame

class Point(pygame.sprite.Sprite):
    def __init__(self, x, y, radius=6, color=(255, 0, 0)):
        super().__init__()
        self.radius = radius
        self.color = color
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)  # 使用透明背景
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # 在表面上绘制圆
        self.rect = self.image.get_rect(center=(x, y))  # 设置位置
        self.trace=[]
        self.fill=True

    def update(self, x, y):
        self.rect.x=x
        self.rect.y=y
        self.trace.append((x,y))  # 记录y坐标反转

        if len(self.trace) > c.SCREEN_WIDTH:
            self.trace.pop(0)

    def draw_point(self,level):
        self.image.fill((0, 0, 0, 0))  # 清空表面
        pygame.draw.circle(level, self.color, (self.rect.x, self.rect.y), self.radius)  # 重新绘制
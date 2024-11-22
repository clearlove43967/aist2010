import pygame as pg
from .. import setup, tools
from .. import constants as c

class Button(pg.sprite.Sprite):
    def __init__(self, x, y, type, frame_rect_list, scatter=None, name=c.MAP_BUTTON):
        pg.sprite.Sprite.__init__(self)

        self.frames = []
        #self.frame_index = 0
        self.load_frames(frame_rect_list)
        self.is_pressed = False
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        #self.animation_timer = 0
        self.type = type
        self.scatters=scatter
        self.name = name


    def load_frames(self,frame_rect_list):
        sheet = setup.GFX['item_objects']
        #frame_rect_list = [(0, 143, 15, 15), (0, 64, 16, 16)]
        for frame_rect in frame_rect_list:
            self.frames.append(tools.get_image(sheet, *frame_rect,
                                               c.COLOR_TYPE_ORANGE, c.BRICK_SIZE_MULTIPLIER))

    def press(self):
        self.image = self.frames[1]
        if not self.is_pressed:
            self.is_pressed = True

    def release(self):
        self.image = self.frames[0]
        if self.is_pressed:
            self.is_pressed = False



class ScatterButton(Button):
    def __init__(self, x, y, type, frame_rect_list, scatter, name=c.MAP_BUTTON):
        super().__init__(x, y, type, frame_rect_list, scatter, name)
        self.load_frames(frame_rect_list)
        self.scatters=pg.sprite.Group()
        self.generate_scatter(scatter)

    def generate_scatter(self,positions):
        for position in positions:
            self.scatters.add()


import pygame as pg
from .. import setup, tools
from source.components import powerup
from .. import constants as c

class Button(pg.sprite.Sprite):
    def __init__(self, x, y, frame_rect_list, type=None, dist=None, group=None, name=c.MAP_BUTTON):
        pg.sprite.Sprite.__init__(self)

        self.frames = []
        #self.frame_index = 0
        self.type = type
        self.load_frames(frame_rect_list)
        self.is_pressed = False
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.group = group
        self.name = name
        self.dist = dist


    def load_frames(self, frame_rect_list):
        # cannon
        if self.type == 3:
            sheet = setup.GFX['item_objects(1)']
            frame_rect_list = [(287, 171, 33, 18), (287, 171, 33, 18)]
            for frame_rect in frame_rect_list:
                self.frames.append(tools.get_image(sheet, *frame_rect,
                                                   c.BLACK, c.BRICK_SIZE_MULTIPLIER))
        elif self.type == 2:
            sheet = setup.GFX['item_objects(1)']
            frame_rect_list = [(287, 189, 33, 18), (287, 189, 33, 18)]
            for frame_rect in frame_rect_list:
                self.frames.append(tools.get_image(sheet, *frame_rect,
                                                   c.BLACK, c.BRICK_SIZE_MULTIPLIER))
        else:
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

    def shoot_pitch_bullet(self, pitch, powerup_group):
        powerup_group.add(powerup.FireBall(self.rect.right, self.rect.y, False, pitch))

    def shoot_volume_bullet(self, powerup_group):
        powerup_group.add(powerup.FireMisso(self.rect.right, self.rect.y, True))

class ScatterButton(Button):
    def __init__(self, x, y, type, dist, frame_rect_list, scatter, name=c.MAP_BUTTON):
        super().__init__(x, y, type, dist, frame_rect_list, scatter, name)
        self.load_frames(frame_rect_list)
        self.scatters = pg.sprite.Group()
        self.generate_scatter(scatter)

    def generate_scatter(self, positions):
        for position in positions:
            self.scatters.add()



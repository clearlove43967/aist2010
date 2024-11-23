__author__ = 'marble_xu'

import pygame as pg
from .. import setup, tools
from .. import constants as c
from . import stuff


class Powerup(stuff.Stuff):
    def __init__(self, x, y, sheet, image_rect_list, scale):
        stuff.Stuff.__init__(self, x, y, sheet, image_rect_list, scale)
        self.rect.centerx = x
        self.state = c.REVEAL
        self.y_vel = -1
        self.x_vel = 0
        self.direction = c.RIGHT
        self.box_height = y
        self.gravity = 1
        self.max_y_vel = 8
        self.animate_timer = 0

    def update_position(self, level):
        self.rect.x += self.x_vel
        self.check_x_collisions(level)

        self.rect.y += self.y_vel
        self.check_y_collisions(level)

        if self.rect.x <= 0:
            self.kill()
        elif self.rect.y > (level.viewport.bottom):
            self.kill()

    def check_x_collisions(self, level):
        sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
                                       level.brick_group, level.box_group)
        sprite = pg.sprite.spritecollideany(self, sprite_group)
        if sprite:
            if self.direction == c.RIGHT:
                self.rect.right = sprite.rect.left - 1
                self.direction = c.LEFT
            elif self.direction == c.LEFT:
                self.rect.left = sprite.rect.right
                self.direction = c.RIGHT
            self.x_vel = self.speed if self.direction == c.RIGHT else -1 * self.speed
            if sprite.name == c.MAP_BRICK:
                self.x_vel = 0

    def check_y_collisions(self, level):
        sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
                                       level.brick_group, level.box_group)

        sprite = pg.sprite.spritecollideany(self, sprite_group)
        if sprite:
            self.y_vel = 0
            self.rect.bottom = sprite.rect.top
            self.state = c.SLIDE
        level.check_is_falling(self)

    def animation(self):
        self.image = self.frames[self.frame_index]


class Mushroom(Powerup):
    def __init__(self, x, y):
        Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                         [(0, 0, 16, 16)], c.SIZE_MULTIPLIER)
        self.type = c.TYPE_MUSHROOM
        self.speed = 2

    def update(self, game_info, level):
        if self.state == c.REVEAL:
            self.rect.y += self.y_vel
            if self.rect.bottom <= self.box_height:
                self.rect.bottom = self.box_height
                self.y_vel = 0
                self.state = c.SLIDE
        elif self.state == c.SLIDE:
            self.x_vel = self.speed if self.direction == c.RIGHT else -1 * self.speed
        elif self.state == c.FALL:
            if self.y_vel < self.max_y_vel:
                self.y_vel += self.gravity

        if self.state == c.SLIDE or self.state == c.FALL:
            self.update_position(level)
        self.animation()


class LifeMushroom(Mushroom):
    def __init__(self, x, y):
        Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                         [(16, 0, 16, 16)], c.SIZE_MULTIPLIER)
        self.type = c.TYPE_LIFEMUSHROOM
        self.speed = 2


class FireFlower(Powerup):
    def __init__(self, x, y):
        frame_rect_list = [(0, 32, 16, 16), (16, 32, 16, 16),
                           (32, 32, 16, 16), (48, 32, 16, 16)]
        Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                         frame_rect_list, c.SIZE_MULTIPLIER)
        self.type = c.TYPE_FIREFLOWER

    def update(self, game_info, *args):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.state == c.REVEAL:
            self.rect.y += self.y_vel
            if self.rect.bottom <= self.box_height:
                self.rect.bottom = self.box_height
                self.y_vel = 0
                self.state = c.RESTING

        if (self.current_time - self.animate_timer) > 30:
            if self.frame_index < 3:
                self.frame_index += 1
            else:
                self.frame_index = 0
            self.animate_timer = self.current_time

        self.animation()


class Star(Powerup):
    def __init__(self, x, y):
        frame_rect_list = [(1, 48, 15, 16), (17, 48, 15, 16),
                           (33, 48, 15, 16), (49, 48, 15, 16)]
        Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                         frame_rect_list, c.SIZE_MULTIPLIER)
        self.type = c.TYPE_STAR
        self.gravity = .4
        self.speed = 5

    def update(self, game_info, level):
        self.current_time = game_info[c.CURRENT_TIME]
        if self.state == c.REVEAL:
            self.rect.y += self.y_vel
            if self.rect.bottom <= self.box_height:
                self.rect.bottom = self.box_height
                self.y_vel = -2
                self.state = c.BOUNCING
        elif self.state == c.BOUNCING:
            self.y_vel += self.gravity
            self.x_vel = self.speed if self.direction == c.RIGHT else -1 * self.speed

        if (self.current_time - self.animate_timer) > 30:
            if self.frame_index < 3:
                self.frame_index += 1
            else:
                self.frame_index = 0
            self.animate_timer = self.current_time

        if self.state == c.BOUNCING:
            self.update_position(level)
        self.animation()

    def check_y_collisions(self, level):
        sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
                                       level.brick_group, level.box_group)

        sprite = pg.sprite.spritecollideany(self, sprite_group)

        if sprite:
            if self.rect.top > sprite.rect.top:
                self.y_vel = 5
            else:
                self.rect.bottom = sprite.rect.y
                self.y_vel = -5


class FireBall(Powerup):
    def __init__(self, x, y, facing_right, pitch):
        # first 3 Frames are flying, last 4 frames are exploding
        print("pitch is " + pitch)
        self.fireball_type = pitch
        if pitch == c.DO:
            frame_rect_list = [(255, 191, 9, 9), (263, 191, 9, 9),
                               (255, 199, 9, 9), (263, 199, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.RE:
            frame_rect_list = [(255, 209, 9, 9), (263, 209, 9, 9),
                               (255, 217, 9, 9), (263, 217, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.MI:
            frame_rect_list = [(255, 227, 9, 9), (263, 227, 9, 9),
                               (255, 235, 9, 9), (263, 235, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.FA:
            frame_rect_list = [(255, 263, 9, 9), (263, 263, 9, 9),
                               (255, 271, 9, 9), (263, 271, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.SOL:
            frame_rect_list = [(255, 281, 9, 9), (263, 281, 9, 9),
                               (255, 289, 9, 9), (263, 289, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.LA:
            frame_rect_list = [(255, 299, 9, 9), (263, 299, 9, 9),
                               (255, 307, 9, 9), (263, 307, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)
        elif pitch == c.TI:
            frame_rect_list = [(255, 245, 9, 9), (263, 245, 9, 9),
                               (255, 253, 9, 9), (263, 253, 9, 9),
                               (112, 144, 16, 16), (112, 160, 16, 16),
                               (112, 176, 16, 16)]
            Powerup.__init__(self, x, y, setup.GFX[c.ITEM_SHEET2], frame_rect_list, c.SIZE_MULTIPLIER)

        self.type = c.TYPE_FIREBALL
        self.y_vel = 10
        self.gravity = .9
        self.state = c.FLYING
        self.rect.right = x
        if facing_right:
            self.direction = c.RIGHT
            self.x_vel = 12
        else:
            self.direction = c.LEFT
            self.x_vel = -12

    def update(self, game_info, level):
        self.current_time = game_info[c.CURRENT_TIME]
        print(self.frame_index)
        if self.state == c.FLYING or self.state == c.BOUNCING:
            self.y_vel += self.gravity
            if (self.current_time - self.animate_timer) > 200:
                self.frame_index = (self.frame_index + 1) % 4
                self.animate_timer = self.current_time
            self.update_position(level)
        elif self.state == c.EXPLODING:
            if (self.current_time - self.animate_timer) > 50:
                if self.frame_index < 6:
                    self.frame_index += 1
                else:
                    self.kill()
                self.animate_timer = self.current_time

        self.animation()

    def check_x_collisions(self, level):
        sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
                                       level.brick_group, level.box_group)
        sprite = pg.sprite.spritecollideany(self, sprite_group)
        if sprite:
            self.change_to_explode()

    def check_y_collisions(self, level):
        sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
                                       level.brick_group, level.box_group)

        sprite = pg.sprite.spritecollideany(self, sprite_group)
        enemy = pg.sprite.spritecollideany(self, level.enemy_group)
        if sprite:
            if self.rect.top > sprite.rect.top:
                self.change_to_explode()
            else:
                self.rect.bottom = sprite.rect.y
                self.y_vel = -8
                if self.direction == c.RIGHT:
                    self.x_vel = 15
                else:
                    self.x_vel = -15
                self.state = c.BOUNCING
        elif enemy:
            if (enemy.name != c.FIRESTICK):
                level.update_score(100, enemy, 0)
                level.move_to_dying_group(level.enemy_group, enemy)
                enemy.start_death_jump(self.direction)
            self.change_to_explode()

    def change_to_explode(self):
        self.frame_index = 4
        self.state = c.EXPLODING



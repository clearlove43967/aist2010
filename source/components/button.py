import pygame as pg
from .. import setup, tools
from .. import constants as c
import numpy as np
import pyaudio
from scipy.fftpack import fft
import time

class Button(pg.sprite.Sprite):
    def __init__(self, x, y, type, group=None, name=c.MAP_BUTTON):
        pg.sprite.Sprite.__init__(self)

        self.frames = []
        #self.frame_index = 0
        self.load_frames()
        self.is_collision = False
        self.is_pressed = False
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        #self.animation_timer = 0
        self.state = c.RESTING
        self.type = type
        self.group = group
        self.name = name

        self.frequencies = []
        self.recording = False
        self.start_time = None  # 开始时间

    def load_frames(self):
        sheet = setup.GFX['item_objects']
        frame_rect_list = [(0, 143, 15, 15), (0, 64, 16, 16),]
        for frame_rect in frame_rect_list:
            self.frames.append(tools.get_image(sheet, *frame_rect,
                                               c.COLOR_TYPE_ORANGE, c.BRICK_SIZE_MULTIPLIER))

    def press(self):
        self.image = self.frames[1]
        if not self.recording:  # 只有在不录音时才开始录音
            self.recording = True

    def release(self):
        self.image = self.frames[0]
        if self.recording:
            self.recording = False  # 停止录音



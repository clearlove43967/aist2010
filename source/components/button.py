import pygame as pg
from .. import setup, tools
from .. import constants as c
import numpy as np
import pyaudio
from scipy.fftpack import fft
import time

RATE = 44100  # 采样率
CHUNK = 1024  # 每次读取的音频块大小
WHITE = (255, 255, 255)
LIGHT_BLUE = (173, 216, 230)  # 淡蓝色
LINE_COLOR = (0, 0, 255)  # 蓝色线条
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

# 丢弃前几帧数据以稳定麦克风
for _ in range(5):
    stream.read(CHUNK)

frequencies = []
recording = False
start_time = None  # 开始时间

# 获取音调频率的函数


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



        #if xx  不同类型的按钮效果不同


    def release(self):
        self.image = self.frames[0]
        if self.recording:
            self.recording = False  # 停止录音



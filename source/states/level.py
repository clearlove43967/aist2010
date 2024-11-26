__author__ = 'marble_xu'
import time
import os
import json
import pyaudio
from scipy.fftpack import fft
import numpy as np
import pygame as pg
from .. import setup, tools
from .. import constants as c
from ..components import info, stuff, player, brick, box, enemy, powerup, coin, button, point,bridge



class Level(tools.State):
    def __init__(self):
        tools.State.__init__(self)
        self.player = None
        self.if_display_freq = False

    def startup(self, current_time, persist):
        self.game_info = persist
        self.persist = self.game_info
        self.game_info[c.CURRENT_TIME] = current_time
        self.death_timer = 0
        self.castle_timer = 0
        self.button_is_pressed=False
        
        self.moving_score_list = []
        self.overhead_info = info.Info(self.game_info, c.LEVEL)
        self.load_map()
        self.setup_background()
        self.setup_maps()
        self.ground_group = self.setup_collide(c.MAP_GROUND)
        self.step_group = self.setup_collide(c.MAP_STEP)

        self.setup_buttons()
        self.setup_scatters()
        self.setup_pipe()
        self.setup_slider()
        self.setup_static_coin()
        self.setup_brick_and_box()
        self.setup_player()
        self.setup_enemies()
        self.setup_checkpoints()
        self.setup_flagpole()
        self.setup_sprite_groups()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=c.RATE, input=True,
                                  frames_per_buffer=c.CHUNK)
        # 丢弃前几帧数据以稳定麦克风
        for _ in range(25):
            self.stream.read(c.CHUNK)
        self.recording = False
        self.gen_flag = False
        self.frequencies=[]
        self.point = None
        self.bridge_points = []  # Initial empty list for bridge points
        self.bridge = bridge.Bridge(self.bridge_points)
        self.bridge_group = pg.sprite.Group(self.bridge)

        self.current_freq = 0  # 初始化滑块为 None

    def load_map(self):
        map_file = 'level_' + str(self.game_info[c.LEVEL_NUM]) + '.json'
        file_path = os.path.join('source', 'data', 'maps', map_file)
        f = open(file_path)
        self.map_data = json.load(f)
        f.close()

    def setup_buttons(self):
        self.button_group = pg.sprite.Group()
        frame_rect_list = [(0, 64, 16, 16), (48, 64, 16, 16)]
        if c.MAP_BUTTON in self.map_data:
            for data in self.map_data[c.MAP_BUTTON]:
                if c.BUTTON_GROUP in data:
                    self.button_group.add(button.Button(data['x'], data['y'], frame_rect_list, data['type'],data['dist'], data['group']))
                else:
                    self.button_group.add(button.Button(data['x'], data['y'], frame_rect_list, data['type'],data['dist']))

    def setup_scatters(self):
        self.scatter_group_list=[]
        frame_rect_list = [(304, 48, 16, 16), (288, 48, 16, 16)]
        index = 0
        for data in self.map_data[c.MAP_SCATTER]:
            group = pg.sprite.Group()
            for item in data[str(index)]:
                scatter = button.Button(item['x'], item['y'], frame_rect_list,group=index)
                scatter.release()
                group.add(scatter)
            self.scatter_group_list.append(group)
            index += 1

    def setup_background(self):
        img_name = self.map_data[c.MAP_IMAGE]
        self.background = setup.GFX[img_name]
        self.bg_rect = self.background.get_rect()
        self.background = pg.transform.scale(self.background, 
                                    (int(self.bg_rect.width*c.BACKGROUND_MULTIPLER),
                                    int(self.bg_rect.height*c.BACKGROUND_MULTIPLER)))
        self.bg_rect = self.background.get_rect()

        self.level = pg.Surface((self.bg_rect.w, self.bg_rect.h)).convert()
        self.viewport = setup.SCREEN.get_rect(bottom=self.bg_rect.bottom)

    # draw freq
    def display_frequency(self, surface, freq):
        """在屏幕左上角显示频率值，颜色基于音高频率范围"""
        font = pg.font.Font(None, 20)  # 使用默认字体，字体大小为20

        # 音高频率和颜色的映射
        pitch_data = [
            {"pitch": "Do", "freq": 261.6, "color": (255, 0, 0)},  # 红色
            {"pitch": "Re", "freq": 293.6, "color": (165, 42, 42)},  # 棕色
            {"pitch": "Mi", "freq": 329.6, "color": (0, 255, 0)},  # 绿色
            {"pitch": "Fa", "freq": 349.2, "color": (128, 128, 128)},  # 灰色
            {"pitch": "So", "freq": 392.0, "color": (255, 0, 255)},  # 紫红色
            {"pitch": "La", "freq": 440.0, "color": (255, 255, 0)},  # 黄色
            {"pitch": "Ti", "freq": 493.8, "color": (0, 0, 255)}  # 蓝色
        ]

        color = (255, 255, 255)  # 默认颜色为白色
        pitch_label = "Unknown"  # 默认标签

        # 判断频率在哪个音高范围内
        for data in pitch_data:
            if data["freq"] - c.TOLERANCE <= freq <= data["freq"] + c.TOLERANCE:
                color = data["color"]  # 设置对应颜色
                pitch_label = data["pitch"]  # 设置对应音高标签
                break

        # 显示频率值和音高标签
        freq_text = f"{pitch_label}: {freq:.2f} Hz"  # 显示音高和频率
        text_surface = font.render(freq_text, True, color)  # 用对应颜色渲染文字
        surface.blit(text_surface, (10, 10))  # 绘制在屏幕左上角

    def display_pitch_range(self, surface):
        font = pg.font.Font(None, 20)
        # 红色 (Red)
        do_text = "Do: 261.6Hz"
        do_surface = font.render(do_text, True, (255, 0, 0))  # 红色
        surface.blit(do_surface, (10, 40))  # 第一行的位置

        # 棕色 (Brown)
        re_text = "Re: 293.6Hz"
        re_surface = font.render(re_text, True, (165, 42, 42))  # 棕色
        surface.blit(re_surface, (10, 60))  # 第二行的位置

        # 绿色 (Green)
        mi_text = "Mi: 329.6Hz"
        mi_surface = font.render(mi_text, True, (0, 255, 0))  # 绿色
        surface.blit(mi_surface, (10, 80))  # 第三行的位置

        # 灰色 (Gray)
        fa_text = "Fa: 349.2Hz"
        fa_surface = font.render(fa_text, True, (128, 128, 128))  # 灰色
        surface.blit(fa_surface, (10, 100))  # 第四行的位置

        # 紫红色 (Magenta)
        so_text = "So: 392.0Hz"
        so_surface = font.render(so_text, True, (255, 0, 255))  # 紫红色
        surface.blit(so_surface, (10, 120))  # 第五行的位置

        # 黄色 (Yellow)
        la_text = "La: 440.0Hz"
        la_surface = font.render(la_text, True, (255, 255, 0))  # 黄色
        surface.blit(la_surface, (10, 140))  # 第六行的位置

        # 蓝色 (Blue)
        ti_text = "Ti: 493.8Hz"
        ti_surface = font.render(ti_text, True, (0, 0, 255))  # 蓝色
        surface.blit(ti_surface, (10, 160))  # 第七行的位置

    def setup_maps(self):
        self.map_list = []
        if c.MAP_MAPS in self.map_data:
            for data in self.map_data[c.MAP_MAPS]:
                self.map_list.append((data['start_x'], data['end_x'], data['player_x'], data['player_y']))
            self.start_x, self.end_x, self.player_x, self.player_y = self.map_list[0]
        else:
            self.start_x = 0
            self.end_x = self.bg_rect.w
            self.player_x = 110
            self.player_y = c.GROUND_HEIGHT

    def change_map(self, index, type):
        self.start_x, self.end_x, self.player_x, self.player_y = self.map_list[index]
        self.viewport.x = self.start_x
        if type == c.CHECKPOINT_TYPE_MAP:
            self.player.rect.x = self.viewport.x + self.player_x
            self.player.rect.bottom = self.player_y
            self.player.state = c.STAND
        elif type == c.CHECKPOINT_TYPE_PIPE_UP:
            self.player.rect.x = self.viewport.x + self.player_x
            self.player.rect.bottom = c.GROUND_HEIGHT
            self.player.state = c.UP_OUT_PIPE
            self.player.up_pipe_y = self.player_y

    def setup_collide(self, name):
        group = pg.sprite.Group()
        if name in self.map_data:
            for data in self.map_data[name]:
                group.add(stuff.Collider(data['x'], data['y'], 
                        data['width'], data['height'], name))
        return group

    def setup_pipe(self):
        self.pipe_group = pg.sprite.Group()
        if c.MAP_PIPE in self.map_data:
            for data in self.map_data[c.MAP_PIPE]:
                self.pipe_group.add(stuff.Pipe(data['x'], data['y'],
                    data['width'], data['height'], data['type']))

    def setup_slider(self):
        self.slider_group = pg.sprite.Group()
        if c.MAP_SLIDER in self.map_data:
            for data in self.map_data[c.MAP_SLIDER]:
                if c.VELOCITY in data:
                    vel = data[c.VELOCITY]
                else:
                    vel = 1
                self.slider_group.add(stuff.Slider(data['x'], data['y'], data['num'],
                    data['direction'], data['range_start'], data['range_end'], vel))

    def setup_static_coin(self):
        self.static_coin_group = pg.sprite.Group()
        if c.MAP_COIN in self.map_data:
            for data in self.map_data[c.MAP_COIN]:
                self.static_coin_group.add(coin.StaticCoin(data['x'], data['y']))

    def setup_brick_and_box(self):
        self.coin_group = pg.sprite.Group()
        self.powerup_group = pg.sprite.Group()
        self.brick_group = pg.sprite.Group()
        self.brickpiece_group = pg.sprite.Group()

        if c.MAP_BRICK in self.map_data:
            for data in self.map_data[c.MAP_BRICK]:
                brick.create_brick(self.brick_group, data, self)
        
        self.box_group = pg.sprite.Group()
        if c.MAP_BOX in self.map_data:
            for data in self.map_data[c.MAP_BOX]:
                if data['type'] == c.TYPE_COIN:
                    self.box_group.add(box.Box(data['x'], data['y'], data['type'], self.coin_group))
                else:
                    self.box_group.add(box.Box(data['x'], data['y'], data['type'], self.powerup_group))
            
    def setup_player(self):
        if self.player is None:
            self.player = player.Player(self.game_info[c.PLAYER_NAME])
        else:
            self.player.restart()
        self.player.rect.x = self.viewport.x + self.player_x
        self.player.rect.bottom = self.player_y
        if c.DEBUG:
            self.player.rect.x = self.viewport.x + c.DEBUG_START_X
            self.player.rect.bottom = c.DEBUG_START_y
        self.viewport.x = self.player.rect.x - 110

    def setup_enemies(self):
        self.enemy_group_list = []
        index = 0
        for data in self.map_data[c.MAP_ENEMY]:
            group = pg.sprite.Group()
            for item in data[str(index)]:
                group.add(enemy.create_enemy(item, self))
            self.enemy_group_list.append(group)
            index += 1
            
    def setup_checkpoints(self):
        self.checkpoint_group = pg.sprite.Group()
        for data in self.map_data[c.MAP_CHECKPOINT]:
            if c.ENEMY_GROUPID in data:
                enemy_groupid = data[c.ENEMY_GROUPID]
            else:
                enemy_groupid = 0
            if c.MAP_INDEX in data:
                map_index = data[c.MAP_INDEX]
            else:
                map_index = 0
            self.checkpoint_group.add(stuff.Checkpoint(data['x'], data['y'], data['width'], 
                data['height'], data['type'], enemy_groupid, map_index))
    
    def setup_flagpole(self):
        self.flagpole_group = pg.sprite.Group()
        if c.MAP_FLAGPOLE in self.map_data:
            for data in self.map_data[c.MAP_FLAGPOLE]:
                if data['type'] == c.FLAGPOLE_TYPE_FLAG:
                    sprite = stuff.Flag(data['x'], data['y'])
                    self.flag = sprite
                elif data['type'] == c.FLAGPOLE_TYPE_POLE:
                    sprite = stuff.Pole(data['x'], data['y'])
                else:
                    sprite = stuff.PoleTop(data['x'], data['y'])
                self.flagpole_group.add(sprite)

    def setup_sprite_groups(self):
        self.dying_group = pg.sprite.Group()
        self.enemy_group = pg.sprite.Group()
        self.shell_group = pg.sprite.Group()
        self.ground_step_pipe_group = pg.sprite.Group(self.ground_group,
                        self.pipe_group, self.step_group, self.slider_group)
        self.player_group = pg.sprite.Group(self.player)


        
    def update(self, surface, keys, current_time):
        self.game_info[c.CURRENT_TIME] = self.current_time = current_time
        self.handle_states(keys)
        self.draw(surface)
        if self.if_display_freq:
            self.display_pitch_range(surface)
            self.display_frequency(surface, self.current_freq)

    def handle_states(self, keys):
        self.update_all_sprites(keys)
    
    def update_all_sprites(self, keys):
        if self.player.dead:
            self.player.update(keys, self.game_info, self.powerup_group)
            if self.current_time - self.death_timer > 3000:
                self.update_game_info()
                self.done = True
        elif self.player.state == c.IN_CASTLE:
            self.player.update(keys, self.game_info, None)
            self.flagpole_group.update()
            if self.current_time - self.castle_timer > 2000:
                self.update_game_info()
                self.done = True
        elif self.in_frozen_state():
            self.player.update(keys, self.game_info, None)
            self.check_checkpoints()
            self.update_viewport()
            self.overhead_info.update(self.game_info, self.player)
            for score in self.moving_score_list:
                score.update(self.moving_score_list)
        else:
            self.player.update(keys, self.game_info, self.powerup_group)
            self.flagpole_group.update()
            self.check_checkpoints()
            self.slider_group.update()
            self.static_coin_group.update(self.game_info)
            self.enemy_group.update(self.game_info, self)
            self.shell_group.update(self.game_info, self)
            self.brick_group.update()
            self.box_group.update(self.game_info)
            self.powerup_group.update(self.game_info, self)
            self.coin_group.update(self.game_info)
            self.brickpiece_group.update()
            self.dying_group.update(self.game_info, self)
            self.update_player_position()
            self.check_for_player_death()
            self.update_viewport()
            self.overhead_info.update(self.game_info, self.player)
            for score in self.moving_score_list:
                score.update(self.moving_score_list)

    def check_checkpoints(self):
        checkpoint = pg.sprite.spritecollideany(self.player, self.checkpoint_group)
        
        if checkpoint:
            if checkpoint.type == c.CHECKPOINT_TYPE_ENEMY:
                group = self.enemy_group_list[checkpoint.enemy_groupid]
                self.enemy_group.add(group)
            elif checkpoint.type == c.CHECKPOINT_TYPE_FLAG:
                self.player.state = c.FLAGPOLE
                if self.player.rect.bottom < self.flag.rect.y:
                    self.player.rect.bottom = self.flag.rect.y
                self.flag.state = c.SLIDE_DOWN
                self.update_flag_score()
            elif checkpoint.type == c.CHECKPOINT_TYPE_CASTLE:
                self.player.state = c.IN_CASTLE
                self.player.x_vel = 0
                self.castle_timer = self.current_time
                self.flagpole_group.add(stuff.CastleFlag(8745, 322))
            elif (checkpoint.type == c.CHECKPOINT_TYPE_MUSHROOM and
                    self.player.y_vel < 0):
                mushroom_box = box.Box(checkpoint.rect.x, checkpoint.rect.bottom - 40,
                                c.TYPE_LIFEMUSHROOM, self.powerup_group)
                mushroom_box.start_bump(self.moving_score_list)
                self.box_group.add(mushroom_box)
                self.player.y_vel = 7
                self.player.rect.y = mushroom_box.rect.bottom
                self.player.state = c.FALL
            elif checkpoint.type == c.CHECKPOINT_TYPE_PIPE:
                self.player.state = c.WALK_AUTO
            elif checkpoint.type == c.CHECKPOINT_TYPE_PIPE_UP:
                self.change_map(checkpoint.map_index, checkpoint.type)
            elif checkpoint.type == c.CHECKPOINT_TYPE_MAP:
                self.change_map(checkpoint.map_index, checkpoint.type)
            elif checkpoint.type == c.CHECKPOINT_TYPE_BOSS:
                self.player.state = c.WALK_AUTO
            checkpoint.kill()

    def check_press_number(self):
        num=0
        for group in self.scatter_group_list:
            for scatter in group:
                if scatter.is_pressed:
                    num+=1
        return num

    def update_flag_score(self):
        base_y = c.GROUND_HEIGHT - 80
        
        y_score_list = [(base_y, 100), (base_y-120, 400),
                    (base_y-200, 800), (base_y-320, 2000),
                    (0, 5000)]
        for y, score in y_score_list:
            if self.player.rect.y > y:
                self.update_score(score, self.flag)
                break
        
    def update_player_position(self):
        if self.player.state == c.UP_OUT_PIPE:
            return

        self.player.rect.x += round(self.player.x_vel)
        if self.player.rect.x < self.start_x:
            self.player.rect.x = self.start_x
        elif self.player.rect.right > self.end_x:
            self.player.rect.right = self.end_x
        self.check_player_x_collisions()
        
        if not self.player.dead:
            self.player.rect.y += round(self.player.y_vel)
            self.check_player_y_collisions()

    def update_bridge(self, new_points):
        self.bridge.update_points(new_points)

    def check_player_x_collisions(self):
        ground_step_pipe = pg.sprite.spritecollideany(self.player, self.ground_step_pipe_group)
        brick = pg.sprite.spritecollideany(self.player, self.brick_group)
        box = pg.sprite.spritecollideany(self.player, self.box_group)
        enemy = pg.sprite.spritecollideany(self.player, self.enemy_group)
        shell = pg.sprite.spritecollideany(self.player, self.shell_group)
        powerup = pg.sprite.spritecollideany(self.player, self.powerup_group)
        coin = pg.sprite.spritecollideany(self.player, self.static_coin_group)
        button = pg.sprite.spritecollideany(self.player, self.button_group)
        bridge_segment = self.bridge.check_collision(self.player)

        if button and not self.recording:
            self.player.message=True
            self.recording_start(button)

        if self.recording and not button:
            self.recording_stop()

        if button and self.point.trace[0][0] - self.point.trace[-1][0] < int(button.dist) and self.recording and not self.player.message:
            x, y = button.rect.x, button.rect.y
            group = button.group
            type = button.type
            # cannon
            if button.type == 2:
                self.cannon_audio(button, self.powerup_group)
            else:
                self.handle_audio_data(x, y, type, group)
        

        if box:
            self.adjust_player_for_x_collisions(box)
        elif brick:
            self.adjust_player_for_x_collisions(brick)
        elif ground_step_pipe:
            if (ground_step_pipe.name == c.MAP_PIPE and
                ground_step_pipe.type == c.PIPE_TYPE_HORIZONTAL):
                return
            self.adjust_player_for_x_collisions(ground_step_pipe)
        elif powerup:
            if powerup.type == c.TYPE_MUSHROOM:
                self.update_score(1000, powerup, 0)
                if not self.player.big:
                    self.player.y_vel = -1
                    self.player.state = c.SMALL_TO_BIG
            elif powerup.type == c.TYPE_FIREFLOWER:
                self.update_score(1000, powerup, 0)
                if not self.player.big:
                    self.player.state = c.SMALL_TO_BIG
                elif self.player.big and not self.player.fire:
                    self.player.state = c.BIG_TO_FIRE
            elif powerup.type == c.TYPE_STAR:
                self.update_score(1000, powerup, 0)
                self.player.invincible = True
            elif powerup.type == c.TYPE_LIFEMUSHROOM:
                self.update_score(500, powerup, 0)
                self.game_info[c.LIVES] += 1
            if powerup.type != c.TYPE_FIREBALL:
                powerup.kill()
        elif enemy:
            if self.player.invincible:
                self.update_score(100, enemy, 0)
                self.move_to_dying_group(self.enemy_group, enemy)
                direction = c.RIGHT if self.player.facing_right else c.LEFT
                enemy.start_death_jump(direction)
            elif self.player.hurt_invincible:
                pass
            elif self.player.big:
                self.player.y_vel = -1
                self.player.state = c.BIG_TO_SMALL
            else:
                self.player.start_death_jump(self.game_info)
                self.death_timer = self.current_time
        elif shell:
            if shell.state == c.SHELL_SLIDE:
                if self.player.invincible:
                    self.update_score(200, shell, 0)
                    self.move_to_dying_group(self.shell_group, shell)
                    direction = c.RIGHT if self.player.facing_right else c.LEFT
                    shell.start_death_jump(direction)
                elif self.player.hurt_invincible:
                    pass
                elif self.player.big:
                    self.player.y_vel = -1
                    self.player.state = c.BIG_TO_SMALL
                else:
                    self.player.start_death_jump(self.game_info)
                    self.death_timer = self.current_time
            else:
                self.update_score(400, shell, 0)
                if self.player.rect.x < shell.rect.x:
                    self.player.rect.left = shell.rect.x 
                    shell.direction = c.RIGHT
                    shell.x_vel = 10
                else:
                    self.player.rect.x = shell.rect.left
                    shell.direction = c.LEFT
                    shell.x_vel = -10
                shell.rect.x += shell.x_vel * 4
                shell.state = c.SHELL_SLIDE
        elif coin:
            self.update_score(100, coin, 1)
            coin.kill()
        elif bridge_segment:
            if bridge_segment.height > 3 * bridge_segment.width:
                self.player.y_vel = 0
                self.player.x_vel = 0
                if self.player.rect.x < bridge_segment.x:
                    self.player.rect.right = bridge_segment.left - 1
                else:
                    self.player.rect.left = bridge_segment.right + 1

    def adjust_player_for_x_collisions(self, collider):
        if collider.name == c.MAP_SLIDER:
            return
        if self.player.rect.x < collider.rect.x:
            self.player.rect.right = collider.rect.left
        else:
            self.player.rect.left = collider.rect.right
        self.player.x_vel = 0

    def check_player_y_collisions(self):
        ground_step_pipe = pg.sprite.spritecollideany(self.player, self.ground_step_pipe_group)
        bridge_segment = self.bridge.check_collision(self.player)
        enemy = pg.sprite.spritecollideany(self.player, self.enemy_group)
        shell = pg.sprite.spritecollideany(self.player, self.shell_group)

        # decrease runtime delay: when player is on the ground, don't check brick and box
        if self.player.rect.bottom < c.GROUND_HEIGHT:
            brick = pg.sprite.spritecollideany(self.player, self.brick_group)
            box = pg.sprite.spritecollideany(self.player, self.box_group)
            brick, box = self.prevent_collision_conflict(brick, box)
        else:
            brick, box = False, False

        if bridge_segment:
            # Adjust player position for the bridge
            if self.player.rect.bottom < c.GROUND_HEIGHT:
                self.player.rect.bottom = bridge_segment.top
                self.player.y_vel = 0
            self.player.state = c.WALK
            if bridge_segment.height > 3 * bridge_segment.width:
                self.player.y_vel = 0
                self.player.x_vel = 0
                if self.player.rect.x < bridge_segment.x:
                    self.player.rect.right = bridge_segment.left - 1
                else:
                    self.player.rect.left = bridge_segment.right + 1

        if box:
            self.adjust_player_for_y_collisions(box)
        elif brick:
            self.adjust_player_for_y_collisions(brick)
        elif ground_step_pipe:
            self.adjust_player_for_y_collisions(ground_step_pipe)
        elif enemy:
            if self.player.invincible:
                self.update_score(100, enemy, 0)
                self.move_to_dying_group(self.enemy_group, enemy)
                direction = c.RIGHT if self.player.facing_right else c.LEFT
                enemy.start_death_jump(direction)
            elif (enemy.name == c.PIRANHA or
                  enemy.name == c.FIRESTICK or
                  enemy.name == c.FIRE_KOOPA or
                  enemy.name == c.FIRE):
                pass
            elif self.player.y_vel > 0:
                self.update_score(100, enemy, 0)
                enemy.state = c.JUMPED_ON
                if enemy.name == c.GOOMBA:
                    self.move_to_dying_group(self.enemy_group, enemy)
                elif enemy.name == c.KOOPA or enemy.name == c.FLY_KOOPA:
                    self.enemy_group.remove(enemy)
                    self.shell_group.add(enemy)

                self.player.rect.bottom = enemy.rect.top
                self.player.state = c.JUMP
                self.player.y_vel = -7
        elif shell:
            if self.player.y_vel > 0:
                if shell.state != c.SHELL_SLIDE:
                    shell.state = c.SHELL_SLIDE
                    if self.player.rect.centerx < shell.rect.centerx:
                        shell.direction = c.RIGHT
                        shell.rect.left = self.player.rect.right + 5
                    else:
                        shell.direction = c.LEFT
                        shell.rect.right = self.player.rect.left - 5
        self.check_is_falling(self.player)
        self.check_if_player_on_IN_pipe()

    def prevent_collision_conflict(self, sprite1, sprite2):
        if sprite1 and sprite2:
            distance1 = abs(self.player.rect.centerx - sprite1.rect.centerx)
            distance2 = abs(self.player.rect.centerx - sprite2.rect.centerx)
            if distance1 < distance2:
                sprite2 = False
            else:
                sprite1 = False
        return sprite1, sprite2

    def adjust_player_for_y_collisions(self, sprite):
        if self.player.rect.top > sprite.rect.top:
            if sprite.name == c.MAP_BRICK:
                self.check_if_enemy_on_brick_box(sprite)
                if sprite.state == c.RESTING:
                    if self.player.big and sprite.type == c.TYPE_NONE:
                        sprite.change_to_piece(self.dying_group)
                    else:
                        if sprite.type == c.TYPE_COIN:
                            self.update_score(200, sprite, 1)
                        sprite.start_bump(self.moving_score_list)
            elif sprite.name == c.MAP_BOX:
                self.check_if_enemy_on_brick_box(sprite)
                if sprite.state == c.RESTING:
                    if sprite.type == c.TYPE_COIN:
                        self.update_score(200, sprite, 1)
                    sprite.start_bump(self.moving_score_list)
            elif (sprite.name == c.MAP_PIPE and
                  sprite.type == c.PIPE_TYPE_HORIZONTAL):
                return

            self.player.y_vel = 7
            self.player.rect.top = sprite.rect.bottom
            self.player.state = c.FALL
        else:
            self.player.y_vel = 0
            self.player.rect.bottom = sprite.rect.top
            if self.player.state == c.FLAGPOLE:
                self.player.state = c.WALK_AUTO
            elif self.player.state == c.END_OF_LEVEL_FALL:
                self.player.state = c.WALK_AUTO
            else:
                self.player.state = c.WALK

    
    def check_if_enemy_on_brick_box(self, brick):
        brick.rect.y -= 5
        enemy = pg.sprite.spritecollideany(brick, self.enemy_group)
        if enemy:
            self.update_score(100, enemy, 0)
            self.move_to_dying_group(self.enemy_group, enemy)
            if self.player.rect.centerx > brick.rect.centerx:
                direction = c.RIGHT
            else:
                direction = c.LEFT
            enemy.start_death_jump(direction)
        brick.rect.y += 5

    def in_frozen_state(self):
        if (self.player.state == c.SMALL_TO_BIG or
            self.player.state == c.BIG_TO_SMALL or
            self.player.state == c.BIG_TO_FIRE or
            self.player.state == c.DEATH_JUMP or
            self.player.state == c.DOWN_TO_PIPE or
            self.player.state == c.UP_OUT_PIPE):
            return True
        else:
            return False

    def check_is_falling(self, sprite):
        sprite.rect.y += 1
        check_group = pg.sprite.Group(self.ground_step_pipe_group,
                            self.brick_group, self.box_group)
        
        if pg.sprite.spritecollideany(sprite, check_group) is None and self.bridge.check_collision(sprite) is None:
            if (sprite.state == c.WALK_AUTO or
                sprite.state == c.END_OF_LEVEL_FALL):
                sprite.state = c.END_OF_LEVEL_FALL
            elif (sprite.state != c.JUMP and 
                sprite.state != c.FLAGPOLE and
                not self.in_frozen_state()):
                sprite.state = c.FALL
        sprite.rect.y -= 1
    
    def check_for_player_death(self):
        if (self.player.rect.y > c.SCREEN_HEIGHT or
            self.overhead_info.time <= 0):
            self.player.start_death_jump(self.game_info)
            self.death_timer = self.current_time

    def check_if_player_on_IN_pipe(self):
        '''check if player is on the pipe which can go down in to it '''
        self.player.rect.y += 1
        pipe = pg.sprite.spritecollideany(self.player, self.pipe_group)
        if pipe and pipe.type == c.PIPE_TYPE_IN:
            if (self.player.crouching and
                self.player.rect.x < pipe.rect.centerx and
                self.player.rect.right > pipe.rect.centerx):
                self.player.state = c.DOWN_TO_PIPE
        self.player.rect.y -= 1

    def update_game_info(self):
        if self.player.dead:
            self.persist[c.LIVES] -= 1

        if self.persist[c.LIVES] == 0:
            self.next = c.GAME_OVER
        elif self.overhead_info.time == 0:
            self.next = c.TIME_OUT
        elif self.player.dead:
            self.next = c.LOAD_SCREEN
        else:
            self.game_info[c.LEVEL_NUM] += 1
            self.next = c.LOAD_SCREEN

    def update_viewport(self):
        third = self.viewport.x + self.viewport.w // 3
        player_center = self.player.rect.centerx
        
        if (self.player.x_vel > 0 and 
            player_center >= third and
            self.viewport.right < self.end_x):
            self.viewport.x += round(self.player.x_vel)
        elif self.player.x_vel < 0 and self.viewport.x > self.start_x:
            self.viewport.x += round(self.player.x_vel)
    
    def move_to_dying_group(self, group, sprite):
        group.remove(sprite)
        self.dying_group.add(sprite)
        
    def update_score(self, score, sprite, coin_num=0):
        self.game_info[c.SCORE] += score
        self.game_info[c.COIN_TOTAL] += coin_num
        x = sprite.rect.x
        y = sprite.rect.y - 10
        self.moving_score_list.append(stuff.Score(x, y, score))

    def recording_start(self, button):
        self.recording = True
        self.if_display_freq = True
        self.gen_flag = False
        self.frequencies = []

        button.press()

        self.bridge_points = []
        self.bridge = bridge.Bridge(self.bridge_points)

        self.point = point.Point(button.rect.x, button.rect.y)
        if button.group:
            for scatter in self.scatter_group_list[button.group]:
                scatter.release()

    def recording_stop(self):
        for button in self.button_group:
            button.release()
        #if self.stream is not None:
        #    self.stream.stop_stream()  # 停止音频流
        #    self.stream.close()  # 关闭音频流
        #    self.p.terminate()
        self.recording = False
        self.if_display_freq = False
        self.frequencies = []


    def handle_audio_data(self,button_x, button_y, type,group):
        data = np.frombuffer(self.stream.read(c.CHUNK), dtype=np.int16) / 32768.0  # 归一化
        pitch = get_pitch(data)  # 获取当前音调频率
        self.frequencies.append(pitch)

        alpha = 0.03  # 平滑因子，值越小越平滑
        if len(self.frequencies) > 1:
            smoothed_pitch = alpha * pitch + (1 - alpha) * self.frequencies[-2]
        else:
            smoothed_pitch = pitch  # 初始值直接使用当前频率

        self.frequencies[-1] = smoothed_pitch

        window_size = 5  # 平滑窗口大小（可根据需要调整）
        if len(self.frequencies) >= window_size:
            smoothed_pitch = np.mean(self.frequencies[-window_size:])  # 取窗口内平均值
        else:
            smoothed_pitch = pitch  # 如果不足窗口大小，则保持原值

        if len(self.frequencies) > c.SCREEN_WIDTH:
            self.frequencies.pop(0)
        self.point.trace.clear()
        for i, freq in enumerate(self.frequencies):
            x = i + button_x + 50
            y = c.SCREEN_HEIGHT - int((freq / 1500) * c.SCREEN_HEIGHT)-64       # 2000Hz 作为频率上限的缩放
            self.point.update(x, y)
            if type == 0:
                self.point.fill = True
                if len(self.point.trace) > self.player_x:
                    new_points = []
                    for i, freq in enumerate(self.frequencies):
                        x = i + button_x + 50
                        y = c.SCREEN_HEIGHT - int((freq / 1500) * c.SCREEN_HEIGHT) - 64
                        new_points.append((x, y))
                    self.bridge_points = new_points
                    self.update_bridge(self.bridge_points)

            if type == 1:
                print(type,group)
                scatter=None
                all_scatters_collision_flag=True
                self.point.fill=False
                scatter = pg.sprite.spritecollideany(self.point, self.scatter_group_list[group])
                if scatter:
                    if not scatter.is_pressed:
                        self.update_score(100, scatter)
                    scatter.press()
                    for scatter in self.scatter_group_list[group]:
                        if not scatter.is_pressed:
                            all_scatters_collision_flag = False
                    if all_scatters_collision_flag and not self.gen_flag:
                        self.gen_flag=True
                        for data in self.map_data[c.MAP_NEWBRICK][group][str(group)]:
                            brick.create_brick(self.brick_group, data, self)



    def cannon_audio(self, button, powerup_group):
        # 静态变量初始化
        if not hasattr(self, '_last_shoot_time'):
            self._last_shoot_time = 0  # 初始化上一次射击时间为0

        data = np.frombuffer(self.stream.read(c.CHUNK), dtype=np.int16) / 32768.0  # 归一化

        freq = get_pitch(data)
        self.current_freq = freq
        detected_pitch = check_frequency_match(freq)
        print(detected_pitch)

        # 获取当前时间
        current_time = time.time()

        # 检查时间间隔
        if detected_pitch:
            if current_time - self._last_shoot_time > 0.5:  # 如果时间间隔大于0.5秒
                button.shoot_bullet(detected_pitch, powerup_group)  # 执行射击动作
                self._last_shoot_time = current_time  # 更新上一次发射时间
            else:
                print("Shoot is cooling down.")  # 输出冷却提示
        return

    def draw(self, surface):
        self.level.blit(self.background, self.viewport, self.viewport)
        self.powerup_group.draw(self.level)
        self.brick_group.draw(self.level)
        self.box_group.draw(self.level)
        self.coin_group.draw(self.level)
        self.dying_group.draw(self.level)
        self.brickpiece_group.draw(self.level)
        self.flagpole_group.draw(self.level)
        self.shell_group.draw(self.level)
        self.enemy_group.draw(self.level)
        self.player_group.draw(self.level)
        self.static_coin_group.draw(self.level)
        self.slider_group.draw(self.level)
        self.pipe_group.draw(self.level)
        '''
        if self.player.message:
            message_x=self.player.rect.x+200
            message_y=self.player.rect.y-200
            box_rect = pg.Rect(message_x,message_y, 400, 200)
            pg.draw.rect(self.level, c.GRAY, box_rect)
            pg.draw.rect(self.level, c.BLACK, box_rect, 3)
        '''

        self.button_group.draw(self.level)
        for group in self.scatter_group_list:
            group.draw(self.level)

        if self.point:
            if self.point.trace and self.point.fill:
                fill_points = self.point.trace + [(self.point.trace[-1][0], c.SCREEN_HEIGHT), (self.point.trace[0][0], c.SCREEN_HEIGHT)]
                pg.draw.polygon(self.level, c.YELLOW, fill_points)

            # 画出曲线
            if len(self.point.trace) > 1:
                pg.draw.lines(self.level, c.ORANGE, False, self.point.trace, 2)
            self.point.draw_point(self.level)

        for score in self.moving_score_list:
            score.draw(self.level)
        if c.DEBUG:
            self.ground_step_pipe_group.draw(self.level)
            self.checkpoint_group.draw(self.level)

        surface.blit(self.level, (0, 0), self.viewport)
        self.overhead_info.draw(surface)


def get_pitch(data):
    fft_data = fft(data)
    freqs = np.fft.fftfreq(len(fft_data), 1 / c.RATE)
    magnitude = np.abs(fft_data)

    # 找到主频率
    peak_idx = np.argmax(magnitude)
    peak_freq = abs(freqs[peak_idx])

    return peak_freq


def get_frequency(self, data, rate):
    """calculate frequency"""
    n = len(data)
    # Hanning window to decrease leakage
    window = np.hanning(n)
    data = data * window
    fft = np.fft.rfft(data)
    frequencies = np.fft.rfftfreq(n, 1 / rate)
    magnitude = np.abs(fft)
    # get the freq with maximum magnitude
    peak_index = np.argmax(magnitude)
    return frequencies[peak_index]


def check_frequency_match(freq):
    """
    using microphone to get freq
    target_frequency
    tolerance: error range
    """
    frequency_dict = {
        261.6: 'do',
        293.6: 're',
        329.6: 'mi',
        349.2: 'fa',
        392: 'sol',
        440: 'la',
        493.8: 'ti'
    }
    # init pyaudio
    detected_pitch = None
    for pitch in frequency_dict.keys():
        if pitch - c.TOLERANCE <= freq <= pitch + c.TOLERANCE:
            print(f"detect target freq {freq:.2f} Hz，Done！")
            detected_pitch = pitch
            break
    if detected_pitch:
        return frequency_dict[detected_pitch]
    else:
        return None

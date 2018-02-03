import os
import math
from enum import Enum
import itertools
import pygame
from PIL import Image

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

CHARACTER_STATES = Enum('Character State', ['stopped', 'running', 'breaking', 'jumping', 'crouching'])
CHARACTER_STYLES = Enum('Character Style', ['big', 'small', 'fire'])

IMAGES_DICT = {CHARACTER_STYLES.big:
                   {CHARACTER_STATES.stopped: ['mario0.png'],
                    CHARACTER_STATES.running: ['mario1.png', 'mario2.png', 'mario3.png'],
                    CHARACTER_STATES.breaking: ['mario4.png'],
                    CHARACTER_STATES.jumping: ['mario5.png'],
                    CHARACTER_STATES.crouching: ['mario6.png'],
                    },
               CHARACTER_STYLES.small:
                   {CHARACTER_STATES.stopped: ['mario0_mini.png'],
                    CHARACTER_STATES.running: ['mario1_mini.png', 'mario2_mini.png', 'mario3_mini.png'],
                    CHARACTER_STATES.breaking: ['mario4_mini.png'],
                    CHARACTER_STATES.jumping: ['mario5_mini.png'],
                    CHARACTER_STATES.crouching: ['mario6_mini.png'],
                    },
               }
GRAVITY = 1
GROUND_LEVEL = 293

def repeat_image(image_path, nrepeat=2):
    image = Image.open(image_path)

    width, height = image.size[0], image.size[1]

    total_width = width * nrepeat

    new_im = Image.new(image.mode, (total_width, height))

    x_offset = 0
    for i in range(0, nrepeat):
        new_im.paste(image, (x_offset, 0))
        x_offset += width

    return new_im


def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(pygame.compat.geterror())
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image


def load_sound(name):
    class NoneSound:
        def play(self): pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)

    sound = pygame.mixer.Sound(fullname)

    return sound

class CycleCounter(itertools.cycle):
    def __init__(self, iterable):
        self.iterable = iterable

    def __iter__(self):
        return itertools.cycle.__iter__(self)

class FixedObjectSprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()

    def pan(self, pan_amount):
        if self.rect.right + pan_amount < self.area.right:
            pan_amount = 600 + pan_amount
        elif self.rect.left + pan_amount > self.area.left:
            pan_amount = pan_amount - 600
        else:
            move = pan_amount

        self.rect.move_ip((pan_amount, 0))


class LevelBackdrop(FixedObjectSprite):
    def __init__(self):
        FixedObjectSprite.__init__(self)
        self.image_path = os.path.join(data_dir, 'supermariobackground.jpg')
        self._load_image()
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.move = 4

    def _load_image(self):
        image = repeat_image(self.image_path, 2)
        mode = image.mode
        size = image.size
        data = image.tobytes()
        self.image = pygame.image.fromstring(data, size, mode).convert()


class LuckyBlock(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.image = load_image('luckyblock.png', (250, 250, 250))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (300, 210)

    def pan(self, pan_amount):
        self.rect.move_ip((pan_amount, 0))


class CharacterSprite(pygame.sprite.DirtySprite):
    def __init__(self, start_position):
        pygame.sprite.DirtySprite.__init__(self)  # call Sprite initializer
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self._load_images()
        self.layer = 1
        self._direction = 1
        self._state = CHARACTER_STATES.stopped
        self._sub_states = itertools.cycle(range(len(self._images[self._state])))
        self._sub_state = next(self._sub_states)
        self.rect = self.image.get_rect()
        self.rect.midbottom = start_position
        self.velocity = [0, 0]
        self.acceleration = [0, GRAVITY]
        self._cycle_cadence = 2  # higher is slower
        self._wait_cycle = itertools.cycle(range(self._cycle_cadence))

    def _load_images(self):
        self._images = {}
        self._state_cycles = {}


        for k, v in IMAGES_DICT[self._style].items():
            self._images[k] = [load_image(filename, -1) for filename in v]
            if len(v) > 1:
                self._state_cycles[k] = itertools.cycle(range(len(v)))

    def _flip_images(self):
        for k, v in self._images.items():
            self._images[k] = [pygame.transform.flip(x, 1, 0) for x in v]

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if self._direction != direction:
            self._direction = direction
            self._flip_images()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state

    def _cycle_sub_state(self):
        sub_states = self._state_cycles.get(self.state, False):
        if
            if next(self._wait_cycle) == self._cycle_cadence - 1:
                sub_states = self._state_cycles[self.state]
                self._sub_state = next(sub_states)
        else:
            self._sub_state = 0

    @property
    def image(self):
        try:
            return self._images[self.state][self._sub_state]
        except:
            print('')

    def update(self):
        pass


class Mario(CharacterSprite):
    def __init__(self, start_position=(0,0), style=CHARACTER_STYLES.big ):
        self._style = style
        CharacterSprite.__init__(self, start_position)
        self.running_speed = 4
        self.jumping_speed = 20

    def run(self, direction):
        self.direction = direction
        if self.velocity[1] == 0:
            self.state = CHARACTER_STATES.running
            self.velocity[0] = self.running_speed * direction
        else:
            self.velocity[0] = self.running_speed * direction / 2

    def crouch(self):
        if self.velocity[1] == 0:
            self.state = CHARACTER_STATES.crouching


    def jump(self):
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.jumping
            self.velocity[1] = -self.jumping_speed

    def stop(self):
        if self.velocity[1] == 0:
            self.state = CHARACTER_STATES.stopped
            self.velocity[0] = 0

    def _update_vectors(self):
        orig_pos = self.rect
        self.rect = self.image.get_rect(midbottom=orig_pos.midbottom)
        self.rect.move_ip(self.velocity)
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

    def _update_state(self):
        if self.state == CHARACTER_STATES.jumping:
            if self.rect.bottom == GROUND_LEVEL:
                if abs(self.velocity[0]) > 0:
                    self.state = CHARACTER_STATES.running
                else:
                    self.state = CHARACTER_STATES.stopped

    def update(self):
        self._cycle_sub_state()
        self._update_vectors()
        self._update_state()

class Ground(pygame.sprite.DirtySprite):
    def __init__(self, ground_level):
        pygame.sprite.DirtySprite.__init__(self)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.image = pygame.Surface((self.area.width, self.area.height - ground_level))
        self.image.set_colorkey(self.image.get_at((0,0)), pygame.RLEACCEL)
        self.rect = self.image.get_rect()
        self.rect.top = ground_level



class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(0)
        self.screen = pygame.display.set_mode((600, 337))
        self.area = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.level_backdrop = LevelBackdrop()
        self.mario = Mario((50, GROUND_LEVEL))
        self.lucky_block = LuckyBlock()
        self.ground = Ground(GROUND_LEVEL)
        self.allsprites = pygame.sprite.RenderPlain( self.level_backdrop, self.ground, self.mario, self.lucky_block,)
        pygame.display.flip()
        self.paused = False
        self.run()

    def run(self):
        going = True
        while going:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    going = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.paused = 1 - self.paused
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                    self.mario.run(1)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                    self.mario.run(-1)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                    self.mario.jump()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                    self.mario.crouch()
                elif event.type == pygame.KEYUP:
                    self.mario.stop()

            keys = pygame.key.get_pressed()

            if not self.paused:
                self.allsprites.update()

                if self.mario.rect.colliderect(self.ground.rect):
                    self.mario.rect.bottom = self.ground.rect.top
                    self.mario.velocity[1] = 0

                if self.mario.rect.colliderect(self.lucky_block.rect):
                    t1_pos = self.mario.rect
                    dx = self.mario.velocity[0]
                    dy = self.mario.velocity[1]
                    t0_pos = self.mario.rect.move((-dx, -dy))

                    collision_direction = [0, 0] # where [1,0] means from the left, [-1,0] from the right etc.
                    # movement along one axis at the time
                    test_pos = t0_pos.move((dx, 0))
                    if test_pos.colliderect(self.lucky_block.rect):
                        if dx > 0:
                            self.mario.rect.right = self.lucky_block.rect.left
                        else:
                            self.mario.rect.left = self.lucky_block.rect.right

                        self.mario.velocity[0] = 0

                    test_pos = t0_pos.move((0, dy))
                    if test_pos.colliderect(self.lucky_block.rect):
                        if dy > 0:
                            self.mario.rect.bottom = self.lucky_block.rect.top
                        else:
                            self.mario.rect.top = self.lucky_block.rect.bottom

                        self.mario.velocity[1] = 0


                movebackdrop = min(0, self.area.centerx - self.mario.rect.centerx)
                if movebackdrop < 0:
                    self.level_backdrop.pan(movebackdrop)
                    self.lucky_block.pan(movebackdrop)
                    self.mario.rect.centerx = self.area.centerx

                if self.mario.rect.left < self.area.left:
                    self.mario.rect.left = self.area.left




                self.allsprites.draw(self.screen)
                pygame.display.flip()

        pygame.quit()

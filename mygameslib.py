import os
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
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def load_sound(name):
    class NoneSound:
        def play(self): pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)

    sound = pygame.mixer.Sound(fullname)

    return sound


# classes for our game objects
class LevelBackdrop(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.layer = 0
        self.image_path = os.path.join(data_dir, 'supermariobackground.jpg')
        self.repeat_image = True
        self._load_image()
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.move = 4

    def _load_image(self):
        if self.repeat_image:
            image = repeat_image(self.image_path, 2)
            mode = image.mode
            size = image.size
            data = image.tobytes()
            self.image = pygame.image.fromstring(data, size, mode).convert()
            self.rect = self.image.get_rect()
        else:
            self.image, self.rect = load_image('supermariobackground.jpg')

        self.rect.topleft = (0, 0)

    def pan(self, pan_amount):
        if self.rect.right + pan_amount < self.area.right:
            pan_amount = 600 + pan_amount
        elif self.rect.left + pan_amount > self.area.left:
            pan_amount = pan_amount - 600
        else:
            move = pan_amount

        self.rect.move_ip((pan_amount, 0))

    def update(self):
        # self.pan_left()
        pass


class LuckyBlock(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.layer = 1
        self.image = load_image('luckyblock.png', (250, 250, 250))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (300, 210)


class CharacterSprite(pygame.sprite.DirtySprite):
    def __init__(self, position ):
        pygame.sprite.DirtySprite.__init__(self)  # call Sprite initializer
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.layer = 1
        self.state = CHARACTER_STATES.stopped
        self._direction = 1
        self._load_images()
        self.rect = self.image.get_rect()
        self.velocity = [0, 0]
        self.acceleration = [0, 0]

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        if self._direction != direction:
            self._direction = direction
            self._flip_images()

    @property
    def image(self):
        state_images = self._images[self.state]
        return state_images[self._state_image_cycles[self.state]]

    @property
    def position(self):
        return getattr(self.rect, self._posattr)

    @position.setter
    def position(self, value):
        setattr(self.rect, self._posattr, value)

    def update(self):
        pass


class Mario(CharacterSprite):
    def __init__(self, position, style=CHARACTER_STYLES.big):
        self._style = style
        CharacterSprite.__init__(self, position)
        self.running_speed = 4
        self.leg_cadence = 2  # higher is slower
        self.jumping_speed = 12

    def _load_images(self):
        self._images = {}
        for k, v in IMAGES_DICT[self.style].items():
            images = []
            for filename in v:
                images.append(load_image(filename, -1))
            self._images[k] = itertools.cycle(images)

    def run(self, direction):
        self.direction = direction
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.running
            self.velocity = (self.running_speed * direction, 0)

    def _on_solid_surface(self):
        return self.rect.bottom == 293

    def crouch(self):
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.crouching
            self.velocity = (0, 0)

    def jump(self):
        self.state = CHARACTER_STATES.jumping
        self.velocity = (self.velocity[0], -self.jumping_speed)
        self.acceleration = (0, GRAVITY)

    def stop(self):
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.stopped
            self.velocity = (0, 0)

    def _flip_images(self):
        for k, v in self._images.items():
            images = []
            for image in v:
                images.append(pygame.transform.flip(image, 1, 0))
            self._images[k] = images

    def _cycle_images(self):

        n_cycles = len(self._images[self.state])
        if n_cycles > 1:
            prev_n = self._state_image_cycles[self.state]
            next_n = (prev_n + 1) % (n_cycles - 1)
            self._state_image_cycles[self.state] = next_n

    def update(self):
        newpos = self.rect.move(self.velocity)
        if newpos.bottom > 293:
            newpos.bottom = 293
        self.rect = newpos
        self._cycle_images()
        self.velocity = (self.velocity[0] + self.acceleration[0], self.velocity[1] + self.acceleration[1])


class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(0)
        self.screen = pygame.display.set_mode((600, 337))
        self.area = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.level_backdrop = LevelBackdrop()
        self.mario = Mario((50, 293))
        self.lucky_block = LuckyBlock()
        self.allsprites = pygame.sprite.RenderPlain(self.level_backdrop, self.mario, self.lucky_block)
        pygame.display.flip()
        self.paused = False
        self.run()

    def run(self):
        going = True
        while going:
            self.clock.tick(60)
            keys = pygame.key.get_pressed()
            if keys[K_RIGHT]:
                self.mario.run(1)
            elif keys[K_LEFT]:
                self.mario.run(-1)
            elif keys[K_UP]:
                self.mario.jump()
            elif keys[K_DOWN]:
                self.crouch()
            else:
                self.mario.stop()

            for event in pygame.event.get():
                if event.type == QUIT:
                    going = False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.paused = 1 - self.paused

            if not self.paused:
                self.allsprites.update()
                movebackdrop = min(0, self.area.centerx - self.mario.rect.centerx)
                if movebackdrop < 0:
                    self.level_backdrop.pan(movebackdrop)
                    self.mario.rect.centerx = self.area.centerx
                if self.mario.rect.left < self.area.left:
                    self.mario.rect.left = self.area.left

                self.allsprites.draw(self.screen)
                pygame.display.flip()
        pygame.quit()

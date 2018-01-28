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
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)  # call Sprite initializer
        self._load_images()
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.layer = 1
        self._direction = 1
        self._state = CHARACTER_STATES.stopped
        self._sub_states = itertools.cycle(range(len(self._images[self._state])))
        self._sub_state = next(self._sub_states)
        self.rect = self.image.get_rect()
        self.velocity = [0, 0]
        self.acceleration = [0, GRAVITY]

    def _load_images(self):
        self._images = {}
        self._state_cycles = {}
        for k, v in IMAGES_DICT[self._style].items():
            self._images[k] = [load_image(filename, -1) for filename in v]
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
        sub_states = self._state_cycles[self.state]
        self._sub_state = next(sub_states)

    @property
    def image(self):
        return self._images[self.state][self._sub_state]

    def update(self):
        pass


class Mario(CharacterSprite):
    def __init__(self, style=CHARACTER_STYLES.big):
        self._style = style
        CharacterSprite.__init__(self)
        self.running_speed = 4
        self.leg_cadence = 2  # higher is slower
        self.jumping_speed = 12

    def run(self, direction):
        self.direction = direction
        self.state = CHARACTER_STATES.running
        self.velocity = [self.running_speed * direction, 0]

    def _on_solid_surface(self):
        return self.rect.bottom == GROUND_LEVEL

    def crouch(self):
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.crouching
            self.velocity = [0, 0]

    def jump(self):
        self.state = CHARACTER_STATES.jumping
        self.velocity[1] = -self.jumping_speed

    def stop(self):
        if self._on_solid_surface():
            self.state = CHARACTER_STATES.stopped
            self.velocity = self.acceleration = [0, 0]

    def _set_vectors(self):
        newpos = self.rect.move(self.velocity)
        if newpos[1] >= GROUND_LEVEL:
            newpos[1] = GROUND_LEVEL
            self.velocity[1] = self.acceleration[1] = 0
        else:
            self.velocity[0] += self.acceleration[0]
            self.velocity[1] += self.acceleration[1]
        self.rect = newpos

    def update(self):
        self._cycle_sub_state()
        self._set_vectors()





class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(0)
        self.screen = pygame.display.set_mode((600, 337))
        self.area = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.level_backdrop = LevelBackdrop()
        self.mario = Mario()
        self.mario.rect.midbottom = (50, GROUND_LEVEL)
        self.lucky_block = LuckyBlock()
        self.allsprites = pygame.sprite.RenderPlain(self.level_backdrop, self.mario, self.lucky_block)
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
                movebackdrop = min(0, self.area.centerx - self.mario.rect.centerx)
                if movebackdrop < 0:
                    self.level_backdrop.pan(movebackdrop)
                    self.mario.rect.centerx = self.area.centerx
                if self.mario.rect.left < self.area.left:
                    self.mario.rect.left = self.area.left

                self.allsprites.draw(self.screen)
                pygame.display.flip()
        pygame.quit()

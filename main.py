import pygame
import os

from pygame.locals import *
from PIL import Image

ACTION_STOP = 0
ACTION_RUN1 = 1
ACTION_RUN2 = 2
ACTION_RUN3 = 3
ACTION_BREAK = 4
ACTION_JUMP = 5
ACTION_CROUCH = 6

ACTION_RUNS = [ACTION_RUN1, ACTION_RUN2, ACTION_RUN3]
ACTIONS = [ACTION_STOP, ACTION_RUN1, ACTION_RUN2, ACTION_RUN3, ACTION_BREAK, ACTION_JUMP, ACTION_CROUCH]

GRAVITY = 1

def repeat_image( image_path, nrepeat = 2 ):
    image = Image.open(image_path)

    width, height = image.size[0], image.size[1]

    total_width = width * nrepeat

    new_im = Image.new(image.mode, (total_width, height))

    x_offset = 0
    for i in range(0, nrepeat):
      new_im.paste(image, (x_offset,0))
      x_offset += width

    return new_im

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def load_sound(name):
    class NoneSound:
        def play(self): pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)

    sound = pygame.mixer.Sound(fullname)

    return sound

# classes for our game objects
class LevelBackdrop(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image_path = os.path.join(data_dir, 'supermariobackground.jpg')
        self.repeat_image = True
        self._load_image()
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.move = 3


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

        self.rect.topleft = (0,0)

    def _pan(self, direction = 1):
        base_move = direction * self.move
        if self.rect.right + base_move < self.area.right:
            move = 600 + base_move
        elif self.rect.left + base_move > self.area.left:
            move = base_move - 600
        else:
            move = base_move

        self.rect.move_ip((move, 0))

    def pan_right(self):
        self._pan(1)

    def pan_left(self):
        self._pan(-1)

    def update(self):
        #self.pan_left()
        pass

class Mario(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self._load_images()
        self.action = ACTION_STOP
        self.image, self.rect = self.images[self.action]
        self.rect.midbottom = (50, 293)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.running_speed = 4
        self.run_cycle_pos = 0
        self.direction = 1
        self.jump_vertical_velocity = 15
        self.jump_sound = load_sound('smb_jump-small.wav')

    def _load_images(self):
        self.images = []
        for action in ACTIONS:
            filename = "mario{}.png".format(action)
            self.images.append(load_image(filename, -1))

    def _flip_images(self):
        flipped_images = [];
        for (image, rect) in self.images:
            flipped_image = pygame.transform.flip(image, 1, 0)
            flipped_rect = flipped_image.get_rect()
            flipped_images.append((flipped_image, flipped_rect))
        self.images = flipped_images

    def run_right(self):
        self._run(1)

    def run_left(self):
        self._run(-1)

    def _run(self, direction):
        if self.direction != direction:
            self._flip_images()
        self.direction = direction
        if not(self._is_jumping()):
            self.action = ACTION_RUN1
        self._update_image()

    def _update_image(self):
        midbottom = self.rect.midbottom
        self.image, self.rect = self.images[self.action]
        self.rect.midbottom = midbottom

    def stop(self):
        if self._is_running():
            self.action = ACTION_STOP
            self._update_image()

    def _update_run_action(self):
        self.action = ACTION_RUNS[self.run_cycle_pos%3]
        self.run_cycle_pos += 1

    def _is_running(self):
        return self.action in ACTION_RUNS

    def _is_jumping(self):
        return self.action == ACTION_JUMP

    def jump(self):
        if not(self._is_jumping()):
            self.jump_sound.play()
            self.action_prior_to_jumping = self.action
            if self._is_running():
                self.jump_velocity = [self.running_speed * self.direction, self.jump_vertical_velocity]
            else:
                self.jump_velocity = [0,self.jump_vertical_velocity]

            self.action = ACTION_JUMP
            self._update_image()

    def crouch(self):
        self.action = ACTION_CROUCH
        self._update_image()

    def update(self):
        if self._is_running():
            self._update_image()
            self.rect.move_ip((self.running_speed * self.direction, 0))
            self._update_run_action()
        if self._is_jumping():
            newpos = self.rect.move((self.jump_velocity[0], -self.jump_velocity[1]))
            self.jump_velocity[1] -= GRAVITY
            if newpos.bottom >= 293:
                newpos.bottom = 293
                self.action = self.action_prior_to_jumping
                self._update_image()
            self.rect = newpos



def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((600, 337))
    pygame.mouse.set_visible(0)

    # Prepare Game Objects
    clock = pygame.time.Clock()
    level_backdrop = LevelBackdrop();
    mario = Mario()
    allsprites = pygame.sprite.RenderPlain(level_backdrop, mario)

    #mario_theme = load_sound('01-main-theme-overworld.mp3')

    pygame.display.flip()

    # Event loop
    going = True
    while going:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and event.key == K_RIGHT:
                mario.run_right()
                #level_backdrop.pan_left()
            elif event.type == KEYDOWN and event.key == K_LEFT:
                mario.run_left()
                #level_backdrop.pan_right()
            elif event.type == KEYDOWN and event.key == K_UP:
                mario.jump()
            elif event.type == KEYDOWN and event.key == K_DOWN:
                mario.crouch()
            elif event.type == KEYUP:
                mario.stop()

        allsprites.update()
        allsprites.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == '__main__': main()
import unittest
import pygame
from mygameslib import *


class TestMarioBase(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((600, 337))
        self.mario = Mario()
        self.mario.rect.midbottom = (50, GROUND_LEVEL)

    def testInit(self):
        self.assertTrue(isinstance(self.mario, Mario))
        self.assertEqual(self.mario.state, CHARACTER_STATES.stopped)

    def tearDown(self):
        pygame.quit()

class TestMarioStates(TestMarioBase):
    def testRunBasic(self):
        pos = self.mario.rect.midbottom
        self.mario.run(1)
        # running sets velocity and updates the image
        self.assertEqual(self.mario.velocity, [self.mario.running_speed, 0])
        self.assertEqual(self.mario.state, CHARACTER_STATES.running)
        self.mario.update()
        self.assertEqual(self.mario.image, self.mario._images[CHARACTER_STATES.running][0])
        # after one update, the position should have updated, and the velocity should remain unchanged
        self.assertEqual(self.mario.velocity, [self.mario.running_speed, 0])
        self.assertEqual(self.mario.rect.midbottom, (pos[0] + self.mario.running_speed, pos[1]))
        self.mario.update()
        self.assertEqual(self.mario.rect.midbottom, (pos[0] + 2*self.mario.running_speed, pos[1]))

    def testChangeDirection(self):
        img = self.mario.image
        self.mario.direction = 1
        self.assertEqual(img, self.mario.image)
        self.mario.direction = -1
        self.assertNotEqual(img, self.mario.image)

    def testRunDirection(self):
        pos = self.mario.rect.midbottom
        self.mario.run(-1)
        self.mario.update()
        self.assertEqual(self.mario.rect.midbottom, (pos[0] - self.mario.running_speed, pos[1]))
        self.mario.run(1)
        self.mario.update()
        self.assertEqual(self.mario.rect.midbottom, (pos[0], pos[1]))

    def testRunCycle(self):
        self.mario.run(1)
        self.mario.update()
        self.assertEqual(self.mario.image, self.mario._images[CHARACTER_STATES.running][0])
        self.mario.update()
        self.assertEqual(self.mario.image, self.mario._images[CHARACTER_STATES.running][1])
        self.mario.update()
        self.assertEqual(self.mario.image, self.mario._images[CHARACTER_STATES.running][2])
        self.mario.update()
        self.assertEqual(self.mario.image, self.mario._images[CHARACTER_STATES.running][0])

    def testJumpBasic(self):
        self.mario.jump()
        self.assertEqual(self.mario.state, CHARACTER_STATES.jumping)
        self.assertEqual(self.mario.velocity[1], -self.mario.jumping_speed)
        self.mario.update()
        self.assertEqual(self.mario.velocity[1], -(self.mario.jumping_speed - GRAVITY))

        # lands on the ground
        maxupdates = 100
        nupdates = 0
        while self.mario.rect.bottom < GROUND_LEVEL:
            if nupdates >= maxupdates:
                break
            self.mario.update()
            nupdates += 1

        self.assertEqual(self.mario.rect.bottom, GROUND_LEVEL)
        self.assertEqual(self.mario.state, CHARACTER_STATES.stopped)

    def testRunningJump(self):
        self.mario.run()
        self.mario.update()
        self.mario.jump()
        self.mario.update()
        self.assertEqual(self.mario.velocity, [self.mario.running_speed, -(self.mario.jumping_speed - GRAVITY)])

if __name__ == '__main__':
    unittest.main()


import unittest
import pygame
from mygameslib import *


class TestMario(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((600, 337))
        self.mario = Mario((50, 273))

    def testInit(self):
        self.assertTrue(isinstance(self.mario, Mario))

    def testRun(self):
        self.mario.run(1)
        self.assertTupleEqual(self.mario.position, (50, 273), "Mario's position instantiated")

    def tearDown(self):
        pygame.quit()


if __name__ == '__main__':
    unittest.main()


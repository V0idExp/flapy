"""Flapy - a Flappy Bird clone in Python."""
from itertools import cycle
import os
import pygame
import sys

# Screen size in pixels.
SCREEN_SIZE = 800, 480

# Scroll speed in pixels.
SCROLL_SPEED = 200


class ResourceError(FileNotFoundError):
    """Resource loading error."""


def resource_filename(relpath):
    return os.path.join(*['data'] + relpath.split('/'))


def load_image(filename):
    try:
        image = pygame.image.load(filename)
        if image.get_alpha() is None:
            return image.convert()
        return image.convert_alpha()
    except pygame.error as err:
        raise ResourceError(err)


class Background:

    def __init__(self, scroll_speed):
        self.image = load_image(resource_filename('/background.png'))
        self.width = self.image.get_rect().width
        self.scroll_speed = scroll_speed
        self.x = 0

    def update(self, dt):
        self.x -= self.scroll_speed * dt
        if self.x <= -self.width:
            self.x += self.width

    def draw(self, surface):
        surface.blit(self.image, (self.x, 0))
        surface.blit(self.image, (self.x + self.width, 0))


class Plane(pygame.sprite.Sprite):

    animation_duration = 50

    def __init__(self):
        super().__init__()

        self._x = 0
        self._y = 0

        self.indices = cycle(range(3))
        self.images = [
            load_image(resource_filename('/planeRed{}.png'.format(i)))
            for i in (1, 2, 3)
        ]
        self.set_frame(0)

        self.time_acc = 0
        self.frame_time = (self.animation_duration / len(self.images)) / 1000.0

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self.rect.left = self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self.rect.top = self._y = y

    def set_frame(self, index):
        self.image = self.images[index]
        self.rect = self.image.get_rect()
        self.rect.left = self.x
        self.rect.top = self.y

    def update(self, dt):
        self.time_acc += dt
        self.y += dt * 50
        while self.time_acc >= self.frame_time:
            self.time_acc -= self.frame_time
            self.set_frame(next(self.indices))


if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('FlaPy')

    # create background
    background = Background(SCROLL_SPEED)

    # create plane
    plane = Plane()
    plane.x = 30
    plane.y = SCREEN_SIZE[1] * 0.3

    sprites = pygame.sprite.Group()
    sprites.add(plane)

    last_update = pygame.time.get_ticks()
    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # compute time delta
        now = pygame.time.get_ticks()
        dt = (now - last_update) / 1000.0
        last_update = now

        # update entities
        sprites.update(dt)
        background.update(dt)

        # render
        screen.fill((0, 0, 0))
        background.draw(screen)
        sprites.draw(screen)
        pygame.display.flip()

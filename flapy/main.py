"""Flapy - a Flappy Bird clone in Python."""
from abc import ABC
from abc import abstractmethod
from abc import abstractproperty
from itertools import cycle
import math
import os
import pygame
import sys

# Screen size in pixels.
SCREEN_SIZE = 800, 480

# Game data.
GAME_DATA = {
    'scroll_speed': 200,
    'entities': [
        {
            'id': 0,
            'type': 'rock',
            'position': (400, 241),
        },
        {
            'id': 1,
            'type': 'rock',
            'position': (1910, 241),
        },
        {
            'id': 2,
            'type': 'rock',
            'position': (2200, 300),
        }
    ]
}


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


def check_circle_collision(c0, c1):
    dx = c1[0] - c0[0]
    dy = c1[1] - c0[1]
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < c0[2] + c1[2]:
        return True
    return False


class Entity(ABC):

    @abstractproperty
    def x(self):
        """Object position X coordinate."""

    @x.setter
    def x(self, x):
        """Set object position X coordinate."""

    @abstractproperty
    def y(self):
        """Object position Y coordinate."""

    @y.setter
    def y(self, y):
        """Set object position Y coordinate."""

    @abstractproperty
    def collision_circles(self):
        """Collision circles associated with the entity as a list of (x, y,
        radius) tuples."""

    @abstractmethod
    def update(self, dt):
        """Updates the entity."""

    @abstractmethod
    def draw(self, surface):
        """Draws the entity on given surface."""


class Rock(Entity):

    def __init__(self, position):
        self.image = load_image(resource_filename('/rockGrass.png'))
        self._x, self._y = position
        self._collision_circles = [
            (65, 21, 21),
            (65, 45, 16),
            (65, 75, 18),
            (61, 108, 28),
            (58, 172, 51),
            (55, 232, 54),
        ]

    @property
    def collision_circles(self):
        return self._collision_circles

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y

    def draw(self, surface):
        surface.blit(self.image, (self._x, self._y))

    def update(self, dt):
        pass


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


class Player(pygame.sprite.Sprite):

    animation_duration = 50

    collision_circle = (44, 36, 44)

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


class Game:

    def __init__(self, screen_size, data):
        self.width, self.height = screen_size
        self.distance = 0
        self.data = data
        self.entities = {}
        self.background = Background(data['scroll_speed'])
        self.objects = pygame.sprite.Group()

        self.player = Player()
        self.objects.add(self.player)

    def spawn_entities(self):
        for spec in self.data['entities']:
            if spec['id'] in self.entities:
                continue

            x, y = spec['position']
            if x > self.distance and x < self.distance + self.width * 2:
                if spec['type'] == 'rock':
                    x -= self.distance
                    entity = Rock((x, y))
                    self.entities[spec['id']] = entity
                    print('Added {} entity with id {}'.format(
                        spec['type'],
                        spec['id']))

    def update_entities(self, dt):
        for entity in self.entities.values():
            entity.x -= self.data['scroll_speed'] * dt
            entity.update(dt)

    def prune_entities(self):
        to_remove = []
        for eid, entity in self.entities.items():
            if entity.x < -self.width:
                to_remove.append(eid)

        for eid in to_remove:
            self.entities.pop(eid)
            print('Removed entity {}'.format(eid))

    def check_collision(self):
        x0, y0, r0 = self.player.collision_circle
        x0 += self.player.x
        y0 += self.player.y
        c0 = (x0, y0, r0)

        for eid, entity in self.entities.items():
            for (x1, y1, r1) in entity.collision_circles:
                x1 += entity.x
                y1 += entity.y
                c1 = (x1, y1, r1)

                if check_circle_collision(c0, c1):
                    print('Collided with entity {}'.format(eid))
                    return True
        return False

    def update(self, dt):
        # update global distance counter
        self.distance += dt * self.data['scroll_speed']

        self.spawn_entities()
        self.update_entities(dt)
        self.prune_entities()

        if self.check_collision():
            exit(1)

        self.background.update(dt)
        self.objects.update(dt)

    def draw(self, screen):
        self.background.draw(screen)
        self.objects.draw(screen)
        for entity in self.entities.values():
            entity.draw(screen)


if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('FlaPy')

    game = Game(SCREEN_SIZE, GAME_DATA)

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
        game.update(dt)

        # render
        screen.fill((0, 0, 0))
        game.draw(screen)
        pygame.display.flip()

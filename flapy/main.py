"""Flapy - a Flappy Bird clone in Python."""
from abc import ABC
from abc import abstractmethod
from abc import abstractproperty
from enum import Enum
from enum import unique
from itertools import cycle
from itertools import zip_longest
import math
import os
import pygame
import sys

# Screen size in pixels.
SCREEN_SIZE = 800, 480


def load_image(path):
    """Loads an image resource and returns a surface object for it."""
    filename = os.path.join(*['data'] + path.split('/'))
    image = pygame.image.load(filename)
    if image.get_alpha() is None:
        return image.convert()
    return image.convert_alpha()


def check_circle_collision(c0, c1):
    """Checks whether two circles collide."""
    dx = c1[0] - c0[0]
    dy = c1[1] - c0[1]
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < c0[2] + c1[2]:
        return True
    return False


class Entity(ABC):

    def __init__(self):
        self._x = 0
        self._y = 0

    @property
    def x(self):
        """Object position X coordinate."""
        return self._x

    @x.setter
    def x(self, x):
        """Set object position X coordinate."""
        self._x = x

    @property
    def y(self):
        """Object position Y coordinate."""
        return self._y

    @y.setter
    def y(self, y):
        """Set object position Y coordinate."""
        self._y = y

    @abstractproperty
    def colliders(self):
        """Collision circles associated with the entity as a list of
        (x, y, radius) tuples."""

    @abstractmethod
    def update(self, dt):
        """Updates the entity."""

    @abstractmethod
    def draw(self, surface):
        """Draws the entity on given surface."""


class Obstacle(Entity):

    @unique
    class Type(Enum):
        rock = 'rock'
        ice = 'ice'

    def __init__(self, obstacle_type, position):
        super().__init__()
        filename = {
            Obstacle.Type.rock: '/rockGrass.png',
            Obstacle.Type.ice: '/rockIceDown.png',
        }[obstacle_type]
        self.type = obstacle_type
        self.image = load_image(filename)
        self.x, self.y = position
        self._colliders = []

        width, height = self.image.get_size()
        alpha_values = pygame.surfarray.pixels_alpha(self.image)
        segments = []
        for x, column in enumerate(alpha_values):
            for y, alpha in enumerate(column):
                if len(segments) != height:
                    segments.append([None, None])

                if alpha != 0:
                    if segments[y][0] is None:
                        segments[y][0] = x
                    segments[y][1] = x

        v_offset = 0
        chunks = [iter(segments)] * int(height / 10)
        for c, chunk in enumerate(zip_longest(*chunks)):
            chunk = list(filter(lambda x: x is not None, chunk))
            min_x = min(segment[0] for segment in chunk)
            max_x = max(segment[1] for segment in chunk)
            x = sum([(x0 + x1) / 2 for x0, x1 in chunk]) / len(chunk)
            chunk_height = len(chunk) / len(segments) * height
            y = v_offset + chunk_height
            v_offset += chunk_height
            r = (max_x - min_x) / 2
            self._colliders.append((x, y, r))

    @property
    def colliders(self):
        return self._colliders

    def draw(self, surface):
        surface.blit(self.image, (self._x, self._y))

    def update(self, dt):
        pass


class Background(Entity):

    colliders = []

    def __init__(self, scroll_speed):
        super().__init__()
        self.image = load_image('/background.png')
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


class Player(Entity):

    animation_duration = 50

    def __init__(self):
        super().__init__()

        self.indices = cycle(range(3))
        self.images = [
            load_image('/planeRed{}.png'.format(i))
            for i in (1, 2, 3)
        ]
        self.set_frame(0)

        self.time_acc = 0
        self.frame_time = (self.animation_duration / len(self.images)) / 1000.0

        self.vertical_velocity = 0

    @property
    def colliders(self):
        return [(44, 36, 44)]

    @property
    def x(self):
        return super().x

    @x.setter
    def x(self, x):
        Entity.x.fset(self, x)
        self.rect.left = x

    @property
    def y(self):
        return super().y

    @y.setter
    def y(self, y):
        Entity.y.fset(self, y)
        self.rect.top = y

    def set_frame(self, index):
        self.image = self.images[index]
        self.rect = self.image.get_rect()
        self.rect.left = self.x
        self.rect.top = self.y

    def boost_up(self):
        self.vertical_velocity -= 50

    def update(self, dt):
        self.time_acc += dt
        self.vertical_velocity += 9.81 * dt * 10
        self.y += self.vertical_velocity * dt
        while self.time_acc >= self.frame_time:
            self.time_acc -= self.frame_time
            self.set_frame(next(self.indices))

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Game:

    def __init__(self, screen_size, data):
        self.width, self.height = screen_size
        self.distance = 0
        self.data = data
        self.entities = {}
        self.background = Background(data['scroll_speed'])
        self.player = Player()

    def spawn_entities(self):
        for spec in self.data['entities']:
            if spec['id'] in self.entities:
                continue

            x, y = spec['position']
            if x > self.distance and x < self.distance + self.width * 2:
                if spec['type'] in {Obstacle.Type.rock, Obstacle.Type.ice}:
                    x -= self.distance
                    entity = Obstacle(spec['type'], (x, y))
                    self.entities[spec['id']] = entity
                    print('Added {} entity with id {}'.format(
                        spec['type'].value,
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
        x0, y0, r0 = self.player.colliders[0]
        x0 += self.player.x
        y0 += self.player.y
        c0 = (x0, y0, r0)

        for eid, entity in self.entities.items():
            for (x1, y1, r1) in entity.colliders:
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
        self.player.update(dt)

    def draw(self, screen):
        self.background.draw(screen)
        self.player.draw(screen)
        for entity in self.entities.values():
            entity.draw(screen)

    def handle_keypress(self, keyname):
        if keyname == 'space':
            self.player.boost_up()


# Game data.
GAME_DATA = {
    'scroll_speed': 100,
    'entities': [
        {
            'id': 0,
            'type': Obstacle.Type.rock,
            'position': (400, 241),
        },
        {
            'id': 3,
            'type': Obstacle.Type.ice,
            'position': (700, 0),
        },
        {
            'id': 1,
            'type': Obstacle.Type.rock,
            'position': (1910, 241),
        },
        {
            'id': 2,
            'type': Obstacle.Type.rock,
            'position': (2200, 300),
        }
    ]
}


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
            elif event.type == pygame.KEYDOWN:
                game.handle_keypress(pygame.key.name(event.key))

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

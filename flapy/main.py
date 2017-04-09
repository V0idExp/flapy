"""Flapy - a Flappy Bird clone in Python."""
import os
import pygame
import sys

SCREEN_SIZE = 800, 480


class ResourceError(Exception):
    """Resource loading error."""


def resource_filename(relpath):
    return os.path.join(*['data'] + relpath.split('/'))


def load_image(filename):
    try:
        image = pygame.image.load(filename)
        if image.get_alpha() is None:
            return image.convert()
        return image.convert_alpha()
    except pygame.error:
        raise ResourceError(filename)


if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('FlaPy')

    # fill background
    background = load_image(resource_filename('/background.png'))

    # display some text
    font = pygame.font.Font(None, 36)
    text = font.render('FlaPy', 1, (10, 10, 10))
    textpos = text.get_rect()
    textpos.centerx = background.get_rect().centerx

    # blit everything to the screen
    screen.blit(background, (0, 0))
    screen.blit(text, textpos)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        pygame.display.flip()

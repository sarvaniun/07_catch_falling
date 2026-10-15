"""
GameEngine: manages basket movement, falling objects, collisions,
spawning, scoring, misses, and the temporary speed boost.
"""

import random
import pygame

from game.basket import Basket
from game.falling_object import FallingObject
from game.collision import is_caught
from game.renderer import WIDTH, HEIGHT

MIN_SPAWN_INTERVAL_FRAMES = 30
MAX_SPAWN_INTERVAL_FRAMES = 70
MAX_OBJECTS_ON_SCREEN = 5
MIN_SPAWN_DISTANCE = 80
BOOST_DURATION_FRAMES = 180

MAX_MISSES = 5

class GameEngine:
    def __init__(self):
        self.basket = Basket(x=WIDTH / 2, y=HEIGHT - 30)
        self.objects = []
        self.frames_until_spawn = 0
        self.last_spawn_x = None
        self.score = 0
        self.misses = 0
        self.game_over = False

    def _spawn_object(self):
        valid_positions = [
            x for x in range(20, WIDTH - 19)
            if self.last_spawn_x is None
            or abs(x - self.last_spawn_x) >= MIN_SPAWN_DISTANCE
        ]

        x = random.choice(valid_positions)
        self.last_spawn_x = x
        self.objects.append(FallingObject(x=x, y=-14, speed=3))

    def handle_input(self, keys_pressed):
        if self.game_over:
            return
        if keys_pressed[pygame.K_LEFT]:
            self.basket.x -= self.basket.speed
        if keys_pressed[pygame.K_RIGHT]:
            self.basket.x += self.basket.speed
        # Keep the entire basket within the screen boundaries.
        half_width = self.basket.width / 2
        self.basket.x = max(
            half_width,
            min(WIDTH - half_width, self.basket.x)
        )

    def handle_keydown(self, key):
        if self.game_over and key == pygame.K_r:
            self.__init__()
        elif (
            not self.game_over
            and key == pygame.K_SPACE
            and self.basket.boosted_frames <= 0
        ):
            self.basket.boosted_frames = BOOST_DURATION_FRAMES
            self.basket.speed = self.basket.boost_speed

    def update(self):
        if self.game_over:
            return

        if self.basket.boosted_frames > 0:
            self.basket.boosted_frames -= 1

            if self.basket.boosted_frames == 0:
                self.basket.speed = self.basket.normal_speed
        self.frames_until_spawn -= 1
        if self.frames_until_spawn <= 0:
            if len(self.objects) < MAX_OBJECTS_ON_SCREEN:
                self._spawn_object()

            self.frames_until_spawn = random.randint(
                MIN_SPAWN_INTERVAL_FRAMES,
                MAX_SPAWN_INTERVAL_FRAMES
            )

        for obj in self.objects:
            obj.update()

        basket_rect = self.basket.get_rect()
        for obj in self.objects.copy():
            if is_caught(basket_rect, obj):
                self.score += 1
                self.objects.remove(obj)

        missed = [o for o in self.objects if o.is_past_bottom(HEIGHT)]
        if missed:
            self.objects = [o for o in self.objects if not o.is_past_bottom(HEIGHT)]
            self.misses += len(missed)
            if self.misses >= MAX_MISSES:
                self.game_over = True

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_scene(surface, self.basket, self.objects)
        renderer.draw_text(surface, font, f"Score: {self.score}", (10, 10))
        renderer.draw_text(surface, font, f"Misses: {self.misses}/{MAX_MISSES}", (10, 36))

        if self.basket.boosted_frames > 0:
            renderer.draw_text(
                surface,
                font,
                "SPEED BOOST ACTIVE!",
                (10, 62),
                (255, 220, 80)
            )

        if self.game_over:
            renderer.draw_banner(surface, font, f"Game Over! Final score: {self.score}. Press R to restart.")

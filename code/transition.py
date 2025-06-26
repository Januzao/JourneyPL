import pygame


class HorizontalRectangleSwipeTransition(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.width, self.height = pygame.display.get_window_size()

        self.image = pygame.Surface((self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

        self.transitioning = True
        self.speed = 300

        # pass this through via the constructor so we can modify it to be any number
        rect_count = 4

        self.rectangles = []
        division = self.height // rect_count

        for i in range(rect_count):
            self.rectangles.append(
                pygame.Rect(0, division * (i), self.width, division)
            )

        self.to_the_right_x = 0
        self.to_the_left_x = 0

    def update(self, dt):
        self.image.fill((0, 0, 0, 0))
        self.to_the_left_x -= self.speed * dt
        self.to_the_right_x += self.speed * dt

        for i, rect in enumerate(self.rectangles):
            pygame.draw.rect(self.image, (255, 255, 255), rect)

            if i % 2 == 0:
                rect.move_ip(self.to_the_right_x, 0)
            else:
                rect.move_ip(self.to_the_left_x, 0)

        self.check_for_transition_complete()

    def check_for_transition_complete(self):
        if self.rectangles[0].left > self.width:
            self.transitioning = False

    def is_transitioning(self):
        return self.transitioning

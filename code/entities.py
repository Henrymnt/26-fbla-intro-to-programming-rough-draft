from settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, facing_direction):
        super().__init__(groups)
        
        self.z = WORLD_LAYERS['main']

        #graphics
        self.frame_index = 0
        self.frames = frames
        self.facing_direction = facing_direction

        #motion
        self.direction = vector()
        self.speed =250
        self.blocked = False

        #sprite itself
        self.image = self.frames[self.get_state()][self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        self.hitbox = self.rect.inflate(-self.rect.width * 0.5, -60)

        self.y_sort = self.rect.centery

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[self.get_state()][int(self.frame_index % len(self.frames[self.get_state()]))]
    
    def get_state(self):
        moving = bool(self.direction)
        if moving:
            if self.direction.x != 0:
                self.facing_direction = 'right' if self.direction.x > 0 else 'left'
            if self.direction.y != 0:
                self.facing_direction = 'down' if self.direction.y > 0 else 'up'
        suffix = '' if moving else '_idle'
        return f"{self.facing_direction}{suffix}"
    
    def block(self):
        self.blocked = True
        self.direction = vector(0,0)

    def unblock(self):
        self.blocked = False

class Player(Entity):
    def __init__(self, pos, frames, groups, facing_direction, collision_sprites):
        super().__init__(pos, frames, groups, facing_direction)
        self.collision_sprites = collision_sprites
        self.at_home = False

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector()
        if keys[pygame.K_UP]:
            input_vector.y -= 1
        if keys[pygame.K_DOWN]:
            input_vector.y += 1
        if keys[pygame.K_LEFT]:
            input_vector.x -= 1
        if keys[pygame.K_RIGHT]:
            input_vector.x += 1
        self.direction = input_vector.normalize() if input_vector else input_vector

    def move(self, dt):
        # horizontal movement
        self.rect.centerx += self.direction.x * self.speed * dt
        self.hitbox.centerx = self.rect.centerx
        self.collisions('horizontal')

        # vertical movement
        self.rect.centery += self.direction.y * self.speed * dt
        self.hitbox.centery = self.rect.centery
        self.collisions('vertical')


    def collisions(self, axis):
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                # horizontal collision
                if axis == 'horizontal':
                    if self.direction.x > 0: 
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                # vertical collision
                if axis == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery
        
        # temporary
        if not self.at_home:
            cx, cy = 4223.94, 3661.26
            half_w, half_h = 180, 150

            min_x, max_x = cx - half_w, cx + half_w
            min_y, max_y = cy - half_h, cy + half_h

            x, y = self.rect.center
            x = max(min_x, min(max_x, x))
            y = max(min_y, min(max_y, y))
            self.rect.center = (int(x), int(y))
            self.hitbox.center = self.rect.center
        #temporary


    def update(self, dt):
        self.y_sort = self.rect.centery
        if not self.blocked:
            self.input()
            self.move(dt)
        self.animate(dt)

class RandoGuys(Entity):
    def __init__(self, pos, frames, groups,facing_direction):
        super().__init__(pos, frames, groups,facing_direction)

    # def update(self, dt):
    #     self.animate(dt)
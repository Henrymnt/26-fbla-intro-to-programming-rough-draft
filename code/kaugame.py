from settings import *
from pytmx.util_pygame import load_pygame
from os.path import join

from sprites import Sprite, AnimatedSprite, MonsterPatchSprite, BorderSprite, CollidableSprite, TransitionSprite
from entities import Player, RandoGuys
from groups import AllSprites
from pet import Pet

from support import *

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Kaugame')
        self.clock = pygame.time.Clock()

        #groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.transition_sprites = pygame.sprite.Group()

        # transition
        self.transition_target = None
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_mode = 'nah'
        self.tint_progress = 0
        self.tint_direction = -1
        self.tint_speed = 400

        self.import_assets()
        # self.setup(self.tmx_maps['hospital'],'world')
        self.setup(self.tmx_maps['world'],'house')
    
    def import_assets(self):
        self.tmx_maps = tmx_importer(join('..','data', 'maps'))
        
        self.overworld_frames = {
            'water': import_folder("..","graphics", "tilesets","water"),
            'coast': coast_importer(24, 12, '..','graphics','tilesets','coast'),
            'characters': all_character_import('..','graphics',"characters"),
        }

    def setup(self, tmx_map, player_start_pos):
        
        # Clear (char, eTc)
        for group in (self.all_sprites, self.collision_sprites, self.transition_sprites):
            group.empty()

        # Terrain Tiles
        for layer in ['Terrain','Terrain Top']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, WORLD_LAYERS['bg'])

        # Water
        for obj in tmx_map.get_layer_by_name('Water'):
            for x in range(int(obj.x), int(obj.x+obj.width), TILE_SIZE):
                for y in range(int(obj.y), int(obj.y +obj.height), TILE_SIZE):
                    AnimatedSprite((x,y), self.overworld_frames['water'], self.all_sprites, WORLD_LAYERS['water'])

        #Coast
            for obj in tmx_map.get_layer_by_name('Coast'):
                terrain = obj.properties['terrain']
                side = obj.properties['side']
                AnimatedSprite((obj.x,obj.y), self.overworld_frames['coast'][terrain][side], self.all_sprites, WORLD_LAYERS['bg'])

        # Objects
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'top':
                Sprite((obj.x, obj.y), obj.image, self.all_sprites, WORLD_LAYERS['top'])
            else:
                CollidableSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # Transition objects
        for obj in tmx_map.get_layer_by_name('Transition'):
            TransitionSprite((obj.x, obj.y), (obj.width, obj.height), (obj.properties["target"], obj.properties["pos"]), self.transition_sprites)

        # Collision objects
        for obj in tmx_map.get_layer_by_name('Collisions'):
            BorderSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        # Green stuff
        for obj in tmx_map.get_layer_by_name('Monsters'):
            MonsterPatchSprite((obj.x,obj.y), obj.image, self.all_sprites, obj.properties['biome'])

        # Entities
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player': 
                if obj.properties['pos'] == player_start_pos:
                    print(obj.x,obj.y)
                    self.player = Player(
                        pos = (obj.x, obj.y), 
                        frames = self.overworld_frames['characters']['player'],
                        groups = self.all_sprites,
                        facing_direction=obj.properties.get('direction','down'),
                        collision_sprites=self.collision_sprites)
            else:
                RandoGuys(
                    pos = (obj.x, obj.y), 
                    frames = self.overworld_frames['characters'][obj.properties['graphic']], 
                    groups = (self.all_sprites, self.collision_sprites),
                    facing_direction = obj.properties['direction'] if 'direction' in obj.properties else 'down')

        if(tmx_map == self.tmx_maps['house']):
            self.player.at_home = True
        else:
            self.player.at_home = False

    def transition_check(self):
        sprites = [sprite for sprite in self.transition_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites:
            self.player.block()
            self.transition_target = sprites[0].target
            self.tint_mode = 'tint'
    
    def tint_screen(self, dt):
        if self.tint_mode == 'nah':
            self.tint_progress -= self.tint_speed * dt
        if self.tint_mode == 'tint':
            self.tint_progress += self.tint_speed * dt
            if self.tint_progress >= 255:
                self.setup(self.tmx_maps[self.transition_target[0]], self.transition_target[1])
                self.tint_mode = 'nah'
                self.transition_target = None

        self.tint_progress = max(0, min(self.tint_progress, 255))
        self.tint_surf.set_alpha(self.tint_progress)
        self.display_surface.blit(self.tint_surf, (0,0))

    def run(self):
        while True:
            dt = self.clock.tick() / 1000
            self.display_surface.fill("black")

            #event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            #logic
            self.transition_check()
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player.rect.center)

            self.tint_screen(dt)
            pygame.display.update()

if __name__ == '__main__':
        game = Game()
        game.run()

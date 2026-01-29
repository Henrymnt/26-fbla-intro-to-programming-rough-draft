from settings import *
# To be converted into something built in to kaugame

# Simple pet UI for the game: naming, species, care actions, reactions, expense tracking
pygame.init()

# Helpers
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def load_game_font(name, size):
    try:
        path = join(dirname(__file__), '..', 'graphics', 'fonts', name)
        return pygame.font.Font(path, size)
    except Exception:
        return pygame.font.SysFont(None, size)

FONT = load_game_font('PixeloidSans.ttf', 16)
TITLE_FONT = load_game_font('dogicapixelbold.otf', 26)

SAVE_PATH = join(dirname(__file__), 'pet_save.json')
WIDTH, HEIGHT = 700, 420
BG = (245,245,250)
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (200,200,200)
ACCENT = hex_to_rgb(COLORS.get('gold', '#ffd700'))

class Pet:
    def __init__(self, name='Buddy', species='cat'):
        self.name = name
        self.species = species
        self.hunger = 60
        self.happiness = 70
        self.energy = 80
        self.cleanliness = 80
        self.health = 100
        self.money = 200
        self.expenses_total = 0

    def spend(self, amount):
        if self.money >= amount:
            self.money -= amount
            self.expenses_total += amount
            return True
        return False

    def feed(self, cost=5):
        if self.spend(cost) and self.hunger < 100:
            self.hunger = min(100, self.hunger + 20)
            self.happiness = min(100, self.happiness + 6)
            return True
        return False

    def play(self):
        # play costs energy and some hunger
        if self.energy >= 12 and self.hunger >= 8:
            self.energy = max(0, self.energy - 12)
            self.hunger = max(0, self.hunger - 8)
            self.happiness = min(100, self.happiness + 12)
            return True
        return False

    def rest(self):
        self.energy = min(100, self.energy + 28)
        self.hunger = max(0, self.hunger - 6)
        self.happiness = min(100, self.happiness + 4)
        return True

    def clean(self, cost=3):
        if self.spend(cost):
            self.cleanliness = min(100, self.cleanliness + 40)
            self.happiness = min(100, self.happiness + 4)
            self.health = min(100, self.health + 3)
            return True
        return False

    def health_check(self, cost=10):
        if self.spend(cost):
            self.health = min(100, self.health + 22)
            self.happiness = min(100, self.happiness + 6)
            return True
        return False

    def pass_time(self, seconds):
        # passive changes
        self.hunger = max(0, self.hunger - 0.6 * seconds)
        self.cleanliness = max(0, self.cleanliness - 0.08 * seconds)
        # small energy regen when idle
        self.energy = max(0, min(100, self.energy + 0.5 * seconds))
        if self.hunger < 25:
            self.happiness = max(0, self.happiness - 0.4 * seconds)
        if self.cleanliness < 25:
            self.happiness = max(0, self.happiness - 0.3 * seconds)
        if self.hunger < 15 or self.cleanliness < 10:
            self.health = max(0, self.health - 0.6 * seconds)
        else:
            if self.happiness > 60 and self.cleanliness > 50:
                self.health = min(100, self.health + 0.2 * seconds)

    def reaction(self):
        # map stats to reaction string corresponding to animal image names
        if self.health < 30:
            return 'fear'
        if self.hunger < 20:
            return 'anger'
        if self.happiness >= 85 and self.energy >= 60:
            return 'love'
        if self.happiness >= 65:
            return 'joy'
        if self.happiness < 35:
            return 'sadness'
        return 'joy'

    def to_dict(self):
        return {k: getattr(self, k) for k in (
            'name','species','hunger','happiness','energy','cleanliness','health','money','expenses_total')}

    @classmethod
    def from_dict(cls, d):
        p = cls(d.get('name','Buddy'), d.get('species','cat'))
        p.hunger = d.get('hunger',60)
        p.happiness = d.get('happiness',70)
        p.energy = d.get('energy',80)
        p.cleanliness = d.get('cleanliness',80)
        p.health = d.get('health',100)
        p.money = d.get('money',200)
        p.expenses_total = d.get('expenses_total',0)
        return p

class Button:
    def __init__(self, rect, text, cb, bg=GRAY, fg=BLACK):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = cb
        self.bg = bg
        self.fg = fg

    def draw(self, surf):
        pygame.draw.rect(surf, self.bg, self.rect)
        pygame.draw.rect(surf, ACCENT, self.rect, 2)
        txt = FONT.render(self.text, False, self.fg)
        surf.blit(txt, (self.rect.x+8, self.rect.y + (self.rect.height - txt.get_height())//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class PetUI:
    SPECIES = ['cat','dog','fish']

    def __init__(self, pet: Pet, screen):
        self.pet = pet
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.name_buffer = pet.name
        self.input_active = False

        # buttons
        left = 40
        self.feed_btn = Button((left,320,120,36),'Feed ($5)', self.feed)
        self.play_btn = Button((left+140,320,120,36),'Play', self.play)
        self.rest_btn = Button((left,360,120,36),'Rest', self.rest)
        self.clean_btn = Button((left+140,360,120,36),'Clean ($3)', self.clean)
        # move health button to a separate location above the pet image (left panel)
        self.health_btn = Button((120,40,160,36),'Health ($10)', self.health_check)
        self.species_btn = Button((500,320,160,36),'Next Species', self.next_species)

        # load animal images
        base = join(dirname(__file__), '..', 'animal_pics', 'animal picutes')
        self.animal_images = {}
        for sp in ('cat','dog'):
            self.animal_images[sp] = {}
            for emo in ('anger','fear','joy','love','sadness'):
                try:
                    img = pygame.image.load(join(base, f"{sp}_{emo}.png")).convert_alpha()
                    self.animal_images[sp][emo] = img
                except Exception:
                    self.animal_images[sp][emo] = None
        try:
            self.animal_images['fish'] = pygame.image.load(join(base,'fish.png')).convert_alpha()
        except Exception:
            self.animal_images['fish'] = None

    def feed(self):
        if not self.pet.feed():
            print('not enough money or full')

    def play(self):
        if not self.pet.play():
            print('cannot play')

    def rest(self):
        self.pet.rest()

    def clean(self):
        if not self.pet.clean():
            print('not enough money')

    def health_check(self):
        if not self.pet.health_check():
            print('not enough money')

    def next_species(self):
        idx = self.SPECIES.index(self.pet.species) if self.pet.species in self.SPECIES else 0
        self.pet.species = self.SPECIES[(idx+1)%len(self.SPECIES)]

    def draw_pet(self):
        center = (200,180)
        pet_rect = pygame.Rect(center[0]-100, center[1]-100, 200, 200)
        drew = False
        if self.pet.species in ('cat','dog') and self.animal_images.get(self.pet.species):
            emo = self.pet.reaction()
            img = self.animal_images[self.pet.species].get(emo)
            if img:
                scaled = pygame.transform.scale(img, (200,200))
                self.screen.blit(scaled, scaled.get_rect(center=center).topleft)
                drew = True
        elif self.pet.species == 'fish' and self.animal_images.get('fish'):
            img = self.animal_images['fish']
            scaled = pygame.transform.scale(img, (160,120))
            self.screen.blit(scaled, scaled.get_rect(center=center).topleft)
            drew = True

        if not drew:
            pygame.draw.ellipse(self.screen, (30,30,30), (center[0]-60, center[1]+50, 120, 20))
            pygame.draw.circle(self.screen, (200,160,100), center, 80)
            pygame.draw.rect(self.screen, BLACK, (center[0]-36, center[1]-26, 12,12))
            pygame.draw.rect(self.screen, BLACK, (center[0]+24, center[1]-26, 12,12))
            pygame.draw.rect(self.screen, BLACK, (center[0]-16, center[1]+18, 32,6))

    def draw_stats(self):
        panel = pygame.Rect(360,40,310,260)
        pygame.draw.rect(self.screen, WHITE, panel)
        pygame.draw.rect(self.screen, ACCENT, panel, 2)
        self.screen.blit(TITLE_FONT.render('Pet Info', False, BLACK), (370,48))

        def bar(y, name, val):
            self.screen.blit(FONT.render(f"{name}: {int(val)}", False, BLACK), (380,y))
            pygame.draw.rect(self.screen, GRAY, (380,y+22,220,18))
            color = (200,100,50) if name in ('Hunger','Health') else (0,200,0)
            pygame.draw.rect(self.screen, color, (380,y+22,int(val/100*220),18))

        bar(90,'Hunger', self.pet.hunger)
        bar(130,'Happiness', self.pet.happiness)
        bar(170,'Energy', self.pet.energy)
        bar(210,'Cleanliness', self.pet.cleanliness)
        self.screen.blit(FONT.render(f"Health: {int(self.pet.health)}", False, BLACK), (380,250))
        self.screen.blit(FONT.render(f"Money: ${int(self.pet.money)}", False, BLACK), (380,274))
        self.screen.blit(FONT.render(f"Expenses: ${int(self.pet.expenses_total)}", False, BLACK), (380,296))

        # name field
        pygame.draw.rect(self.screen, (240,240,240), (380,320,220,34))
        self.screen.blit(FONT.render('Name:', False, BLACK), (388,326))
        name_txt = self.name_buffer + ('|' if self.input_active and (pygame.time.get_ticks()//400)%2==0 else '')
        self.screen.blit(FONT.render(name_txt, False, BLACK), (438,326))

        # species
        self.screen.blit(FONT.render(f"Species: {self.pet.species}", False, BLACK), (380,350))
        self.screen.blit(FONT.render('Move: none   Interact: click buttons', False, BLACK), (380,370))

    def handle_event(self, event):
        for btn in (self.feed_btn, self.play_btn, self.rest_btn, self.clean_btn, self.health_btn, self.species_btn):
            btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(380,320,220,34).collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False

        if self.input_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.pet.name = self.name_buffer.strip() or self.pet.name
                self.input_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.name_buffer = self.name_buffer[:-1]
            else:
                if len(self.name_buffer) < 16 and event.unicode.isprintable():
                    self.name_buffer += event.unicode

    def draw(self):
        self.screen.fill(BG)
        left_panel = pygame.Rect(20,20,320,320)
        pygame.draw.rect(self.screen, WHITE, left_panel)
        pygame.draw.rect(self.screen, ACCENT, left_panel, 2)
        self.draw_pet()
        self.draw_stats()
        for btn in (self.feed_btn, self.play_btn, self.rest_btn, self.clean_btn, self.health_btn, self.species_btn):
            btn.draw(self.screen)
        self.screen.blit(TITLE_FONT.render(self.pet.name, False, BLACK), (20,320-40))
        pygame.display.flip()

    def save(self):
        try:
            with open(SAVE_PATH,'w',encoding='utf-8') as f:
                json.dump(self.pet.to_dict(), f, indent=2)
        except Exception as e:
            print('save error', e)

    def load(self):
        if exists(SAVE_PATH):
            try:
                with open(SAVE_PATH,'r',encoding='utf-8') as f:
                    data = json.load(f)
                    self.pet = Pet.from_dict(data)
                    self.name_buffer = self.pet.name
            except Exception as e:
                print('load error', e)

    def run(self):
        running = True
        self.load()
        while running:
            dt = self.clock.tick(60) / 1000
            self.pet.pass_time(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            self.draw()
        self.save()


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Pet UI')
    pet = Pet()
    ui = PetUI(pet, screen)
    ui.run()

if __name__ == '__main__':
    main()

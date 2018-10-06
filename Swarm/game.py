import random
from datetime import datetime
from hashlib import md5
from sim import Clock
from inspect import signature
import random
from math import sqrt, floor


class Arguments(object):
    """
    Validates arguments passed to a method/function regardless of position.
    """

    @classmethod
    def validate(cls, func):
        params = list(signature(func).parameters)
        try:
            x_ind = params.index('x')
        except ValueError:
            x_ind = None
        try:
            y_ind = params.index('y')
        except ValueError:
            y_ind = None
        try:
            arena_ind = params.index('arena')
        except ValueError:
            arena_ind = None
        try:
            bot_ind = params.index('bot')
        except ValueError:
            bot_ind = None
        try:
            swarm_ind = params.index('swarm')
        except ValueError:
            swarm_ind = None
        try:
            suppllies_ind = params.index('supplies')
        except ValueError:
            suppllies_ind = None

        def decorator(*args, **kwargs):
            # X
            if x_ind is not None and y_ind is not None:
                x, y = args[x_ind], args[y_ind]
                if not isinstance(x, int) or not isinstance(y, int):
                    raise ValueError('x must be an integer.  x is {}'.format(type(x)))
            # Y
            if y_ind is not None:
                y = args[y_ind]
                if not isinstance(y, int):
                    raise ValueError(' y must be an integer.  y is {}'.format(type(y)))
            # Arena
            if arena_ind is not None:
                arena = args[arena_ind]
                if not isinstance(arena, Arena):
                    raise ValueError('arena must by the Arena type.  arena is {}.'.format(type(arena)))
            # Bot
            if bot_ind is not None:
                bot = args[bot_ind]
                if not isinstance(bot, Bot):
                    raise ValueError('bot must be the Bot type.  bot is {}'.format(type(bot)))
            # Swarm
            if swarm_ind is not None:
                swarm = args[swarm_ind]
                if not isinstance(swarm, Swarm):
                    raise ValueError('swarm must be the Swarm type.  bot is {}'.format(type(swarm)))
            # Supplies
            if suppllies_ind is not None:
                supplies = args[suppllies_ind]
                if not isinstance(supplies, Supplies):
                    raise ValueError('supplies must be the Supplies type.  bot is {}'.format(type(supplies)))
            return func(*args, **kwargs)

        return decorator


class Colors(object):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    ATTACK = (173, 34, 34)      # Red
    DEFENSE = (34, 82, 173)     # Blue
    REPAIR = (173, 34, 90)      # Magenta
    RANGED = (34, 173, 52)      # Green
    BUILDER = (249, 105, 9)     # Orange
    KAMIKAZE = (173, 163, 34)   # Yellow
    ASTEROID = (104, 70, 47)    # Brown
    WALL = (96, 94, 93)         # Steel
    DARK_MATTER = (45, 43, 42)  # Dark grey
    DARK_ENERGY = (58, 37, 71)  # Dark Purple
    TRADER = (0, 255, 182)      # Mint Green
    CLOAKED = BLACK             # BLACK
    UNCLOACKED = (28, 28, 28)   # ALMOST BLACK


class ShipRoles(object):
    player_roles = []
    enemy_roles = []


class Settings(object):
    bot_size = 10, 10
    display_size = 1000, 900


class Display(object):
    settings = Settings
    size = Settings.display_size
    bot_hsize = Settings.bot_size[0] // 2, Settings.bot_size[1] // 2
    grid_size = (int(size[0] / settings.bot_size[0]), int(size[1] / settings.bot_size[1]))
    grid_x = grid_size[0]
    grid_y = grid_size[1]


class Game(object):
    arena = None
    roles = ShipRoles
    colors = Colors
    settings = Settings
    display = Display
    objects = {}


class Universe(object):
    def __init__(self):
        super(Universe, self).__init__()
        self.grid = {0: {0: None}}
        self.current_sector = None

    @Arguments.validate
    def remove_sector(self, x, y):
        grid_object = self.pos(x, y)
        if grid_object is None:
            return False
        self.grid[x][y] = None
        return True

    @Arguments.validate
    def add_sector(self, x, y, arena):
        if not self.pos(x, y):
            return False
        self.grid[x][y] = arena
        return True

    @Arguments.validate
    def pos(self, x, y):
        try:
            return self.grid[x][y]
        except KeyError:
            return None

    @Arguments.validate
    def switch_arena(self, x, y):
        grid_object = self.pos(x, y)
        if grid_object is None:
            raise KeyError('There is no sector to switch to. x{}, y{} is empty'.format(x, y))

        self.current_sector = grid_object
        return True


class Arena(object):
    bots = set()
    swarms = {}
    display = Display
    game = None

    def __init__(self):
        self.bots = set()
        self.supplies = set()
        self.swarms = {}
        self.display = Display
        self.game = Game
        d = self.display
        self.grid = {i: {x: None for x in range(1, d.grid_size[1]+1)} for i in range(1, d.grid_size[0]+1)}
        self.supply_drop = None

    def remove_dead(self):
        self.bots = set(bot for bot in self.bots if not bot.is_dead)

    def remove_bots(self, bots):
        for bot in bots:
            if bot.grid_x and bot.grid_y:
                grid_item = self.grid[bot.grid_x][bot.grid_y]
                if grid_item is not None:
                    self.grid[bot.grid_x][bot.grid_y] = None
            try:
                self.bots.remove(bot)
            except KeyError:
                pass

    def spawn_swarm(self):
        now = datetime.now()
        now = Clock.now = (now.hour, now.minute, now.second, now.microsecond)
        s = Game.objects['Swarm'](name='Enemy {}'.format(md5(bytearray(str(now).encode('utf-8'))).hexdigest()), arena=self)
        m = Game.objects['MotherShipBot'](self)
        s.mothership = m
        s.add_bot(m)
        for _ in range(1, 11):
            ship = random.choice(ShipRoles.enemy_roles)(self)
            s.add_bot(ship)
            self.bots.add(ship)
        self.place_swarm(s)

    @Arguments.validate
    def drop_supplies(self, bot):
        if bot.hp > 0:
            return False
        sd = self.supply_drop(x=bot.grid_x, y=bot.grid_y)
        sd.arena = self
        self.grid[bot.grid_x][bot.grid_y] = sd
        self.supplies.add(sd)
        return self

    @Arguments.validate
    def remove_supplies(self, supplies):
        self.grid[supplies.grid_x][supplies.grid_y] = None
        try:
            self.supplies.remove(supplies)
        except KeyError:
            pass
        return self

    def remove_swarms(self):
        dels = []
        for swarm_name, swarm in self.swarms.items():
            if not swarm.bots and swarm:  # != self.swarms['Player 1']:
                dels.append(swarm_name)
        for d in dels:
            del self.swarms[d]
        if len(self.swarms.keys()) < 4:
            self.spawn_swarm()

    @Arguments.validate
    def remove_bot(self, bot):
        self.grid[bot.grid_x][bot.grid_y] = None
        if bot in bot.swarm.bots:
            bot.swarm.remove(bot)
        try:
            self.bots.remove(bot)
        except KeyError:
            pass
        return self

    @Arguments.validate
    def pos(self, x, y):
        return self.grid[x][y]

    def all_bots(self):
        return self.bots

    @Arguments.validate
    def add_bot(self, x, y, bot):
        """
        Add a bot to the arena.  Make sure you move whatever is in the grid before adding it or it will
        overwrite whatever is in the x/y on the grid.

        :param x:
        :param y:
        :param bot:
        :return:
        """

        self.grid[x][y] = bot
        self.bots.add(bot)

        return bot

    def get_random_location(self, target, proximity=10):
        x, y = target.grid_x, target.grid_y
        px = random.randint(0, 1)
        py = random.randint(0, 1)
        lx = x - proximity if not px else x
        hx = x + proximity if px else x
        ly = y - proximity if not py else y
        hy = y + proximity if py else y
        new_x = random.randint(lx, hx)
        new_y = random.randint(ly, hy)

        if new_x <= 0:
            new_x = random.randint(1, proximity)
        elif new_x >= Display.grid_x:
            new_x = random.randint(Display.grid_x - proximity, Display.grid_x)
        if new_y <= 0:
            new_y = random.randint(1, proximity)
        elif new_y == Display.grid_y:
            new_y = random.randint(Display.grid_y - proximity, Display.grid_y)

        return new_x, new_y

    @Arguments.validate
    def place_swarm(self, swarm):
        if not swarm.arena:
            swarm.arena = self

        m = swarm.mothership
        swarm.detect()
        mx, my = m.grid_x, m.grid_y = next(swarm.spawn_points)
        self.add_bot(mx, my, m)
        for bot in swarm.bots:
            if bot == m:
                continue
            x, y = bot.grid_x, bot.grid_y = next(swarm.spawn_points)
            self.add_bot(x, y, bot)

        self.swarms[swarm.name] = swarm

    @Arguments.validate
    def move_bot(self, x, y, bot):
        grid_x_size = Settings.display_size[0] / Settings.bot_size[0]
        grid_y_size = Settings.display_size[1] / Settings.bot_size[1]

        if x >= grid_x_size or y >= grid_y_size:
            return False
        try:
            if self.grid[x][y] is not None:
                return False
        except KeyError:
            return False

        if bot.grid_x and bot.grid_y:
            self.grid[bot.grid_x][bot.grid_y] = None
        bot.grid_x = x
        bot.grid_y = y
        self.grid[x][y] = bot
        # bot.detect()
        return True

    @Arguments.validate
    def add_swarm(self, swarm):
        self.swarms[swarm.name] = swarm
        self.bots.update(swarm.bots)
        if not swarm.arena:
            swarm.arena = self


class Tile(object):
    def __init__(self):
        self.grid_x = None
        self.grid_y = None
        self.solid = True


class Swarm(object):
    def __init__(self, name='', bots=None, arena=None):
        if not name:
            raise ValueError("A name must be given for the swarm.  Use the `name` kwarg to set the Swarm name.")

        self.name = name
        self.bots = set() if bots is None else bots
        for bot in self.bots:
            bot.swarm = self
        self.arena = arena
        self.groups = {1: [], 2: [], 3: [], 4: []}
        self.spawn_point = (random.randint(1, Display.grid_x), random.randint(1, Display.grid_y))
        self.grid_x, self.grid_y = self.spawn_point
        self.target = None
        self.mothership = None
        self.spawn_points = set()
        self.half_fov = 4
        self.supplies = 0
        self.detect()

        while len(list(self.spawn_points)) < 20:
            self._make_spawn()

    def _make_spawn(self):
        self.spawn_point = (random.randint(1, Display.grid_x), random.randint(1, Display.grid_y))
        self.grid_x, self.grid_y = self.spawn_point
        self.detect()

    def _swarm_update_fov(self):
        half_fov = self.half_fov
        grid_x_range = range(max((1, self.grid_x-half_fov)), min((self.grid_x+half_fov,self.arena.display.grid_size[0]+1)))
        grid_y_range = range(max((1, self.grid_y-half_fov)), min((self.grid_y+half_fov,self.arena.display.grid_size[1]+1)))
        self.spawn_points = ((gx, gy) for gx in grid_x_range for gy in grid_y_range if self.arena.grid[gx][gy] is None)
        return self

    def detect(self):
        if self.mothership:
            if self.mothership.grid_x and self.mothership.grid_y:
                self.grid_x, self.grid_y = self.mothership.grid_x, self.mothership.grid_y
        self._swarm_update_fov()

    def add_bots(self, bots):
        for bot in bots:
            bot.swarm = self
        self.bots.update(bots)
        return self

    @Arguments.validate
    def add_bot(self, bot):
        bot.swarm = self
        self.bots.add(bot)
        return self

    @Arguments.validate
    def remove(self, bot):
        try:
            self.bots.remove(bot)
        except KeyError:
            pass
        return self

    def select_targets(self):
        targets = []
        for bot in self.bots:
            targets.append(bot.select_target())
        self.target = targets[targets.index(max(targets, key=targets.count))]
        return self


class Supplies(object):
    def __init__(self, x=None, y=None):
        self.amount = random.randint(50, 300)
        self.arena = None
        self.grid_x = None if x is None else x
        self.grid_y = None if y is None else y
        self.color = (66, 244, 232)
        self.speed = 0
        self.target = None
        self.swarm = 'Supplies'
        self.is_dead = False

    def __lt__(self, other):
        return other

    def __gt__(self, other):
        return other

    def __le__(self, other):
        return other

    def __ge__(self, other):
        return other

    def select_target(self):
        return self

    def detect(self):
        return self

    def move(self):
        return self

    def attack(self):
        return self

    def destroy(self):
        self.is_dead = True
        self.arena.remove_supplies(self)
        return self


class Bot(object):
    def __init__(self, arena, x=None, y=None):
        self.health = 50
        self.hp = self.health
        self.atk = (1, 5)
        self.damage = 1.5
        self.defense = (1, 2)
        self.targeted = False
        self.repairable = True
        self.repair = False
        self.arena = arena
        self.swarm = None
        self.grid_x = None if x is None else x
        self.grid_y = None if y is None else y

        self.on_up_left = None
        self.on_up_right = None
        self.on_down_left = None
        self.on_down_right = None
        self.on_left = None
        self.on_right = None
        self.on_top = None
        self.on_bottom = None
        self.range = 1
        self.is_dead = False
        self.last_move = (0, 0)
        self.clicked_position = None

        self.target = None
        self.attacks = True
        self.repairs = False
        self.mines = False

        self.built_by = None

        self.mothership_range = 5
        self.mothership_proximity = 2

        self.speed = 1

        self.fov = 10
        self.half_fov = self.fov // 2
        self.field_of_view = set()
        self.proximity = set()

        self._last_fov_update = 0

    def __lt__(self, other):
        return other

    def __gt__(self, other):
        return other

    def __le__(self, other):
        return other

    def __ge__(self, other):
        return other

    def _update_fov(self):
        fov_list = set()
        proximity = set()

        self.proximity.clear()
        self.field_of_view.clear()

        half_fov = self.half_fov
        grid_x_range = range(max((1, self.grid_x-half_fov)), min((self.grid_x+half_fov,self.arena.display.grid_size[0]+1)))
        grid_y_range = range(max((1, self.grid_y-half_fov)), min((self.grid_y+half_fov,self.arena.display.grid_size[1]+1)))
        potential_sightings = (self.arena.grid[gx][gy] for gx in grid_x_range for gy in grid_y_range if self.arena.grid[gx][gy] is not None)
        for bot in potential_sightings:
            if bot.is_dead:
                continue
            tr = self.target_range(bot)
            if tr <= self.fov:
                fov_list.add((tr, bot))
                proximity.add(bot)

        self.proximity.update(proximity)
        self.field_of_view.update(fov_list)

    def move_towards(self, target):
        if isinstance(target, tuple):
            tx, ty = target
        else:
            tx, ty = target.grid_x, target.grid_y
        x, y = nx, ny = self.grid_x, self.grid_y

        if tx > x:
            nx = x + 1
        elif tx < x:
            nx = x - 1
        if ty > y:
            ny = y + 1
        elif ty < y:
            ny = y - 1

        return self.arena.move_bot(nx, ny, self)

    def move_away(self, target):
        tx, ty = target.grid_x, target.grid_y
        x, y = nx, ny = self.grid_x, self.grid_y

        if tx < x:
            nx = x + 1
        elif tx > x:
            nx = x - 1
        elif ty < y:
            ny = y + 1
        elif ty > y:
            ny = y - 1

        return self.arena.move_bot(nx, ny, self)

    def move(self):
        ms = self.swarm.mothership
        if ms and self != ms and not ms.is_dead:
            tr = self.target_range(ms)
            if tr > self.mothership_range:
                if self.move_towards(ms):
                    return True
            if tr <= self.mothership_proximity:
                if self.move_away(ms):
                    return True
            if ms.target and ms.target.grid_x and ms.target.grid_y and self.attacks and ms.target not in self.proximity:
                if self.move_towards(ms.target):
                    return True

        # Move mothership towards closest repair bot if health drops below 0.40 percent.
        if self == ms:
            if self.grid_x and self.grid_y and self.clicked_position:
                if self.grid_x == self.clicked_position[0] and self.grid_y == self.clicked_position[1]:
                    self.clicked_position = None
            if self.hp < self.health * 0.40:
                repair_ships = set(ship for ship in self.proximity if isinstance(ship, RepairBot) and ship.swarm == self.swarm)
                if repair_ships:
                    ship = min(repair_ships)
                    return self.move_towards(ship)
            if self.clicked_position:
                return self.move_towards(self.clicked_position)

        # If there is a target and it is out of range, move towards it
        if self.target and not self.in_range(self.target):
            if self.target.is_dead:
                self.target = None
                if self.rmove():
                    return True
                return False
            if self.target and self.move_towards(self.target):
                return True

        return self.rmove()

    def in_range(self, target):
        return self.target_range(target) <= self.range

    def rmove(self):
        surrounding_coordinates = self.surrounding_coordinates()
        random.shuffle(surrounding_coordinates)
        return self.arena.move_bot(*(*surrounding_coordinates.pop(), self))

    def surrounding_coordinates(self):
        x, y = self.grid_x, self.grid_y

        up = x, y - 1
        down = x, y + 1
        left = x - 1, y
        right = x + 1, y
        up_right = x + 1, y - 1
        up_left = x - 1, y - 1
        down_right = x + 1, y + 1
        down_left = x - 1, y + 1

        return [up, down, left, right, up_left, up_right, down_left, down_right]

    def random_coordinates(self):
        rxl = self.grid_x - 1
        rxh = self.grid_x + 1
        yxl = self.grid_y - 1
        yxh = self.grid_y + 1

        x = random.randint(rxl, rxh)
        y = random.randint(yxl, yxh)
        return x, y

    @Arguments.validate
    def x_out_of_bounds(self, x):
        return x < 1 or x > Display.grid_x

    @Arguments.validate
    def y_out_of_bounds(self, y):
        return y < 1 or y > Display.grid_y

    def detect(self):
        """
        Detect anything in the field of view and immediately surrounding.

        :return:
        """

        self._update_fov()
        # self.select_target()
        swarm = self.swarm
        mothership = False
        ms_target = False

        if swarm and swarm.mothership:
            mothership = swarm.mothership
        if mothership and mothership.target:
            ms_target = mothership.target

        if ms_target and ms_target.is_dead:
            self.swarm.mothership.target = None
        return self

    def drop_supplies(self):
        self.arena.drop_supplies(self)
        return self

    def destroy(self):
        if self.is_dead:
            return False
        self.is_dead = True
        self.arena.remove_bot(self)
        self.drop_supplies()
        self.grid_x = None
        self.grid_y = None
        self.target = None

        return self

    def in_fov(self):
        return self.field_of_view

    def select_target(self):
        enemies = set(
            target for target in self.field_of_view if not target[1].is_dead and target[1].swarm != self.swarm and target[1].swarm != 'Supplies'
        )
        if enemies:
            enemy = min(enemies)[1]
            if enemy.is_dead:
                self.arena.remove_bot(enemy)
                if enemy.swarm != 'Supplies':
                    enemy.swarm.remove(enemy)
                return self.select_target()
            self.target = enemy
            return enemy
        self.target = None
        return None

    def target_range(self, target):
        xd, yd = target.grid_x - self.grid_x, target.grid_y - self.grid_y
        return int(floor(sqrt(xd * xd + yd * yd)))

    def absorb_stats(self, target):
        self.health += target.health * 0.01
        self.atk += target.atk[0] * 0.01, target.atk[1] * 0.01
        self.defense += target.defense * 0.01
        self.range += target.range * 0.01
        if self.range > self.fov:
            self.range = self.fov

    def attack(self):
        if not self.target or self.target.is_dead or self.target_range(self.target) > self.range:
            return False

        dmg = self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)
        self.target.hp -= dmg
        if self.target.hp <= 0:
            self.target.destroy()
            self.target = None
            # Take stats from target and give it to attacker's mothership
            # todo: Fix so that things are
            if isinstance(self.target, MotherShipBot):
                ms = self.swarm.mothership
                if ms.fov < 100:
                    ms.fov += int(self.target.fov * 0.15)
                    if ms.fov > 100:
                        ms.fov = 100
                ms.health += int(self.target.health * 0.10)
                ms.atk = ms.atk[0] + self.target.atk[0], ms.atk[1] + self.target.atk[1]
                if self.target.swarm.bots:
                    for bot in self.target.swarm.bots:
                        if len(self.swarm.bots) >= 25:
                            break
                        bot.swarm = self.swarm
                        self.swarm.bots.add(bot)
                        # self.arena.remove_bot(bot)
                self.target.swarm.bots.clear()
                self.arena.remove_swarms()
                # self.arena.remove_bot(self.target)
                return self


class MotherShipBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(MotherShipBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(250, 500)
        self.hp = self.health
        self.atk = (1, 10)  # random.randint(1, 10)
        self.defense = (5, 10)
        self.speed = 1
        self.color = Colors.WHITE
        self.range = 10
        self.fov = 50
        self.half_fov = self.fov // 2

        # todo: track the last target for situations where a ship goes out of range
        # have the mothership check to see if the last target is still alive.
        # if it is then look at the last_targets_known_location variable and have
        # the mothership start a search and destroy mission.
        self.last_target = self.target
        self.last_targets_known_location = None

        # todo: Run ship scanner every 20 seconds if mothership hasn't had a target.
        # Give chance to find any enemy ship on the map and set it to the last targets
        # known location for search and destroy.


class AttackBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(AttackBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(75, 125)
        self.hp = self.health
        self.atk = (5, 10)
        self.speed = 3
        self.color = Colors.ATTACK
        self.range = 5
        self.fov = 7
        self.half_fov = self.fov // 2
        self.mothership_range = 10


class DefenseBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(DefenseBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(150, 200)
        self.hp = self.health
        self.atk = (1, 5)
        self.speed = 2
        self.color = Colors.DEFENSE
        self.fov = 6
        self.half_fov = self.fov // 2
        self.range = 2
        self.mothership_range = 6


class RangedBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(RangedBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(25, 50)
        self.hp = self.health
        self.atk = (1, 5)
        self.speed = 2
        self.color = Colors.RANGED
        self.fov = 10
        self.half_fov = self.fov // 2
        self.range = 10
        self.mothership_range = 4


class RepairBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(RepairBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(51, 74)
        self.hp = self.health
        self.repair = random.randint(5, 15)
        self.speed = 2
        self.color = Colors.REPAIR
        self.fov = 6
        self.half_fov = self.fov // 2
        self.range = 5
        self.mothership_range = 5
        self.repairs = True
        self.attacks = False

    def move(self):
        ms = self.swarm.mothership
        if ms and not ms.is_dead:
            if self.target_range(ms) > self.mothership_range:
                if self.move_towards(ms):
                    return

        if self.target and not self.target.is_dead:
            if self.target_range(self.target) > (self.range - 2):
                if self.move_towards(self.target):
                    return

        # If there is a target and it is out of range, move towards it
        if self.target and not self.in_range(self.target):
            if self.move_towards(self.target):
                return
        else:
            self.rmove()

    def attack(self):
        if not self.target or self.target.is_dead or self.target_range(self.target) > self.range:
            return False

        dmg = self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)
        self.target.hp += dmg
        if self.target.hp >= self.target.health:
            self.target.hp = self.target.health

    def select_target(self):
        allies = set([ally for ally in self.field_of_view if ally[1].swarm == self.swarm and ally[1].hp < ally[1].health])
        if allies:
            a = min(allies)
            ally = a[1]
            if ally == self:
                allies.remove((a[0], a[1]))
                if allies:
                    ally = min(allies)[1]
            self.target = ally
            return ally
        self.target = None
        return False


class BuilderBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(BuilderBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(126, 149)
        self.atk = (15, 30)
        self.hp = self.health
        self.build_rate = random.randint(1, 5)
        self.speed = 2
        self.color = Colors.BUILDER
        self.fov = 6
        self.half_fov = self.fov // 2
        self.range = 3
        self.mothership_range = 4
        self.attacks = False

    def _update_fov(self):
        """
        Helper for debugging.

        :return:
        """

        Bot._update_fov(self)
        return self

    def select_target(self):
        supplies = set([target for target in self.field_of_view if target[1].swarm == 'Supplies'])
        if supplies:
            supply_drop = min(supplies)[1]
            self.target = supply_drop
            return supply_drop
        self.target = None
        return None

    def attack(self):
        if not self.target or self.target.is_dead or self.target_range(self.target) > self.range:
            return False

        dmg = int(self.damage * random.randint(*self.atk))
        self.target.amount -= dmg
        self.swarm.supplies += dmg
        if self.target.amount <= 0:
            self.target.destroy()
        self.build()
        return self

    def build(self):
        if self.swarm.supplies < 500:
            return False

        if len(self.swarm.bots) >= 25:
            return False

        self.swarm.detect()
        if not self.swarm.spawn_points:
            return False

        # todo: Limit the amount of each ship type for building. That way the swarm does not end up
        # with 15 builder ships or 15 repair ships.

        self.swarm.supplies -= 500
        roles = [AttackBot, DefenseBot, RangedBot, RepairBot, BuilderBot, KamikazeBot]
        bot = random.choice(roles)(self.arena)
        bot.built_by = self
        self.swarm.add_bot(bot)
        bot.grid_x, bot.grid_y = next(self.swarm.spawn_points)
        self.arena.add_bot(bot.grid_x, bot.grid_y, bot)


class KamikazeBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(KamikazeBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(1, 24)
        self.hp = self.health
        self.atk = (25, 50)
        self.repairable = False
        self.speed = 4
        self.color = Colors.KAMIKAZE
        self.range = 1
        self.fov = 10
        self.half_fov = self.fov // 2
        self.mothership_range = 6
        self.attacks = False

    def _get_dmg(self):
        return self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)

    def attack(self):
        Bot.destroy(self)
        self.destroy()


if __name__ == '__main__':
    u = Universe()
    a = Arena()

    u.remove_sector(1, 5)
    u.add_sector(1, 'f', a)

    print(u)


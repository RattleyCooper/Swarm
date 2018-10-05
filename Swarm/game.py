import random
from datetime import datetime
from hashlib import md5
from sim import Clock


class GamePiece(object):
    def __init__(self, x=None, y=None):
        self.x, self.y = x, y


class Void(GamePiece):
    def __init__(self, x=None, y=None):
        super(Void, self).__init__(x=x, y=y)


class Colors(object):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    ATTACK = (173, 34, 34)      # Red
    DEFENSE = (34, 82, 173)     # Blue
    REPAIR = (173, 34, 90)      # Magenta
    RANGED = (34, 173, 52)      # Green
    BUILDER = (173, 82, 34)     # Orange
    KAMIKAZE = (173, 163, 34)   # Yellow


class ShipRoles(object):
    player_roles = []
    enemy_roles = []


class Settings(object):
    bot_size = 10, 10
    display_size = 1000, 600


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

    def drop_supplies(self, bot):
        if bot.hp > 0:
            return False
        sd = self.supply_drop(x=bot.grid_x, y=bot.grid_y)
        sd.arena = self
        self.grid[bot.grid_x][bot.grid_y] = sd
        self.supplies.add(sd)
        return self

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

    def remove_bot(self, bot):
        self.grid[bot.grid_x][bot.grid_y] = None
        if bot in bot.swarm.bots:
            bot.swarm.remove(bot)
        try:
            self.bots.remove(bot)
        except KeyError:
            pass
        return self

    def pos(self, x, y):
        return self.grid[x][y]

    def all_bots(self):
        return self.bots

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
        # while not self.move_bot(x, y, bot):
        #    x, y = self.get_random_location(bot)
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

    def place_swarm(self, swarm):
        if not swarm.arena:
            swarm.arena = self

        x, y = swarm.spawn_point

        # while swarm.mothership.grid_y is None or swarm.mothership.grid_x is None:
        #     rspawn = (random.randint(1, Display.grid_x), random.randint(1, Display.grid_y))
        #     if self.grid[rspawn[0]][rspawn[1]] is None:
        #         swarm.mothership.grid_x, swarm.mothership.grid_y = rspawn
        #         swarm.spawn_point = rspawn
        # # self.bots.add(swarm.mothership)
        m = swarm.mothership
        swarm.detect()
        mx, my = m.grid_x, m.grid_y = next(swarm.spawn_points)
        self.add_bot(mx, my, m)
        # while any([bot for bot in swarm.bots if bot.grid_x is None]):
        for bot in swarm.bots:
            if bot == m:
                continue
            # random.shuffle(m.spawn_points)
            x, y = bot.grid_x, bot.grid_y = next(swarm.spawn_points)

            # bot.grid_x, bot.grid_y = m.grid_x, m.grid_y
            # m.move()
            self.add_bot(x, y, bot)
            #new_x, new_y = self.get_random_location(swarm.mothership)
            # bot.rmove()
            # new_x, new_y = self.get_random_location(swarm.mothership)
            # p = 10
            # moved = False
            # while not moved:
            #     moved = self.move_bot(new_x, new_y, bot)
            #     new_x, new_y = self.get_random_location(swarm.mothership, proximity=p)
            #     p += 1
            #     if p >= 15:
            #        p = 10
            # if bot not in self.bots:
            #     self.bots.add(bot)

        self.swarms[swarm.name] = swarm

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

    def add_swarm(self, swarm):
        self.swarms[swarm.name] = swarm
        self.bots.update(swarm.bots)
        if not swarm.arena:
            swarm.arena = self


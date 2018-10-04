import random


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


class Settings(object):
    bot_size = 10, 10
    display_size = 1840, 1000


class Display(object):
    settings = Settings
    size = Settings.display_size
    grid_size = (int(size[0] / settings.bot_size[0]), int(size[1] / settings.bot_size[1]))
    grid_x = grid_size[0]
    grid_y = grid_size[1]


class Arena(object):
    bots = []
    swarms = {}
    display = Display

    def __init__(self):
        self.bots = []
        self.supplies = []
        self.swarms = {}
        self.display = Display
        d = self.display
        self.grid = {i: {x: None for x in range(1, d.grid_size[1]+1)} for i in range(1, d.grid_size[0]+1)}
        self.supply_drop = None

    def drop_supplies(self, bot):
        if bot.hp > 0:
            return False
        sd = self.supply_drop(x=bot.grid_x, y=bot.grid_y)
        sd.arena = self
        self.grid[bot.grid_x][bot.grid_y] = sd
        self.supplies.append(sd)
        return self

    def remove_supplies(self, supplies):
        self.grid[supplies.grid_x][supplies.grid_y] = None
        if supplies in self.supplies:
            self.supplies.remove(supplies)
        return self

    def remove_swarms(self):
        dels = []
        for swarm_name, swarm in self.swarms.items():
            if not swarm.bots:
                dels.append(swarm_name)
        for d in dels:
            del self.swarms[d]

    def remove_bot(self, bot):
        self.grid[bot.grid_x][bot.grid_y] = None
        try:
            self.bots.remove(bot)
        except ValueError:
            pass
        return self

    def pos(self, x, y):
        return self.grid[x][y]

    def all_bots(self):
        return self.bots

    def add_bot(self, x, y, bot):
        self.grid[x][y] = bot
        self.bots.append(bot)
        while not self.move_bot(x, y, bot):
            x, y = self.get_random_location(bot)
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
        return new_x, new_y

    def place_swarm(self, swarm):
        x, y = swarm.spawn_point

        while any([bot for bot in swarm.bots if bot.grid_x is None]):
            f = 1
            new_x, new_y = x, y
            for bot in swarm.bots:
                while not self.move_bot(new_x, new_y, bot):
                    px = random.randint(0, 1)
                    py = random.randint(0, 1)
                    lx = x - 10 if not px else x
                    hx = x + 10 if px else x
                    ly = y - 10 if not py else y
                    hy = y + 10 if py else y
                    new_x = random.randint(lx, hx)
                    new_y = random.randint(ly, hy)

                if bot not in self.bots:
                    self.bots.append(bot)
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
        bot.detect()
        return True

    def add_swarm(self, swarm):
        self.swarms[swarm.name] = swarm
        self.bots += swarm.bots


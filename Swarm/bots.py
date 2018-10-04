import random
from math import sqrt

try:
    from game import Arena, Colors, Display, Void
except ImportError:
    from .game import Arena, Colors, Display, Void


class Swarm(object):
    def __init__(self, name='', bots=None):
        if not name:
            raise ValueError("A name must be given for the swarm.  Use the `name` kwarg to set the Swarm name.")

        self.name = name
        self.bots = [] if bots is None else bots
        for bot in self.bots:
            bot.swarm = self
        self.groups = {1: [], 2: [], 3: [], 4: []}
        self.spawn_point = (random.randint(1, Display.grid_x), random.randint(1, Display.grid_y))
        self.target = None
        self.mothership = None

        self.supplies = 0

    def detect(self):
        for bot in self.bots:
            bot.detect()

    def add_bots(self, bots):
        for bot in bots:
            bot.swarm = self
        self.bots += bots
        return self

    def add_bot(self, bot):
        bot.swarm = self
        self.bots.append(bot)
        return self

    def remove(self, bot):
        try:
            self.bots.remove(bot)
        except ValueError:
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

        self.target = None
        self.attacks = True
        self.repairs = False
        self.mines = False

        self.built_by = None

        self.mothership_range = 5
        self.mothership_proximity = 2

        self.speed = 1

        self.fov = 10
        self.field_of_view = []

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
        self.field_of_view = []
        for bot in self.arena.bots + self.arena.supplies:
            tr = self.target_range(bot)
            if tr <= self.fov:
                self.field_of_view.append((tr, bot))

    def move_towards(self, target):
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

        self.arena.move_bot(nx, ny, self)

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

        self.arena.move_bot(nx, ny, self)

    def move(self):
        # todo: if mothership is low on health and a repair ship exists, move towards that.

        ms = self.swarm.mothership
        if ms and self != ms:
            tr = self.target_range(ms)
            if tr > self.mothership_range:
                self.move_towards(ms)
                return
            if tr <= self.mothership_proximity:
                self.move_away(ms)
                return
            if ms.target and self.attacks:
                self.move_towards(ms.target)

        # If there is a target and it is out of range, move towards it
        if self.target and not self.in_range(self.target):
            if self.target.is_dead:
                self.target = None
                self.rmove()
                return
            self.move_towards(self.target)
            return

        self.rmove()

    def in_range(self, target):
        return self.target_range(self.target) <= self.range - 1

    def rmove(self):
        rxl = self.grid_x - 1
        rxh = self.grid_x + 1
        yxl = self.grid_y - 1
        yxh = self.grid_y + 1

        x = random.randint(rxl, rxh)
        y = random.randint(yxl, yxh)
        self.arena.move_bot(x, y, self)

    def x_out_of_bounds(self, x):
        return x < 1 or x > Display.grid_x

    def y_out_of_bounds(self, y):
        return y < 1 or y > Display.grid_y

    def detect(self):
        """
        Detect anything in the field of view and immediately surrounding.

        :return:
        """

        self._update_fov()
        self.select_target()
        return self

    def drop_supplies(self):
        self.arena.drop_supplies(self)
        return self

    def destroy(self):
        self.is_dead = True
        self.arena.remove_bot(self)
        try:
            self.swarm.bots.remove(self)
        except ValueError:
            pass
        self.drop_supplies()
        return self

    def in_fov(self):
        return self.field_of_view

    def select_target(self):
        enemies = [target for target in self.field_of_view if target[1].swarm != self.swarm and target[1].swarm != 'Supplies']
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
        return int(sqrt(xd * xd + yd * yd))

    def attack(self):
        if not self.target or self.target_range(self.target) > self.range:
            return False

        dmg = self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)
        self.target.hp -= dmg
        if self.target.hp <= 0:
            self.target.destroy()
            if isinstance(self.target, MotherShipBot):
                ms = self.swarm.mothership
                ms.fov += self.target.fov
                ms.health += int(self.target.health * 0.10)
                ms.atk = ms.atk[0] + self.target.atk[0], ms.atk[1] + self.target.atk[1]
                if self.target.swarm.bots:
                    for bot in self.target.swarm.bots:
                        bot.swarm = self.swarm
                        self.swarm.bots.append(bot)
                        # self.arena.remove_bot(bot)
                self.target.swarm.bots.clear()
                del self.arena.swarms[self.target.swarm.name]
                self.arena.remove_bot(self.target)
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


class AttackBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(AttackBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(75, 125)
        self.hp = self.health
        self.atk = (5, 10)
        self.speed = 3
        self.color = Colors.ATTACK
        self.range = 3
        self.fov = 7
        self.mothership_range = 12


class DefenseBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(DefenseBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(150, 200)
        self.hp = self.health
        self.atk = (1, 5)
        self.speed = 2
        self.color = Colors.DEFENSE
        self.fov = 6
        self.range = 2
        self.mothership_range = 3


class RangedBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(RangedBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(25, 50)
        self.hp = self.health
        self.atk = (1, 5)
        self.speed = 2
        self.color = Colors.RANGED
        self.fov = 10
        self.range = 7
        self.mothership_range = 8


class RepairBot(Bot):
    def __init__(self, arena, x=None, y=None):
        super(RepairBot, self).__init__(arena, x=x, y=y)
        self.health = random.randint(51, 74)
        self.hp = self.health
        self.repair = random.randint(5, 15)
        self.speed = 2
        self.color = Colors.REPAIR
        self.fov = 6
        self.range = 5
        self.mothership_range = 7
        self.repairs = True
        self.attacks = False

    def move(self):
        ms = self.swarm.mothership
        if ms:
            if self.target_range(ms) > self.mothership_range:
                return self.move_towards(ms)

        if self.target:
            if self.target_range(self.target) > (self.range - 2):
                return self.move_towards(self.target)

        # If there is a target and it is out of range, move towards it
        if self.target and not self.in_range(self.target):
            self.move_towards(self.target)
        else:
            self.rmove()

    def attack(self):
        if not self.target or self.target_range(self.target) > self.range:
            return False

        dmg = self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)
        self.target.hp += dmg
        if self.target.hp >= self.target.health:
            self.target.hp = self.target.health

    def select_target(self):
        allies = [ally for ally in self.field_of_view if ally[1].swarm == self.swarm and ally[1].hp < ally[1].health]
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
        self.range = 3
        self.mothership_range = 4
        self.attacks = False

    def select_target(self):
        supplies = [target for target in self.field_of_view if target[1].swarm == 'Supplies']
        if supplies:
            supply_drop = min(supplies)[1]
            self.target = supply_drop
            return supply_drop
        self.target = None
        return None

    def attack(self):
        if not self.target or self.target_range(self.target) > self.range:
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

        if len(self.swarm.bots) >= 35:
            return False

        self.swarm.supplies -= 500
        roles = [AttackBot, DefenseBot, RangedBot, RepairBot, BuilderBot, KamikazeBot]
        bot = random.choice(roles)(self.arena)
        bot.built_by = self
        self.swarm.add_bot(bot)
        bot.grid_x, bot.grid_y = self.grid_x, self.grid_y
        self.move()
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
        self.mothership_range = 10

    def _get_dmg(self):
        return self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)

    def attack(self):
        if not self.target or self.target_range(self.target) > self.range:
            return False

        dmg = self._get_dmg()
        self.target.hp -= dmg
        if self.target.hp <= 0:
            self.target.destroy()

        for rng, bot in self.in_fov():
            if bot.swarm != self.swarm and bot.swarm != 'Supplies' and rng <= self.range:
                bot.hp -= self._get_dmg()
                if bot.hp <= 0:
                    bot.destroy()
        self.destroy()

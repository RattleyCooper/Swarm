import random
from math import sqrt, floor

try:
    from game import Arena, Colors, Display, Void
except ImportError:
    from .game import Arena, Colors, Display, Void


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
        self._swarm_update_fov()

    def add_bots(self, bots):
        for bot in bots:
            bot.swarm = self
        self.bots.update(bots)
        return self

    def add_bot(self, bot):
        bot.swarm = self
        self.bots.add(bot)
        return self

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

    # def spawn(self):
    #     spawnables = [s for s in self.bots if s.grid_x and s.grid_y and self.arena.grid[s.grid_x][s.grid_y] is None]
    #     if spawnables:
    #         ship = spawnables.pop()
    #         x, y = ship.last_move
    #         self.arena.move_bot(x, y, ship)


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
        self.last_move = (0, 0)

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
        #if isinstance(self, MotherShipBot):
        #    self.spawn_points = ((gx, gy) for gx in grid_x_range for gy in grid_y_range if self.arena.grid[gx][gy] is None)
        for bot in potential_sightings:
            if bot.is_dead:
                continue
            tr = self.target_range(bot)
            if tr <= self.fov:
                fov_list.add((tr, bot))
                proximity.add(bot)

        self.proximity.update(proximity)
        self.field_of_view.update(fov_list)

    def _move(self, x_same, y_same, nx, ny):
        if self.arena.grid[nx][ny] is None:
            return self.arena.move_bot(nx, ny, self)
        else:
            if x_same and not self.arena.move_bot(nx + 1, ny, self):
                return self.arena.move_bot(nx - 1, ny, self)
            elif y_same and not self.arena.move_bot(nx, ny + 1, self):
                return self.arena.move_bot(nx, ny - 1, self)

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

        #self._move(tx == x, ty == y, nx, ny)
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
        if ms and self != ms:
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
            if self.hp < self.health * 0.40:
                repair_ships = set(ship for ship in self.proximity if isinstance(ship, RepairBot) and ship.swarm == self.swarm)
                if repair_ships:
                    ship = min(repair_ships)
                    if self.move_towards(ship):
                        return True

        # If there is a target and it is out of range, move towards it
        if self.target and not self.in_range(self.target):
            if self.target.is_dead:
                self.target = None
                if self.rmove():
                    return True
            if self.target and self.move_towards(self.target):
                return True

        return self.rmove()

    def in_range(self, target):
        return self.target_range(target) <= self.range

    def rmove(self):
        x, y = self.random_coordinates()
        self.last_move = x, y
        sc = self.surrounding_coordinates()
        random.shuffle(sc)
        move = (*sc.pop(), self)
        return self.arena.move_bot(*move)

    def surrounding_coordinates(self):
        x, y = self.grid_x, self.grid_y
        xl = self.grid_x - 1
        xh = self.grid_x + 1
        yl = self.grid_y - 1
        yh = self.grid_y + 1

        up = x, y - 1
        down = x, y + 1
        left = x - 1, y
        right = x + 1, y
        up_right = x + 1, y - 1
        up_left = x - 1, y - 1
        down_right = x + 1, y + 1
        down_left = x - 1, y + 1

        return [up, down, left, right, up_left, up_right]

    def random_coordinates(self):
        rxl = self.grid_x - 1
        rxh = self.grid_x + 1
        yxl = self.grid_y - 1
        yxh = self.grid_y + 1

        x = random.randint(rxl, rxh)
        y = random.randint(yxl, yxh)
        return x, y

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

    def attack(self):
        if not self.target or self.target_range(self.target) > self.range:
            return False

        dmg = self.damage * random.randint(*self.atk) - (random.randint(*self.target.defense) * 0.25)
        self.target.hp -= dmg
        if self.target.hp <= 0:
            self.target.destroy()
            self.target.is_dead = True
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
                            continue
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
        if ms:
            if self.target_range(ms) > self.mothership_range:
                if self.move_towards(ms):
                    return

        if self.target:
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
        if not self.target or self.target_range(self.target) > self.range:
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

        if len(self.swarm.bots) >= 25:
            return False

        self.swarm.detect()
        if not self.swarm.spawn_points:
            return False

        # todo: Limit the amount of each bot type for building. That way the swarm does not end up
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
        self.mothership_range = 10
        self.attacks = False

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

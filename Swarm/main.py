import random
from datetime import datetime

import pygame

from bots import AttackBot, DefenseBot, RangedBot, RepairBot
from bots import BuilderBot, KamikazeBot, Swarm, MotherShipBot, Supplies
from game import Display, Settings, Arena, Colors
from sim import Queue, QueueControl, ClockControl


class Threads(object):
    threads = []


def setup():
    q1 = Queue()
    QueueControl.queues.append(q1)

    Settings.display_size = 1840, 1000
    Settings.bot_size = 10, 10
    Display.size = Settings.display_size
    BOT_SIZE = Settings.bot_size
    arena = Arena()
    arena.supply_drop = Supplies
    roles = [AttackBot, DefenseBot, RangedBot, RepairBot, BuilderBot, KamikazeBot]
    enemy_roles = [AttackBot, DefenseBot, RangedBot, KamikazeBot]

    player_swarm = Swarm(name='Player 1')
    for i in range(15):
        player_swarm.add_bot(random.choice(roles)(arena))

    for i in range(1, 11):
        s = Swarm(name='Enemy {}'.format(i))
        m = MotherShipBot(arena)
        s.mothership = m
        s.add_bot(m)
        for _ in range(1, 10):
            s.add_bot(random.choice(roles)(arena))
        arena.place_swarm(s)

    player_swarm.mothership = MotherShipBot(arena)

    player_swarm.add_bot(player_swarm.mothership)

    arena.place_swarm(player_swarm)

    pygame.init()

    # Set the width and height of the screen [width, height]
    size = Display.size
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Swarm")

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    main(clock, screen, pygame, arena, done)


def draw_callback(bot, count):
    if bot.speed >= 1 and count % 15 == 0:
        bot.move()
        bot.attack()
    elif bot.speed >= 2 and count % 10 == 0:
        bot.move()
        bot.attack()
    elif bot.speed >= 3 and count % 5 == 0:
        bot.move()
        bot.attack()
    elif bot.speed >= 4 and count % 3 == 0:
        bot.move()
        bot.attack()


def govern_speed(x, y, bot, count):
    arena = bot.arena
    if bot.speed >= 1 and count % 10 == 0:
        arena.move_bot(x, y, bot)
    elif bot.speed >= 2 and count % 10 == 0:
        arena.move_bot(x, y, bot)
    elif bot.speed >= 3 and count % 5 == 0:
        arena.move_bot(x, y, bot)
    elif bot.speed >= 4 and count % 3 == 0:
        arena.move_bot(x, y, bot)


def process_move(event, player_mothership, count, auto_move=False):
    pm = player_mothership
    if event.key == 273 or event.key == 119:  # UP OR W
        govern_speed(pm.grid_x, pm.grid_y - 1, pm, count)
    elif event.key == 276 or event.key == 97:  # LEFT OR A
        govern_speed(pm.grid_x - 1, pm.grid_y, pm, count)
    elif event.key == 274 or event.key == 115:  # DOWN OR S
        govern_speed(pm.grid_x, pm.grid_y + 1, pm, count)
    elif event.key == 275 or event.key == 100:  # RIGHT OR D
        govern_speed(pm.grid_x + 1, pm.grid_y, pm, count)


# -------- Main Program Loop -----------
def main(clock, screen, pygame, arena, done):
    count = 0
    BOT_SIZE = Settings.bot_size

    now = datetime.now()
    now = (now.hour, now.minute, now.second)
    last = now

    player_swarm = arena.swarms['Player 1']
    pm = player_swarm.mothership
    moving = False
    moving_keys = [273, 274, 275, 276, 97, 100, 115, 119]
    auto_move = False
    while not done:
        if count % 10000 == 0:
            count = 0

        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                process_move(event, pm, count)
                if event.key in moving_keys:
                    moving = event
                if event.key == 9:
                    auto_move = True if not auto_move else False
                    print('auto_move:', auto_move)
                print(event.key)
            elif event.type == pygame.KEYUP:
                if event.key in moving_keys:
                    moving = False
            elif event.type == pygame.QUIT:
                done = True

        # --- Game logic should go here

        # --- Screen-clearing code goes here

        # Here, we clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.

        # If you want a background image, replace this clear with blit'ing the
        # background image.
        screen.fill(Colors.BLACK)

        # --- Drawing code should go here
        all_bots = arena.all_bots() + arena.supplies

        for bot in all_bots:
            bot.detect()
            if bot.target:
                pygame.draw.line(screen, bot.color, [bot.grid_x*10, bot.grid_y*10], [bot.target.grid_x*10, bot.target.grid_y*10], 1)
            if isinstance(bot.swarm, Swarm) and bot.swarm.name == 'Player 1':
                e = pygame.draw.ellipse(screen, bot.color, [bot.grid_x * BOT_SIZE[0], bot.grid_y * BOT_SIZE[1], BOT_SIZE[0], BOT_SIZE[1]], 0)
            elif isinstance(bot, Supplies):
                e = pygame.draw.rect(screen, bot.color, [bot.grid_x * BOT_SIZE[0], bot.grid_y * BOT_SIZE[1], BOT_SIZE[0], BOT_SIZE[1]], 0)
            else:
                e = pygame.draw.rect(screen, bot.color, [bot.grid_x * BOT_SIZE[0], bot.grid_y * BOT_SIZE[1], BOT_SIZE[0], BOT_SIZE[1]], 0)

            if isinstance(bot, MotherShipBot) and bot.swarm == player_swarm:
                if moving:
                    process_move(moving, pm, count)
                elif auto_move:
                    draw_callback(bot, count)
            else:
                draw_callback(bot, count)

        now = datetime.now()
        now = (now.hour, now.minute, now.second)
        if now[2] % 5 == 0 and last != now:
            arena.remove_swarms()
            last = now
            # print('Removing Dead Swarms...')

        # --- Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # --- Limit to 60 frames per second
        count += 1
        clock.tick(30)

    # Close the window and quit.
    pygame.quit()


if __name__ == '__main__':
    setup()
    QueueControl.shutdown = True
    ClockControl.shutdown = True
    for thread in Threads.threads:
        thread.join()
    print('done')


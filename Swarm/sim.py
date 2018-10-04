import random
from time import sleep
from datetime import datetime


class ClockControl(object):
    shutdown = False


class Clock(object):
    def __init__(self):
        self.last = (0, 0, 0)
        now = datetime.now()
        self.now = (now.hour, now.minute, now.second)
        self.confirmed = False

    def _set(self):
        now = datetime.now()
        self.now = (now.hour, now.minute, now.second)

    def start(self):
        while not ClockControl.shutdown:
            self._set()
            if self.last != self.now and not self.confirmed:
                self.last = self.now
                self.confirmed = True


class QueueControl(object):
    shutdown = False
    threads = []
    queues = []


class Queue(object):
    def __init__(self):
        self.data = []
        self.alive = False

    def push(self, function, args=None, kwargs=None):
        self.data.append((function, args, kwargs))

    def main(self):
        self.alive = True
        while not QueueControl.shutdown:
            while self.data:
                try:
                    function, args, kwargs = self.data.pop(0)
                    function(*args, **kwargs if kwargs else {})
                except IndexError:
                    continue
        self.alive = False


def chunks(itterable, size):
    output = []

    while itterable:
        rng = itterable[:size]
        output.append(rng)
        del itterable[:size]
    return output


def chunks_fit(l, n):
    """Yield successive n-sized chunks from l."""

    for i in range(0, len(l), n):
        yield l[i:i + n]


def chunks_fit2(itterable, lists):
    ilen = len(itterable)
    slen = int(ilen / lists)

    output = []
    while itterable:
        rng = itterable[:slen]
        output.append(rng)
        del itterable[:slen]
    return output


if __name__ == '__main__':
    l1 = []
    for i in range(50, random.randint(150,200)):
        l1.append(random.randint(1000, 5000))

    l2 = l1.copy()

    c = chunks_x(l1, 4)
    print('done')

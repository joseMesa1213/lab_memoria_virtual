import sys
from collections import OrderedDict


def pages_of(path, page_size):
    for raw in open(path):
        tokens = raw.split('#')[0].split()
        if not tokens or tokens[0] not in ('read', 'write'):
            continue
        yield int(tokens[1], 0) // page_size


def fifo(refs, frames):
    queue, loaded, faults = [], set(), 0
    for page in refs:
        if page in loaded:
            continue
        faults += 1
        if len(loaded) == frames:
            loaded.discard(queue.pop(0))
        queue.append(page)
        loaded.add(page)
    return faults


def lru(refs, frames):
    order, faults = OrderedDict(), 0
    for page in refs:
        if page in order:
            order.move_to_end(page)
            continue
        faults += 1
        if len(order) == frames:
            order.popitem(last=False)
        order[page] = True
    return faults


def clock(refs, frames):
    slots, referenced, where, hand, faults = [], [], {}, 0, 0
    for page in refs:
        if page in where:
            referenced[where[page]] = True
            continue
        faults += 1
        if len(slots) < frames:
            where[page] = len(slots)
            slots.append(page)
            referenced.append(True)
            continue
        while referenced[hand]:
            referenced[hand] = False
            hand = (hand + 1) % frames
        del where[slots[hand]]
        slots[hand] = page
        referenced[hand] = True
        where[page] = hand
        hand = (hand + 1) % frames
    return faults


if __name__ == '__main__':
    path, page_size, frames = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    refs = list(pages_of(path, page_size))
    print(f"FIFO,{fifo(refs, frames)}")
    print(f"LRU,{lru(refs, frames)}")
    print(f"CLOCK,{clock(refs, frames)}")

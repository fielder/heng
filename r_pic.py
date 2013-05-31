import collections
import struct

import hvars

WadSprite = collections.namedtuple("WadSprite", "w h left_off top_off raw")
Pixmap = collections.namedtuple("Pixmap", "w h left_off top_off pixels")

# raw lump data, keyed by lump name
cached = {}

ascii_chars = {}
ascii_max_w = 0
ascii_max_h = 0


def init():
    global ascii_max_w
    global ascii_max_h

    # load ASCII
    names = filter(lambda x: x.startswith("STCFN"), hvars.iwad.lump_names)
    lumps = [hvars.iwad.readLump(n) for n in names]
    for name, raw in zip(names, lumps):
        num = int(name[-3:], 10)
        ascii_chars[chr(num)] = spriteFromRaw(raw)

    ascii_max_w = max([ac.w for ac in ascii_chars.itervalues()])
    ascii_max_h = max([ac.h for ac in ascii_chars.itervalues()])


def get(name):
    try:
        return cached[name]
    except KeyError:
        cached[name] = hvars.iwad.readLump(name)
        return cached[name]


def free(name):
    del(cached[name])


def spriteFromRaw(raw):
    w, h, l_off, t_off = struct.unpack("<hhhh", raw[:8])
    return WadSprite(w, h, l_off, t_off, raw)


# cached images, drawn out to a basic pixmap
cached_pixmap = {}


def getPixmap(name):
    try:
        return cached_pixmap[name]
    except KeyError:
        cached_pixmap[name] = pixmapFromRaw(hvars.iwad.readLump(name))
        return cached_pixmap[name]


def freePixmap(name):
    del(cached_pixmap[name])


def pixmapFromRaw(raw):
    w, h, l_off, t_off = struct.unpack("<hhhh", raw[:8])

    pixels = " " * (w * h)
    hvars.c_api.DrawSpriteToPixmap(raw, pixels)

    return Pixmap(w, h, l_off, t_off, pixels)

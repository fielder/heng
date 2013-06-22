import zipfile
import struct
import ctypes

import hvars

MAP_VERSION = 2


def read(path):
    ret = {}

    with zipfile.ZipFile(path, "r") as zh:
        ident, ver = struct.unpack("<4si", zh.read("header"))
        if ident != "HENG":
            raise ValueError("invalid map file")
        if ver != MAP_VERSION:
            raise ValueError("invalid map version %d" % ver)

        for f in zh.filelist:
            if f.filename == "header":
                continue

            ret[f.filename] = zh.read(f.filename)

    return ret


def load(path):
    m = read(path)

    raw = m["vertices"]
    hvars.c_api.Map_LoadVertices(ctypes.c_char_p(raw), len(raw))

    raw = m["edges"]
    hvars.c_api.Map_LoadEdges(ctypes.c_char_p(raw), len(raw))

    raw = m["planes"]
    hvars.c_api.Map_LoadPlanes(ctypes.c_char_p(raw), len(raw))

    raw = m["polyedges"]
    hvars.c_api.Map_LoadPolyEdges(ctypes.c_char_p(raw), len(raw))

    raw = m["polys"]
    hvars.c_api.Map_LoadPolys(ctypes.c_char_p(raw), len(raw))

    print "Loaded \"%s\"" % path

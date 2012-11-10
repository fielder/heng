#!/usr/bin/env python

import sys
import os

import pygame

import hvars
import io
import r_main
from utils import wad

if len(sys.argv) != 3:
    print "usage: %s <iwad> <hwa map file>" % sys.argv[0]
    sys.exit(0)

hvars.iwad = wad.Wad(sys.argv[1])
hvars.hwa = None

do_quit = 0

io.init()
r_main.init()

while not do_quit:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            do_quit = 1
        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_ESCAPE:
                do_quit = 1
            elif ev.key == ord("f"):
                print hvars.fps_rate
    r_main.refresh()
    io.swapBuffer()

io.shutdown()

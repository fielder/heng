RENDER_SO = "./render.so"

WIDTH = 320 * 1
HEIGHT = 240 * 1

# camera stuff
PITCH = 0
YAW   = 1
ROLL  = 2

fov_x = 0.0 # radians
fov_y = 0.0 # radians
pos = None
angles = None # radians
left = None
up = None
forward = None

# draw buffer used by C renderer
screen = None

fps_framecount = 0
fps_last_start = 0
fps_rate = 0.0

frametime = 0.0

iwad = None

c_api = None

do_quit = 0

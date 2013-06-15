import hvars
import r_pic

up = False
con_height = 0
text = ""


def write(s):
    global text

    text += s


def toggle():
    global up

    up = not up


def _drawBackground(height):
    pic = r_pic.get("FLOOR0_6")

    W = 64
    H = 64

    left = 0
    while left < hvars.WIDTH:
        bottom = height - 1
        while bottom >= 0:
            hvars.c_api.DrawPixmap(pic, W, H, left, bottom - H + 1)
            bottom -= H
        left += W


def drawString(s, x, y):
    if y >= hvars.HEIGHT:
        return

    for c in s.upper():
        if x >= hvars.WIDTH:
            break

        if c in r_pic.ascii_chars:
            ac = r_pic.ascii_chars[c]
            if x + ac.w > 0:
                hvars.c_api.DrawSprite(ac.raw, x, y)
            x += ac.w
        else:
            x += 4


def _splitLinesReversed():
    idx = len(text) - 1
    while idx >= 0:
        end = idx
        while idx >= 0 and text[idx] != "\n":
            idx -= 1
        yield text[idx + 1:end + 1]
        idx -= 1


def _stringWidth(s):
    width = 0
    for c in s:
        if c in r_pic.ascii_chars:
            width += r_pic.ascii_chars[c].w
        else:
            width += 4
    return width


def _nextChunk(line, idx):
    if line[idx] not in r_pic.ascii_chars:
        return " "
    start = idx
    while idx < len(line) and line[idx] in r_pic.ascii_chars:
        idx += 1
    return line[start:idx]


def _chopLine(line):
    return [line]
#   ret = []

#   idx = 0
#   x = 1
#   while idx < len(line):
#       chunk = _nextChunk(line, idx)
#       chunkw = _stringWidth(chunk)
#       if x + chunkw >= hvars.WIDTH - 1:
#           x = 8
#           ret.append(line
#       pass

#   return ret


def _drawText(height):
    y_stride = r_pic.ascii_max_h + 1

    y = height - y_stride
    y -= y_stride # leave an empty line for input

    for line in _splitLinesReversed():
        if y < 0: break #TODO: remove when we can clip sprites on the top/bottom
        if y + r_pic.ascii_max_h <= 0:
            break

        # we don't store the text in upper-case, but upper it when drawing
        line = line.upper()

        # chop the line up to fit on the screen and draw on multiple
        # lines if necessary
        sublines = _chopLine(line)
        y -= y_stride * (len(sublines) - 1)
        start_x = 1
        subl_y = y
        for subl in sublines:
            drawString(subl, start_x, subl_y)
            start_x = 8
            subl_y += y_stride

        y -= y_stride


def draw(height):
    _drawBackground(height)
    _drawText(height)

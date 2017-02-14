import os
import random
import cStringIO
import io
import base64
import json
from random import shuffle, choice
from datetime import datetime
import uuid 
from PIL import Image, ImageDraw, ImageFont

panelheight = 300
panelwidth = 450

def comic(msgs, title=''):
    # create a unique list of the users
    chars = set([x['user'] for x in msgs])

    panels = []
    panel = []

    for m in msgs:
        char = m['user']
        msg = m['message']
        # if the panel already has 2 message or the next message is by the same
        # person, we append it to the panels list and start a new one
        if len(panel) == 2 or len(panel) == 1 and panel[0][0] == char:
            panels.append(panel)
            panel = []
        panel.append((char, msg))
    panels.append(panel)

    b = io.BytesIO()
    if len(title) > 0:
        make_comic(chars, panels, title).save(b, 'jpeg', quality=86)
    else:
        make_comic(chars, panels).save(b, 'jpeg', quality=86) 
    return b.getvalue()

# text wrapping
def wrap(st, font, draw, width):
    st = st.split() # split the input into words
    mw = 0 # the max width we found
    mh = 0 # the max height we found
    ret = [] # the split text to return

    while len(st) > 0:
        s = 1
        # keep adding words until either we run out or the current line is
        # wider than max width
        while True and s < len(st):
            w, h = draw.textsize(" ".join(st[:s]), font=font)
            if w > width:
                s -= 1
                break
            else:
                s += 1

        # we've hit a case where the current line is wider than the screen.
        # just draw it
        if s == 0 and len(st) > 0:
            s = 1

        w, h = draw.textsize(" ".join(st[:s]), font=font)
        mw = max(mw, w)
        mh += h
        ret.append(" ".join(st[:s]))
        st = st[s:]

    return (ret, (mw, mh))

def rendertext(st, font, draw, pos):
    ch = pos[1]
    # for each line
    for s in st:
        s = unicode(s)
        w, h = draw.textsize(s, font=font)
        h = int(h)
        # PIL doesn't do borders, so we draw the text offset in black a bunch of times then on top
        # of that in white
        for i in range(1,2):
            draw.text((pos[0]-i, ch-i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((pos[0]-i, ch+i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((pos[0]+i, ch-i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((pos[0]+i, ch+i), s, font=font, fill=(0x0,0x0,0x0,0x0))
        draw.text((pos[0], ch), s, font=font, fill=(0xff,0xff,0xff,0xff))
        ch += h

def rendertitle(st, font, draw, pos):
    w, h = draw.textsize(st[0], font=font)
    ch = (300 - (h * len(st)))/2
    for s in st:
        s = unicode(s)
        w, h = draw.textsize(s, font=font)
        h = int(h)
        x = (450 - w)/2
        for i in range(1,2):
            draw.text((x-i, ch-i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((x-i, ch+i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((x+i, ch-i), s, font=font, fill=(0x0,0x0,0x0,0x0))
            draw.text((x+i, ch+i), s, font=font, fill=(0x0,0x0,0x0,0x0))
        draw.text((x, ch), s, font=font, fill=(0xff,0xff,0xff,0xff))
        ch += h

# figures out the best way to fit an image in the given dimensions, preserving the aspect ratio
def fitimg(img, (width, height)):
    scale1 = float(width) / img.size[0]
    scale2 = float(height) / img.size[1]

    l1 = (img.size[0] * scale1, img.size[1] * scale1)
    l2 = (img.size[0] * scale2, img.size[1] * scale2)

    if l1[0] > width or l1[1] > height:
        l = l2
    else:
        l = l1

    return img.resize((int(l[0]), int(l[1])), Image.ANTIALIAS)

def make_comic(chars, panels, title=False):
    # get the list of images. this should really be done on startup, no?
    filenames = os.listdir('comic/chars/')
    shuffle(filenames)
    filenames = map(lambda x: os.path.join('comic/chars', x), filenames[:len(chars)])

    # associate characters with images
    chars = list(chars)
    chars = zip(chars, filenames)
    charmap = dict()
    for ch, f in chars:
        # support for multiple images per character. if we found a directory
        # store all of the images in it as the value, else just the one image
        if os.path.isdir(f):
            charmap[ch] = []
            for fi in os.listdir(f):
                charmap[ch].append(Image.open(os.path.join(f, fi)))
        else:
            charmap[ch] = [Image.open(f)]

    imgwidth = panelwidth
    imgheight = panelheight * len(panels)
    if title:
        imgheight += panelheight

    bg = Image.open(os.path.join('comic/backgrounds', random.choice(os.listdir('comic/backgrounds'))))

    im = Image.new("RGBA", (imgwidth, imgheight), (0xff, 0xff, 0xff, 0xff))
    font = ImageFont.truetype("comic/COMICBD.TTF", 14)
    titlefont = ImageFont.truetype("comic/COMICBD.TTF", 20)

    # title drawing
    # see below for useful comments this is basically one iteration of the loop below
    if title:
        pim = Image.new("RGBA", (panelwidth, panelheight), (0xff, 0xff, 0xff, 0xff))
        pim.paste(bg, (0, 0))
        draw = ImageDraw.Draw(pim)
        st1w = 0; st1h = 0; st2w = 0; st2h = 0
        (st1, (st1w, st1h)) = wrap(title, titlefont, draw, 2*panelwidth/3.0)
        rendertitle(st1, titlefont, draw, (10, 10))

        draw.line([(0, 0), (0, panelheight-1), (panelwidth-1, panelheight-1), (panelwidth-1, 0), (0, 0)], (0, 0, 0, 0xff))
        del draw
        im.paste(pim, (0, 0))

    # panel drawing
    for i in xrange(len(panels)):
        pim = Image.new("RGBA", (panelwidth, panelheight), (0xff, 0xff, 0xff, 0xff))
        pim.paste(bg, (0, 0))
        draw = ImageDraw.Draw(pim)

        # text widths for character 1 and 2
        st1w = 0; st1h = 0; st2w = 0; st2h = 0
        # st = split (wrapped) text
        (st1, (st1w, st1h)) = wrap(panels[i][0][1], font, draw, 2*panelwidth/3.0)
        rendertext(st1, font, draw, (10, 10))
        if len(panels[i]) == 2:
            # draw the second character's text, if there is one
            (st2, (st2w, st2h)) = wrap(panels[i][1][1], font, draw, 2*panelwidth/3.0)
            rendertext(st2, font, draw, (panelwidth-10-st2w, st1h + 10))

        texth = st1h + 10
        if st2h > 0:
            texth += st2h + 10 + 5

        # figure out where to put the characters so they won't overlap text
        maxch = panelheight - texth

        # draw the first character.random.choice here for multi image support, again
        im1 = fitimg(random.choice(charmap[panels[i][0][0]]), (2*panelwidth/5.0-10, maxch))
        try:
            # not sure what this try would catch
            pim.paste(im1, (10, panelheight-im1.size[1]), im1)
        except Exception, e:
            print e, st2

        if len(panels[i]) == 2:
            # draw the second character
            im2 = fitimg(random.choice(charmap[panels[i][1][0]]), (2*panelwidth/5.0-10, maxch))
            im2 = im2.transpose(Image.FLIP_LEFT_RIGHT)
            pim.paste(im2, (panelwidth-im2.size[0]-10, panelheight-im2.size[1]), im2)

        # borders
        draw.line([(0, 0), (0, panelheight-1), (panelwidth-1, panelheight-1), (panelwidth-1, 0), (0, 0)], (0, 0, 0, 0xff))
        del draw
        if title:
            im.paste(pim, (0, panelheight * (i+1)))
        else:
            im.paste(pim, (0, panelheight * i))

    return im

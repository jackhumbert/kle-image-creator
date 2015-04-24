# encoding=utf8
from datetime import datetime
from flask import abort, Flask, jsonify, redirect, request, url_for, Response, session, make_response, send_file
# from flask.ext import restful
from functools import wraps
from random import randrange
import hashlib
import os, re
import random
import json
from flask_cors import cross_origin
import string
# import pytz
from datetime import datetime, timedelta
import time
import math
# from werkzeug import secure_filename



from PIL import Image, ImageFont, ImageDraw
import requests
from StringIO import StringIO
import copy
import webcolors
from HTMLParser import HTMLParser

app = Flask(__name__)
app.config.update(dict(
    COMPRESS_DEBUG=True,
    DEBUG=True
))

port = int(os.environ.get('PORT', 5000))

########################################################################

class Key(object):
    x = 0.0
    y = 0.0
    x2 =0.0
    y2 = 0.0
    width = 1.0
    height = 1.0
    width2 = 1.0
    height2 = 1.0
    color = "#cccccc"
    text = "#000000"
    labels =[]
    align = 4
    fontheight = 3.0
    fontheight2 = 3.0
    rotation_angle = 0.0
    rotation_x = 0.0
    rotation_y = 0.0
    profile = ""
    nub = False
    ghost = False
    stepped = False

def deserialise(rows):
    # Initialize with defaults
    current = Key()
    meta = { "backcolor": "#eeeeee" }
    keys = []
    cluster = { "x": 0.0, "y": 0.0 }
    for row in rows:
        if isinstance(row, list):
            for key in row:
                if isinstance(key, basestring):
                    newKey = copy.copy(current);
                    newKey.width2 = current.width if newKey.width2 == 0.0 else current.width2
                    newKey.height2 = current.height if newKey.height2 == 0.0 else current.height2
                    newKey.labels = key.split('\n')
                    keys.append(newKey)

                    # Set up for the next key
                    current.x += current.width
                    current.width = current.height = 1.0
                    current.x2 = current.y2 = current.width2 = current.height2 = 0.0
                    current.nub = current.stepped = False
                else:
                    if 'r' in key:
                        current.rotation_angle = key['r']
                    if 'rx' in key:
                        current.rotation_x = cluster['x'] = key['rx']
                    if 'ry' in key:
                        current.rotation_y = cluster['y'] = key['ry']
                    if 'a' in key:
                        current.align = key['a']
                    if 'f' in key:
                        current.fontheight = current.fontheight2 = float(key['f'])
                    if 'f2' in key:
                        current.fontheight2 = (key['f2'])
                    if hasattr(key, 'p'):
                        current.profile = key.p
                    if 'c' in key:
                        current.color = key['c'].replace(";", "")
                    if 't' in key:
                        current.text = key['t'].replace(";", "")
                    if 'x' in key:
                        current.x += float(key['x'])
                    if 'y' in key:
                        current.y += float(key['y'])
                    if 'w' in key:
                        current.width = float(key['w'])
                    if 'h' in key:
                        current.height = float(key['h'])
                    if 'x2' in key:
                        current.x2 = float(key['x2'])
                    if 'y2' in key:
                        current.y2 = float(key['y2'])
                    if 'w2' in key:
                        current.width2 = float(key['w2'])
                    if 'h2' in key:
                        current.height2 = float(key['h2'])
                    if hasattr(key, 'n'):
                        current.nub = key.n
                    if hasattr(key, 'l'):
                        current.stepped = key.l
                    if hasattr(key, 'g'):
                        current.ghost = key.g
            # End of the row
            current.y += 1.0;
        elif 'backcolor' in row:
            meta['backcolor'] = row['backcolor'].replace(";", "")
        current.x = current.rotation_x
    return { "meta":meta, "keys":keys }

def render_keys(kb):
    keys = kb['keys']
    meta = kb['meta']
    max_x = 0
    max_y = 0
    for key in keys:
        max_x = max(key.x*56+key.width*56, max_x)
        max_y = max(key.y*56+key.height*56, max_y)
    spacing = 10
    img = Image.new("RGB", (int(max_x - 3 + 2 * spacing), int(max_y - 3 + 2 * spacing)), meta['backcolor'])
    draw = ImageDraw.Draw(img)
    font_scale = 4
    font_layer = Image.new("RGBA", (img.size[0]*font_scale, img.size[1]*font_scale))
    draw_font = ImageDraw.Draw(font_layer)
    for key in keys:
        x = key.x*56 - 1.5 + spacing
        y = key.y*56 - 1.5 + spacing
        w = key.width*56 - 3 
        h = key.height*56 - 3
        light_color = webcolors.rgb_to_hex([color * 1.2 for color in webcolors.hex_to_rgb(key.color)])
        lightdark_color = webcolors.rgb_to_hex([color + 25 for color in webcolors.hex_to_rgb(key.color)])
        dark_color = webcolors.rgb_to_hex([color - 25 for color in webcolors.hex_to_rgb(key.color)])
        draw.rectangle([(x, y), (x+w, y+h)], fill=key.color, outline=dark_color)
        draw.rectangle([(x + 5, y + 5), (x+w-6, y+h-6)], fill=light_color, outline=dark_color)


        font = ImageFont.truetype("fonts/Roboto-Light.ttf", int((8+key.fontheight*1.5)*font_scale))
        small_font = ImageFont.truetype("fonts/Roboto-Light.ttf", 8*font_scale)

        key.centerx = key.align&1;
        key.centery = key.align&2;
        key.centerf = key.align&4;
        for label in key.labels:
            text = HTMLParser().unescape(re.sub(r'<.+>', '', label))
            text_size = draw_font.textsize(text, font)
            small_text_size = draw_font.textsize(text, small_font)
            text_x = (x + 1.5 + 4)*font_scale
            text_y = (y + 1.5 + 4)*font_scale
            # top left
            if key.labels.index(label) == 0:
                if key.centerx:
                    text_x = text_x + (56*key.width-15)/2*font_scale - text_size[0]/2
                else:
                    text_x += 1*font_scale
                if key.centery:
                    text_y = text_y + (56*key.height/2 - 10)*font_scale - text_size[1]/2
            # bottom left
            if key.labels.index(label) == 1:
                if key.centery:
                    continue
                text_y = text_y + (56*key.height - 3 - 12 - 3)*font_scale- text_size[1]
                if key.centerx:
                    text_x = text_x + (56*key.width-17)/2*font_scale - text_size[0]/2
                else:
                    text_x += 1*font_scale
            # top right
            if key.labels.index(label) == 2:
                if key.centerx:
                    continue
            # bottom right
            if key.labels.index(label) == 3:
                if key.centery:
                    continue
                if key.centerx:
                    continue
                text_y = text_y + (56*key.height - 3 - 12 - 3)*font_scale - text_size[1]


            # side left
            if key.labels.index(label) == 4:
                if key.centerf:
                    text_x = text_x + (56*key.width-15)/2*font_scale - small_text_size[0]/2
                text_y = text_y + (56*key.height - 16)*font_scale
                draw_font.text((text_x, text_y), text, key.text, font=small_font)
                continue
            # side right
            if key.labels.index(label) == 5:
                if key.centerf:
                    continue
                text_y = text_y + (56*key.height - 16)*font_scale
                text_x = text_x + (56*key.width - 15)*font_scale - small_text_size[0]
                draw_font.text((text_x, text_y), text, key.text, font=small_font)
                continue

            # middle left
            if key.labels.index(label) == 6:
                if key.centery:
                    continue
                if key.centerx:
                    text_x = text_x + (56*key.width-15)/2*font_scale - text_size[0]/2
                text_y = text_y + (56*key.height/2 - 4)*font_scale - text_size[1]
            # middle right
            if key.labels.index(label) == 7:
                if key.centery:
                    continue
                if key.centerx:
                    continue
                text_y = text_y + (56*key.height/2 - 4)*font_scale - text_size[1]
                text_x = text_x + (56*key.width-15)*font_scale - text_size[0]

            draw_font.text((text_x, text_y), text, key.text, font=font)


    font_layer.thumbnail(img.size, Image.ANTIALIAS)
    img.paste(font_layer, (0, 0), font_layer)
    return img

def serve_pil_image(pil_img):
    img_io = StringIO()
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/')
def index():
    return '''
HI
''', 200

@app.route('/<id>', methods = ['GET'])
@app.route('/<id>.png', methods = ['GET'])
def get_image(id):
    out = ""
    rows = requests.get('http://www.keyboard-layout-editor.com/layouts/%s' % id).json()
    app.logger.info(rows)
    kb = deserialise(rows)
    img = render_keys(kb)
    return serve_pil_image(img)

########################################################################

# http://coalkids.github.io/flask-cors.html

@app.before_request
def option_autoreply():
    """ Always reply 200 on OPTIONS request """

    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()

        headers = None
        if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
            headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']

        h = resp.headers

        # Allow the origin which made the XHR
        h['Access-Control-Allow-Origin'] = request.headers['Origin']
        # Allow the actual method
        h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']
        # Allow for 10 seconds
        h['Access-Control-Max-Age'] = "10"

        # We also keep current headers
        if headers is not None:
            h['Access-Control-Allow-Headers'] = headers

        return resp


@app.after_request
def set_allow_origin(resp):
    """ Set origin for GET, POST, PUT, DELETE requests """

    h = resp.headers

    # Allow crossdomain for other HTTP Verbs
    if request.method != 'OPTIONS' and 'Origin' in request.headers:
        h['Access-Control-Allow-Origin'] = request.headers['Origin']


    return resp

########################################################################

# @app.errorhandler(401)
# def unauthorized_access(e):
#     return "{'message': 'Invalid email/password', 'errorMessage': 'Invalid email/password'}", 401

# @app.errorhandler(400)
# def nope(e):
#     return "{'message': 'Incorrectly formed request', 'error': 400}", 400

########################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)

########################################################################

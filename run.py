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
from shortid import ShortId
import copy

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
    fontheight = 3
    fontheight2 = 3 
    rotation_angle = 0
    rotation_x = 0
    rotation_y = 0
    profile = ""
    nub = False
    ghost = False
    stepped = False

def deserialise(rows):
    # Initialize with defaults
    current = Key()
    meta = { "backcolor": "#eeeeee" }
    keys = []
    cluster = { "x": 0, "y": 0 }
    for row in rows:
        if isinstance(row, list):
            for key in row:
                if isinstance(key, basestring):
                    newKey = copy.copy(current);
                    newKey.width2 = current.width if newKey.width2 == 0 else current.width2
                    newKey.height2 = current.height if newKey.height2 == 0 else current.height2
                    newKey.labels = key.split('\n')
                    keys.append(newKey)

                    # Set up for the next key
                    current.x += current.width
                    current.width = current.height = 1
                    current.x2 = current.y2 = current.width2 = current.height2 = 0
                    current.nub = current.stepped = False
                else:
                    app.logger.info(key)
                    if hasattr(key, 'r'):
                        current.rotation_angle = key.r
                    if hasattr(key, 'rx'):
                        current.rotation_x = cluster.x = key.rx
                    if hasattr(key, 'ry'):
                        current.rotation_y = cluster.y = key.ry
                    if hasattr(key, 'a'):
                        current.align = key.a
                    if hasattr(key, 'f'):
                        current.fontheight = current.fontheight2 = key.f
                    if hasattr(key, 'f2'):
                        current.fontheight2 = key.f2
                    if hasattr(key, 'p'):
                        current.profile = key.p
                    if hasattr(key, 'c'):
                        current.color = key.c
                    if hasattr(key, 't'):
                        current.text = key.t
                    if 'x' in key:
                        current.x += float(key['x'])
                    if hasattr(key, 'y'):
                        current.y += float(key.y)
                    if 'w' in key:
                        current.width = float(key['w'])
                    if 'h' in key:
                        current.height = float(key['h'])
                    if hasattr(key, 'x2'):
                        current.x2 = key.x2
                    if hasattr(key, 'y2'):
                        current.y2 = key.y2
                    if hasattr(key, 'w2'):
                        current.width2 = key.w2
                    if hasattr(key, 'h2'):
                        current.height2 = key.h2
                    if hasattr(key, 'n'):
                        current.nub = key.n
                    if hasattr(key, 'l'):
                        current.stepped = key.l
                    if hasattr(key, 'g'):
                        current.ghost = key.g

            # End of the row
            current.y += 1;
        current.x = current.rotation_x
    return { "meta":meta, "keys":keys }

def render_keys(kb):
    keys = kb['keys']
    meta = kb['meta']
    last = keys[len(keys)-1]
    spacing = 10
    img = Image.new("RGB", (int(last.x*56+last.width*56 - 3 + 2 * spacing), int(last.y*56+last.height*56 - 3 + 2 * spacing)), meta['backcolor'])
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("fonts/HelveticaNeueLight.ttf", 17)
    for key in keys:
        x = key.x*56 - 1.5 + spacing
        y = key.y*56 - 1.5 + spacing
        w = key.width*56 - 3 
        h = key.height*56 - 3
        draw.rectangle([(x, y), (x+w, y+h)], fill="white", outline="#cccccc")
        draw.text((x + 1.5, y + 1.5), key.labels[0], (0,0,0), font=font)
        # # Some predefined sizes for our caps
        # sizes = { "cap": 54, "padding": 2, "margin": 6, "spacing": 1 }
        # def capsize(size):
        #     return (size*sizes['cap']) - (2*sizes['spacing'])
        # sizes.capsize = capsize

        # # Lighten a color by the specified amount
        # function lightenColor(color,mod) { 
        #     var c = $color.sRGB8(color.r,color.g,color.b).Lab();
        #     c.l = Math.min(100,c.l*mod);
        #     return c.sRGB8();
        # }

        # $renderKey.getKeyRotationStyles = function(key) {
        #     if(key.rotation_angle == 0) {
        #         return "";
        #     }
        #     var angle = key.rotation_angle.toString() + "deg";
        #     var origin = (sizes.capsize(key.rotation_x) + sizes.margin).toString() + "px " + (sizes.capsize(key.rotation_y) + sizes.margin).toString() + "px";
        #     return "transform: rotate("+angle+"); -ms-transform: rotate("+angle+"); -webkit-transform: rotate("+angle+"); " + 
        #            "transform-origin: "+origin+"; -ms-transform-origin: "+origin+"; -webkit-transform-origin: "+origin+";";     
        # };
        
        # # Given a key, generate the HTML needed to render it   
        # noRenderText = [0,2,1,3,0,4,2,3];
        # $renderKey.html = function(key, $sanitize) {
        #     var html = "";
        #     var capwidth = sizes.capsize(key.width), capwidth2 = sizes.capsize(key.width2);
        #     var capheight = sizes.capsize(key.height), capheight2 = sizes.capsize(key.height2);
        #     var capx = sizes.capsize(key.x) + sizes.margin, capx2 = sizes.capsize(key.x+key.x2)+sizes.margin;
        #     var capy = sizes.capsize(key.y) + sizes.margin, capy2 = sizes.capsize(key.y+key.y2)+sizes.margin;
        #     var jShaped = (capwidth2 !== capwidth) || (capheight2 !== capheight) || (capx2 !== capx) || (capy2 !== capy);
        #     var darkColor = key.color;
        #     var lightColor = lightenColor($color.hex(key.color), 1.2).hex();
        #     var innerPadding = (2*sizes.margin) + (2*sizes.padding);
        #     var borderStyle = "keyborder", bgStyle = "keybg";

        #     key.centerx = key.align&1 ? true : false;
        #     key.centery = key.align&2 ? true : false;
        #     key.centerf = key.align&4 ? true : false;

        #     if(key.ghost) {
        #         borderStyle += " ghosted";
        #         bgStyle += " ghosted";
        #     } 
        #     // The border
        #     html += "<div style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4};' class='{5}'></div>\n"
        #                 .format( capwidth,    capheight,    capx,       capy,      darkColor,             borderStyle );
        #     if(jShaped) {
        #         html += "<div style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4};' class='{5}'></div>\n"
        #                     .format( capwidth2,   capheight2,   capx2,      capy2,     darkColor,             borderStyle );
        #     }
        #     // The key edges
        #     html += "<div style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4};' class='{5}'></div>\n"
        #                 .format( capwidth,    capheight,    capx+1,     capy+1,    darkColor,             bgStyle );
        #     if(jShaped) {
        #         html += "<div style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4};' class='{5}'></div>\n"
        #                     .format( capwidth2,   capheight2,   capx2+1,    capy2+1,   darkColor,             bgStyle );
        #     }

        #     if(!key.ghost) {
        #         # The top of the cap
        #         html += "<div class='keyborder inner' style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4}; padding:{5}px;'></div>\n"
        #                 .format( capwidth-innerPadding, capheight-innerPadding, capx+sizes.margin, capy+(sizes.margin/2), lightColor, sizes.padding );
        #         if(jShaped && !key.stepped) {
        #             html += "<div class='keyborder inner' style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4}; padding:{5}px;'></div>\n"
        #                     .format( capwidth2-innerPadding, capheight2-innerPadding, capx2+sizes.margin, capy2+(sizes.margin/2), lightColor, sizes.padding );
        #         }

        #         var maxWidth = capwidth-(2*sizes.margin);
        #         var maxHeight = capheight-(2*sizes.margin);
        #         if(jShaped && !key.stepped) {
        #             maxWidth = Math.max(capwidth,capwidth2)-(2*sizes.margin);
        #             maxHeight = Math.max(capheight,capheight2)-(2*sizes.margin);
        #             html += "<div class='keyfg' style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4}; padding:{5}px; background-size:{6}px {7}px; background-position:{8}px {9}px;'>\n"
        #                     .format( capwidth2-innerPadding, capheight2-innerPadding, capx2+sizes.margin+1, capy2+(sizes.margin/2)+1, lightColor, sizes.padding, maxWidth, maxHeight, Math.min(capx,capx2)-capx2, Math.min(capy,capy2)-capy2 );
        #         }
        #         html += "</div><div class='keyfg' style='width:{0}px; height:{1}px; left:{2}px; top:{3}px; background-color:{4}; padding:{5}px; background-size:{6}px {7}px; background-position:{8}px {9}px;'>\n"
        #                 .format( capwidth-innerPadding, capheight-innerPadding, capx+sizes.margin+1, capy+(sizes.margin/2)+1, lightColor, sizes.padding, maxWidth, maxHeight, Math.min(capx,capx2)-capx, Math.min(capy,capy2)-capy );

        #         # The key labels           
        #         var textColor = lightenColor($color.hex(key.text), 1.2).hex();
        #         html += "<div class='keylabels' style='width:{0}px; height:{1}px;'>".format(capwidth-innerPadding, capheight-innerPadding);
        #         key.labels.forEach(function(label,i) {
        #             if(label && label !== "" && !(key.align&noRenderText[i])) {
        #                 var sanitizedLabel = $sanitize(label.replace(/<([^a-zA-Z\/]|$)/,"&lt;$1"));
        #                 html += "<div class='keylabel keylabel{2} centerx-{5} centery-{6} centerf-{7} textsize{8}' style='color:{1};width:{3}px;height:{4}px;'><div style='width:{3}px;max-width:{3}px;height:{4}px;'>{0}</div></div>\n"
        #                             .format(sanitizedLabel, i===4||i===5 ? key.text : textColor, i+1, capwidth-innerPadding, capheight-innerPadding, 
        #                                     key.centerx, key.centery, key.centerf, i>0 ? key.fontheight2 : key.fontheight);
        #             }
        #         });
        #         html += "</div></div>";
        #     }

        #     key.rect = { x:capx, y:capy, w:capwidth, h:capheight, x2:capx+capwidth, y2:capy+capheight };
        #     key.rect2 = { x:capx2, y:capy2, w:capwidth2, h:capheight2, x2:capx2+capwidth2, y2:capy2+capheight2 };
        #     key.rectMax = { x:Math.min(capx,capx2), y:Math.min(capy,capy2), x2:Math.max(capx+capwidth,capx2+capwidth2), y2:Math.max(capy+capheight,capy2+capheight2) };
        #     key.rectMax.w = key.rectMax.x2 - key.rectMax.x;
        #     key.rectMax.h = key.rectMax.y2 - key.rectMax.y;

        #     # Rotation matrix about the origin
        #     var origin_x = sizes.capsize(key.rotation_x)+sizes.margin;
        #     var origin_y = sizes.capsize(key.rotation_y)+sizes.margin;
        #     key.mat = Math.transMatrix(origin_x, origin_y).mult(Math.rotMatrix(key.rotation_angle)).mult(Math.transMatrix(-origin_x, -origin_y));

        #     # Construct the *eight* corner points, transform them, and determine the transformed bbox.
        #     key.bbox = { x:9999999, y:9999999, x2:-9999999, y2:-9999999 };
        #     var corners = [ 
        #         {x:key.rect.x, y:key.rect.y}, 
        #         {x:key.rect.x, y:key.rect.y2}, 
        #         {x:key.rect.x2, y:key.rect.y}, 
        #         {x:key.rect.x2, y:key.rect.y2},
        #         {x:key.rect2.x, y:key.rect2.y}, 
        #         {x:key.rect2.x, y:key.rect2.y2}, 
        #         {x:key.rect2.x2, y:key.rect2.y}, 
        #         {x:key.rect2.x2, y:key.rect2.y2},
        #     ];
        #     for(var i = 0; i < corners.length; ++i) {
        #         corners[i] = key.mat.transformPt(corners[i]); 
        #         key.bbox.x = Math.min(key.bbox.x, corners[i].x);
        #         key.bbox.y = Math.min(key.bbox.y, corners[i].y);
        #         key.bbox.x2 = Math.max(key.bbox.x2, corners[i].x);
        #         key.bbox.y2 = Math.max(key.bbox.y2, corners[i].y);
        #     }
        #     key.bbox.w = key.bbox.x2 - key.bbox.x;
        #     key.bbox.h = key.bbox.y2 - key.bbox.y;

        #     # Keep an inverse transformation matrix so that we can transform mouse
        #     # coordinates into key-space.
        #     key.mat = Math.transMatrix(origin_x, origin_y).mult(Math.rotMatrix(-key.rotation_angle)).mult(Math.transMatrix(-origin_x, -origin_y));

        #     # Determine the location of the rotation crosshairs for the key
        #     key.crosshairs = "none";
        #     if(key.rotation_x || key.rotation_y || key.rotation_angle) {
        #         key.crosshairs_x = sizes.capsize(key.rotation_x) + sizes.margin;
        #         key.crosshairs_y = sizes.capsize(key.rotation_y) + sizes.margin;
        #         key.crosshairs = "block";
        #     }
    return img

def serve_pil_image(pil_img):
    img_io = StringIO()
    pil_img.save(img_io, 'JPEG', quality=80)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

@app.route('/')
def index():
    return '''
HI
''', 200

@app.route('/<id>', methods = ['GET'])
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

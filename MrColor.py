import discord, os, webcolors, requests
from discord.ext import commands
from colors import rgb, hex, hsv
from random import randint
from textwrap import wrap
from colorthief import ColorThief
from io import BytesIO
from colorharmonies import Color, complementaryColor, triadicColor, tetradicColor, analogousColor, monochromaticColor
token = os.environ['token']
prefix = "c?"
bot = commands.Bot(command_prefix=prefix)
bot.remove_command("help")

def get_channel(server):
    for channel in server.channels:
        if (channel.permissions_for(server.me).send_messages) and (channel.type == discord.ChannelType.text):
            return channel

def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name

def rgb_to_cmyk(r,g,b):
    if (r,g,b) == (0,0,0):
        return 0, 0, 0, 1
    r = r/255
    g = g/255
    b = b/255

    k = 1-max(r,g,b)
    c = (1-r-k) / (1-k)
    m = (1-g-k) / (1-k)
    y = (1-b-k) / (1-k)
    return c, m, y, k

def cmyk_to_rgb(c,m,y,k):
    rgb_scale = 255
    r = rgb_scale*(1.0-c)*(1.0-k)
    g = rgb_scale*(1.0-m)*(1.0-k)
    b = rgb_scale*(1.0-y)*(1.0-k)
    return r, g, b

def yiq_to_rgb(y,i,q):
    r = y + 0.9468822170900693*i + 0.6235565819861433*q
    g = y - 0.27478764629897834*i - 0.6356910791873801*q
    b = y - 1.1085450346420322*i + 1.7090069284064666*q
    return r, g, b

def rgb_to_yiq(r,g,b):
    y = (0.299*r + 0.587*g + 0.114*b) / 255
    i = (0.596*r - 0.275*g - 0.321*b) / 255
    q = (0.212*r - 0.523*g + 0.311*b) / 255
    return y, i, q

def compute_average_image_color(img):
    width, height = img.size

    r_total = 0
    g_total = 0
    b_total = 0

    count = 0
    for x in range(0, width):
        for y in range(0, height):
            r, g, b = img.getpixel((x,y))
            r_total += r
            g_total += g
            b_total += b
            count += 1

    return (r_total/count, g_total/count, b_total/count)

def shade(shade_factor, r, g ,b ):
    newR = r - shade_factor
    newG = g - shade_factor
    newB = b - shade_factor

    if newR < 0:
        newR = 0.0
    if newG < 0:
        newG = 0.0
    if newB < 0:
        newB = 0.0

    return newR, newG, newB

def tint(tint_factor, r, g ,b ):
    newR = r + tint_factor
    newG = g + tint_factor
    newB = b + tint_factor

    if newR > 255:
        newR = 255
    if newG > 255:
        newG = 255
    if newB > 255:
        newB = 255

    return newR, newG, newB

async def message(channel, r, g, b, title):
    if not (r,g,b) == (-1,-1,-1): 
        x, z = get_colour_name((r, g, b))
        c, m, y, k = rgb_to_cmyk(r,g,b)
        h, s, v = rgb(r, g, b).hsv
        y, i, q = rgb_to_yiq(r,g,b)

        text = """
        RGB - ``{0}``
        HEX - ``#{1}``
        HSV - ``{2}`` 
        YIQ - ``{3}``
        CMYK - ``{4}``

        Closest colour - ``{5}``
        """.format(str(r) + ', ' + str(g) + ', '+ str(b),
        str(rgb(r, g, b).hex),
        str(round(float(h * 360), 1)) + '°, ' + str(round(float(s * 100), 1)) + '%, ' + str(round(float(v * 100), 1)) + '%',
        str(float(round(y,3))) + ', ' + str(float(round(i,3))) + ', ' + str(float(round(q,3))),
        str(float(round(c, 1))) + '%, ' + str(float(round(m, 1))) + '%, ' + str(float(round(y, 1))) + '%, ' + str(float(round(k, 1))) + '% ',
        z)  
        color = str(rgb(r, g, b).hex)
        await bot.send_message(channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))

async def to_rgb(channel, color_type, color):
    color_type = color_type.lower()
    if color_type == 'rgb':
        try:
            color = color.replace(' ', '').replace('(', '').replace(')', '').split(',')
            r = int(round(float(color[0])))
            g = int(round(float(color[1])))
            b = int(round(float(color[2])))
        except:
            await bot.send_message(channel, "Wrong **rgb** format!")
    elif color_type == "hex":
        try:
            color = color.replace('#','')
            r, g, b = hex(color).rgb
        except:
            await bot.send_message(channel, "Wrong **hex** format!")
    elif color_type == 'hsv':
        try:
            color = color.replace(' ', '').replace('%', '').replace('°', '').split(',')
            h = float(color[0]) / 360
            s = float(color[1]) / 100
            v = float(color[2]) / 100
            r, g, b = hsv(h, s, v).rgb
            r, g, b = int(round(r)), int(round(g)), int(round(b))
        except:
            await bot.send_message(channel, "Wrong **hsv** format!")
    elif color_type == 'yiq':
        try:
            color = color.replace(' ', '').split(',')
            y = float(color[0]) * 255
            i = float(color[1]) * 255
            q = float(color[2]) * 255
            r, g, b = yiq_to_rgb(y,i,q)
            r, g, b = int(round(r)), int(round(g)), int(round(b))
        except:
            await bot.send_message(channel, "Wrong **yiq** format!")
    elif color_type == 'cmyk':
        try:
            color = color.replace(' ', '').replace('%', '').split(',')
            c = float(color[0]) / 100
            m = float(color[1]) / 100
            y = float(color[2]) / 100
            k = float(color[3]) / 100
            r, g, b = cmyk_to_rgb(c,m,y,k)
            r, g, b = int(round(r)) , int(round(g)), int(round(b))
        except:
            await bot.send_message(channel, "Wrong **cmyk** format!")
    elif color_type == "name":
        try:
            r, g, b = webcolors.name_to_rgb(color)
        except:
            await bot.send_message(channel, "Wrong **color** name!")
    try:
        return r, g, b
    except:
        return -1, -1, -1
    
@bot.event
async def on_server_join(server):
    channel = get_channel(server)
    
    title = "**TheColor**"
    text = """**Thank you for adding me to your server!**\n\npreifx - ``c?``\nbot version ``1.0`` \nfor help - ``c?help``\n\n This bot will help you with colors, their format, shades, tints and with many other!\n ~~*google translated*~~"""
    await bot.send_message(channel, embed = discord.Embed(title = title, description = text)) 

@bot.event
async def on_ready():
    await bot.change_presence(game = discord.Game(name='c?help'))
    print("Бот работает!")

@bot.command(pass_context=True, name="randomcolor")
async def rand_color(ctx, *, content:int = 1):
    """Get random color/s"""
    def get_rand_color():
        r = randint(0,255) 
        b = randint(0,255)
        g = randint(0,255)
        return r, g, b
    for num in range(content):

        r, g, b = get_rand_color()
        x, z = get_colour_name((r, g, b))
        c, m, yy, k = rgb_to_cmyk(r,g,b)
        h, s, v = rgb(r, g, b).hsv
        y, i, q = rgb_to_yiq(r,g,b)

        title = "{0} Color!".format(num + 1)
        text = """
        RGB - ``{0}``
        HEX - ``#{1}``
        HSV - ``{2}`` 
        YIQ - ``{3}``
        CMYK - ``{4}``

        Closest colour - ``{5}``
        """.format(str(r) + ', ' + str(g) + ', '+ str(b),
        str(rgb(r, g, b).hex),
        str(round(float(h * 360), 1)) + '°, ' + str(round(float(s * 100), 1)) + '%, ' + str(round(float(v * 100), 1)) + '%',
        str(float(round(y,3))) + ', ' + str(float(round(i,3))) + ', ' + str(float(round(q,3))),
        str(float(round(c * 100))) + '%, ' + str(float(round(m * 100))) + '%, ' + str(float(round(yy * 100))) + '%, ' + str(float(round(k * 100))) + '% ',
        z) 
        color = str(rgb(r, g, b).hex)
        await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))   

@bot.command(pass_context=True, name="colorinfo")
async def color_info(ctx, color_type:str, *, color):
    """Get info about color. \n**Examples:** \ncolorinfo hex ff0000 or #ff0000\ncolorinfo name Black\ncolorinfo rgb 255, 255, 255 or (254.70,254.70,254.70)\ncolorinfo hsv 360, 100, 100 or 360,100,100\nList of colors: RGB, HEX, HSV, YIQ, CMYK, Name"""
    r,g,b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return 
    x, z = get_colour_name((r, g, b))
    c, m, yy, k = rgb_to_cmyk(r,g,b)
    h, s, v = rgb(r, g, b).hsv
    y, i, q = rgb_to_yiq(r,g,b)

    title = "Color info"
    text = """
    RGB - ``{0}``
    HEX - ``#{1}``
    HSV - ``{2}`` 
    YIQ - ``{3}``
    CMYK - ``{4}``

    Closest colour - ``{5}``
    """.format(str(r) + ', ' + str(g) + ', '+ str(b),
    str(rgb(r, g, b).hex),
    str(round(float(h * 360), 1)) + '°, ' + str(round(float(s * 100), 1)) + '%, ' + str(round(float(v * 100), 1)) + '%',
    str(float(round(y,3))) + ', ' + str(float(round(i,3))) + ', ' + str(float(round(q,3))),
    str(float(round(c * 100))) + '%, ' + str(float(round(m * 100))) + '%, ' + str(float(round(yy * 100))) + '%, ' + str(float(round(k * 100))) + '% ',
    z)  
    color = str(rgb(r, g, b).hex)
    await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))

@bot.command(pass_context=True, name="imagepalette")
async def image_palette(ctx, url, *, num:int = 5):
    """Get image color palette. \n **Examples:** \n imagepalette https://...img.png 2 """
    response = requests.get(url)
    color_thief = ColorThief((BytesIO(response.content)))
    colorn = color_thief.get_palette(color_count= num)
    for ii in range(num):
        try:
            r,g,b = await to_rgb(ctx.message.channel, 'rgb', str(colorn[ii]))
            if (r, g, b) == (-1, -1, -1):
                return
        except:
            print('endpalitra')
        if not (r,g,b) == (-1,-1,-1): 
            x, z = get_colour_name((r, g, b))
            c, m, y, k = rgb_to_cmyk(r,g,b)
            h, s, v = rgb(r, g, b).hsv
            y, i, q = rgb_to_yiq(r,g,b)

            title = "Palette color info {0}".format(ii + 1)
            text = """
            RGB - ``{0}``
            HEX - ``#{1}``
            HSV - ``{2}`` 
            YIQ - ``{3}``
            CMYK - ``{4}``

            Closest colour - ``{5}``
            """.format(str(r) + ', ' + str(g) + ', '+ str(b),
            str(rgb(r, g, b).hex),
            str(round(float(h * 360), 1)) + '°, ' + str(round(float(s * 100), 1)) + '%, ' + str(round(float(v * 100), 1)) + '%',
            str(float(round(y,3))) + ', ' + str(float(round(i,3))) + ', ' + str(float(round(q,3))),
            str(float(round(c, 1))) + '%, ' + str(float(round(m, 1))) + '%, ' + str(float(round(y, 1))) + '%, ' + str(float(round(k, 1))) + '% ',
            z)  
            color = str(rgb(r, g, b).hex)
            await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))

@bot.command(pass_context=True, name="colorshades")
async def color_shades(ctx, countshades:int, shades:int, color_type, *, color):
    """Shades of color \n **Examples:** \n colorshades 0 0 0 20, 20, 20 \n colorshades 5 20 hex #ffff00 \n if countshades, shades or color_type = 0, then this means that the var's will be set automatically. \n if countshades = 0 then countshades = 10 \n if shades = 0 then shades will be exposed by the formula. \(o-o)/ \n if type_color = 0 then type_color = rgb"""
    if countshades == 0:
        countshades = 10
    elif countshades > 30:
        await bot.send_message(ctx.message.channel, "Max shades count **30**!")
        return
    if shades == 0:
        shades = 'auto'
    if color_type == 0:
        color_type = 'rgb'
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    if r > g and r > b:
        most = r
    elif g > r and g > b:
        most = g
    elif b > r and b > g:
        most = b
    elif r == g or g == b:
        most = g
    elif r == b:
        most = r

    if shades == 'auto':
        shades = most / countshades
        if not int(str(shades).split('.')[1]) == 0:
            shades = int(str(shades).split('.')[0]) + 1
        
    for num in range(1, countshades + 1, 1):
        nr, ng, nb = shade(shades * num, r, g, b)
        nr, ng, nb = round(nr), round(ng), round(nb)

        color = str(rgb(r, g, b).hex)
        title = "Shade {0}".format(num)
        text = """
        RGB - {0}
        HEX - #{1}
        """.format(
            str(nr) + ', ' + str(ng) + ', '+ str(nb),
            str(rgb(nr, ng, nb).hex)
        )
        color = str(rgb(nr, ng, nb).hex)
        await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))
    
@bot.command(pass_context=True, name="colortints")
async def color_tints(ctx, counttints:int, tints:int, color_type, *, color):
    "Tints of color"
    if counttints == 0:
        counttints = 10
    elif counttints > 30:
        await bot.send_message(ctx.message.channel, "Max tints count **30**!")
        return
    if tints == 0:
        tints = 'auto'
    if color_type == 0:
        color_type = 'rgb'
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    if r < g and r < b:
        low = r
    elif g < r and g < b:
        low = g
    elif b < r and b < g:
        low = b
    elif r == g or g == b:
        low = g
    elif r == b:
        low = r
        
    if tints == 'auto':
        tints = (255 - low) / counttints
        if not int(str(tints).split('.')[1]) == 0:
            tints = int(str(tints).split('.')[0]) + 1
        
    for num in range(1, counttints + 1, 1):
        nr, ng, nb = tint(tints * num, r, g, b)
        nr, ng, nb = round(nr), round(ng), round(nb)

        color = str(rgb(r, g, b).hex)
        title = "Tint {0}".format(num)
        text = """
        RGB - {0}
        HEX - #{1}
        """.format(
            str(nr) + ', ' + str(ng) + ', '+ str(nb),
            str(rgb(nr, ng, nb).hex)
        )
        color = str(rgb(nr, ng, nb).hex)
        await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(color, 16))))

@bot.command(pass_context=True, name="link")
async def link(ctx, color_type, *, color):
    """Gives information about the color on the website www.color-hex.com \n Example: \n link cmyk 0.0%, 88.0%, 52.0%, 4.0%"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    color = str(rgb(r, g, b).hex)
    await bot.send_message(ctx.message.channel, embed = discord.Embed(title = "About color", description = "https://www.color-hex.com/color/{0}".format(color), color = discord.Color(int(color, 16)))) 
    
@bot.command(pass_context =True, name="compcolor")
async def comp_color(ctx, color_type, *, color):
    """Complementary color"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    color = Color([r, g, b],"","")
    color = complementaryColor(color)
    color = [[r,g,b]] + [color]
    for i in range(2):
        r = color[i][0]
        g = color[i][1]
        b = color[i][2]
        title = "Complementary color {0}".format(i + 1)
        await message(ctx.message.channel, r, g, b, title)

@bot.command(pass_context =True, name="triadiccolor")
async def triadic_color(ctx, color_type, *, color):
    """Triadic color"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    color = Color([r, g, b],"","")
    color = [[r,g,b]] + triadicColor(color)
    for i in range(3):
        r = color[i][0]
        g = color[i][1]
        b = color[i][2]
        title = "Triadic color {0}".format(i + 1)
        await message(ctx.message.channel, r, g, b, title)

@bot.command(pass_context =True, name="tetradiccolor")
async def tetriadic_color(ctx, color_type, *, color):
    """Tetradic color"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    color = Color([r, g, b],"","")
    color = [[r,g,b]] + tetradicColor(color)
    for i in range(4):
        r = color[i][0]
        g = color[i][1]
        b = color[i][2]
        title = "Tetradic color {0}".format(i + 1)
        await message(ctx.message.channel, r, g, b, title)

@bot.command(pass_context =True, name="analogcolor")
async def tetriadic_color(ctx, color_type, *, color):
    """Analogous color"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    color = Color([r, g, b],"","")
    color = [[r,g,b]] + analogousColor(color)
    for i in range(3):
        r = color[i][0]
        g = color[i][1]
        b = color[i][2]
        title = "Analogous color {0}".format(i + 1)
        await message(ctx.message.channel, r, g, b, title)

@bot.command(pass_context =True, name="monocolor")
async def mono_color(ctx, count:int, color_type, *, color):
    """Monochromatic color"""
    r, g, b = await to_rgb(ctx.message.channel, color_type, color)
    if (r, g, b) == (-1, -1, -1):
        return
    if count == 0:
        count = 10
    elif count > 19:
        count = 19
    color = Color([r, g, b],"","")
    color = monochromaticColor(color)
    for i in range(10):
        r = color[i][0]
        g = color[i][1]
        b = color[i][2]
        title = "Monochromatic color {0}".format(i + 1)
        text = """
        RGB - {0}
        HEX - #{1}
        """.format(
            str(r) + ', ' + str(g) + ', '+ str(b),
            str(rgb(r, g, b).hex)
        )
        colorn = str(rgb(r, g, b).hex)
        await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text, color = discord.Color(int(colorn, 16))))

@bot.command(pass_context = True, name="help")
async def help(ctx,*, command:str = None):
    if command == None:
        title = "All commands"
        text = """
        **{0}help** - Shows this message
        **{0}randomcolor** - Returns a random color
        **{0}colorinfo** - Returns color information
        **{0}imagepalette** - Returns the color palette of the image 
        **{0}colorshades** - Returns a shades of color
        **{0}colortints** - Returns a tints of color
        **{0}compcolor** - Returns complementary colors
        **{0}triadiccolor** - Returns triadic colors
        **{0}tetradiccolor** - Returns tetradic colors
        **{0}analogcolor** - Returns analogous colors
        **{0}monocolor** - Returns monochromatic colors
        **{0}link** - Returns information about the color on the website

        Type {0}help command for more info on a command.
        Example:
        {0}help colorinfo
        """
    else:
        title = command
        if command == "help":
            text = "{0}help <none/command> \n**Examples:** \n{0}help randomcolor"
        elif command == "randomcolor":
            text = "{0}randomcolor <none/num> \n**Examples:** \n{0}randomcolor 2" 
        elif command == "imagepalette":
            text = "{0}imagepalette <url> <none/num> \n**Examples:** \n{0}imagepalette www.website.com/img.png 10"
        elif command == "colorinfo":
            text = "{0}colorinfo <color type> <color> \n**Examples:** \ncolorinfo hex ff0000 or #ff0000\ncolorinfo name Black\ncolorinfo rgb 255, 255, 255 or (254.70,254.70,254.70)\ncolorinfo hsv 360, 100, 100 or 360,100,100\nList of colors: RGB, HEX, HSV, YIQ, CMYK, Name"""
        elif command == "colorshades":
            text = "{0}colorshades <count> <shade> <color type> <color> \n**Examples:** \n {0}colorshades 0 0 hex ffffff \n if <count> or <shade> = 0, then this means that <count> = 10 and <shade> = color / count \n {0}colorshades 5 30 rgb 20, 20, 20"
        elif command == "colortints":
            text = "{0}colortints <count> <tint> <color type> <color> \n**Examples:** \n {0}colortints 0 0 hex ffffff \n if <count> or <tints> = 0, then this means that <count> = 10 and <tints> = (rgb size - color in rgb) / count \n {0}colortints 5 30 rgb 20, 20, 20"
        elif command == "compcolor":
            text = "{0}compcolor <color type> <color> \n**Examples:** \n{0}compcolor hex ffffff"
        elif command == "triadiccolor":
            text = "{0}triadiccolor <color type> <color> \n**Examples:** \n{0}triadiccolor hex ffffff"
        elif command == "tetriadiccolor":
            text = "{0}tetriadiccolor <color type> <color> \n**Examples:** \n{0}tetriadiccolor hex ffffff"
        elif command == "analogcolor":
            text = "{0}analogcolor <color type> <color> \n**Examples:** \n{0}analogcolor hex ffffff"
        elif command == "monocolor":
            text = "{0}monocolor <count> <color type> <color> \n**Examples:** \n{0}monocolor 10 hex ffffff"
        elif command == "link":
            text = "{0}link <color type> <color> \n**Examples:** \n{0}link hex ffffff"
        else:
            text = "Wrong command"
    await bot.send_message(ctx.message.channel, embed = discord.Embed(title = title, description = text.format(prefix))) 
bot.run(token)


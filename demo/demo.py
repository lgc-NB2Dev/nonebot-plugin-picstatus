from PIL import Image, ImageDraw, ImageFont


def get_font(size: int):
    return ImageFont.truetype('SourceHanSansSC-Bold-2.otf', size=size)


def draw_header():
    circle_mask = Image.new('RGBA', (250, 250), '#ffffff00')
    ImageDraw.Draw(circle_mask).ellipse((0, 0, 250, 250), fill='black')

    header = Image.new('RGBA', (1200, 300), '#ffffff66')
    avatar: Image.Image = Image.open('photo_2020-12-08_22-46-51.jpg')
    avatar = avatar.convert('RGBA').resize((250, 250))
    header.paste(avatar, (25, 25), circle_mask)

    header_draw = ImageDraw.Draw(header)
    f30 = get_font(30)
    header_draw.text((300, 140), '饼干又在咕咕咕', 'black', get_font(80), 'ld')
    stat_t = ('在线 2:23:23 | 收 114 | 发 514\n'
              'NoneBot运行 2:23:23 | 系统运行 13天 14:52:00')
    header_draw.multiline_text((300, 160), stat_t, 'black', f30)
    header_draw.line((300, 150, 500, 150), '#aaaaaaaa', 3)

    return header


def draw_cpu_memory_usage():
    bg = Image.new('RGBA', (1200, 550), '#ffffff66')
    circle_bg = Image.new('RGBA', (300, 300), '#ffffff00')
    ImageDraw.Draw(circle_bg).arc((0, 0, 300, 300), 0, 360, '#aaaaaaaa', 30)

    bg.paste(circle_bg, (50, 50), circle_bg)
    bg.paste(circle_bg, (450, 50), circle_bg)
    bg.paste(circle_bg, (850, 50), circle_bg)

    bg_draw = ImageDraw.Draw(bg)
    bg_draw.text((200, 200), '25%', 'black', get_font(70), 'mm')
    bg_draw.text((600, 200), '70%', 'black', get_font(70), 'mm')
    bg_draw.text((1000, 200), '90%', 'black', get_font(70), 'mm')

    bg_draw.arc((50, 50, 350, 350), -90, (360 * 0.25) - 90, 'lightgreen', 30)
    bg_draw.arc((450, 50, 750, 350), -90, (360 * 0.70) - 90, 'orange', 30)
    bg_draw.arc((850, 50, 1150, 350), -90, (360 * 0.90) - 90, 'orangered', 30)

    bg_draw.text((200, 350), 'CPU', 'black', get_font(70), 'ma')
    bg_draw.text((600, 350), 'RAM', 'black', get_font(70), 'ma')
    bg_draw.text((1000, 350), 'VRAM', 'black', get_font(70), 'ma')

    bg_draw.text((200, 500), '2600MHz', 'gray', get_font(45), 'ms')
    bg_draw.text((600, 500), '2867M / 4096M', 'gray', get_font(45), 'ms')
    bg_draw.text((1000, 500), '7372M / 8192M', 'gray', get_font(45), 'ms')

    return bg


def main():
    w = 1300
    bg: Image.Image = Image.open('88303951_p0.png')
    bg = bg.convert('RGBA')
    bg_w, bg_h = bg.size
    scale = w / bg_w
    bg = bg.resize((w, int(bg_h * scale)))

    header = draw_header()
    bg.paste(header, (50, 50), header)

    cm = draw_cpu_memory_usage()
    bg.paste(cm, (50, 400), cm)

    bg.show()


if __name__ == '__main__':
    main()

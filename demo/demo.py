from PIL import Image, ImageDraw, ImageFont


def get_font(size: int):
    return ImageFont.truetype('SourceHanSansSC-Bold-2.otf', size=size)


def main():
    w = 1300
    bg: Image.Image = Image.open('88303951_p0.png')
    bg = bg.convert('RGBA')
    bg_w, bg_h = bg.size
    scale = w / bg_w
    bg = bg.resize((w, int(bg_h * scale)))

    circle_mask = Image.new('RGBA', (250, 250), '#ffffff00')
    ImageDraw.Draw(circle_mask).ellipse((0, 0, 250, 250), fill='black')

    header = Image.new('RGBA', (1200, 300), '#ffffff66')
    avatar: Image.Image = Image.open('photo_2020-12-08_22-46-51.jpg')
    avatar = avatar.convert('RGBA').resize((250, 250))
    header.paste(avatar, (25, 25), circle_mask)

    header_draw = ImageDraw.Draw(header)
    f30 = get_font(30)
    header_draw.text((300, 140), '饼干又在咕咕咕', 'black', get_font(80), 'lb')
    stat_t = ('在线 2:23:23 | 收 114 | 发 514\n'
              'NoneBot运行 2:23:23 | 系统运行 13天 14:52:00')
    header_draw.multiline_text((300, 160), stat_t, 'black', f30)
    header_draw.line((300, 150, 500, 150), '#aaaaaaaa', 3)

    bg.paste(header, (50, 50), header)

    bg.show()


if __name__ == '__main__':
    main()

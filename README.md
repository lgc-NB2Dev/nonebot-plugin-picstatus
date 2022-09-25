<!-- markdownlint-disable MD033 MD036 MD041 -->

<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="logo">
  </a>
  <br>
  <p>
    <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="logo">
  </p>
</div>

<div align="center">

# NoneBot-Plugin-PicStatus

_✨ 运行状态图片版 for NoneBot2 ✨_

<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/lgc2333/nonebot-plugin-picstatus.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-picstatus">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-picstatus.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="https://pypi.python.org/pypi/nonebot-plugin-picstatus">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-picstatus" alt="pypi download">
</a>
<a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/bfec6993-aa9e-42fb-9f3e-53a5d4739373">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/bfec6993-aa9e-42fb-9f3e-53a5d4739373.svg" alt="wakatime">
</a>

</div>

## 📖 介绍

不多说，直接看图！

### 效果图

![example](https://raw.githubusercontent.com/lgc2333/nonebot-plugin-picstatus/master/readme/example.png)

## 💿 安装

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-picstatus

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-picstatus

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-picstatus

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-picstatus

</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-picstatus

</details>

打开 nonebot2 项目的 `bot.py` 文件, 在其中写入

    nonebot.load_plugin('nonebot_plugin_picstatus')

</details>

<details>
<summary>从 github 安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 输入以下命令克隆此储存库

    git clone https://github.com/lgc2333/nonebot-plugin-picstatus.git

打开 nonebot2 项目的 `bot.py` 文件, 在其中写入

    nonebot.load_plugin('src.plugins.nonebot_plugin_picstatus')

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

|         配置项         |                   类型                    | 必填 |         默认值          |                           说明                           |
| :--------------------: | :---------------------------------------: | :--: | :---------------------: | :------------------------------------------------------: |
|      `PS_ONLY_SU`      |             布尔值（`bool`）              |  否  |         `False`         |              是否只能由`SuperUsers`触发指令              |
|      `PS_NEED_AT`      |             布尔值（`bool`）              |  否  |         `False`         |                   触发指令是否需要@Bot                   |
|   `PS_USE_ENV_NICK`    |             布尔值（`bool`）              |  否  |         `False`         |   使用`.env.*`中配置的`NICKNAME`作为图片上的 Bot 昵称    |
|   `PS_IGNORE_PARTS`    |          文本列表（`List[str]`）          |  否  |          `[]`           |  分区列表里忽略的盘符（挂载点）<br/>使用正则表达式匹配   |
| `PS_IGNORE_BAD_PARTS`  |             布尔值（`bool`）              |  否  |         `False`         |              忽略获取容量状态失败的磁盘分区              |
|  `PS_IGNORE_DISK_IOS`  |          文本列表（`List[str]`）          |  否  |          `[]`           |  磁盘 IO 统计列表中忽略的磁盘名<br/>使用正则表达式匹配   |
|    `PS_IGNORE_NETS`    |          文本列表（`List[str]`）          |  否  | `["^lo$", "^Loopback"]` |     网速列表中忽略的网络名称<br/>使用正则表达式匹配      |
| `PS_IGNORE_NO_IO_DISK` |             布尔值（`bool`）              |  否  |         `False`         |               是否忽略 IO 都为 0B/s 的磁盘               |
|   `PS_IGNORE_0B_NET`   |             布尔值（`bool`）              |  否  |         `False`         |              是否忽略上下行都为 0B/s 的网卡              |
|    `PS_MASK_COLOR`     | 4 整数元组（`Tuple[int, int, int, int]`） |  否  | `[255, 255, 255, 125]`  |                      背景图遮罩颜色                      |
|     `PS_BG_COLOR`      | 4 整数元组（`Tuple[int, int, int, int]`） |  否  | `[255, 255, 255, 150]`  |                    各状态矩形背景底色                    |
|    `PS_BLUR_RADIUS`    |               整数（`int`）               |  否  |           `4`           |                    背景图高斯模糊半径                    |
|       `PS_FONT`        |               文本（`str`）               |  否  |           无            |                      自定义字体路径                      |
|     `PS_CUSTOM_BG`     |          文本列表（`List[str]`）          |  否  |          `[]`           | 自定义背景图 URL 列表<br/>本地图请使用`file:///文件路径` |

## 🎉 使用

使用指令`运行状态`（或者`状态` / `zt` / `yxzt` / `status`）来触发插件功能  
可以在消息后面跟一张图片或者回复一张图片来自定义背景图，默认为随机背景图  
更多自定义项参见 [配置](#️-配置)

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

## 💡 鸣谢

### [故梦 API](https://api.gmit.vip)

- 随机背景图来源

## 💰 赞助

感谢大家的赞助！你们的赞助将是我继续创作的动力！

- [爱发电](https://afdian.net/@lgc2333)
- <details>
    <summary>赞助二维码（点击展开）</summary>

  ![讨饭](https://raw.githubusercontent.com/lgc2333/ShigureBotMenu/master/src/imgs/sponsor.png)

  </details>

## 📝 更新日志

### 0.2.4

配置项更新详见 [配置](#️-配置)

- 支持自定义默认背景图
- 一些配置项类型更改（不影响原先配置）

### 0.2.3

- 尝试修复磁盘列表的潜在 bug

### 0.2.2

此版本在图片脚注中显示的版本还是`0.2.1`，抱歉，我大意了没有改版本号

- 添加配置项`PS_IGNORE_NO_IO_DISK`用于忽略 IO 为 0B/s 的磁盘
- 添加配置项`PS_IGNORE_0B_NET`用于忽略上下行都为 0B/s 的网卡
- 添加触发指令`zt` `yxzt` `status`
- 获取信息收发量兼容旧版 GoCQ ，即使获取失败也不会报错而显示`未知`
- 将忽略 IO 统计磁盘名独立出一个配置项`PS_IGNORE_DISK_IOS`
- 忽略 磁盘容量盘符/IO 统计磁盘名/网卡名称 改为匹配正则表达式
- 配置项`PS_IGNORE_NETS`添加默认值`["^lo$", "^Loopback"]`
- 修复空闲内存显示错误的问题

### 0.2.1

- 尝试修复`type object is not subscriptable`报错

### 0.2.0

- 新增磁盘 IO、网络 IO 状态显示
- SWAP 大小为 0 时占用率将会显示`未部署`而不是`0%`
- CPU 等占用下方灰色字排板更改
- 获取失败的磁盘分区占用率修改为`未知%`
- 图片下方脚注修改为居中文本，字号调小，优化显示的系统信息
- 修改随机背景图 API 为[故梦 API 随机二次元壁纸](https://api.gmit.vip)
- 现在会分 QQ 记录 Bot 连接时间（不同的 QQ 连接同一个 NoneBot 显示的连接时间将不同）
- 背景图增加遮罩，颜色可配置
- 可以配置各模块的背景底色
- 可以配置分区列表中忽略的盘符（挂载点）
- 可以忽略获取容量状态失败的分区
- 可以使用`.env.*`文件中配置的`NICKNAME`作为图片中的 Bot 昵称
- 添加必须 @Bot 才能触发指令的配置
- 其他小优化/更改

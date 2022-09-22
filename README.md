<!-- markdownlint-disable MD033 MD036 MD041 -->

<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="logo">
  </a>
  <br>
  <p>
    <img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="logo">
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

![example](readme/example.png)

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

|      配置项      |       类型       | 必填 | 默认值  |              说明              |
| :--------------: | :--------------: | :--: | :-----: | :----------------------------: |
|   `PS_ONLY_SU`   | 布尔值（`bool`） |  否  | `False` | 是否只能由`SuperUsers`触发指令 |
| `PS_BLUR_RADIUS` |  整数（`int`）   |  否  |   `4`   |        背景高斯模糊半径        |
|    `PS_FONT`     |  文本（`str`）   |  否  |   无    |         自定义字体路径         |

## 🎉 使用

使用指令`运行状态`（或者`状态`）来触发插件功能  
可以在消息后面跟一张图片或者回复一张图片来自定义背景图，默认为随机背景图  
可以配置`PS_ONLY_SU`配置项来仅允许超级用户（`SuperUsers`）触发插件功能（见[配置](#️-配置)）

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

<!--
## 💡 鸣谢
-->

## 💰 赞助

感谢大家的赞助！你们的赞助将是我继续创作的动力！

- [爱发电](https://afdian.net/@lgc2333)
- <details>
    <summary>赞助二维码（点击展开）</summary>

  ![讨饭](https://raw.githubusercontent.com/lgc2333/ShigureBotMenu/master/src/imgs/sponsor.png)

  </details>

## 📝 更新日志

### 暂无

<!-- markdownlint-disable MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/template/plugin.svg" alt="NoneBotPluginText">
</p>

# NoneBot-Plugin-PicStatus

_✨ 运行状态图片版 for NoneBot2 ✨_

<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
<a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/bfec6993-aa9e-42fb-9f3e-53a5d4739373">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/bfec6993-aa9e-42fb-9f3e-53a5d4739373.svg" alt="wakatime">
</a>

<br />

<a href="https://pydantic.dev">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/template/pyd-v1-or-v2.json" alt="Pydantic Version 1 Or 2" >
</a>
<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/lgc2333/nonebot-plugin-picstatus.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-picstatus">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-picstatus.svg" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-picstatus">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-picstatus" alt="pypi download">
</a>

<br />

<a href="https://registry.nonebot.dev/plugin/nonebot-plugin-picstatus:nonebot_plugin_picstatus">
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin%2Fnonebot-plugin-picstatus" alt="NoneBot Registry">
</a>
<a href="https://registry.nonebot.dev/plugin/nonebot-plugin-picstatus:nonebot_plugin_picstatus">
  <img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin-adapters%2Fnonebot-plugin-picstatus" alt="Supported Adapters">
</a>

</div>

## 📖 介绍

不多说，直接看图！

### 效果图

<details>
  <summary>点击展开</summary>

![example](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/picstatus/example1.jpg)
![example](https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/picstatus/example2.jpg)

</details>

## 💿 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-picstatus
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-picstatus
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-picstatus
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-picstatus
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-picstatus
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_picstatus"
]
```

</details>

## ⚙️ 配置

### 见 [.env.example](https://github.com/lgc2333/nonebot-plugin-picstatus/blob/master/.env.example)

## 🎨 扩展

想知道如何为插件新增数据源、图片模板与背景图来源的话，请参考下方示例

### 见 [examples/external_example](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/tree/master/examples/external_example)

## 🎉 使用

使用指令 `运行状态`（或者 `状态` / `zt` / `yxzt` / `status`，可修改）来触发插件功能  
可以在消息后面跟一张图片或者回复一张图片来自定义背景图，默认为随机背景图  
更多自定义项参见 [配置](#️-配置)

## 📞 联系

QQ：3076823485  
Telegram：[@lgc2333](https://t.me/lgc2333)  
吹水群：[1105946125](https://jq.qq.com/?_wv=1027&k=Z3n1MpEp)  
邮箱：<lgc2333@126.com>

## 💡 鸣谢

### [nonebot/plugin-alconna](https://github.com/nonebot/plugin-alconna)

- 强大的命令解析库，和多平台适配方案

### [noneplugin/nonebot-plugin-userinfo](https://github.com/noneplugin/nonebot-plugin-userinfo)

- 多平台用户信息获取方案

### [kexue-z/nonebot-plugin-htmlrender](https://github.com/kexue-z/nonebot-plugin-htmlrender)

- HTML 渲染方案

### [LoliApi](https://docs.loliapi.com/) & [Lolicon API](https://api.lolicon.app/)

- 背景图来源

## 💰 赞助

**[赞助我](https://blog.lgc2333.top/donate)**

感谢大家的赞助！你们的赞助将是我继续创作的动力！

## 📝 更新日志

### 2.1.3

- 兼容 HTTPX 0.28

### 2.1.2

- fix [#49](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/issues/49)

### 2.1.1

- 重新加入指令带图/回复图自定义背景功能

### 2.1.0

- 优化代码结构，现在理论上可以使用其他插件往本插件内添加数据源、图片模板与背景图来源了
- 添加背景图预载功能，理论可以加快出图速度
- 删除 `gm` 背景图源，默认图源改为 `loli`
- 配置项变动：
  - 新增 `PS_BG_PRELOAD_COUNT`
  - 新增 `PS_DEFAULT_PIC_FORMAT`
  - `PS_BG_PROVIDER` 默认值变动
  - `PS_COUNT_MESSAGE_SENT_EVENT` 接受类型变动

### 2.0.0

- 代码重构，现在开发者可以更自由灵活的添加新状态图片样式
- 配置项变动：
  - 新增 `PS_TEMPLATE`
  - 新增 `PS_COLLECT_INTERVAL`
  - 新增 `PS_DEFAULT_COLLECT_CACHE_SIZE`
  - 新增 `PS_COLLECT_CACHE_SIZE`
  - 新增 `PS_COUNT_MESSAGE_SENT_EVENT`
  - 新增 `PS_DISCONNECT_RESET_COUNTER`
  - 重命名 `PS_COMPONENTS` -> `PS_DEFAULT_COMPONENTS`
  - 重命名 `PS_ADDITIONAL_CSS` -> `PS_DEFAULT_ADDITIONAL_CSS`
  - 重命名 `PS_ADDITIONAL_SCRIPT` -> `PS_DEFAULT_ADDITIONAL_SCRIPT`

<details>
<summary><strong>v1 更新日志（点击展开）</strong></summary>

### 1.1.1

- 新增内置 CSS `theme-vanilla.css`
- 微调默认 CSS

### 1.1.0

- 支持 Pydantic V2

### 1.0.3

- 修复了当有读取数据出错的分区时图片无法正常渲染的 Bug

### 1.0.2

- 修复了背景图还没加载就出图的 Bug（希望），顺带调整了一下附加 JS 的写法

### 1.0.1

- impl [#38](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/issues/38)，新增配置 `PS_OB_V11_USE_GET_STATUS`

### 1.0.0

重构项目：

- 换用 alconna 与 userinfo 适配多平台
- 换用 htmlrender 渲染图片
- 删除消息附带图片作为自定义背景图功能
- 配置项改动：
  - 添加 `PS_COMPONENTS`
  - 添加 `PS_ADDITIONAL_CSS`
  - 添加 `PS_ADDITIONAL_SCRIPT`
  - 添加 `PS_BG_PROVIDER`
  - 添加 `PS_BG_LOLICON_R18_TYPE`
  - 添加 `PS_BG_LOCAL_PATH`
  - 添加 `PS_SHOW_CURRENT_BOT_ONLY`
  - 删除 `PS_FONT`
  - 删除 `PS_CUSTOM_BG`
  - 删除 `PS_BG_COLOR`
  - 删除 `PS_MASK_COLOR`
  - 删除 `PS_BLUR_RADIUS`
  - 删除 `PS_FOOTER_SIZE`
  - 删除 `PS_MAX_TEXT_LEN`
  - 删除 `PS_DEFAULT_BG`

</details>

<details>
<summary><strong>v0 更新日志（点击展开）</strong></summary>

### 0.5.7

- 修复 Bot 刚连接时收发数为未知的问题

### 0.5.6

- 修复 Bot 连接时间与收发数显示不正确的问题

### 0.5.5

- 一些不影响使用的小更改
- 添加配置项 `PS_DEFAULT_AVATAR`、`PS_DEFAULT_BG`、`PS_COMMAND`

### 0.5.4

- 针对性修复 Shamrock 获取状态信息报错的问题 ([#34](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/issues/34))

### 0.5.3

- 修改了读取 Linux 发行版名称与版本的方式

### 0.5.2

- 修正读取分区信息错误时的提示信息 \([#33](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/issues/33)\)

### 0.5.1

- 使用 SAA 向 Telegram 平台发送消息

### 0.5.0

- 先获取状态信息再进行画图，可以获取到更精准的状态信息
- 添加进程占用信息的展示
- 测试网站结果状态码后面会带上 `reason`，如 `200 OK` / `404 Not Found`
- 添加了一些配置项（`PS_SORT_PARTS`, `PS_SORT_PARTS_REVERSE`, `PS_SORT_DISK_IOS`, `PS_SORT_NETS`, `PS_SORT_SITES`, `PS_PROC_LEN`, `PS_IGNORE_PROCS`, `PS_PROC_SORT_BY`, `PS_PROC_CPU_MAX_100P`, `PS_REPLY_TARGET`, `PS_TG_MAX_FILE_SIZE`）

### 0.4.2

- 添加配置项 `PS_REQ_TIMEOUT` ([#25](https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/issues/25))

### 0.4.1

- 现在默认使用 `pil_utils` 自动选择系统内支持中文的字体，删除插件内置字体
- 使用 `pil_utils` 写 Bot 昵称，可以显示 Emoji 等特殊字符
- 测试网站出错时不会往日志里甩错误堆栈了

### 0.4.0

- 使用 [nonebot-plugin-send-anything-anywhere](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere) 兼容多平台发送，并对 OneBot V11 和 Telegram 做了特殊兼容
- 将状态图片保存为 `jpg` 格式，缩减体积
- 测试网站现在按照配置文件中的顺序排序
- 随机图来源换回 [故梦 API](https://api.gumengya.com)
- `aiohttp` 与 `aiofiles` 换成了 `httpx` 与 `anyio`

### 0.3.3

- 修了点 bug
- 新配置 `PS_MAX_TEXT_LEN`

### 0.3.2

- 只有当 `nickname` 配置项填写后，插件才会使用该项作为图片中 Bot 的显示名称

### 0.3.1

- 修复一处 Py 3.10 以下无法正常运行的代码

### 0.3.0

配置项更新详见 [配置](#️-配置)

- 更新配置项 `PS_TEST_SITES` `PS_TEST_TIMEOUT`
- 修复`PS_NEED_AT`配置无效的 bug
- 现在只有命令完全匹配时才会触发

### 0.2.5

- 更新配置项 `PS_FOOTER_SIZE`

### 0.2.4

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

</details>

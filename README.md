# ⚡ Clash 节点跃迁 (ClashNodeX)

<p align="center">
  <img src="app_icon.png" alt="ClashNodeX Logo" width="128" height="128">
</p>

<p align="center">
  <strong>让优雅现代的 Clash Verge Rev / Mihomo，拥有超越 v2rayN 般随心所欲的节点管理体验！</strong><br>
  剪贴板秒导 · 二维码双向识别分享 · 手机扫码专属大图 · 三模精准测速 · 顶栏实时网速 · 节点调序置顶 · 属性编辑改名 · 双层防断网沙盒 · Windows / macOS 全平台原生支持
</p>

<p align="center">
  <a href="#-核心特性深度全景"><img src="https://img.shields.io/badge/Version-v1.3.0%20(Full%20Release)-blue.svg?style=flat-square" alt="Version"></a>
  <a href="#-开源协议与隐私承诺"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License"></a>
  <a href="#-平台支持与快速上手"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-brightgreen.svg?style=flat-square" alt="Platform"></a>
  <a href="https://github.com/MetaCubeX/mihomo"><img src="https://img.shields.io/badge/Core-Mihomo%20%2F%20Clash-orange.svg?style=flat-square" alt="Core"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blueviolet.svg?style=flat-square" alt="Python">
</p>

<p align="center">
  <a href="#-为什么开发-clashnodex痛点背景与设计初心">为什么开发</a> •
  <a href="#-全维度体验对比表">功能对比</a> •
  <a href="#-核心特性深度全景">核心功能</a> •
  <a href="#-平台支持与快速上手">快速上手</a> •
  <a href="#-快捷键速查表-windows--macos">快捷键</a> •
  <a href="#-常见问题与排错指南-faq">常见问题 FAQ</a> •
  <a href="#-开源支持点赞就是最大的动力">支持项目</a>
</p>

---

## 📖 为什么开发 ClashNodeX？(痛点背景与设计初心)

作为长期的科学上网重度用户，我们绝大多数人都经历过 **v2rayN** 时代的极致便捷：
- 朋友随手发来一个新节点或测试链接，按一下 `Ctrl+V` 瞬间录入；
- 屏幕上看到别人分享的配置二维码，截个图贴进去立刻自动扫码解析；
- 测出哪个节点速度快、延迟低，鼠标一点直接【⭐ 置顶】，常用节点永远排在最上方；
- 想把电脑上的节点给手机用，直接展示二维码或复制链接，手机小火箭（Shadowrocket）扫码秒导。

后来，以 **Clash Verge Rev** 为代表的现代客户端全面普及。我们深深被其精致的图形界面、极低的内存与系统资源占用、强大的基于分流规则的无感网络分流所折服。然而，在**最基础、最频繁的节点日常维护与调校上**，却存在着巨大的体验鸿沟：
1. **添加节点极度痛苦**：Clash 原生只支持订阅源，无法像 v2rayN 那样直接粘贴单个临时节点。用户要么手写复杂的 Merge 扩展脚本，要么被迫在数千行的 YAML 配置文件里小心翼翼地手动拼接缩进；
2. **顺序混乱无法排序**：每次更新订阅，所有节点顺序被打散重排，根本无法把自己最喜爱的精选节点固定在最顶层；
3. **节点无法反向导出**：想把电脑配置里的好节点分享给手机或朋友，Clash 无法生成协议链接，更无法弹出二维码供手机扫描；
4. **Reality 节点神秘超时断流**：手机小火箭上飞快的 VLESS Reality 节点，导入电脑端后却报连接超时（电脑端未显式指定 `client-fingerprint: chrome`，导致触发防嗅探主动阻断）；
5. **手改 YAML 极易断网**：手动改配置稍有空格缩进错误，Mihomo 核心直接报错崩溃，整个电脑瞬间全面断网。

**Clash 节点跃迁 (ClashNodeX)** 应运而生：
> **它绝不替代 Clash Verge Rev，而是作为其专属的“极速副驾驶管家”。在保持 Clash 核心完整性与强大分流的同时，把 v2rayN 般随心所欲的极致节点管理体验，完整交还到用户手中！**

---

## 🆚 全维度体验对比表

| 核心维度 | Clash Verge Rev 原生体验 | 经典 v2rayN | Clash 节点跃迁 (ClashNodeX) |
| :--- | :--- | :--- | :--- |
| **临时/自建单节点录入** | ❌ 极度繁琐，需手改庞大 YAML 或写合并脚本 | ✅ 复制链接按 `Ctrl+V` 极速添加 | 🌟 **复制直接按 `Ctrl+V` (Mac: `Cmd+V`)，0秒自动解析分类导入** |
| **屏幕截图二维码导入** | ❌ 完全不支持 | ⚠️ 需手动在菜单里找截图识别 | 🌟 **截屏（Win+Shift+S / 微信截图）后直接 `Ctrl+V`，AI 级自动扫码导入** |
| **反向分享 (手机扫码)** | ❌ 无法反向生成协议链接或二维码 | ⚠️ 仅基础二维码，无法自适应 | 🌟 **专属独立超清大图弹窗，小火箭/v2rayNG 远距离扫码秒识别，支持存图** |
| **多协议多格式导出** | ❌ 无法反向导出 | ⚠️ 仅支持单链接导出 | 🌟 **支持 VLESS/VMess/SS/Trojan/Hy2/TUIC 链接、Base64 订阅源及 YAML 块** |
| **节点调序与常用置顶** | ❌ 顺序受制于订阅，无法自定义 | ⚠️ 支持拖动，但不支持策略组联动 | 🌟 **点击【⭐ 置顶】或 `Alt+↑`，并自动保持策略组卡片显示顺序绝对同步** |
| **延迟测速引擎** | ⚠️ 仅单核心通用探测，易被规则干扰 | ⚠️ 基础 Ping 或 HTTP 测试 | 🌟 **三模精准测速：真外网连接 (HTTP 204) / TCP 三次握手 / TLS Connect** |
| **VLESS Reality 指纹** | ⚠️ 缺失指纹时报连接重置（手机行电脑不行） | ⚠️ 需手动逐个配置指纹 | 🌟 **内置智能注入引擎，全自动补齐 `client-fingerprint: chrome` 解决暗坑** |
| **节点编辑与重命名** | ❌ 无法可视化修改密钥端口或改名 | ✅ 支持可视化编辑 | 🌟 **按 `F2` 直接可视化修改，弹窗内即时测速，全自动级联更新所有规则** |
| **误操作与防断网体系** | ⚠️ 改错一个空格缩进立刻全网中断 | ⚠️ 语法错误直接退出 | 🛡️ **双层防断网沙盒：0.01ms 内存语义校验 + Mihomo 真实核心沙箱试运行** |
| **实时网速监控** | ⚠️ 需点开深层连接面板查看 | ❌ 仅状态栏简略显示 | ⚡ **顶栏原生实时瞬时流量卡片（直连系统命名管道，每秒动态上下行流）** |
| **跨平台原生适配** | ⚠️ 仅跨平台外壳 | ❌ 仅限 Windows | 🍎 **全平台原生支持：Windows 绿色/安装包 + macOS 原生 App (M系列/Intel)** |
| **高分屏与视觉美学** | ⚠️ 字体缩放固定 | ⚠️ 界面老旧传统 | 🎨 **三大经典主题 + 任意图片壁纸换肤 + 80%~180% 界面字体无级缩放** |

---

## ✨ 核心特性深度全景

### 1. 🔗 节点全协议反向导出与专属超清大图二维码
* **多协议标准 URL 反向逆向生成**：
  * **VLESS**：完整支持还原 Reality (`pbk`, `sid`, `sni`, `fp`)、Vision flow、WebSocket、gRPC 及 TLS 全流控参数；
  * **VMess**：标准 v2rayN Base64 JSON 规范；
  * **Shadowsocks (SS)**：标准 SIP002 规范（`ss://base64@server:port#name`）；
  * **Trojan**：标准 `trojan://password@server:port?sni=...#name`；
  * **Hysteria 2 (`hy2`)**：标准 `hysteria2://password@server:port/?sni=...#name`；
  * **TUIC**：标准 `tuic://uuid:password@server:port?sni=...#name`。
* **📱 专属大图二维码弹窗 (`QRCodeBigViewDialog`)**：
  * 工具栏提供独立绿色按钮 **`[📱 专属大图]`**，节点右键菜单支持 **`🔍 弹出专属大图二维码`**；
  * 300px~420px 动态高分黑白高对比度二维码，专为手机远距离扫码优化；
  * 手机 Shadowrocket（小火箭）、v2rayNG、Sing-box、Clash 扫码秒速录入；
  * 内置 **`[📋 复制链接]`** 与 **`[💾 保存高清图片]`**（PNG 格式导出）按钮；
  * 智能选中机制：未提前点选节点时自动默认选中第一项，弹窗强力居中置顶，按 `Esc` 键随心关闭。
* **📦 多节点批量导出矩阵**：
  * 支持多选节点批量复制所有换行链接；
  * 一键将多个选中节点打包转码为**通用 Base64 订阅源**（直接当订阅源文本使用）；
  * 一键提取纯净合规的标准 **Clash YAML proxies 代码片段**。

---

### 2. 📋 剪贴板秒导 (`Ctrl+V`) & 远程订阅批量拉取
* **0 键极速录入**：在软件任意界面按下 `Ctrl+V`（Mac: `Cmd+V`），自动识别导入；
* **支持全量前沿协议**：VLESS (Reality/Vision/gRPC/WS)、Hysteria 2、VMess (AEAD)、Trojan、SS、TUIC；
* **智能远程订阅拉取**：直接粘贴 `http(s)://` 订阅源链接，后台自动异步下载、解密并提取所有节点；
* **YAML 配置块解析**：支持直接粘贴单段或多段 YAML 节点配置代码块。

---

### 3. 📷 首创剪贴板截图 & 本地图片二维码极速识别
* **截屏即录入**：使用微信截图（`Alt+A`）、QQ截图或 Windows 系统截图（`Win+Shift+S`）截取网页、聊天窗口或文档中的节点二维码，切回软件直接按下 `Ctrl+V`，内置 OpenCV 图像算法自动从剪贴板位图中提取并解析节点！
* **本地图片批量扫码**：点击工具栏 **`[📷 扫码/图片导入]`**，选择电脑上的 PNG/JPG/WebP/BMP 图片，一键识别载入。

---

### 4. ⚡ 三模高精度延迟测速引擎
针对不同网络环境与诊断需求，提供三种可选测速模式：
1. **⚡ 真实全链路延迟 (HTTP 204)**：
   * 直连 Mihomo 内核管道，真正通过代理隧道向外网测试目标 (`http://www.gstatic.com/generate_204`) 发起真实请求；
   * 测出的是节点能否真正连通外网以及真实的端到端往返时延（RTT）。
2. **🔌 TCP 握手延迟**：
   * 并发对目标节点 IP/域名和端口发起三次握手，测出本地与节点服务器直连的网络基准时延。
3. **🔒 极速 Connect / TLS 握手**：
   * 测试目标节点的 TCP 握手 + TLS 证书协商耗时；
   * 针对 Reality 节点自动绑定 camouflage servername 校验，毫秒级得出握手状态。

---

### 5. 🛠️ VLESS Reality 智能指纹注入 (彻底治愈 Windows 端超时暗坑)
* **技术背景**：手机端（小火箭/v2rayNG/Sing-box）默认会自动伪装 Chrome 的 uTLS ClientHello 指纹；而在 Windows 端，若 YAML 未显式声明 `client-fingerprint: chrome`，Mihomo 默认采用标准 Go 指纹，直接被目标服务器的主动探测防御机制丢包，表现为“手机能连，电脑超时”。
* **全自动修复**：ClashNodeX 在导入与保存节点时，**会自动全链路补齐 `client-fingerprint: chrome`**，彻底告别玄学断连。

---

### 6. ⭐ 节点自由调序与秒级置顶
* 提供单节点【⭐ 置顶】、【⬆ 上移】、【⬇ 下移】；
* 快捷键操作：选中节点按 **`Alt + ↑`** 或 **`Alt + ↓`** 极速调序；
* 毫秒级后台异步防抖落盘，界面操作始终保持 60FPS 丝滑，绝无卡顿感。

---

### 7. 📁 代理组全生命周期管理 & 上下顺序 100% 同步
* **父级联动排序**：在 ClashNodeX 中调整分组顺序后，会自动深度更新维护顶级策略组（如【节点选择】/【PROXY】）内部引用的相对顺序，**保证在 Clash Verge Rev 主界面中的代理组卡片上下排列顺序完全一致**！
* **新建空分组安全兜底**：独创安全占位机制，新分组自动通过内核语法校验，杜绝因分组暂无节点引发的核心崩溃。

---

### 8. ✏️ 节点属性完整可视化编辑与重命名 (`F2` / 双击)
* 选中节点按 **`F2`** 或双击节点，直接修改节点名称、服务器域名/IP、端口、UUID 或密钥；
* **弹窗内即时测速**：在编辑窗口内可选择测速模式，一键验证修改后的参数是否可用；
* **全局级联同步**：重命名节点时，自动级联更新所有代理分组（`proxy-groups`）和分流规则（`rules`）中的该节点引用，绝不断链。

---

### 9. 🛡️ 双层防断网安全沙盒体系（永不断网承诺）
每次保存写盘前强制执行两道防线：
1. **第一道：0.01ms 内存拓扑语义校验**：验证所有规则引用的目标实体是否存在，拦截孤儿引用；
2. **第二道：Mihomo 内核独立沙箱试运行**（`verge-mihomo -t`）：在隔离的临时沙盒环境中进行真实语法检测；
* **检测到任何语法或语义风险立即拦截并自动回滚备份**，绝不破坏原有正常网络。

---

### 10. 🎨 原生三套经典主题 + 任意图片壁纸换肤
* **内置经典三大纯色主题**：
  * ⚪ **经典浅白 (Default Light)**：清爽素雅，办公与白昼首选；
  * 🌙 **极客黑夜 (Dark Night)**：深邃沉浸，夜间极客护眼；
  * ❄️ **现代冷灰 (Nord Slate)**：GitHub 雅致风，柔和高级；
* **🖼️ 图片皮肤/壁纸自由导入**：
  * 支持将任意图片（PNG/JPG/WebP/BMP）一键设置为软件背景壁纸；
  * 内置智能色彩识别算法，根据壁纸明暗自动反转文字与按钮对比度，美观且清晰易读。

---

### 11. 🔠 界面字体多档无级缩放
* 针对大屏 2K/4K 高分屏或距离较远的场景，顶部工具栏提供 **`[A-]` `[100%]` `[A+]`** 调节按钮；
* 支持在 80% ~ 180% 之间平滑无级放大缩小，自动记忆用户偏好。

---

## 🖥️ 平台支持与快速上手

### 🪟 Windows 用户使用指南 (Win 10 / 11 64-bit)

| 版本类型 | 文件名称 | 适用场景 | 说明 |
| :--- | :--- | :--- | :--- |
| **绿色免安装版 (首推)** | `ClashNodeX.exe` | 绝大多数用户 | 单文件免安装，解压即用，支持随身携带 |
| **现代安装包版** | `ClashNodeX_Setup.exe` | 习惯快捷方式的用户 | 带桌面快捷方式、开始菜单及卸载向导 |

#### 快速开始：
1. 确保电脑上的 **Clash Verge Rev** 或 **Mihomo** 处于开启运行状态；
2. 下载 `ClashNodeX.exe` 直接双击打开；
3. 软件会自动识别当前激活的 Clash 配置 Profile；
4. 复制你的节点或订阅链接，在软件中按下 `Ctrl+V`，享受飞速管理体验！

---

### 🍎 macOS 用户使用指南 (Apple Silicon M系列 & Intel)

| 版本类型 | 文件名称 | 说明 |
| :--- | :--- | :--- |
| **原生应用压缩包** | `ClashNodeX_macOS.zip` | 解压即得苹果原生 `ClashNodeX.app` |
| **原生应用目录** | `ClashNodeX.app` | 标准 macOS 应用程序 Bundle 包 |

#### 快速开始：
1. 下载 `ClashNodeX_macOS.zip` 并双击解压，得到 `ClashNodeX.app`；
2. 将 `ClashNodeX.app` 拖入系统的 **「访达 -> 应用程序 (Applications)」** 目录或放在桌面上；
3. 双击 `ClashNodeX.app` 启动，首次运行会自动完成环境探测与必要依赖准备；
4. **若遇到 macOS 提示“应用已损坏，打不开”或“未知的开发者”**：
   - 这是由于个人开源软件未缴纳苹果昂贵开发者证书签名的系统 Gatekeeper 机制；
   - 只需打开 Mac 的 **终端 (Terminal)**，复制并运行以下命令即可正常打开：
     ```bash
     sudo xattr -cr /Applications/ClashNodeX.app
     ```
   - 更多进阶技巧请查阅 **[🍎 macOS 专属使用指南 (README_macOS.md)](README_macOS.md)**。

---

### 💻 开发者源码运行指南

```bash
# 1. 克隆代码仓库
git clone https://github.com/<your-username>/clash-node-manager.git
cd clash-node-manager

# 2. 安装 Python 依赖 (Python 3.10+)
pip install -r requirements.txt

# 3. 启动图形界面
# Windows:
python gui.pyw
# macOS / Linux:
python3 gui.pyw
```

---

## ⌨️ 快捷键速查表 (Windows & macOS)

| Windows 快捷键 | macOS 快捷键 | 功能说明 |
| :--- | :--- | :--- |
| **`Ctrl + V`** | **`Cmd + V`** | 剪贴板快速导入节点、订阅链接或识别截屏二维码 |
| **`Ctrl + S`** | **`Cmd + S`** | 立即安全保存并触发 Clash 内核热重载 |
| **`Ctrl + T`** | **`Cmd + T`** | 批量测试当前分组全部节点延迟 |
| **`F2`** / 双击行 | **`F2`** / 双击行 | 打开节点属性编辑与弹窗即时测速窗口 |
| **`Alt + ↑`** | **`Option + ↑`** | 上移当前选中的节点 |
| **`Alt + ↓`** | **`Option + ↓`** | 下移当前选中的节点 |
| **`Ctrl + ↑`** | **`Cmd + ↑`** | 上移当前选中的分组 |
| **`Ctrl + ↓`** | **`Cmd + ↓`** | 下移当前选中的分组 |
| **`Delete`** | **`Delete`** | 从当前分组中移除选中的节点 |
| **`F5`** | **`F5`** | 重新从本地磁盘加载当前 Profile 配置 |
| **鼠标右键** | **触控板双指轻按** | 弹出 macOS 风格圆角右键上下文菜单 |

---

## ❓ 常见问题与排错指南 (FAQ)

<details>
<summary><strong>Q1: 为什么提示找不到 Clash Verge Rev 配置文件？</strong></summary>
<br>
A: 请确认 Clash Verge Rev 或 Mihomo 已经启动并正在运行。ClashNodeX 会自动扫描 Windows / macOS 标准路径（如 <code>~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev</code> 或 <code>~/.config/mihomo</code>）。若使用非标准便携安装版，可在软件设置中手动指定配置目录路径。
</details>

<details>
<summary><strong>Q2: 为什么手机小火箭上能连的 Reality 节点，电脑上总是超时？</strong></summary>
<br>
A: 这是由于电脑端未配置 TLS 浏览器指纹模拟。ClashNodeX 内置了智能指纹注入引擎，只要经由 ClashNodeX 导入或编辑保存的节点，都会自动注入 <code>client-fingerprint: chrome</code>，即可彻底解决此问题。
</details>

<details>
<summary><strong>Q3: 专属大图二维码手机扫不出来怎么办？</strong></summary>
<br>
A: 请确保手机扫码软件是代理客户端（如 Shadowrocket 小火箭、v2rayNG、Clash 等）自带的扫码器，而不是微信/支付宝原生扫码（微信不识别 vless:// 等专有代理协议）。在专属大图弹窗中也可以点击【复制链接】直接发送文本给手机。
</details>

<details>
<summary><strong>Q4: 修改保存后，Clash Verge Rev 没有立刻切换怎么办？</strong></summary>
<br>
A: ClashNodeX 会自动调用 Mihomo 核心外部控制接口进行热重载 (Hot Reload)。若未即时刷新，可以在 Clash Verge Rev 主界面点击右上角刷新配置，或按软件工具栏最右侧绿色的【💾 立即保存 (Ctrl+S)】强制重载。
</details>

<details>
<summary><strong>Q5: 本工具是否会收集或上传我的节点数据或订阅链接？</strong></summary>
<br>
A: <strong>绝对不会！</strong> ClashNodeX 遵循 MIT 开源协议，所有代码完全公开透明。所有配置解析与写入完全在您本地内存与硬盘中闭环运行，没有任何遥测代码，绝不向任何第三方服务器发送任何数据。
</details>

---

## 🌟 开源支持：点赞就是最大的动力！

ClashNodeX 是一款完全免费、无广告、纯粹出于极客热爱而打造的开源工具。

我们**不设任何打赏或收款码**，也不收取任何费用。如果您觉得它为您解决了节点管理的痛点、节省了大量繁琐折腾的时间：

👉 **请在 GitHub 页面右上角为本项目点一颗 ⭐️ Star（点赞）并点击 Watch（关注）！**<br>
您的每一个 Star 都是作者持续迭代与维护的最强动力！

---

## 💬 交流反馈 (GitHub Issues)

- 如在使用中遇到任何 Bug、适配问题或有新功能构想，欢迎在 GitHub 仓库提交 **[Issue](../../issues)**；
- 作者手机绑定了 GitHub 官方高优先级邮件实时推送，收到 Issue 通知后会在第一时间进行排查与修复。

---

## 📄 开源协议与免责声明 (MIT License)

- **开源协议**：本项目基于国际通用的 **[MIT License](LICENSE)** 协议开源，项目代码版权归作者所有；
- **免责声明**：本项目按“现状 (AS IS)”提供，仅作为辅助本地配置管理的效率工具，不提供任何形式的代理服务或节点。作者不对使用本工具产生的任何间接问题承担法律责任。
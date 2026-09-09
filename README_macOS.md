# 🍎 ClashNodeX (Clash 节点跃迁) macOS 使用与编译指南

欢迎使用 **ClashNodeX** macOS 跨平台版本！本工具原生兼容 Apple Silicon (M1/M2/M3/M4 系列芯片) 以及 Intel Mac，支持 macOS 10.15 (Catalina) 及更高版本（macOS Sonoma / Sequoia 原生 Retina 视网膜高清适配）。

---

## 📥 方式一：下载预编译版 (.dmg 安装包)

1. 前往项目的 [Releases 页面](https://github.com/gpt-bridge/ClashNodeX/releases)；
2. 下载最新版 **`ClashNodeX_macOS.dmg`**；
3. 双击打开 `.dmg` 镜像，将 **`ClashNodeX.app`** 拖入 **`Applications`（应用程序）** 文件夹；
4. **首次启动提示“已损坏，无法打开”解决办法**：
   - 因为开源软件未购买苹果昂贵的开发者证书（年费 $99），macOS Gatekeeper 会自动加上隔离标记；
   - 打开 Mac 自带的 **终端（Terminal）**，粘贴运行以下命令即可秒解：
     ```bash
     sudo xattr -cr /Applications/ClashNodeX.app
     ```
   - 随后即可直接在“启动台”或“访达”中正常双击运行！

---

## 🚀 方式二：直接通过源码一键运行

如果你的 Mac 上已安装 Python 3.10+：

1. 克隆或下载本仓库源码到本地；
2. 打开终端进入项目根目录：
   ```bash
   cd ClashNodeX
   ```
3. 执行一键运行脚本：
   ```bash
   chmod +x run_macos.sh
   ./run_macos.sh
   ```
   *脚本会自动检查并安装依赖（PyYAML、Pillow、qrcode 等），随后启动图形界面。*

---

## 🔨 方式三：在本地 Mac 上自行编译生成 .dmg

如果你想在本地 Mac 上自行打包属于自己的 `.app` 或 `.dmg`：

```bash
chmod +x build_macos.sh
./build_macos.sh
```

构建完成后，你将在 `dist/` 目录下得到：
- `dist/ClashNodeX.app` (原生应用程序包)
- `dist/ClashNodeX_v1.3.0_macOS.dmg` (DMG 安装镜像)
- `dist/ClashNodeX_macOS.zip` (便携压缩包)

---

## 💡 macOS 专属特性与优化
- **Retina 视网膜高清适配**：原生支持苹果视网膜屏幕，界面与文字细腻锐利；
- **苹方字体（PingFang SC）**：默认采用苹果系统经典优雅的苹方字体，视觉质感出众；
- **原生快捷键支持**：
  - `Command + V`：剪贴板极速导入节点；
  - `Command + S`：立即保存并同步；
  - `Command + T`：测试选中节点延迟；
- **触控板双指右键适配**：全面支持 MacBook 触控板双指轻按弹出右键上下文菜单。

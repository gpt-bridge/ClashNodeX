#!/usr/bin/env bash
set -e

echo "========================================================="
echo "🚀 ClashNodeX macOS 打包构建脚本 (Build for macOS)"
echo "========================================================="

# 1. 确保安装依赖
echo "📦 正在安装依赖..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# 2. 清理旧构建缓存
rm -rf build dist

# 3. 使用 PyInstaller 构建 .app 包
echo "🔨 正在编译 ClashNodeX.app..."
pyinstaller ClashNodeX_macOS.spec --noconfirm

# 4. 构建 DMG 镜像
echo "💿 正在生成 DMG 安装镜像..."
DMG_NAME="ClashNodeX_v1.3.0_macOS.dmg"
DMG_DIR="dist/dmg_staging"
rm -rf "$DMG_DIR" "$DMG_NAME"
mkdir -p "$DMG_DIR"

cp -R "dist/ClashNodeX.app" "$DMG_DIR/"
ln -s /Applications "$DMG_DIR/Applications"

hdiutil create -volname "ClashNodeX" -srcfolder "$DMG_DIR" -ov -format UDZO "dist/$DMG_NAME"
rm -rf "$DMG_DIR"

# 5. 同时生成 .app.zip 压缩包供免挂载使用
echo "📦 正在生成 ClashNodeX_macOS.zip..."
cd dist
zip -r -y "ClashNodeX_macOS.zip" "ClashNodeX.app"
cd ..

echo "========================================================="
echo "🎉 构建成功！生成文件位于 dist/ 目录："
echo "   - dist/$DMG_NAME (DMG 拖拽安装镜像)"
echo "   - dist/ClashNodeX_macOS.zip (独立 App 压缩包)"
echo "========================================================="

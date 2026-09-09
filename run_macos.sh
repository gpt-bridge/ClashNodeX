#!/usr/bin/env bash
# ClashNodeX 一键启动脚本 (macOS)
set -e

if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未在您的系统检测到 python3，请先安装 Python 3.10+ (可通过 brew install python3 安装)"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "⚡ 检查并安装依赖..."
python3 -m pip install -r requirements.txt -q

echo "🚀 启动 ClashNodeX..."
python3 gui.pyw

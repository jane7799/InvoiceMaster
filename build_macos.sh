#!/bin/bash
# macOS 本地打包脚本

echo "🚀 开始打包 InvoiceMaster for macOS..."

# 检查Python环境
echo "📦 检查Python版本..."
python3 --version

# 安装PyInstaller
echo "📦 安装PyInstaller..."
pip3 install pyinstaller

# 清理旧的构建文件
echo "🧹 清理旧文件..."
rm -rf build dist *.spec

# 开始打包
echo "🔨 开始打包..."
pyinstaller \
  --name "智能发票打印助手" \
  --windowed \
  --onefile \
  --icon=logo.icns \
  --add-data "qr1.jpg:." \
  --add-data "qr2.jpg:." \
  --add-data "license_manager.py:." \
  --add-data "icon_1x1_l.png:." \
  --add-data "icon_1x1_p.png:." \
  --add-data "icon_1x2_l.png:." \
  --add-data "icon_1x2_p.png:." \
  --add-data "icon_2x2_l.png:." \
  --add-data "icon_2x2_p.png:." \
  InvoiceMaster.py

# 检查结果
if [ -f "dist/智能发票打印助手.app/Contents/MacOS/智能发票打印助手" ]; then
    echo "✅ 打包成功！"
    echo "📍 位置: dist/智能发票打印助手.app"
    echo ""
    echo "🧪 测试运行:"
    echo "   open dist/智能发票打印助手.app"
else
    echo "❌ 打包失败！"
    exit 1
fi

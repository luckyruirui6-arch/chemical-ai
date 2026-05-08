#!/bin/bash
echo "========================================"
echo "化工AI专业版 - Mac/Linux启动脚本"
echo "========================================"
echo ""

echo "[1/3] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi
echo "Python环境检测通过"
echo ""

echo "[2/3] 安装依赖包..."
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "依赖安装完成"
echo ""

echo "[3/3] 启动化工AI系统..."
echo ""
echo "========================================"
echo "系统启动成功！"
echo "请在浏览器中访问: http://localhost:5000"
echo "默认账号: admin / admin123"
echo "========================================"
echo ""
python3 app.py

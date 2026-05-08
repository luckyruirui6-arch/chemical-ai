@echo off
chcp 65001 >nul
echo ========================================
echo 化工AI专业版 - Windows启动脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo Python环境检测通过
echo.

echo [2/3] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo 依赖安装完成
echo.

echo [3/3] 启动化工AI系统...
echo.
echo ========================================
echo 系统启动成功！
echo 请在浏览器中访问: http://localhost:5000
echo 默认账号: admin / admin123
echo ========================================
echo.
python app.py

pause

@echo off
echo ========================================
echo 知识管理智能体 - Web演示启动脚本
echo ========================================
echo.
echo 正在启动Web代理服务器...
echo 服务器地址: http://localhost:3000
echo.
echo 按Ctrl+C停止服务器
echo ========================================
echo.

python mcp_web_proxy.py

pause
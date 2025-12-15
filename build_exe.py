#!/usr/bin/env python3
"""
本地构建 EXE 文件的脚本
使用方法: python build_exe.py
"""

import os
import sys
import subprocess
import shutil

def check_dependencies():
    """检查必要的依赖"""
    print("检查依赖...")
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import pygame
        print("✓ pygame 已安装")
    except ImportError:
        print("✗ pygame 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
    
    try:
        import PIL
        print("✓ Pillow 已安装")
    except ImportError:
        print("✗ Pillow 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])

def check_assets():
    """检查资源文件"""
    print("\n检查资源文件...")
    if not os.path.exists('assets'):
        print("✗ assets 目录不存在")
        return False
    
    if not os.path.exists('assets/cards'):
        print("✗ assets/cards 目录不存在")
        return False
    
    if not os.path.exists('assets/characters'):
        print("✗ assets/characters 目录不存在") 
        return False
    
    # 统计资源文件
    card_files = [f for f in os.listdir('assets/cards') if f.endswith('.png')]
    character_files = [f for f in os.listdir('assets/characters') if f.endswith('.png')]
    
    print(f"✓ 找到 {len(card_files)} 个卡牌图片")
    print(f"✓ 找到 {len(character_files)} 个角色图片")
    
    if os.path.exists('assets/icon.ico'):
        print("✓ 找到应用程序图标")
    else:
        print("! 未找到应用程序图标 (assets/icon.ico)")
        print("  将使用默认图标")
    
    return True

def build_exe():
    """构建 EXE 文件"""
    print("\n开始构建 EXE 文件...")
    
    # 清理之前的构建
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"清理 {dir_name} 目录")
    
    # 执行 PyInstaller
    try:
        result = subprocess.run([
            'pyinstaller', 
            '--clean', 
            'MagicWound.spec'
        ], check=True, capture_output=True, text=True)
        
        print("✓ PyInstaller 执行成功")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller 执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    
    # 检查输出
    exe_path = 'dist/MagicWound.exe'
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✓ EXE 文件构建成功: {exe_path}")
        print(f"✓ 文件大小: {size_mb:.1f} MB")
        return True
    else:
        print("✗ EXE 文件未找到")
        return False

def main():
    """主函数"""
    print("=== MagicWound EXE 构建工具 ===")
    
    # 检查当前目录
    if not os.path.exists('main_gui.py'):
        print("✗ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 执行构建步骤
    if not check_dependencies():
        sys.exit(1)
    
    if not check_assets():
        print("✗ 资源文件检查失败")
        sys.exit(1)
    
    if build_exe():
        print("\n🎉 构建完成！")
        print(f"可执行文件位置: dist/MagicWound.exe")
        print("你可以双击运行该文件")
    else:
        print("\n❌ 构建失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
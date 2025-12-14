#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成占位符图片
用于测试图形界面，后续可替换为实际插图
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("需要安装 Pillow: pip install pillow")
    import sys
    sys.exit(1)

# 资源目录
ASSETS_DIR = Path(__file__).parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
CHARACTERS_DIR = ASSETS_DIR / "characters"

# 创建目录
CARDS_DIR.mkdir(parents=True, exist_ok=True)
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)

# 卡牌列表
CARDS = [
    ("madposion", "狂乱药水", (150, 50, 200)),
    ("organichemistry", "魔药学", (50, 150, 200)),
    ("slowdown", "缓慢药水", (100, 100, 200)),
    ("timeelder", "时空限速", (100, 50, 150)),
    ("lgbtq", "多彩药水", (200, 100, 200)),
    ("lazarus", "起尸", (80, 50, 100)),
    ("dontforgotme", "瓶装记忆", (50, 150, 255)),
    ("memorywipe", "记忆屏蔽", (50, 100, 200)),
    ("memorycrush", "记忆摧毁", (100, 50, 50)),
    ("what", "你说啥？", (200, 150, 50)),
    ("balance", "平衡", (150, 150, 150)),
    ("tearall", "遗忘灵药", (50, 50, 100)),
    ("wordle", "Wordle", (200, 200, 50)),
    ("idontcar", "窝不载乎", (150, 100, 50)),
]

# 角色列表
CHARACTERS = [
    ("jintian", "金天", (50, 150, 255)),
    ("sanjin", "三金", (150, 255, 150)),
    ("jiangyuan", "江源", (255, 255, 150)),
]

def create_card_placeholder(card_id: str, name: str, color: tuple):
    """创建卡牌占位符"""
    # 创建图片
    img = Image.new('RGB', (200, 200), color=color)
    draw = ImageDraw.Draw(img)
    
    # 绘制边框
    draw.rectangle([0, 0, 199, 199], outline=(255, 255, 255), width=3)
    
    # 绘制对角线
    draw.line([0, 0, 200, 200], fill=(255, 255, 255), width=2)
    draw.line([200, 0, 0, 200], fill=(255, 255, 255), width=2)
    
    # 尝试添加文字
    try:
        font = ImageFont.truetype("simhei.ttf", 24)  # Windows 中文字体
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)  # macOS
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)  # Linux
            except:
                font = ImageFont.load_default()
    
    # 绘制文字
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (200 - text_width) // 2
    text_y = (200 - text_height) // 2
    
    # 文字阴影
    draw.text((text_x + 2, text_y + 2), name, fill=(0, 0, 0), font=font)
    # 文字主体
    draw.text((text_x, text_y), name, fill=(255, 255, 255), font=font)
    
    # 保存
    output_path = CARDS_DIR / f"{card_id}.png"
    img.save(output_path)
    print(f"创建卡牌: {output_path}")

def create_character_placeholder(char_id: str, name: str, color: tuple):
    """创建角色占位符"""
    # 创建图片
    img = Image.new('RGB', (300, 300), color=color)
    draw = ImageDraw.Draw(img)
    
    # 绘制边框
    draw.rectangle([0, 0, 299, 299], outline=(255, 255, 255), width=4)
    
    # 绘制圆形
    draw.ellipse([50, 50, 250, 250], outline=(255, 255, 255), width=3)
    
    # 尝试添加文字
    try:
        font = ImageFont.truetype("simhei.ttf", 36)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 36)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 36)
            except:
                font = ImageFont.load_default()
    
    # 绘制文字
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (300 - text_width) // 2
    text_y = (300 - text_height) // 2
    
    # 文字阴影
    draw.text((text_x + 2, text_y + 2), name, fill=(0, 0, 0), font=font)
    # 文字主体
    draw.text((text_x, text_y), name, fill=(255, 255, 255), font=font)
    
    # 保存
    output_path = CHARACTERS_DIR / f"{char_id}.png"
    img.save(output_path)
    print(f"创建角色: {output_path}")

def main():
    print("开始生成占位符图片...")
    print(f"输出目录: {ASSETS_DIR}")
    
    # 生成卡牌
    print("\n生成卡牌占位符:")
    for card_id, name, color in CARDS:
        create_card_placeholder(card_id, name, color)
    
    # 生成角色
    print("\n生成角色占位符:")
    for char_id, name, color in CHARACTERS:
        create_character_placeholder(char_id, name, color)
    
    print("\n✅ 完成！所有占位符已生成。")
    print("提示：可以用实际插图替换这些占位符文件。")

if __name__ == "__main__":
    main()

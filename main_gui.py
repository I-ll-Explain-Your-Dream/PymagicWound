#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔法伤痕卡牌游戏 - Pygame图形化版本
MagicWound Card Game - Pygame GUI Version
"""

import sys
import os
import base64
import zlib
import random
import pygame
import socket
import threading
import queue
from typing import List, Dict, Optional, Tuple, Callable
from enum import IntEnum
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

# 初始化 Pygame
pygame.init()
pygame.font.init()

# 中文字体设置
def get_chinese_font(size):
    """获取中文字体"""
    font_names = [
        'SimHei',  # 黑体
        'Microsoft YaHei',  # 微软雅黑
        'SimSun',  # 宋体
        'KaiTi',  # 楷体
        'C:\\Windows\\Fonts\\msyh.ttc',  # 微软雅黑路径
        'C:\\Windows\\Fonts\\simhei.ttf',  # 黑体路径
        'C:\\Windows\\Fonts\\simsun.ttc',  # 宋体路径
    ]
    
    for font_name in font_names:
        try:
            return pygame.font.SysFont(font_name, size)
        except:
            try:
                return pygame.font.Font(font_name, size)
            except:
                continue
    
    # 如果都失败了，返回默认字体
    return pygame.font.Font(None, size)

# ============= 常量定义 =============

# 屏幕设置
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# 颜色定义
COLOR_BG = (20, 20, 40)
COLOR_CARD_BG = (40, 40, 60)
COLOR_CARD_BORDER = (100, 100, 150)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 200)
COLOR_BUTTON = (60, 60, 100)
COLOR_BUTTON_HOVER = (80, 80, 120)
COLOR_HP_BAR = (220, 50, 50)
COLOR_MANA_BAR = (50, 150, 220)
COLOR_ENERGY_BAR = (150, 220, 50)

# 元素颜色
ELEMENT_COLORS = {
    1: (200, 200, 200),  # PHYSICAL - 灰
    2: (255, 255, 150),  # LIGHT - 金
    3: (100, 50, 150),   # DARK - 紫
    4: (50, 150, 255),   # WATER - 蓝
    5: (255, 100, 50),   # FIRE - 红
    6: (150, 100, 50),   # EARTH - 棕
    7: (150, 255, 150),  # WIND - 绿
}

# 稀有度颜色
RARITY_COLORS = {
    1: (180, 180, 180),  # COMMON
    2: (100, 200, 100),  # UNCOMMON
    3: (100, 150, 255),  # RARE
    4: (255, 150, 50),   # MYTHIC
    5: (255, 100, 255),  # FUNNY
}

# 资源目录
ASSETS_DIR = Path(__file__).parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
CHARACTERS_DIR = ASSETS_DIR / "characters"
UI_DIR = ASSETS_DIR / "ui"

# 创建资源目录
ASSETS_DIR.mkdir(exist_ok=True)
CARDS_DIR.mkdir(exist_ok=True)
CHARACTERS_DIR.mkdir(exist_ok=True)
UI_DIR.mkdir(exist_ok=True)

# ============= 枚举定义 =============

class CardType(IntEnum):
    """卡牌类型"""
    CREATURE = 1
    SPELL = 2

class Element(IntEnum):
    """元素类型"""
    PHYSICAL = 1
    LIGHT = 2
    DARK = 3
    WATER = 4
    FIRE = 5
    EARTH = 6
    WIND = 7

class Rarity(IntEnum):
    """稀有度"""
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    MYTHIC = 4
    FUNNY = 5

class DeckType(IntEnum):
    """牌组类型"""
    STANDARD = 1
    CASUAL = 2

class GameState(IntEnum):
    """游戏状态"""
    MAIN_MENU = 1
    DECK_BUILDER = 2
    DECK_LIST = 3
    BATTLE = 4
    CARD_VIEWER = 5
    CHARACTER_VIEWER = 6
    NETWORK_LOBBY = 7
    DECK_DETAIL = 8
    DECK_EXPORT = 9
    DECK_IMPORT = 10

# ============= 辅助函数 =============

def element_to_string(element: Element) -> str:
    """元素转字符串"""
    mapping = {
        Element.PHYSICAL: "物理", Element.LIGHT: "光", Element.DARK: "暗",
        Element.WATER: "水", Element.FIRE: "火", Element.EARTH: "土", Element.WIND: "风"
    }
    return mapping.get(element, "未知")

def rarity_to_string(rarity: Rarity) -> str:
    """稀有度转字符串"""
    mapping = {
        Rarity.COMMON: "普通", Rarity.UNCOMMON: "罕见", Rarity.RARE: "稀有",
        Rarity.MYTHIC: "神话", Rarity.FUNNY: "趣味"
    }
    return mapping.get(rarity, "未知")

def card_type_to_string(card_type: CardType) -> str:
    """卡牌类型转字符串"""
    return "生物" if card_type == CardType.CREATURE else "法术"

def generate_checksum(data: str) -> str:
    """生成CRC32校验和"""
    crc = zlib.crc32(data.encode('utf-8')) & 0xffffffff
    return f"{crc:08x}"[:4]

def encode_deck_code(data: str) -> str:
    """编码牌组代码"""
    checksum = generate_checksum(data)
    combined = f"{data}|{checksum}"
    return base64.b64encode(combined.encode('utf-8')).decode('utf-8')

def decode_deck_code(code: str) -> Optional[Tuple[str, bool]]:
    """解码牌组代码"""
    try:
        decoded = base64.b64decode(code).decode('utf-8')
        parts = decoded.split('|')
        if len(parts) != 2:
            return None, False
        data, checksum = parts
        if generate_checksum(data) != checksum:
            return None, False
        return data, True
    except Exception:
        return None, False

# ============= 核心数据类 =============

@dataclass
class Character:
    """角色类"""
    id: str
    name: str
    elements: List[Element]
    health: int
    energy: int  # 普通人为0，魔法师有魔力上限
    defense: int  # 防御力
    attack: int  # 攻击力
    ability: str  # 专属技能名称
    description: str  # 专属技能描述
    is_active_ability: bool  # 是否为主动技能
    image_path: Optional[str] = None
    
    def has_element(self, element: Element) -> bool:
        return element in self.elements
    
    def is_mage(self) -> bool:
        """判断是否为魔法师"""
        # 只有物理属性的是普通人，其他都是魔法师
        return not (len(self.elements) == 1 and self.elements[0] == Element.PHYSICAL)
    
    def get_image(self) -> Optional[pygame.Surface]:
        """获取角色图片"""
        if self.image_path and os.path.exists(self.image_path):
            try:
                return pygame.image.load(self.image_path)
            except:
                pass
        return None

@dataclass
class Card:
    """卡牌类"""
    id: str
    name: str
    elements: List[Element]
    cost: int
    rarity: Rarity
    description: str
    attack: int = 0
    defense: int = 0
    health: int = 0
    image_path: Optional[str] = None
    
    @property
    def card_type(self) -> CardType:
        if self.attack == 0 and self.defense == 0 and self.health == 0:
            return CardType.SPELL
        return CardType.CREATURE
    
    def has_element(self, element: Element) -> bool:
        return element in self.elements
    
    def serialize(self) -> str:
        return self.id
    
    def get_image(self) -> Optional[pygame.Surface]:
        """获取卡牌图片"""
        if self.image_path and os.path.exists(self.image_path):
            try:
                return pygame.image.load(self.image_path)
            except:
                pass
        return None

class Deck:
    """牌组类"""
    def __init__(self, name: str, deck_type: DeckType = DeckType.STANDARD):
        self.name = name
        self.deck_type = deck_type
        self.cards: List[Card] = []
        self.characters: List[Character] = []
        self.deck_elements: List[Element] = []
        self.deck_code = ""
        self.max_card_limit = 20
        self._update_deck_code()
    
    def add_card(self, card: Card) -> bool:
        if self.deck_type == DeckType.STANDARD and card.rarity == Rarity.FUNNY:
            return False
        if len(self.cards) >= self.max_card_limit:
            return False
        self.cards.append(card)
        self._update_deck_elements()
        self._update_deck_code()
        return True
    
    def remove_card(self, card_name: str) -> bool:
        for i, card in enumerate(self.cards):
            if card.name == card_name:
                self.cards.pop(i)
                self._update_deck_elements()
                self._update_deck_code()
                return True
        return False
    
    def add_character(self, character: Character) -> bool:
        if len(self.characters) >= 3:
            return False
        self.characters.append(character)
        self._update_deck_code()
        return True
    
    def remove_character(self, character_name: str) -> bool:
        for i, char in enumerate(self.characters):
            if char.name == character_name:
                self.characters.pop(i)
                self._update_deck_code()
                return True
        return False
    
    def is_valid(self) -> bool:
        return len(self.cards) >= 20 and len(self.characters) == 3
    
    def _update_deck_elements(self):
        elements = set()
        for card in self.cards:
            elements.update(card.elements)
        self.deck_elements = sorted(list(elements))
    
    def _update_deck_code(self):
        char_ids = ','.join(char.id for char in self.characters)
        card_ids = ','.join(card.serialize() for card in self.cards)
        data = f"{self.name};{int(self.deck_type)};{char_ids};{card_ids};{self.max_card_limit};"
        self.deck_code = encode_deck_code(data)
    
    def import_from_code(self, code: str, all_cards: List[Card], 
                        all_characters: List[Character]) -> bool:
        data, valid = decode_deck_code(code)
        if not valid or data is None:
            return False
        try:
            parts = data.split(';')
            if len(parts) < 4:
                return False
            self.name = parts[0]
            self.deck_type = DeckType(int(parts[1]))
            char_ids = parts[2].split(',') if parts[2] else []
            self.characters = []
            for char_id in char_ids:
                if char_id:
                    char = next((c for c in all_characters if c.id == char_id), None)
                    if char:
                        self.characters.append(char)
            card_ids = parts[3].split(',') if parts[3] else []
            self.cards = []
            for card_id in card_ids:
                if card_id:
                    card = next((c for c in all_cards if c.id == card_id), None)
                    if card:
                        self.cards.append(card)
            if len(parts) >= 5:
                try:
                    self.max_card_limit = int(parts[4])
                except ValueError:
                    pass
            self._update_deck_elements()
            self.deck_code = code
            return True
        except Exception:
            return False

class CharacterDatabase:
    """角色数据库"""
    def __init__(self):
        self.all_characters: List[Character] = []
        self._initialize_characters()
    
    def _initialize_characters(self):
        self.all_characters = [
            # 魔法师角色 - 光属性
            Character("light_mage1", "光明祭司", [Element.LIGHT], 20, 20, 3, 2,
                     "圣光治愈", "消耗8点魔力，恢复友方角色8点生命值。",
                     True,
                     str(CHARACTERS_DIR / "light_priest.png")),
            Character("light_mage2", "光辉骑士", [Element.LIGHT], 25, 15, 4, 3,
                     "光明斩击", "消耗10点魔力，对目标造成8点光属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "light_knight.png")),
            
            # 魔法师角色 - 暗属性
            Character("dark_mage1", "暗影术士", [Element.DARK], 22, 18, 2, 3,
                     "暗影腐蚀", "消耗12点魔力，目标下回合防御力-3。",
                     True,
                     str(CHARACTERS_DIR / "dark_mage.png")),
            Character("dark_mage2", "死亡骑士", [Element.DARK], 28, 12, 3, 4,
                     "死亡之握", "消耗15点魔力，对目标造成10点暗属性伤害并附加混乱1回合。",
                     True,
                     str(CHARACTERS_DIR / "death_knight.png")),
            
            # 魔法师角色 - 地属性
            Character("earth_mage1", "大地守护者", [Element.EARTH], 30, 15, 5, 2,
                     "岩石护盾", "消耗6点魔力，获得嘲讽状态和+3防御力，持续2回合。",
                     True,
                     str(CHARACTERS_DIR / "earth_guardian.png")),
            Character("earth_mage2", "震地者", [Element.EARTH], 24, 20, 3, 3,
                     "地震术", "消耗14点魔力，对所有敌方角色造成6点地属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "earth_shaker.png")),
            
            # 魔法师角色 - 火属性
            Character("fire_mage1", "火焰法师", [Element.FIRE], 18, 22, 1, 4,
                     "火球术", "消耗9点魔力，对目标造成10点火属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "fire_mage.png")),
            Character("fire_mage2", "炎魔", [Element.FIRE], 22, 18, 2, 4,
                     "烈焰风暴", "消耗16点魔力，对目标造成12点火属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "fire_demon.png")),
            
            # 魔法师角色 - 水属性
            Character("water_mage1", "水元素使", [Element.WATER], 20, 20, 2, 3,
                     "治疗波", "消耗7点魔力，恢复所有友方角色5点生命值。",
                     True,
                     str(CHARACTERS_DIR / "water_mage.png")),
            Character("water_mage2", "冰霜巫师", [Element.WATER], 22, 18, 3, 3,
                     "冰霜新星", "消耗11点魔力，对目标造成8点水属性伤害并冻结1回合。",
                     True,
                     str(CHARACTERS_DIR / "frost_mage.png")),
            
            # 魔法师角色 - 风属性
            Character("wind_mage1", "风语者", [Element.WIND], 19, 21, 1, 3,
                     "风刃", "消耗8点魔力，对目标造成9点风属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "wind_caller.png")),
            Character("wind_mage2", "风暴领主", [Element.WIND], 21, 19, 2, 4,
                     "雷霆一击", "消耗13点魔力，对目标造成11点风属性伤害。",
                     True,
                     str(CHARACTERS_DIR / "storm_lord.png")),
            
            # 普通人角色
            Character("warrior", "战士", [Element.PHYSICAL], 35, 0, 6, 4,
                     "重击", "对目标造成6点物理伤害。",
                     True,
                     str(CHARACTERS_DIR / "warrior.png")),
            Character("archer", "弓箭手", [Element.PHYSICAL], 25, 0, 3, 5,
                     "精准射击", "对目标造成5点物理伤害，无视2点防御力。",
                     True,
                     str(CHARACTERS_DIR / "archer.png")),
            Character("rogue", "盗贼", [Element.PHYSICAL], 22, 0, 2, 6,
                     "暗杀", "对目标造成7点物理伤害。",
                     True,
                     str(CHARACTERS_DIR / "rogue.png")),
            Character("knight", "骑士", [Element.PHYSICAL], 40, 0, 8, 3,
                     "盾击", "对目标造成4点物理伤害并使其下回合无法攻击。",
                     True,
                     str(CHARACTERS_DIR / "knight.png")),
        ]
    
    def get_all_characters(self) -> List[Character]:
        return self.all_characters
    
    def find_character_by_id(self, char_id: str) -> Optional[Character]:
        return next((c for c in self.all_characters if c.id == char_id), None)

class CardDatabase:
    """卡牌数据库"""
    def __init__(self):
        self.all_cards: List[Card] = []
        self._initialize_cards()
    
    def _initialize_cards(self):
        self.all_cards = [
            Card("madposion", "狂乱药水", [Element.WATER], 15, Rarity.MYTHIC,
                 "本回合中，目标人物卡牌释放三次，在其魔力不足时以三倍于魔力值消耗的生命替代。",
                 image_path=str(CARDS_DIR / "madposion.png")),
            Card("organichemistry", "魔药学领城大神！", [Element.WATER], 9, Rarity.MYTHIC,
                 "本局对战中，你的药水魔力消耗减少（2）。随机获取3张药水。",
                 image_path=str(CARDS_DIR / "organichemistry.png")),
            Card("slowdown", "缓慢药水", [Element.WATER], 5, Rarity.RARE,
                 "直到你的下个回合，你对手的牌魔力消耗增加（2）。",
                 image_path=str(CARDS_DIR / "slowdown.png")),
            Card("Timeelder", "时空限速", [Element.DARK], 5, Rarity.RARE,
                 "直到你的下个回合，你对手不能使用5张以上的牌。",
                 image_path=str(CARDS_DIR / "timeelder.png")),
            Card("LGBTQ", "多彩药水", [Element.WATER], 3, Rarity.RARE,
                 "本回合中，你的牌是所有属性。",
                 image_path=str(CARDS_DIR / "lgbtq.png")),
            Card("Lazarus,Arise!", "起尸", [Element.DARK], 2, Rarity.RARE,
                 "复活一个人物，并具有25%的生命。",
                 image_path=str(CARDS_DIR / "lazarus.png")),
            Card("DontForgotMe", "瓶装记忆", [Element.WATER], 5, Rarity.RARE,
                 "这张牌是药水。将目标玩家卡组中的8张牌洗入你的牌库。",
                 image_path=str(CARDS_DIR / "dontforgotme.png")),
            Card("TheCardLetMeWin", "记忆屏蔽", [Element.WATER], 6, Rarity.RARE,
                 "摧毁你对手牌库顶和底各2张牌。",
                 image_path=str(CARDS_DIR / "memorywipe.png")),
            Card("TheCardLetYouLose", "记忆摧毁", [Element.WATER], 2, Rarity.RARE,
                 "摧毁你和对手牌库顶和底各2张牌。然后如果你的牌库为空，你输掉游戏。",
                 image_path=str(CARDS_DIR / "memorycrush.png")),
            Card("whAt", "你说啥？", [Element.WATER], 2, Rarity.RARE,
                 "摧毁对手牌库中的1张牌。然后摧毁所有同名卡。",
                 image_path=str(CARDS_DIR / "what.png")),
            Card("balance", "平衡", [Element.LIGHT, Element.DARK], 4, Rarity.RARE,
                 "弃掉你的手牌。抽等量的牌。",
                 image_path=str(CARDS_DIR / "balance.png")),
            Card("TearAll", "遗忘灵药", [Element.WATER, Element.DARK], 18, Rarity.RARE,
                 "摧毁你对手的牌库。",
                 image_path=str(CARDS_DIR / "tearall.png")),
            Card("Wordle", "Wordle", [Element.PHYSICAL], 4, Rarity.FUNNY,
                 "使你对手下回合造成的伤害额外乘上今日Wordle的通关率。",
                 image_path=str(CARDS_DIR / "wordle.png")),
            Card("IDontcar", "窝不载乎", [Element.PHYSICAL], 2, Rarity.FUNNY,
                 "你的对手发送的表情改为汽车鸣笛声。",
                 image_path=str(CARDS_DIR / "idontcar.png")),
        ]
    
    def get_all_cards(self) -> List[Card]:
        return self.all_cards
    
    def find_card_by_id(self, card_id: str) -> Optional[Card]:
        return next((c for c in self.all_cards if c.id == card_id), None)

# ============= UI组件 =============

class Button:
    """按钮组件"""
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 font_size: int = 24, callback: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = get_chinese_font(font_size)
        self.callback = callback
        self.hovered = False
    
    def draw(self, screen: pygame.Surface):
        color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BORDER, self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

class CardWidget:
    """卡牌显示组件"""
    def __init__(self, card: Card, x: int, y: int, width: int = 120, height: int = 180):
        self.card = card
        self.rect = pygame.Rect(x, y, width, height)
        self.font_name = get_chinese_font(20)
        self.font_cost = get_chinese_font(32)
        self.font_desc = get_chinese_font(16)
        self.hovered = False
        self.selected = False
    
    def draw(self, screen: pygame.Surface):
        # 卡牌背景
        border_color = COLOR_CARD_BORDER
        if self.selected:
            border_color = (255, 255, 100)
        elif self.hovered:
            border_color = (150, 150, 200)
        
        # 稀有度边框
        rarity_color = RARITY_COLORS.get(self.card.rarity, COLOR_CARD_BORDER)
        pygame.draw.rect(screen, rarity_color, self.rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BG, self.rect, border_radius=8)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        
        # 尝试加载卡牌图片
        img = self.card.get_image()
        if img:
            img = pygame.transform.scale(img, (self.rect.width - 10, 80))
            screen.blit(img, (self.rect.x + 5, self.rect.y + 5))
        else:
            # 无图片时显示占位符
            placeholder = pygame.Rect(self.rect.x + 5, self.rect.y + 5, 
                                     self.rect.width - 10, 80)
            pygame.draw.rect(screen, (60, 60, 80), placeholder, border_radius=4)
        
        # 费用
        cost_surf = self.font_cost.render(str(self.card.cost), True, COLOR_MANA_BAR)
        screen.blit(cost_surf, (self.rect.x + 10, self.rect.y + 10))
        
        # 卡名
        name_surf = self.font_name.render(self.card.name[:8], True, COLOR_TEXT)
        screen.blit(name_surf, (self.rect.x + 5, self.rect.y + 90))
        
        # 元素标记
        for i, elem in enumerate(self.card.elements[:3]):
            elem_color = ELEMENT_COLORS.get(elem, (150, 150, 150))
            elem_rect = pygame.Rect(self.rect.x + 5 + i * 18, self.rect.y + 110, 15, 15)
            pygame.draw.circle(screen, elem_color, elem_rect.center, 7)
        
        # 描述（简化）
        desc_lines = self.wrap_text(self.card.description, self.rect.width - 10)
        for i, line in enumerate(desc_lines[:3]):
            desc_surf = self.font_desc.render(line, True, COLOR_TEXT_DIM)
            screen.blit(desc_surf, (self.rect.x + 5, self.rect.y + 130 + i * 16))
    
    def wrap_text(self, text: str, max_width: int) -> List[str]:
        """文本换行"""
        words = text
        if len(words) * 8 <= max_width:
            return [words]
        
        lines = []
        chunk_size = max_width // 8
        for i in range(0, len(words), chunk_size):
            lines.append(words[i:i+chunk_size])
        return lines
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.selected = not self.selected
                return True
        return False

class CharacterWidget:
    """角色显示组件"""
    def __init__(self, character: Character, x: int, y: int, 
                 width: int = 150, height: int = 200):
        self.character = character
        self.rect = pygame.Rect(x, y, width, height)
        self.font_name = get_chinese_font(24)
        self.font_stat = get_chinese_font(20)
        self.hovered = False
        self.selected = False
    
    def draw(self, screen: pygame.Surface):
        border_color = (255, 255, 100) if self.selected else COLOR_CARD_BORDER
        if self.hovered and not self.selected:
            border_color = (150, 150, 200)
        
        pygame.draw.rect(screen, COLOR_CARD_BG, self.rect, border_radius=8)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        
        # 尝试加载角色图片
        img = self.character.get_image()
        if img:
            img = pygame.transform.scale(img, (self.rect.width - 10, 100))
            screen.blit(img, (self.rect.x + 5, self.rect.y + 5))
        else:
            placeholder = pygame.Rect(self.rect.x + 5, self.rect.y + 5,
                                     self.rect.width - 10, 100)
            pygame.draw.rect(screen, (80, 60, 60), placeholder, border_radius=4)
        
        # 角色名
        name_surf = self.font_name.render(self.character.name, True, COLOR_TEXT)
        screen.blit(name_surf, (self.rect.x + 10, self.rect.y + 110))
        
        # 生命值
        hp_surf = self.font_stat.render(f"HP: {self.character.health}", True, COLOR_HP_BAR)
        screen.blit(hp_surf, (self.rect.x + 10, self.rect.y + 140))
        
        # 能量
        mp_surf = self.font_stat.render(f"MP: {self.character.energy}", True, COLOR_ENERGY_BAR)
        screen.blit(mp_surf, (self.rect.x + 10, self.rect.y + 165))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.selected = not self.selected
                return True
        return False

# ============= 游戏场景 =============

class Scene:
    """场景基类"""
    def __init__(self, game):
        self.game = game
    
    def handle_event(self, event: pygame.event.Event):
        pass
    
    def update(self, dt: float):
        pass
    
    def draw(self, screen: pygame.Surface):
        pass

class MainMenuScene(Scene):
    """主菜单场景"""
    def __init__(self, game):
        super().__init__(game)
        self.title_font = get_chinese_font(72)
        self.buttons = [
            Button(SCREEN_WIDTH//2 - 150, 200, 300, 50, "查看卡牌",
                   callback=lambda: game.change_scene(GameState.CARD_VIEWER)),
            Button(SCREEN_WIDTH//2 - 150, 270, 300, 50, "查看角色",
                   callback=lambda: game.change_scene(GameState.CHARACTER_VIEWER)),
            Button(SCREEN_WIDTH//2 - 150, 340, 300, 50, "牌组管理",
                   callback=lambda: game.change_scene(GameState.DECK_LIST)),
            Button(SCREEN_WIDTH//2 - 150, 410, 300, 50, "开始对局",
                   callback=lambda: game.change_scene(GameState.BATTLE)),
            Button(SCREEN_WIDTH//2 - 150, 480, 300, 50, "局域网联机",
                   callback=lambda: game.change_scene(GameState.NETWORK_LOBBY)),
            Button(SCREEN_WIDTH//2 - 150, 550, 300, 50, "退出游戏",
                   callback=lambda: game.quit()),
        ]
    
    def handle_event(self, event: pygame.event.Event):
        for button in self.buttons:
            button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        # 标题
        title_surf = self.title_font.render("魔法伤痕", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 120))
        screen.blit(title_surf, title_rect)
        
        # 按钮
        for button in self.buttons:
            button.draw(screen)

class CardViewerScene(Scene):
    """卡牌查看器场景"""
    def __init__(self, game):
        super().__init__(game)
        self.cards = game.card_db.get_all_cards()
        self.card_widgets = []
        self.scroll_offset = 0
        self.create_widgets()
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
    
    def create_widgets(self):
        x, y = 50, 80
        for i, card in enumerate(self.cards):
            if i > 0 and i % 8 == 0:
                y += 200
                x = 50
            widget = CardWidget(card, x, y)
            self.card_widgets.append(widget)
            x += 140
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 30
            self.scroll_offset = max(0, min(self.scroll_offset, 400))
        
        for widget in self.card_widgets:
            widget.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        # 标题
        font = get_chinese_font(48)
        title = font.render("卡牌图鉴", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 25))
        
        # 卡牌
        for widget in self.card_widgets:
            widget.rect.y = widget.rect.y - self.scroll_offset if hasattr(widget, 'original_y') else widget.rect.y
            if not hasattr(widget, 'original_y'):
                widget.original_y = widget.rect.y
            widget.draw(screen)
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))

class CharacterViewerScene(Scene):
    """角色查看器场景"""
    def __init__(self, game):
        super().__init__(game)
        self.characters = game.character_db.get_all_characters()
        self.char_widgets = []
        self.create_widgets()
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
    
    def create_widgets(self):
        x = 150
        for i, char in enumerate(self.characters):
            widget = CharacterWidget(char, x + i * 200, 150)
            self.char_widgets.append(widget)
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        for widget in self.char_widgets:
            widget.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        font = get_chinese_font(48)
        title = font.render("角色图鉴", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 25))
        
        for widget in self.char_widgets:
            widget.draw(screen)
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))

class DeckBuilderScene(Scene):
    """牌组创建器场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font_title = get_chinese_font(32)
        self.font = get_chinese_font(24)
        self.font_small = get_chinese_font(18)
        
        self.deck_name = ""
        self.deck_type = DeckType.STANDARD
        self.selected_characters: List[Character] = []
        self.selected_cards: List[Card] = []  # 存储Card对象及其数量
        self.card_counts: Dict[str, int] = {}  # 卡牌ID -> 数量
        
        self.stage = 0  # 0=名称, 1=类型, 2=角色, 3=卡牌
        self.scroll_offset = 0
        
        # 创建角色和卡牌控件
        self.char_widgets = []
        self.card_widgets = []
        self._create_widgets()
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.DECK_LIST))
        self.next_button = Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 70, 200, 50, "下一步",
                                  callback=self.next_stage)
        self.finish_button = Button(SCREEN_WIDTH - 440, SCREEN_HEIGHT - 70, 200, 50, "完成",
                                    callback=self.finish_deck)
    
    def _create_widgets(self):
        # 创建角色控件
        all_chars = self.game.character_db.get_all_characters()
        x = 100
        for i, char in enumerate(all_chars):
            widget = CharacterWidget(char, x + (i % 4) * 180, 200 + (i // 4) * 220)
            self.char_widgets.append(widget)
        
        # 创建卡牌控件
        all_cards = self.game.card_db.get_all_cards()
        x, y = 50, 180
        for i, card in enumerate(all_cards):
            if i > 0 and i % 8 == 0:
                y += 200
                x = 50
            widget = CardWidget(card, x, y)
            self.card_widgets.append(widget)
            x += 140
    
    def next_stage(self):
        if self.stage == 0:  # 名称输入完成
            if not self.deck_name.strip():
                print("请输入牌组名称")
                return
            self.stage = 1
        elif self.stage == 1:  # 类型选择完成
            self.stage = 2
        elif self.stage == 2:  # 角色选择完成
            if len(self.selected_characters) != 3:
                print("请选择3个角色")
                return
            self.stage = 3
            # 根据牌组类型过滤卡牌
            if self.deck_type == DeckType.STANDARD:
                self.card_widgets = [w for w in self.card_widgets if w.card.rarity != Rarity.FUNNY]
        elif self.stage == 3:  # 卡牌选择完成
            self.finish_deck()
    
    def finish_deck(self):
        total_cards = sum(self.card_counts.values())
        if total_cards < 20:
            print(f"至少需要20张卡牌，当前: {total_cards}")
            return
        
        # 创建牌组
        new_deck = Deck(self.deck_name, self.deck_type)
        for char in self.selected_characters:
            new_deck.add_character(char)
        
        # 根据数量添加卡牌
        for card in self.selected_cards:
            count = self.card_counts.get(card.id, 0)
            for _ in range(count):
                new_deck.add_card(card)
        
        self.game.decks.append(new_deck)
        print(f"牌组 '{self.deck_name}' 创建成功！")
        self.game.change_scene(GameState.DECK_LIST)
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        
        if self.stage == 0:  # 名称输入
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.deck_name = self.deck_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.next_stage()
                elif event.unicode.isprintable():
                    self.deck_name += event.unicode
        
        elif self.stage == 1:  # 类型选择
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                # 标准牌组按钮
                std_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, 300, 200, 60)
                cas_rect = pygame.Rect(SCREEN_WIDTH//2 + 50, 300, 200, 60)
                if std_rect.collidepoint(mouse_pos):
                    self.deck_type = DeckType.STANDARD
                    self.next_stage()
                elif cas_rect.collidepoint(mouse_pos):
                    self.deck_type = DeckType.CASUAL
                    self.next_stage()
        
        elif self.stage == 2:  # 角色选择
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, min(self.scroll_offset, 200))
            
            for widget in self.char_widgets:
                if widget.handle_event(event):
                    if widget.selected and widget.character not in self.selected_characters:
                        if len(self.selected_characters) < 3:
                            self.selected_characters.append(widget.character)
                    elif not widget.selected and widget.character in self.selected_characters:
                        self.selected_characters.remove(widget.character)
        
        elif self.stage == 3:  # 卡牌选择
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, min(self.scroll_offset, 600))
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for widget in self.card_widgets:
                    if widget.rect.collidepoint(mouse_pos):
                        card_id = widget.card.id
                        current_count = self.card_counts.get(card_id, 0)
                        
                        if event.button == 1:  # 左键增加
                            if current_count < 3:
                                self.card_counts[card_id] = current_count + 1
                                if widget.card not in self.selected_cards:
                                    self.selected_cards.append(widget.card)
                                print(f"{widget.card.name}: {self.card_counts[card_id]}/3")
                        elif event.button == 3:  # 右键减少
                            if current_count > 0:
                                self.card_counts[card_id] = current_count - 1
                                if self.card_counts[card_id] == 0:
                                    self.selected_cards.remove(widget.card)
                                print(f"{widget.card.name}: {self.card_counts[card_id]}/3")
        
        if self.stage > 1:
            self.next_button.handle_event(event)
        if self.stage == 3:
            self.finish_button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        if self.stage == 0:  # 名称输入
            title = self.font_title.render("创建牌组 - 输入名称", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            
            # 输入框
            input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 300, 400, 50)
            pygame.draw.rect(screen, COLOR_CARD_BG, input_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, input_rect, 2, border_radius=8)
            
            name_surf = self.font.render(self.deck_name + "|", True, COLOR_TEXT)
            screen.blit(name_surf, (input_rect.x + 10, input_rect.y + 12))
            
            hint = self.font_small.render("按回车继续", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 400))
        
        elif self.stage == 1:  # 类型选择
            title = self.font_title.render("选择牌组类型", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            
            # 标准牌组按钮
            std_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, 300, 200, 60)
            pygame.draw.rect(screen, COLOR_BUTTON, std_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, std_rect, 2, border_radius=8)
            std_text = self.font.render("标准牌组", True, COLOR_TEXT)
            screen.blit(std_text, (std_rect.centerx - std_text.get_width()//2, std_rect.centery - std_text.get_height()//2))
            
            std_desc = self.font_small.render("不能携带趣味卡", True, COLOR_TEXT_DIM)
            screen.blit(std_desc, (std_rect.centerx - std_desc.get_width()//2, std_rect.bottom + 10))
            
            # 休闲牌组按钮
            cas_rect = pygame.Rect(SCREEN_WIDTH//2 + 50, 300, 200, 60)
            pygame.draw.rect(screen, COLOR_BUTTON, cas_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, cas_rect, 2, border_radius=8)
            cas_text = self.font.render("休闲牌组", True, COLOR_TEXT)
            screen.blit(cas_text, (cas_rect.centerx - cas_text.get_width()//2, cas_rect.centery - cas_text.get_height()//2))
            
            cas_desc = self.font_small.render("可携带所有卡牌", True, COLOR_TEXT_DIM)
            screen.blit(cas_desc, (cas_rect.centerx - cas_desc.get_width()//2, cas_rect.bottom + 10))
        
        elif self.stage == 2:  # 角色选择
            title = self.font_title.render(f"选择3个角色 ({len(self.selected_characters)}/3)", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
            
            for widget in self.char_widgets:
                widget.selected = widget.character in self.selected_characters
                widget.rect.y -= self.scroll_offset if not hasattr(widget, 'original_y') else 0
                if not hasattr(widget, 'original_y'):
                    widget.original_y = widget.rect.y
                widget.draw(screen)
            
            self.next_button.draw(screen)
        
        elif self.stage == 3:  # 卡牌选择
            total_cards = sum(self.card_counts.values())
            title = self.font_title.render(f"选择卡牌 ({total_cards}/20)", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
            
            hint = self.font_small.render("左键添加(最多3张) | 右键移除", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 120))
            
            for widget in self.card_widgets:
                widget.selected = widget.card.id in self.card_counts and self.card_counts[widget.card.id] > 0
                widget.rect.y -= self.scroll_offset if not hasattr(widget, 'original_y') else 0
                if not hasattr(widget, 'original_y'):
                    widget.original_y = widget.rect.y
                widget.draw(screen)
                
                # 显示数量
                if widget.card.id in self.card_counts and self.card_counts[widget.card.id] > 0:
                    count = self.card_counts[widget.card.id]
                    count_surf = self.font.render(f"x{count}", True, (255, 255, 100))
                    screen.blit(count_surf, (widget.rect.right - 35, widget.rect.top + 5))
            
            self.next_button.draw(screen)
            self.finish_button.draw(screen)
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))

class DeckListScene(Scene):
    """牌组列表场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font = get_chinese_font(32)
        self.font_small = get_chinese_font(20)
        self.selected_deck_index = -1
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
        self.create_button = Button(SCREEN_WIDTH - 220, 20, 200, 40, "创建牌组",
                                    callback=self.create_deck)
        self.detail_button = Button(SCREEN_WIDTH - 440, 20, 200, 40, "查看详情",
                                    callback=self.view_detail)
        self.export_button = Button(SCREEN_WIDTH - 660, 20, 200, 40, "导出代码",
                                    callback=self.export_code)
        self.import_button = Button(SCREEN_WIDTH - 880, 20, 200, 40, "导入代码",
                                    callback=self.import_code)
    
    def create_deck(self):
        self.game.change_scene(GameState.DECK_BUILDER)
    
    def view_detail(self):
        if self.selected_deck_index >= 0:
            self.game.selected_deck_index = self.selected_deck_index
            self.game.change_scene(GameState.DECK_DETAIL)
    
    def export_code(self):
        if self.selected_deck_index >= 0:
            self.game.selected_deck_index = self.selected_deck_index
            self.game.change_scene(GameState.DECK_EXPORT)
    
    def import_code(self):
        self.game.change_scene(GameState.DECK_IMPORT)
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        self.create_button.handle_event(event)
        self.detail_button.handle_event(event)
        self.export_button.handle_event(event)
        self.import_button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            y = 150
            for i in range(len(self.game.decks)):
                deck_rect = pygame.Rect(100, y, SCREEN_WIDTH - 200, 35)
                if deck_rect.collidepoint(mouse_pos):
                    self.selected_deck_index = i
                    print(f"选中牌组: {self.game.decks[i].name}")
                    return
                y += 40
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        title = self.font.render("我的牌组", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # 显示牌组列表
        y = 150
        for i, deck in enumerate(self.game.decks):
            valid_str = "✓" if deck.is_valid() else "✗"
            text = f"{valid_str} {i+1}. {deck.name} ({len(deck.cards)}张卡牌, {len(deck.characters)}角色)"
            
            # 高亮选中的牌组
            deck_rect = pygame.Rect(100, y, SCREEN_WIDTH - 200, 35)
            if i == self.selected_deck_index:
                pygame.draw.rect(screen, (50, 50, 80), deck_rect, border_radius=4)
            
            deck_surf = self.font_small.render(text, True, COLOR_TEXT if deck.is_valid() else COLOR_TEXT_DIM)
            screen.blit(deck_surf, (105, y + 5))
            y += 40
        
        if not self.game.decks:
            text = self.font.render("还没有牌组，点击右上角创建", True, COLOR_TEXT_DIM)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 300))
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        self.create_button.draw(screen)
        if self.game.decks:
            self.detail_button.draw(screen)
            self.export_button.draw(screen)
        self.import_button.draw(screen)

@dataclass
class CharacterState:
    """角色战斗状态"""
    character: Character
    cur_hp: int
    cur_energy: int
    taunt: bool = False  # 嘲讽状态
    confused: bool = False  # 混乱状态
    
    def take_damage(self, damage: int, is_magic: bool, base_player) -> int:
        """
        接受伤害并返回溢出伤害
        根据规则IV-a和IV-b实现伤害计算
        Args:
            damage: 原始伤害（已考虑技能x2和属性匹配）
            is_magic: 是否为魔法伤害
            base_player: 玩家状态（用于扣除基地血量）
        Returns:
            溢出伤害
        """
        # IV-a 魔法师伤害计算
        if self.character.is_mage():
            if is_magic:
                # 受到魔法伤害，优先扣除魔力
                mana_absorbed = min(self.cur_energy, damage)
                self.cur_energy -= mana_absorbed
                remaining_damage = damage - mana_absorbed
                
                # 扣除生命值
                if remaining_damage > 0:
                    self.cur_hp -= remaining_damage
            else:
                # 受到物理伤害，直接扣除血量
                self.cur_hp -= damage
        else:
            # IV-b 普通人伤害计算：不论何种伤害均扣除血量
            self.cur_hp -= damage
        
        # 计算溢出伤害
        overflow = 0
        if self.cur_hp < 0:
            overflow = -self.cur_hp
            self.cur_hp = 0
        
        return overflow
    
    def can_attack(self) -> bool:
        """检查角色是否可以攻击"""
        return not self.confused and self.cur_hp > 0

@dataclass
class PlayerBattleState:
    """玩家战斗状态"""
    name: str
    base_hp: int = 50  # 基地生命值
    base_mana: int = 30  # 基地魔力
    chars: List[CharacterState] = field(default_factory=list)  # [前场1, 前场2, 后场]
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    discard: List[Card] = field(default_factory=list)
    extra_mana_per_turn: int = 0  # 每回合额外魔力
    
    def get_active_chars(self) -> List[CharacterState]:
        """获取前场角色"""
        return self.chars[:2]
    
    def has_reserve(self) -> bool:
        """是否有后场角色"""
        return len(self.chars) >= 3
    
    def get_reserve_char(self) -> Optional[CharacterState]:
        """获取后场角色"""
        if self.has_reserve():
            return self.chars[2]
        return None
    
    def swap_to_reserve(self, field_idx: int) -> bool:
        """将前场角色替换为后场"""
        if field_idx < 0 or field_idx >= 2:
            return False
        if not self.has_reserve():
            return False
        
        self.chars[field_idx] = self.chars[2]
        self.chars.pop(2)
        return True
    
    def start_turn(self):
        """
        回合开始时的操作
        根据规则V：补充魔力和角色能量，生成专属技能卡牌
        """
        # 恢复基地魔力（每回合+5基础+额外魔力）
        self.base_mana = min(30, self.base_mana + 5 + self.extra_mana_per_turn)
        
        # 恢复角色能量（每个魔法师+5魔力）
        for char_state in self.chars:
            if char_state.character.is_mage():
                max_energy = char_state.character.energy
                char_state.cur_energy = min(max_energy, char_state.cur_energy + 5)
        
        # 根据规则V：将场上角色的主动专属技能作为卡牌加入手牌
        for char_state in self.chars:
            if char_state.character.is_active_ability and char_state.cur_hp > 0:
                # 创建专属技能卡牌
                ability_card = Card(
                    f"ability_{char_state.character.id}",
                    char_state.character.ability,
                    [Element.PHYSICAL] if not char_state.character.is_mage() else char_state.character.elements,
                    0,  # 费用在打出时根据技能描述计算
                    Rarity.MYTHIC,
                    char_state.character.description
                )
                self.hand.append(ability_card)
        
        # 抽1张牌
        if self.deck:
            self.hand.append(self.deck.pop(0))
    
    def pay_cost(self, cost: int, actor: CharacterState) -> bool:
        """
        支付卡牌费用
        根据规则III：魔法师优先消耗自身魔力，不足时消耗基地魔力
        """
        remaining = cost
        
        # 魔法师优先消耗自身魔力
        if actor.character.is_mage():
            from_char = min(actor.cur_energy, remaining)
            actor.cur_energy -= from_char
            remaining -= from_char
        
        # 消耗基地魔力（剩余部分）
        from_base = min(self.base_mana, remaining)
        self.base_mana -= from_base
        remaining -= from_base
        
        # 用生命支付剩余（特殊卡牌效果，部分牌可以更改此规则）
        if remaining > 0:
            actor.cur_hp -= remaining
            if actor.cur_hp <= 0:
                return False
        
        return True
    
    def get_valid_targets(self, attacker: CharacterState, opponent: 'PlayerBattleState') -> List[str]:
        """
        获取有效目标列表
        根据规则V的嘲讽状态：当对手有嘲讽时，只能攻击嘲讽角色
        """
        targets = []
        
        # 检查对手是否有嘲讽状态
        taunt_chars = [char for char in opponent.get_active_chars() if char.taunt and char.cur_hp > 0]
        
        if taunt_chars:
            # 只能攻击有嘲讽的角色
            for i, char in enumerate(opponent.get_active_chars()):
                if char.taunt and char.cur_hp > 0:
                    targets.append(f"t{i}")
        else:
            # 可以攻击任何角色
            for i, char in enumerate(opponent.get_active_chars()):
                if char.cur_hp > 0:
                    targets.append(f"t{i}")
            
            # 可以攻击基地
            targets.append("b")
        
        return targets

class BattleScene(Scene):
    """对战场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font = get_chinese_font(24)
        self.font_small = get_chinese_font(18)
        self.font_tiny = get_chinese_font(16)
        
        # 战斗状态
        self.player1: Optional[PlayerBattleState] = None
        self.player2: Optional[PlayerBattleState] = None
        self.current_turn = 0  # 0=p1, 1=p2
        self.turn_number = 1
        self.selected_hand_index = -1
        self.selected_actor_index = -1
        self.selected_target = None  # "b" or "t0" or "t1"
        self.battle_log = []
        
        # 初始化战斗
        if not self._init_battle():
            self.back_button = Button(20, 20, 100, 40, "返回",
                                      callback=lambda: game.change_scene(GameState.MAIN_MENU))
            self.battle_started = False
        else:
            self.battle_started = True
            self.back_button = Button(20, SCREEN_HEIGHT - 60, 100, 40, "投降",
                                      callback=self.surrender)
            self.end_turn_button = Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60, 200, 40, "结束回合",
                                         callback=self.end_turn)
    
    def _init_battle(self) -> bool:
        """
        初始化战斗
        根据规则II：每位玩家拥有基地50生命值与30魔力，角色满生命值，魔力为上限一半
        根据规则III：对局开始时随机获得3张各自牌堆中的牌作为手牌
        """
        if len(self.game.decks) < 2:
            self.add_log("需要至少2个牌组才能开始对战")
            return False
        
        # 创建玩家状态
        deck1 = self.game.decks[0]
        deck2 = self.game.decks[1] if len(self.game.decks) > 1 else self.game.decks[0]
        
        self.player1 = PlayerBattleState(f"玩家1 ({deck1.name})")
        self.player2 = PlayerBattleState(f"玩家2 ({deck2.name})")
        
        # 根据规则II：每位玩家选择三位不同人物，其中两位作为上场人物，一位作为备场人物
        # 初始化角色（前两位上场，第三位后场）
        for char in deck1.characters[:3]:
            # 角色拥有满生命值
            # 魔法师初始魔力为上限的一半（向上取整），普通人为0
            initial_energy = (char.energy + 1) // 2 if char.is_mage() else 0
            cs = CharacterState(char, char.health, initial_energy)
            self.player1.chars.append(cs)
            self.add_log(f"{cs.character.name} 加入战场 (HP:{cs.cur_hp}, MP:{cs.cur_energy})")
        
        for char in deck2.characters[:3]:
            initial_energy = (char.energy + 1) // 2 if char.is_mage() else 0
            cs = CharacterState(char, char.health, initial_energy)
            self.player2.chars.append(cs)
            self.add_log(f"{cs.character.name} 加入战场 (HP:{cs.cur_hp}, MP:{cs.cur_energy})")
        
        # 初始化牌库并洗牌
        self.player1.deck = deck1.cards.copy()
        self.player2.deck = deck2.cards.copy()
        random.shuffle(self.player1.deck)
        random.shuffle(self.player2.deck)
        
        # 根据规则III：对局开始时随机获得三张各自牌堆中的牌作为手牌
        for _ in range(3):
            if self.player1.deck:
                self.player1.hand.append(self.player1.deck.pop(0))
            if self.player2.deck:
                self.player2.hand.append(self.player2.deck.pop(0))
        
        self.add_log("战斗开始！")
        self.add_log(f"{self.player1.name} vs {self.player2.name}")
        self.add_log(f"双方基地HP:50, MP:30，手牌3张")
        return True
    
    def add_log(self, msg: str):
        """添加战斗日志"""
        self.battle_log.append(msg)
        if len(self.battle_log) > 10:
            self.battle_log.pop(0)
        print(msg)
    
    def surrender(self):
        """投降"""
        current_player = self.player1 if self.current_turn == 0 else self.player2
        self.add_log(f"{current_player.name} 投降了！")
        self.game.change_scene(GameState.MAIN_MENU)
    
    def end_turn(self):
        """
        结束回合
        根据规则V：每回合开始时补充魔力和生成专属技能卡牌
        """
        current_player = self.player1 if self.current_turn == 0 else self.player2
        
        # 切换回合
        self.current_turn = 1 - self.current_turn
        self.turn_number += 1
        self.selected_hand_index = -1
        self.selected_actor_index = -1
        self.selected_target = None
        
        # 下一个玩家开始回合（包含补充魔力、生成专属技能卡牌、抽牌）
        next_player = self.player1 if self.current_turn == 0 else self.player2
        next_player.start_turn()
        
        self.add_log(f"--- 回合 {self.turn_number}: {next_player.name} ---")
        self.add_log(f"{next_player.name} 基地MP:{next_player.base_mana}/30")
        
        # 显示生成的专属技能卡牌
        ability_cards = [card for card in next_player.hand if card.id.startswith("ability_")]
        if ability_cards:
            for card in ability_cards[-len(next_player.chars):]:  # 只显示新生成的
                self.add_log(f"生成专属技能: {card.name}")
        
        # 显示抽牌信息
        self.add_log(f"{next_player.name} 手牌: {len(next_player.hand)}张")
    
    def is_mage(self, char: Character) -> bool:
        """判断是否为法师"""
        return any(e != Element.PHYSICAL for e in char.elements)
    
    def play_card(self):
        """
        打出卡牌
        根据规则III和IV实现完整的出牌逻辑
        """
        if self.selected_hand_index < 0 or self.selected_actor_index < 0 or not self.selected_target:
            self.add_log("请选择手牌、角色和目标")
            return
        
        current_player = self.player1 if self.current_turn == 0 else self.player2
        opponent = self.player2 if self.current_turn == 0 else self.player1
        
        card = current_player.hand[self.selected_hand_index]
        actor = current_player.chars[self.selected_actor_index]
        
        # 检查角色是否可以攻击（混乱状态）
        if not actor.can_attack():
            self.add_log(f"{actor.character.name} 处于混乱状态，无法攻击")
            return
        
        # 根据规则III：检查使用限制
        is_physical = Element.PHYSICAL in card.elements
        actor_is_mage = actor.character.is_mage()
        
        # 非物理属性牌只能由魔法师打出，具有物理属性的牌可以由普通人打出
        if not actor_is_mage and not is_physical:
            self.add_log("普通人只能使用物理属性的牌")
            return
        
        # 计算费用（物理牌无需消耗魔力）
        cost = 0 if is_physical else card.cost
        
        # 检查是否可以支付费用
        if cost > 0:
            available_energy = actor.cur_energy if actor_is_mage else 0
            available_mana = current_player.base_mana
            total_available = available_energy + available_mana
            
            if total_available < cost:
                self.add_log(f"魔力不足，需要{cost}点，可用{total_available}点")
                return
            
            # 支付费用
            if not current_player.pay_cost(cost, actor):
                self.add_log("支付费用失败")
                return
        
        # 根据规则IV：计算伤害
        # 基础伤害计算：技能（x2）-防御力
        base_dmg = max(1, card.cost)
        
        # 根据规则III：魔法师打出牌时，若牌的属性与魔法师属性相同，则将该牌造成的伤害×2
        element_match = any(e in actor.character.elements for e in card.elements)
        final_dmg = base_dmg * (2 if (element_match and actor_is_mage) else 1)
        dmg_is_magic = not is_physical
        
        # 应用目标伤害
        if self.selected_target == "b":
            # 直接攻击基地
            opponent.base_hp -= final_dmg
            self.add_log(f"{actor.character.name} 使用 {card.name} 对基地造成 {final_dmg} 点{('魔法' if dmg_is_magic else '物理')}伤害")
        else:
            target_idx = int(self.selected_target[1])  # 从"t0"或"t1"提取索引
            if target_idx < len(opponent.chars):
                target = opponent.chars[target_idx]
                
                # 使用角色状态的伤害计算方法（已实现规则IV-a和IV-b）
                overflow = target.take_damage(final_dmg, dmg_is_magic, opponent)
                
                self.add_log(f"{actor.character.name} 使用 {card.name} 对 {target.character.name} 造成 {final_dmg} 点{('魔法' if dmg_is_magic else '物理')}伤害")
                
                if overflow > 0:
                    opponent.base_hp -= overflow
                    self.add_log(f"溢出伤害 {overflow} 点打到基地")
                
                # 检查角色死亡和替补
                if target.cur_hp <= 0:
                    self.add_log(f"{target.character.name} 被击败！")
                    
                    # 检查是否有后场角色可以替补
                    if opponent.has_reserve():
                        reserve_char = opponent.get_reserve_char()
                        if reserve_char.cur_hp > 0:
                            opponent.chars[target_idx] = reserve_char
                            opponent.chars.pop(2)
                            self.add_log(f"后场角色 {reserve_char.character.name} 上场替补")
        
        # 移除打出的卡牌到弃牌堆
        current_player.discard.append(current_player.hand.pop(self.selected_hand_index))
        self.selected_hand_index = -1
        self.selected_actor_index = -1
        self.selected_target = None
        
        # 检查胜负
        if self.player1.base_hp <= 0:
            self.add_log(f"{self.player2.name} 获胜！")
            self.battle_started = False
        elif self.player2.base_hp <= 0:
            self.add_log(f"{self.player1.name} 获胜！")
            self.battle_started = False
    
    def handle_event(self, event: pygame.event.Event):
        if not self.battle_started:
            self.back_button.handle_event(event)
            return
        
        self.back_button.handle_event(event)
        self.end_turn_button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            current_player = self.player1 if self.current_turn == 0 else self.player2
            opponent = self.player2 if self.current_turn == 0 else self.player1
            
            # 选择手牌
            hand_y = SCREEN_HEIGHT - 140
            for i, card in enumerate(current_player.hand):
                card_rect = pygame.Rect(50 + i * 130, hand_y, 120, 100)
                if card_rect.collidepoint(mouse_pos):
                    self.selected_hand_index = i
                    self.add_log(f"选择了 {card.name}")
                    return
            
            # 选择己方角色
            for i in range(min(2, len(current_player.chars))):
                char_rect = pygame.Rect(50 + i * 200, SCREEN_HEIGHT - 300, 180, 120)
                if char_rect.collidepoint(mouse_pos):
                    self.selected_actor_index = i
                    self.add_log(f"选择角色 {current_player.chars[i].character.name}")
                    return
            
            # 选择对手目标
            for i in range(min(2, len(opponent.chars))):
                char_rect = pygame.Rect(50 + i * 200, 80, 180, 120)
                if char_rect.collidepoint(mouse_pos):
                    self.selected_target = f"t{i}"
                    self.add_log(f"目标: {opponent.chars[i].character.name}")
                    return
            
            # 选择对手基地
            base_rect = pygame.Rect(SCREEN_WIDTH - 250, 80, 200, 80)
            if base_rect.collidepoint(mouse_pos):
                self.selected_target = "b"
                self.add_log("目标: 对手基地")
                return
            
            # 打出卡牌按钮
            play_rect = pygame.Rect(SCREEN_WIDTH - 440, SCREEN_HEIGHT - 60, 200, 40)
            if play_rect.collidepoint(mouse_pos):
                self.play_card()
                return
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        if not self.battle_started:
            title = self.font.render("无法开始对战，需要至少2个牌组", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
            self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
            return
        
        current_player = self.player1 if self.current_turn == 0 else self.player2
        opponent = self.player2 if self.current_turn == 0 else self.player1
        
        # 绘制对手区域
        self.draw_player_area(screen, opponent, 50, 80, False)
        
        # 绘制己方区域
        self.draw_player_area(screen, current_player, 50, SCREEN_HEIGHT - 300, True)
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(current_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 250
        for log in self.battle_log[-5:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 20
        
        # 绘制回合信息
        turn_text = f"回合 {self.turn_number} - {current_player.name}"
        turn_surf = self.font.render(turn_text, True, COLOR_TEXT)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 20))
        
        # 按钮
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        self.end_turn_button.draw(screen)
        
        # 打出卡牌按钮
        play_button_rect = pygame.Rect(SCREEN_WIDTH - 440, SCREEN_HEIGHT - 60, 200, 40)
        pygame.draw.rect(screen, COLOR_BUTTON, play_button_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BORDER, play_button_rect, 2, border_radius=8)
        play_text = self.font_small.render("打出卡牌", True, COLOR_TEXT)
        screen.blit(play_text, (play_button_rect.centerx - play_text.get_width()//2,
                                play_button_rect.centery - play_text.get_height()//2))
    
    def draw_player_area(self, screen: pygame.Surface, player: PlayerBattleState, 
                        x: int, y: int, is_current: bool):
        """绘制玩家区域"""
        # 玩家信息
        name_surf = self.font.render(player.name, True, COLOR_TEXT)
        screen.blit(name_surf, (x, y - 30))
        
        # 基地生命和魔力
        hp_text = f"基地HP: {player.base_hp}"
        mp_text = f"魔力: {player.base_mana}"
        hp_surf = self.font_small.render(hp_text, True, COLOR_HP_BAR)
        mp_surf = self.font_small.render(mp_text, True, COLOR_MANA_BAR)
        screen.blit(hp_surf, (SCREEN_WIDTH - 230, y))
        screen.blit(mp_surf, (SCREEN_WIDTH - 230, y + 25))
        
        # 绘制前场角色
        for i in range(min(2, len(player.chars))):
            char_state = player.chars[i]
            char_x = x + i * 200
            char_rect = pygame.Rect(char_x, y, 180, 120)
            
            # 高亮选中的角色
            if is_current and i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            elif not is_current and self.selected_target == f"t{i}":
                pygame.draw.rect(screen, (255, 100, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, y + 10))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, y + 40, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, y + 40, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                           True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, y + 42))
            
            # MP条
            mp_ratio = max(0, char_state.cur_energy / char_state.character.energy)
            mp_bar_rect = pygame.Rect(char_x + 10, y + 60, 160, 15)
            pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
            mp_fill_rect = pygame.Rect(char_x + 10, y + 60, int(160 * mp_ratio), 15)
            pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
            mp_text = self.font_tiny.render(f"{char_state.cur_energy}/{char_state.character.energy}",
                                           True, COLOR_TEXT)
            screen.blit(mp_text, (char_x + 15, y + 62))
        
        # 显示后场角色
        if len(player.chars) == 3:
            reserve = player.chars[2]
            res_text = f"后场: {reserve.character.name} ({reserve.cur_hp}HP)"
            res_surf = self.font_tiny.render(res_text, True, COLOR_TEXT_DIM)
            screen.blit(res_surf, (x, y + 130))

class NetworkLobbyScene(Scene):
    """网络大厅场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font_title = get_chinese_font(32)
        self.font = get_chinese_font(24)
        self.font_small = get_chinese_font(18)
        
        self.mode = None  # "host" or "client"
        self.stage = 0  # 0=选择模式, 1=输入参数, 2=连接中, 3=已连接
        
        self.host_address = "127.0.0.1"
        self.port = "4000"
        self.player_name = "玩家"
        self.opponent_name = "对手"
        
        self.input_focus = None  # "host", "port", "name"
        
        # 网络相关
        self.conn_socket = None
        self.recv_thread = None
        self.net_running = False
        self.message_queue = queue.Queue()
        self.send_lock = threading.Lock()
        
        # 战斗相关
        self.local_player: Optional[PlayerBattleState] = None
        self.remote_player: Optional[PlayerBattleState] = None
        self.battle_log = []
        self.my_turn = False
        self.turn_number = 1
        self.selected_hand_index = -1
        self.selected_actor_index = -1
        self.selected_target = None
        self.network_battle_started = False
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=self.disconnect)
        self.host_button = Button(SCREEN_WIDTH//2 - 250, 300, 200, 60, "创建房间",
                                  callback=lambda: self.select_mode("host"))
        self.client_button = Button(SCREEN_WIDTH//2 + 50, 300, 200, 60, "加入房间",
                                    callback=lambda: self.select_mode("client"))
        self.connect_button = Button(SCREEN_WIDTH//2 - 100, 450, 200, 50, "连接",
                                     callback=self.start_connection)
        self.start_battle_button = Button(SCREEN_WIDTH//2 - 100, 500, 200, 50, "开始战斗",
                                          callback=self.start_network_battle)
        self.end_turn_button = Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60, 200, 40, "结束回合",
                                      callback=self.network_end_turn)
        self.play_card_button = Button(SCREEN_WIDTH - 440, SCREEN_HEIGHT - 60, 200, 40, "打出卡牌",
                                       callback=self.network_play_card)
    
    def select_mode(self, mode: str):
        self.mode = mode
        self.stage = 1
    
    def start_connection(self):
        """开始连接"""
        if not self.player_name.strip():
            self.add_log("请输入玩家名称")
            return
        
        self.stage = 2
        self.add_log("正在连接...")
        
        # 启动连接线程
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()
    
    def _connect_thread(self):
        """连接线程"""
        try:
            if self.mode == "host":
                # 创建服务器
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('0.0.0.0', int(self.port)))
                server.listen(1)
                self.add_log(f"等待连接，端口 {self.port}...")
                
                self.conn_socket, addr = server.accept()
                self.add_log(f"已连接: {addr}")
                server.close()
                self.my_turn = True  # 主机先手
            else:
                # 连接到服务器
                self.conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.add_log("尝试连接...")
                self.conn_socket.connect((self.host_address, int(self.port)))
                self.add_log("已连接！")
                self.my_turn = False  # 客户端后手
            
            # 启动接收线程
            self.net_running = True
            self.recv_thread = threading.Thread(target=self._recv_thread, daemon=True)
            self.recv_thread.start()
            
            # 交换名称
            self._send_message(f"NAME;{self.player_name}")
            
            # 等待对方名称
            import time
            timeout = time.time() + 5
            while time.time() < timeout:
                try:
                    msg = self.message_queue.get(timeout=0.1)
                    if msg.startswith("NAME;"):
                        self.opponent_name = msg.split(';', 1)[1]
                        break
                except queue.Empty:
                    continue
            
            self.stage = 3
            self.add_log(f"已连接: {self.opponent_name}")
            
            # 如果是主机，发送牌组信息并准备战斗
            if self.mode == "host":
                if len(self.game.decks) > 0:
                    deck = self.game.decks[0]  # 使用第一个牌组
                    deck_info = f"{deck.name};{deck.deck_code}"
                    self._send_message(f"DECK;{deck_info}")
                    self.add_log("已发送牌组信息")
            
        except Exception as e:
            self.add_log(f"连接失败: {e}")
            self.stage = 1
    
    def _recv_thread(self):
        """接收线程"""
        buffer = ""
        while self.net_running:
            try:
                data = self.conn_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        self.message_queue.put(line)
            except:
                break
        self.net_running = False
    
    def _send_message(self, msg: str):
        """发送消息"""
        if self.conn_socket:
            with self.send_lock:
                try:
                    self.conn_socket.send((msg + '\n').encode('utf-8'))
                except:
                    pass
    
    def add_log(self, msg: str):
        """添加日志"""
        self.battle_log.append(msg)
        if len(self.battle_log) > 10:
            self.battle_log.pop(0)
        print(msg)
    
    def disconnect(self):
        """断开连接"""
        self.net_running = False
        if self.conn_socket:
            try:
                self.conn_socket.close()
            except:
                pass
        self.game.change_scene(GameState.MAIN_MENU)
    
    def send_play(self, card_id: str, actor_idx: int, target: str):
        """发送出牌消息"""
        self._send_message(f"PLAY;{card_id};{actor_idx};{target}")
    
    def send_emoji(self, emoji: str):
        """发送表情"""
        self._send_message(f"EMOJI;{emoji}")
    
    def start_network_battle(self):
        """开始网络战斗"""
        if len(self.game.decks) == 0:
            self.add_log("请先创建牌组")
            return
        
        # 创建本地玩家状态
        deck = self.game.decks[0]  # 使用第一个牌组
        self.local_player = PlayerBattleState(self.player_name)
        
        # 初始化角色
        for char in deck.characters[:3]:
            initial_energy = (char.energy + 1) // 2 if char.is_mage() else 0
            cs = CharacterState(char, char.health, initial_energy)
            self.local_player.chars.append(cs)
        
        # 初始化牌库
        self.local_player.deck = deck.cards.copy()
        random.shuffle(self.local_player.deck)
        
        # 抽初始手牌
        for _ in range(3):
            if self.local_player.deck:
                self.local_player.hand.append(self.local_player.deck.pop(0))
        
        # 标记战斗开始
        self.network_battle_started = True
        self.stage = 4  # 进入战斗阶段
        
        self.add_log("网络战斗开始！")
        self.add_log(f"你使用牌组: {deck.name}")
        
        # 通知对方开始战斗
        self._send_message("STARTBATTLE")
        
        # 如果是主机，开始第一回合
        if self.my_turn:
            self.local_player.start_turn()
            self.add_log("你的回合开始")
    
    def network_end_turn(self):
        """网络战斗结束回合"""
        if not self.network_battle_started or not self.my_turn:
            return
        
        self._send_message("ENDTURN")
        self.my_turn = False
        self.add_log("已结束回合，等待对手...")
    
    def network_play_card(self):
        """网络战斗出牌"""
        if not self.network_battle_started or not self.my_turn:
            return
        
        if self.selected_hand_index < 0 or self.selected_actor_index < 0 or not self.selected_target:
            self.add_log("请选择手牌、角色和目标")
            return
        
        card = self.local_player.hand[self.selected_hand_index]
        actor = self.local_player.chars[self.selected_actor_index]
        
        # 检查使用限制
        is_physical = Element.PHYSICAL in card.elements
        actor_is_mage = actor.character.is_mage()
        
        if not actor_is_mage and not is_physical:
            self.add_log("普通人只能使用物理属性的牌")
            return
        
        # 计算费用
        cost = 0 if is_physical else card.cost
        total_available = (actor.cur_energy if actor_is_mage else 0) + self.local_player.base_mana
        
        if total_available < cost:
            self.add_log(f"魔力不足，需要{cost}点，可用{total_available}点")
            return
        
        # 发送出牌消息
        self._send_message(f"PLAY;{card.id};{self.selected_actor_index};{self.selected_target}")
        
        # 本地执行出牌逻辑
        self.execute_play_card(self.selected_hand_index, self.selected_actor_index, self.selected_target)
        
        self.add_log(f"使用 {card.name}")
        
        # 清除选择
        self.selected_hand_index = -1
        self.selected_actor_index = -1
        self.selected_target = None
    
    def execute_play_card(self, hand_idx: int, actor_idx: int, target: str):
        """执行出牌逻辑"""
        if not self.local_player:
            return
        
        card = self.local_player.hand[hand_idx]
        actor = self.local_player.chars[actor_idx]
        
        # 支付费用
        is_physical = Element.PHYSICAL in card.elements
        cost = 0 if is_physical else card.cost
        
        if cost > 0:
            self.local_player.pay_cost(cost, actor)
        
        # 计算伤害
        base_dmg = max(1, card.cost)
        element_match = any(e in actor.character.elements for e in card.elements)
        final_dmg = base_dmg * (2 if (element_match and actor.character.is_mage) else 1)
        
        # 这里需要对方的状态来应用伤害
        # 暂时只记录日志
        dmg_is_magic = not is_physical
        self.add_log(f"造成 {final_dmg} 点{('魔法' if dmg_is_magic else '物理')}伤害")
        
        # 移除卡牌
        self.local_player.discard.append(self.local_player.hand.pop(hand_idx))
    
    def end_turn(self):
        """结束回合"""
        self._send_message("ENDTURN")
        self.my_turn = False
        self.add_log("已结束回合")
    
    def process_messages(self):
        """处理接收到的消息"""
        while not self.message_queue.empty():
            try:
                msg = self.message_queue.get_nowait()
                self.handle_message(msg)
            except queue.Empty:
                break
    
    def handle_message(self, msg: str):
        """处理网络消息，实现局域网对战"""
        if msg.startswith("NAME;"):
            self.opponent_name = msg.split(';', 1)[1]
            self.add_log(f"对手 {self.opponent_name} 已连接")
        elif msg.startswith("EMOJI;"):
            emoji = msg.split(';', 1)[1]
            self.add_log(f"[对方表情] {emoji}")
        elif msg.startswith("PLAY;"):
            parts = msg.split(';')
            if len(parts) >= 4:
                card_id = parts[1]
                actor_idx = int(parts[2])
                target = parts[3]
                self.add_log(f"对方使用卡牌: {card_id} -> {target}")
                # 实现对方出牌的逻辑同步
                self.handle_opponent_play(card_id, actor_idx, target)
        elif msg.startswith("DECK;"):
            # 接收对方的牌组信息
            deck_data = msg.split(';', 1)[1]
            self.add_log(f"收到对方牌组: {deck_data}")
            # 如果是客户端，回应发送自己的牌组信息
            if self.mode == "client" and len(self.game.decks) > 0:
                deck = self.game.decks[0]
                deck_info = f"{deck.name};{deck.deck_code}"
                self._send_message(f"DECK;{deck_info}")
                self.add_log("已发送我的牌组信息")
        elif msg.startswith("STARTBATTLE"):
            # 开始战斗
            self.add_log("对手开始战斗！")
            self.prepare_opponent_battle()
            self.stage = 4  # 进入战斗阶段
        elif msg == "ENDTURN":
            self.my_turn = True
            self.add_log("对方结束回合，轮到你了")
            if self.local_player:
                self.local_player.start_turn()
                self.add_log("你的回合开始")
        elif msg.startswith("ABILITY;"):
            # 使用专属技能
            parts = msg.split(';')
            if len(parts) >= 3:
                char_id = parts[1]
                target = parts[2]
                self.add_log(f"对方使用专属技能: {char_id} -> {target}")
        elif msg.startswith("STATUS;"):
            # 状态同步
            status_data = msg.split(';', 1)[1]
            self.add_log(f"状态更新: {status_data}")
    
    def handle_opponent_play(self, card_id: str, actor_idx: int, target: str):
        """处理对手出牌"""
        # 这里需要实现对手出牌的完整逻辑
        # 包括验证、费用支付、伤害计算等
        self.add_log(f"对手出牌: 卡牌{card_id}，角色{actor_idx}，目标{target}")
        
        # 创建一个临时的对手玩家状态来模拟出牌
        if not self.remote_player:
            return
        
        # 根据card_id找到卡牌（需要从对方的牌组中查找）
        # 这里简化处理，只记录日志
        self.add_log("正在处理对手出牌...")
    
    def prepare_opponent_battle(self):
        """准备对手战斗状态"""
        # 创建远程玩家状态（简化版本）
        self.remote_player = PlayerBattleState(self.opponent_name)
        
        # 这里应该解析对方的牌组信息并初始化角色
        # 暂时使用默认设置
        self.add_log("准备对手战斗状态完成")
        
        if not self.local_player:
            # 如果本地玩家还没准备，先准备
            self.start_network_battle()
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        
        if self.stage == 0:  # 选择模式
            self.host_button.handle_event(event)
            self.client_button.handle_event(event)
        
        elif self.stage == 1:  # 输入参数
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                # 检查输入框点击
                if self.mode == "client":
                    host_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 250, 300, 40)
                    if host_rect.collidepoint(mouse_pos):
                        self.input_focus = "host"
                        return
                
                port_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 310, 300, 40)
                if port_rect.collidepoint(mouse_pos):
                    self.input_focus = "port"
                    return
                
                name_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 370, 300, 40)
                if name_rect.collidepoint(mouse_pos):
                    self.input_focus = "name"
                    return
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if self.input_focus == "host":
                        self.host_address = self.host_address[:-1]
                    elif self.input_focus == "port":
                        self.port = self.port[:-1]
                    elif self.input_focus == "name":
                        self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.start_connection()
                elif event.unicode.isprintable():
                    if self.input_focus == "host":
                        self.host_address += event.unicode
                    elif self.input_focus == "port":
                        self.port += event.unicode
                    elif self.input_focus == "name":
                        self.player_name += event.unicode
            
            self.connect_button.handle_event(event)
        
        elif self.stage == 3:  # 已连接，等待开始战斗
            self.start_battle_button.handle_event(event)
            if event.type == pygame.KEYDOWN:
                # 快捷键发送表情
                if event.key == pygame.K_1:
                    self.send_emoji("😀")
                elif event.key == pygame.K_2:
                    self.send_emoji("😎")
                elif event.key == pygame.K_3:
                    self.send_emoji("😢")
        
        elif self.stage == 4:  # 网络战斗进行中
            self.handle_network_battle_event(event)
    
    def handle_network_battle_event(self, event: pygame.event.Event):
        """处理网络战斗事件"""
        if not self.my_turn or not self.network_battle_started:
            # 只允许表情和返回
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.send_emoji("😀")
                elif event.key == pygame.K_2:
                    self.send_emoji("😎")
                elif event.key == pygame.K_3:
                    self.send_emoji("😢")
            self.back_button.handle_event(event)
            return
        
        # 我的回合，允许所有操作
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # 选择手牌
            hand_y = SCREEN_HEIGHT - 140
            for i, card in enumerate(self.local_player.hand):
                card_rect = pygame.Rect(50 + i * 130, hand_y, 120, 100)
                if card_rect.collidepoint(mouse_pos):
                    self.selected_hand_index = i
                    self.add_log(f"选择了 {card.name}")
                    return
            
            # 选择己方角色
            my_y = SCREEN_HEIGHT - 300
            for i in range(min(2, len(self.local_player.chars))):
                char_rect = pygame.Rect(50 + i * 200, my_y + 60, 180, 120)
                if char_rect.collidepoint(mouse_pos):
                    self.selected_actor_index = i
                    self.add_log(f"选择角色 {self.local_player.chars[i].character.name}")
                    return
            
            # 选择对手基地（简化处理）
            base_rect = pygame.Rect(SCREEN_WIDTH - 250, 100, 200, 80)
            if base_rect.collidepoint(mouse_pos):
                self.selected_target = "b"
                self.add_log("目标: 对手基地")
                return
            
            # 选择对手角色（简化处理，选择第一个角色）
            if 100 < mouse_pos[1] < 200 and 250 < mouse_pos[0] < 430:
                self.selected_target = "t0"
                self.add_log("目标: 对手角色")
                return
        
        elif event.type == pygame.KEYDOWN:
            # 快捷键
            if event.key == pygame.K_1:
                self.send_emoji("😀")
            elif event.key == pygame.K_2:
                self.send_emoji("😎")
            elif event.key == pygame.K_3:
                self.send_emoji("😢")
        
        # 通用按钮处理
        self.back_button.handle_event(event)
        self.end_turn_button.handle_event(event)
        self.play_card_button.handle_event(event)
    
    def update(self, dt: float):
        if self.stage >= 3:  # 在连接后和战斗中都要处理消息
            self.process_messages()
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        if self.stage == 0:  # 选择模式
            title = self.font_title.render("局域网联机", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            
            self.host_button.draw(screen)
            self.client_button.draw(screen)
            
            hint = self.font_small.render("创建房间将等待其他玩家加入", True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 400))
        
        elif self.stage == 1:  # 输入参数
            title_text = "创建房间" if self.mode == "host" else "加入房间"
            title = self.font_title.render(title_text, True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            
            # 主机地址输入（仅客户端）
            y = 250
            if self.mode == "client":
                label = self.font.render("主机地址:", True, COLOR_TEXT)
                screen.blit(label, (SCREEN_WIDTH//2 - 250, y))
                
                host_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, y, 300, 40)
                color = COLOR_BUTTON_HOVER if self.input_focus == "host" else COLOR_BUTTON
                pygame.draw.rect(screen, color, host_rect, border_radius=8)
                pygame.draw.rect(screen, COLOR_CARD_BORDER, host_rect, 2, border_radius=8)
                
                host_surf = self.font_small.render(self.host_address, True, COLOR_TEXT)
                screen.blit(host_surf, (host_rect.x + 10, host_rect.y + 10))
                y += 60
            
            # 端口输入
            label = self.font.render("端口:", True, COLOR_TEXT)
            screen.blit(label, (SCREEN_WIDTH//2 - 250, y))
            
            port_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, y, 300, 40)
            color = COLOR_BUTTON_HOVER if self.input_focus == "port" else COLOR_BUTTON
            pygame.draw.rect(screen, color, port_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, port_rect, 2, border_radius=8)
            
            port_surf = self.font_small.render(self.port, True, COLOR_TEXT)
            screen.blit(port_surf, (port_rect.x + 10, port_rect.y + 10))
            y += 60
            
            # 玩家名称输入
            label = self.font.render("玩家名称:", True, COLOR_TEXT)
            screen.blit(label, (SCREEN_WIDTH//2 - 250, y))
            
            name_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, y, 300, 40)
            color = COLOR_BUTTON_HOVER if self.input_focus == "name" else COLOR_BUTTON
            pygame.draw.rect(screen, color, name_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, name_rect, 2, border_radius=8)
            
            name_surf = self.font_small.render(self.player_name, True, COLOR_TEXT)
            screen.blit(name_surf, (name_rect.x + 10, name_rect.y + 10))
            
            self.connect_button.draw(screen)
        
        elif self.stage == 2:  # 连接中
            title = self.font_title.render("连接中...", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
        
        elif self.stage == 3:  # 已连接，等待开始战斗
            # 显示对战信息
            title = self.font_title.render(f"对战: {self.player_name} vs {self.opponent_name}", 
                                          True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
            
            # 显示连接状态
            turn_text = "等待开始战斗..."
            turn_surf = self.font.render(turn_text, True, COLOR_TEXT_DIM)
            screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 120))
            
            # 显示日志
            log_y = 200
            for log in self.battle_log[-10:]:
                log_surf = self.font_small.render(log, True, COLOR_TEXT_DIM)
                screen.blit(log_surf, (100, log_y))
                log_y += 25
            
            # 显示开始战斗按钮（如果是主机）
            if self.mode == "host":
                self.start_battle_button.draw(screen)
                hint = self.font_small.render("点击按钮开始战斗 | 1-3键发送表情", 
                                             True, COLOR_TEXT_DIM)
                screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
            else:
                hint = self.font_small.render("等待主机开始战斗 | 1-3键发送表情", 
                                             True, COLOR_TEXT_DIM)
                screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        
        elif self.stage == 4:  # 网络战斗进行中
            self.draw_network_battle(screen)
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))

class DeckDetailScene(Scene):
    """牌组详情场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font_title = get_chinese_font(32)
        self.font = get_chinese_font(24)
        self.font_small = get_chinese_font(18)
        self.scroll_offset = 0
        
        self.deck = game.decks[game.selected_deck_index] if 0 <= game.selected_deck_index < len(game.decks) else None
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.DECK_LIST))
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 30
            self.scroll_offset = max(0, min(self.scroll_offset, 500))
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        if not self.deck:
            text = self.font.render("未找到牌组", True, COLOR_TEXT)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 300))
            self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
            return
        
        y = 80 - self.scroll_offset
        
        # 标题
        title = self.font_title.render(f"牌组详情: {self.deck.name}", True, COLOR_TEXT)
        screen.blit(title, (100, y))
        y += 50
        
        # 基本信息
        type_text = "标准牌组" if self.deck.deck_type == DeckType.STANDARD else "休闲牌组"
        info1 = self.font.render(f"类型: {type_text}", True, COLOR_TEXT)
        screen.blit(info1, (100, y))
        y += 35
        
        info2 = self.font.render(f"卡牌数量: {len(self.deck.cards)}/20", True, COLOR_TEXT)
        screen.blit(info2, (100, y))
        y += 35
        
        info3 = self.font.render(f"角色数量: {len(self.deck.characters)}/3", True, COLOR_TEXT)
        screen.blit(info3, (100, y))
        y += 45
        
        # 元素分布
        elem_dist = defaultdict(int)
        for card in self.deck.cards:
            for elem in card.elements:
                elem_dist[elem] += 1
        
        if elem_dist:
            elem_title = self.font.render("元素分布:", True, COLOR_TEXT)
            screen.blit(elem_title, (100, y))
            y += 30
            
            for elem, count in elem_dist.items():
                elem_text = self.font_small.render(f"  {element_to_string(elem)}: {count} 张", True, COLOR_TEXT_DIM)
                screen.blit(elem_text, (120, y))
                y += 25
        
        y += 15
        
        # 角色列表
        char_title = self.font.render("角色列表:", True, COLOR_TEXT)
        screen.blit(char_title, (100, y))
        y += 30
        
        for char in self.deck.characters:
            char_text = self.font_small.render(
                f"  • {char.name} (HP:{char.health}, MP:{char.energy})", 
                True, COLOR_TEXT_DIM
            )
            screen.blit(char_text, (120, y))
            y += 25
        
        y += 15
        
        # 卡牌列表（统计数量）
        card_title = self.font.render("卡牌列表:", True, COLOR_TEXT)
        screen.blit(card_title, (100, y))
        y += 30
        
        card_counts = defaultdict(int)
        for card in self.deck.cards:
            card_counts[card.id] += 1
        
        # 按卡牌分组显示
        seen_cards = set()
        for card in self.deck.cards:
            if card.id not in seen_cards:
                seen_cards.add(card.id)
                count = card_counts[card.id]
                elements_str = ' '.join(element_to_string(e) for e in card.elements)
                card_text = self.font_small.render(
                    f"  • {card.name} x{count} (费用:{card.cost}, 元素:{elements_str})",
                    True, COLOR_TEXT_DIM
                )
                screen.blit(card_text, (120, y))
                y += 25
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))

class DeckExportScene(Scene):
    """牌组导出场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font_title = get_chinese_font(32)
        self.font = get_chinese_font(20)
        self.font_small = get_chinese_font(18)
        
        self.deck = game.decks[game.selected_deck_index] if 0 <= game.selected_deck_index < len(game.decks) else None
        self.deck_code = self.deck.deck_code if self.deck else ""
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.DECK_LIST))
        self.copy_button = Button(SCREEN_WIDTH//2 - 100, 450, 200, 50, "复制到剪贴板",
                                  callback=self.copy_to_clipboard)
    
    def copy_to_clipboard(self):
        try:
            import pyperclip
            pyperclip.copy(self.deck_code)
            print("牌组代码已复制到剪贴板")
        except ImportError:
            print("未安装 pyperclip，请手动复制代码")
        except:
            print("复制失败，请手动复制代码")
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        self.copy_button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        if not self.deck:
            text = self.font.render("未找到牌组", True, COLOR_TEXT)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 300))
            self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
            return
        
        # 标题
        title = self.font_title.render(f"导出牌组: {self.deck.name}", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # 说明
        hint = self.font_small.render("请保存以下代码，可用于导入牌组", True, COLOR_TEXT_DIM)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 180))
        
        # 显示代码（换行显示）
        code_rect = pygame.Rect(100, 240, SCREEN_WIDTH - 200, 150)
        pygame.draw.rect(screen, COLOR_CARD_BG, code_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BORDER, code_rect, 2, border_radius=8)
        
        # 分行显示代码
        chunk_size = 60
        y = 250
        for i in range(0, len(self.deck_code), chunk_size):
            chunk = self.deck_code[i:i+chunk_size]
            code_surf = self.font_small.render(chunk, True, COLOR_TEXT)
            screen.blit(code_surf, (110, y))
            y += 22
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        self.copy_button.draw(screen)

class DeckImportScene(Scene):
    """牌组导入场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font_title = get_chinese_font(32)
        self.font = get_chinese_font(24)
        self.font_small = get_chinese_font(18)
        
        self.deck_code = ""
        self.deck_name = ""
        self.input_focus = "code"  # "code" or "name"
        self.import_success = False
        self.error_message = ""
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.DECK_LIST))
        self.import_button = Button(SCREEN_WIDTH//2 - 100, 520, 200, 50, "导入",
                                    callback=self.do_import)
    
    def do_import(self):
        if not self.deck_code.strip():
            self.error_message = "请输入牌组代码"
            return
        
        if not self.deck_name.strip():
            self.error_message = "请输入牌组名称"
            return
        
        # 验证代码
        data, valid = decode_deck_code(self.deck_code.strip())
        if not valid:
            self.error_message = "无效的牌组代码"
            return
        
        # 创建新牌组并导入
        new_deck = Deck(self.deck_name)
        success = new_deck.import_from_code(
            self.deck_code.strip(),
            self.game.card_db.get_all_cards(),
            self.game.character_db.get_all_characters()
        )
        
        if success:
            self.game.decks.append(new_deck)
            self.import_success = True
            self.error_message = f"成功导入牌组: {self.deck_name}"
            print(f"成功导入牌组: {self.deck_name}")
        else:
            self.error_message = "导入失败，请检查代码"
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        self.import_button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            code_rect = pygame.Rect(SCREEN_WIDTH//2 - 300, 220, 600, 120)
            name_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 380, 400, 50)
            
            if code_rect.collidepoint(mouse_pos):
                self.input_focus = "code"
            elif name_rect.collidepoint(mouse_pos):
                self.input_focus = "name"
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.input_focus == "code":
                    self.deck_code = self.deck_code[:-1]
                elif self.input_focus == "name":
                    self.deck_name = self.deck_name[:-1]
            elif event.key == pygame.K_RETURN:
                self.do_import()
            elif event.unicode.isprintable():
                if self.input_focus == "code":
                    self.deck_code += event.unicode
                elif self.input_focus == "name":
                    self.deck_name += event.unicode
            
            # 清除错误消息
            if not self.import_success:
                self.error_message = ""
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        # 标题
        title = self.font_title.render("导入牌组", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # 代码输入
        code_label = self.font.render("牌组代码:", True, COLOR_TEXT)
        screen.blit(code_label, (SCREEN_WIDTH//2 - 300, 180))
        
        code_rect = pygame.Rect(SCREEN_WIDTH//2 - 300, 220, 600, 120)
        color = COLOR_BUTTON_HOVER if self.input_focus == "code" else COLOR_BUTTON
        pygame.draw.rect(screen, color, code_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BORDER, code_rect, 2, border_radius=8)
        
        # 分行显示输入的代码
        chunk_size = 50
        y = 230
        for i in range(0, len(self.deck_code), chunk_size):
            chunk = self.deck_code[i:i+chunk_size]
            code_surf = self.font_small.render(chunk, True, COLOR_TEXT)
            screen.blit(code_surf, (SCREEN_WIDTH//2 - 290, y))
            y += 22
        
        # 名称输入
        name_label = self.font.render("牌组名称:", True, COLOR_TEXT)
        screen.blit(name_label, (SCREEN_WIDTH//2 - 200, 350))
        
        name_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 380, 400, 50)
        color = COLOR_BUTTON_HOVER if self.input_focus == "name" else COLOR_BUTTON
        pygame.draw.rect(screen, color, name_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_CARD_BORDER, name_rect, 2, border_radius=8)
        
        name_surf = self.font.render(self.deck_name, True, COLOR_TEXT)
        screen.blit(name_surf, (name_rect.x + 10, name_rect.y + 12))
        
        # 错误/成功消息
        if self.error_message:
            msg_color = (100, 255, 100) if self.import_success else (255, 100, 100)
            msg_surf = self.font_small.render(self.error_message, True, msg_color)
            screen.blit(msg_surf, (SCREEN_WIDTH//2 - msg_surf.get_width()//2, 460))
        
        self.back_button.draw(screen)
    
    def draw_network_battle(self, screen: pygame.Surface):
        """绘制网络战斗界面"""
        if not self.local_player:
            return
        
        # 显示对战信息
        title = self.font_title.render(f"战斗: {self.player_name} vs {self.opponent_name}", 
                                      True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 20))
        
        # 显示回合状态
        turn_text = f"回合 {self.turn_number} - {'你的回合' if self.my_turn else '对方回合'}"
        turn_color = (100, 255, 100) if self.my_turn else (255, 100, 100)
        turn_surf = self.font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (SCREEN_WIDTH//2 - turn_surf.get_width()//2, 60))
        
        # 绘制对手区域（简化显示）
        if self.remote_player:
            opponent_y = 100
            opp_name_surf = self.font.render(f"{self.opponent_name}", True, COLOR_TEXT)
            screen.blit(opp_name_surf, (50, opponent_y))
            
            opp_base_text = f"基地HP: {self.remote_player.base_hp} MP: {self.remote_player.base_mana}"
            opp_base_surf = self.font_small.render(opp_base_text, True, COLOR_TEXT_DIM)
            screen.blit(opp_base_surf, (50, opponent_y + 30))
        
        # 绘制己方区域
        my_y = SCREEN_HEIGHT - 300
        my_name_surf = self.font.render(f"{self.player_name}", True, COLOR_TEXT)
        screen.blit(my_name_surf, (50, my_y))
        
        # 基地状态
        base_text = f"基地HP: {self.local_player.base_hp} MP: {self.local_player.base_mana}"
        base_surf = self.font_small.render(base_text, True, COLOR_TEXT)
        screen.blit(base_surf, (50, my_y + 30))
        
        # 绘制己方角色
        for i, char_state in enumerate(self.local_player.chars[:2]):
            char_x = 50 + i * 200
            char_rect = pygame.Rect(char_x, my_y + 60, 180, 120)
            
            # 高亮选中的角色
            if i == self.selected_actor_index:
                pygame.draw.rect(screen, (100, 255, 100), char_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, char_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, char_rect, 2, border_radius=8)
            
            # 角色名
            name = self.font_small.render(char_state.character.name, True, COLOR_TEXT)
            screen.blit(name, (char_x + 10, my_y + 70))
            
            # HP条
            hp_ratio = max(0, char_state.cur_hp / char_state.character.health)
            hp_bar_rect = pygame.Rect(char_x + 10, my_y + 100, 160, 15)
            pygame.draw.rect(screen, (50, 50, 50), hp_bar_rect)
            hp_fill_rect = pygame.Rect(char_x + 10, my_y + 100, int(160 * hp_ratio), 15)
            pygame.draw.rect(screen, COLOR_HP_BAR, hp_fill_rect)
            hp_text = self.font_tiny.render(f"{char_state.cur_hp}/{char_state.character.health}", 
                                          True, COLOR_TEXT)
            screen.blit(hp_text, (char_x + 15, my_y + 102))
            
            # MP条
            if char_state.character.is_mage():
                mp_ratio = max(0, char_state.cur_energy / char_state.character.energy) if char_state.character.energy > 0 else 0
                mp_bar_rect = pygame.Rect(char_x + 10, my_y + 120, 160, 15)
                pygame.draw.rect(screen, (30, 30, 30), mp_bar_rect)
                mp_fill_rect = pygame.Rect(char_x + 10, my_y + 120, int(160 * mp_ratio), 15)
                pygame.draw.rect(screen, COLOR_ENERGY_BAR, mp_fill_rect)
                mp_text = self.font_tiny.render(f"MP:{char_state.cur_energy}/{char_state.character.energy}",
                                              True, COLOR_TEXT)
                screen.blit(mp_text, (char_x + 15, my_y + 122))
        
        # 绘制手牌
        hand_y = SCREEN_HEIGHT - 140
        for i, card in enumerate(self.local_player.hand):
            x = 50 + i * 130
            card_rect = pygame.Rect(x, hand_y, 120, 100)
            
            # 高亮选中的牌
            if i == self.selected_hand_index:
                pygame.draw.rect(screen, (255, 255, 100), card_rect.inflate(4, 4), border_radius=8)
            
            pygame.draw.rect(screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_CARD_BORDER, card_rect, 2, border_radius=8)
            
            name_surf = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            cost_surf = self.font_small.render(str(card.cost), True, COLOR_MANA_BAR)
            screen.blit(name_surf, (x + 5, hand_y + 5))
            screen.blit(cost_surf, (x + 5, hand_y + 25))
        
        # 绘制战斗日志
        log_y = 200
        for log in self.battle_log[-8:]:
            log_surf = self.font_tiny.render(log, True, COLOR_TEXT_DIM)
            screen.blit(log_surf, (SCREEN_WIDTH - 450, log_y))
            log_y += 18
        
        # 按钮
        self.back_button.draw(screen)
        if self.my_turn and self.network_battle_started:
            self.end_turn_button.draw(screen)
            self.play_card_button.draw(screen)
            
            hint = self.font_small.render("选择手牌、角色和目标后点击出牌 | 1-3键发送表情", 
                                         True, COLOR_TEXT_DIM)
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 100))
        self.import_button.draw(screen)

# ============= 主游戏类 =============

class Game:
    """主游戏类"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("魔法伤痕 - MagicWound")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 数据库
        self.card_db = CardDatabase()
        self.character_db = CharacterDatabase()
        self.decks: List[Deck] = []
        
        # 选中的牌组索引（用于详情/导出）
        self.selected_deck_index = -1
        
        # 场景管理
        self.current_scene: Optional[Scene] = None
        self.change_scene(GameState.MAIN_MENU)
    
    def change_scene(self, state: GameState):
        """切换场景"""
        scene_map = {
            GameState.MAIN_MENU: MainMenuScene,
            GameState.CARD_VIEWER: CardViewerScene,
            GameState.CHARACTER_VIEWER: CharacterViewerScene,
            GameState.DECK_LIST: DeckListScene,
            GameState.DECK_BUILDER: DeckBuilderScene,
            GameState.BATTLE: BattleScene,
            GameState.NETWORK_LOBBY: NetworkLobbyScene,
            GameState.DECK_DETAIL: DeckDetailScene,
            GameState.DECK_EXPORT: DeckExportScene,
            GameState.DECK_IMPORT: DeckImportScene,
        }
        
        scene_class = scene_map.get(state)
        if scene_class:
            self.current_scene = scene_class(self)
    
    def quit(self):
        """退出游戏"""
        self.running = False
    
    def run(self):
        """主循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if isinstance(self.current_scene, MainMenuScene):
                            self.running = False
                        else:
                            self.change_scene(GameState.MAIN_MENU)
                
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            # 更新
            if self.current_scene:
                self.current_scene.update(dt)
            
            # 渲染
            if self.current_scene:
                self.current_scene.draw(self.screen)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

# ============= 主程序入口 =============

def main():
    """主函数"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"程序错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())

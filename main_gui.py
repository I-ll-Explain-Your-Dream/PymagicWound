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
    energy: int
    ability: str
    description: str
    passive_ability: str
    passive_description: str
    image_path: Optional[str] = None
    
    def has_element(self, element: Element) -> bool:
        return element in self.elements
    
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
            Character("xxmlt", "金天", [Element.WATER], 25, 15,
                     "治疗", "消耗5点魔力，指定一个友方目标获得5点生命值。",
                     "死生", "每局对战限一次，当我方人物受到致命伤时，不使其下场,而是使生命值降为1。",
                     str(CHARACTERS_DIR / "jintian.png")),
            Character("neko", "三金", [Element.WIND], 20, 25,
                     "吹飞", "消耗10点魔力，选择一项：指定一个对方目标下场；或令一个效果消失。",
                     "", "",
                     str(CHARACTERS_DIR / "sanjin.png")),
            Character("soybeanmilk", "江源", [Element.LIGHT], 20, 20,
                     "恢复", "消耗10点魔力将场上存在的其他人或魔物状态恢复至上回合结束时。",
                     "无", "什么？都能回溯了你还想要被动？",
                     str(CHARACTERS_DIR / "jiangyuan.png")),
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

class DeckListScene(Scene):
    """牌组列表场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font = get_chinese_font(32)
        
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
        self.create_button = Button(SCREEN_WIDTH - 220, 20, 200, 40, "创建牌组",
                                    callback=self.create_deck)
    
    def create_deck(self):
        # TODO: 实现牌组创建
        print("创建牌组功能待实现")
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        self.create_button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        title = self.font.render("我的牌组", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # 显示牌组列表
        y = 150
        for i, deck in enumerate(self.game.decks):
            text = f"{i+1}. {deck.name} ({len(deck.cards)}张卡牌)"
            deck_surf = self.font.render(text, True, COLOR_TEXT)
            screen.blit(deck_surf, (100, y))
            y += 50
        
        if not self.game.decks:
            text = self.font.render("还没有牌组，点击右上角创建", True, COLOR_TEXT_DIM)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 300))
        
        self.back_button.draw(screen)
        self.create_button.draw(screen)

class BattleScene(Scene):
    """对战场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font = get_chinese_font(32)
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        title = self.font.render("对战场景（开发中）", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
        
        self.back_button.draw(screen)

class NetworkLobbyScene(Scene):
    """网络大厅场景"""
    def __init__(self, game):
        super().__init__(game)
        self.font = get_chinese_font(32)
        self.back_button = Button(20, 20, 100, 40, "返回",
                                  callback=lambda: game.change_scene(GameState.MAIN_MENU))
    
    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
    
    def draw(self, screen: pygame.Surface):
        screen.fill(COLOR_BG)
        
        title = self.font.render("网络对战（开发中）", True, COLOR_TEXT)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 300))
        
        self.back_button.draw(screen)

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
            GameState.BATTLE: BattleScene,
            GameState.NETWORK_LOBBY: NetworkLobbyScene,
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

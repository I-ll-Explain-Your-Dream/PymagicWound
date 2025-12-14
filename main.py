#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔法伤痕卡牌游戏 - Python实现
MagicWound Card Game - Python Implementation
"""

import sys
import os
import base64
import zlib
import random
import json
import socket
import threading
import queue
import time
from typing import List, Dict, Optional, Tuple, Callable
from enum import IntEnum
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy

# 确保控制台支持UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# ============= 枚举定义 =============

class CardType(IntEnum):
    """卡牌类型"""
    CREATURE = 1  # 生物
    SPELL = 2     # 法术


class Element(IntEnum):
    """元素类型"""
    PHYSICAL = 1  # 物理
    LIGHT = 2     # 光
    DARK = 3      # 暗
    WATER = 4     # 水
    FIRE = 5      # 火
    EARTH = 6     # 土
    WIND = 7      # 风


class Rarity(IntEnum):
    """稀有度"""
    COMMON = 1    # 普通
    UNCOMMON = 2  # 罕见
    RARE = 3      # 稀有
    MYTHIC = 4    # 神话
    FUNNY = 5     # 趣味


class DeckType(IntEnum):
    """牌组类型"""
    STANDARD = 1  # 标准牌组
    CASUAL = 2    # 休闲牌组


# ============= 辅助函数 =============

def element_to_string(element: Element) -> str:
    """元素转字符串"""
    mapping = {
        Element.PHYSICAL: "物理",
        Element.LIGHT: "光",
        Element.DARK: "暗",
        Element.WATER: "水",
        Element.FIRE: "火",
        Element.EARTH: "土",
        Element.WIND: "风"
    }
    return mapping.get(element, "未知")


def rarity_to_string(rarity: Rarity) -> str:
    """稀有度转字符串"""
    mapping = {
        Rarity.COMMON: "普通",
        Rarity.UNCOMMON: "罕见",
        Rarity.RARE: "稀有",
        Rarity.MYTHIC: "神话",
        Rarity.FUNNY: "趣味"
    }
    return mapping.get(rarity, "未知")


def card_type_to_string(card_type: CardType) -> str:
    """卡牌类型转字符串"""
    return "生物" if card_type == CardType.CREATURE else "法术"


def deck_type_to_string(deck_type: DeckType) -> str:
    """牌组类型转字符串"""
    return "标准牌组" if deck_type == DeckType.STANDARD else "休闲牌组"


def generate_checksum(data: str) -> str:
    """生成CRC32校验和（4位十六进制）"""
    crc = zlib.crc32(data.encode('utf-8')) & 0xffffffff
    return f"{crc:08x}"[:4]


def encode_deck_code(data: str) -> str:
    """编码牌组代码"""
    checksum = generate_checksum(data)
    combined = f"{data}|{checksum}"
    return base64.b64encode(combined.encode('utf-8')).decode('utf-8')


def decode_deck_code(code: str) -> Optional[Tuple[str, bool]]:
    """解码牌组代码，返回(数据, 是否有效)"""
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


# ============= 核心类 =============

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
    
    def has_element(self, element: Element) -> bool:
        """检查是否拥有指定元素"""
        return element in self.elements
    
    def display(self):
        """显示角色信息"""
        print(f"角色: {self.name}")
        print(f"元素: {' '.join(element_to_string(e) for e in self.elements)}")
        print(f"生命值: {self.health}")
        print(f"能量: {self.energy}")
        print(f"能力: {self.ability}")
        print(f"描述: {self.description}")
        print(f"被动能力: {self.passive_ability}")
        print(f"被动描述: {self.passive_description}")
        print(f"ID: {self.id}")
        print("------------------------")


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
    
    @property
    def card_type(self) -> CardType:
        """根据属性判断卡牌类型"""
        if self.attack == 0 and self.defense == 0 and self.health == 0:
            return CardType.SPELL
        return CardType.CREATURE
    
    def has_element(self, element: Element) -> bool:
        """检查是否拥有指定元素"""
        return element in self.elements
    
    def serialize(self) -> str:
        """序列化为ID"""
        return self.id
    
    def display(self):
        """显示卡牌信息"""
        print(f"名称: {self.name}")
        print(f"类型: {card_type_to_string(self.card_type)}")
        print(f"元素: {' '.join(element_to_string(e) for e in self.elements)}")
        print(f"费用: {self.cost}")
        print(f"稀有度: {rarity_to_string(self.rarity)}")
        print(f"描述: {self.description}")
        if self.card_type == CardType.CREATURE:
            print(f"攻击/防御/生命: {self.attack}/{self.defense}/{self.health}")
        print(f"ID: {self.id}")
        print("------------------------")


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
        """添加卡牌"""
        # 标准牌组不能携带趣味稀有度
        if self.deck_type == DeckType.STANDARD and card.rarity == Rarity.FUNNY:
            print(f"标准牌组不能携带趣味稀有度的卡牌: {card.name}")
            return False
        
        # 检查最大数量
        if len(self.cards) >= self.max_card_limit:
            print(f"牌组已达到最大卡牌数量 ({self.max_card_limit}张)")
            return False
        
        self.cards.append(card)
        self._update_deck_elements()
        self._update_deck_code()
        return True
    
    def remove_card(self, card_name: str) -> bool:
        """移除卡牌"""
        for i, card in enumerate(self.cards):
            if card.name == card_name:
                self.cards.pop(i)
                self._update_deck_elements()
                self._update_deck_code()
                return True
        return False
    
    def add_character(self, character: Character) -> bool:
        """添加角色"""
        if len(self.characters) >= 3:
            print("牌组最多只能有3个角色")
            return False
        self.characters.append(character)
        self._update_deck_code()
        return True
    
    def remove_character(self, character_name: str) -> bool:
        """移除角色"""
        for i, char in enumerate(self.characters):
            if char.name == character_name:
                self.characters.pop(i)
                self._update_deck_code()
                return True
        return False
    
    def get_card_count(self) -> int:
        """获取卡牌数量"""
        return len(self.cards)
    
    def get_character_count(self) -> int:
        """获取角色数量"""
        return len(self.characters)
    
    def is_valid(self) -> bool:
        """检查牌组是否有效"""
        return len(self.cards) >= 20 and len(self.characters) == 3
    
    def get_element_distribution(self) -> Dict[Element, int]:
        """获取元素分布"""
        distribution = defaultdict(int)
        for card in self.cards:
            for element in card.elements:
                distribution[element] += 1
        return dict(distribution)
    
    def shuffle(self):
        """洗牌"""
        random.shuffle(self.cards)
    
    def display(self):
        """显示牌组详情"""
        print("\n=== 牌组详情 ===")
        print(f"牌组名称: {self.name}")
        print(f"牌组类型: {deck_type_to_string(self.deck_type)}")
        print(f"卡牌数量: {len(self.cards)}/{self.max_card_limit}")
        print(f"角色数量: {len(self.characters)}/3")
        print(f"牌组代码: {self.deck_code}")
        
        distribution = self.get_element_distribution()
        print("元素分布:")
        for element, count in distribution.items():
            print(f"  {element_to_string(element)}: {count} 张")
        
        type_count = defaultdict(int)
        for card in self.cards:
            type_count[card.card_type] += 1
        
        print("类型分布:")
        for card_type, count in type_count.items():
            print(f"  {card_type_to_string(card_type)}: {count} 张")
        
        print("角色列表:")
        for char in self.characters:
            print(f"- {char.name} (生命:{char.health}, 能量:{char.energy})")
        
        print("卡牌列表:")
        for card in self.cards:
            elements_str = ' '.join(element_to_string(e) for e in card.elements)
            print(f"- {card.name} (费用:{card.cost}, 元素:{elements_str})")
    
    def _update_deck_elements(self):
        """更新牌组元素"""
        elements = set()
        for card in self.cards:
            elements.update(card.elements)
        self.deck_elements = sorted(list(elements))
    
    def _update_deck_code(self):
        """更新牌组代码"""
        char_ids = ','.join(char.id for char in self.characters)
        card_ids = ','.join(card.serialize() for card in self.cards)
        data = f"{self.name};{int(self.deck_type)};{char_ids};{card_ids};{self.max_card_limit};"
        self.deck_code = encode_deck_code(data)
    
    def import_from_code(self, code: str, all_cards: List[Card], 
                        all_characters: List[Character]) -> bool:
        """从牌组代码导入"""
        data, valid = decode_deck_code(code)
        if not valid or data is None:
            return False
        
        try:
            parts = data.split(';')
            if len(parts) < 4:
                return False
            
            self.name = parts[0]
            self.deck_type = DeckType(int(parts[1]))
            
            # 解析角色
            char_ids = parts[2].split(',') if parts[2] else []
            self.characters = []
            for char_id in char_ids:
                if not char_id:
                    continue
                char = next((c for c in all_characters if c.id == char_id), None)
                if char:
                    self.characters.append(char)
            
            # 解析卡牌
            card_ids = parts[3].split(',') if parts[3] else []
            self.cards = []
            for card_id in card_ids:
                if not card_id:
                    continue
                card = next((c for c in all_cards if c.id == card_id), None)
                if card:
                    self.cards.append(card)
            
            # 解析最大限制
            if len(parts) >= 5:
                try:
                    self.max_card_limit = int(parts[4])
                except ValueError:
                    pass
            
            self._update_deck_elements()
            self.deck_code = code
            return True
            
        except Exception as e:
            print(f"导入失败: {e}")
            return False
    
    @staticmethod
    def is_valid_deck_code(code: str) -> bool:
        """验证牌组代码"""
        _, valid = decode_deck_code(code)
        return valid


class CharacterDatabase:
    """角色数据库"""
    
    def __init__(self):
        self.all_characters: List[Character] = []
        self._initialize_characters()
    
    def _initialize_characters(self):
        """初始化角色"""
        self.all_characters = [
            Character(
                "xxmlt", "金天",
                [Element.WATER], 25, 15,
                "治疗", "消耗5点魔力，指定一个友方目标获得5点生命值。",
                "死生", "\033[1m每局对战限一次\033[0m，当我方人物受到致命伤时，不使其下场,而是使生命值降为1。"
            ),
            Character(
                "neko", "三金",
                [Element.WIND], 20, 25,
                "吹飞", "消耗10点魔力，选择一项：指定一个对方目标下场；或令一个效果消失。",
                "", ""
            ),
            Character(
                "soybeanmilk", "江源",
                [Element.LIGHT], 20, 20,
                "恢复", "消耗10点魔力将场上存在的其他人或魔物状态恢复至上回合结束时。（第二回合解锁）",
                "无", "\033[3m什么？都能回溯了你还想要被动？\033[0m"
            ),
        ]
    
    def get_all_characters(self) -> List[Character]:
        """获取所有角色"""
        return self.all_characters
    
    def find_character(self, name: str) -> Optional[Character]:
        """根据名称查找角色"""
        return next((c for c in self.all_characters if c.name == name), None)
    
    def find_character_by_id(self, char_id: str) -> Optional[Character]:
        """根据ID查找角色"""
        return next((c for c in self.all_characters if c.id == char_id), None)
    
    def get_characters_by_element(self, element: Element) -> List[Character]:
        """根据元素获取角色"""
        return [c for c in self.all_characters if c.has_element(element)]


class CardDatabase:
    """卡牌数据库"""
    
    def __init__(self):
        self.all_cards: List[Card] = []
        self._initialize_cards()
    
    def _initialize_cards(self):
        """初始化卡牌"""
        self.all_cards = [
            Card("madposion", "狂乱药水", [Element.WATER], 15, Rarity.MYTHIC,
                 "本回合中，目标人物卡牌释放三次，在其魔力不足时以三倍于魔力值消耗的生命替代。"),
            Card("organichemistry", "魔药学领城大神！", [Element.WATER], 9, Rarity.MYTHIC,
                 "本局对战中，你的药水魔力消耗减少（2）。随机获取3张药水。"),
            Card("slowdown", "缓慢药水", [Element.WATER], 5, Rarity.RARE,
                 "直到你的下个回合，你对手的牌魔力消耗增加（2）。"),
            Card("Timeelder", "时空限速", [Element.DARK], 5, Rarity.RARE,
                 "直到你的下个回合，你对手不能使用5张以上的牌。（已使用%d张）"),
            Card("LGBTQ", "多彩药水", [Element.WATER], 3, Rarity.RARE,
                 "本回合中，你的牌是所有属性。"),
            Card("Lazarus,Arise!", "起尸", [Element.DARK], 2, Rarity.RARE,
                 "复活一个人物，并具有25%的生命（向下取整），在你的的结束时，将其消灭。如果其已死亡，致为使其无法复活。"),
            Card("DontForgotMe", "瓶装记忆", [Element.WATER], 5, Rarity.RARE,
                 "这张牌是药水。将目标玩家卡组中的8张牌洗入你的牌库，其魔力消耗减少（2）。"),
            Card("TheCardLetMeWin", "记忆屏蔽", [Element.WATER], 6, Rarity.RARE,
                 "摧毁你对手牌库顶和底各2张牌。"),
            Card("TheCardLetYouLose", "记忆摧毁", [Element.WATER], 2, Rarity.RARE,
                 "摧毁\033[3m你\033[0m和对手牌库顶和底各2张牌。然后如果你的牌库为空，你输掉游戏。"),
            Card("whAt", "你说啥？", [Element.WATER], 2, Rarity.RARE,
                 "摧毁对手牌库中的1张牌。然后摧毁所有同名卡（无论其在哪里）。"),
            Card("balance", "平衡", [Element.LIGHT, Element.DARK], 4, Rarity.RARE,
                 "弃掉你的手牌。抽等量的牌。"),
            Card("TearAll", "遗忘灵药", [Element.WATER, Element.DARK], 18, Rarity.RARE,
                 "摧毁你对手的牌库。将你对手弃牌堆中的10张牌洗入其牌库，它们的魔力消耗增加（2）。"),
            Card("Wordle", "Wordle", [Element.PHYSICAL], 4, Rarity.FUNNY,
                 "使你对手下回合造成的伤害额外乘上今日Wordle的通关率。"),
            Card("IDontcar", "窝不载乎", [Element.PHYSICAL], 2, Rarity.FUNNY,
                 "你的对手发送的表情改为汽车鸣笛声。\033[3m呜呜呜！\033[0m"),
        ]
    
    def get_all_cards(self) -> List[Card]:
        """获取所有卡牌"""
        return self.all_cards
    
    def find_card(self, name: str) -> Optional[Card]:
        """根据名称查找卡牌"""
        return next((c for c in self.all_cards if c.name == name), None)
    
    def find_card_by_id(self, card_id: str) -> Optional[Card]:
        """根据ID查找卡牌"""
        return next((c for c in self.all_cards if c.id == card_id), None)
    
    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        """根据类型获取卡牌"""
        return [c for c in self.all_cards if c.card_type == card_type]
    
    def get_cards_by_element(self, element: Element) -> List[Card]:
        """根据元素获取卡牌"""
        return [c for c in self.all_cards if c.has_element(element)]
    
    def get_cards_by_rarity(self, rarity: Rarity) -> List[Card]:
        """根据稀有度获取卡牌"""
        return [c for c in self.all_cards if c.rarity == rarity]


class GameManager:
    """游戏管理器"""
    
    def __init__(self):
        self.card_db = CardDatabase()
        self.character_db = CharacterDatabase()
        self.decks: List[Deck] = []
    
    def display_all_cards(self):
        """显示所有卡牌"""
        print("=== 所有卡牌 ===")
        for card in self.card_db.get_all_cards():
            card.display()
    
    def display_all_characters(self):
        """显示所有角色"""
        print("=== 所有角色 ===")
        for character in self.character_db.get_all_characters():
            character.display()
    
    def create_deck(self):
        """创建牌组"""
        deck_name = input("请输入牌组名称: ").strip()
        
        print("选择牌组类型:")
        print("1. 标准牌组 (不能携带趣味稀有度卡牌)")
        print("2. 休闲牌组 (可以携带所有卡牌)")
        type_choice = input("选择: ").strip()
        
        deck_type = DeckType.STANDARD if type_choice == "1" else DeckType.CASUAL
        new_deck = Deck(deck_name, deck_type)
        
        # 选择角色
        print("\n选择3个角色 (输入编号):")
        all_chars = self.character_db.get_all_characters()
        for i, char in enumerate(all_chars):
            print(f"[{i}] {char.name} ({char.health} HP, {char.energy} MP)")
        
        for i in range(3):
            while True:
                try:
                    idx = int(input(f"选择第 {i+1} 个角色编号: ").strip())
                    if 0 <= idx < len(all_chars):
                        new_deck.add_character(all_chars[idx])
                        print(f"已添加角色: {all_chars[idx].name}")
                        break
                    else:
                        print("无效编号，请重试。")
                except ValueError:
                    print("请输入有效的数字。")
        
        # 选择卡牌
        print("\n选择要添加到牌组的卡牌 (输入卡牌编号，输入'done'结束):")
        
        # 根据牌组类型过滤卡牌
        if deck_type == DeckType.STANDARD:
            available_cards = [c for c in self.card_db.get_all_cards() 
                             if c.rarity != Rarity.FUNNY]
        else:
            available_cards = self.card_db.get_all_cards()
        
        for i, card in enumerate(available_cards):
            print(f"[{i}] {card.name} ({card_type_to_string(card.card_type)}, "
                  f"{card.cost}, {rarity_to_string(card.rarity)})")
        
        while True:
            line = input("输入卡牌编号或 done: ").strip()
            if line.lower() == 'done':
                break
            try:
                cidx = int(line)
                if 0 <= cidx < len(available_cards):
                    card = available_cards[cidx]
                    new_deck.add_card(card)
                    print(f"已添加卡牌: {card.name} "
                          f"({new_deck.get_card_count()}/{new_deck.max_card_limit})")
                else:
                    print("无效编号。")
            except ValueError:
                print("请输入有效的数字或 'done'。")
        
        # 检查牌组是否有效
        if new_deck.is_valid():
            self.decks.append(new_deck)
            print("牌组创建成功!")
        else:
            print("牌组无效! 需要至少20张卡牌和3个角色。")
            print(f"当前: {new_deck.get_card_count()}张卡牌, "
                  f"{new_deck.get_character_count()}个角色")
    
    def display_decks(self):
        """显示牌组列表"""
        print("=== 我的牌组 ===")
        for i, deck in enumerate(self.decks):
            valid_status = "有效" if deck.is_valid() else "无效"
            print(f"{i+1}. {deck.name} ({deck.get_card_count()} 张卡牌, "
                  f"{deck.get_character_count()} 个角色) - {valid_status}")
    
    def display_deck_details(self):
        """显示牌组详情"""
        if not self.decks:
            print("没有牌组可以显示。")
            return
        
        self.display_decks()
        try:
            choice = int(input("选择牌组编号: ").strip())
            if 1 <= choice <= len(self.decks):
                self.decks[choice - 1].display()
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效的数字。")
    
    def export_deck_code(self):
        """导出牌组代码"""
        if not self.decks:
            print("没有牌组可以导出")
            return
        
        self.display_decks()
        try:
            choice = int(input("选择要导出的牌组编号: ").strip())
            if 1 <= choice <= len(self.decks):
                print(f"牌组代码: {self.decks[choice - 1].deck_code}")
                print("请保存此代码以备后续导入。")
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效的数字。")
    
    def import_deck_from_code(self):
        """从代码导入牌组"""
        deck_code = input("请输入牌组代码: ").strip()
        
        if not Deck.is_valid_deck_code(deck_code):
            print("无效的牌组代码!")
            return
        
        new_name = input("请输入新的牌组名称: ").strip()
        imported_deck = Deck(new_name)
        
        if imported_deck.import_from_code(deck_code, 
                                         self.card_db.get_all_cards(),
                                         self.character_db.get_all_characters()):
            self.decks.append(imported_deck)
            print("牌组导入成功!")
            imported_deck.display()
        else:
            print("导入失败，请检查代码是否正确。")
    
    def start_battle(self):
        """开始对局"""
        if not self.decks:
            print("没有已创建的牌组，请先创建牌组后再开始对局。")
            return
        
        # 选择牌组
        def choose_deck_for_player(player_name: str) -> Optional[Deck]:
            print(f"\n{player_name} 请选择一个牌组编号：")
            for i, deck in enumerate(self.decks):
                print(f"[{i}] {deck.name} ({deck.get_card_count()} 张)")
            while True:
                try:
                    idx = int(input("输入编号: ").strip())
                    if 0 <= idx < len(self.decks):
                        return self.decks[idx]
                    print("无效编号，请重试。")
                except ValueError:
                    print("请输入有效数字。")
        
        # 玩家状态
        @dataclass
        class CharacterState:
            character: Character
            cur_hp: int
            cur_energy: int
        
        @dataclass
        class PlayerState:
            name: str
            base_hp: int = 50
            base_mana: int = 30
            chars: List[CharacterState] = field(default_factory=list)
            deck: List[Card] = field(default_factory=list)
            hand: List[Card] = field(default_factory=list)
        
        # 创建两个玩家
        p1_name = input("\n请输入玩家1名称: ").strip() or "玩家1"
        p1_deck = choose_deck_for_player(p1_name)
        if not p1_deck:
            return
        
        p2_name = input("请输入玩家2名称: ").strip() or "玩家2"
        p2_deck = choose_deck_for_player(p2_name)
        if not p2_deck:
            return
        
        p1 = PlayerState(p1_name)
        p2 = PlayerState(p2_name)
        
        # 选择角色
        def select_characters(player: PlayerState):
            print(f"\n{player.name} 请选择3个角色:")
            all_chars = self.character_db.get_all_characters()
            for i, char in enumerate(all_chars):
                print(f"[{i}] {char.name}")
            for k in range(3):
                while True:
                    try:
                        idx = int(input(f"第{k+1}个: ").strip())
                        if 0 <= idx < len(all_chars):
                            char = all_chars[idx]
                            char_state = CharacterState(
                                char, char.health, (char.energy + 1) // 2
                            )
                            player.chars.append(char_state)
                            break
                        print("无效编号。")
                    except ValueError:
                        print("请输入数字。")
        
        select_characters(p1)
        select_characters(p2)
        
        # 构建牌库
        def build_deck(player: PlayerState, deck: Deck):
            # 从牌组代码解析卡牌
            data, valid = decode_deck_code(deck.deck_code)
            if valid and data:
                parts = data.split(';')
                if len(parts) >= 4:
                    card_ids = parts[3].split(',')
                    for card_id in card_ids:
                        if card_id:
                            card = self.card_db.find_card_by_id(card_id)
                            if card:
                                player.deck.append(card)
            
            if not player.deck:
                player.deck = self.card_db.get_all_cards()[:]
            
            random.shuffle(player.deck)
            # 初始抽3张
            for _ in range(3):
                if player.deck:
                    player.hand.append(player.deck.pop())
        
        build_deck(p1, p1_deck)
        build_deck(p2, p2_deck)
        
        # 辅助函数
        def is_mage(char: Character) -> bool:
            """判断是否为法师"""
            return any(e != Element.PHYSICAL for e in char.elements)
        
        def draw_cards(player: PlayerState, n: int):
            """抽牌"""
            for _ in range(n):
                if player.deck:
                    player.hand.append(player.deck.pop())
        
        # 卡牌效果注册表
        card_effects: Dict[str, Callable] = {}
        
        def register_effect(card_id: str, effect: Callable):
            card_effects[card_id] = effect
        
        # 注册卡牌效果
        register_effect("Wordle", lambda owner, opp, dmg: dmg * 2)
        register_effect("madposion", lambda owner, opp, dmg: dmg * 3)
        
        def apply_damage_to_char(player: PlayerState, idx: int, dmg: int, is_magic: bool):
            """对角色造成伤害"""
            if idx < 0 or idx >= len(player.chars):
                return
            
            char_state = player.chars[idx]
            if is_magic and is_mage(char_state.character):
                energy_taken = min(char_state.cur_energy, dmg)
                char_state.cur_energy -= energy_taken
                dmg -= energy_taken
            
            if dmg > 0:
                char_state.cur_hp -= dmg
            
            if char_state.cur_hp <= 0:
                overflow = -char_state.cur_hp
                print(f"{player.name} 的角色 {char_state.character.name} 被击败！")
                
                # 替补上场
                if len(player.chars) == 3:
                    player.chars[idx] = player.chars[2]
                    player.chars.pop()
                else:
                    char_state.cur_hp = 0
                
                if overflow > 0:
                    player.base_hp -= overflow
                    print(f"{player.name} 的基地受到溢出伤害 {overflow} 点！")
        
        def apply_damage_to_base(player: PlayerState, dmg: int):
            """对基地造成伤害"""
            player.base_hp -= dmg
        
        def check_winner(p1: PlayerState, p2: PlayerState) -> int:
            """检查胜者"""
            if p1.base_hp <= 0:
                return 2
            if p2.base_hp <= 0:
                return 1
            return 0
        
        # 主循环
        turn = 1
        active = 0  # 0=p1, 1=p2
        running = True
        
        while running:
            cur = p1 if active == 0 else p2
            opp = p2 if active == 0 else p1
            
            print(f"\n{'='*50}")
            print(f"回合 {turn} - {cur.name} 的回合开始")
            print('='*50)
            
            # 抽牌
            if cur.deck:
                cur.hand.append(cur.deck.pop())
                print(f"{cur.name} 抽了1张牌。")
            else:
                print(f"{cur.name} 的牌库已空，无法抽牌。")
            
            # 恢复魔力和能量
            cur.base_mana = min(30, cur.base_mana + 5)
            for char_state in cur.chars:
                max_energy = char_state.character.energy
                char_state.cur_energy = min(max_energy, char_state.cur_energy + 5)
            
            # 回合内循环
            while True:
                # 显示状态
                def show_state(p: PlayerState, is_current: bool):
                    prefix = ">>> " if is_current else "    "
                    print(f"\n{prefix}【{p.name}】基地生命: {p.base_hp} | 基地魔力: {p.base_mana}")
                    print(f"{prefix}前场角色:")
                    for i in range(min(2, len(p.chars))):
                        cs = p.chars[i]
                        print(f"{prefix}  [{i}] {cs.character.name} "
                              f"(HP: {cs.cur_hp}/{cs.character.health}, "
                              f"MP: {cs.cur_energy}/{cs.character.energy})")
                    if len(p.chars) == 3:
                        r = p.chars[2]
                        print(f"{prefix}  后场: {r.character.name} "
                              f"(HP: {r.cur_hp}/{r.character.health})")
                    if is_current:
                        print(f"{prefix}手牌({len(p.hand)}): ", end='')
                        for i, card in enumerate(p.hand):
                            print(f"[{i}]{card.name} ", end='')
                        print()
                
                show_state(cur, True)
                show_state(opp, False)
                
                print("\n操作：p 出牌 | e 结束回合 | q 退出对局")
                op = input("输入操作: ").strip().lower()
                
                if op == 'q':
                    print("对局提前结束。")
                    running = False
                    break
                
                if op == 'e':
                    print("结束回合。")
                    break
                
                if op == 'p':
                    if not cur.hand:
                        print("手牌为空。")
                        continue
                    
                    try:
                        hidx = int(input("选择手牌索引: ").strip())
                        if hidx < 0 or hidx >= len(cur.hand):
                            print("无效索引。")
                            continue
                        
                        card = cur.hand[hidx]
                        is_physical = Element.PHYSICAL in card.elements
                        
                        char_idx = int(input("选择使用角色(0或1): ").strip())
                        if char_idx < 0 or char_idx >= len(cur.chars):
                            print("无效角色。")
                            continue
                        
                        actor = cur.chars[char_idx]
                        actor_is_mage = is_mage(actor.character)
                        
                        if not actor_is_mage and not is_physical:
                            print("普通人只能使用物理属性的牌。")
                            continue
                        
                        target = input("目标(t0/t1=前场, b=基地): ").strip().lower()
                        target_is_base = target == 'b'
                        target_idx = -1
                        
                        if not target_is_base:
                            if target in ['t0', 't1']:
                                target_idx = 0 if target == 't0' else 1
                                if target_idx >= len(opp.chars):
                                    print("对方该位置无角色。")
                                    continue
                            else:
                                print("无效目标。")
                                continue
                        
                        # 计算费用
                        cost = 0 if is_physical else card.cost
                        remaining = cost
                        
                        if actor_is_mage and cost > 0:
                            from_char = min(actor.cur_energy, remaining)
                            actor.cur_energy -= from_char
                            remaining -= from_char
                            
                            from_base = min(cur.base_mana, remaining)
                            cur.base_mana -= from_base
                            remaining -= from_base
                            
                            if remaining > 0:
                                print(f"生命支付剩余费用: {remaining}")
                                actor.cur_hp -= remaining
                        
                        # 计算伤害
                        base_dmg = max(1, card.cost)
                        element_match = any(e in actor.character.elements 
                                          for e in card.elements)
                        final_dmg = base_dmg * (2 if element_match else 1)
                        dmg_is_magic = not is_physical
                        
                        # 应用卡牌效果
                        if card.id in card_effects:
                            final_dmg = card_effects[card.id](cur, opp, final_dmg)
                        
                        # 造成伤害
                        print(f"\n{actor.character.name} 使用 {card.name} ", end='')
                        if target_is_base:
                            print(f"对 {opp.name} 的基地", end='')
                            apply_damage_to_base(opp, final_dmg)
                        else:
                            print(f"对 {opp.chars[target_idx].character.name}", end='')
                            apply_damage_to_char(opp, target_idx, final_dmg, dmg_is_magic)
                        
                        print(f" 造成 {final_dmg} 点{'魔法' if dmg_is_magic else '物理'}伤害！")
                        
                        cur.hand.pop(hidx)
                        
                        # 检查胜负
                        winner = check_winner(p1, p2)
                        if winner != 0:
                            winner_name = p1.name if winner == 1 else p2.name
                            print(f"\n{'='*50}")
                            print(f"🎉 {winner_name} 获胜！")
                            print('='*50)
                            running = False
                            break
                        
                    except (ValueError, IndexError) as e:
                        print(f"输入错误: {e}")
                        continue
            
            if not running:
                break
            
            # 切换回合
            active = 1 - active
            turn += 1
        
        print("\n对局结束，返回主菜单。")
    
    def start_network_battle(self):
        """局域网联机"""
        print("\n局域网联机模式")
        print("1. 主机")
        print("2. 加入")
        mode = input("选择: ").strip()
        
        if mode not in ['1', '2']:
            print("取消联机。")
            return
        
        is_host = (mode == '1')
        
        # 网络通信
        net_running = True
        recv_queue = queue.Queue()
        conn_socket = None
        
        try:
            if is_host:
                port_str = input("监听端口(默认4000): ").strip() or "4000"
                port = int(port_str)
                
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.bind(('0.0.0.0', port))
                server.listen(1)
                print(f"等待连接，端口 {port} ...")
                
                conn_socket, addr = server.accept()
                print(f"已连接: {addr}")
                server.close()
            else:
                host = input("主机地址(默认127.0.0.1): ").strip() or "127.0.0.1"
                port_str = input("端口(默认4000): ").strip() or "4000"
                port = int(port_str)
                
                conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print("尝试连接...")
                conn_socket.connect((host, port))
                print("已连接！")
            
            # 接收线程
            def recv_thread():
                buffer = ""
                while net_running:
                    try:
                        data = conn_socket.recv(4096).decode('utf-8')
                        if not data:
                            break
                        buffer += data
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            recv_queue.put(line)
                    except:
                        break
            
            thread = threading.Thread(target=recv_thread, daemon=True)
            thread.start()
            
            # 简单握手
            my_name = input("请输入你的名称: ").strip() or ("Host" if is_host else "Client")
            conn_socket.send(f"NAME;{my_name}\n".encode('utf-8'))
            
            # 等待对方名称
            their_name = "对手"
            try:
                msg = recv_queue.get(timeout=5)
                if msg.startswith("NAME;"):
                    their_name = msg.split(';', 1)[1]
            except queue.Empty:
                pass
            
            print(f"已连接: {their_name}")
            
            # 简化的网络对战循环
            my_turn = is_host
            print("网络对战开始" + (" - 你先手" if my_turn else " - 对方先手"))
            
            while net_running:
                # 处理接收的消息
                try:
                    while True:
                        msg = recv_queue.get_nowait()
                        if msg.startswith("EMOJI;"):
                            print(f"\n[对方表情] {msg.split(';', 1)[1]}")
                        elif msg == "ENDTURN":
                            my_turn = True
                            print("\n对方结束回合，轮到你了。")
                except queue.Empty:
                    pass
                
                if not my_turn:
                    time.sleep(0.3)
                    continue
                
                print("\n你的回合：p 出牌 | /emoji 文本 | e 结束回合 | q 退出")
                op = input("> ").strip()
                
                if op == 'q':
                    break
                
                if op.startswith("/emoji"):
                    emoji = op[6:].strip() or "🙂"
                    conn_socket.send(f"EMOJI;{emoji}\n".encode('utf-8'))
                    print(f"[已发送表情] {emoji}")
                    continue
                
                if op == 'e':
                    conn_socket.send("ENDTURN\n".encode('utf-8'))
                    my_turn = False
                    print("已结束回合。")
                    continue
                
                if op == 'p':
                    print("出牌功能（简化）")
                    continue
        
        except Exception as e:
            print(f"网络错误: {e}")
        finally:
            if conn_socket:
                conn_socket.close()
            print("退出联机。")
    
    def show_menu(self):
        """显示菜单"""
        print("\n=== 魔法伤痕卡牌游戏 ===")
        print("1. 查看所有卡牌")
        print("2. 查看所有角色")
        print("3. 创建牌组")
        print("4. 查看我的牌组")
        print("5. 查看牌组详情")
        print("6. 导出牌组代码")
        print("7. 导入牌组代码")
        print("8. 退出")
        print("9. 开始对局")
        print("10. 局域网联机")
        print("选择: ", end='')
    
    def run(self):
        """运行游戏"""
        while True:
            self.show_menu()
            try:
                choice = int(input().strip())
                
                if choice == 1:
                    self.display_all_cards()
                elif choice == 2:
                    self.display_all_characters()
                elif choice == 3:
                    self.create_deck()
                elif choice == 4:
                    self.display_decks()
                elif choice == 5:
                    self.display_deck_details()
                elif choice == 6:
                    self.export_deck_code()
                elif choice == 7:
                    self.import_deck_from_code()
                elif choice == 8:
                    print("再见!")
                    break
                elif choice == 9:
                    self.start_battle()
                elif choice == 10:
                    self.start_network_battle()
                else:
                    print("无效选择，请重试。")
                    
            except ValueError:
                print("请输入有效的数字。")
            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except Exception as e:
                print(f"发生错误: {e}")


# ============= 主程序入口 =============

def main():
    """主函数"""
    try:
        game = GameManager()
        game.run()
    except Exception as e:
        print(f"程序错误: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# 魔法伤痕 - 图形化版本

## 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装 pygame：

```bash
pip install pygame
```

## 运行游戏

```bash
python main_gui.py
```

## 目录结构

```
MagicWound/
├── main_gui.py              # 图形化主程序
├── main.py                  # 控制台版本（保留）
├── requirements.txt         # 依赖列表
└── assets/                  # 资源目录（自动创建）
    ├── cards/              # 卡牌插图目录
    │   ├── madposion.png
    │   ├── slowdown.png
    │   └── ...
    ├── characters/         # 角色插图目录
    │   ├── jintian.png
    │   ├── sanjin.png
    │   └── jiangyuan.png
    └── ui/                 # UI素材目录
        └── ...
```

## 添加插图

### 卡牌插图
1. 将图片命名为对应的卡牌ID（例如：`madposion.png`）
2. 放入 `assets/cards/` 目录
3. 推荐尺寸：200x200 像素

### 角色插图
1. 将图片命名为对应的角色ID（例如：`jintian.png`）
2. 放入 `assets/characters/` 目录
3. 推荐尺寸：300x300 像素

## 功能说明

### 已实现功能 ✅
- 主菜单导航
- 卡牌图鉴浏览（支持插图显示）
- 角色图鉴浏览（支持插图显示）
- 牌组列表查看
- 元素/稀有度颜色标识
- 鼠标悬停效果

### 开发中功能 🚧
- 牌组构建器（拖拽式）
- 完整对战系统（带动画）
- 局域网联机（图形化界面）
- 卡牌效果动画
- 音效系统

## 卡牌ID列表

用于添加对应插图：

```
madposion.png          # 狂乱药水
organichemistry.png    # 魔药学领城大神！
slowdown.png           # 缓慢药水
timeelder.png          # 时空限速
lgbtq.png              # 多彩药水
lazarus.png            # 起尸
dontforgotme.png       # 瓶装记忆
memorywipe.png         # 记忆屏蔽
memorycrush.png        # 记忆摧毁
what.png               # 你说啥？
balance.png            # 平衡
tearall.png            # 遗忘灵药
wordle.png             # Wordle
idontcar.png           # 窝不载乎
```

## 角色ID列表

```
jintian.png      # 金天
sanjin.png       # 三金
jiangyuan.png    # 江源
```

## 操作说明

- **鼠标左键**：点击选择
- **鼠标滚轮**：在卡牌浏览界面滚动
- **ESC键**：返回上一级/退出游戏
- **关闭窗口**：退出游戏

## 开发计划

### Phase 1: 基础UI（已完成）
- [x] 主菜单
- [x] 卡牌查看器
- [x] 角色查看器
- [x] 牌组列表

### Phase 2: 牌组构建
- [ ] 可视化牌组编辑器
- [ ] 拖拽添加/移除卡牌
- [ ] 实时显示牌组统计

### Phase 3: 对战系统
- [ ] 对战场景搭建
- [ ] 回合制逻辑
- [ ] 卡牌使用动画
- [ ] 伤害特效

### Phase 4: 网络功能
- [ ] 网络大厅UI
- [ ] 房间系统
- [ ] 实时对战同步

## 技术特性

- **纯Python实现**：无需外部游戏引擎
- **模块化设计**：场景系统易于扩展
- **资源热加载**：插图可随时添加
- **跨平台**：支持 Windows/Linux/macOS

## 性能优化

- 目标帧率：60 FPS
- 内存占用：< 100 MB（无插图）
- 插图格式：PNG（支持透明）

## 自定义

### 修改界面配色
编辑 `main_gui.py` 中的颜色常量：
```python
COLOR_BG = (20, 20, 40)           # 背景色
COLOR_CARD_BG = (40, 40, 60)      # 卡牌背景
COLOR_BUTTON = (60, 60, 100)      # 按钮颜色
# ...
```

### 修改窗口大小
```python
SCREEN_WIDTH = 1280   # 宽度
SCREEN_HEIGHT = 720   # 高度
```

## 故障排除

### Q: 游戏无法启动
A: 确认已安装 pygame：`pip install pygame`

### Q: 插图不显示
A: 检查图片文件名是否与卡牌/角色ID匹配，路径是否正确

### Q: 游戏卡顿
A: 降低 FPS 设置或减少同时显示的卡牌数量

## 贡献

欢迎提交插图素材和代码改进！

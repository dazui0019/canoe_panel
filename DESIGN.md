# 设计思路

## 需求背景

用户需要创建一个 Web 页面，通过按钮控制 CANoe 报文中的灯光信号。

## 技术选型

- **前端**：原生 HTML + JavaScript，无框架依赖，简单轻量
- **后端**：Python Flask，提供 REST API
- **CANoe 交互**：py_canoe 库

## 架构设计

```
┌─────────────┐     HTTP      ┌─────────────┐     py_canoe     ┌─────────────┐
│   浏览器    │ ◄────────────► │  Flask App  │ ◄──────────────► │    CANoe    │
│  (前端页面)  │   JSON API    │   (后端)    │                  │  (实时总线)  │
└─────────────┘               └─────────────┘                  └─────────────┘
```

## 文件结构

```
canoe_ctrl/
├── main.py           # CANoe 控制核心逻辑 (信号读取/设置)
├── app.py            # Flask Web 服务器 (API 接口)
├── templates/
│   └── index.html    # 控制页面 (前端)
├── README.md         # 使用说明
└── DESIGN.md        # 本设计文档
```

## 核心实现

### 1. CANoe 信号读取 (main.py)

- 使用 `get_signal_value()` 读取单个信号
- 优化为单次 CANoe 连接读取所有信号，减少连接开销
- 每次调用 `attach_to_active_application()` 连接已运行的 CANoe

### 2. Flask API (app.py)

- `GET /api/get_all_signals` - 获取所有灯光状态
- `POST /api/set_signal` - 设置信号值

### 3. 前端页面 (index.html)

- 使用卡片式布局展示 6 个灯光
- 点击卡片切换状态（toggle 逻辑）
- 每 500ms 轮询读取信号状态
- 灯亮时显示黄色发光效果

## 关键决策

1. **为什么不用 WebSocket？**
   - Flask-SocketIO 需要额外依赖
   - 当前轮询方式足够满足需求

2. **为什么单次连接读取所有信号？**
   - py_canoe 每次调用都需要通过 COM 连接 CANoe
   - 逐个读取会产生多次连接开销
   - 优化为一次连接读取 6 个信号

3. **为什么每 500ms 刷新？**
   - 100ms 响应太快，增加 CANoe 负载
   - 2s 响应太慢
   - 500ms 是平衡点

4. **日志抑制**
   - py_canoe 使用 emoji 日志，在 Windows GBK 控制台会编码错误
   - 通过禁用日志输出解决

## 后续优化方向

- 支持更多信号
- 添加日志记录功能
- 移动端适配
- 皮肤切换

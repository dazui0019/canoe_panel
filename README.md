# CANoe 灯光控制 Web 界面

通过 Web 页面控制 CANoe 报文中的灯光信号。

## 功能

- Web 界面控制 6 个灯光信号
- 实时读取 CANoe 报文状态
- 点击卡片切换灯光状态

## 支持的信号

| 信号名 | 说明 |
|--------|------|
| DaytimeLight | 日行灯 |
| LHTrunLight | 左转向灯 |
| RHTrunLight | 右转向灯 |
| PosLamp | 位置灯 |
| LowBeam | 近光灯 |
| HighBeam | 远光灯 |

## 使用方法

1. 启动 CANoe 并加载配置文件，开始测量
2. 启动服务：`uv run python app.py`
3. 浏览器访问：`http://127.0.0.1:5000`
4. 点击卡片切换灯光状态

## 技术栈

- 前端：原生 HTML + JavaScript
- 后端：Python Flask
- CANoe 交互：py_canoe

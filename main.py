"""
设置 CANoe 报文信号值
"""

import os
import sys

# 设置环境变量让 Python 使用 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 重新配置 stdin/stdout/stderr
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import time
import logging

# 禁用所有日志
logging.disable(logging.CRITICAL)

from py_canoe import CANoe

# CANoe 工程配置
CANOE_CFG = r"D:\File\temp\Chery_Lamp_Control_Test_5.0_V1.7\Lamp_Control_5.0.cfg"

# 信号配置
BUS = "CAN"
CHANNEL = 1  # 数据库加载在通道1
MESSAGE = "FLZCU_4"

# 灯光信号映射
LIGHT_SIGNALS = {
    "DaytimeLight": "日行灯",
    "LHTrunLight": "左转向灯",
    "RHTrunLight": "右转向灯",
    "PosLamp": "位置灯",
    "LowBeam": "近光灯",
    "HighBeam": "远光灯",
}


def get_light_signal(signal_name: str) -> int:
    """
    读取灯光信号值

    Args:
        signal_name: 信号名称

    Returns:
        int: 信号值 (0 或 1)，读取失败返回 -1
    """
    if signal_name not in LIGHT_SIGNALS:
        print(f"错误: 未知的信号名 {signal_name}")
        return -1

    canoe = CANoe()
    try:
        canoe.attach_to_active_application()
        canoe.start_measurement()

        value = canoe.get_signal_value(
            bus=BUS,
            channel=CHANNEL,
            message=MESSAGE,
            signal=signal_name,
            raw_value=False
        )
        return int(value)

    except Exception as e:
        print(f"读取失败: {e}")
        return -1


def get_all_light_signals() -> dict:
    """
    读取所有灯光信号的值 (使用单次连接)

    Returns:
        dict: {信号名: 值}，读取失败的信号值为 -1
    """
    result = {}
    canoe = CANoe()
    try:
        canoe.attach_to_active_application()
        canoe.start_measurement()

        # 一次连接读取所有信号
        for signal_name in LIGHT_SIGNALS.keys():
            try:
                value = canoe.get_signal_value(
                    bus=BUS,
                    channel=CHANNEL,
                    message=MESSAGE,
                    signal=signal_name,
                    raw_value=False
                )
                result[signal_name] = int(value)
            except Exception:
                result[signal_name] = -1

    except Exception:
        # 连接失败时返回所有信号为 -1
        for signal_name in LIGHT_SIGNALS.keys():
            result[signal_name] = -1

    return result


def set_light_signal(signal_name: str, value: int) -> bool:
    """
    设置灯光信号值

    Args:
        signal_name: 信号名称 (DaytimeLight, LHTrunLight, RHTrunLight, PosLamp, LowBeam, HighBeam)
        value: 要设置的值 (0 或 1)

    Returns:
        bool: 是否设置成功
    """
    if signal_name not in LIGHT_SIGNALS:
        print(f"错误: 未知的信号名 {signal_name}")
        return False

    canoe = CANoe()
    try:
        canoe.attach_to_active_application()
        canoe.start_measurement()

        canoe.set_signal_value(
            bus=BUS,
            channel=CHANNEL,
            message=MESSAGE,
            signal=signal_name,
            value=value,
            raw_value=False
        )
        print(f"已设置 {MESSAGE}.{signal_name} = {value}")
        return True

    except Exception as e:
        print(f"设置失败: {e}")
        return False


# 保留旧接口的信号名
SIGNAL = "HighBeam"


def set_signal_loop(value: int = None, signal: str = None):
    """
    持续设置信号值

    Args:
        value: 如果指定值则固定该值，否则循环切换 0/1
        signal: 信号名称，默认为 SIGNAL
    """
    signal = signal or SIGNAL
    canoe = CANoe()
    try:
        # 连接到已打开的 CANoe
        canoe.attach_to_active_application()

        # 启动测量
        canoe.start_measurement()
        print("测量已启动")

        current_value = 0
        print("开始持续设置信号值，按 Ctrl+C 停止")

        while True:
            if value is not None:
                current_value = value
            else:
                # 切换值 0/1
                current_value = 1 if current_value == 0 else 0

            try:
                canoe.set_signal_value(
                    bus=BUS,
                    channel=CHANNEL,
                    message=MESSAGE,
                    signal=signal,
                    value=current_value,
                    raw_value=False
                )
                print(f"{time.strftime('%H:%M:%S')} - 已设置 {MESSAGE}.{signal} = {current_value}")
            except Exception as e:
                print(f"设置失败: {e}")

            time.sleep(1)  # 每秒切换一次

    except KeyboardInterrupt:
        print("\n停止运行")


def set_signal_once(value: int, signal: str = None):
    """
    设置一次信号值

    Args:
        value: 要设置的值 (0 或 1)
        signal: 信号名称，默认为 SIGNAL
    """
    signal = signal or SIGNAL
    return set_light_signal(signal, value)


if __name__ == "__main__":
    # 方式1: 循环切换信号值
    # set_signal_loop()

    # 方式2: 设置为固定值 1
    set_signal_once(0)

    # 方式3: 设置为固定值 0
    # set_signal_once(0)

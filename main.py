"""
设置 CANoe 报文信号值
"""

import os
import sys
import threading

# 设置环境变量让 Python 使用 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 重新配置 stdin/stdout/stderr
if sys.platform == 'win32':
    # 使用 reconfigure 保留控制台流的原始缓冲策略，避免替换流对象导致输出异常
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(
            encoding='utf-8',
            errors='replace',
            line_buffering=True,
            write_through=True,
        )
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(
            encoding='utf-8',
            errors='replace',
            line_buffering=True,
            write_through=True,
        )

import time
import logging

from py_canoe import CANoe

LOGGER = logging.getLogger(__name__)

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


_CANOE_LOCK = threading.Lock()
_CANOE_SESSION = {
    "client": None,
    "attached": False,
    "measurement_started": False,
}


def _reset_canoe_session():
    """重置 CANoe 会话状态，在连接异常后触发重连。"""
    _CANOE_SESSION["client"] = None
    _CANOE_SESSION["attached"] = False
    _CANOE_SESSION["measurement_started"] = False


def _get_canoe_client() -> CANoe:
    """
    获取可用的 CANoe 客户端（惰性初始化 + 会话复用）。

    Returns:
        CANoe: 已连接并确保测量已启动的客户端实例
    """
    canoe = _CANOE_SESSION["client"]
    if canoe is None:
        canoe = CANoe()
        _CANOE_SESSION["client"] = canoe
        _CANOE_SESSION["attached"] = False
        _CANOE_SESSION["measurement_started"] = False

    try:
        if not _CANOE_SESSION["attached"]:
            canoe.attach_to_active_application()
            _CANOE_SESSION["attached"] = True

        if not _CANOE_SESSION["measurement_started"]:
            canoe.start_measurement()
            _CANOE_SESSION["measurement_started"] = True

        return canoe
    except Exception as e:
        _reset_canoe_session()
        raise RuntimeError(f"无法连接 CANoe 或启动测量: {e}") from e


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

    try:
        with _CANOE_LOCK:
            canoe = _get_canoe_client()
            value = canoe.get_signal_value(
                bus=BUS,
                channel=CHANNEL,
                message=MESSAGE,
                signal=signal_name,
                raw_value=False
            )
            return int(value)
    except Exception as e:
        LOGGER.exception("读取信号失败: %s", signal_name)
        print(f"读取失败: {e}")
        return -1


def get_all_light_signals() -> dict:
    """
    读取所有灯光信号的值 (使用单次连接)

    Returns:
        dict: {信号名: 值}，读取失败的信号值为 -1
    """
    with _CANOE_LOCK:
        canoe = _get_canoe_client()
        result = {}
        failed_count = 0

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
                failed_count += 1

        # 全部失败时触发会话重建，并向上抛错给 API 返回失败信息
        if failed_count == len(LIGHT_SIGNALS):
            _reset_canoe_session()
            raise RuntimeError("读取所有信号失败，请检查 CANoe 是否运行并已开始测量")

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

    with _CANOE_LOCK:
        canoe = _get_canoe_client()
        try:
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
            # 写入失败时重置会话，避免后续继续使用失效连接
            _reset_canoe_session()
            raise RuntimeError(f"设置信号失败: {e}") from e


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

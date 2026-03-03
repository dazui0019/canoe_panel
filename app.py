"""
Flask Web 服务器 - CANoe 灯光控制
"""

import os

from flask import Flask, render_template, request, jsonify
from main import set_light_signal, get_all_light_signals, LIGHT_SIGNALS

app = Flask(__name__)


def _is_true_env(value: str | None, default: bool = False) -> bool:
    """解析环境变量中的布尔值。"""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@app.route("/")
def index():
    """渲染控制页面"""
    return render_template("index.html", signals=LIGHT_SIGNALS)


@app.route("/api/get_all_signals", methods=["GET"])
def api_get_all_signals():
    """
    获取所有灯光信号状态的 API 接口

    响应 JSON:
        {
            "success": true/false,
            "signals": {
                "DaytimeLight": 0,
                "LHTrunLight": 1,
                ...
            },
            "message": "错误信息(如果失败)"
        }
    """
    try:
        signals = get_all_light_signals()
        return jsonify({
            "success": True,
            "signals": signals
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/set_signal", methods=["POST"])
def api_set_signal():
    """
    设置信号值的 API 接口

    请求 JSON:
        {
            "signal": "信号名",
            "value": 0 或 1
        }

    响应 JSON:
        {
            "success": true/false,
            "message": "错误信息(如果失败)"
        }
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "无效的请求数据"}), 400

    signal_name = data.get("signal")
    value = data.get("value")

    # 验证参数
    if signal_name is None:
        return jsonify({"success": False, "message": "缺少 signal 参数"}), 400
    if value is None:
        return jsonify({"success": False, "message": "缺少 value 参数"}), 400
    if signal_name not in LIGHT_SIGNALS:
        return jsonify({"success": False, "message": f"未知的信号: {signal_name}"}), 400
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
        return jsonify({"success": False, "message": "value 必须是整数 0 或 1"}), 400

    # 设置信号值
    try:
        success = set_light_signal(signal_name, value)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "设置信号失败，请检查 CANoe 是否正在运行"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    debug_mode = _is_true_env(os.environ.get("FLASK_DEBUG"), default=True)
    is_reloader_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    # debug 模式下仅在重载后的服务进程打印一次
    if (not debug_mode) or is_reloader_process:
        print("=" * 50, flush=True)
        print("CANoe 灯光控制 Web 服务", flush=True)
        print("=" * 50, flush=True)
        print("请确保 CANoe 已启动并加载配置", flush=True)
        print("访问 http://127.0.0.1:5000 打开控制页面", flush=True)
        print("=" * 50, flush=True)

    app.run(debug=debug_mode, host="127.0.0.1", port=5000, threaded=False)

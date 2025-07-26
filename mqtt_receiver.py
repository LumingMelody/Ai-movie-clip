import paho.mqtt.client as mqtt
import json
import logging
import threading
import time

class MQTTReceiver:
    def __init__(self, client_id, broker="121.36.203.36", port=18020, username="user", password="password"):
        # 配置日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # 使用外部传入的客户端ID
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id)

        # 设置连接参数
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password

        # 设置用户名和密码
        self.client.username_pw_set(username, password)

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        # 用于存储自定义消息处理函数
        self.message_handler = None

        # 连接状态
        self.connected = False

        # 运行标志
        self.running = False
        self.loop_thread = None

        # 当前订阅的主题
        self.current_topic = "douyin_notice/author_user_id"  # 默认主题

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        connection_results = {
            0: "连接成功",
            1: "协议版本错误",
            2: "客户端标识符无效",
            3: "服务器不可用",
            4: "用户名或密码错误",
            5: "未授权"
        }
        if rc == 0:
            self.connected = True
            self.logger.info(f"MQTT连接成功")
            # 连接成功后自动订阅当前主题
            self.subscribe(self.current_topic)
        else:
            self.connected = False
            self.logger.error(f"MQTT连接失败: {connection_results.get(rc, '未知错误')}")

    def _on_message(self, client, userdata, msg):
        """消息回调"""
        self.logger.info(f"收到消息 - 主题: {msg.topic}")

        # 解析JSON
        data = json.loads(msg.payload.decode('utf-8'))

        # 如果设置了自定义处理函数，则调用它
        if self.message_handler:
            self.message_handler(msg.topic, data)
        else:
            self.logger.info(f"消息内容: {json.dumps(data, indent=2, ensure_ascii=False)}")

    def set_message_handler(self, handler_function):
        """设置自定义消息处理函数"""
        self.message_handler = handler_function

    def subscribe(self, topic):
        """订阅主题"""
        if self.connected:
            try:
                self.client.subscribe(topic)
                self.current_topic = topic  # 更新当前主题
                self.logger.info(f"已订阅主题: {topic}")
            except Exception as e:
                self.logger.error(f"订阅主题失败: {e}")
        else:
            self.logger.warning("MQTT未连接，无法订阅主题")

    def update_topic(self, new_topic):
        """动态更新订阅的主题"""
        if self.connected:
            try:
                # 取消订阅当前主题
                self.client.unsubscribe(self.current_topic)
                # 订阅新的主题
                self.subscribe(new_topic)
                self.logger.info(f"已更新订阅主题为: {new_topic}")
            except Exception as e:
                self.logger.error(f"更新主题失败: {e}")
        else:
            self.logger.warning("MQTT未连接，无法更新主题")

    def connect(self):
        """连接到MQTT broker"""
        try:
            self.logger.info(f"使用客户端ID: {self.client_id} 连接MQTT broker")
            self.client.connect(self.broker, self.port, 60)

            # 启动网络循环
            self.running = True
            self.loop_thread = threading.Thread(target=self._loop_forever)
            self.loop_thread.daemon = True
            self.loop_thread.start()

            # 等待连接建立
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.connected:
                raise Exception("连接超时")

        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            self.connected = False

    def _loop_forever(self):
        """在单独的线程中运行网络循环"""
        try:
            while self.running:
                self.client.loop(timeout=1.0)
        except Exception as e:
            self.logger.error(f"网络循环发生错误: {e}")
        finally:
            self.logger.info("网络循环已停止")

    def disconnect(self):
        """断开连接"""
        self.running = False
        try:
            if self.loop_thread:
                self.loop_thread.join(timeout=2)
            self.client.disconnect()
            self.connected = False
            self.logger.info("已断开MQTT连接")
        except Exception as e:
            self.logger.error(f"断开连接时发生错误: {e}")


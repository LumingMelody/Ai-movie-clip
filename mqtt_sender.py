import paho.mqtt.client as mqtt
import json
import time
import logging
import random
import string


class MQTTSender:
    def __init__(self, broker, port):
        # 使用最新版本的客户端
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        # 生成随机客户端ID
        self.client_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )

        # 配置消息处理参数
        self.client.max_inflight_messages_set(20)
        self.client.max_queued_messages_set(0)

        # 设置用户名密码
        self.client.username_pw_set("user", "password")

        # 设置回调
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish

        self.broker = broker
        self.port = port
        self.connected = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """连接成功回调"""
        if rc == 0:
            print("成功连接到MQTT broker")
            self.connected = True
        else:
            print(f"连接失败，返回码: {rc}")
            self.connected = False

    def on_publish(self, client, userdata, mid, rc=None, properties=None):
        """发布消息回调"""
        if rc == 0:
            print(f"消息 {mid} 发布成功")
        else:
            print(f"消息 {mid} 发布失败，返回码: {rc}")

    def send_large_message(self, topic, message):
        try:
            # 确保连接
            if not self.connected:
                print("未连接，正在重新连接...")
                self.connect()
                time.sleep(2)  # 等待连接建立

            # 序列化消息
            payload = json.dumps(message)

            # 发送消息
            result = self.client.publish(topic, payload, qos=1)

            # 等待发布完成
            result.wait_for_publish()

            # 检查发布结果
            if result.is_published():
                print("消息发送成功")
            else:
                print("消息发送失败")

        except Exception as e:
            print(f"发送消息时出错: {e}")

    def connect(self):
        try:
            # 连接到broker
            self.client.connect(self.broker, self.port, 60)

            # 启动网络循环
            self.client.loop_start()

            # 等待连接建立
            start_time = time.time()
            while not self.connected and time.time() - start_time < 10:
                time.sleep(0.1)

            if not self.connected:
                raise Exception("连接超时")

        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            print("已断开MQTT连接")
        except Exception as e:
            print(f"断开连接时出错: {e}")


def main():
    sender = MQTTSender("121.36.203.36 ", 18020)

    try:
        # 连接到broker
        sender.connect()

        # 生成大的测试消息"""
        large_message = {
              'recordNo': 123456,
              'keywordInfo': [
                  {
                      'jobTitle': 'python',
                      'educational': '本科及以上',
                      'universities': '不限',
                      'experience': '1-3年',
                      'age': '25-30',
                      'wages': '11,15',
                      'city': '苏州'
                }
                  # {
                  #     'jobTitle': '前端开发工程师',
                  #     'educational': '本科及以上',
                  #     'universities': '不限',
                  #     'experience': '3-5年',
                  #     'age': '25-30',
                  #     'wages': '18,30'
                  # }
              ]
            }

        # 发送消息
        sender.send_large_message("expert/keyword", large_message)

        # 等待消息发送
        time.sleep(5)

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        # 断开连接
        sender.disconnect()


if __name__ == "__main__":
    main()
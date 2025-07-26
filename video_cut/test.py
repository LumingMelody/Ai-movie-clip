# -*- coding: utf-8 -*-
# @Time    : 2025/7/22 09:58
# @Author  : 蔍鸣霸霸
# @FileName: test.py
# @Software: PyCharm
# @Blog    ：只因你太美


import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:8100"
HEADERS = {"Content-Type": "application/json"}

def test_timeline_generation():
  """测试时间轴生成功能"""
  print("=== 测试时间轴生成 ===")

  # 1. 同步生成测试
  print("\n1. 测试同步生成...")
  sync_data = {
      "categoryId": "timeline_test",
      "tenant_id": "1",
      "id": "test_sync_001",
      "mode": "sync",

      "title": "人工智能科普介绍",
      "content": "这是一个介绍人工智能的科普视频，包含AI的定义、发展历程、典型应用和未来展望",
      "duration": 60,
      "platform": "B站",
      "audience": "学生",
      "style": "科技感",

      "include_subtitles": True,
      "include_logo": True,
      "include_bgm": True,
      "brand_colors": ["#0080FF", "#00D4FF"],
      "special_requirements": "需要中文字幕，科技风格音效"
  }

  response = requests.post(
      f"{BASE_URL}/video/timeline-generate",
      headers=HEADERS,
      data=json.dumps(sync_data)
  )

  if response.status_code == 200:
      result = response.json()
      print(f"✅ 同步生成成功!")
      print(f"   时间轴ID: {result.get('timeline_id')}")
      print(f"   处理时间: {result.get('processing_time')}秒")
      print(f"   轨道数量: {len(result.get('timeline_data', {}).get('timeline', {}).get('tracks', []))}")
      timeline_id = result.get('timeline_id')
  else:
      print(f"❌ 同步生成失败: {response.status_code}")
      print(response.text)
      return

  # 2. 异步生成测试
  print("\n2. 测试异步生成...")
  async_data = {
      "categoryId": "timeline_test",
      "tenant_id": "1",
      "id": "test_async_001",
      "mode": "async",

      "title": "区块链技术解析",
      "content": "深入浅出介绍区块链技术原理、应用场景和发展前景",
      "duration": 90,
      "platform": "抖音",
      "audience": "技术爱好者",
      "style": "简洁风"
  }

  response = requests.post(
      f"{BASE_URL}/video/timeline-generate",
      headers=HEADERS,
      data=json.dumps(async_data)
  )

  if response.status_code == 200:
      result = response.json()
      task_id = result.get('task_id')
      print(f"✅ 异步任务已提交!")
      print(f"   任务ID: {task_id}")

      # 轮询任务结果
      print("\n   等待任务完成...")
      for i in range(10):  # 最多等待10秒
          time.sleep(1)
          task_response = requests.get(f"{BASE_URL}/get-result/{task_id}")
          if task_response.status_code == 200:
              task_result = task_response.json()
              if task_result.get('status') == 'completed':
                  print(f"   ✅ 异步任务完成!")
                  break
              else:
                  print(f"   ⏳ 任务状态: {task_result.get('status')}")
  else:
      print(f"❌ 异步生成失败: {response.status_code}")
      print(response.text)

  # 3. 测试时间轴修改
  print("\n3. 测试时间轴修改...")
  modify_data = {
      "categoryId": "timeline_test",
      "tenant_id": "1",
      "mode": "async",
      "node_id": "node3",  # 修改内容规划节点
      "changes": {
          "content_segments": [
              "AI不仅仅是模拟人类智能",
              "更是创造全新的智能形式",
              "机器学习让AI具备自主学习能力",
              "深度学习推动了AI的快速发展",
              "让我们一起探索AI的无限可能"
          ]
      }
  }

  response = requests.post(
      f"{BASE_URL}/video/timeline-modify",
      headers=HEADERS,
      data=json.dumps(modify_data)
  )

  if response.status_code == 200:
      result = response.json()
      print(f"✅ 修改成功!")
      print(f"   修改节点: {result.get('modified_node')}")
      print(f"   影响节点: {result.get('affected_nodes')}")
  else:
      print(f"❌ 修改失败: {response.status_code}")

  # 4. 测试获取时间轴
  if timeline_id:
      print(f"\n4. 测试获取时间轴...")
      response = requests.get(f"{BASE_URL}/video/timeline/{timeline_id}")

      if response.status_code == 200:
          result = response.json()
          timeline = result.get('timeline_data', {})
          print(f"✅ 获取成功!")
          print(f"   版本: {timeline.get('version')}")
          print(f"   时长: {timeline.get('timeline', {}).get('duration')}秒")
          print(f"   分辨率: {timeline.get('timeline', {}).get('resolution')}")
      else:
          print(f"❌ 获取失败: {response.status_code}")

def test_error_cases():
  """测试错误处理"""
  print("\n=== 测试错误处理 ===")

  # 1. 缺少必要参数
  print("\n1. 测试缺少必要参数...")
  invalid_data = {
      "categoryId": "timeline_test",
      # 缺少 title
      "content": "测试内容"
  }

  response = requests.post(
      f"{BASE_URL}/video/timeline-generate",
      headers=HEADERS,
      data=json.dumps(invalid_data)
  )

  if response.status_code == 422:
      print("✅ 正确返回参数验证错误")
  else:
      print(f"❌ 错误处理异常: {response.status_code}")

  # 2. 修改不存在的节点
  print("\n2. 测试修改不存在的节点...")
  invalid_modify = {
      "categoryId": "timeline_test",
      "node_id": "non_existent_node",
      "changes": {"test": "data"}
  }

  response = requests.post(
      f"{BASE_URL}/video/timeline-modify",
      headers=HEADERS,
      data=json.dumps(invalid_modify)
  )

  if response.status_code in [400, 422, 500]:
      print("✅ 正确处理无效节点错误")
  else:
      print(f"❌ 错误处理异常: {response.status_code}")

if __name__ == "__main__":
  # 运行测试
  test_timeline_generation()
  test_error_cases()

  print("\n=== 测试完成 ===")

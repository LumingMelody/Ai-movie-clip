# Video Editor AI - DAG Based Automation

## 简介

本项目是一个基于 **DAG 的视频生成自动化系统**，支持：

- 视频剪辑流程自动化
- 支持 Prompt + Qwen API 生成 JSON
- 支持用户修改任意节点输出
- 自动识别影响节点并增量更新
- 支持 Schema 校验与失败重试

## 项目结构

详见上方项目结构图

## 依赖安装

```bash
pip install -r requirements.txt
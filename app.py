import argparse
import threading
import queue
import time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 命令行参数解析
parser = argparse.ArgumentParser(description='Run the FastAPI service with mounted folders.')
parser.add_argument('--mount', action='append', nargs=2, metavar=('NAME', 'PATH'),
                    help='Mount a folder with a name and path, e.g., --mount data /path/to/data')
args = parser.parse_args()

# 初始化FastAPI应用
app = FastAPI()

# 全局任务队列和锁
task_queue = queue.Queue()
global_lock = threading.Lock()

# 任务处理函数（示例）
def process_task(task_data):
    with global_lock:
        print(f"[{time.ctime()}] Processing task: {task_data['task_id']}")
        # 模拟耗时操作
        time.sleep(5)
        print(f"[{time.ctime()}] Task {task_data['task_id']} completed")

# 工作线程
def worker():
    while True:
        try:
            task = task_queue.get()
            process_task(task)
            task_queue.task_done()
        except Exception as e:
            print(f"Error processing task: {e}")
            task_queue.task_done()

# 启动工作线程
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

# 挂载文件夹
if args.mount:
    for name, path in args.mount:
        app.mount(f"/mnt/{name}", StaticFiles(directory=path, check_dir=True), name=name)
        print(f"Mounted folder '{name}' at /mnt/{name} (Path: {path})")

# 任务提交模型
class TaskRequest(BaseModel):
    task_id: str
    data: dict  # 可扩展的自定义数据

# 任务提交端点
@app.post("/submit-task")
async def submit_task(request: TaskRequest):
    task_queue.put(request.dict())
    return {"status": "Task submitted", "task_id": request.task_id}

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "Service is running"}

# 启动服务
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
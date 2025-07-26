# 这里可以放置工具函数，如重试、日志、格式转换等
import time

def retry(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e}, retrying in {delay} seconds...")
                    retries += 1
                    time.sleep(delay)
            return func(*args, **kwargs)  # 最后一次不捕获异常
        return wrapper
    return decorator
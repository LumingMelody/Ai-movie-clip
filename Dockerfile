FROM python:3.11-slim

# 换源 + 安装编译工具和依赖
RUN echo "deb https://mirrors.ustc.edu.cn/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y \
        git \
        cron \
        vim \
        nodejs \
        supervisor \
        gcc \
        g++ \
        python3-dev \
        make \
        libssl-dev \
        # OpenCV 依赖
        libgl1 \
        libglib2.0-0 \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# 先升级 pip 再安装依赖
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 8100
ENV PYTHONUNBUFFERED=1

CMD ["python", "/app/app.py"]
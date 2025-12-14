# 1. 使用 Debian 11 (Bullseye) 作为底座
# 这个版本的配置路径是固定的，方便我们换源
FROM python:3.9-bullseye

WORKDIR /app

# 2. 【关键一步】把下载源强行替换为阿里云
# 这能解决 apt-get update 报错 exit code 100 的问题
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 3. 安装系统依赖 (现在速度会很快)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 4. 安装 PaddleOCR 和 Flask (使用阿里云镜像加速)
# 去掉了版本号，让它自动选最合适的，防止报错
RUN pip install --no-cache-dir \
    Flask \
    paddlepaddle \
    paddleocr \
    pymupdf \
    -i https://mirrors.aliyun.com/pypi/simple/

# 5. 复制您的代码并启动
COPY app.py .
EXPOSE 8891
CMD ["python", "app.py"]
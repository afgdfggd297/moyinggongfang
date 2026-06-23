FROM python:3.11-slim

WORKDIR /app

# 系统依赖（Playwright + Pandoc）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg pandoc \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Node.js（html2ppt 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g html2ppt \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 浏览器
RUN playwright install chromium

# 应用代码
COPY . .

# 上传目录
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

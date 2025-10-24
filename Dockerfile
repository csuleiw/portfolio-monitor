# 构建阶段
FROM python:3.9-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.9-slim

RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app . .

ENV PATH=/home/app/.local/bin:$PATH
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python3", "app.py"]

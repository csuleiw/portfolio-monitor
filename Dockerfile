FROM python:3.10-slim

WORKDIR /app

COPY . .

EXPOSE 5000

RUN apk update && apk --no-cache add openssl bash curl &&\
    chmod +x app.py &&\
    pip install -r requirements.txt
    
CMD ["python3", "app.py"]

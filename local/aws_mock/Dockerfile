FROM python:3.14-slim

WORKDIR /app
COPY local/aws_mock/server.py /app/server.py

EXPOSE 8080
CMD ["python", "/app/server.py"]

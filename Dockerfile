FROM python:3.8-slim
COPY . /app
WORKDIR /app
CMD ["python", "gateway_node.py"]

FROM python:3.10-alpine
WORKDIR /app
RUN apk add --no-cache gcc musl-dev protobuf-dev python3-dev
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 50051
CMD ["python", "schedule.py"]

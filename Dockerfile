FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home hf
COPY . .
RUN mkdir -p /data && chown hf:hf /data
USER hf
ENV HF_DATA_DIR=/data
EXPOSE 8000
CMD ["waitress-serve", "--listen=0.0.0.0:8000", "wsgi:app"]

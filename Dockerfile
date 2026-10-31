FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY outputs/demo/quality_report.json ./outputs/demo/quality_report.json
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uvicorn","i29.api:app","--host","0.0.0.0","--port","8080"]

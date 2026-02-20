# Shiny for Python app (Marketstack EOD Explorer)
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py api_client.py ./

# App Platform may set PORT; default to 8000
ENV PORT=8000
EXPOSE 8000

# Run Shiny app, binding to all interfaces so the container is reachable
CMD ["sh", "-c", "shiny run --host 0.0.0.0 --port ${PORT} app.py"]

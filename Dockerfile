FROM python:3.12-slim

WORKDIR /app

# Install deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 7008
EXPOSE 9008

# Run both processes (dev-friendly)

CMD ["sh", "-c", "python api_backend.py & python frontend.py"]
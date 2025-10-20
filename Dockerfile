FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb libgtk-3-0 libx11-xcb1 libnss3 libxcomposite1 libasound2 \
    libxdamage1 libxrandr2 libpangocairo-1.0-0 libatk-bridge2.0-0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
RUN playwright install chromium firefox

COPY . .

CMD ["python", "app.py"]

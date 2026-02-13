FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for downloads if it doesn't exist
RUN mkdir -p downloads

# Expose port (EasyPanel usually uses 80 or 3000, but we'll stick to 5000 and configure it)
# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port (Documentation only, actual port determined by start.sh)
EXPOSE 80

# Command to run the application using the startup script
CMD ["./start.sh"]

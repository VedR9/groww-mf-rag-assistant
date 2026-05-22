FROM python:3.11-slim

WORKDIR /app

# Install basic build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./

# Install dependencies without cache to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# HuggingFace Spaces expects the app to run on port 7860
ENV PORT=7860
EXPOSE 7860

# Start the FastAPI backend
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]

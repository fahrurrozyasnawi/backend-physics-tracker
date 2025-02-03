# Use Python 3.8 as the base image
FROM python:3.12.2

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads

# Copy the requirements file first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

RUN pip install -e .

# Expose the port FastAPI will run on
EXPOSE 401

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "401"]

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies required for building packages like python-qpid-proton
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libssl-dev \
    libsasl2-dev \
    libqpid-proton11-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x entrypoint.sh

# Expose the port the app runs on (default is 8080)
EXPOSE 8080

# Run entrypoint.sh when the container launches
ENTRYPOINT ["./entrypoint.sh"]

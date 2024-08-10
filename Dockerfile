# Base image with Python 3.10
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Create directory for storing code files
RUN mkdir -p /app/room_code_files

# Command to run the application with Gunicorn
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:5000", "app:app", "--worker-connections", "1000", "--timeout", "120", "--log-level", "info"]

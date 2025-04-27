# Use an official Python runtime as a parent image
# Choose a version compatible with your code and App Engine runtime (e.g., 3.9, 3.10, 3.11)
FROM python:3.9-slim

# Set environment variables
# Prevents Python from writing pyc files to disc (optional)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to terminal (good for container logging)
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on.
# Cloud Run automatically provides the $PORT environment variable,
# so we don't need to hardcode it here. Gunicorn will use it.
# EXPOSE 8080 is documentary; Cloud Run manages the actual port exposure.

# Define the command to run the application using Gunicorn
# Gunicorn will listen on 0.0.0.0 and the port specified by the $PORT env var.
# Caused errors--> CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "main:app"]
CMD gunicorn --log-level=info --error-logfile=- --access-logfile=- -b 0.0.0.0:$PORT main:app
# CMD gunicorn -b 0.0.0.0:$PORT main:app
# Use official Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt



# Expose port
EXPOSE 8000

# Command to run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

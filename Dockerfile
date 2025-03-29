# Use official Python image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies and Vault
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip && \
    wget https://releases.hashicorp.com/vault/1.9.0/vault_1.9.0_linux_amd64.zip && \
    unzip vault_1.9.0_linux_amd64.zip && \
    mv vault /usr/local/bin/ && \
    rm vault_1.9.0_linux_amd64.zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /Certificate-Management

# Copy only requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Copy and make the startup script executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose the port your app runs on (if applicable)
EXPOSE 8200

# Run the startup script on container start
CMD ["/start.sh"]
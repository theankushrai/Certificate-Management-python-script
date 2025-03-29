# Use official Python image
FROM python:3.12-slim

# Set environment variables
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

# Make the startup script executable
RUN chmod +x start.sh

# Run the startup script on container start
CMD ["./start.sh"]
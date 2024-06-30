FROM python:3.11

# Update and install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-utils \
    python3 \
    python3-pip \
    git \
    p7zip-full \
    xz-utils \
    wget \
    curl \
    pv \
    jq \
    ffmpeg \
    unzip \
    neofetch \
    mediainfo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Clone the repository
RUN git clone https://github.com/Rajbhaiya/mergebot.git mergebot

# Set working directory to the cloned repository
WORKDIR mergebot

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make start.sh executable
RUN chmod +x start.sh

# Set the default command to execute when the container starts
CMD ["bash", "start.sh"]

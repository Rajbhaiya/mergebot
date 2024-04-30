FROM python:3.11

WORKDIR /usr/src/mergebot
RUN chmod 777 /usr/src/mergebot

RUN apt-get -y update && apt-get -y upgrade && apt-get install apt-utils -y && \
    apt-get install -y python3 python3-pip git \
    p7zip-full p7zip-rar xz-utils wget curl pv jq \
    ffmpeg unzip neofetch mediainfo

# RUN curl https://rclone.org/install.sh | bash

RUN git clone https://github.com/Rajbhaiya/mergebot/ mergebot

WORKDIR mergebot

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x start.sh

CMD ["bash","start.sh"]

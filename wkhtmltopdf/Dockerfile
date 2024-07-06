FROM debian:stable-slim

RUN apt update && apt -y upgrade
RUN apt install -y wget
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb
RUN apt install -y \
                fontconfig \
                libfreetype6 \
                libjpeg62-turbo \
                libpng16-16 \
                libx11-6 \
                libxcb1 \
                libxext6 \
                libxrender1 \
                xfonts-75dpi \
                xfonts-base

RUN dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb 
RUN dpkg -i wkhtmltox_0.12.5-1.buster_amd64.deb

ENTRYPOINT ["wkhtmltopdf"]

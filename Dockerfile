FROM python:3-onbuild

WORKDIR /bot
ADD . /bot
RUN echo "deb http://deb.debian.org/debian jessie-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb http://deb.debian.org/debian jessie-backports-sloppy main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y libopus0 ffmpeg
RUN export PATH=$PATH:/usr/bin

ENTRYPOINT [ "python", "bot.py" ]

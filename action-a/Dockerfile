FROM debian:9.5-slim

RUN apt update && apt upgrade -y
RUN apt install git -y

ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

FROM latonaio/l4t:latest

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=container-sweeper \
    AION_HOME=/var/lib/aion
# 1day
ENV INTERVAL_TIME_SECOND 2592000

RUN mkdir ${AION_HOME}
WORKDIR ${AION_HOME}

# Setup Directoties
RUN mkdir -p \
    $POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

ADD . .
RUN pip3 install -U pip && pip3 install -r requirement.txt

CMD ["python3", "-u", "main.py"]

FROM cytomine/software-python3-base:v2.3.1

# Create the directories
RUN mkdir -p app/

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get -y install libopenjp2-7-dev libopenjp2-tools openslide-tools

# Install tiatoolbox and pytorch and its dependencies
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Install scripts
COPY descriptor.json /app/descriptor.json
COPY run.py /app/run.py
# COPY CMU-1-Small-Region.svs /app/CMU-1-Small-Region.svs

ENTRYPOINT ["python3", "/app/run.py"]
# ENTRYPOINT ["/bin/bash"]

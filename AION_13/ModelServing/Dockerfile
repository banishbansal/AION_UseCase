FROM python:3.8-slim-buster
LABEL "usecase"="AION_13"
LABEL "usecase_test"="AION_13_test"
COPY  requirements.txt requirements.txt
COPY  config.json config.json
COPY  code.py code.py
COPY  predict.py predict.py
COPY  groundtruth.py groundtruth.py
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "code.py","-ip","0.0.0.0","-pn","8094"]

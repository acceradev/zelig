FROM python:3.6.1-alpine

ADD ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY . /app

ENV PYTHONPATH=$PYTHONPATH:/app

CMD ["python", "/app/zelig/main.py"]

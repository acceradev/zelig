FROM python:3.6.1-alpine

ADD ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "zelig/server.py"]

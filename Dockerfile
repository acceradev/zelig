FROM python:3.5

ADD ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "zelig/server.py"]

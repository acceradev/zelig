FROM python:3.6.1-alpine

ADD ./requirements.txt /zelig/requirements.txt

RUN pip install -r /zelig/requirements.txt

COPY . /zelig

ENV PYTHONPATH=$PYTHONPATH:/zelig

CMD ["python", "/zelig/zelig/main.py"]

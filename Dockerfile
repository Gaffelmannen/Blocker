FROM python:3.13.2
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5050
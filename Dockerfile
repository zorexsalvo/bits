FROM python:2.7
MAINTAINER Zorex Salvo (zsalvo@ayannah.com)

COPY requirements.txt /opt/
RUN pip install -r /opt/requirements.txt

COPY . /opt/

EXPOSE 8080

WORKDIR /opt/

CMD ["./issue_tracking/manage.py", "runserver", "0.0.0.0:8080"]



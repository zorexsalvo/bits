FROM python:2.7
MAINTAINER Zorex Salvo (zorexsalvo@gmail.com)

COPY requirements.txt /opt/
RUN pip install -r /opt/requirements.txt

COPY issue_tracking/ /opt/

WORKDIR /opt/

RUN ./manage.py collectstatic --no-input && \
    ./manage.py migrate

EXPOSE 8080

CMD ["uwsgi", "--ini", "uwsgi.ini"]

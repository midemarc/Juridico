FROM python:3.6-alpine

RUN apk add --no-cache supervisor netcat-openbsd gcc python3-dev musl-dev

RUN mkdir /backend
WORKDIR /backend
#COPY requirements.txt /backend/
RUN pip install --upgrade pip
#RUN pip install -r requirements.txt
RUN pip install Django==2.0.2
RUN pip install django-cors-headers==2.2.0
RUN pip install djangorestframework==3.7.7
RUN pip install numpy==1.14.1
RUN pip install python-dateutil==2.6.1
#RUN pip install pytz==2018.3
#RUN apk add libopenblas-dev gfortran
RUN apk add mkl-rt
RUN pip install scipy==1.0.0
RUN pip install six==1.11.0
RUN pip install treetaggerwrapper==2.2.3
RUN pip install typing==3.6.4
RUN pip install gensim==3.4.0
RUN pip install geopy==1.11.0
RUN pip install django-extensions==2.0.5
RUN pip install geoip2==2.7.0

COPY manage.py /backend/manage.py

EXPOSE 8000

COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

FROM python:3.6-alpine

RUN apk add --no-cache supervisor netcat-openbsd gcc python3-dev musl-dev
RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk add --update-cache --no-cache gfortran build-base freetype-dev openblas-dev

#RUN mkdir /backend
#RUN mkdir /backend/juridico_site/
WORKDIR /backend/juridico_site
RUN pip install --upgrade pip
COPY requirements.txt .
# RUN pip install -r requirements.txt

RUN pip install boto==2.48.0
RUN pip install boto3==1.6.17
RUN pip install botocore==1.9.17
RUN pip install bz2file==0.98
RUN pip install certifi==2018.1.18
RUN pip install chardet==3.0.4
RUN pip install Django==2.0.2
RUN pip install django-cors-headers==2.2.0
RUN pip install django-extensions==2.0.5
RUN pip install djangorestframework==3.7.7
RUN pip install docutils==0.14

RUN pip install geoip2==2.7.0
RUN pip install geopy==1.11.0
RUN pip install idna==2.6
RUN pip install jmespath==0.9.3
RUN pip install maxminddb==1.3.0
RUN pip install python-dateutil==2.6.1
RUN pip install pytz==2018.3
RUN pip install requests==2.18.4
RUN pip install s3transfer==0.1.13
RUN pip install six==1.11.0
RUN pip install smart-open==1.5.7
RUN pip install treetaggerwrapper==2.2.3
RUN pip install typing==3.6.4
RUN pip install urllib3==1.22

RUN pip install numpy==1.14.1

RUN pip install scipy==1.0.0

RUN pip install gensim==3.4.0

WORKDIR /backend/juridico_site/juridico_site

# Copy sources
COPY fake_site/ /backend/fake_site
COPY juridico_site/ /backend/juridico_site
COPY README.md /backend/README.md
COPY remplir_categories_a_partir_de_cappel.ipynb /backend/remplir_categories_a_partir_de_cappel.ipynb
COPY treetagger-install /backend/treetagger-install 


# For supervisord
RUN pip install gunicorn

EXPOSE 8000

COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

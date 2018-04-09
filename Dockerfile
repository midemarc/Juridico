FROM midemarc/scipy

WORKDIR /backend/juridico_site
COPY requirements.txt .

RUN pip install -r requirements.txt

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

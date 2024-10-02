FROM squidfunk/mkdocs-material:9

COPY requirements.txt ./

RUN pip install -r requirements.txt
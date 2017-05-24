FROM python:3
MAINTAINER Dibyo Majumdar <dibyo.majumdar@gmail.com>

COPY . mezuri
WORKDIR mezuri

RUN pip install --requirement registry/requirements.txt
ENV PYTHONPATH /mezuri

EXPOSE 8421
ENTRYPOINT ["python", "-m", "registry"]

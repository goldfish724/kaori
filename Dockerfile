FROM python:3.6-stretch

ENV workdir /kizuna

WORKDIR ${workdir}
ENV PYTHONPATH="${PYTHONPATH}:${workdir}"

RUN apt-get update \
    && apt-get install -y vim graphviz

COPY requirements.txt ${workdir}/requirements.txt
RUN pip install -r requirements.txt

ARG entry="python -u ./bot.py"
ENV entry=$entry
CMD $entry

COPY . ${workdir}

FROM python:3.12.7

RUN useradd -m -u 1000 bsw

ENV HOME=/home/bsw \
    PATH=/home/bsw/.local/bin:$PATH \
    PYTHONPATH=/home/bsw/.local/lib/python3.12/site-packages:/home/bsw/shared:/home/bsw/src \
    HF_HOME=/home/bsw/.cache/huggingface \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 

USER bsw
WORKDIR $HOME/src

COPY --chown=bsw bsw-api/requirements.txt .
RUN pip install --user -r requirements.txt

RUN python3 -c "import nltk; nltk.download('stopwords', download_dir='/home/bsw/nltk_data')"
ENV NLTK_DATA=/home/bsw/nltk_data

# Copy shared code first
COPY --chown=bsw shared/src $HOME/shared

# Copy application code
COPY --chown=bsw bsw-api/src $HOME/src

CMD ["gunicorn", "-c=gunicorn_conf.py", "main:app"]

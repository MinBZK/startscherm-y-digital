FROM python:3.12.7
RUN useradd bsw

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY annotation/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy shared code first
COPY shared/src/ /app/shared/

# Copy the application code
COPY annotation/src/ /app/src/

# Set the working directory to where the job script is located
WORKDIR /app/src
ENV PYTHONPATH=/app/src:/app/shared

RUN chown -R bsw /app/
USER bsw

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Command to run the annotation job
CMD ["python3", "jobs/annotation_job.py"] 

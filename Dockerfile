FROM apache/airflow:slim-2.11.0-python3.11

# Install system packages
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      r-base \
      libcurl4-openssl-dev \
      libssl-dev \
      libxml2-dev && \
    Rscript -e "install.packages(c('bigrquery', 'dplyr', 'tidyr', 'ggplot2', 'DBI', 'RSQLite', 'googlesheets4', 'googledrive', 'lubridate', 'data.table', 'glue','jsonlite', 'languageserver'), repos='https://cloud.r-project.org')" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the alerts package and templates
COPY alerts/ /opt/airflow/alerts/
COPY templates/ /opt/airflow/templates/
COPY setup.py ./
COPY README.md ./
COPY CHANGELOG.md ./

# Install the package in editable mode
RUN pip install --no-cache-dir -e .
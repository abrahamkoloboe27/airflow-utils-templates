FROM quay.io/astronomer/astro-runtime:13.3.0

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

USER astro
# Use the base image from Apache Airflow
FROM apache/airflow:2.10.2

# Switch to root user to install additional software
USER root

# Install Firefox and Geckodriver
RUN apt-get update && \
    apt-get install -y firefox-esr wget && \
    wget -q https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz && \
    tar -xzf geckodriver-v0.33.0-linux64.tar.gz -C /usr/local/bin/ && \
    rm geckodriver-v0.33.0-linux64.tar.gz && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the airflow user to maintain container security
USER airflow

# Install additional Python libraries
RUN pip install selenium==4.25.0 google-cloud-storage requests

# Copy a custom Airflow config file if needed
# COPY airflow.cfg /opt/airflow/airflow.cfg

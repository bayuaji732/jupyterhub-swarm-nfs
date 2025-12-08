# Define base image and ARG
ARG JUPYTERHUB_VERSION=5.4.2
FROM jupyterhub/jupyterhub:${JUPYTERHUB_VERSION}

# Install and upgrade necessary Python packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        dockerspawner==14.0.0 \
        jupyterhub==5.4.2 \
        jupyterhub-idle-culler==1.4.0

# Add configuration file
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

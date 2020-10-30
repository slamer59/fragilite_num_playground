# https://pythonspeed.com/articles/conda-docker-image-size/
# Or https://jcristharif.com/conda-docker-tips.html
# The build-stage image:
FROM continuumio/miniconda3 AS build

# Install the package as normal:
COPY environment-prod.yml .
RUN conda env create -f environment-prod.yml

# Install conda-pack:
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone enviornment
# in /venv:
RUN conda-pack -n fragil_num -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /venv/bin/conda-unpack


# Runtime image
FROM python:3.8.5-slim-stretch AS runtime

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

# Copy /venv from the previous stage:
COPY --from=build /venv /venv


# Creation of the workdir
RUN mkdir /notebooks

WORKDIR /notebooks
COPY ./notebooks/*.ipynb /

# When image is run, run the code with the environment
# activated:
SHELL ["/bin/bash", "-c"]

ENTRYPOINT source /venv/bin/activate

RUN python -m panel serve ind_frag_num_communes-mybinder.ipynb --allow-websocket-origin=*

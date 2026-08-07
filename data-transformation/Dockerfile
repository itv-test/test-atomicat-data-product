# syntax=docker/dockerfile:1
ARG BASE_REGISTRY=europe-west2-docker.pkg.dev/itv-data-platformconfig-prd/platform-base-images
FROM ${BASE_REGISTRY}/python-base-images:cortex-poetry-build-python-3.12

COPY . .
RUN poetry install --only main

USER spark

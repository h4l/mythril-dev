# syntax=docker/dockerfile:1

FROM python:3.11-slim AS generate-updated-poetry-lockfile
RUN pip install 'poetry >=1, <2'
WORKDIR /project
COPY pyproject.toml poetry.lock /project/
# Fail if the lockfile is not in sync with pyproject.toml
RUN poetry lock --check
ARG cache_invalidator
RUN poetry lock


FROM scratch AS updated-poetry-lockfile
COPY --from=generate-updated-poetry-lockfile \
  /project/poetry.lock /


FROM python:3.11-slim AS generate-updated-base-image-lockfile
COPY --from=gcr.io/go-containerregistry/crane /ko-app/crane /usr/local/bin/crane
WORKDIR /project
COPY base-images.json lock_base_images.py /project/
ARG cache_invalidator
RUN ./lock_base_images.py < base-images.json > base-images.lock


FROM scratch AS updated-base-image-lockfile
COPY --from=generate-updated-base-image-lockfile \
  /project/base-images.lock /base-images.lock

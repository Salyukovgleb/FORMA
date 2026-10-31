ARG PYTHON_IMAGE=python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
FROM ${PYTHON_IMAGE} AS build
WORKDIR /build
COPY requirements-build.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements-build.lock
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --no-build-isolation --no-deps --wheel-dir /wheels .

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-runtime.lock /tmp/requirements-runtime.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements-runtime.lock \
    && groupadd --gid 10001 forma \
    && useradd --uid 10001 --gid 10001 --no-create-home forma \
    && mkdir -p /var/lib/forma \
    && chown 10001:10001 /var/lib/forma
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-deps /wheels/*.whl && rm -r /wheels
USER 10001:10001
WORKDIR /var/lib/forma
CMD ["python", "-c", "import forma_backend; print(forma_backend.__version__)"]

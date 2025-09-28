FROM python:3.12-slim
RUN useradd -ms /bin/bash runner && mkdir -p /work && chown -R runner:runner /work
USER runner
WORKDIR /work
# No additional packages; scripts are mounted read-only at /opt/scripts
ENTRYPOINT ["/bin/bash", "-lc"]
CMD ["echo", "Runner ready"]

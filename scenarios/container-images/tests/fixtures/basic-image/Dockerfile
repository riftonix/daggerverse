FROM docker.io/alpine:3.24 AS runtime
ARG MESSAGE=hello
RUN printf '%s\n' "$MESSAGE" > /message.txt
CMD ["cat", "/message.txt"]

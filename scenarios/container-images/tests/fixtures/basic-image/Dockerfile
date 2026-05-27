FROM docker.io/alpine:3.23 AS runtime
ARG MESSAGE=hello
RUN printf '%s\n' "$MESSAGE" > /message.txt
CMD ["cat", "/message.txt"]

FROM docker.io/alpine:3.22 AS runtime

ARG MESSAGE=hello

RUN printf '%s\n' "$MESSAGE" > /message.txt

CMD ["cat", "/message.txt"]

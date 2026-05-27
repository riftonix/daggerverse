FROM alpine:3.23
ARG MESSAGE=hello
RUN printf '%s\n' "$MESSAGE" > /message.txt
CMD ["cat", "/message.txt"]

FROM alpine AS base
ARG MESSAGE=hello
RUN echo "$MESSAGE" > /message.txt

FROM base AS final
RUN echo "final" > /final.txt

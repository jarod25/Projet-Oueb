# syntax=docker/dockerfile:1.4

FROM python:3.12.3-alpine
EXPOSE 8000
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt --no-cache-dir

#COPY --from=gloursdocker/docker / /
ENV DEBUG=False
CMD ["/app/entrypoint.sh"]
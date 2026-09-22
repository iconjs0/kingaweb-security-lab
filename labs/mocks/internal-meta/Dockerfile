FROM python:3.12-alpine
WORKDIR /srv
COPY labs/mocks/internal-meta/app.py ./app.py
EXPOSE 8081
USER 65532:65532
CMD ["python", "app.py"]

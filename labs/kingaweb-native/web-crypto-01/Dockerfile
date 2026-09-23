FROM python:3.12-alpine
WORKDIR /srv
COPY labs/kingaweb-native/web-crypto-01/app.py ./app.py
COPY packages/lab-sdk/flag.py ./flag.py
EXPOSE 8080
USER 65532:65532
CMD ["python", "app.py"]

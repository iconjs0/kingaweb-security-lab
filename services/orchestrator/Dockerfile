FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV LABS_ROOT=/labs ALLOW_UNSIGNED_MANIFESTS=false ALLOW_DEV_DIGESTS=false
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

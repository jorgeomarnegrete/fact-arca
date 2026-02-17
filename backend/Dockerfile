FROM python:3.11-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi git
RUN apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info
RUN apt-get install -y swig libssl-dev
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

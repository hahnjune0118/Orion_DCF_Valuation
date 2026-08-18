FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user \
    && chown -R user:user /app

USER user

EXPOSE 7860

CMD ["marimo", "run", "orion_valuation_lab.py", "--host", "0.0.0.0", "--port", "7860"]
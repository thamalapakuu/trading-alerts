FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip

RUN pip uninstall -y telegram telegram-bot python-telegram-bot || true

RUN pip install --no-cache-dir -r requirements.txt

ENV LD_LIBRARY_PATH=/app/forexconnect/lib

CMD ["python", "bot.py"]

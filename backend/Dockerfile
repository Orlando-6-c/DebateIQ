FROM python:3.11-slim

# system deps for soundfile/audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

# HF Spaces expects the app on port 7860
ENV PORT=7860
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

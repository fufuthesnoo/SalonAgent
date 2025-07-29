FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the actual browser binaries  
RUN playwright install

COPY . .
CMD ["python", "start_runner.py"]

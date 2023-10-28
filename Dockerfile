FROM python:3.11-slim

# install git for dev purposes
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/*

WORKDIR /app
ADD ./app/ ./

RUN pip install -r requirements.txt 

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]

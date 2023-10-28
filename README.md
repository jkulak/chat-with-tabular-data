## Usage

1. `cd chat-with-tabular-data`
1. `cp .env.example .env` - copy environment file
1. [download](https://cloud.google.com/iam/docs/keys-list-get#get-key) Google Service Account key and save it as `keys/key.json`
1. fill in variables in .env
1. `cd app`
1. `docker build -t gen41/streamlit .` - build docker image
1. `docker run -ti --rm --env-file=.env -p 8501:8501 -v $(pwd)/app/keys/key.json:/app/keys/key.json gen41/streamlit` - run docker container with the app

### Development

1. `docker run -ti --rm --env-file=.env -p 8501:8501 -v $(pwd)/app:/app gen41/streamlit bash --login` - mount code directory and run bash from the docker container

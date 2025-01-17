#!/bin/sh

APP_NAME=$(basename $(pwd))

if [ $# -eq 0 ]; then
    echo "Usage: run.sh [--run (-r), --build (-b), or --test (-t)]"
    exit 1
fi

for arg in "$@"; do
    case $arg in
        --run|-r)
            docker run --rm -ti -p 8000:8000 \
                -v "$(pwd)/files:/files" \
                --env-file .env \
                $APP_NAME
            ;;
        --build|-b)
            docker build -t $APP_NAME:latest .
            ;;
        --test|-t)
            docker run -it \
                --entrypoint python3 \
                -e PYTHONPATH=/home/app/src \
                $APP_NAME \
                -m unittest discover -s tests -v
            ;;
    esac
done

#!/bin/sh

if [[ $# -eq 0 ]] ; then
    echo 'Need to provide version arg'
    exit 1
fi


docker build -t ghcr.io/psychobilly13/pdfconverter-backend:${1} --build-arg APP_TAG=${1} -f Dockerfile .
docker push ghcr.io/psychobilly13/pdfconverter-backend:${1}

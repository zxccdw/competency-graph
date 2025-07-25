#!/bin/bash

set -e

while ! curl -s http://graphdb:7200/rest/repositories > /dev/null; do
  sleep 1
done

curl -X POST -H "Content-Type: multipart/form-data" \
     -F "config=@competencies.ttl" \
     http://graphdb:7200/rest/repositories

echo "🚀 Запуск main.py..."
python main.py

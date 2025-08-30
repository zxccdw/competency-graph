#!/bin/bash

# Ждем, пока GraphDB запустится
until curl -f "http://localhost:7200/rest/repositories"; do
  echo "Waiting for GraphDB..."
  sleep 5
done

# Проверяем, существует ли репозиторий
REPO_EXISTS=$(curl -s "http://localhost:7200/rest/repositories/competencies")

if [[ $REPO_EXISTS == *"Repository not found"* ]]; then
  echo "Creating repository..."
  # Создаем репозиторий из конфигурации
  curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "config=@/opt/graphdb/home/repository-config.ttl" \
    "http://localhost:7200/rest/repositories"
  echo "Repository created"
else
  echo "Repository already exists"
fi
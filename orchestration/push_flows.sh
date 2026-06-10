#!/bin/bash
# Push all Kestra flows via API. Subflows must be imported before pipelines that reference them.

KESTRA_URL="${KESTRA_URL:-http://localhost:8082}"
KESTRA_AUTH="${KESTRA_AUTH:-admin@kestra.io:Niyctn5ma!}"
DIR="$(cd "$(dirname "$0")" && pwd)"

push() {
  local file="$DIR/$1"
  echo -n "Pushing $1 ... "
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -u "$KESTRA_AUTH" \
    -X POST "$KESTRA_URL/api/v1/flows/import" \
    -H "Content-Type: multipart/form-data" \
    -F "fileUpload=@$file")
  if [ "$status" -ge 200 ] && [ "$status" -lt 300 ]; then
    echo "OK ($status)"
  else
    echo "FAILED ($status)"
    exit 1
  fi
}

# Subflows first
push ingest.yml
push load.yml
push transform.yml

# Pipelines
push daily_etl.yml

echo "All flows pushed."

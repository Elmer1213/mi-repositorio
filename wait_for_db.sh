#!/bin/bash
set -e

host="$1"
shift
cmd="$@"

echo "Esperando a que MySQL en $host esté disponible..."

until nc -z "$host" 3306; do
  echo "Esperando a la base de datos..."
  sleep 2
done

echo "MySQL está listo. Ejecutando FastAPI..."
exec $cmd

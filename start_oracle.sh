#!/bin/bash

# Wczytaj zmienne środowiskowe z pliku .env
set -a
source .env
set +a

# Uruchom kontener
docker run -d --name oracle-db \
  -p 1521:1521 -p 5500:5500 \
  -e ORACLE_SID=$ORACLE_SID \
  -e ORACLE_PDB=$ORACLE_PDB \
  -e ORACLE_PWD=$ORACLE_PWD \
  container-registry.oracle.com/database/enterprise:latest
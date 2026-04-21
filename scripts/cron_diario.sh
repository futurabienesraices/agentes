#!/bin/bash
# Publicación automática diaria — Futura Bienes Raíces + Futura Cleaning
# Cron: 0 8 * * * /home/user/agentes/scripts/cron_diario.sh

cd /home/user/agentes

FECHA=$(date +%Y-%m-%d)
LOG="logs/cron_${FECHA}.log"

echo "=== Inicio: $(date) ===" >> "$LOG"

/usr/local/bin/python3 reporte_diario.py --publicar >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "=== OK: $(date) ===" >> "$LOG"
else
    echo "=== ERROR: $(date) ===" >> "$LOG"
fi

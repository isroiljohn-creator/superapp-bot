#!/bin/sh
# Postgres backup loop (runs in the nuvi-db-backup container).
# Every 6 hours: pg_dump (custom format) -> verify with pg_restore -l -> keep 14 days. Telegram alert on failure.
set -u
DIR=${BACKUP_DIR:-/backups}
alert() {
  [ -n "${ALERT_BOT_TOKEN:-}" ] && [ -n "${ALERT_CHAT_ID:-}" ] || return 0
  msg=$(printf '%s' "$1" | sed 's/ /%20/g')
  wget -qO- --post-data "chat_id=${ALERT_CHAT_ID}&text=${msg}" "https://api.telegram.org/bot${ALERT_BOT_TOKEN}/sendMessage" >/dev/null 2>&1 || true
}
while true; do
  ts=$(date -u +%Y%m%d-%H%M%S)
  f="$DIR/${PGDATABASE}-$ts.dump"
  if pg_dump -h "$PGHOST" -U "$PGUSER" -Fc -f "$f.tmp" "$PGDATABASE" && pg_restore -l "$f.tmp" >/dev/null 2>&1; then
    mv "$f.tmp" "$f"
    echo "backup ok: $f ($(du -h "$f" | cut -f1))"
    find "$DIR" -name '*.dump' -mtime +14 -delete
  else
    rm -f "$f.tmp"
    echo "backup FAILED at $ts"
    alert "Baza zaxira nusxasi olinmadi ($ts UTC). Serverdagi nuvi-db-backup loglarini tekshiring."
  fi
  sleep 21600
done

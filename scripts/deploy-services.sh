#!/usr/bin/env bash
# Run on the deployment host, from the checked-out release directory.
set -Eeuo pipefail
mode="${1:-preview}"
action="${2:-deploy}"
compose=(docker compose --env-file .env.production -f docker-compose.prod.yml)
legacy=(docker compose --env-file .env.production -f docker-compose.legacy.yml)
if [[ "$mode" == preview ]]; then
  compose+=(-f docker-compose.preview.yml)
  legacy+=(-f docker-compose.preview.yml)
elif [[ "$mode" != https ]]; then
  echo 'Expected preview or https' >&2; exit 1
fi
if [[ "$action" == rollback ]]; then
  test -f backups/last-backend-image
  previous=$(cat backups/last-backend-image)
  docker image inspect "$previous" >/dev/null
  "${compose[@]}" stop backend
  export YY_ROLLBACK_IMAGE="$previous"
  if docker image inspect --format '{{json .Config.Entrypoint}}' "$previous" | grep -q '"java"'; then
    "${compose[@]}" -f docker-compose.rollback.yml up -d --no-deps backend
  else
    "${legacy[@]}" -f docker-compose.rollback.yml up -d --no-deps backend
  fi
  exit
fi
[[ "$action" == deploy ]] || { echo 'Expected deploy or rollback' >&2; exit 1; }
"${compose[@]}" config -q
# Build before maintenance; no existing writer is changed if this fails.
"${compose[@]}" build backend ai-service frontend
mkdir -p backups
previous_container=$("${compose[@]}" ps -q backend)
if [[ -n "$previous_container" ]]; then
  docker inspect --format '{{.Image}}' "$previous_container" > backups/last-backend-image
fi
"${compose[@]}" stop backend
restore_on_error() {
  if [[ -s backups/last-backend-image ]]; then
    echo 'Deployment failed; restoring the previous backend image.' >&2
    bash scripts/deploy-services.sh "$mode" rollback
  fi
}
trap restore_on_error ERR
"${compose[@]}" up -d postgres redis ai-service
stamp=$(date +%Y%m%d-%H%M%S)
"${compose[@]}" exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip > "backups/database-$stamp.sql.gz"
gzip -t "backups/database-$stamp.sql.gz"
"${compose[@]}" run --rm --no-deps --entrypoint sh backend -c 'tar -czf /tmp/uploads.tar.gz -C /app/uploads .; cat /tmp/uploads.tar.gz' > "backups/uploads-$stamp.tar.gz"
gzip -t "backups/uploads-$stamp.tar.gz"
has_legacy=$("${compose[@]}" exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT to_regclass('\''public.alembic_version'\'') IS NOT NULL"')
if [[ "$has_legacy" == t ]]; then
  "${compose[@]}" run --rm --no-deps backend --spring.main.web-application-type=none --spring.flyway.enabled=false --yy.migration-action=adopt --WECHAT_ENABLED=false
fi
"${compose[@]}" up -d backend frontend
if [[ "$mode" == https ]]; then "${compose[@]}" up -d caddy; fi
healthy=false
for attempt in $(seq 1 40); do
  if "${compose[@]}" exec -T backend curl -fsS http://127.0.0.1:8001/api/v1/health >/dev/null && "${compose[@]}" exec -T frontend wget -q -O /dev/null http://127.0.0.1/healthz; then healthy=true; break; fi
  sleep 2
done
[[ "$healthy" == true ]]
trap - ERR
"${compose[@]}" ps
echo 'Deployment health checks passed. Backups are under backups/.'

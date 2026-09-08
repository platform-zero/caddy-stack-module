#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
validator="${WEBSERVICES_MODULE_CONTRACT_VALIDATOR:-}"
if [ -z "$validator" ]; then
  for candidate in     "$repo_root/../../sso-stack-generator/scripts/modules/module-contract.sh"     "$repo_root/../sso-stack-generator/scripts/modules/module-contract.sh"; do
    if [ -x "$candidate" ]; then
      validator="$candidate"
      break
    fi
  done
fi
[ -n "$validator" ] || { printf '[module-contract] set WEBSERVICES_MODULE_CONTRACT_VALIDATOR or keep sso-stack-generator next to modules workspace\n' >&2; exit 1; }
"$validator" validate "$repo_root"
caddyfile="$repo_root/stack.config/caddy/Caddyfile"
grep -Fq "spawner.{\$DOMAIN}" "$caddyfile"
grep -Fq "*.apps.{\$DOMAIN}" "$caddyfile"
grep -Fq 'keycloak_group_allow workload-spawner admins|operators' "$caddyfile"
grep -Fq "websearch.{\$DOMAIN}" "$caddyfile"
grep -Fq 'reverse_proxy searxng:8080' "$caddyfile"
donetick_block="$(sed -n '/# webservices-component-start donetick/,/# webservices-component-end donetick/p' "$caddyfile")"
grep -Fq 'reverse_proxy donetick:2021' <<<"$donetick_block"
grep -Fq 'keepalive off' <<<"$donetick_block"
matrix_rtc_block="$(sed -n '/matrix-rtc\.{$DOMAIN}/,/^}/p' "$caddyfile")"
grep -Fq 'reverse_proxy host.containers.internal:7880' <<<"$matrix_rtc_block"

# caddy stack module

- Module id: `caddy`
- Module repo: `caddy-stack-module`
- Source repo: none declared
- Lifecycle: `active`

## Owned overlays
- `stack.compose/caddy.yml`
- `stack.config/caddy`

## Dependencies
- `stack-foundation`

## Validation

```sh
./tests/validate.sh
```

## Lifecycle

`active` modules are expected to keep `stack.module.json`, owned overlays, and `tests/validate.sh` in sync.

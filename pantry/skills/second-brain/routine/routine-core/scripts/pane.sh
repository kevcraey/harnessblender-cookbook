#!/usr/bin/env bash
# pane.sh — Herdr-hulp voor de orchestrator. Houdt ochtend/avond dun: één regel per
# pane, één regel om te wachten. Zonder Herdr (HERDR_ENV != 1) geeft `spawn` exit 3,
# zodat de orchestrator terugvalt op sequentieel draaien in de eigen sessie.
#
#   pane.sh spawn <naam> <model> <prompt> [cwd]   split, start claude, stuur prompt
#   pane.sh wait <run-dir> <naam>...              wacht tot elke <naam>.done.md bestaat
#   pane.sh report <run-dir> <naam>...            print de done-bestanden na elkaar
#
# Layout: de eerste pane splitst de aanroepende pane naar rechts, elke volgende splitst
# de vorige nieuwe pane naar onder. Zo blijft de orchestrator links volledig zichtbaar.
# De laatst aangemaakte pane staat in $ROUTINE_LAST_PANE (bestand in de run-dir), want
# elke `spawn` is een apart proces.
set -euo pipefail

cmd="${1:-}"; shift || true

need_herdr() {
  if [ "${HERDR_ENV:-}" != "1" ] || ! command -v herdr >/dev/null 2>&1; then
    echo "geen Herdr: draai de sub-skills sequentieel in deze sessie" >&2
    exit 3
  fi
}

json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(eval('d'+sys.argv[1]))" "$1"; }

case "$cmd" in
  spawn)
    need_herdr
    name="$1"; model="$2"; prompt="$3"; cwd="${4:-$PWD}"
    run_dir="${ROUTINE_RUN_DIR:?ROUTINE_RUN_DIR moet gezet zijn (pad van de run-map)}"
    last_file="$run_dir/.last-pane"
    # de pane erft run-map en tokenpad via env, zodat de sub-skill niets hoeft te raden
    env=(--env "ROUTINE_RUN_DIR=$run_dir" --env "GRAPH_TOKEN_FILE=$run_dir/.gtok")
    if [ -s "$last_file" ]; then
      # volgende panes stapelen onder de vorige, niet naast de orchestrator
      out=$(herdr pane split --pane "$(cat "$last_file")" --direction down --cwd "$cwd" "${env[@]}" --no-focus)
    else
      out=$(herdr pane split --current --direction right --cwd "$cwd" "${env[@]}" --no-focus)
    fi
    pane=$(echo "$out" | json "['result']['pane']['pane_id']")
    echo "$pane" > "$last_file"
    herdr pane rename "$pane" "$name" >/dev/null 2>&1 || true
    # auto-mode: anders blijft de pane hangen op de eerste Write/Bash-bevestiging
    herdr agent start "$name" --kind claude --pane "$pane" --timeout 90000 -- \
      --model "$model" --permission-mode auto >/dev/null
    # --wait niet: de pane gaat pas 'idle' als het voorstel klaar is, en dat kan lang duren
    herdr agent prompt "$name" "$prompt" >/dev/null
    echo "$pane"
    ;;
  wait)
    run_dir="$1"; shift
    for name in "$@"; do
      until [ -f "$run_dir/$name.done.md" ]; do
        if [ "${HERDR_ENV:-}" = "1" ] && herdr agent get "$name" >/dev/null 2>&1; then
          # blokkerend wachten op een toestandswissel; time-out is geen fout, enkel een nieuwe check
          herdr agent wait "$name" --timeout 60000 >/dev/null 2>&1 || true
          # agent weg (pane gesloten) zonder done-bestand -> niet eindeloos wachten
          herdr agent get "$name" >/dev/null 2>&1 || { echo "$name: pane gesloten zonder afronding" >&2; break; }
        else
          echo "$name: geen agent en geen done-bestand" >&2; break
        fi
      done
    done
    ;;
  report)
    run_dir="$1"; shift
    for name in "$@"; do
      echo "## $name"
      if [ -f "$run_dir/$name.done.md" ]; then cat "$run_dir/$name.done.md"; else echo "_niet afgerond_"; fi
      echo
    done
    ;;
  *)
    sed -n '2,15p' "$0"; exit 2 ;;
esac

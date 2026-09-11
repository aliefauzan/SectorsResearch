#!/usr/bin/env bash
#
# KATALIS — satu simbol masuk, empat pilar keluar, tiap angka membawa field asalnya.
#
#   ./run.sh                          kartu untuk kasus demo, di atas data lokal
#   ./run.sh pilar BBCA 2026-08-14    satu simbol, satu tanggal
#   ./run.sh symbols                  apa yang bisa dinilai, dan kenapa sisanya tidak
#   ./run.sh method                   tiap ambang, batasnya, dan asalnya
#   ./run.sh test                     seluruh gate produk ini
#
# SOURCE=recorded|synth memilih lapisan data (default: recorded).
# Semua perintah di sini gratis. Tidak ada yang menyentuh API live.
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="${SOURCE:-recorded}"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }
cd "$DIR"

if [ $# -eq 0 ]; then
  echo "Kasus demo: konsentrasi di atas payload yang benar-benar dibeli."
  python3 cli.py --source recorded pilar BBCA 2026-08-14 || true
  echo
  echo "Kasus demo: empat pilar penuh, di atas 90 hari data sintetis."
  exec python3 cli.py --source synth pilar KVDN 2026-09-04
fi

case "$1" in
  test) exec python3 cli.py --source "$SOURCE" test ;;
  *)    exec python3 cli.py --source "$SOURCE" "$@" ;;
esac

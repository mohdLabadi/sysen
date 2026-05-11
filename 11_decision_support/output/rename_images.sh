#!/usr/bin/env bash
# Restore the four screenshot PNGs from their `.png.bin` staging copies.
# Run once after pulling the repo, then embed the .png files into the
# .docx submission.
set -e
cd "$(dirname "$0")"
for f in *.png.bin; do mv -v "$f" "${f%.bin}"; done

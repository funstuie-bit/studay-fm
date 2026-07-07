#!/usr/bin/env bash
# Generate a handful of original, royalty-free placeholder tracks so the demo has
# something musical to play out of the box: a gentle kalimba-style arpeggio over a
# soft pad, in a consonant pentatonic/triad shape so it reads as music rather than
# a test tone. They are deliberately simple and not the point of the project.
# Replace seed/music/ with your own tracks (or ACE-Step output).
#
# Requires ffmpeg. Committed copies already exist; run this only to regenerate.
set -euo pipefail

OUT="$(cd "$(dirname "$0")" && pwd)/music"
mkdir -p "$OUT"
D=48            # track length (seconds)
NOTE=0.60       # per-note length (seconds)

# one decaying "pluck" note (kalimba/marimba-ish): a fundamental plus two soft
# harmonics, an exponential decay, and a short tail fade so notes butt together
# without a click.  $1=freq  $2=outfile
pluck() {
  ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i "aevalsrc=exprs='(0.34*sin(2*PI*$1*t)+0.12*sin(2*PI*(2*$1)*t)+0.05*sin(2*PI*(3*$1)*t))*exp(-3.0*t)':s=44100:d=${NOTE}" \
    -af "afade=t=out:st=0.50:d=0.10" -ac 1 "$2"
}

# build one track:  $1=root(Hz)  $2="ratio ratio ..."  $3=title  $4=artist  $5=file
# the ratios are consonant intervals (major triad + octave, a couple of pentatonic
# colours), so any pattern stays pleasant.
gen() {
  local ROOT="$1" PATTERN="$2" TITLE="$3" ARTIST="$4" FILE="$5"
  local TMP; TMP="$(mktemp -d)"
  local i=0 list="$TMP/list.txt"; : > "$list"
  for r in $PATTERN; do
    local f; f=$(awk "BEGIN{printf \"%.4f\", $ROOT*$r}")
    pluck "$f" "$TMP/n$i.wav"
    echo "file '$TMP/n$i.wav'" >> "$list"
    i=$((i+1))
  done
  # phrase = the notes played in sequence
  ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$list" -c copy "$TMP/phrase.wav"
  # loop the phrase across the track and lay a soft root+fifth pad underneath, then
  # a little room reverb, a gentle low-pass, and fades in/out.
  ffmpeg -y -hide_banner -loglevel error \
    -stream_loop 40 -i "$TMP/phrase.wav" \
    -f lavfi -i "aevalsrc=exprs='(0.10*sin(2*PI*($ROOT/2)*t)+0.06*sin(2*PI*($ROOT*0.75)*t))*(0.88+0.12*sin(2*PI*0.07*t))':s=44100:d=${D}" \
    -filter_complex "[0:a]atrim=0:${D},asetpts=N/SR/TB[arp];[arp][1:a]amix=inputs=2:normalize=0:duration=first[m];[m]aecho=0.8:0.9:64:0.16,lowpass=f=3600,afade=t=in:st=0:d=2,afade=t=out:st=$((D-4)):d=4,volume=1.9[out]" \
    -map "[out]" -t "${D}" -ac 2 -c:a libmp3lame -b:a 128k \
    -metadata title="$TITLE" -metadata artist="$ARTIST" -metadata album="Studay FM Seed" \
    "$OUT/$FILE"
  rm -rf "$TMP"
  echo "  wrote $FILE  ($TITLE / $ARTIST)"
}

echo "Generating seed tracks into $OUT"
# Each is a root note plus an arpeggio pattern.  Varied roots and patterns so the
# six do not all sound alike.
gen 220.00 "1 1.25 1.5 2 1.5 1.25"        "Distant Ballroom"      "The Latent Trio" seed_01_distant_ballroom.mp3
gen 174.61 "1 1.5 1.25 1.5 2 1.5"         "Nightshift Atrium"     "Vector Choir"    seed_02_nightshift_atrium.mp3
gen 261.63 "2 1.5 1.6667 1.25 1.5 1"      "Paper Lantern Highway" "The Gradient"    seed_03_paper_lantern_highway.mp3
gen 196.00 "1 1.125 1.25 1.5 1.25 1.125"  "Slow Modem Sunrise"    "Ambient Dept."   seed_04_slow_modem_sunrise.mp3
gen 293.66 "1 1.25 1.5 1.6667 2 1.6667"   "Held Chord Society"    "Neural Sundays"  seed_05_held_chord_society.mp3
gen 164.81 "1 1.5 2 2.5 2 1.5"            "Low Battery Lullaby"   "The Overfit"     seed_06_low_battery_lullaby.mp3
echo "Done."

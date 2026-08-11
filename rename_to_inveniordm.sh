#!/usr/bin/env bash

set -euo pipefail

# Keep the source terms split so this reusable script does not itself appear in
# searches for the branding being replaced. Binary files are not rewritten.
readonly FROM_LOWER='zen''odo'
readonly FROM_UPPER='Zen''odo'
readonly FROM_CAPS='ZEN''ODO'
readonly TO_LOWER='inveniordm'
readonly TO_UPPER='InvenioRDM'
readonly TO_CAPS='INVENIORDM'
readonly REPOSITORY_ROOT="$(cd "$(dirname "$0")" && pwd -P)"
export FROM_LOWER FROM_UPPER FROM_CAPS TO_LOWER TO_UPPER TO_CAPS

# Directories with any of these names are excluded wherever they occur in the
# repository. Add or remove entries here to adjust the scope of the rename.
EXCLUDED_DIRECTORY_NAMES=(
  '.git'
  '.venv'
  '__pycache__'
  'node_modules'
  '.ipynb_checkpoints'
  '.mypy_cache'
  '.pytest_cache'
  '.ruff_cache'
)
readonly EXCLUDED_DIRECTORY_NAMES

cd "$REPOSITORY_ROOT"

# Construct one find expression so every repository scan uses exactly the same
# exclusions. The array expands to: -name .git -o -name .venv -o ...
find_exclusions=()
for excluded_name in "${EXCLUDED_DIRECTORY_NAMES[@]}"; do
  if [[ ${#find_exclusions[@]} -gt 0 ]]; then
    find_exclusions+=('-o')
  fi
  find_exclusions+=('-name' "$excluded_name")
done

# Build the complete rename list before changing anything so a path collision
# cannot leave the repository partially updated. Paths are collected from
# parents to children and renamed in reverse order below.
sources=()
destinations=()

while IFS= read -r -d '' source; do
  directory=${source%/*}
  basename=${source##*/}
  renamed_basename=${basename//$FROM_CAPS/$TO_CAPS}
  renamed_basename=${renamed_basename//$FROM_UPPER/$TO_UPPER}
  renamed_basename=${renamed_basename//$FROM_LOWER/$TO_LOWER}
  destination="$directory/$renamed_basename"

  if [[ -e "$destination" || -L "$destination" ]]; then
    printf 'Cannot rename %q to %q: destination already exists.\n' \
      "$source" "$destination" >&2
    exit 1
  fi

  sources+=("$source")
  destinations+=("$destination")
done < <(
  find . \
    -type d \( "${find_exclusions[@]}" \) -prune -o \
    \( -name "*$FROM_CAPS*" -o -name "*$FROM_UPPER*" -o \
       -name "*$FROM_LOWER*" \) -print0
)

content_count=0
while IFS= read -r -d '' file; do
  if LC_ALL=C grep -IFq \
    -e "$FROM_CAPS" -e "$FROM_UPPER" -e "$FROM_LOWER" -- "$file"; then
    perl -pi -e '
      s/\Q$ENV{FROM_CAPS}\E/$ENV{TO_CAPS}/g;
      s/\Q$ENV{FROM_UPPER}\E/$ENV{TO_UPPER}/g;
      s/\Q$ENV{FROM_LOWER}\E/$ENV{TO_LOWER}/g;
    ' -- "$file"
    content_count=$((content_count + 1))
  fi
done < <(
  find . \
    -type d \( "${find_exclusions[@]}" \) -prune -o \
    -type f -print0
)

rename_count=${#sources[@]}
for ((index = rename_count - 1; index >= 0; index--)); do
  mv -- "${sources[index]}" "${destinations[index]}"
done

printf 'Updated %d text file(s) and renamed %d path(s).\n' \
  "$content_count" "$rename_count"

#!/bin/bash
# refresh_shortcuts.sh
# Interactive checkbox UI to create symlinks for latest N55 tuning maps
#
# Controls:
#   ? / ?       Move cursor
#   Space        Toggle checkbox
#   A            Select all
#   N            Select none
#   G            Git pull then redraw
#   Enter        Confirm and create symlinks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE=".shortcuts_config.json"

config_save() {
    local items=""
    for k in "$@"; do items+="\"$k\","; done
    items="${items%,}"
    printf '{\n  "enabled": [%s]\n}\n' "$items" > "$CONFIG_FILE"
}

config_load() {
    if [[ -f "$CONFIG_FILE" ]]; then
        grep -oE '"[^"]+"' "$CONFIG_FILE" | grep -v '"enabled"' | tr -d '"' | tr '\n' ' '
    else
        echo "93 E30 E85 Flex XDF"
    fi
}

find_latest() {
    local dir="$1"
    local result
    result=$(ls "$dir"/*_LATEST.bin 2>/dev/null | head -1)
    echo "$result"
}

make_symlink() {
    local target="$1"
    local linkname="$2"
    [[ -L "$linkname" || -e "$linkname" ]] && rm -f "$linkname"
    ln -sf "$target" "$linkname"
}

if [[ "${1:-}" == "--auto" ]]; then
    for link in 93_LATEST E30_LATEST E85_LATEST Flex_LATEST XDF; do
        [[ -L "$link" ]] && rm -f "$link"
    done
    read -ra enabled <<< "$(config_load)"
    for key in "${enabled[@]}"; do
        case "$key" in
            93)   t=$(find_latest 93);   [[ -n "$t" ]] && make_symlink "$t" 93_LATEST ;;
            E30)  t=$(find_latest E30);  [[ -n "$t" ]] && make_symlink "$t" E30_LATEST ;;
            E85)  t=$(find_latest E85);  [[ -n "$t" ]] && make_symlink "$t" E85_LATEST ;;
            Flex) t=$(find_latest Flex); [[ -n "$t" ]] && make_symlink "$t" Flex_LATEST ;;
            XDF)  t=$(ls Tools/*.xdf 2>/dev/null | grep -v conflict | grep -v DEV | head -1)
                  [[ -z "$t" ]] && t=$(ls *.xdf 2>/dev/null | grep -v conflict | grep -v DEV | head -1)
                  [[ -n "$t" ]] && make_symlink "$t" XDF ;;
        esac
    done
    exit 0
fi

LABELS=("93 Octane" "E30 Ethanol" "E85 Ethanol" "Flex / Mixed" "XDF Definition")
KEYS=("93" "E30" "E85" "Flex" "XDF")
N=${#KEYS[@]}

declare -a CHECKED
prev=$(config_load)
for i in "${!KEYS[@]}"; do
    CHECKED[$i]=0
    for p in $prev; do
        [[ "$p" == "${KEYS[$i]}" ]] && CHECKED[$i]=1
    done
done

CURSOR=0
_FIRST_DRAW=1
_UI_LINES=$(( ${#LABELS[@]} + 9 ))

draw() {
    if [[ $_FIRST_DRAW -eq 0 ]]; then
        printf "\033[%dA\033[J" $_UI_LINES
    fi
    _FIRST_DRAW=0

    printf "\n"
    printf "  +-----------------------------------------+\n"
    printf "  ¦   N55 Shortcut Selector                  ¦\n"
    printf "  +-----------------------------------------¦\n"

    for i in "${!LABELS[@]}"; do
        local box="[ ]"
        [[ "${CHECKED[$i]}" -eq 1 ]] && box="[?]"
        if [[ $i -eq $CURSOR ]]; then
            printf "  ¦  \e[7m %s  %-28s\e[0m ¦\n" "$box" "${LABELS[$i]}"
        else
            printf "  ¦   %s  %-28s ¦\n" "$box" "${LABELS[$i]}"
        fi
    done

    printf "  +-----------------------------------------¦\n"
    printf "  ¦  ?? move  ·  Space toggle              ¦\n"
    printf "  ¦  A all  ·  N none  ·  G git pull       ¦\n"
    printf "  ¦  Enter ? apply & exit                  ¦\n"
    printf "  +-----------------------------------------+\n"
}

tput civis
stty -echo -icanon min 1 time 0
trap 'tput cnorm; stty echo icanon; echo ""; exit' INT TERM EXIT

draw

while true; do
    IFS= read -r -s -n1 key

    if [[ "$key" == $'\x1b' ]]; then
        IFS= read -r -s -n2 rest
        key="$key$rest"
    fi

    case "$key" in
        $'\x1b[A') (( CURSOR > 0 )) && (( CURSOR-- )) ;;
        $'\x1b[B') (( CURSOR < N-1 )) && (( CURSOR++ )) ;;
        ' ') CHECKED[$CURSOR]=$(( 1 - CHECKED[$CURSOR] )) ;;
        [Aa]) for i in "${!CHECKED[@]}"; do CHECKED[$i]=1; done ;;
        [Nn]) for i in "${!CHECKED[@]}"; do CHECKED[$i]=0; done ;;
        [Gg])
            tput cnorm; stty echo icanon
            printf "\033[%dA\033[J" $_UI_LINES
            echo "  Pulling from GitHub..."
            git -C "$SCRIPT_DIR" pull 2>&1 | sed 's/^/  /'
            echo ""
            sleep 1
            _FIRST_DRAW=1
            tput civis
            stty -echo -icanon min 1 time 0
            ;;
        '') break ;;
    esac

    draw
done

tput cnorm
stty echo icanon
printf "\033[%dA\033[J" $_UI_LINES

selected_keys=()
for i in "${!KEYS[@]}"; do
    [[ "${CHECKED[$i]}" -eq 1 ]] && selected_keys+=("${KEYS[$i]}")
done

if [[ ${#selected_keys[@]} -eq 0 ]]; then
    echo "  No shortcuts selected — nothing created."
    exit 0
fi

config_save "${selected_keys[@]}"

for link in 93_LATEST E30_LATEST E85_LATEST Flex_LATEST XDF; do
    [[ -L "$link" ]] && rm -f "$link"
done

echo "  Creating symlinks..."
echo ""

for key in "${selected_keys[@]}"; do
    case "$key" in
        93)
            t=$(find_latest 93)
            if [[ -n "$t" ]]; then make_symlink "$t" 93_LATEST; printf "  ?  93_LATEST  ?  %s\n" "$(basename "$t")"; else echo "  !  No 93 _LATEST found — run save_map.sh first"; fi ;;
        E30)
            t=$(find_latest E30)
            if [[ -n "$t" ]]; then make_symlink "$t" E30_LATEST; printf "  ?  E30_LATEST ?  %s\n" "$(basename "$t")"; else echo "  !  No E30 _LATEST found"; fi ;;
        E85)
            t=$(find_latest E85)
            if [[ -n "$t" ]]; then make_symlink "$t" E85_LATEST; printf "  ?  E85_LATEST ?  %s\n" "$(basename "$t")"; else echo "  !  No E85 _LATEST found"; fi ;;
        Flex)
            t=$(find_latest Flex)
            if [[ -n "$t" ]]; then make_symlink "$t" Flex_LATEST; printf "  ?  Flex_LATEST ?  %s\n" "$(basename "$t")"; else echo "  !  No Flex _LATEST found"; fi ;;
        XDF)
            t=$(ls Tools/*.xdf 2>/dev/null | grep -v conflict | grep -v DEV | head -1)
            [[ -z "$t" ]] && t=$(ls *.xdf 2>/dev/null | grep -v conflict | grep -v DEV | head -1)
            [[ -z "$t" ]] && t=$(ls *.xdf 2>/dev/null | head -1)
            if [[ -n "$t" ]]; then make_symlink "$t" XDF; printf "  ?  XDF  ?  %s\n" "$(basename "$t")"; else echo "  !  No XDF file found in Tools/"; fi ;;
    esac
done

echo ""
echo "  Done! Selections saved for next time."
echo ""

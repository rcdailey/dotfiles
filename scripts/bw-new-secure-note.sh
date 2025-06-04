#!/usr/bin/env bash

item="$(bw get template item)"
note="$(bw get template item.securenote)"

template="$(echo "$item" | jq -s --argjson note "$note" '.[0] * $note')"

export name="$1"
export value="$2"
# item_with_data="$(echo "$template" | jq '.name = env.name | .secureNote = env.value')"
echo "$template" | jq '.name = env.name | .secureNote = env.value'

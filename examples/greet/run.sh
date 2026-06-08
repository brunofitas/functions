echo "greeting $INPUT_NAME"
printf '{"greeting":"hello %s"}' "$INPUT_NAME" > "$FN_OUTPUTS"

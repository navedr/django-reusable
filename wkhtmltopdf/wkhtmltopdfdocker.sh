#!/bin/bash
content=""
while IFS= read -r line; do
   content+="$line"
done
echo "$content" | docker run --rm -i -v /Users/narangwa/www:/Users/narangwa/www -v /Users/narangwa/.virtualenvs:/Users/narangwa/.virtualenvs navedrangwala/wkhtmltopdf "$@"
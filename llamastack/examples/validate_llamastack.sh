#!/bin/bash

# Validate if basic functionalities like foundation & embedding model calls works

# Set Llama Stack URL and API key
LLAMASTACK_URL=""
LLAMASTACK_APIKEY=""

# Validate model list
MODELS_LIST=$(curl -s -X GET -H "Authorization: Bearer ${LLAMASTACK_APIKEY}" ${LLAMASTACK_URL}/v1/models)
echo "$MODELS_LIST"
LLM_MODEL_ID=$(echo "$MODELS_LIST" | jq -r 'first(.data[] | select(.custom_metadata.model_type == "llm") | .id)')
EMB_MODEL_ID=$(echo "$MODELS_LIST" | jq -r 'first(.data[] | select(.custom_metadata.model_type == "embedding") | .id)')

echo "LLM Model ID: ${LLM_MODEL_ID}"
echo "Embedding Model ID: ${EMB_MODEL_ID}"


# Validate foundation model call
curl -s -X POST -H "Authorization: Bearer ${LLAMASTACK_APIKEY}" -H "Content-Type: application/json" ${LLAMASTACK_URL}/v1/chat/completions \
--data @<(cat <<EOF
{
  "model": "${LLM_MODEL_ID}",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
EOF
)

echo

# Validate embedding model call
curl -s -X POST -H "Authorization: Bearer ${LLAMASTACK_APIKEY}" -H "Content-Type: application/json" ${LLAMASTACK_URL}/v1/embeddings \
--data @<(cat <<EOF
{
  "model": "${EMB_MODEL_ID}",
  "input": "Hello, how are you?"
}
EOF
)
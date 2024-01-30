import fluorite

response = fluorite.completion.create(
    fetch_attestation_insecure=True,
    model="meta-llama/Llama-2-7b-hf",
    text_input="What is machine Learning?",
    bad_words="",
    stop_words="",
    max_tokens=20,
)

print(response)

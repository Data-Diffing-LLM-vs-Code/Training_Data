from transformers.utils import logging
from transformers import pipeline
from transformers import AutoTokenizer

logging.set_verbosity_error()


fill_mask = pipeline("fill-mask", model="bert-base-uncased")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

#print(tokenizer.encode("Servas I bin da Manuel"))
#print(tokenizer.tokenize("Servas I bin da Manuelll"))

results = fill_mask(
    "exceptions, code, [MASK], codeSize, maxStackSize",
    top_k=1
)

for result in results:
    print(result["token_str"])


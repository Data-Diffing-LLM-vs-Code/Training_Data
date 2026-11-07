from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


model_name = "google/flan-t5-small"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)#.to(torch.device("cpu"))

#prompt = """
#    These are expressions of the same domain: Science Fiction, Adventure, Horror, Novels. Respond with another one.
#""".strip()

prompt="Science Fiction, Adventure, Horror, Novel, Respond with another one."

inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
output = model.generate(**inputs, max_new_tokens=1000)
result=tokenizer.decode(output[0], skip_special_tokens=True)

print(next(model.parameters()).device)
print(result)
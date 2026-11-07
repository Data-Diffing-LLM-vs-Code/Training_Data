import random
from lxml import etree
import math
from copy import deepcopy

from torch._C._functionalization import values_ViewMeta
from transformers.utils import logging
from transformers import pipeline
from transformers import AutoTokenizer

tree = etree.parse("./samples/sample_2278278.xml")
# tree = etree.parse("./samples/sample_1115373.xml")
root = tree.getroot()

logging.set_verbosity_error()

fill_mask = pipeline("fill-mask", model="bert-large-cased")
tokenizer = AutoTokenizer.from_pretrained("bert-large-cased")

# randomization represents the amount of modifications done to the xml indirectly
# to handle all sizes of files, each modification step calcs a percentage using this score as a base
randomization = random.randint(1, 20)

# removing elements

elements = root.findall(".//*")
print(f"subelements pre removal: {elements.__len__()}")

iterations = 0
for i in range(math.ceil(elements.__len__() * randomization / 1000)):  # 0,1 - 2 % of the elements
    elements = root.findall(".//*")
    element = random.choice(elements)

    # this tries to find a subelement of the already selected element. it tries this because this way the script favors
    # removing deeply nested elements. this is necessary since selecting a root-near element could cause a removal of a
    # huge chunk
    subelements = element.findall(".//*")

    if subelements:
        element = random.choice(subelements)

    print(f"removing element {tree.getpath(element)}")
    element.getparent().remove(element)

    iterations += 1

print("removing iterations: ", iterations)

# adding elements

elements = root.findall(".//*")
print(f"subelements pre addition: {elements.__len__()}")

iterations = 0
for i in range(math.ceil(elements.__len__() * randomization / 1000)):  # 0,1 - 2 % of the elements
    elements = root.findall(".//*")
    element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = element.findall(".//*")

    if subelements:
        element = random.choice(subelements)

    ########
    print(f"adding element similar to {tree.getpath(element)}")
    new_element = deepcopy(element)

    print(f"el tag: {new_element.tag}")
    print(f"attributes: {new_element.attrib}")

    for attribute in new_element.attrib:
        attr_values_list = list()

        # this retrieves a list of all the values used in the same attribute in elements with the same tag
        for el in element.getparent().findall(element.tag):
            if attribute in el.attrib: attr_values_list.append(el.attrib[attribute])
        print(f"attr list: {attr_values_list}")

        # now 6 random values are picked from the list and used to predict a new one that fits the domain
        prompt = list()
        i = 0

        while len(tokenizer.encode(", ".join(prompt))) < 300 and i < len(attr_values_list):
            prompt.append(random.choice(attr_values_list))
            i+=1

        tmp=prompt[math.floor(len(prompt)/2)]
        prompt[math.floor(len(prompt) / 2)]="[MASK]"
        prompt.append(tmp)
        prompt=", ".join(prompt)
        prompt=f"The XML values are: {prompt}"
        print(prompt)

        results = fill_mask(
            prompt,
            top_k=1
        )

        for result in results:
            print(f"############# predicted value: {result["token_str"]} for attribute {attribute}")

    iterations += 1

print("adding iterations: ", iterations)

# renaming elements

# removing properties

# adding properties

# renaming properties

# changing element text

# changing property values

# moving elements


# print(f"\n\n\n\n Modified XML: \n {etree.tostring(tree, pretty_print=True)}")

"""
when changing text the new text should make sense. thus smth similar to the original could be used or smth as unknown
"""

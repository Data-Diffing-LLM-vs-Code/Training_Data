import random
from lxml import etree
import math
import ollama


# todo check if the valid xml check also falsly claims that elements that use a namespace are invalid since they arent declared beforehand
# todo make sure to add elements after the selected element not at the end of the parent element
# todo test if continuing the same chat with the model might increase the quality of the generated elements

def is_valid_xml(xml):
    try:
        etree.fromstring(xml)
        return True
    except etree.XMLSyntaxError:
        return False


# color setup for print commands
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

# tree = etree.parse("./samples/sample_2278278.xml")
tree = etree.parse("./samples/sample_c.xml")
root = tree.getroot()

print(f"Valid input XML: {is_valid_xml(etree.tostring(root, encoding='unicode', pretty_print=True))}")

# randomization represents the amount of modifications done to the XML indirectly
# to handle all sizes of files, each modification step calcs a percentage using this score as a base

# removing elements
randomization = random.randint(1, 3)
removing_elements_iterations = 0
elements = root.findall(".//*")

# 1 - 3 % of the elements
for removing_elements_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### removing element iteration nr {removing_elements_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this tries to find a subelement of the already selected element. it tries this because this way the script favors
    # removing deeply nested elements. this is necessary since selecting a root-near element could cause a removal of a
    # huge chunk
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    print(
        f"removing element {tree.getpath(selected_element)}")
    selected_element.getparent().remove(selected_element)

# adding elements
randomization = random.randint(1, 5)
adding_elements_failed_iterations = 0
adding_elements_thinking_iterations = 0
adding_elements_iterations = 0
elements = root.findall(".//*")

# 1 - 5 % of the elements
for adding_elements_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### adding element iteration nr {adding_elements_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    print(f"adding element similar to {tree.getpath(selected_element)}")

    # this retrieves 5 elements on the same level as the selected element and converts them to one continues string
    sibling_elements_as_string = ""
    i = 0
    for el in selected_element.getparent().findall("./*"):
        if i == 5: break
        sibling_elements_as_string += etree.tostring(el, encoding='unicode', pretty_print=True).strip() + "\n"
        i += 1

    response = ollama.chat(
        model='gemma4:e2b',
        messages=[
            {
                'role': 'system',
                'content': """
                You are a precise XML generator.
                Analyze the provided sibling elements and output EXACTLY ONE single, valid XML element that could 
                sit alongside them. Output raw XML only. Ensure you close the XML-Element correctly. No markdown, 
                no multiple root elements!
                """
            },
            {
                'role': 'user',
                'content': f"""
                Here are some sibling elements for context:
                {sibling_elements_as_string}
                
                Respond with ONE single new XML element of the exact same type/structure:
                """
            }
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384}
    )
    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        adding_elements_thinking_iterations += 1
    print(f"Given elements: \n{sibling_elements_as_string}")
    print(f"Newly generated element: \n{response["message"]["content"]}")

    if not is_valid_xml(response["message"]["content"]):
        print(f"{RED}Failed generating a similar XML-Element!{RESET}")
        adding_elements_failed_iterations += 1
    else:
        print(f"{GREEN}Successfully generated a similar XML-Element!{RESET}")
        new_element = etree.fromstring(response["message"]["content"])
        selected_element.getparent().append(new_element)

# renaming elements
randomization = random.randint(1, 3)
elements = root.findall(".//*")
renaming_elements_thinking_iterations = 0
renaming_elements_failed_iterations = 0
renaming_elements_iterations = 0

# 1 - 4 % of the elements
for renaming_elements_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### renaming element iteration nr {renaming_elements_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    print(
        f"renaming element {tree.getpath(selected_element)}")

    # this retrieves 5 elements on the same level as the selected element and converts them to one continues string
    sibling_elements_as_string = ""
    i = 0
    for el in selected_element.getparent().findall("./*"):
        if i == 5: break
        sibling_elements_as_string += etree.tostring(el, encoding='unicode', pretty_print=True).strip() + "\n"
        i += 1

    response = ollama.chat(
        model='gemma4:e2b',
        messages=[
            {
                'role': 'system',
                'content': 'You are a synonym generator. Take a look at the instruction and expression given and respond with an expression that fits the same domain!'
            },
            {
                'role': 'user',
                'content': f"""
                Analyze the following XML-Element:
                {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}

                This is the XML-Elements tag:
                {selected_element.tag}
                
                Here are some sibling elements for context:
                {sibling_elements_as_string}

                Respond with a tag similar to this one. The XML-Element tag means the name of the XML-Element. Do NOT respond with the full XML-Element! If unclear read the following example:
                XML-Element:
                <user id=1>Franz Hinterbauer</user>
                
                XML-Element tag or name of XML-Element:
                user
                """
            }
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384}
    )
    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        renaming_elements_thinking_iterations += 1

    if response["message"]["content"] is None:
        print(f"{RESET}Failed renaming an element!{RESET}")
        renaming_elements_failed_iterations += 1
    else:
        print(f"Model Response: {response["message"]["content"]}")

        selected_element.tag = response["message"]["content"]

# removing attributes
randomization = random.randint(1, 3)
removing_attributes_iterations = 0

elements = root.findall(".//*")

# 1 - 3 % of the elements
for removing_attributes_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### removing attribute iteration nr {removing_attributes_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    # since some elements do not represent any valuable data without any properties, this check ensures that the selected element has at least one property
    i = 0
    while len(list(selected_element.attrib.keys())) <= 1 and i != 5:
        selected_element = random.choice(elements)
        i += 1

    if len(list(selected_element.attrib.keys())) <= 1:
        print("Didnt find an element with more than 1 properties. Skipping...")
        continue

    print(f"selected el: {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}")
    attribute_pool = list(selected_element.attrib.keys())
    print(f"attribute pool: {attribute_pool}")

    selected_attribute = random.choice(attribute_pool)

    print(f"removing attribute {selected_attribute} from element {tree.getpath(selected_element)}")
    selected_element.attrib.pop(selected_attribute)

# adding attribute
randomization = random.randint(1, 5)
adding_attributes_iterations = 0
adding_attributes_thinking_iterations = 0
adding_attributes_failed_iterations = 0

elements = root.findall(".//*")

# 1 - 5 % of the elements
for adding_attributes_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### adding attribute iteration nr {adding_attributes_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    print(f"selected el: {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}")

    response = ollama.chat(
        model='gemma4:e2b',
        messages=[
            {
                'role': 'system',
                'content': """
                You are a precise XML generator.
                Analyze the provided XML-Element and output EXACTLY ONE single attribute that fits the provided domain. 
                Respond with ONE attribute in the form of attribute=value. Do NOT Use double quotes if 
                you use a string as value. No markdown!
                """
            },
            {
                'role': 'user',
                'content': f"""
                    Analyze the following XML-Element:
                    {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}

                    Note the, if existing, attributes of the XML-Element and generate another one that fits the provided domain.
                    """
            }
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384}
    )
    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        adding_attributes_thinking_iterations += 1

    new_attribute = response["message"]["content"]

    print(f"Model Response: {new_attribute}")

    if not "=" in new_attribute or len(new_attribute.split("=")) != 2:
        print(f"{RED}Failed generating a new attribute!{RESET}")
        adding_attributes_failed_iterations += 1
        continue

    print(f"adding attribute {new_attribute} to element {tree.getpath(selected_element)}")
    selected_element.set(new_attribute.split("=")[0], new_attribute.split("=")[1].replace("\"", ""))

# renaming attributes
randomization = random.randint(1, 3)
renaming_attributes_iterations = 0
renaming_attributes_thinking_iterations = 0

elements = root.findall(".//*")

# 1 - 3 % of the elements
for renaming_attributes_iterations in range(math.ceil(elements.__len__() * randomization / 100)):
    print(f"{YELLOW}### renaming attribute iteration nr {renaming_attributes_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    i = 0
    while len(list(selected_element.attrib.keys())) == 0 and i != 5:
        selected_element = random.choice(elements)
        i += 1

    if len(list(selected_element.attrib.keys())) == 0:
        print("Didnt find an element with properties. Skipping...")
        continue

    print(f"selected el: {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}")
    attribute_pool = list(selected_element.attrib.keys())
    print(f"attribute pool: {attribute_pool}")

    selected_attribute = random.choice(attribute_pool)

    response = ollama.chat(
        model='gemma4:e2b',
        messages=[
            {
                'role': 'system',
                'content': """
                You are a precise XML generator.
                Analyze the provided XML-Element and output EXACTLY ONE single attribute that fits the provided domain. 
                Respond with ONE attribute. No markdown!
                """
            },
            {
                'role': 'user',
                'content': f"""
                    Analyze the following XML-Element:
                    {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}

                    Note this attribute:
                    {selected_element.attrib[selected_attribute]}
                    
                    Generate a synonym for the identifier of the attribute. The identifier in this case is:
                    {selected_attribute}
                    
                    ONLY generate a new identifier that fits the provided domain.
                    """
            }
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384}
    )
    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        renaming_attributes_thinking_iterations += 1

    new_attribute_identifier = response["message"]["content"]

    print(f"Model Response: {new_attribute_identifier}")

    print(f"renaming attribute {selected_attribute} to {new_attribute_identifier}")
    selected_element.set(new_attribute_identifier, selected_element.attrib.pop(selected_attribute))

# changing element text
randomization = random.randint(1, 5)
changing_text_iterations = 0
changing_text_thinking_iterations = 0
changing_text_failed_iterations = 0

elements = root.findall(".//*")

for changing_text_iterations in range(math.ceil(len(elements) * randomization / 100)):
    print(f"{YELLOW}### changing element text iteration nr {changing_text_iterations} ###{RESET}")
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    i = 0
    while (len(selected_element) > 0 or selected_element.text is None or not selected_element.text.strip()) and i < 10:
        selected_element = random.choice(elements)
        i += 1

    if not selected_element.text:
        print("Didnt find an element with text inside. Skipping...")
        continue

    old_text = selected_element.text.strip()

    print(f"changing text of {tree.getpath(selected_element)}")
    print(old_text)

    response = ollama.chat(
        model="gemma4:e2b",
        messages=[
            {
                "role": "system",
                "content": """
                    You generate replacement XML element text.
                    Return only the replacement text, with no markup or explanation.
                """
            },
            {
                "role": "user",
                "content": f"""
                Element: 
                {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}
                
                Current text:
                {old_text.strip()}
                
                Provide a plausible replacement for the current text that fits the element's meaning and context.
                """,
            },
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384},
    )

    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        changing_text_thinking_iterations += 1

    new_text = response["message"]["content"].strip()
    if new_text is None or new_text == old_text:
        print(f"{RED}Failed generating replacement text!{RESET}")
        changing_text_failed_iterations += 1
        continue

    selected_element.text = new_text
    print(f"Changed text from {old_text} to {new_text}")

# changing attribute values
randomization = random.randint(1, 5)
changing_attribute_values_iterations = 0
changing_attribute_values_thinking_iterations = 0
changing_attribute_values_failed_iterations = 0

elements = root.findall(".//*")

for changing_attribute_values_iterations in range(math.ceil(len(elements) * randomization / 100)):
    print(f"{YELLOW}### changing attribute value iteration nr {changing_attribute_values_iterations} ###{RESET}")
    eligible_elements = list()

    for el in root.findall(".//*"):
        if len(list(el.attrib)) > 0:
            eligible_elements.append(el)

    if len(eligible_elements) == 0:
        print("Didnt find an element with attributes. Skipping...")
        break

    selected_element = random.choice(eligible_elements)
    selected_attribute = random.choice(list(selected_element.attrib))
    old_value = selected_element.attrib[selected_attribute]

    print(f"""changing attribute {selected_attribute} on {tree.getpath(selected_element)}""")

    response = ollama.chat(
        model="gemma4:e2b",
        messages=[
            {
                "role": "system",
                "content": """
                    You generate replacement values for XML attributes.
                    Return only the new value, with no attribute name, quotes, markup or explanation.
                """,
            },
            {
                "role": "user",
                "content": f"""
                Element: {etree.tostring(selected_element, encoding='unicode', pretty_print=True).strip()}
                Attribute: {selected_attribute}
                Current value: {old_value}

                Provide a different plausible value that fits the attribute's meaning and context.
                """,
            },
        ],
        think=True,
        options={"temperature": 0.1, "num_ctx": 16384},
    )

    if "thinking" not in response["message"]:
        print(f"{BLUE}Model did not think{RESET}")
    else:
        print(f"{BLUE}Model thinking: {response["message"]["thinking"]}{RESET}")
        changing_attribute_values_thinking_iterations += 1

    new_value = response["message"]["content"].strip()
    if new_value is None or new_value == old_value:
        print(f"{RED}Failed generating a replacement value!{RESET}")
        changing_attribute_values_failed_iterations += 1
        continue

    selected_element.set(selected_attribute, new_value)
    print(f"Changed {selected_attribute} from {old_value} to {new_value}")

# moving elements

randomization = random.randint(1, 3)
moving_elements_iterations = 0

elements = root.findall(".//*")

for moving_elements_iterations in range(math.ceil(len(elements) * randomization / 100)):
    print(f"{YELLOW}### moving element iteration nr {moving_elements_iterations} ###{RESET}")

    eligible_elements = list()

    for el in root.findall(".//*"):
        if len(el.findall("./*")) > 1:
            eligible_elements.append(el)

    if len(eligible_elements) == 0:
        print("Didnt find an element with attributes. Skipping...")
        break

    selected_element = random.choice(eligible_elements)
    subelements = selected_element.findall("./*")

    indices = list(range(len(subelements)))
    source_index = random.choice(indices)
    print(f"source index {source_index}")
    source_element = subelements[source_index]
    print(f"source element {etree.tostring(source_element, encoding='unicode').strip()}")
    indices.remove(source_index)
    print(indices)
    target_index = random.choice(indices)
    print(f"target index {target_index}")

    selected_element.remove(source_element)
    print(f"before insertion: {selected_element.findall("./*")}")
    selected_element.insert(target_index, source_element)

    print(selected_element.findall("./*"))
    print(f"subelements: {subelements}")

print(f"""{GREEN}
Stats:

removing_elements_iterations {removing_elements_iterations}

adding_elements_iterations {adding_elements_iterations}
adding_elements_thinking_iterations {adding_elements_thinking_iterations}
adding_elements_failed_iterations {adding_elements_failed_iterations}

renaming_elements_iterations {renaming_elements_iterations}
renaming_elements_thinking_iterations {renaming_elements_thinking_iterations}
renaming_elements_failed_iterations {renaming_elements_failed_iterations}

removing_attributes_iterations {removing_attributes_iterations}

adding_attributes_iterations {adding_attributes_iterations}
adding_attribute_thinking_iterations {adding_attributes_thinking_iterations}
adding_attributes_failed_iterations {adding_attributes_failed_iterations}

renaming_attributes_iterations {renaming_attributes_iterations}
renaming_attributes_thinking_iterations {renaming_attributes_thinking_iterations}

changing_text_iterations {changing_text_iterations}
changing_text_thinking_iterations {changing_text_thinking_iterations}
changing_text_failed_iterations {changing_text_failed_iterations}

changing_attribute_values_iterations {changing_attribute_values_iterations}
changing_attribute_values_thinking_iterations {changing_attribute_values_thinking_iterations}
changing_attribute_values_failed_iterations {changing_attribute_values_failed_iterations}

{RESET}""")

with open("./samples/modified.xml", "wb") as f:
    tree = etree.fromstring(etree.tostring(tree), etree.XMLParser(remove_blank_text=True)).getroottree()
    root = tree.getroot()
    etree.indent(root, space="  ")
    tree.write_c14n(f, with_comments=False, exclusive=False)
    print(f"{GREEN}Successfully saved modified xml{RESET}")

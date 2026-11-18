import random
from lxml import etree
import math
import ollama

# todo check if the valid xml check also falsly claims that elements that use a namespace are invalid since they arent declared beforehand
# todo make sure to add elements after the selected element not at the end of the parent element
# todo test if continuing the same chat with the model might increase the quality of the generated elements


# color setup for print commands
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def is_valid_xml(xml):
    try:
        etree.fromstring(xml)
        return True
    except etree.XMLSyntaxError:
        return False


def remove_element(element):
    element.getparent().remove(element)


def add_similar_element(element):
    sibling_elements_as_string = ""

    i = 0
    for el in element.getparent().findall("./*"):
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

    if not is_valid_xml(response["message"]["content"]):
        print(f"{RED}Failed generating a similar XML-Element!{RESET}")
    else:
        print(f"{GREEN}Successfully generated a similar XML-Element!{RESET}")
        new_element = etree.fromstring(response["message"]["content"])
        parent = element.getparent()
        parent.insert(parent.index(element) + 1, new_element)

def rename_element(element):
    sibling_elements_as_string = ""

    i = 0
    for el in element.getparent().findall("./*"):
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
                {etree.tostring(element, encoding='unicode', pretty_print=True).strip()}

                This is the XML-Elements tag:
                {element.tag}
                
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

    if len(response["message"]["content"].strip()) == 0:
        print(f"{RESET}Failed renaming an element!{RESET}")
        return False

    element.tag = response["message"]["content"]
    return True


def remove_attribute(element):
    attribute_pool = list(element.attrib.keys())
    selected_attribute = random.choice(attribute_pool)

    element.attrib.pop(selected_attribute)


def add_attribute(element):
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
                    {etree.tostring(element, encoding='unicode', pretty_print=True).strip()}

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

    new_attribute = response["message"]["content"]

    print(f"Model Response: {new_attribute}")

    if not "=" in new_attribute or len(new_attribute.split("=")) != 2:
        print(f"{RED}Failed generating a new attribute!{RESET}")
        return False

    element.set(new_attribute.split("=")[0], new_attribute.split("=")[1].replace("\"", ""))
    return True


def rename_attribute(element):
    selected_attribute = random.choice(list(element.attrib.keys()))

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
                    {etree.tostring(element, encoding='unicode', pretty_print=True).strip()}

                    Note this attribute:
                    {element.attrib[selected_attribute]}
                    
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

    if len(response["message"]["content"].strip()) == 0:
        print(f"{RED}Failed generating a new attribute identifier!{RESET}")
        return False

    new_attribute_identifier = response["message"]["content"]
    element.set(new_attribute_identifier, element.attrib.pop(selected_attribute))
    return True


def change_element_text(element):
    old_text = element.text.strip()

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
                {etree.tostring(element, encoding='unicode', pretty_print=True).strip()}
                
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

    new_text = response["message"]["content"].strip()
    if new_text is None or new_text == old_text:
        print(f"{RED}Failed generating replacement text!{RESET}")
        return False

    element.text = new_text
    print(f"Changed text from {old_text} to {new_text}")
    return True


def change_attribute_value(element):
    selected_attribute = random.choice(list(element.attrib))
    old_value = element.attrib[selected_attribute]

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
                Element: {etree.tostring(element, encoding='unicode', pretty_print=True).strip()}
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

    new_value = response["message"]["content"].strip()
    if new_value is None or new_value == old_value:
        print(f"{RED}Failed generating a replacement value!{RESET}")
        return False

    element.set(selected_attribute, new_value)
    print(f"Changed {selected_attribute} from {old_value} to {new_value}")
    return True


"""
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
    source_element = subelements[source_index]
    indices.remove(source_index)
    print(indices)
    target_index = random.choice(indices)

    selected_element.remove(source_element)
    selected_element.insert(target_index, source_element)
"""


def main():
    tree = etree.parse("./samples/sample_c.xml")
    root = tree.getroot()

    if not is_valid_xml(etree.tostring(root, encoding='unicode', pretty_print=True)):
        print(f"{RED}The modified XML is not valid!{RESET}")
        return

    elements = root.findall(".//*")
    i = 0

    while i+10 < len(elements):
        eligible_elements_for_removal = list()
        eligible_elements_for_adding = list()
        eligible_elements_for_renaming = list()
        eligible_elements_for_attribute_removal = list()
        eligible_elements_for_attribute_adding = list()
        eligible_elements_for_attribute_renaming = list()
        eligible_elements_for_attribute_value_changing = list()
        eligible_elements_for_text_changing = list()

        i = i + random.randint(5, 10)
        selected_element = elements[i]
        eligible_operations = list()

        # it is assumed that any element can be renamed or feature an extra attribute
        eligible_operations.append("element_renaming")
        eligible_operations.append("attribute_adding")

        # this tries to avoid removing elements with too many child elements, which could lead to drastic changes in the structure
        # this also ensure that no element with too many child elements is copied to also not drastically change the structure
        if len(selected_element.findall(".//*"))==0:
            eligible_operations.append("element_removal")
            eligible_operations.append("element_adding")

        # any element with attributes can have its attributes removed, renamed, or have their values changed
        if len(selected_element.attrib) > 0:
            eligible_operations.append("attribute_removal")
            eligible_operations.append("attribute_renaming")
            eligible_operations.append("attribute_value_changing")

        # any element with no child element and some text can have its text changed
        if len(selected_element.findall(".//*")) == 0 and selected_element.text is not None and len(selected_element.text.strip()) > 0:
            eligible_operations.append("text_changing")

        if len(eligible_operations) == 0:
            print(f"{YELLOW}No eligible operations for element found{RESET}")
            continue

        selected_operation = random.choice(eligible_operations)

        if selected_operation == "element_removal":
            remove_element(selected_element)
        elif selected_operation == "element_adding":
            add_similar_element(selected_element)
        elif selected_operation == "element_renaming":
            rename_element(selected_element)
        elif selected_operation == "attribute_removal":
            remove_attribute(selected_element)
        elif selected_operation == "attribute_adding":
            add_attribute(selected_element)
        elif selected_operation == "attribute_renaming":
            rename_attribute(selected_element)
        elif selected_operation == "attribute_value_changing":
            change_attribute_value(selected_element)
        elif selected_operation == "text_changing":
            change_element_text(selected_element)

    with open("./samples/modified.xml", "wb") as f:
        tree = etree.fromstring(etree.tostring(tree), etree.XMLParser(remove_blank_text=True)).getroottree()
        root = tree.getroot()
        etree.indent(root, space="  ")
        tree.write_c14n(f, with_comments=False, exclusive=False)
        print(f"{GREEN}Successfully saved modified xml{RESET}")


if __name__ == "__main__":
    main()

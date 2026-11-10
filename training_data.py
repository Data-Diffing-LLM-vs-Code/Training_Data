import random
from lxml import etree
import math
import ollama


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
tree = etree.parse("./samples/sample_1115373.xml")
root = tree.getroot()

print(f"Valid input XML: {is_valid_xml(etree.tostring(root, encoding='unicode', pretty_print=True))}")

# randomization represents the amount of modifications done to the XML indirectly
# to handle all sizes of files, each modification step calcs a percentage using this score as a base
randomization = random.randint(1, 20)

# removing elements
removing_element_iterations = 0

elements = root.findall(".//*")
for removing_element_iterations in range(math.ceil(elements.__len__() * randomization / 1000)):  # 0,1 - 2 % of the elements
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this tries to find a subelement of the already selected element. it tries this because this way the script favors
    # removing deeply nested elements. this is necessary since selecting a root-near element could cause a removal of a
    # huge chunk
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    print(
        f"{YELLOW}#### removing element {tree.getpath(selected_element)} as iteration nr {removing_element_iterations} ####{RESET}")
    selected_element.getparent().remove(selected_element)

# adding elements

elements = root.findall(".//*")
adding_elements_failed_iterations = 0
adding_elements_thinking_iterations = 0
adding_elements_iterations = 0

# 0,1 - 2 % of the elements
for adding_elements_iterations in range(math.ceil(elements.__len__() * randomization / 1000)):
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    print(
        f"{YELLOW}#### adding element similar to {tree.getpath(selected_element)} as iteration nr {adding_elements_iterations} ####{RESET}")

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
        options={'temperature': 0.1}
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

elements = root.findall(".//*")
renaming_elements_thinking_iterations = 0
renaming_elements_nr_of_modified_elements = 0
renaming_elements_failed_iterations = 0
renaming_elements_iterations = 0

for renaming_elements_iterations in range(
        math.ceil(elements.__len__() * randomization / 1000)):  # 0,1 - 2 % of the elements
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    print(
        f"{YELLOW}#### renaming element {tree.getpath(selected_element)} as iteration nr {renaming_elements_iterations} ####{RESET}")

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
                {etree.tostring(selected_element, encoding='unicode', pretty_print=True)}

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
        options={'temperature': 0.1}
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
        print(f"response: \n{response["message"]["content"]}")

        for el in selected_element.getparent().findall(f".//{selected_element.tag}"):
            el.tag = response["message"]["content"]
            renaming_elements_nr_of_modified_elements += 1

        new_element = etree.fromstring(etree.tostring(selected_element, encoding='unicode', pretty_print=True))
        print(new_element)

# removing properties
removing_attribute_iterations = 0
removing_attributes_nr_of_modified_elements = 0

elements = root.findall(".//*")

# 0,1 - 2 % of the elements
for removing_attribute_iterations in range(math.ceil(elements.__len__() * randomization / 1000)):
    elements = root.findall(".//*")
    selected_element = random.choice(elements)

    # this favors selecting deeply nested elements again. the explanation for this behavior can be found in the removal section
    subelements = selected_element.findall(".//*")

    if len(subelements) > 0:
        selected_element = random.choice(subelements)

    attribute_pool = list(selected_element.attrib.keys())
    print(f"attribute pool: {attribute_pool}")

    if len(attribute_pool)>0:
        selected_attribute = random.choice(attribute_pool)

        print(
            f"{YELLOW}#### removing attribute {selected_attribute} from element {tree.getpath(selected_element)} as iteration nr {removing_attribute_iterations} ####{RESET}")
        selected_element.attrib.pop(selected_attribute)
        removing_attributes_nr_of_modified_elements+=1

# adding properties

# renaming properties

# changing element text

# changing property values

# moving elements

print(f"""{GREEN}
Stats:

removing_elements_iterations {removing_element_iterations}

adding_elements_iterations {adding_elements_iterations}
adding_elements_thinking_iterations {adding_elements_thinking_iterations}
adding_elements_failed_iterations {adding_elements_failed_iterations}

renaming_elements_iterations {renaming_elements_iterations}
renaming_elements_thinking_iterations {renaming_elements_thinking_iterations}
renaming_elements_nr_of_modified_elements {renaming_elements_nr_of_modified_elements}
renaming_elements_failed_iterations {renaming_elements_failed_iterations}

removing_attribute_iterations {removing_attribute_iterations}
removing_attributes_nr_of_modified_elements {removing_attributes_nr_of_modified_elements}
{RESET}""")

with open("./samples/modified2.xml", "wb") as f:
    tree = etree.fromstring(etree.tostring(tree), etree.XMLParser(remove_blank_text=True)).getroottree()
    tree.write_c14n(f, with_comments=False, exclusive=False)
    print(f"{GREEN}Successfully saved modified xml{RESET}")

"""
when changing text the new text should make sense. thus smth similar to the original could be used or smth as unknown
"""

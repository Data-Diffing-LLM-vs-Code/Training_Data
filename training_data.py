import random
from pathlib import Path

from lxml import etree
import ollama
import json

# color setup for print commands
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

changes = []

def is_valid_xml(xml):
    try:
        etree.fromstring(xml)
        return True
    except etree.XMLSyntaxError:
        return False


def remove_element(element):
    print("removing an element")
    element.getparent().remove(element)
    changes.append({
        "line": element.sourceline,
        "type": "removed",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0],
        "newValue": ""
    })

    print(f"removed element {element.getroottree().getpath(element)}")
    return True


def add_similar_element(element):
    print("adding an element")
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
                sit alongside them. Output raw XML only. Do NOT use namespaces in your new element! 
                Ensure you close the XML-Element correctly. No markdown, no multiple root elements!
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

    new_element = response["message"]["content"].strip()
    print(f"Model Response: {new_element}")

    try:
        parent = element.getparent()
        parent.insert(parent.index(element) + 1, etree.fromstring(new_element))

        changes.append({
            "line": element.sourceline + 1,
            "type": "added",
            "oldValue": "",
            "newValue": new_element.split("\n")[0]
        })

        print(f"{GREEN}Successfully generated a similar XML-Element!{RESET}")
        print(f"Added the following element: {element.getroottree().getpath(element)}")
        return True
    except Exception as e:
        print(f"{RED}Failed generating a similar XML-Element!{RESET}")
        print(f"{RED}Error: {e}{RESET}")
        return False


def rename_element(element):
    print("renaming an element")
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

    new_tag = response["message"]["content"].strip()

    if len(new_tag) == 0 or element.tag.strip() == new_tag:
        print(f"{RESET}Failed renaming an element!{RESET}")
        return False

    entry_opening_tag={
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    # if elements feature at least one child element, the opening and closing tag are on different lines.
    # Since renaming the opening tag causes the closing tag to also be renamed, both of these lines need to be mentioned in the changes report.
    # This if checks if a second entry in the changes report is need and if so, adds one
    element_has_children=False
    if element.find(".//*") is not None:
        element_has_children=True
        entry_closing_tag = {
            "line": element.sourceline+etree.tostring(element, encoding="unicode").count("\n")-1,
            "type": "modified",
            "oldValue": f"</{element.tag}>"
        }

    print(f"renamed element tag of {element.getroottree().getpath(element)} from {element.tag} to {new_tag}")
    element.tag = new_tag
    entry_opening_tag["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    changes.append(entry_opening_tag)

    if element_has_children:
        entry_closing_tag["newValue"] = f"</{element.tag}"
        changes.append(entry_closing_tag)

    return True


def remove_attribute(element):
    print("removing an attribute")
    attribute_pool = list(element.attrib.keys())
    selected_attribute = random.choice(attribute_pool)

    entry = {
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    element.attrib.pop(selected_attribute)
    entry["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    changes.append(entry)
    print(f"removed attribute {selected_attribute} from {element.getroottree().getpath(element)}")
    return True

def add_attribute(element):
    print("adding an attribute")
    response = ollama.chat(
        model='gemma4:e2b',
        messages=[
            {
                'role': 'system',
                'content': """
                You are a precise XML generator.
                Analyze the provided XML-Element and output EXACTLY ONE single attribute that fits the provided domain. 
                Respond with ONE attribute in the form of attribute=value. Do NOT use namespaces! Do NOT Use double quotes 
                if you use a string as value. No markdown!
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

    if not "=" in new_attribute or len(new_attribute.split("=")) != 2 or "xmlns" in new_attribute or "{" in new_attribute:
        print(f"{RED}Failed generating a new attribute!{RESET}")
        return False

    entry={
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    try:
        element.set(new_attribute.split("=")[0], new_attribute.split("=")[1].replace("\"", ""))
        entry["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
        changes.append(entry)
        print(f"added attribute {new_attribute} to element {element.getroottree().getpath(element)}")
        return True
    except ValueError:
        print(f"{RED}Failed applying the new attribute! Maybe a namespace was used since that isn't supported currently{RESET}")
        return False



def rename_attribute(element):
    print("renaming an attribute")
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

    new_attribute_identifier=response["message"]["content"].strip()

    if len(new_attribute_identifier) == 0 or "xmlns" in new_attribute_identifier or "{" in new_attribute_identifier:
        print(f"{RED}Failed generating a new attribute identifier!{RESET}")
        return False

    entry={
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    print(f"renamed attribute {selected_attribute} to {new_attribute_identifier} for element {element.getroottree().getpath(element)}")
    element.set(new_attribute_identifier, element.attrib.pop(selected_attribute))

    entry["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    changes.append(entry)
    return True


def change_element_text(element):
    print("changing an element text")
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

    entry={
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    element.text = new_text
    entry["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    changes.append(entry)

    print(f"Changed text from {old_text} to {new_text} for element {element.getroottree().getpath(element)}")
    return True


def change_attribute_value(element):
    print("changing an attribute value")
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

    entry={
        "line": element.sourceline,
        "type": "modified",
        "oldValue": etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    }

    element.set(selected_attribute, new_value)
    entry["newValue"] = etree.tostring(element, encoding='unicode').strip().split("\n")[0]
    changes.append(entry)

    print(f"Changed attribute {selected_attribute} from {old_value} to {new_value} for element {element.getroottree().getpath(element)}")
    return True


def main():
    folder = Path("samples/training_data/source")
    files = list(folder.iterdir())
    files.sort()

    for file in files:
        print(f"{RED}Current File: {file}{RESET}")

        tree = etree.parse(file)
        root = tree.getroot()

        if not is_valid_xml(etree.tostring(root, encoding='unicode', pretty_print=True)):
            print(f"{RED}The input XML is not valid!{RESET}")
            continue

        elements = root.findall(".//*")
        statistics = {
            "element_removal_successful": 0,
            "element_removal_failed": 0,
            "element_adding_successful": 0,
            "element_adding_failed": 0,
            "element_renaming_successful": 0,
            "element_renaming_failed": 0,
            "attribute_removal_successful": 0,
            "attribute_removal_failed": 0,
            "attribute_adding_successful": 0,
            "attribute_adding_failed": 0,
            "attribute_renaming_successful": 0,
            "attribute_renaming_failed": 0,
            "attribute_value_changing_successful": 0,
            "attribute_value_changing_failed": 0,
            "text_changing_successful": 0,
            "text_changing_failed": 0,
        }
        i = 0

        while i + 20 < len(elements):

            i = i + random.randint(5, 20)
            selected_element = elements[i]
            eligible_operations = list()

            # it is assumed that any element can be renamed or feature an extra attribute
            eligible_operations.append("element_renaming")
            eligible_operations.append("attribute_adding")

            # this tries to avoid removing elements with too many child elements, which could lead to drastic changes in the structure
            # this also ensure that no element with too many child elements is copied to also not drastically change the structure
            if len(selected_element.findall(".//*")) == 0:
                eligible_operations.append("element_removal")
                eligible_operations.append("element_adding")

            # any element with attributes can have its attributes removed, renamed, or have their values changed
            if len(selected_element.attrib) > 0:
                eligible_operations.append("attribute_removal")
                eligible_operations.append("attribute_renaming")
                eligible_operations.append("attribute_value_changing")

            # any element with no child element and some text can have its text changed
            if len(selected_element.findall(".//*")) == 0 and selected_element.text is not None and len(
                    selected_element.text.strip()) > 0:
                eligible_operations.append("text_changing")

            if len(eligible_operations) == 0:
                print(f"{YELLOW}No eligible operations for element found{RESET}")
                continue

            selected_operation = random.choice(eligible_operations)

            if selected_operation == "element_removal":
                is_successful = remove_element(selected_element)
            elif selected_operation == "element_adding":
                is_successful = add_similar_element(selected_element)
            elif selected_operation == "element_renaming":
                is_successful = rename_element(selected_element)
            elif selected_operation == "attribute_removal":
                is_successful = remove_attribute(selected_element)
            elif selected_operation == "attribute_adding":
                is_successful = add_attribute(selected_element)
            elif selected_operation == "attribute_renaming":
                is_successful = rename_attribute(selected_element)
            elif selected_operation == "attribute_value_changing":
                is_successful = change_attribute_value(selected_element)
            elif selected_operation == "text_changing":
                is_successful = change_element_text(selected_element)

            result = "successful" if is_successful else "failed"
            statistics[f"{selected_operation}_{result}"] += 1

        file_b = Path(f"samples/training_data/completed_samples/{file.stem}_b.xml")
        with open(file_b, "wb") as f:
            tree = etree.fromstring(etree.tostring(tree), etree.XMLParser(remove_blank_text=True)).getroottree()
            root = tree.getroot()
            etree.indent(root, space="    ")
            tree.write_c14n(f, with_comments=False, exclusive=False)
            print(f"{GREEN}Successfully saved modified xml{RESET}")

        with open(f"./samples/training_data/statistics/statistics_{file.stem}.json", "w", encoding="utf-8") as f:
            json.dump(statistics, f, indent=2)

        with open(f"./samples/training_data/completed_samples/changes_{file.stem}.json", "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=2, ensure_ascii=False)

        file.replace(f"samples/training_data/completed_samples/{file.stem}_a.xml")
        print(f"{GREEN}Successfully moved original file to completed_samples folder{RESET}")

if __name__ == "__main__":
    main()

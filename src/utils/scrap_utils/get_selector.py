def get_selector(element):
    component_type = element["component_type"]
    if component_type == "id":
        selector = f"#{element['content']}"
    elif component_type == "class":
        selector = f".{element['content']}"
    else:
        selector = element["content"]
    return selector

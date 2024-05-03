def get_selector(element):
    print('element', element)
    component_type = element['component_type']

    if component_type == 'id':
        selector = f"#{element['content']}"
    elif component_type == 'class':
        selector = f".{element['content']}"
    else:
        selector = element['content']
    print('selector', selector)
    return selector
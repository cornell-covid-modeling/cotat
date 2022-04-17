var case_numbers = source.data["case"]

for (let i = 0; i < source.data["alpha"].length; i++) {{
    source.data["alpha"][i] = {NODE_ALPHA_DEFAULT}
    source.data["size"][i] = {NODE_SIZE_DEFAULT}
}}

source.change.emit()

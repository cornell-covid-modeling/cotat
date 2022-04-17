var case_num = parseInt(this.value)
var case_numbers = source.data["case"]

if (case_numbers.includes(case_num)) {{
    var n = case_numbers.indexOf(case_num)
    for (let i = 0; i < source.data["alpha"].length; i++) {{
        if (i == n) {{
            source.data["alpha"][i] = {NODE_ALPHA_SELECTED}
            source.data["size"][i] = {NODE_SIZE_SELECTED}
        }} else {{
            source.data["alpha"][i] = {NODE_ALPHA_UNSELECTED}
            source.data["size"][i] = {NODE_SIZE_UNSELECTED}
        }}
    }}

}}

source.change.emit()

gray_list = (54, 60, 70)
x = 4
PushButtonStyle = f"""QPushButton{{
    background-color: rgb{gray_list}; 
    border-radius: {x}px;
    color: white;
    padding: 0.2em;
}}
QPushButton:pressed {{
    background-color: black;
    color: red;
}}
QPushButton:disabled {{
    background-color: gray;
    color: green;

}}"""

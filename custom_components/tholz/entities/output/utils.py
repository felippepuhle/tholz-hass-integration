def get_valid_outputs(data):
    """
    Retorna uma lista de outputs válidos.

    Cada item do retorno é uma tupla (path, state).
    """
    outputs = []

    if "outputs" in data:
        for output_key, state in data["outputs"].items():
            if state is None:
                continue
            outputs.append((["outputs", output_key], state))

    return outputs

def parse_aag(file):
    # M = maximum variable index
    # I = number of inputs
    # L = number of latches
    # O = number of outputs
    # A = number of AND gates
    header = file.readline().split()
    assert header[0] == 'aag'
    assert header[3] == '0'
    max_var = int(header[1])
    num_inputs = int(header[2])
    num_outputs = int(header[4])
    num_and_gates = int(header[5])
    lines = file.readlines()
    assert len(lines) == num_inputs + num_outputs + num_and_gates
    inputs = []
    for i in range(0, num_inputs):
        words = lines[i].split()
        assert len(words) == 1, "it is not input"
        inputs.append(int(words[0]))
    outputs = []
    for i in range(num_inputs, num_inputs + num_outputs):
        words = lines[i].split()
        assert len(words) == 1, "it is not output"
        outputs.append(int(words[0]))
    gates = dict()
    for i in range(num_inputs + num_outputs, num_and_gates + num_inputs + num_outputs):
        words = list(map(int, lines[i].split()))
        assert len(words) == 3, "it is not and gate"
        assert words[0] // 2 not in gates, "not unique gate"
        gates[words[0] // 2] = (words[1], words[2], words[0] % 2)
    return inputs, outputs, gates, max_var



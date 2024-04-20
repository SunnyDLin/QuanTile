from qu_states import QuantumBitState


# This class is an adapter for testing Qiskit-like syntax.
class QuantumCircuit:
    registers = []

    def __init__(self):
        pass

    def add_register(self, register):
        self.registers.append(register)

    def __str__(self):
        s = '['
        for i in range(len(self.registers)):
            if i != 0:
                s += ', '
            s += str(self.registers[i])
        s += ']'
        return s


# This class is an adapter for testing Qiskit-like syntax.
class QuantumRegister:
    qubits = []
    name = None

    def __init__(self, num_qubits, name='q'):
        self.name = name
        for i in range(num_qubits):
            self.qubits.append(QuantumBitState)

    def getNumQubit(self):
        return len(self.qubits)

    def __str__(self):
        return '{}({}, \'{}\')'.format(self.__class__.__name__, len(self.qubits), self.name)

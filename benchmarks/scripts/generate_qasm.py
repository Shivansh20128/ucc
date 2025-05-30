#!/usr/bin/env python
# coding: utf-8

# ### Prepare & Select
# Prepare an N-qubit GHZ state and select the all ones state.

from write_qasm import write_qasm
from cirq_circuits import VQE_ansatz, cirq_prep_select
from qiskit_circuits import qcnn_circuit, qaoa_ising_ansatz
from numpy import log2, ceil


# ### Prepare & Select
num_qubits = 25
target_state = "1" * num_qubits

circuit = cirq_prep_select(num_qubits, target_state=target_state)
filename = f"prep_select_N{num_qubits}_ghz"

write_qasm(
    circuit,
    circuit_name=filename,
    # basis_gates=['rz', 'rx', 'ry', 'h', 'cx']
)

# ### QCNN circuit
num_qubits = 10
num_layers = int(ceil(log2(num_qubits)))

seed = 12345

circuit = qcnn_circuit(num_qubits, seed=seed)
filename = f"qcnn_N{num_qubits}_{num_layers}layers"

write_qasm(
    circuit, circuit_name=filename, basis_gates=["rz", "rx", "ry", "h", "cx"]
)

# ### Parameterized VQE ansatz
num_qubits = 50
num_layers = num_qubits * 2
num_layers = num_qubits * 2

circuit = VQE_ansatz(num_qubits, num_layers)
filename = f"VQE_ansatz_N{num_qubits}_{num_layers}layers"

write_qasm(circuit, circuit_name=filename, version="3")

# ### QAOA neighest neighbors Ising mode
num_qubits = 50
num_layers = num_qubits * 3

circuit = qaoa_ising_ansatz(num_qubits, num_layers)
filename = f"QAOA_Ising_ansatz_N{num_qubits}_{num_layers}layers"

write_qasm(circuit, circuit_name=filename, version="3")

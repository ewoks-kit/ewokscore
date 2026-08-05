import time

from ewoks import load_graph
from ewoksppf.bindings import EwoksWorkflow

t0 = time.perf_counter()

ewoksgraph = load_graph("MXPressE", root_module="bes.flows")

t1 = time.perf_counter()

workflow = EwoksWorkflow(ewoksgraph)

t2 = time.perf_counter()

print("Ewoks:", t1 - t0)
print("Ppf:", t2 - t1)

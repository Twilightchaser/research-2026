# General AI workflow

1. Call `ads_status` only when ADS GUI is closed.
2. Compose one `ads_execute_plan` JSON array. Prefer absolute, user-writable
   workspace paths and explicit instance names.
3. Place schematic ports as `ads_simulation/Term`, ground their second pins,
   and add an `ads_simulation/S_Param` controller for S-parameter work.
4. Set values at placement time with the `parameters` object.
5. Add wires for presentation and deterministic labels/connectivity where
   required by the design.
6. Save and generate a netlist in the same atomic plan.
7. Inspect the netlist for shared nodes, controller settings, and units.
8. Call `ads_run_netlist`; require return code zero and a dataset.
9. Read the dataset with `keysight.ads.dataset`, calculate objective metrics,
   change parameters, and repeat. Do not claim optimization from a single run.

Example plan shape:

```json
[
  {"method":"create_workspace","params":{"path":"/absolute/path/demo_wrk"}},
  {"method":"create_library","params":{"name":"demo_lib"}},
  {"method":"create_schematic","params":{"lcv":"demo_lib:LPF:schematic"}},
  {"method":"add_instance","params":{"library":"ads_rflib","cell":"L","x":0,"y":0,"name":"L1","parameters":{"L":"2 nH"}}},
  {"method":"save_design","params":{}},
  {"method":"generate_netlist","params":{}}
]
```

The plan method names omit the public `ads_` prefix.

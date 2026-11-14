# Simulation Spec

Modules: mass, power, communications, budget, orbit, evaluator.

- mass: total = (structure + components + propellant) * (1 + margin). Compare to launch capacity.
- power: generation vs consumption; eclipse energy deficit vs battery.
- communications: max range vs required distance; link margin.
- budget: sum costs vs limit.
- orbit: Hohmann transfer delta-v and time (educational estimate).
- evaluator: aggregates checks, score, explanation.
## Relativistic Engine

This project independently evolves a one-dimensional collisionless gas in the
end-wall frame and the post-acceleration piston frame.

At matched piston events, each simulation infers an apparent bulk-average gas
ideal-gas temperature from its own simultaneous state:

```text
temperature = pressure * chamber_volume / (trapped_gas_mass * specific_gas_constant)
```

The pressure is the chamber-average longitudinal momentum flux
`sum(particle_momentum * particle_velocity) / chamber_volume`. Because this is
an observer-frame measurement, directed gas motion contributes to the result.
No bulk-motion or proper-temperature correction is applied.

Run the experiment with:

```shell
uv run python -m relativistic_engine
```

## Relativistic Engine

This project independently evolves a one-dimensional collisionless gas in the
end-wall frame and the post-acceleration piston frame.

At matched piston events, each simulation infers an apparent bulk-average gas
temperature from its own simultaneous state:

```text
T_apparent = pressure * chamber_volume / (particle_count * k_B)
```

The pressure is the chamber-average longitudinal momentum flux
`sum(particle_momentum * particle_velocity) / chamber_volume`. Because this is
an observer-frame measurement, directed gas motion contributes to the result.
It is intentionally distinct from a proper temperature measured in the gas's
comoving frame.

Run the experiment with:

```shell
uv run python -m relativistic_engine
```

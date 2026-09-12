Design a clean, educational Python experiment for a hypothetical relativistic piston engine. The purpose is to test whether independently evolving the same physical engine from two relativistic reference frames can ever produce different material states or irreversible outcomes.

The experiment should be treated as an exploratory numerical test. Do NOT assume ahead of time that the frames must agree, and do NOT force their final states to match. Likewise, do not deliberately insert an inconsistent rule merely to manufacture disagreement. Every assumption should be explicit.

Physical setup

Use normalized units initially:

speed_of_light = 1.0
initial_chamber_length = 10.0
cross_sectional_area = 1.0


The engine consists of:

A sealed one-dimensional chamber.

A fixed end wall on the right.

A piston on the left.

Gas trapped between the piston and the end wall.

The piston moves toward the end wall at a relativistic speed.

Use:

piston_speed = 0.95 * speed_of_light


in the chamber/end-wall rest frame.

At the initial wall-frame state:

PISTON                                      END WALL
|                                              |
|<---------------- gas ----------------------->|
|                                              |

x = 0                                        x = 10

piston velocity = +0.95c
end-wall velocity = 0


The piston physically compresses the gas as it travels toward the wall.

The two frames

There should be exactly two primary simulations.

Frame A — chamber/end-wall frame

The end wall is stationary.

end_wall_velocity = 0
piston_velocity = +0.95


Frame B — piston frame

The piston is stationary.

The end wall and chamber move toward the piston according to the relativistic velocity transformation.

piston_velocity = 0
end_wall_velocity = transformed_value


Frame B should genuinely be the piston's rest frame — not an arbitrary third observer moving at some unrelated velocity.

Critical experimental requirement

Treat Frame A and Frame B as independent forward-running simulations.

Conceptually:

wall_frame_engine = Engine(...)
piston_frame_engine = Engine(...)

wall_frame_engine.run()
piston_frame_engine.run()


Each simulation must maintain its own:

particle_positions
particle_velocities
particle_momenta
particle_energies

piston_position
piston_velocity

wall_position
wall_velocity

gas_density
gas_energy_density
gas_stress
gas_pressure

internal_energy
temperature_estimates

engine_state


Do NOT evolve Frame A and then merely Lorentz-transform its completed states to produce Frame B.

Lorentz transformations may be used to create physically equivalent initial conditions and later to compare matching physical events, but Frame B must calculate its subsequent collisions and material evolution independently.

Do not copy pressures, collisions, temperatures, ignition states, or other results from one simulation into the other.

Simultaneity

Be extremely explicit about simultaneity.

Each frame should construct its own simultaneous spatial snapshots.

For example:

frame_a.snapshot_at(frame_a_time)

frame_b.snapshot_at(frame_b_time)


Do not pretend that one frame's simultaneous spatial slice is automatically simultaneous in the other frame.

Whenever comparing snapshots, explain exactly which physical event anchors the comparison.

Prefer matching the simulations using a clearly identifiable event such as:

the piston has completed X% of its journey


or:

a specified event occurs on the end wall


Then allow each frame to construct its own simultaneous state through that event.

Gas model

Start with a simple gas model that is still capable of actual material evolution.

Use at least 1,000 particles.

Each particle should track:

position
velocity
momentum
energy


Particles should bounce from the piston and wall.

The moving piston must be capable of doing work on the gas and increasing particle energy.

If practical, add particle-particle collisions so that the gas can redistribute energy and approach thermal equilibrium. If this makes the first implementation too complicated, make it a clearly separated second version.

Keep the code readable and educational.

Prefer descriptive classes such as:

class Particle:
    ...

class Wall:
    ...

class Piston:
    ...

class Gas:
    ...

class ReferenceFrame:
    ...

class Engine:
    ...


Avoid clever abstractions and dense mathematical notation.

Measurements

At several matched stages of compression, independently measure in EACH frame:

Geometry

piston position
end-wall position
simultaneous chamber length
chamber volume


Density

number_density = particle_count / simultaneous_volume


Report both chamber-average density and local spatial-bin densities.

Particle state

Report:

mean particle velocity
velocity distribution
mean momentum
momentum distribution
mean particle energy
energy distribution


Energy density

Calculate:

energy_density = total_particle_energy / simultaneous_volume


Do this using each frame's own simultaneous particle state.

Gas stress / momentum flow

Calculate the average x-direction momentum flow throughout the gas.

Explain this in plain English rather than relying on tensor notation.

Conceptually:

average_gas_stress = sum(
    particle.momentum * particle.velocity
    for particle in particles
) / chamber_volume


Also calculate it locally in spatial bins.

Wall pressure

Separately calculate actual mechanical loading on the end wall:

wall_pressure = (
    momentum_transferred_to_wall
    / elapsed_time
    / wall_area
)


Keep this separate from chamber-average gas stress.

Temperature

Calculate several clearly labeled temperature-like quantities rather than silently choosing one definition.

At minimum calculate:

A frame-native value inferred naively from that frame's measured pressure/stress and number density:

frame_native_temperature_like_value = (
    measured_pressure_or_stress
    / number_density
)


with k_B = 1.

A thermal/internal temperature estimate obtained after removing the common bulk motion of the gas and looking at the random particle motion.

Clearly explain why these may differ.

Do not simply declare one of them "the real temperature" without showing the calculation.

Irreversible outcomes

The purpose of the experiment is ultimately to determine whether frame-dependent material properties can produce different timelines.

Add one or more irreversible engine-state transitions.

Candidates include:

ignition
wall rupture
piston stall
valve activation
phase transition
chemical reaction
thermal runaway


For each threshold mechanism, explicitly state which measured physical quantity causes it.

Example:

if density >= critical_density:
    ignition = True


or:

if local_pressure >= wall_failure_pressure:
    wall_broken = True


or:

if temperature >= ignition_temperature:
    ignited = True


Once triggered, the state should remain triggered and should alter subsequent simulation behavior if practical.

For example:

if engine.ignited:
    released_energy += combustion_energy

if wall.broken:
    gas_can_escape = True


This turns a small difference into a genuine divergent timeline if one exists.

Do not privilege a frame during runtime

This is critical.

Do NOT write code resembling:

# We are running the piston-frame simulation,
# but convert everything back to the wall frame
# before deciding what happens.

wall_frame_energy = transform_to_wall_frame(...)

if wall_frame_energy > threshold:
    ignite()


That may be useful as a separate relativistic consistency calculation, but it defeats the purpose of the primary experiment.

The primary experiment asks:

If each frame independently evolves the physical quantities it assigns to the engine, what state does that calculation produce?

If a material rule truly requires a local-rest-frame quantity, calculate that quantity within the current simulation from the complete local states of the interacting objects, rather than switching the entire simulation into another frame.

For example, Frame B should be capable of calculating the interaction between a stationary piston and a moving wall entirely using Frame B's variables.

Do not hard-code frame agreement

Never write logic equivalent to:

assert frame_a.ignition == frame_b.ignition


unless it is purely a post-experiment diagnostic.

Likewise, do not replace one frame's calculated result with the other's result.

If a mathematical identity guarantees agreement for a particular measurement, show exactly why.

For example:

quantity A increases by factor X
quantity B increases by factor X
therefore A / B remains unchanged


Distinguish clearly between:

agreement that emerges numerically,

agreement mathematically forced by an explicitly chosen interaction law,

agreement imposed by the code.

That distinction is central to the experiment.

Conservation bookkeeping

Where practical, make the system closed.

Track:

gas energy
gas momentum
piston energy
piston momentum
wall energy
wall momentum
internal/thermal energy


If the piston is externally powered or the wall is externally held stationary, explicitly track the work or momentum supplied/removed by that external mechanism.

Do not allow energy or momentum to disappear into an unspecified constraint.

Print a conservation report for each frame.

Extended matter

After the simple gas version works, create a second experiment with an extended deformable object or fluid.

Do not model an extended object as if its entire state changes at one instant.

Represent it as spatial cells, for example:

[cell][cell][cell][cell][cell]...


Each cell may contain:

position
velocity
density
compression
internal_energy
temperature
stress
damage


Changes must propagate between neighboring cells at finite speed.

This version should test whether differing simultaneous shapes, densities, stresses, and temperatures between frames can feed back into later evolution.

Output

Print the two simulations side by side.

Something like:

RELATIVISTIC ENGINE TEST
========================

                         WALL FRAME       PISTON FRAME
------------------------------------------------------
chamber length             ...
gas density                ...
energy density             ...
average gas stress         ...
end-wall pressure          ...
mean particle energy       ...
thermal energy             ...
temperature estimate       ...

IGNITED                    TRUE/FALSE      TRUE/FALSE
WALL BROKEN                TRUE/FALSE      TRUE/FALSE
PISTON STALLED             TRUE/FALSE      TRUE/FALSE


Also print the evolution over time so that we can determine where two histories first begin to differ.

If the outcomes agree, identify the exact mechanism or mathematical cancellation that caused them to agree.

If the outcomes disagree, identify the first state variable or interaction at which the histories diverged.

Do not dismiss disagreement merely by saying "relativity requires the outcomes to agree." Trace the actual calculation.

Scientific goal

We are testing the following proposition:

Relativity allows different reference frames to assign different simultaneous geometries, densities, energies, momentum distributions, stresses, and other material properties to the same evolving engine. Are the relativistic transformation and interaction rules sufficient to guarantee that independently evolving those states can never produce different irreversible physical outcomes?

A single genuine case in which equivalent initial physical conditions produce:

Frame A:
    engine survives

Frame B:
    engine fails


would be extremely significant.

Conversely, if all tested cases converge, identify precisely what local or global mathematical structure prevents divergence.

Treat either result as interesting.

Do not assume the answer before running the experiment.

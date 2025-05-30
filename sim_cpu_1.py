import genesis as gs
import csv
import os

# --- Output file setup ---
output_file = "fluid_state_log_2.csv"
# Overwrite if exists
if os.path.exists(output_file):
    os.remove(output_file)

# Write CSV header
with open(output_file, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['step', 'particle_id', 'x', 'y', 'z', 'vx', 'vy', 'vz'])

# --- Genesis initialization and scene setup ---
gs.init(backend=gs.cpu, debug=False, precision='32')

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=4e-3, substeps=4), # It was 10
    sph_options=gs.options.SPHOptions(
        lower_bound=(0.0, -25.0, -25.0),
        upper_bound=(10.0, 10.0, 0.5),
        particle_size=0.1, # It was 0.05
    ),
    vis_options=gs.options.VisOptions(visualize_sph_boundary=True),
    show_viewer=True #False in case I dont want to see the scene
)

# --- Terrain setup ---

# terrain = scene.add_entity(
#     morph=gs.morphs.Terrain(
#         n_subterrains=(1, 1),
#         subterrain_size=(10.0, 10.0),
#         subterrain_types='sloped_terrain',
#         horizontal_scale=0.25,
#         vertical_scale=0.05,
#         randomize=False
#     ),
#     surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)
#     ),
# )     

terrain = scene.add_entity(
    morph=gs.morphs.Terrain(
        n_subterrains=(1, 2),  # 2 subterrain in orizzontale
        subterrain_size=(10.0, 10.0),  # ognuno 10x10 (totale 20x10)
        subterrain_types=[['flat_terrain', 'sloped_terrain']],  # primo flat, secondo slope
        horizontal_scale=0.25,
        vertical_scale=0.05,
        randomize=False
    ),
    surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
)

# --- Fluid block initialization ---
water_block = scene.add_entity(
    material=gs.materials.SPH.Liquid(sampler='pbs'), #|[WARNING] `pbs` sampler failed. Falling back to `random` sampler| this happens every time on my pc.
    morph=gs.morphs.Box(
        pos=(1.0, 5.0, 0.30),
        size=(0.2, 0.2, 0.2) 
    ),
    surface=gs.surfaces.Default(color=(0.4, 0.8, 1.0), vis_mode='particle')
)

scene.build()

# --- Simulation parameters ---
simulation_steps = int(10.0 / scene.sim_options.dt) #it was 30.0 for more simulation steps 
output_interval = 250 #how often it takes a particles snapshot

# --- Simulation loop with state export ---
for i in range(simulation_steps):
    scene.step()

    if i % output_interval == 0:
        state = water_block.get_state()
        print(state)
        positions = state.pos
        velocities = state.vel
        num_particles = len(positions)

        # Append to CSV
        with open(output_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            for pid in range(num_particles):
                pos = positions[pid]
                vel = velocities[pid]
                row = [i, pid, pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]]
                writer.writerow(row)


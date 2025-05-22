import genesis as gs
import csv
import os

# --- Output folders ---
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

output_csv = os.path.join(results_dir, "fluid_state_log_large.csv")
if os.path.exists(output_csv):
    os.remove(output_csv)

with open(output_csv, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['step', 'particle_id', 'x', 'y', 'z', 'vx', 'vy', 'vz'])

# --- Init GPU ---
gs.init(backend=gs.cuda, debug=False, precision='32')

# --- Scene ---
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=2e-3, substeps=10),
    sph_options=gs.options.SPHOptions(
        lower_bound=(0.0, -50.0, -50.0),
        upper_bound=(20.0, 20.0, 2.0),
        particle_size=0.025,
    ),
    vis_options=gs.options.VisOptions(visualize_sph_boundary=True),
    show_viewer=False  # GPU headless
)

# --- Terrain ---
terrain = scene.add_entity(
    morph=gs.morphs.Terrain(
        n_subterrains=(3, 3),
        subterrain_size=(10.0, 10.0),
        subterrain_types='sloped_terrain',
        horizontal_scale=0.5,
        vertical_scale=0.1,
        randomize=True
    ),
    surface=gs.surfaces.Default(color=(0.3, 0.3, 0.3)),
)

# --- Fluid ---
water_block = scene.add_entity(
    material=gs.materials.SPH.Liquid(sampler='random'),
    morph=gs.morphs.Box(
        pos=(2.0, 8.0, 1.0),
        size=(5.0, 5.0, 2.0)
    ),
    surface=gs.surfaces.Default(color=(0.4, 0.8, 1.0), vis_mode='particle')
)

scene.build()

# --- Simulation loop config ---
simulation_time = 3600  # seconds
steps_per_second = int(1.0 / scene.sim_options.dt)
simulation_steps = simulation_time * steps_per_second
output_interval = 1000
frame_interval = 500  # Save frame every 500 steps

# --- Optional: enable recording
scene.start_recording(path=os.path.join(results_dir, "sim_recording"))

# --- Run simulation ---
for i in range(simulation_steps):
    scene.step()

    # Save visual frame for future .mp4 (optional)
    if i % frame_interval == 0:
        frame_path = os.path.join(results_dir, f"frame_{i:06d}.png")
        scene.save_frame(frame_path)

    # Save particle state
    if i % output_interval == 0:
        state = water_block.get_state()
        positions = state.pos
        velocities = state.vel

        with open(output_csv, mode='a', newline='') as f:
            writer = csv.writer(f)
            for pid in range(len(positions)):
                pos = positions[pid]
                vel = velocities[pid]
                writer.writerow([i, pid, pos[0], pos[1], pos[2], vel[0], vel[1], vel[2]])

# --- Optional: save entire sim state (if supported)
scene.save(os.path.join(results_dir, "final_scene.gsim"))

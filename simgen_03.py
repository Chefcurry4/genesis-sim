# --- Import principali ---
from genesis.engine.scene import Scene
from genesis.engine import options, morphs, materials, surfaces

import csv
import os
import numpy as np

# --- Configurazione output ---
results_dir = os.path.join(os.path.expanduser("~"), "Desktop", "genesis", "results")
os.makedirs(results_dir, exist_ok=True)

output_csv = os.path.join(results_dir, "optimized_fluid_log.csv")
if os.path.exists(output_csv):
    os.remove(output_csv)

CSV_BUFFER_SIZE = 500
csv_buffer = []

# --- Inizializzazione GPU (commentato se non serve ora) ---
# import genesis
# genesis.init(
#     backend=genesis.cuda,
#     debug=False,
#     precision='32'
# )

# --- Creazione scena ---
scene = Scene(
    sim_options=options.SimOptions(
        dt=1.5e-3,
        substeps=10,
        # solver_iterations=3
    ),
    sph_options=options.SPHOptions(
        lower_bound=(-30.0, -50.0, -30.0),
        upper_bound=(100.0, 50.0, 30.0),
        particle_size=0.01,
        # rest_density=800,
        # surface_tension=0.05,
        # viscosity=0.005
    ),
    show_viewer=False
)

# --- Terreno semplificato ---
terrain = scene.add_entity(
    morph=morphs.Terrain(
        n_subterrains=(3, 3),
        subterrain_size=(15.0, 15.0),
        horizontal_scale=0.3,
        vertical_scale=0.2,
        subterrain_types=[
            ['flat_terrain', 'sloped_terrain', 'flat_terrain'],
            ['sloped_terrain', 'flat_terrain', 'sloped_terrain'],
            ['flat_terrain', 'flat_terrain', 'sloped_terrain']
        ]
    ),
    surface=surfaces.Default(color=(0.3, 0.3, 0.3)),
)

# --- Sistema fluido ottimizzato ---
fluid_block = scene.add_entity(
    material=materials.SPH.Liquid(
        sampler='poisson',
        sampling_ratio=0.9
    ),
    morph=morphs.Box(
        pos=(30.0, 0.0, 8.0),
        size=(15.0, 15.0, 6.0)
    ),
    surface=surfaces.Default(color=(0.4, 0.8, 1.0))
)

# --- Costruzione scena ---
scene.build()

# --- Parametri simulazione ---
simulation_time = 7200
steps_per_second = int(1.0 / scene.sim_options.dt)
simulation_steps = simulation_time * steps_per_second
output_interval = 3000
frame_interval = 1500

# --- Inizio recording ---
scene.start_recording(
    path=os.path.join(results_dir, "optimized_recording"),
    quality='medium'
)

# --- Loop di simulazione ---
try:
    for i in range(simulation_steps):
        scene.step()

        if i % frame_interval == 0:
            scene.save_frame(os.path.join(results_dir, f"frame_{i:06d}.png"))

        if i % output_interval == 0:
            state = fluid_block.get_state()
            positions = state.pos
            velocities = state.vel
            
            for pid in range(len(positions)):
                csv_buffer.append([i, pid, *positions[pid], *velocities[pid]])
                
                if len(csv_buffer) >= CSV_BUFFER_SIZE:
                    with open(output_csv, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerows(csv_buffer)
                    csv_buffer.clear()

    if csv_buffer:
        with open(output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_buffer)

except Exception as e:
    print(f"Errore: {str(e)}")
    scene.save(os.path.join(results_dir, "partial_simulation.gsim"))
    raise

finally:
    scene.stop_recording()
    scene.save(os.path.join(results_dir, "final_scene.gsim"))

print("Simulazione completata correttamente!")

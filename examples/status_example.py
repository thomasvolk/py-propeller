from propeller import status

s = status.get_status()
print(f"status: {s.status}")
print(f"mode: {s.mode}")
print(f"bpm: {s.bpm}")
print(f"loop_duration: {s.loop_duration}")
print(f"clock_state: {s.clock_state}")
print(f"project_present: {s.project_present}")
print(f"midi_port_name: {s.midi_port_name}")
print(f"sync_port_name: {s.sync_port_name}")
print(f"sync_clock_state: {s.sync_clock_state}")

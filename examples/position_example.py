from propeller import loop

p = loop.get_position()
print(f"tick: {p.tick}")
print(f"loop_duration: {p.loop_duration}")
print(f"loop_count: {p.loop_count}")

import streamlit as st

st.set_page_config(page_title="Pace Calculator", layout="centered")

st.title("Running Pace Calculator")

unit_choice = st.radio("Distance Unit:", ["Kilometers (km)", "Miles (mi)"], horizontal=True)
unit = "km" if "Kilometers" in unit_choice else "mi"

col_m, col_s = st.columns(2)
with col_m:
    mins = st.number_input("Goal Minutes", min_value=0, max_value=300, value=20)
with col_s:
    secs = st.number_input("Goal Seconds", min_value=0, max_value=59, value=0)

total_seconds = (mins * 60) + secs
distance = st.number_input(f"Distance ({unit})", min_value=0.1, max_value=100.0, value=5.0, step=0.5)

split_bias = st.slider("Split Bias (-1.0 Faster Start / +1.0 Faster End)", min_value=-1.0, max_value=1.0, value=0.0, step=0.05)

split_strength = split_bias / 5.0

def format_time(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"

whole_units = int(distance)
segment_count = whole_units + (1 if distance - whole_units > 1e-9 else 0)

segment_distances = []
for index in range(segment_count):
    seg_dist = 1.0 if index < whole_units else (distance - whole_units)
    if seg_dist > 0:
        segment_distances.append(seg_dist)

if distance > 0 and total_seconds > 0:
    base_pace_seconds = total_seconds / distance
    unscaled_times = []
    for i, seg_dist in enumerate(segment_distances):
        progress = i / max(len(segment_distances) - 1, 1)
        factor = 1 + split_strength * (2 * progress - 1)
        unscaled_times.append(base_pace_seconds * factor * seg_dist)

    total_unscaled = sum(unscaled_times)
    scale = total_seconds / total_unscaled if total_unscaled > 0 else 1.0

    st.subheader("Split Breakdown")

    splits_data = []
    cumulative = 0.0
    for i, seg_dist in enumerate(segment_distances):
        seg_time = unscaled_times[i] * scale
        cumulative += seg_time
        split_num = i + 1 if i < whole_units else f"{distance:.2f}"
        
        splits_data.append({
            f"Split ({unit})": str(split_num),
            "Cumulative Time": format_time(cumulative),
            "Pace": f"{format_time(seg_time / seg_dist)} /{unit}"
        })

    st.dataframe(splits_data, use_container_width=True)

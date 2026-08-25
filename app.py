import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Pace Calculator", layout="centered")

st.title("Pace Calculator")

# --- 0. UNIT SELECTOR (MILES VS KM) ---
unit = st.radio("Select Distance Unit:", ["Miles (mi)", "Kilometers (km)"], horizontal=True)
is_miles = unit.startswith("Miles")

unit_label = "mi" if is_miles else "km"
alt_unit_label = "km" if is_miles else "mi"
unit_full = "Mile" if is_miles else "Kilometer"

st.markdown("---")

# --- 1. USER INPUTS ---
col_m, col_s = st.columns(2)
with col_m:
    mins = st.number_input("Goal Minutes", min_value=1, max_value=600, value=30)
with col_s:
    secs = st.number_input("Goal Seconds", min_value=0, max_value=59, value=0)

total_goal_seconds = (mins * 60) + secs
distance = st.number_input(f"Total Distance ({unit_full}s)", min_value=1, max_value=100, value=6, step=1)

avg_pace_seconds = total_goal_seconds / distance

def format_time(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"

# --- 2. MANAGING STATE & MODES ---
if "active_sliders" not in st.session_state:
    st.session_state.active_sliders = []

st.session_state.active_sliders = [m for m in st.session_state.active_sliders if m <= distance]

st.markdown("---")

# --- SECTION 2: SPLIT BREAKDOWN TABLE PLACEHOLDER ---
table_container = st.container()

st.markdown("---")

# --- SECTION 3: PACING CONTROL OPTIONS ---
st.subheader("Pacing Options")

pace_mode = st.radio(
    "Select Pacing Strategy:",
    ["Even Pace", "General Split (Positive / Negative)", f"Custom Per-{unit_full} Override"],
    horizontal=False
)

raw_weights = []

if pace_mode == "Even Pace":
    raw_weights = [1.0] * int(distance)

elif pace_mode == "General Split (Positive / Negative)":
    split_bias = st.slider(
        "Split Bias (-0.30 Faster Start / +0.30 Faster End)",
        min_value=-0.30,
        max_value=0.30,
        value=0.00,
        step=0.01,
        help="Negative split = start faster. Positive split = finish faster."
    )
    split_strength = split_bias / 5.0
    for i in range(int(distance)):
        progress = i / max(distance - 1, 1)
        factor = 1 + split_strength * (2 * progress - 1)
        raw_weights.append(factor)

else:
    st.caption(f"Add sliders one by one for specific {unit_full.lower()}s. Unconfigured segments stay balanced automatically.")
    
    unconfigured_segments = [m for m in range(1, int(distance) + 1) if m not in st.session_state.active_sliders]
    
    col_add, col_reset = st.columns([2, 1])
    with col_add:
        if unconfigured_segments:
            selected_segment = st.selectbox(f"Select a {unit_full.lower()} to customize:", unconfigured_segments)
            if st.button(f"➕ Add {unit_full} Override"):
                st.session_state.active_sliders.append(selected_segment)
                st.rerun()
        else:
            st.info(f"All {unit_full.lower()}s currently have custom sliders.")

    with col_reset:
        if st.session_state.active_sliders:
            if st.button(" Reset All Sliders"):
                st.session_state.active_sliders = []
                st.rerun()

    for m in sorted(st.session_state.active_sliders):
        col_slider, col_del = st.columns([4, 1])
        with col_slider:
            st.slider(
                f"{unit_full} {m} Effort Factor",
                min_value=0.70,
                max_value=1.30,
                value=st.session_state.get(f"weight_seg_{m}", 1.0),
                step=0.01,
                key=f"weight_seg_{m}"
            )
        with col_del:
            st.write("")
            st.write("")
            if st.button("❌", key=f"remove_{m}"):
                st.session_state.active_sliders.remove(m)
                st.rerun()

    for i in range(1, int(distance) + 1):
        if i in st.session_state.active_sliders:
            raw_weights.append(st.session_state.get(f"weight_seg_{i}", 1.0))
        else:
            raw_weights.append(1.0)

# --- 4. EXACT TIME NORMALIZATION MATH ---
weight_sum = sum(raw_weights)
scaled_weights = [w * (distance / weight_sum) for w in raw_weights]
segment_times = [avg_pace_seconds * w for w in scaled_weights]

# --- 5. BUILD DATA & POPULATE TABLE ---
splits_data = []
cumulative_time = 0.0
has_too_fast_segment = False

# Thresholds: 4:00/mi (240s) or 2:29/km (149s)
too_fast_threshold = 240 if is_miles else 149

for i, seg_time in enumerate(segment_times):
    cumulative_time += seg_time
    alt_unit_time = seg_time / 1.609344 if is_miles else seg_time * 1.609344
    
    if seg_time < too_fast_threshold:
        effort_label = "TOO FAST"
        has_too_fast_segment = True
    elif scaled_weights[i] < 0.98:
        effort_label = "Fast"
    elif scaled_weights[i] > 1.02:
        effort_label = "Slow"
    else:
        effort_label = "Even"

    primary_pace = f"{format_time(seg_time)} /{unit_label}"
    secondary_pace = f"{format_time(alt_unit_time)} /{alt_unit_label}"

    splits_data.append({
        unit_full: i + 1,
        f"Min/{unit_label.upper()} Pace": primary_pace,
        f"Min/{alt_unit_label.upper()} Pace": secondary_pace,
        "Pace Seconds": seg_time,
        "Cumulative Time": format_time(cumulative_time),
        "Effort": effort_label
    })

df = pd.DataFrame(splits_data)

# Render table inside top container
with table_container:
    st.subheader("Split Breakdown")
    st.dataframe(
        df[[unit_full, f"Min/{unit_label.upper()} Pace", f"Min/{alt_unit_label.upper()} Pace", "Cumulative Time", "Effort"]], 
        use_container_width=True
    )
    
    if has_too_fast_segment:
        threshold_text = "< 4:00/mi" if is_miles else "< 2:29/km"
        st.error(f"**TOO FAST:** One or more segments fall below a realistic pace threshold ({threshold_text})!")

    st.success(f"Total calculated time: **{format_time(cumulative_time)}** (Matches Goal Time Exactly)")

st.markdown("---")

# --- SECTION 4: INTERACTIVE LINE CHART ---
st.subheader("Interactive Pace Line Chart")

fig = px.line(
    df, 
    x=unit_full, 
    y="Pace Seconds",
    markers=True,
    text=f"Min/{unit_label.upper()} Pace",
    hover_data={f"Min/{unit_label.upper()} Pace": True, f"Min/{alt_unit_label.upper()} Pace": True, "Pace Seconds": False}
)

fig.update_traces(
    line_color='#3498db',
    line_width=3,
    marker=dict(size=10, color='#2980b9'),
    textposition='top center'
)

fig.update_layout(
    yaxis=dict(
        autorange="reversed", 
        title="Pace (Faster ↑ / Slower ↓)", 
        showticklabels=False, 
        zeroline=False
    ),
    xaxis=dict(dtick=1, title=f"{unit_full} Number"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

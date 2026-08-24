import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Pace Calculator", layout="centered")

st.title("🏃 Custom Running Pace Calculator")

# --- 1. USER INPUTS ---
col_m, col_s = st.columns(2)
with col_m:
    mins = st.number_input("Goal Minutes", min_value=1, max_value=600, value=30)
with col_s:
    secs = st.number_input("Goal Seconds", min_value=0, max_value=59, value=0)

total_goal_seconds = (mins * 60) + secs
distance_miles = st.number_input("Total Distance (Miles)", min_value=1, max_value=50, value=6, step=1)

avg_pace_seconds = total_goal_seconds / distance_miles

def format_time(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"

# --- 2. MANAGING STATE & MODES ---
if "active_sliders" not in st.session_state:
    st.session_state.active_sliders = []

st.session_state.active_sliders = [m for m in st.session_state.active_sliders if m <= distance_miles]

st.markdown("---")

# --- SECTION 2: SPLIT BREAKDOWN TABLE PLACEHOLDER ---
table_container = st.container()

st.markdown("---")

# --- SECTION 3: PACING CONTROL OPTIONS ---
st.subheader("🎛️ Pacing Options")

pace_mode = st.radio(
    "Select Pacing Strategy:",
    ["Even Pace", "General Split (Negative / Positive)", "Custom Per-Mile Override"],
    horizontal=False
)

raw_weights = []

if pace_mode == "Even Pace":
    raw_weights = [1.0] * int(distance_miles)

elif pace_mode == "General Split (Negative / Positive)":
    # Finer control bounds to prevent impossible splits (-0.30 to +0.30, step 0.01)
    split_bias = st.slider(
        "Split Bias (-0.30 Faster Start / +0.30 Faster End)",
        min_value=-0.30,
        max_value=0.30,
        value=0.00,
        step=0.01,
        help="Negative split = start faster. Positive split = finish faster."
    )
    # Scale factor for realistic, subtle progression
    split_strength = split_bias / 5.0
    for i in range(int(distance_miles)):
        progress = i / max(distance_miles - 1, 1)
        factor = 1 + split_strength * (2 * progress - 1)
        raw_weights.append(factor)

elif pace_mode == "Custom Per-Mile Override":
    st.caption("Add sliders one by one for specific miles. Unconfigured miles stay balanced automatically.")
    
    unconfigured_miles = [m for m in range(1, int(distance_miles) + 1) if m not in st.session_state.active_sliders]
    
    col_add, col_reset = st.columns([2, 1])
    with col_add:
        if unconfigured_miles:
            selected_mile = st.selectbox("Select a mile to customize:", unconfigured_miles)
            if st.button("➕ Add Mile Override"):
                st.session_state.active_sliders.append(selected_mile)
                st.rerun()
        else:
            st.info("All miles currently have custom sliders.")

    with col_reset:
        if st.session_state.active_sliders:
            if st.button("🔄 Reset All Sliders"):
                st.session_state.active_sliders = []
                st.rerun()

    for m in sorted(st.session_state.active_sliders):
        col_slider, col_del = st.columns([4, 1])
        with col_slider:
            st.slider(
                f"Mile {m} Effort Factor",
                min_value=0.70,
                max_value=1.30,
                value=st.session_state.get(f"weight_mile_{m}", 1.0),
                step=0.01,
                key=f"weight_mile_{m}"
            )
        with col_del:
            st.write("")
            st.write("")
            if st.button("❌", key=f"remove_{m}"):
                st.session_state.active_sliders.remove(m)
                st.rerun()

    for i in range(1, int(distance_miles) + 1):
        if i in st.session_state.active_sliders:
            raw_weights.append(st.session_state.get(f"weight_mile_{i}", 1.0))
        else:
            raw_weights.append(1.0)

# --- 4. EXACT TIME NORMALIZATION MATH ---
weight_sum = sum(raw_weights)
scaled_weights = [w * (distance_miles / weight_sum) for w in raw_weights]
mile_times = [avg_pace_seconds * w for w in scaled_weights]

# --- 5. BUILD DATA & POPULATE TABLE ---
splits_data = []
cumulative_time = 0.0

for i, seg_time_mile in enumerate(mile_times):
    cumulative_time += seg_time_mile
    seg_time_km = seg_time_mile / 1.609344
    
    if seg_time_mile < 240 or seg_time_km < 149:
        effort_label = "🚨 Unrealistic Fast"
    elif scaled_weights[i] < 0.98:
        effort_label = "⚡ Fast"
    elif scaled_weights[i] > 1.02:
        effort_label = "🐢 Slow"
    else:
        effort_label = "🎯 Even"

    splits_data.append({
        "Mile": i + 1,
        "Min/Mile Pace": f"{format_time(seg_time_mile)} /mi",
        "Min/KM Pace": f"{format_time(seg_time_km)} /km",
        "Pace Seconds": seg_time_mile,
        "Cumulative Time": format_time(cumulative_time),
        "Effort": effort_label
    })

df = pd.DataFrame(splits_data)

# Render table inside top container
with table_container:
    st.subheader("📊 Split Breakdown")
    st.dataframe(
        df[["Mile", "Min/Mile Pace", "Min/KM Pace", "Cumulative Time", "Effort"]], 
        use_container_width=True
    )
    st.success(f"✅ Total calculated time: **{format_time(cumulative_time)}** (Matches Goal Time Exactly)")

st.markdown("---")

# --- SECTION 4: INTERACTIVE LINE CHART ---
st.subheader("📈 Interactive Pace Line Chart")

fig = px.line(
    df, 
    x="Mile", 
    y="Pace Seconds",
    markers=True,
    text="Min/Mile Pace",
    hover_data={"Min/Mile Pace": True, "Min/KM Pace": True, "Pace Seconds": False}
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
    xaxis=dict(dtick=1, title="Mile Number"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

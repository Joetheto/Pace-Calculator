import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Pace Calculator", layout="centered")

st.title(" Custom Running Pace Calculator ")

# --- 1. USER INPUTS ---
col_m, col_s = st.columns(2)
with col_m:
    mins = st.number_input("Goal Minutes", min_value=1, max_value=600, value=30)
with col_s:
    secs = st.number_input("Goal Seconds", min_value=0, max_value=59, value=0)

total_goal_seconds = (mins * 60) + secs
distance_miles = st.number_input("Total Distance (Miles)", min_value=1, max_value=50, value=6, step=1)

# Base average pace in seconds per mile
avg_pace_seconds = total_goal_seconds / distance_miles

def format_time(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"

st.markdown("---")
st.subheader(" Configure Mile Efforts")
st.caption("Adjust the sliders below to make specific miles faster or slower. The app automatically scales them so your **total goal time remains exact**.")

# --- 2. PER-MILE PACE SLIDERS ---
raw_weights = []
for i in range(int(distance_miles)):
    weight = st.slider(
        f"Mile {i+1} Effort Factor",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="< 1.0 = Faster pace, > 1.0 = Slower pace",
        key=f"weight_{i}"
    )
    raw_weights.append(weight)

# --- 3. EXACT TIME NORMALIZATION MATH ---
weight_sum = sum(raw_weights)
scaled_weights = [w * (distance_miles / weight_sum) for w in raw_weights]

mile_times = [avg_pace_seconds * w for w in scaled_weights]

# --- 4. BUILD DATA ---
splits_data = []
cumulative_time = 0.0

for i, seg_time_mile in enumerate(mile_times):
    cumulative_time += seg_time_mile
    seg_time_km = seg_time_mile / 1.609344
    
    splits_data.append({
        "Mile": i + 1,
        "Min/Mile Pace": f"{format_time(seg_time_mile)} /mi",
        "Min/KM Pace": f"{format_time(seg_time_km)} /km",
        "Pace Seconds": seg_time_mile,
        "Cumulative Time": format_time(cumulative_time),
        "Effort": "⚡ Fast" if scaled_weights[i] < 0.98 else ("🐢 Slow" if scaled_weights[i] > 1.02 else "🎯 Even")
    })

df = pd.DataFrame(splits_data)

st.markdown("---")

# --- SECOND SECTION: SPLIT BREAKDOWN TABLE ---
st.subheader("Split Breakdown")
st.dataframe(
    df[["Mile", "Min/Mile Pace", "Min/KM Pace", "Cumulative Time", "Effort"]], 
    use_container_width=True
)

st.success(f" Total calculated time: **{format_time(cumulative_time)}** (Matches Goal Time Exactly)")

st.markdown("---")

# --- THIRD SECTION: INTERACTIVE PACE CHART ---
st.subheader("Interactive Pace Chart")

fig = px.bar(
    df, 
    x="Mile", 
    y="Pace Seconds", 
    color="Effort",
    text="Min/Mile Pace",
    hover_data={"Min/Mile Pace": True, "Min/KM Pace": True, "Pace Seconds": False},
    color_discrete_map={ "Fast": "#2ecc71", "Even": "#3498db", "Slow": "#e74c3c"}
)

fig.update_traces(textposition='outside')
fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)

st.plotly_chart(fig, use_container_width=True)

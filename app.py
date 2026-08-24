import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Pace Calculator", layout="centered")

st.title("Running Pace Calculator")

# --- 1. USER INPUTS ---
unit_choice = st.radio("Distance Unit:", ["Miles (mi)", "Kilometers (km)"], horizontal=True)
unit = "mi" if "Miles" in unit_choice else "km"

col_m, col_s = st.columns(2)
with col_m:
    mins = st.number_input("Goal Minutes", min_value=1, max_value=600, value=30)
with col_s:
    secs = st.number_input("Goal Seconds", min_value=0, max_value=59, value=0)

total_goal_seconds = (mins * 60) + secs
distance = st.number_input(f"Total Distance ({unit})", min_value=1, max_value=50, value=6, step=1)

# Base average pace
avg_pace_seconds = total_goal_seconds / distance

def format_time(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:02d}:{s:02d}"

st.markdown("---")
st.subheader("Configure Mile Efforts")
st.caption("Adjust the sliders below to make specific miles faster or slower. The app automatically scales them so your **total goal time remains exact**.")

# --- 2. PER-UNIT PACE SLIDERS ---
raw_weights = []
for i in range(int(distance)):
    # Slider default at 1.0 (average effort), range 0.5 (fast) to 1.5 (slow)
    weight = st.slider(
        f"{unit.capitalize()} {i+1} Effort Factor",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="< 1.0 = Faster pace, > 1.0 = Slower pace",
        key=f"weight_{i}"
    )
    raw_weights.append(weight)

# --- 3. EXACT TIME NORMALIZATION MATH ---
# Scale weights so their average equals 1.0, preserving exact target time
weight_sum = sum(raw_weights)
scaled_weights = [w * (distance / weight_sum) for w in raw_weights]

unit_times = [avg_pace_seconds * w for w in scaled_weights]

# --- 4. BUILD DATA & DISPLAY ---
splits_data = []
cumulative_time = 0.0

for i, seg_time in enumerate(unit_times):
    cumulative_time += seg_time
    splits_data.append({
        f"{unit.capitalize()}": i + 1,
        "Pace (Min/Unit)": format_time(seg_time),
        "Pace (Seconds)": seg_time,
        "Cumulative Time": format_time(cumulative_time),
        "Effort": "⚡ Fast" if scaled_weights[i] < 0.98 else (" Slow" if scaled_weights[i] > 1.02 else " Even")
    })

df = pd.DataFrame(splits_data)

st.markdown("---")
st.subheader(" Interactive Pace Chart")

# Interactive Bar Chart
fig = px.bar(
    df, 
    x=f"{unit.capitalize()}", 
    y="Pace (Seconds)", 
    color="Effort",
    text="Pace (Min/Unit)",
    labels={"Pace (Seconds)": "Pace (Seconds per unit)"},
    color_discrete_map={" Fast": "#2ecc71", " Even": "#3498db", " Slow": "#e74c3c"}
)

fig.update_traces(textposition='outside')
fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)

st.plotly_chart(fig, use_container_width=True)

st.subheader(" Split Breakdown")
st.dataframe(df[[f"{unit.capitalize()}", "Pace (Min/Unit)", "Cumulative Time", "Effort"]], use_container_width=True)

st.success(f"Total calculated time: **{format_time(cumulative_time)}** (Matches Goal Time Exactly)")

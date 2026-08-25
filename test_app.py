import pytest

# Core math normalization rule: total calculated split seconds must match target goal seconds
def calculate_splits(mins, secs, distance, raw_weights):
    total_seconds = (mins * 60) + secs
    avg_pace = total_seconds / distance
    weight_sum = sum(raw_weights)
    scaled_weights = [w * (distance / weight_sum) for w in raw_weights]
    mile_times = [avg_pace * w for w in scaled_weights]
    return sum(mile_times)

def test_exact_time_match_miles():
    target_secs = 1800  # 30 mins
    calculated_secs = calculate_splits(30, 0, 6, [1.0, 0.95, 1.05, 1.0, 0.98, 1.02])
    assert abs(target_secs - calculated_secs) < 0.001

def test_exact_time_match_km():
    target_secs = 2700  # 45 mins
    calculated_secs = calculate_splits(45, 0, 10, [1.0] * 10)
    assert abs(target_secs - calculated_secs) < 0.001

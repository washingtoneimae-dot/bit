#!/usr/bin/env python3
"""
BBU Phase Log Simulator — generates realistic 5G SSB phase correction logs
for testing the Structural-Maintenance Debt observer.

Models a 5G Massive MIMO antenna on a telecom tower. The BBU applies
phase corrections to maintain beam alignment. When the tower deforms
from wind or permanent structural strain, the corrections encode it.

Output: CSV with columns [timestamp, wind_shear, phase_correction,
        ground_truth_elastic, ground_truth_plastic]

Usage:
    python bbu_log_sim.py --hours=24 --pattern=gusty --event=06:00,1.5
    python bbu_log_sim.py --hours=72 --alpha=0.168 --noise=0.02 --seed=42
"""

import argparse
import csv
import math
import random
from datetime import datetime, timedelta

# ── Default calibrated parameters (Nairobi, June 2026) ──────────
DEFAULT_ALPHA = 0.168       # °·s/m — elastic modulus multiplier
DEFAULT_C_ENV = 1.12        # environmental corrosion factor
DEFAULT_NOISE = 0.015       # ° — measurement noise stddev
DEFAULT_INTERVAL = 10       # seconds between samples
DEFAULT_SEED = 42


def generate_wind(
    hours: int,
    interval: int,
    pattern: str,
    seed: int,
) -> list[float]:
    """Generate realistic wind shear series (m/s).

    Patterns:
        calm       — light breeze, 2-5 m/s
        gusty      — moderate with sudden gusts, 4-13 m/s
        storm      — sustained high wind, 10-20 m/s
        diurnal    — calm night, windy afternoon (tropical pattern)
    """
    rng = random.Random(seed)
    samples = int(hours * 3600 / interval)
    wind = []
    t = 0.0

    for i in range(samples):
        hour_of_day = (t / 3600) % 24

        if pattern == "calm":
            base = 2.0
            amp = 3.0
        elif pattern == "gusty":
            base = 4.0
            amp = 5.0
            # Occasional gusts: multiply by 1.5-2.5 every ~20 mins
            if rng.random() < 1 / 120:
                amp *= rng.uniform(1.5, 2.5)
        elif pattern == "storm":
            base = 10.0
            amp = 6.0
        elif pattern == "diurnal":
            # Calm at night, windy midday
            daytime = abs(hour_of_day - 14)  # peak at 2 PM
            diurnal_factor = 1.0 + 0.6 * math.exp(-daytime * 0.15)
            base = 2.0 * diurnal_factor
            amp = 4.0 * diurnal_factor
        else:
            base = 4.0
            amp = 4.0

        # Smooth correlated noise (random walk + white)
        if i == 0:
            w = base + rng.gauss(0, amp / 3)
        else:
            w = 0.95 * wind[-1] + 0.05 * (base + rng.gauss(0, amp / 2))

        wind.append(max(0.5, w))  # floor at 0.5 m/s
        t += interval

    return wind


def generate_phase(
    wind: list[float],
    alpha: float,
    c_env: float,
    noise_std: float,
    interval: int,
    rng: random.Random,
    event_specs: list[tuple[float, float]] | None = None,
) -> tuple[list[float], list[float], list[float]]:
    """Generate phase correction series from wind + physics model.

    Returns:
        (phase_correction, ground_truth_elastic, ground_truth_plastic)
        All in degrees.
    """
    phase = []
    elastic_gt = []
    plastic_gt = []
    cumulative_plastic = 0.0
    elastic_state = 0.0  # elastic sway (damped harmonic oscillator)

    # Parse events: list of (hour, delta_plastic_degrees)
    events = event_specs or []
    event_times = {int(e[0] * 3600 / interval): e[1] for e in events}

    for i, w in enumerate(wind):
        # Wind-driven elastic response (damped)
        expected_elastic = alpha * w
        elastic_state = 0.8 * elastic_state + 0.2 * expected_elastic

        # Measurement noise
        noise = rng.gauss(0, noise_std)

        # Total observed phase correction = elastic + plastic + noise
        observed = elastic_state + cumulative_plastic + noise

        # Plastic deformation event injected at specific time
        if i in event_times:
            cumulative_plastic += event_times[i]

        # Ground truth components (noiseless, for validation)
        elastic_gt.append(elastic_state)
        plastic_gt.append(cumulative_plastic)
        phase.append(observed)

    return phase, elastic_gt, plastic_gt


def generate_csv(
    wind: list[float],
    phase: list[float],
    elastic_gt: list[float],
    plastic_gt: list[float],
    interval: int,
    start_time: str,
    output: str,
):
    """Write simulated BBU log to CSV."""
    start = datetime.fromisoformat(start_time)

    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "wind_shear_mps",
            "phase_correction_deg",
            "ground_truth_elastic_deg",
            "ground_truth_plastic_deg",
            "source",
        ])
        for i in range(len(wind)):
            ts = start + timedelta(seconds=i * interval)
            writer.writerow([
                ts.isoformat(),
                round(wind[i], 4),
                round(phase[i], 4),
                round(elastic_gt[i], 4),
                round(plastic_gt[i], 4),
                "simulated",
            ])

    print(f"Wrote {len(wind)} samples to {output}")


def print_summary(
    phase: list[float],
    wind: list[float],
    plastic_gt: list[float],
    alpha: float,
    c_env: float,
):
    """Print a summary of the generated data."""
    print(f"\n{'='*60}")
    print(f"BBU Phase Log Simulation Summary")
    print(f"{'='*60}")
    print(f"  Alpha (elastic modulus):     {alpha:.3f} °·s/m")
    print(f"  C_env (corrosion factor):    {c_env:.2f}")
    print(f"  Samples:                     {len(phase)}")
    print(f"  Duration:                    {len(phase) * 10 / 3600:.1f} hours")
    print()
    print(f"  Wind shear:")
    print(f"    Min:  {min(wind):.2f} m/s")
    print(f"    Max:  {max(wind):.2f} m/s")
    print(f"    Mean: {sum(wind)/len(wind):.2f} m/s")
    print()
    print(f"  Phase correction (Δθ):")
    print(f"    Min:  {min(phase):.3f}°")
    print(f"    Max:  {max(phase):.3f}°")
    print(f"    Mean: {sum(phase)/len(phase):.3f}°")
    print()
    print(f"  Plastic deformation (δ_plastic):")
    print(f"    Final: {plastic_gt[-1]:.3f}°")
    print(
        f"    Events detected: "
        f"{sum(1 for i in range(1, len(plastic_gt)) if plastic_gt[i] > plastic_gt[i-1])}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic 5G BBU SSB phase correction logs"
    )
    parser.add_argument(
        "--hours", type=float, default=24.0,
        help="Duration in hours (default: 24)",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL,
        help="Sampling interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--pattern",
        choices=["calm", "gusty", "storm", "diurnal"],
        default="diurnal",
        help="Wind pattern (default: diurnal)",
    )
    parser.add_argument(
        "--alpha", type=float, default=DEFAULT_ALPHA,
        help="Elastic modulus multiplier °·s/m (default: 0.168)",
    )
    parser.add_argument(
        "--c-env", type=float, default=DEFAULT_C_ENV,
        help="Environmental corrosion factor (default: 1.12)",
    )
    parser.add_argument(
        "--noise", type=float, default=DEFAULT_NOISE,
        help="Measurement noise stddev in degrees (default: 0.015)",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--event", action="append",
        help="Plastic event: 'hour,delta_deg' e.g. '06:00,1.5'",
    )
    parser.add_argument(
        "--start", default="2026-06-10T00:00:00",
        help="Start timestamp (ISO format, default: 2026-06-10T00:00:00)",
    )
    parser.add_argument(
        "--output", default="bbu_phase_log.csv",
        help="Output CSV path (default: bbu_phase_log.csv)",
    )

    args = parser.parse_args()
    rng = random.Random(args.seed)

    # Parse events
    events = []
    if args.event:
        for e in args.event:
            parts = e.split(",")
            if len(parts) != 2:
                print(f"Invalid event format: {e}. Use 'HH:MM,degrees'")
                continue
            time_str, delta_str = parts
            if ":" in time_str:
                h, m = time_str.split(":")
                hour = int(h) + int(m) / 60
            else:
                hour = float(time_str)
            events.append((hour, float(delta_str)))

    print(f"\nGenerating {args.hours}h BBU phase log ({args.pattern} wind)...")
    print(f"  Events: {events if events else 'none'}")

    wind = generate_wind(args.hours, args.interval, args.pattern, args.seed)
    phase, elastic_gt, plastic_gt = generate_phase(
        wind, args.alpha, args.c_env, args.noise,
        args.interval, rng, events,
    )

    generate_csv(wind, phase, elastic_gt, plastic_gt,
                 args.interval, args.start, args.output)

    print_summary(phase, wind, plastic_gt, args.alpha, args.c_env)

    print(f"\nTo run the Kalman filter against this data:")
    print(f"  python3 -c \"import pandas as pd; "
          f"df = pd.read_csv('{args.output}'); "
          f"print(df.describe())\"")
    print()


if __name__ == "__main__":
    main()

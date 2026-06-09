#!/usr/bin/env python3
"""Plot MEDEA output directories.

The script expects the output layout produced by a full MEDEA run:

  outputs/<neural_network>/
    <layer_name>/pareto/medea.stats.NNN.yaml
    negotiated_pareto/medea.stats.txt
"""

import re
import argparse
import matplotlib.pyplot as plt

from pathlib import Path


def parse_float(value):
    return float(value.strip())


def read_negotiated_stats(path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 3:
                raise ValueError(f"Invalid negotiated stats row at {path}:{line_no}: {line}")

            energy_pj, cycles, area_um2 = map(parse_float, parts)
            rows.append(
                {
                    "point": len(rows) + 1,
                    "energy_pj": energy_pj,
                    "energy_mj": energy_pj / 1e9,
                    "cycles": cycles,
                    "area_um2": area_um2,
                    "area_mm2": area_um2 / 1e6,
                }
            )

    return rows


def read_layer_pareto(layer_dir):
    pareto_dir = layer_dir / "pareto"
    rows = []

    for path in sorted(pareto_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        energy = re.search(r"energy:\s*([0-9.Ee+-]+)", text)
        cycles = re.search(r"cycles:\s*([0-9.Ee+-]+)", text)
        area = re.search(r"area:\s*([0-9.Ee+-]+)", text)
        if not (energy and cycles and area):
            continue

        energy_pj = float(energy.group(1))
        area_um2 = float(area.group(1))
        rows.append(
            {
                "file": path.name,
                "energy_pj": energy_pj,
                "energy_mj": energy_pj / 1e9,
                "cycles": float(cycles.group(1)),
                "area_um2": area_um2,
                "area_mm2": area_um2 / 1e6,
            }
        )

    return rows


def try_add_frequency_metrics(rows, frequency_mhz):
    if frequency_mhz is None:
        return

    frequency_hz = frequency_mhz * 1e6
    for row in rows:
        latency_ms = row["cycles"] / frequency_hz * 1e3
        energy_j = row["energy_pj"] * 1e-12
        latency_s = latency_ms / 1e3
        row["latency_ms"] = latency_ms
        row["power_mw"] = energy_j / latency_s * 1e3 if latency_s > 0 else 0.0


def load_results(output_dir, frequency_mhz):
    output_dir = Path(output_dir)
    negotiated_path = output_dir / "negotiated_pareto" / "medea.stats.txt"
    negotiated = read_negotiated_stats(negotiated_path) if negotiated_path.exists() else []
    try_add_frequency_metrics(negotiated, frequency_mhz)

    layers = {}
    for layer_dir in sorted(output_dir.iterdir()):
        if not layer_dir.is_dir() or layer_dir.name == "negotiated_pareto":
            continue
        if not (layer_dir / "pareto").exists():
            continue
        layer_rows = read_layer_pareto(layer_dir)
        try_add_frequency_metrics(layer_rows, frequency_mhz)
        layers[layer_dir.name] = layer_rows

    return negotiated, layers


def scatter(ax, rows, x_key, y_key, color_key, title, x_label, y_label, color_label):
    if not rows:
        ax.set_title(f"{title} (no data)")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        return None

    x = [row[x_key] for row in rows]
    y = [row[y_key] for row in rows]
    c = [row[color_key] for row in rows]
    plot = ax.scatter(x, y, c=c, cmap="viridis", s=42, edgecolors="black", linewidths=0.25)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)
    colorbar = ax.figure.colorbar(plot, ax=ax)
    colorbar.set_label(color_label)
    return plot


def best_points(rows):
    if not rows:
        return None

    return {
        "energy": min(rows, key=lambda row: row["energy_mj"]),
        "cycles": min(rows, key=lambda row: row["cycles"]),
        "area": min(rows, key=lambda row: row["area_mm2"]),
    }


def add_best_point_markers(ax, rows, x_key, y_key):
    points = best_points(rows)
    if not points:
        return

    marker_specs = [
        ("energy", "v"),
        ("cycles", "s"),
        ("area", "D"),
    ]

    seen = set()
    for key, marker in marker_specs:
        row = points[key]
        dedup_key = (row[x_key], row[y_key], row["area_mm2"])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        ax.scatter(
            [row[x_key]],
            [row[y_key]],
            marker=marker,
            s=82,
            facecolors="none",
            edgecolors="#111111",
            linewidths=1.4,
            label={"energy": "Best energy", "cycles": "Best cycles", "area": "Best area"}[key],
            zorder=4,
        )


def format_best_summary(rows, frequency_mhz):
    points = best_points(rows)
    if not points:
        return ""

    def fmt(label, row):
        parts = [
            f"{label}: point {row['point']}",
            f"E={row['energy_mj']:.6f} mJ",
            f"cycles={row['cycles']:.0f}",
            f"A={row['area_mm2']:.4f} mm2",
        ]
        if frequency_mhz is not None:
            parts.append(f"lat={row['latency_ms']:.4f} ms")
            parts.append(f"Pavg={row['power_mw']:.2f} mW")
        return ", ".join(parts)

    return "\n".join(
        [
            fmt("Best energy", points["energy"]),
            fmt("Best cycles", points["cycles"]),
            fmt("Best area", points["area"]),
        ]
    )


def plot_negotiated(rows, output_path, frequency_mhz):
    if frequency_mhz is None:
        x_key = "cycles"
        x_label = "Cycles"
    else:
        x_key = "latency_ms"
        x_label = f"Latency at {frequency_mhz:g} MHz (ms)"

    fig, ax = plt.subplots(figsize=(8.5, 6.35))
    scatter(
        ax,
        rows,
        x_key=x_key,
        y_key="energy_mj",
        color_key="area_mm2",
        title="Negotiated Pareto Front",
        x_label=x_label,
        y_label="Energy per inference (mJ)",
        color_label="Area (mm2)",
    )
    add_best_point_markers(ax, rows, x_key, "energy_mj")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(
            handles,
            labels,
            loc="upper right",
            frameon=True,
            framealpha=0.88,
            fontsize=8,
            borderpad=0.45,
            handletextpad=0.45,
        )
    summary = format_best_summary(rows, frequency_mhz)
    if summary:
        fig.text(
            0.08,
            0.025,
            summary,
            ha="left",
            va="bottom",
            fontsize=8.5,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f7f7f7", "edgecolor": "#cccccc"},
        )
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_layer_summary(layers, output_path):
    names = []
    min_energy = []
    min_cycles = []

    for name, rows in layers.items():
        if not rows:
            continue
        names.append(name.split("_", 1)[0])
        min_energy.append(min(row["energy_mj"] for row in rows))
        min_cycles.append(min(row["cycles"] for row in rows))

    fig, ax_energy = plt.subplots(figsize=(9.5, 5.5))
    ax_cycles = ax_energy.twinx()

    x = range(len(names))
    ax_energy.bar([value - 0.2 for value in x], min_energy, width=0.4, label="Min energy")
    ax_cycles.bar([value + 0.2 for value in x], min_cycles, width=0.4, color="#d07a2d", label="Min cycles")

    ax_energy.set_title("Per-Layer Best Pareto Values")
    ax_energy.set_xlabel("Layer")
    ax_energy.set_ylabel("Minimum energy (mJ)")
    ax_cycles.set_ylabel("Minimum cycles")
    ax_energy.set_xticks(list(x))
    ax_energy.set_xticklabels(names, rotation=0)
    ax_energy.grid(True, axis="y", alpha=0.3)

    handles_a, labels_a = ax_energy.get_legend_handles_labels()
    handles_b, labels_b = ax_cycles.get_legend_handles_labels()
    ax_energy.legend(handles_a + handles_b, labels_a + labels_b, loc="upper right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_layer_paretos(layers, output_dir):
    for name, rows in layers.items():
        if not rows:
            continue
        fig, ax = plt.subplots(figsize=(8.5, 5.5))
        scatter(
            ax,
            rows,
            x_key="cycles",
            y_key="energy_mj",
            color_key="area_mm2",
            title=f"Layer Pareto: {name}",
            x_label="Cycles",
            y_label="Energy (mJ)",
            color_label="Area (mm2)",
        )
        fig.tight_layout()
        fig.savefig(output_dir / f"{name}_pareto.png", dpi=180)
        plt.close(fig)


def print_summary(negotiated, layers, frequency_mhz):
    print(f"Negotiated points: {len(negotiated)}")
    if negotiated:
        best_energy = min(negotiated, key=lambda row: row["energy_mj"])
        best_cycles = min(negotiated, key=lambda row: row["cycles"])
        best_area = min(negotiated, key=lambda row: row["area_mm2"])
        print(
            "Best energy: "
            f"point {best_energy['point']}, "
            f"{best_energy['energy_mj']:.6f} mJ, "
            f"{best_energy['cycles']:.0f} cycles, "
            f"{best_energy['area_mm2']:.4f} mm2"
        )
        print(
            "Best cycles: "
            f"point {best_cycles['point']}, "
            f"{best_cycles['energy_mj']:.6f} mJ, "
            f"{best_cycles['cycles']:.0f} cycles, "
            f"{best_cycles['area_mm2']:.4f} mm2"
        )
        print(
            "Best area: "
            f"point {best_area['point']}, "
            f"{best_area['energy_mj']:.6f} mJ, "
            f"{best_area['cycles']:.0f} cycles, "
            f"{best_area['area_mm2']:.4f} mm2"
        )
        if frequency_mhz is not None:
            print(
                "Best-energy point at "
                f"{frequency_mhz:g} MHz: "
                f"{best_energy['latency_ms']:.4f} ms, "
                f"{best_energy['power_mw']:.2f} mW"
            )

    print(f"Layer directories: {len(layers)}")
    for name, rows in layers.items():
        print(f"  {name}: {len(rows)} Pareto mappings")


def main():
    parser = argparse.ArgumentParser(description="Plot MEDEA output data.")
    parser.add_argument(
        "output_dir",
        help="MEDEA output directory, e.g. examples/outputs/cnn_rul",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory where PNG plots will be written. Defaults to <output_dir>/plots.",
    )
    parser.add_argument(
        "--frequency-mhz",
        type=float,
        default=None,
        help="Optional clock frequency used to derive latency and average power.",
    )
    parser.add_argument(
        "--layer-plots",
        action="store_true",
        help="Also generate one Pareto scatter plot per layer.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print parsed summary without writing plot files.",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    negotiated, layers = load_results(output_dir, args.frequency_mhz)
    print_summary(negotiated, layers, args.frequency_mhz)

    if args.summary_only:
        return

    out_dir = Path(args.out_dir) if args.out_dir else output_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    if negotiated:
        plot_negotiated(negotiated, out_dir / "negotiated_pareto.png", args.frequency_mhz)
    if layers:
        plot_layer_summary(layers, out_dir / "layer_summary.png")
    if args.layer_plots:
        plot_layer_paretos(layers, out_dir)

    print(f"Plots written to: {out_dir}")


if __name__ == "__main__":
    main()

import scipy.io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import os
import pandas as pd

# =============================================================================
# path configuration  <- edit this section before running
# =============================================================================
#
# base_path is the folder that contains:
#   - zapit_waveforms_site*.mat        (galvo waveform data)
#   - power_vs_voltage_obis473.xlsx    (Obis 473 linearity data)
#
# Two options:
#
#   Option A - absolute path (your own machine, do NOT commit this to git):
#       base_path = r"C:\Users\yourname\data\Zapit_2025"
#
#   Option B - relative path (default; recommended for the public repo).
#       Points to a folder called data/ sitting next to this script.
#       Clone the repo, place your data files in that folder, and run.
#       No edits needed.
#
# Root of the repository (one level up from the code/ folder this script lives in).
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# All raw data files live in raw_data/ (mat, xlsx, and bin).
base_path = os.path.join(repo_root, "raw_data")

# Figures are written to a figures/ folder at the repo root.
output_path = os.path.join(repo_root, "figures")

# Filenames (relative to base_path / output_path above).
obis473_filename         = "power_vs_voltage_obis473.xlsx"
waveform_figure_filename = "galvo_waveforms_all_stimlocations_shaded.svg"
heatmap_figure_filename  = "multisite_power_heatmap.svg"
blanking_data_filename  = "control_feedback_photodiode.bin"
blanking_figure_filename = "blanking_figure.svg"

# Number of zapit_waveforms_site*.mat files to load (site1 ... siteN).
num_waveform_files = 3

# =============================================================================
# shared plot style configuration
# =============================================================================

plt.rcParams["font.size"]       = 8
plt.rcParams["font.family"]     = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["svg.fonttype"]    = "none"

# =============================================================================
# adjusting waveforms for blanking period visualisation
# =============================================================================

laser_on_color        = "#46D3FF"
laser_on_alpha        = 0.3
min_laser_on_duration = 50   # samples; at 100 kHz this is 0.5 ms
margin_start          = 22   # samples to trim from START of each ON period
margin_end            = 22   # samples to trim from END of each ON period


# =============================================================================
# shared utility functions
# =============================================================================

def lighten_color(color, amount=0.7):
    """Mix color with white. amount=0 gives the original colour, 1 gives white."""
    try:
        rgba = to_rgba(color)
        return tuple(rgba[i] * (1 - amount) + amount for i in range(3)) + (1.0,)
    except Exception:
        return color


def save_figure_safely(fig, filepath):
    """Save fig to filepath, creating any missing parent directories."""
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        fmt    = "svg" if filepath.endswith(".svg") else None
        kwargs = dict(bbox_inches="tight")
        if fmt:
            kwargs.update(format="svg", metadata={"Date": None})
        fig.savefig(filepath, **kwargs)
        print(f"Saved: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False
    finally:
        plt.close(fig)


# =============================================================================
# galvo waveforms
# =============================================================================

def load_stimlocation_across_files(data_path, stimlocation_idx, num_files=5):
    all_waveforms = []
    for file_num in range(1, num_files + 1):
        filename = os.path.join(data_path, f"zapit_waveforms_site{file_num}.mat")
        if not os.path.exists(filename):
            continue
        try:
            mat_data      = scipy.io.loadmat(filename)
            waveforms_arr = mat_data["waveforms"].flatten()
            if stimlocation_idx >= len(waveforms_arr):
                continue
            wf = waveforms_arr[stimlocation_idx]
            all_waveforms.append((wf[:, 0], wf[:, 1], wf[:, 2]))
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    if all_waveforms:
        return (
            np.concatenate([w[0] for w in all_waveforms]),
            np.concatenate([w[1] for w in all_waveforms]),
            np.concatenate([w[2] for w in all_waveforms]),
            all_waveforms,
        )
    return None, None, None, []


def get_sample_rate(data_path):
    for file_num in range(1, 10):
        filename = os.path.join(data_path, f"zapit_waveforms_site{file_num}.mat")
        if os.path.exists(filename):
            try:
                mat_data = scipy.io.loadmat(filename)
                if "stimData" in mat_data:
                    return mat_data["stimData"]["samplesPerSecond"][0, 0][0, 0]
            except Exception:
                pass
    return 100_000


def get_global_ranges(data_path, num_files=5, num_stimlocations=4):
    gx_min, gx_max = float("inf"), float("-inf")
    gy_min, gy_max = float("inf"), float("-inf")
    for idx in range(num_stimlocations):
        x, y, _, _ = load_stimlocation_across_files(data_path, idx, num_files)
        if x is not None:
            gx_min, gx_max = min(gx_min, x.min()), max(gx_max, x.max())
            gy_min, gy_max = min(gy_min, y.min()), max(gy_max, y.max())
    return (gx_min, gx_max), (gy_min, gy_max)


def get_laser_on_periods_from_blanking(blanking, min_duration=None,
                                       trim_start=None, trim_end=None):
    if min_duration is None:
        min_duration = min_laser_on_duration
    if trim_start is None:
        trim_start = margin_start
    if trim_end is None:
        trim_end = margin_end

    laser_on = blanking == 1
    ch       = np.diff(np.concatenate([[False], laser_on, [False]]).astype(int))
    periods  = []
    for s, e in zip(np.where(ch == 1)[0], np.where(ch == -1)[0]):
        adj_s, adj_e = s + trim_start, e - trim_end
        if adj_e > adj_s and (adj_e - adj_s) >= min_duration:
            periods.append((adj_s, adj_e))
    return periods


def add_laser_shading(ax, laser_on_periods, color=None, alpha=None):
    if color is None:
        color = laser_on_color
    if alpha is None:
        alpha = laser_on_alpha
    for s, e in laser_on_periods:
        ax.axvspan(s, e, facecolor=color, alpha=alpha, edgecolor="none", zorder=0)


def plot_all_stimlocations(data_path, fig_output_path, num_files=5, save_filename=None):
    if not os.path.exists(data_path):
        print(f"Error: data directory not found: {data_path}")
        return

    existing = [f for f in os.listdir(data_path)
                if f.startswith("zapit_waveforms_site") and f.endswith(".mat")]
    print(f"Found {len(existing)} waveform files in {data_path}\n")

    sample_rate = get_sample_rate(data_path)
    print(f"Sample rate: {sample_rate} Hz\n")

    num_stimlocations = 4
    (gx_min, gx_max), (gy_min, gy_max) = get_global_ranges(
        data_path, num_files, num_stimlocations)
    gx_range = gx_max - gx_min

    fig, axes = plt.subplots(num_stimlocations, 1, figsize=(20, 14), sharex=True)

    stimlocation_info = [
        ("stimLocation01", 2),
        ("stimLocation02", 2),
        ("stimLocation03", 1),
        ("stimLocation04", 5),
    ]
    trace_separation = gx_range * 0.3

    for stim_idx in range(num_stimlocations):
        ax = axes[stim_idx]
        stim_name, n_sites = stimlocation_info[stim_idx]

        x_data, y_data, blanking, all_waveforms = load_stimlocation_across_files(
            data_path, stim_idx, num_files)

        if x_data is None or len(x_data) == 0:
            ax.text(0.5, 0.5, f"No data for {stim_name}",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=12, color="red")
            ax.set_ylabel(stim_name, fontsize=11, fontweight="bold")
            continue

        time     = np.arange(len(x_data))
        y_offset = gx_min - gy_max - trace_separation
        y_ax_min = gy_min + y_offset - 0.05
        y_ax_max = gx_max + 0.15

        laser_periods = get_laser_on_periods_from_blanking(blanking)
        total_on_samp = sum(e - s for s, e in laser_periods)
        print(f"{stim_name}: {n_sites} site(s) | "
              f"{len(laser_periods)} ON periods | "
              f"{total_on_samp / sample_rate * 1000:.2f} ms "
              f"({total_on_samp / len(blanking) * 100:.1f}% duty cycle)")

        add_laser_shading(ax, laser_periods)
        ax.plot(time, x_data,            "b-", linewidth=0.5, alpha=0.8, zorder=2)
        ax.plot(time, y_data + y_offset, "r-", linewidth=0.5, alpha=0.8, zorder=2)
        ax.set_ylim(y_ax_min, y_ax_max)

        ax.text(-800, np.mean(x_data),            "X", fontsize=10, fontweight="bold",
                color="blue", va="center", ha="right")
        ax.text(-800, np.mean(y_data) + y_offset, "Y", fontsize=10, fontweight="bold",
                color="red",  va="center", ha="right")

        cur = 0
        for wf_num, (xw, _, _) in enumerate(all_waveforms):
            if wf_num > 0:
                ax.axvline(cur, color="black", linestyle=":", linewidth=1,
                           alpha=0.4, zorder=3)
            cur += len(xw)

        ax.set_yticks([])

    axes[-1].set_xlabel("Time (samples)", fontsize=12, fontweight="bold")
    plt.tight_layout()

    if save_filename:
        os.makedirs(fig_output_path, exist_ok=True)
        save_fp = os.path.join(fig_output_path, save_filename)
        plt.savefig(save_fp, dpi=600, bbox_inches="tight")
        print(f"Waveform figure saved to: {save_fp}")

    plt.show()


# =============================================================================
# theoretical power heat map for multi-site stimulation
# =============================================================================

def calculate_multisite_power_simple(power_range=(1, 10), max_sites=5,
                                     max_sites_heatmap=20):
    power_values = np.linspace(power_range[0], power_range[1], 50)
    results = {}
    for n in range(1, max_sites + 1):
        scaling_factor = 2.0 if n <= 2 else float(n)
        duty_cycle     = 0.5 if n <= 2 else 1.0 / n
        results[n] = dict(
            power_per_site=power_values,
            total_power=power_values * scaling_factor,
            duty_cycle=duty_cycle,
            scaling_factor=scaling_factor,
        )

    pps_vals = np.linspace(power_range[0], power_range[1], 100)
    ns_vals  = np.arange(1, max_sites_heatmap + 1)
    matrix   = np.zeros((len(pps_vals), len(ns_vals)))
    for i, p in enumerate(pps_vals):
        for j, n in enumerate(ns_vals):
            matrix[i, j] = p * (2.0 if n <= 2 else n)

    masked = np.ma.masked_where(matrix > 100, matrix)
    cmap   = plt.cm.viridis.copy()
    cmap.set_bad(color="white")

    orig_font = plt.rcParams["font.sans-serif"].copy()
    plt.rcParams["font.sans-serif"] = ["Arial"]

    fig, ax = plt.subplots(1, 1, figsize=(3.343, 2.347))
    im = ax.imshow(masked, aspect="auto", origin="lower",
                   cmap=cmap, interpolation="nearest", vmin=0, vmax=100)
    ax.set_xlabel("Number of Sites", fontsize=8)
    ax.set_ylabel("Target Power per Site (mW)", fontsize=8)
    ax.set_xticks([0, 4, 9, 14, 19])
    ax.set_xticklabels([1, 5, 10, 15, 20], fontsize=8)

    y_tick_powers  = [1, 5, 10]
    y_tick_indices = [int((p - power_range[0]) / (power_range[1] - power_range[0])
                         * (len(pps_vals) - 1)) for p in y_tick_powers]
    ax.set_yticks(y_tick_indices)
    ax.set_yticklabels(y_tick_powers, fontsize=8)

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Total Laser Power Required (mW)", fontsize=8)
    cbar.ax.tick_params(labelsize=8)

    contour_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    contours       = ax.contour(masked, levels=contour_levels,
                                colors="white", alpha=1, linewidths=1.0)
    x_pos  = 10
    manual = []
    for lv in contour_levels:
        yi = int((lv / x_pos - power_range[0]) / (power_range[1] - power_range[0])
                 * (len(pps_vals) - 1))
        if 0 <= yi < len(pps_vals):
            manual.append((x_pos - 1, yi))
    ax.clabel(contours, inline=True, manual=manual, fmt="%d mW",
              colors="white", fontsize=8)
    ax.grid(False)
    plt.tight_layout()
    plt.rcParams["font.sans-serif"] = orig_font

    print("\nMulti-site power scaling summary:")
    print("=" * 50)
    for n in range(1, min(max_sites + 1, 11)):
        dc = 0.5 if n <= 2 else 1.0 / n
        sf = 2.0 if n <= 2 else float(n)
        print(f"{n:2d} site(s): {dc*100:5.1f}% duty cycle, {sf:4.1f}x scaling")
    if max_sites_heatmap > 10:
        print(f"... (up to {max_sites_heatmap} sites shown in heatmap)")

    return fig, results


# =============================================================================
# Obis 473 nm power vs voltage analysis
# =============================================================================

def analyze_obis473_power_vs_voltage(filepath, fig_output_path):
    """
    Read the Obis 473 nm power-vs-voltage Excel file and produce:
      1. Full-range plot  ->  power_vs_voltage_obis473.svg
      2. Low-voltage zoom ->  power_vs_voltage_obis473_lowvoltage.svg
    Both saved to fig_output_path.
    """
    if not os.path.exists(filepath):
        print(f"Obis 473 file not found: {filepath}")
        return
    if os.path.basename(filepath).startswith("~$"):
        print(f"Skipping temporary Excel file: {filepath}")
        return

    print(f"\nAnalysing Obis 473 power vs voltage: {filepath}")

    try:
        df_raw = pd.read_excel(filepath)
    except Exception as e:
        print(f"  Error reading file: {e}")
        return

    # First two columns are Voltage / Power
    df_laser = df_raw.iloc[:, :2].iloc[1:].copy()
    df_laser.columns = ["Voltage", "Power"]
    df_laser["Voltage"] = pd.to_numeric(df_laser["Voltage"], errors="coerce")
    df_laser["Power"]   = pd.to_numeric(df_laser["Power"],   errors="coerce")
    df_laser = df_laser.dropna().sort_values("Voltage").reset_index(drop=True)

    if df_laser.empty:
        print("  No valid numeric data - aborting.")
        return

    voltages = df_laser["Voltage"].values
    powers   = df_laser["Power"].values
    print(f"  {len(voltages)} pts | "
          f"V: {voltages.min():.4f}-{voltages.max():.4f} | "
          f"P: {powers.min():.2f}-{powers.max():.2f} mW")

    coeffs     = np.polyfit(voltages, powers, 1)
    poly       = np.poly1d(coeffs)
    fit_powers = poly(voltages)
    r2         = 1 - (np.sum((powers - fit_powers) ** 2) /
                      np.sum((powers - powers.mean()) ** 2))
    print(f"  Fit: Power = {coeffs[0]:.3f}V + {coeffs[1]:.3f}  |  R2 = {r2:.6f}")

    os.makedirs(fig_output_path, exist_ok=True)
    plot_color = "black"

    # 1. Full-range plot
    fig1, ax1 = plt.subplots(1, 1, figsize=(2.872, 2.306))
    ax1.plot(voltages, powers, "o", markersize=2,
             markerfacecolor=plot_color, markeredgecolor=plot_color, label="Measured")
    ax1.plot(voltages, fit_powers, "-", linewidth=0.8, color=plot_color,
             label=f"Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR2 = {r2:.4f}")
    ax1.set_xlabel("Voltage (V)")
    ax1.set_ylabel("Power (mW)")
    ax1.set_title("Power vs Voltage: Obis 473 nm")
    ax1.legend(loc="upper left", fontsize=7)
    ax1.grid(False)
    for spine in ["top", "right"]:
        ax1.spines[spine].set_visible(False)
    ax1.spines["bottom"].set_position(("outward", 5))
    ax1.spines["left"].set_position(("outward", 5))
    plt.tight_layout()
    save_figure_safely(fig1, os.path.join(fig_output_path,
                                          "power_vs_voltage_obis473.svg"))

    # 2. Low-voltage zoom
    low_v_threshold = 0.05
    low_mask        = voltages <= low_v_threshold
    n_low           = low_mask.sum()
    print(f"  Low-voltage points (<= {low_v_threshold} V): {n_low}")

    if n_low > 3:
        v_low, p_low = voltages[low_mask], powers[low_mask]
        fit_low = poly(v_low)
        r2_low  = 1 - (np.sum((p_low - fit_low) ** 2) /
                       np.sum((p_low - p_low.mean()) ** 2))
        print(f"  R2 (low V) = {r2_low:.6f}")

        fig2, ax2 = plt.subplots(1, 1, figsize=(2.872, 2.306))
        ax2.plot(v_low, p_low, "o", markersize=2,
                 markerfacecolor=plot_color, markeredgecolor=plot_color,
                 label="Measured", zorder=3)
        ax2.plot(v_low, p_low, "--", linewidth=0.6,
                 color=lighten_color(plot_color, 0.3),
                 label="Measured trend", zorder=2)
        ax2.plot(v_low, fit_low, "-", linewidth=0.8, color=plot_color,
                 label=f"Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\n"
                       f"R2 = {r2_low:.6f}",
                 zorder=1)
        ax2.set_xlabel("Voltage (V)")
        ax2.set_ylabel("Power (mW)")
        ax2.set_title("Power vs Voltage (Low Voltage): Obis 473 nm")
        ax2.legend(loc="upper left", fontsize=7)
        ax2.grid(False)
        for spine in ["top", "right"]:
            ax2.spines[spine].set_visible(False)
        ax2.spines["bottom"].set_position(("outward", 5))
        ax2.spines["left"].set_position(("outward", 5))
        y_lo, y_hi = ax2.get_ylim()
        ax2.set_yticks([y_lo, y_hi])
        ax2.set_yticklabels([f"{y_lo:.2f}", f"{y_hi:.2f}"])
        plt.tight_layout()
        save_figure_safely(fig2, os.path.join(fig_output_path,
                                              "power_vs_voltage_obis473_lowvoltage.svg"))
    else:
        print(f"  Skipping low-voltage plot "
              f"(fewer than 4 points <= {low_v_threshold} V).")
        
# =============================================================================
# blanking figures
# =============================================================================

def read_and_plot(fname, sample_rate=1e5, n_chans=3, plot=True):
    """
    Read raw binary data from photodiode/blanking calibration.

    Parameters
    ----------
    fname : str
        Path to the .bin file.
    sample_rate : float
        Sample rate in Hz. Default 100,000.
    n_chans : int
        Number of interleaved channels. Default 3.
    plot : bool
        If True, plot all channels. If False, just return the data.

    Returns
    -------
    dict with keys: waveforms, time, sample_rate, n_chans
    """
    data      = np.fromfile(fname, dtype=np.int16)
    n_samples = len(data) // n_chans
    time_axis = np.linspace(0, n_samples / sample_rate * 1e3, n_samples)

    out = {
        'waveforms':   data,
        'time':        time_axis,
        'sample_rate': sample_rate,
        'n_chans':     n_chans,
    }

    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))
        for ii in range(n_chans):
            ax.plot(time_axis, data[ii::n_chans])
        ax.set_xlabel('Time (ms)')
        plt.show()

    return out


def make_blanking_fig(data_path, fig_output_path,
                      data_filename=None, save_filename=None):
    """
    Make the figure showing how Zapit coordinates scanner motion with beam blanking.
    The beam is off while the scanners are moving between sites.

    Parameters
    ----------
    data_path : str
        Directory containing the raw .bin file.
    fig_output_path : str
        Directory where the output SVG will be saved.
    data_filename : str, optional
        Name of the .bin file. Defaults to blanking_data_filename.
    save_filename : str, optional
        Output SVG filename. Defaults to blanking_figure_filename.
    """
    if data_filename is None:
        data_filename = blanking_data_filename
    if save_filename is None:
        save_filename = blanking_figure_filename

    fname = os.path.join(data_path, data_filename)
    if not os.path.exists(fname):
        print(f"Blanking data file not found: {fname}")
        return

    # ---------- load ----------
    raw = read_and_plot(fname, plot=False)
    feedback   = raw['waveforms'][1::3].astype(float)  # galvo feedback
    photodiode = raw['waveforms'][2::3].astype(float)  # photodiode

    # ---------- process ----------
    diff_peak_threshold = 1e4
    transition_ind = np.where(np.diff(photodiode) < -diff_peak_threshold)[0]

    filt_len = 3
    kernel   = np.ones(filt_len) / filt_len
    feedback = np.convolve(feedback, kernel, mode='same')

    feedback = feedback - np.min(feedback)
    feedback = (feedback / np.max(feedback) * 10) - 5

    # ---------- figure ----------
    fig, (ax_c, ax_d) = plt.subplots(1, 2, figsize=(8, 4))

    font_size    = 10
    pre_ticks    = 78
    post_ticks   = 122
    time_points  = np.arange(-pre_ticks, post_ticks + 1) / 1e2  # ms
    pd_color     = [0.5, 0.5, 1.0]
    fb_color     = 'k'
    spine_offset = 10

    # left panel - odd transitions
    ax_c_right = ax_c.twinx()

    odd_indices = list(range(0, len(transition_ind), 2))
    for ii in odd_indices:
        t = transition_ind[ii]
        if t - pre_ticks >= 0 and t + post_ticks < len(feedback):
            ax_c.plot(time_points,
                      feedback[t - pre_ticks:t + post_ticks + 1],
                      '-', color=fb_color, linewidth=1)
    for ii in odd_indices:
        t = transition_ind[ii]
        if t - pre_ticks >= 0 and t + post_ticks < len(photodiode):
            ax_c_right.plot(time_points,
                            photodiode[t - pre_ticks:t + post_ticks + 1],
                            '-', color=pd_color, linewidth=1)

    ax_c.set_ylabel('Beam position (mm)', fontsize=font_size, color=fb_color)
    ax_c.set_ylim([-5.01, 5.01])
    ax_c.set_yticks(np.arange(-5, 6, 1))
    ax_c.tick_params(axis='y', labelcolor=fb_color, labelsize=font_size)
    ax_c.tick_params(axis='x', labelsize=font_size)
    ax_c.set_xlabel('Time (ms)', fontsize=font_size)
    ax_c.set_xlim([-0.25, 1.2])
    ax_c.set_xticks(np.arange(-0.25, 1.25, 0.25))
    ax_c.grid(False)
    ax_c.spines['left'].set_position(('outward', spine_offset))
    ax_c.spines['bottom'].set_position(('outward', spine_offset))
    ax_c.spines['right'].set_position(('outward', spine_offset))
    ax_c.spines['top'].set_visible(False)

    ax_c_right.tick_params(axis='y', left=False, right=True,
                            labelleft=False, labelright=False)
    ax_c_right.spines['left'].set_position(('outward', spine_offset))
    ax_c_right.spines['bottom'].set_position(('outward', spine_offset))
    ax_c_right.spines['right'].set_position(('outward', spine_offset))
    ax_c_right.spines['top'].set_visible(False)
    ax_c_right.grid(False)
    ax_c.text(-0.2, -4.5, f'n={len(odd_indices)} trials', fontsize=font_size - 2)

    # right panel - even transitions
    ax_d_right = ax_d.twinx()

    even_indices = list(range(1, len(transition_ind), 2))
    for ii in even_indices:
        t = transition_ind[ii]
        if t - pre_ticks >= 0 and t + post_ticks < len(feedback):
            ax_d.plot(time_points,
                      feedback[t - pre_ticks:t + post_ticks + 1],
                      '-', color=fb_color, linewidth=1)
    for ii in even_indices:
        t = transition_ind[ii]
        if t - pre_ticks >= 0 and t + post_ticks < len(photodiode):
            ax_d_right.plot(time_points,
                            photodiode[t - pre_ticks:t + post_ticks + 1],
                            '-', color=pd_color, linewidth=1)

    ax_d.set_ylim([-5.01, 5.01])
    ax_d.set_yticks(np.arange(-5, 6, 1))
    ax_d.tick_params(axis='y', labelcolor=fb_color, labelleft=False)
    ax_d.tick_params(axis='x', labelsize=font_size)
    ax_d.set_xlabel('Time (ms)', fontsize=font_size)
    ax_d.set_xlim([-0.25, 1.2])
    ax_d.set_xticks(np.arange(-0.25, 1.25, 0.25))
    ax_d.grid(False)
    ax_d.spines['left'].set_position(('outward', spine_offset))
    ax_d.spines['bottom'].set_position(('outward', spine_offset))
    ax_d.spines['right'].set_position(('outward', spine_offset))
    ax_d.spines['top'].set_visible(False)

    ax_d_right.set_ylabel('Photodiode signal (a.u.)', fontsize=font_size,
                           color=pd_color)
    ax_d_right.tick_params(axis='y', left=False, right=True,
                            labelleft=False, labelright=False)
    ax_d_right.spines['left'].set_position(('outward', spine_offset))
    ax_d_right.spines['bottom'].set_position(('outward', spine_offset))
    ax_d_right.spines['right'].set_position(('outward', spine_offset))
    ax_d_right.spines['top'].set_visible(False)
    ax_d_right.grid(False)
    ax_d.text(0.7, -4.75, f'n={len(even_indices)} trials', fontsize=font_size - 2)

    plt.tight_layout()

    os.makedirs(fig_output_path, exist_ok=True)
    save_fp = os.path.join(fig_output_path, save_filename)
    plt.savefig(save_fp, format='svg', bbox_inches='tight')
    print(f"Saved: {save_fp}")
    plt.show()

    return fig


# =============================================================================
# running code
# =============================================================================

if __name__ == "__main__":
    # Galvo waveform figure
    plot_all_stimlocations(
        data_path=base_path,
        fig_output_path=output_path,
        num_files=num_waveform_files,
        save_filename=waveform_figure_filename,
    )

    # Multi-site power heatmap
    fig_heatmap, _ = calculate_multisite_power_simple(
        power_range=(1, 10), max_sites=5, max_sites_heatmap=20)
    os.makedirs(output_path, exist_ok=True)
    fig_heatmap.savefig(os.path.join(output_path, heatmap_figure_filename),
                        dpi=600, bbox_inches="tight")
    print(f"Heatmap saved to: {os.path.join(output_path, heatmap_figure_filename)}")
    plt.close(fig_heatmap)

    # Obis 473 nm power vs voltage
    analyze_obis473_power_vs_voltage(
        filepath=os.path.join(base_path, obis473_filename),
        fig_output_path=output_path,
    )
    # Blanking figure
    make_blanking_fig(
        data_path=base_path,
        fig_output_path=output_path,
    )
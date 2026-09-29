import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.colors import to_rgba

# =============================================================================
# path configuration  <- edit this section before running
# =============================================================================
#
# Option A - absolute path (your own machine, do NOT commit this to git):
#     base_path = r"C:\Users\ainia\Documents\University\PhD\Writing\Zapit_2025"
#
# Option B - relative path (default; recommended for the public repo).
#     Points to raw_data/ one level up from the code/ folder this script lives in.
#
repo_root   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base_path   = os.path.join(repo_root, "raw_data")
output_path = os.path.join(repo_root, "figures")

# =============================================================================
# shared plot style configuration
# =============================================================================

plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size']       = 8
plt.rcParams['font.family']     = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Calibri', 'Arial', 'DejaVu Sans']
plt.rcParams['svg.fonttype']    = 'none'

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
        if filepath.endswith('.svg'):
            fig.savefig(filepath, bbox_inches='tight', format='svg',
                        metadata={'Date': None})
        else:
            fig.savefig(filepath, bbox_inches='tight')
        print(f"Saved: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False
    finally:
        plt.close(fig)


# =============================================================================
# power stability analysis
# =============================================================================

def parse_power_stability_file(filename):
    """Parse power stability files (ms and hr files)."""
    data = []
    wavelength = None

    with open(filename, 'r') as f:
        lines = f.readlines()

        for line in lines[:10]:
            if 'Wave' in line:
                wavelength = line.split()[1].replace('nm', '')
                break

        for line in lines:
            if 'W' in line and '/' in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        timestamp_str = f"{parts[0]} {parts[1]}"
                        timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S.%f')
                        power = float(parts[2]) * 1000  # convert to mW
                        data.append({'timestamp': timestamp, 'power_mW': power})
                    except Exception:
                        continue

    df = pd.DataFrame(data)
    if not df.empty and len(df) > 1:
        df['time_seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()

    return df, wavelength


def analyze_power_stability(filename, fig_output_path):
    """Analyze power stability for ms and hr files."""
    df, wavelength = parse_power_stability_file(filename)

    if df.empty:
        print(f"No data found in {filename}")
        return

    base_name = os.path.basename(filename)
    os.makedirs(fig_output_path, exist_ok=True)

    if 'ms' in base_name:
        df['time_ms'] = df['time_seconds'] * 1000
        df_analysis   = df.copy()
        df_analysis['time_ms_windowed'] = df_analysis['time_ms'] - df_analysis['time_ms'].min()
        df_analysis['time_s_windowed']  = df_analysis['time_ms_windowed'] / 1000

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))

        mean_power = df_analysis['power_mW'].mean()
        cv         = (df_analysis['power_mW'].std() / mean_power) * 100

        raw_data_color = lighten_color('blue', 0.3)
        orange_light   = lighten_color('orange', 0.3)
        orange_fill    = lighten_color('orange', 0.8)

        ax1.plot(df_analysis['time_s_windowed'], df_analysis['power_mW'],
                 color=raw_data_color, linewidth=0.8, label='Raw data')
        ax1.axhline(mean_power, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_power:.3f} mW')
        ax1.axhline(mean_power + df_analysis['power_mW'].std(),
                    color=orange_light, linestyle=':', linewidth=1.5, label='±1σ')
        ax1.axhline(mean_power - df_analysis['power_mW'].std(),
                    color=orange_light, linestyle=':', linewidth=1.5)
        ax1.fill_between(df_analysis['time_s_windowed'],
                         mean_power - df_analysis['power_mW'].std(),
                         mean_power + df_analysis['power_mW'].std(),
                         color=orange_fill)
        ax1.set_ylabel('Power (mW)')
        ax1.set_title(f'Power Stability - {base_name} - {wavelength}nm\n'
                      f'Mean: {mean_power:.3f} mW, CV: {cv:.2f}%, N={len(df_analysis)} samples')
        ax1.legend(loc='upper right')
        ax1.grid(False)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_position(('outward', 5))
        ax1.spines['left'].set_position(('outward', 5))
        ax1.set_xticklabels([])
        ax1.tick_params(axis='x', which='both', bottom=False)

        window_size_ms = 50
        if len(df_analysis) >= window_size_ms:
            df_sorted    = df_analysis.sort_values('time_ms_windowed').reset_index(drop=True)
            rolling_mean = df_sorted['power_mW'].rolling(window=window_size_ms, center=True).mean()
            rolling_std  = df_sorted['power_mW'].rolling(window=window_size_ms, center=True).std()
            ax2.plot(df_sorted['time_s_windowed'], rolling_mean, 'b-', linewidth=2,
                     label=f'{window_size_ms}-point rolling avg')
            ax2.fill_between(df_sorted['time_s_windowed'],
                             rolling_mean - rolling_std, rolling_mean + rolling_std,
                             color=lighten_color('blue', 0.7), label='±1σ range')
            ax2.axhline(mean_power, color='red', linestyle='--', linewidth=1.5)
        else:
            ax2.plot(df_analysis['time_s_windowed'], df_analysis['power_mW'],
                     color=lighten_color('blue', 0.5), linewidth=1, label='Raw data')
            ax2.axhline(mean_power, color='black', linestyle='--', linewidth=1.5)

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Power (mW)')
        ax2.set_title(f'Rolling Average Analysis ({window_size_ms}-point window)')
        ax2.legend(loc='upper right')
        ax2.grid(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        ax2.set_ylim(ax1.get_ylim())

        plt.tight_layout()
        save_figure_safely(fig, os.path.join(fig_output_path,
                                              f'{os.path.splitext(base_name)[0]}_stability.svg'))

    else:  # hour-scale
        df['time_hours'] = df['time_seconds'] / 3600

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))

        mean_power    = df['power_mW'].mean()
        cv            = (df['power_mW'].std() / mean_power) * 100
        drift_percent = ((df['power_mW'].iloc[-1] - df['power_mW'].iloc[0]) /
                          df['power_mW'].iloc[0]) * 100

        ax1.plot(df['time_hours'], df['power_mW'],
                 color=lighten_color('blue', 0.3), linewidth=1, label='Raw data')
        ax1.axhline(mean_power, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_power:.3f} mW')
        ax1.axhline(mean_power + 0.005 * mean_power,
                    color=lighten_color('green', 0.3), linestyle=':', linewidth=1.5, label='±0.5%')
        ax1.axhline(mean_power - 0.005 * mean_power,
                    color=lighten_color('green', 0.3), linestyle=':', linewidth=1.5)
        ax1.axhline(mean_power + 0.01 * mean_power,
                    color=lighten_color('orange', 0.3), linestyle=':', linewidth=1.5, label='±1.0%')
        ax1.axhline(mean_power - 0.01 * mean_power,
                    color=lighten_color('orange', 0.3), linestyle=':', linewidth=1.5)
        ax1.fill_between(df['time_hours'],
                         mean_power - 0.005 * mean_power, mean_power + 0.005 * mean_power,
                         color=lighten_color('green', 0.8), label='±0.5% zone')
        ax1.set_ylabel('Power (mW)')
        ax1.set_title(f'Power Stability Over Time - {base_name} - {wavelength}nm\n'
                      f'Mean: {mean_power:.3f} mW, CV: {cv:.2f}%, Drift: {drift_percent:+.2f}%')
        ax1.legend(loc='upper right')
        ax1.grid(False)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_position(('outward', 5))
        ax1.spines['left'].set_position(('outward', 5))
        ax1.set_xticklabels([])
        ax1.tick_params(axis='x', which='both', bottom=False)

        df['time_minutes'] = df['time_seconds'] / 60
        df_sorted   = df.sort_values('time_minutes')
        time_grid   = np.arange(df_sorted['time_minutes'].min(),
                                df_sorted['time_minutes'].max(), 1)
        running_avg, running_std, valid_times = [], [], []

        for t in time_grid:
            mask = ((df_sorted['time_minutes'] >= t) &
                    (df_sorted['time_minutes'] < t + 1))
            wd = df_sorted[mask]['power_mW']
            if len(wd) > 0:
                running_avg.append(wd.mean())
                running_std.append(wd.std())
                valid_times.append(t / 60)

        running_avg = np.array(running_avg)
        running_std = np.array(running_std)
        valid_times = np.array(valid_times)

        ax2.plot(valid_times, running_avg, 'bo-', linewidth=2, markersize=3,
                 label='10-min running average (1-min step)', markeredgewidth=0)
        ax2.fill_between(valid_times, running_avg - running_std, running_avg + running_std,
                         color=lighten_color('blue', 0.7), label='±1σ range')
        ax2.axhline(mean_power, color='red', linestyle='--', linewidth=2)
        ax2.set_xlabel('Time (hours)')
        ax2.set_ylabel('Power (mW)')
        ax2.set_title('Running Average Analysis (10-min window, 1-min step)')
        ax2.legend(loc='upper right')
        ax2.grid(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        ax2.set_ylim(ax1.get_ylim())

        plt.tight_layout()
        save_figure_safely(fig, os.path.join(fig_output_path,
                                              f'{os.path.splitext(base_name)[0]}_stability.svg'))


# =============================================================================
# power stability overlay plots
# =============================================================================

def create_stability_overlay_plots(files, fig_output_path, file_type='ms',
                                   exclude_lasers=None):
    """
    Create overlay plots comparing multiple lasers.
    Stable lasers = blue shades, Chengchun (unstable) = grey.
    """
    if not files:
        print(f"No {file_type} files to overlay")
        return

    all_parsed_data = {}
    for file in files:
        base_name  = os.path.basename(file)
        laser_name = base_name.replace(f'_{file_type}.txt', '').replace('.txt', '')
        df, wavelength = parse_power_stability_file(file)
        if not df.empty:
            all_parsed_data[laser_name] = {'df': df, 'wavelength': wavelength}

    if file_type == 'ms':
        global_min_time = min(d['df']['time_seconds'].max() for d in all_parsed_data.values())
    else:
        global_min_time = None

    laser_data = {}
    for laser_name, data in all_parsed_data.items():
        if exclude_lasers and any(ex.lower() in laser_name.lower() for ex in exclude_lasers):
            continue
        df         = data['df']
        mean_power = df['power_mW'].mean()
        df['percent_deviation'] = ((df['power_mW'] - mean_power) / mean_power) * 100
        laser_data[laser_name] = {
            'df': df, 'wavelength': data['wavelength'],
            'mean': mean_power, 'std': df['power_mW'].std(),
            'cv': (df['power_mW'].std() / mean_power) * 100,
            'min': df['power_mW'].min(), 'max': df['power_mW'].max(),
        }

    if not laser_data:
        print("No valid laser data found for overlay")
        return

    suffix      = "_stable" if exclude_lasers else "_all"
    blue_shades = ['#08306B', '#2171B5', '#6BAED6']
    colors      = {}
    stable_lasers = [n for n in laser_data if 'chengchun' not in n.lower()]

    if exclude_lasers:
        for i, name in enumerate(stable_lasers):
            colors[name] = blue_shades[i % len(blue_shades)]
    else:
        stable_idx = 0
        for name in laser_data:
            if 'chengchun' in name.lower():
                colors[name] = '#404040'
            else:
                colors[name] = blue_shades[stable_idx % len(blue_shades)]
                stable_idx += 1

    ref_line_color = '#DC143C'

    if file_type == 'ms':
        plot_data = {}
        for laser_name, data in laser_data.items():
            df_cut   = data['df'][data['df']['time_seconds'] <= global_min_time].copy()
            mean_cut = df_cut['power_mW'].mean()
            df_cut['percent_deviation'] = ((df_cut['power_mW'] - mean_cut) / mean_cut) * 100
            plot_data[laser_name] = {
                'df': df_cut, 'wavelength': data['wavelength'],
                'mean': mean_cut, 'std': df_cut['power_mW'].std(),
                'cv': (df_cut['power_mW'].std() / mean_cut) * 100,
                'min': df_cut['power_mW'].min(), 'max': df_cut['power_mW'].max(),
            }
        full_range_min = min(
            data['df'][data['df']['time_seconds'] <= global_min_time]['power_mW'].min()
            for data in all_parsed_data.values())
        full_range_max = max(
            data['df'][data['df']['time_seconds'] <= global_min_time]['power_mW'].max()
            for data in all_parsed_data.values())
    else:
        plot_data      = laser_data
        full_range_min = min(d['df']['power_mW'].min() for d in all_parsed_data.values())
        full_range_max = max(d['df']['power_mW'].max() for d in all_parsed_data.values())

    subplot_width  = 72.876 / 25.4
    subplot_height = 29.063 / 25.4
    hspace_inches  = 0.15
    fig, (ax1, ax2) = plt.subplots(2, 1,
                                    figsize=(subplot_width, subplot_height * 2 + hspace_inches))
    plt.subplots_adjust(right=0.92, hspace=hspace_inches / subplot_height)

    for laser_name, data in plot_data.items():
        line_color = lighten_color(colors[laser_name], 0.2)
        ax1.plot(data['df']['time_seconds'], data['df']['power_mW'],
                 linewidth=0.5, color=line_color,
                 label=f"{laser_name} ({data['wavelength']}nm)")
        ax1.axhline(data['mean'], color=lighten_color(colors[laser_name], 0.7),
                    linestyle='-', linewidth=0.3)

    ax1.set_ylabel('Power (mW)')
    ax1.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
    ax1.grid(False)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 5))
    ax1.spines['left'].set_position(('outward', 5))
    ax1.set_xticklabels([])
    ax1.tick_params(axis='x', which='both', bottom=False)
    ax1.set_xlim(0, 12)

    if exclude_lasers:
        stable_center = np.mean([d['mean'] for d in plot_data.values()])
        padding_all   = (full_range_max - full_range_min) * 0.05
        y_min_all     = full_range_min - padding_all
        y_max_all     = full_range_max + padding_all
        rel_pos       = (stable_center - y_min_all) / (y_max_all - y_min_all)
        ax1.set_ylim(stable_center - rel_pos * 2, stable_center + (1 - rel_pos) * 2)

    def add_reference_bar(ax, s_min, s_max, s_range):
        ax_bbox = ax.get_position()
        ylim    = ax.get_ylim()
        y_min_n = (s_min - ylim[0]) / (ylim[1] - ylim[0])
        y_max_n = (s_max - ylim[0]) / (ylim[1] - ylim[0])
        fig.add_artist(plt.Line2D(
            [ax_bbox.x1 + 0.01, ax_bbox.x1 + 0.01],
            [ax_bbox.y0 + y_min_n * ax_bbox.height,
             ax_bbox.y0 + y_max_n * ax_bbox.height],
            transform=fig.transFigure, color=ref_line_color, linewidth=1.5))
        return f'Stable range: {s_range:.2f} mW'

    stable_plot_data = {k: v for k, v in plot_data.items() if 'chengchun' not in k.lower()}
    if stable_plot_data:
        stable_min   = min(d['min'] for d in stable_plot_data.values())
        stable_max   = max(d['max'] for d in stable_plot_data.values())
        stable_range = stable_max - stable_min
        ref_label    = add_reference_bar(ax1, stable_min, stable_max, stable_range)
        ax1.plot([], [], color=ref_line_color, linewidth=1.5, label=ref_label)
        ax1.legend(loc='upper right', fontsize=4.5, framealpha=0.95)

    if file_type == 'ms':
        window_size_ms = 50
        for laser_name, data in plot_data.items():
            df_sorted = data['df'].sort_values('time_seconds').reset_index(drop=True)
            if len(df_sorted) >= window_size_ms:
                rm = df_sorted['power_mW'].rolling(window=window_size_ms, center=True,
                                                    min_periods=1).mean()
                rs = df_sorted['power_mW'].rolling(window=window_size_ms, center=True,
                                                    min_periods=1).std()
                ax2.plot(df_sorted['time_seconds'], rm, linewidth=0.8,
                         color=lighten_color(colors[laser_name], 0.1),
                         label=f"{laser_name} ({window_size_ms}-pt avg)")
                ax2.fill_between(df_sorted['time_seconds'], rm - rs, rm + rs,
                                 color=lighten_color(colors[laser_name], 0.75))
            else:
                ax2.plot(df_sorted['time_seconds'], df_sorted['power_mW'],
                         linewidth=0.5, color=lighten_color(colors[laser_name], 0.2),
                         label=laser_name)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Power (mW)')
        ax2.set_xlim(0, 12)
        ax2.set_xticks(np.arange(0, 14, 2))

    else:  # hr
        for laser_name, data in laser_data.items():
            df_s      = data['df'].copy()
            df_s['time_minutes'] = df_s['time_seconds'] / 60
            df_sorted = df_s.sort_values('time_minutes').reset_index(drop=True)
            half_w    = 1.0
            time_grid = np.arange(df_sorted['time_minutes'].min() + half_w,
                                   df_sorted['time_minutes'].max() - half_w, 0.25)
            r_times, r_means, r_stds = [], [], []
            for t in time_grid:
                mask = ((df_sorted['time_minutes'] >= t - half_w) &
                        (df_sorted['time_minutes'] < t + half_w))
                wd = df_sorted[mask]['power_mW']
                if len(wd) > 0:
                    r_times.append(t / 60)
                    r_means.append(wd.mean())
                    r_stds.append(wd.std())
            r_times = np.array(r_times)
            r_means = np.array(r_means)
            r_stds  = np.array(r_stds)
            ax2.plot(r_times, r_means, linewidth=0.8,
                     color=lighten_color(colors[laser_name], 0.1),
                     label=f"{laser_name} (2-min avg)")
            ax2.fill_between(r_times, r_means - r_stds, r_means + r_stds,
                             color=lighten_color(colors[laser_name], 0.75))
        ax2.set_xlabel('Time (hours)')
        ax2.set_ylabel('Power (mW)')
        max_hr = max(d['df']['time_seconds'].max() / 3600 for d in laser_data.values())
        ax2.set_xlim(0, max_hr)

    ax2.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
    ax2.grid(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_position(('outward', 5))
    ax2.spines['left'].set_position(('outward', 5))
    ax2.set_ylim(ax1.get_ylim())

    if stable_plot_data:
        add_reference_bar(ax2, stable_min, stable_max, stable_range)

    os.makedirs(fig_output_path, exist_ok=True)
    save_fp = os.path.join(fig_output_path, f'overlay_{file_type}{suffix}.svg')
    fig.savefig(save_fp, bbox_inches='tight', pad_inches=0.1, format='svg')
    print(f"Saved: {save_fp}")
    plt.close(fig)


# =============================================================================
# power vs voltage analysis
# =============================================================================

def analyze_power_vs_voltage(filename, fig_output_path):
    """
    Analyze power vs voltage linearity from a multi-laser Excel file.
    Produces individual, combined stable-laser, and Chengchun plots.
    """
    blue_shades = ['#08306B', '#2171B5', '#6BAED6']
    color_map = {
        'obis 473': blue_shades[0], 'obis_473': blue_shades[0],
        'obis 594': blue_shades[1], 'obis_594': blue_shades[1],
        'oxxius 450': blue_shades[2], 'oxxius_450': blue_shades[2],
        'oxxius': blue_shades[2],   'chengchun': '#404040',
    }

    def get_laser_color(name):
        for key, color in color_map.items():
            if key in name.lower():
                return color
        return blue_shades[1]

    def is_stable(name):
        n = name.lower()
        return ('chengchun' not in n and
                ('594' in n or '450' in n or ('obis' in n and '473' in n)))

    if os.path.basename(filename).startswith('~$'):
        print(f"Skipping temporary file: {filename}")
        return

    try:
        df = pd.read_excel(filename)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return

    laser_info = []
    for i in range(0, len(df.columns), 2):
        col = df.columns[i]
        if not str(col).startswith('Unnamed'):
            laser_info.append({
                'name': str(col),
                'voltage_col': col,
                'power_col': df.columns[i + 1] if i + 1 < len(df.columns) else None,
            })

    if not laser_info:
        print(f"Could not identify any laser columns in {filename}")
        return

    combined_lasers = [l for l in laser_info if is_stable(l['name'])]
    all_laser_data  = {}
    os.makedirs(fig_output_path, exist_ok=True)

    for laser in laser_info:
        laser_name  = laser['name']
        power_col   = laser['power_col']
        if power_col is None:
            continue

        laser_color = get_laser_color(laser_name)
        df_laser    = df[[laser['voltage_col'], power_col]].iloc[1:].copy()
        df_laser.columns = ['Voltage', 'Power']
        df_laser['Voltage'] = pd.to_numeric(df_laser['Voltage'], errors='coerce')
        df_laser['Power']   = pd.to_numeric(df_laser['Power'],   errors='coerce')
        df_laser = df_laser.dropna().sort_values('Voltage')

        if df_laser.empty:
            continue

        voltages   = df_laser['Voltage'].values
        powers     = df_laser['Power'].values
        coeffs     = np.polyfit(voltages, powers, 1)
        poly       = np.poly1d(coeffs)
        fit_powers = poly(voltages)
        r2         = 1 - (np.sum((powers - fit_powers) ** 2) /
                          np.sum((powers - powers.mean()) ** 2))

        all_laser_data[laser_name] = {
            'voltages': voltages, 'powers': powers,
            'coeffs': coeffs, 'poly': poly,
            'fit_powers': fit_powers, 'r_squared': r2,
            'color': laser_color,
        }

        if not is_stable(laser_name):
            plot_color = ('black' if ('obis' in laser_name.lower() and '473' in laser_name.lower())
                          else laser_color)
            safe_name  = laser_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')

            # full-range plot
            fig1, ax1 = plt.subplots(1, 1, figsize=(2.872, 2.306))
            ax1.plot(voltages, powers, 'o', markersize=2,
                     markerfacecolor=plot_color, markeredgecolor=plot_color, label='Measured')
            ax1.plot(voltages, fit_powers, '-', linewidth=0.8, color=plot_color,
                     label=f'Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR2 = {r2:.4f}')
            ax1.set_xlabel('Voltage (V)')
            ax1.set_ylabel('Power (mW)')
            ax1.set_title(f'Power vs Voltage: {laser_name}')
            ax1.legend(loc='upper left')
            ax1.grid(False)
            for spine in ['top', 'right']:
                ax1.spines[spine].set_visible(False)
            ax1.spines['bottom'].set_position(('outward', 5))
            ax1.spines['left'].set_position(('outward', 5))
            plt.tight_layout()
            save_figure_safely(fig1, os.path.join(fig_output_path,
                                                   f'power_vs_voltage_{safe_name}.svg'))

            # low-voltage zoom
            low_mask = voltages <= 0.05
            if low_mask.sum() > 3:
                v_low, p_low = voltages[low_mask], powers[low_mask]
                fit_low = poly(v_low)
                r2_low  = 1 - (np.sum((p_low - fit_low) ** 2) /
                               np.sum((p_low - p_low.mean()) ** 2))
                fig2, ax2 = plt.subplots(1, 1, figsize=(2.872, 2.306))
                ax2.plot(v_low, p_low, 'o', markersize=2,
                         markerfacecolor=plot_color, markeredgecolor=plot_color,
                         label='Measured', zorder=3)
                ax2.plot(v_low, p_low, '--', linewidth=0.6,
                         color=lighten_color(plot_color, 0.3),
                         label='Measured trend', zorder=2)
                ax2.plot(v_low, fit_low, '-', linewidth=0.8, color=plot_color,
                         label=f'Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR2 = {r2_low:.6f}',
                         zorder=1)
                ax2.set_xlabel('Voltage (V)')
                ax2.set_ylabel('Power (mW)')
                ax2.set_title(f'Power vs Voltage (Low Voltage): {laser_name}')
                ax2.legend(loc='upper left')
                ax2.grid(False)
                for spine in ['top', 'right']:
                    ax2.spines[spine].set_visible(False)
                ax2.spines['bottom'].set_position(('outward', 5))
                ax2.spines['left'].set_position(('outward', 5))
                y_lo, y_hi = ax2.get_ylim()
                ax2.set_yticks([y_lo, y_hi])
                ax2.set_yticklabels([f'{y_lo:.2f}', f'{y_hi:.2f}'])
                save_figure_safely(fig2, os.path.join(fig_output_path,
                                                       f'power_vs_voltage_{safe_name}_lowvoltage.svg'))

    # combined stable full-range
    if len(combined_lasers) >= 2:
        fig_c, ax_c = plt.subplots(1, 1, figsize=(2.872, 2.306))
        for laser in combined_lasers:
            if laser['name'] not in all_laser_data:
                continue
            d = all_laser_data[laser['name']]
            ax_c.plot(d['voltages'], d['powers'], 'o', markersize=2,
                      color=d['color'], markeredgewidth=0)
            ax_c.plot(d['voltages'], d['fit_powers'], '-', linewidth=0.8, color=d['color'],
                      label=f"{laser['name']}: y={d['coeffs'][0]:.3f}x+{d['coeffs'][1]:.3f}, R2={d['r_squared']:.4f}")
        ax_c.set_xlabel('Voltage (V)')
        ax_c.set_ylabel('Power (mW)')
        ax_c.set_title('Power vs Voltage: Stable Lasers')
        ax_c.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
        ax_c.grid(False)
        for spine in ['top', 'right']:
            ax_c.spines[spine].set_visible(False)
        ax_c.spines['bottom'].set_position(('outward', 5))
        ax_c.spines['left'].set_position(('outward', 5))
        plt.tight_layout()
        save_figure_safely(fig_c, os.path.join(fig_output_path,
                                                'power_vs_voltage_stable_combined.svg'))

        # combined stable low-voltage
        fig_cl, ax_cl = plt.subplots(1, 1, figsize=(2.872, 2.306))
        has_data = False
        for laser in combined_lasers:
            if laser['name'] not in all_laser_data:
                continue
            d        = all_laser_data[laser['name']]
            low_mask = d['voltages'] <= 0.05
            if low_mask.sum() > 3:
                has_data = True
                v_low, p_low = d['voltages'][low_mask], d['powers'][low_mask]
                fit_low = d['poly'](v_low)
                r2_low  = 1 - (np.sum((p_low - fit_low) ** 2) /
                               np.sum((p_low - p_low.mean()) ** 2))
                ax_cl.plot(v_low, p_low, 'o', markersize=2,
                           color=d['color'], zorder=3, markeredgewidth=0)
                ax_cl.plot(v_low, p_low, '--', linewidth=0.6,
                           color=lighten_color(d['color'], 0.3), zorder=2)
                ax_cl.plot(v_low, fit_low, '-', linewidth=0.8, color=d['color'],
                           label=f"{laser['name']}: y={d['coeffs'][0]:.3f}x+{d['coeffs'][1]:.3f}, R2={r2_low:.4f}",
                           zorder=1)
        if has_data:
            ax_cl.set_xlabel('Voltage (V)')
            ax_cl.set_ylabel('Power (mW)')
            ax_cl.set_title('Power vs Voltage (Low Voltage): Stable Lasers')
            ax_cl.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
            ax_cl.grid(False)
            for spine in ['top', 'right']:
                ax_cl.spines[spine].set_visible(False)
            ax_cl.spines['bottom'].set_position(('outward', 5))
            ax_cl.spines['left'].set_position(('outward', 5))
            y_lo, y_hi = ax_cl.get_ylim()
            ax_cl.set_yticks([y_lo, y_hi])
            ax_cl.set_yticklabels([f'{y_lo:.2f}', f'{y_hi:.2f}'])
            save_figure_safely(fig_cl, os.path.join(fig_output_path,
                                                     'power_vs_voltage_stable_combined_lowvoltage.svg'))
        else:
            plt.close(fig_cl)

    # Chengchun separate plot
    for laser in laser_info:
        if 'chengchun' not in laser['name'].lower():
            continue
        if laser['name'] not in all_laser_data:
            continue
        d = all_laser_data[laser['name']]
        fig_u, ax_u = plt.subplots(1, 1, figsize=(2.872, 2.306))
        ax_u.plot(d['voltages'], d['powers'], 'o', markersize=2,
                  color=d['color'], markeredgewidth=0)
        ax_u.plot(d['voltages'], d['fit_powers'], '-', linewidth=0.8, color=d['color'],
                  label=f"Linear fit: y={d['coeffs'][0]:.3f}x+{d['coeffs'][1]:.3f}\nR2={d['r_squared']:.4f}")
        ax_u.set_xlabel('Voltage (V)')
        ax_u.set_ylabel('Power (mW)')
        ax_u.set_title(f"Power vs Voltage: {laser['name']}")
        ax_u.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
        ax_u.grid(False)
        for spine in ['top', 'right']:
            ax_u.spines[spine].set_visible(False)
        ax_u.spines['bottom'].set_position(('outward', 5))
        ax_u.spines['left'].set_position(('outward', 5))
        plt.tight_layout()
        safe_name = laser['name'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
        save_figure_safely(fig_u, os.path.join(fig_output_path,
                                                f'power_vs_voltage_{safe_name}.svg'))


# =============================================================================
# entry point
# =============================================================================

if __name__ == "__main__":
    all_ms_files        = glob.glob(os.path.join(base_path, '*ms.txt'))
    all_hr_files        = glob.glob(os.path.join(base_path, '*hr.txt'))
    power_voltage_files = glob.glob(os.path.join(base_path, '*power*.xlsx'))

    print(f"base_path:   {base_path}")
    print(f"output_path: {output_path}")
    print(f"MS files:    {len(all_ms_files)}")
    print(f"HR files:    {len(all_hr_files)}")
    print(f"P-V files:   {len(power_voltage_files)}")

    for file in all_ms_files:
        analyze_power_stability(file, output_path)
    if all_ms_files:
        create_stability_overlay_plots(all_ms_files, output_path,
                                       file_type='ms', exclude_lasers=['chengchun'])
        create_stability_overlay_plots(all_ms_files, output_path,
                                       file_type='ms', exclude_lasers=None)

    for file in all_hr_files:
        analyze_power_stability(file, output_path)
    if all_hr_files:
        create_stability_overlay_plots(all_hr_files, output_path,
                                       file_type='hr', exclude_lasers=['chengchun'])
        create_stability_overlay_plots(all_hr_files, output_path,
                                       file_type='hr', exclude_lasers=None)

    for file in power_voltage_files:
        analyze_power_vs_voltage(file, output_path)

    print(f"\nAll figures saved to: {output_path}")
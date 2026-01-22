import sys
import os

# Try to import required packages with error handling
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime
    from matplotlib.colors import to_rgba

except ImportError as e:
    print(f"Error importing basic packages: {e}")
    print("\nTrying to install missing packages...")
    import subprocess
    packages = ['pandas', 'numpy', 'matplotlib']
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime

try:
    from scipy.signal import butter, filtfilt, find_peaks
except ImportError:
    print("scipy not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'scipy'])
    from scipy.signal import butter, filtfilt, find_peaks

try:
    import openpyxl
except ImportError:
    print("openpyxl not found. Installing for Excel support...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl'])
    import openpyxl

# Set up plotting style
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 8
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Calibri', 'Arial', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'

def lighten_color(color, amount=0.7):
    """
    Lighten a color by mixing with white.
    amount: 0.0 = original color, 1.0 = white
    """
    try:
        rgba = to_rgba(color)
        # Mix with white (1, 1, 1) by amount
        light_rgba = tuple(rgba[i] * (1 - amount) + amount for i in range(3)) + (1.0,)
        return light_rgba
    except:
        return color

def save_figure_safely(fig, filepath):
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        if filepath.endswith('.svg'):
            fig.savefig(filepath, bbox_inches='tight', format='svg', 
                       metadata={'Date': None})
        else:
            fig.savefig(filepath, bbox_inches='tight')
        print(f"Figure saved successfully to: {filepath}")
        return True
    except Exception as e:
        return False
    finally:
        plt.close(fig)

def parse_power_stability_file(filename):
    """
    Parse power stability files (ms and hr files)
    """
    data = []
    wavelength = None
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Extract wavelength from header
        for line in lines[:10]:
            if 'Wave' in line:
                wavelength = line.split()[1].replace('nm', '')
                break
        
        # Parse data lines
        for line in lines:
            if 'W' in line and '/' in line: 
                parts = line.strip().split()
                if len(parts) >= 3:  # Need date, time, power, W
                    try:
                        timestamp_str = f"{parts[0]} {parts[1]}"
                        power_str = parts[2]
                        # Parse timestamp
                        timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S.%f')
                        power = float(power_str) * 1000  # Convert to mW
                        data.append({'timestamp': timestamp, 'power_mW': power})
                    except Exception as e:
                        continue
    
    df = pd.DataFrame(data)
    if not df.empty and len(df) > 1:
        # Calculate relative time in appropriate units
        df['time_seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()
        
    return df, wavelength

def analyze_power_stability(filename):
    """
    Analyze power stability for ms and hr files
    """
    df, wavelength = parse_power_stability_file(filename)
    
    if df.empty:
        print(f"No data found in {filename}")
        return
    
    # Determine if this is ms or hr file
    base_name = os.path.basename(filename)
    
    if 'ms' in base_name:
        df['time_ms'] = df['time_seconds'] * 1000
        max_time_ms = df['time_ms'].max()
        
        df_analysis = df.copy()
        
        # Shift time to start at 0 for the analysis window
        df_analysis['time_ms_windowed'] = df_analysis['time_ms'] - df_analysis['time_ms'].min()
        df_analysis['time_s_windowed'] = df_analysis['time_ms_windowed'] / 1000  # For display in seconds
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # Calculate statistics
        mean_power = df_analysis['power_mW'].mean()
        df_analysis['percent_deviation'] = ((df_analysis['power_mW'] - mean_power) / mean_power) * 100
        std_percent = df_analysis['percent_deviation'].std()
        cv = (df_analysis['power_mW'].std() / mean_power) * 100
        
        # TOP PLOT: Raw absolute time 
        raw_data_color = lighten_color('blue', 0.3)
        ax1.plot(df_analysis['time_s_windowed'], df_analysis['power_mW'], 
                color=raw_data_color, linewidth=0.8, label='Raw data')
        ax1.axhline(mean_power, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_power:.3f} mW')
        orange_light = lighten_color('orange', 0.3)
        orange_fill = lighten_color('orange', 0.8)
        ax1.axhline(mean_power + df_analysis['power_mW'].std(), 
                   color=orange_light, linestyle=':', linewidth=1.5, label='±1σ')
        ax1.axhline(mean_power - df_analysis['power_mW'].std(), 
                   color=orange_light, linestyle=':', linewidth=1.5)
        ax1.fill_between(df_analysis['time_s_windowed'],
                        mean_power - df_analysis['power_mW'].std(),
                        mean_power + df_analysis['power_mW'].std(),
                        color=orange_fill)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Power (mW)')
        ax1.set_title(f'Power Stability - {base_name} - {wavelength}nm\n'
                     f'Mean: {mean_power:.3f} mW, CV: {cv:.2f}%, N={len(df_analysis)} samples')
        ax1.legend(loc='upper right')
        ax1.grid(False)
        # remove top and right spines
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax1.spines['bottom'].set_position(('outward', 5))
        ax1.spines['left'].set_position(('outward', 5))
        
        # MIDDLE PLOT: Rolling average 
        # Create rolling average with small window to smooth noise
        window_size_ms = 50  # Use 50-point rolling window
        
        if len(df_analysis) >= window_size_ms:
            df_sorted = df_analysis.sort_values('time_ms_windowed').reset_index(drop=True)
            
            # Calculate rolling mean and std
            rolling_mean = df_sorted['power_mW'].rolling(window=window_size_ms, center=True).mean()
            rolling_std = df_sorted['power_mW'].rolling(window=window_size_ms, center=True).std()
            
            # Plot rolling average
            ax2.plot(df_sorted['time_ms_windowed'], rolling_mean, 
                    'b-', linewidth=2, label=f'{window_size_ms}-point rolling avg')
            
            # Add shaded band for ±1 std dev
            blue_fill = lighten_color('blue', 0.7)
            ax2.fill_between(df_sorted['time_ms_windowed'],
                            rolling_mean - rolling_std,
                            rolling_mean + rolling_std,
                            color=blue_fill, label='±1σ range')
            
            ax2.axhline(mean_power, color='red', linestyle='--', linewidth=1.5)
        else:
            raw_color = lighten_color('blue', 0.5)
            ax2.plot(df_analysis['time_ms_windowed'], df_analysis['power_mW'], 
                    color=raw_color, linewidth=1, label='Raw data')
            ax2.axhline(mean_power, color='black', linestyle='--', linewidth=1.5)
        
        ax2.set_ylabel('Power (mW)')
        ax2.set_title(f'Rolling Average Analysis ({window_size_ms}-point window)')
        ax2.legend(loc='upper right')
        ax2.grid(False)
        # Minimal axis design
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        # Remove x-axis ticks and labels since it shares scale with top plot
        ax2.set_xticklabels([])
        ax2.tick_params(axis='x', which='both', bottom=False)
        
        # Align y-axis with ax1
        ax2.set_ylim(ax1.get_ylim())
        
        # BOTTOM PLOT: Line plot instead of histogram
        # Calculate histogram data with equal bin widths
        counts, bin_edges = np.histogram(df_analysis['percent_deviation'], bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Plot as line
        ax3.plot(bin_centers, counts, 'b-', linewidth=2, label='Distribution')
        ax3.axvline(0, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_power:.3f} mW')
        ax3.axvline(-std_percent, color='orange', linestyle=':', linewidth=1.5, 
                   label=f'±1σ: {std_percent:.3f}%')
        ax3.axvline(std_percent, color='orange', linestyle=':', linewidth=1.5)
        
        ax3.set_xlabel('% Deviation from Mean')
        ax3.set_ylabel('Frequency')
        ax3.set_title(f'Power Deviation Distribution (CV: {cv:.2f}%)')
        ax3.legend(loc='upper right')
        ax3.grid(False)
        # Minimal axis design
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax3.spines['bottom'].set_position(('outward', 5))
        ax3.spines['left'].set_position(('outward', 5))
        
        plt.tight_layout()
        
        # Save figure
        dir_path = os.path.dirname(filename)
        output_path = os.path.join(dir_path, f'{os.path.splitext(base_name)[0]}_stability.svg')
        save_figure_safely(fig, output_path)
        
    else:  # Hour scale analysis
        df['time_hours'] = df['time_seconds'] / 3600
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # Calculate statistics
        mean_power = df['power_mW'].mean()
        std_power = df['power_mW'].std()
        cv = (std_power / mean_power) * 100
        df['percent_deviation'] = ((df['power_mW'] - mean_power) / mean_power) * 100
        
        # Calculate drift
        initial_power = df['power_mW'].iloc[0]
        final_power = df['power_mW'].iloc[-1]
        drift_percent = ((final_power - initial_power) / initial_power) * 100
        
        # TOP PLOT: Power vs time with stability zones
        raw_color = lighten_color('blue', 0.3)
        ax1.plot(df['time_hours'], df['power_mW'], color=raw_color, linewidth=1, label='Raw data')
        ax1.axhline(mean_power, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_power:.3f} mW')
        green_light = lighten_color('green', 0.3)
        orange_light = lighten_color('orange', 0.3)
        green_fill = lighten_color('green', 0.8)
        ax1.axhline(mean_power + 0.005*mean_power, color=green_light, linestyle=':', 
                   linewidth=1.5, label='±0.5%')
        ax1.axhline(mean_power - 0.005*mean_power, color=green_light, linestyle=':', 
                   linewidth=1.5)
        ax1.axhline(mean_power + 0.01*mean_power, color=orange_light, linestyle=':', 
                   linewidth=1.5, label='±1.0%')
        ax1.axhline(mean_power - 0.01*mean_power, color=orange_light, linestyle=':', 
                   linewidth=1.5)
        ax1.fill_between(df['time_hours'],
                        mean_power - 0.005*mean_power,
                        mean_power + 0.005*mean_power,
                        color=green_fill, label='±0.5% zone')
        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('Power (mW)')
        ax1.set_title(f'Power Stability Over Time - {base_name} - {wavelength}nm\n'
                     f'Mean: {mean_power:.3f} mW, CV: {cv:.2f}%, Drift: {drift_percent:+.2f}%')
        ax1.legend(loc='upper right')
        ax1.grid(False)
        # Minimal axis design
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax1.spines['bottom'].set_position(('outward', 5))
        ax1.spines['left'].set_position(('outward', 5))
        
        # MIDDLE PLOT: Running average
        df['time_minutes'] = df['time_seconds'] / 60
        df_sorted = df.sort_values('time_minutes')
        
        # Create 1-minute time grid
        time_grid = np.arange(df_sorted['time_minutes'].min(), 
                             df_sorted['time_minutes'].max(), 1)
        
        # Calculate running average for each point on the grid
        window_size = 1  # minutes
        running_avg = []
        running_std = []
        valid_times = []
        
        for t in time_grid:
            # Get data within window [t, t+10]
            mask = (df_sorted['time_minutes'] >= t) & (df_sorted['time_minutes'] < t + window_size)
            window_data = df_sorted[mask]['power_mW']
            
            if len(window_data) > 0:
                running_avg.append(window_data.mean())
                running_std.append(window_data.std())
                valid_times.append(t / 60)  # Convert to hours
        
        running_avg = np.array(running_avg)
        running_std = np.array(running_std)
        valid_times = np.array(valid_times)
        
        ax2.plot(valid_times, running_avg, 'bo-', linewidth=2, markersize=3, 
                label='10-min running average (1-min step)', markeredgewidth=0)
        blue_fill = lighten_color('blue', 0.7)
        ax2.fill_between(valid_times,
                        running_avg - running_std,
                        running_avg + running_std,
                        color=blue_fill, label='±1σ range')
        ax2.axhline(mean_power, color='red', linestyle='--', linewidth=2)
        ax2.set_ylabel('Power (mW)')
        ax2.set_title('Running Average Analysis (10-min window, 1-min step)')
        ax2.legend(loc='upper right')
        ax2.grid(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        ax2.set_xticklabels([])
        ax2.tick_params(axis='x', which='both', bottom=False)
        
        # Align y-axis with ax1
        ax2.set_ylim(ax1.get_ylim())
        
        # BOTTOM PLOT: Line plot instead of histogram
        counts, bin_edges = np.histogram(df['percent_deviation'], bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Plot as line
        ax3.plot(bin_centers, counts, 'b-', linewidth=2, label='Distribution')
        ax3.axvline(0, color='red', linestyle='--', linewidth=2)
        
        # Calculate time in zones
        time_in_05 = (df['percent_deviation'].abs() <= 0.5).sum() / len(df) * 100
        time_in_10 = (df['percent_deviation'].abs() <= 1.0).sum() / len(df) * 100
        
        ax3.set_xlabel('% Deviation from Mean')
        ax3.set_ylabel('Frequency')
        ax3.set_title(f'Power Deviation Distribution\n'
                     f'Time in ±0.5%: {time_in_05:.1f}% | Time in ±1.0%: {time_in_10:.1f}%')
        ax3.legend(loc='upper right')
        ax3.grid(False)
        # Minimal axis design
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax3.spines['bottom'].set_position(('outward', 5))
        ax3.spines['left'].set_position(('outward', 5))
        
        plt.tight_layout()
        
        # Save figure
        dir_path = os.path.dirname(filename)
        output_path = os.path.join(dir_path, f'{os.path.splitext(base_name)[0]}_stability.svg')
        save_figure_safely(fig, output_path)

def create_stability_overlay_plots(files, file_type='ms', exclude_lasers=None):
    """
    Create overlay plots comparing multiple lasers with 3-subplot structure
    Color coding: Chengchun (unstable) = red, All others (stable) = distinct colors
    Includes vertical reference bar showing stable laser power variation range

    """

    if not files:
        print(f"No {file_type} files to overlay")
        return
    
    # First pass for consistent time alignment
    all_parsed_data = {}
    print(f"\nParsing all {file_type} files...")
    for file in files:
        base_name = os.path.basename(file)
        laser_name = base_name.replace(f'_{file_type}.txt', '').replace('.txt', '')
        print(f"  Found file: {base_name} → laser name: {laser_name}")
        df, wavelength = parse_power_stability_file(file)
        if not df.empty:
            all_parsed_data[laser_name] = {
                'df': df,
                'wavelength': wavelength,
                'file': file
            }
    
    print(f"  Total lasers parsed: {len(all_parsed_data)}")
    print(f"  Laser names: {list(all_parsed_data.keys())}")
    
    # Calculate min_time from ALL lasers
    if file_type == 'ms':
        global_min_time = min([data['df']['time_seconds'].max() for data in all_parsed_data.values()])
    else:
        global_min_time = None
    
    #Filter to only include non-excluded lasers for plotting
    laser_data = {}
    print(f"\nFiltering lasers (exclude_lasers={exclude_lasers})...")
    for laser_name, data in all_parsed_data.items():
        # Check if this laser should be excluded
        if exclude_lasers and any(excluded.lower() in laser_name.lower() for excluded in exclude_lasers):
            print(f"  EXCLUDING: {laser_name}")
            continue
        
        print(f"  INCLUDING: {laser_name}")
        df = data['df']
        mean_power = df['power_mW'].mean()
        df['percent_deviation'] = ((df['power_mW'] - mean_power) / mean_power) * 100
        
        laser_data[laser_name] = {
            'df': df,
            'wavelength': data['wavelength'],
            'mean': mean_power,
            'std': df['power_mW'].std(),
            'cv': (df['power_mW'].std() / mean_power) * 100,
            'min': df['power_mW'].min(),
            'max': df['power_mW'].max()
        }
    
    print(f"  Total lasers after filtering: {len(laser_data)}")
    
    if not laser_data:
        print(f"No valid laser data found for overlay")
        return
    
    # Calculate power ranges for reference bar
    all_mins = [data['min'] for data in laser_data.values()]
    all_maxs = [data['max'] for data in laser_data.values()]
    overall_min = min(all_mins)
    overall_max = max(all_maxs)
    overall_range = overall_max - overall_min
    
    # Determine suffix for filename
    suffix = "_stable" if exclude_lasers else "_all"
    
    # Color palette: Stable lasers = 3 distinct blue shades, Unstable (Chengchun) = 75% grey
    colors = {}
    stable_lasers = [name for name in laser_data.keys() if 'chengchun' not in name.lower()]
    
    # 3 distinct blue shades for 3 stable lasers
    blue_shades = ['#08306B', '#2171B5', '#6BAED6']  # Dark, medium, light blue
    
    if exclude_lasers:  # Stable lasers only
        for i, laser_name in enumerate(stable_lasers):
            colors[laser_name] = blue_shades[i % len(blue_shades)]
    else:  # All lasers - distinct blues for stable, 75% grey for unstable
        stable_idx = 0
        for laser_name in laser_data.keys():
            if 'chengchun' in laser_name.lower():
                colors[laser_name] = '#404040'  # 75% grey for unstable
            else:
                colors[laser_name] = blue_shades[stable_idx % len(blue_shades)]
                stable_idx += 1
    
    # Create time unit
    time_unit = 'ms' if file_type == 'ms' else 'hours'
    time_scale = 1000 if file_type == 'ms' else 1/3600
    
    # Reference line color - red for visual contrast against blue/grey data
    ref_line_color = '#DC143C'  # Crimson red
    
    # For MS files: Cut all data to match shortest recording
    if file_type == 'ms':
        min_time = global_min_time
        print(f"\nMS files: Aligning all plots to shortest recording = {min_time:.3f} seconds ({min_time*1000:.1f} ms)")
        
        # Create cut dataframes and recalculate statistics
        laser_data_cut = {}
        for laser_name, data in laser_data.items():
            df_cut = data['df'][data['df']['time_seconds'] <= min_time].copy()
            mean_power_cut = df_cut['power_mW'].mean()
            df_cut['percent_deviation'] = ((df_cut['power_mW'] - mean_power_cut) / mean_power_cut) * 100
            
            laser_data_cut[laser_name] = {
                'df': df_cut,
                'wavelength': data['wavelength'],
                'mean': mean_power_cut,
                'std': df_cut['power_mW'].std(),
                'cv': (df_cut['power_mW'].std() / mean_power_cut) * 100,
                'min': df_cut['power_mW'].min(),
                'max': df_cut['power_mW'].max()
            }
            print(f"  {laser_name}: {len(data['df'])} → {len(df_cut)} points")
        
        # Use cut data for plotting and recalculate ranges
        plot_data = laser_data_cut
        all_mins = [data['min'] for data in plot_data.values()]
        all_maxs = [data['max'] for data in plot_data.values()]
        overall_min = min(all_mins)
        overall_max = max(all_maxs)
        overall_range = overall_max - overall_min
        
        # Also calculate full range from ALL lasers (including excluded) for y-axis matching
        all_laser_data_cut = {}
        for laser_name, data in all_parsed_data.items():
            df_cut = data['df'][data['df']['time_seconds'] <= min_time].copy()
            all_laser_data_cut[laser_name] = {
                'min': df_cut['power_mW'].min(),
                'max': df_cut['power_mW'].max()
            }
        full_range_min = min([d['min'] for d in all_laser_data_cut.values()])
        full_range_max = max([d['max'] for d in all_laser_data_cut.values()])
    else:
        # For HR files: Use full data
        plot_data = laser_data
        
        # Calculate full range from ALL lasers (including excluded) for y-axis matching
        full_range_min = min([data['df']['power_mW'].min() for data in all_parsed_data.values()])
        full_range_max = max([data['df']['power_mW'].max() for data in all_parsed_data.values()])
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(3.241, 3.937))
    
    plt.subplots_adjust(right=0.92, hspace=0.6)
    
    for laser_name, data in plot_data.items():
        df = data['df']
        time_data = df['time_seconds'] * time_scale
        

        line_color = lighten_color(colors[laser_name], 0.2)
        ax1.plot(time_data, df['power_mW'], 
                linewidth=0.5, color=line_color, label=f"{laser_name} ({data['wavelength']}nm)")
        
        mean_color = lighten_color(colors[laser_name], 0.7)
        ax1.axhline(data['mean'], color=mean_color, linestyle='-', 
                   linewidth=0.3)
    
    ax1.set_xlabel(f'Time ({time_unit})')
    ax1.set_ylabel('Power (mW)')
    ax1.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
    ax1.grid(False)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_position(('outward', 5))
    ax1.spines['left'].set_position(('outward', 5))
    
    if file_type == 'ms':
        data_max_time = min_time * 1000
    else:
        # For hr files, get the max time from all data
        data_max_time = max([data['df']['time_seconds'].max() / 3600 for data in plot_data.values()])
    
    ax1.set_xlim(0, data_max_time)
    
    # For stable-only plots
    if exclude_lasers:
        # Calculate where stable data center sits relative to all-lasers plot
        stable_center = np.mean([data['mean'] for data in plot_data.values()])
        
        # Calculate relative position of stable data in all-lasers y-range
        padding_all = (full_range_max - full_range_min) * 0.05
        y_min_all = full_range_min - padding_all
        y_max_all = full_range_max + padding_all
        rel_pos = (stable_center - y_min_all) / (y_max_all - y_min_all)
        
        # Set ±1 mW range positioned so stable_center is at same relative position
        # Total range = 2 mW, stable_center at rel_pos from bottom
        y_min_stable = stable_center - (rel_pos * 2)
        y_max_stable = stable_center + ((1 - rel_pos) * 2)
        ax1.set_ylim(y_min_stable, y_max_stable)
        
    def add_reference_bar(ax, fig, stable_min, stable_max, stable_range, exclude_lasers, ref_color):
        """Add vertical reference bar to the right of the plot"""
        ax_bbox = ax.get_position()
        ylim = ax.get_ylim()
        
        if exclude_lasers:
            # Stable lasers only: show their range in crimson red (no cap lines)
            y_min_norm = (stable_min - ylim[0]) / (ylim[1] - ylim[0])
            y_max_norm = (stable_max - ylim[0]) / (ylim[1] - ylim[0])
            
            # Draw line in figure coordinates
            line = plt.Line2D([ax_bbox.x1 + 0.01, ax_bbox.x1 + 0.01], 
                             [ax_bbox.y0 + y_min_norm * ax_bbox.height, 
                              ax_bbox.y0 + y_max_norm * ax_bbox.height],
                             transform=fig.transFigure, color=ref_color, linewidth=1.5)
            fig.add_artist(line)
            
            return f'Stable range: {stable_range:.2f} mW'
        else:
            # All lasers: show stable range in crimson red for comparison (no cap lines)
            y_min_norm = (stable_min - ylim[0]) / (ylim[1] - ylim[0])
            y_max_norm = (stable_max - ylim[0]) / (ylim[1] - ylim[0])
            
            # Draw line in figure coordinates
            line = plt.Line2D([ax_bbox.x1 + 0.01, ax_bbox.x1 + 0.01], 
                             [ax_bbox.y0 + y_min_norm * ax_bbox.height, 
                              ax_bbox.y0 + y_max_norm * ax_bbox.height],
                             transform=fig.transFigure, color=ref_color, linewidth=1.5)
            fig.add_artist(line)
            fig.add_artist(line)
            
            return f'Stable range: {stable_range:.2f} mW'
    
    # Calculate stable laser range for reference bar
    stable_laser_data = {k: v for k, v in plot_data.items() if 'chengchun' not in k.lower()}
    if stable_laser_data:
        stable_mins = [data['min'] for data in stable_laser_data.values()]
        stable_maxs = [data['max'] for data in stable_laser_data.values()]
        stable_min = min(stable_mins)
        stable_max = max(stable_maxs)
        stable_range = stable_max - stable_min
        
        # Add reference bar to ax1
        ref_label = add_reference_bar(ax1, fig, stable_min, stable_max, stable_range, 
                                      exclude_lasers, ref_line_color)
        
        # Add to legend for ax1
        ax1.plot([], [], color=ref_line_color, linewidth=1.5, label=ref_label)
        ax1.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
    
    # MIDDLE PLOT
    if file_type == 'ms':
        # For ms files: Use rolling average to smooth noise
        window_size_ms = 50  # 50-point rolling window
        
        for laser_name, data in plot_data.items():
            df = data['df'].copy()
            df['time_ms'] = df['time_seconds'] * 1000
            
            # Sort by time
            df_sorted = df.sort_values('time_ms').reset_index(drop=True)
            
            if len(df_sorted) >= window_size_ms:
                print(f"    → Using rolling average")
                # Calculate rolling mean and std with min_periods to avoid NaN at edges
                rolling_mean = df_sorted['power_mW'].rolling(
                    window=window_size_ms, 
                    center=True, 
                    min_periods=1
                ).mean()
                
                rolling_std = df_sorted['power_mW'].rolling(
                    window=window_size_ms, 
                    center=True, 
                    min_periods=1
                ).std()
                
                # Plot rolling average
                line_color = lighten_color(colors[laser_name], 0.1)
                ax2.plot(df_sorted['time_ms'], rolling_mean, 
                        linewidth=0.8,
                        label=f"{laser_name} ({window_size_ms}-pt avg)", 
                        color=line_color)
                
                # Add shaded band for ±1 std dev - use lighter color
                fill_color = lighten_color(colors[laser_name], 0.75)
                ax2.fill_between(df_sorted['time_ms'],
                                rolling_mean - rolling_std,
                                rolling_mean + rolling_std,
                                color=fill_color)
            else:
                print(f"    → Using raw data (not enough points)")
                # Fall back to raw data if not enough points
                line_color = lighten_color(colors[laser_name], 0.2)
                ax2.plot(df_sorted['time_ms'], df_sorted['power_mW'], 
                        linewidth=0.5, 
                        label=f"{laser_name}", color=line_color)
        
        ax2.set_ylabel('Power (mW)')
        ax2.set_title(f'Rolling Average Analysis ({window_size_ms}-point window)')
        ax2.set_xlim(0, min_time * 1000)
        ax2.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
        ax2.grid(False)
        # Minimal axis design
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        # Remove x-axis ticks and labels since it shares scale with top plot
        ax2.set_xticklabels([])
        ax2.tick_params(axis='x', which='both', bottom=False)
        
        # MODIFIED: Align y-axis with ax1 to ensure consistent height
        ax2.set_ylim(ax1.get_ylim())
        
    else:  # hr files
        # For hr files: Plot running average with rolling std dev as shaded band
        
        for laser_name, data in laser_data.items():
            df = data['df'].copy()
            df['time_minutes'] = df['time_seconds'] / 60
            df['time_hours'] = df['time_seconds'] / 3600
            
            # Sort by time
            df_sorted = df.sort_values('time_minutes').reset_index(drop=True)
        
            # Calculate rolling mean and std with centred window
            time_min = df_sorted['time_minutes'].min()
            time_max = df_sorted['time_minutes'].max()
            window_size = 2  # minutes
            half_window = window_size / 2
            time_grid = np.arange(time_min + half_window, time_max - half_window, 0.25)  # Centred grid
            
            rolling_times = []
            rolling_means = []
            rolling_stds = []
            
            for idx, t in enumerate(time_grid):
                # CENTRED window: [t-1, t+1]
                mask = (df_sorted['time_minutes'] >= t - half_window) & (df_sorted['time_minutes'] < t + half_window)
                window_data = df_sorted[mask]['power_mW']
                
                if len(window_data) > 0:
                    mean_val = window_data.mean()
                    std_val = window_data.std()
                    t_hours = t / 60
                    
                    rolling_times.append(t_hours)  
                    rolling_means.append(mean_val)
                    rolling_stds.append(std_val)

            rolling_times = np.array(rolling_times)
            rolling_means = np.array(rolling_means)
            rolling_stds = np.array(rolling_stds)
            
            # Plot running average line
            line_color = lighten_color(colors[laser_name], 0.1)
            ax2.plot(rolling_times, rolling_means, 
                    linewidth=0.8,
                    label=f"{laser_name} (2-min avg)", color=line_color)
            
            # Add shaded band for ±1 std dev - use lighter color
            fill_color = lighten_color(colors[laser_name], 0.75)
            ax2.fill_between(rolling_times,
                            rolling_means - rolling_stds,
                            rolling_means + rolling_stds,
                            color=fill_color)
        
        ax2.set_ylabel('Power (mW)')
        ax2.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
        ax2.grid(False)
        # Minimal axis design
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        # Add gap/break at origin by offsetting spines
        ax2.spines['bottom'].set_position(('outward', 5))
        ax2.spines['left'].set_position(('outward', 5))
        # Remove x-axis ticks and labels since it shares scale with top plot
        ax2.set_xticklabels([])
        ax2.tick_params(axis='x', which='both', bottom=False)
        
        # MODIFIED: Align y-axis with ax1 to ensure consistent height
        ax2.set_ylim(ax1.get_ylim())
        
        # Set tight x-axis limits for hr files
        max_time_hr = max([data['df']['time_seconds'].max() / 3600 for data in laser_data.values()])
        ax2.set_xlim(0, max_time_hr)

    # Add reference bar to ax2 as well
    if stable_laser_data:
        add_reference_bar(ax2, fig, stable_min, stable_max, stable_range, 
                         exclude_lasers, ref_line_color)
    
    # BOTTOM PLOT: Line plot instead of histogram
    all_deviations = []
    for laser_name, data in plot_data.items():
        df = data['df']
        all_deviations.extend(df['percent_deviation'].tolist())
        
        if exclude_lasers:
            # For stable lasers only: use line plots with wider bins for smoother lines
            counts, bin_edges = np.histogram(df['percent_deviation'], bins=15)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Plot as line
            line_color = lighten_color(colors[laser_name], 0.2)
            ax3.plot(bin_centers, counts, 
                    linewidth=0.8,
                    label=f"{laser_name} (CV={data['cv']:.2f}%)", 
                    color=line_color)
        else:
            # For all lasers: use line plots with wider bins for smoother lines
            counts, bin_edges = np.histogram(df['percent_deviation'], bins=15)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Plot as line
            line_color = lighten_color(colors[laser_name], 0.2)
            ax3.plot(bin_centers, counts, 
                    linewidth=0.8,
                    label=f"{laser_name} (CV={data['cv']:.2f}%)", 
                    color=line_color)
    
    # Add only the mean reference line
    ax3.axvline(0, color='black', linestyle='-', linewidth=0.8, label='Mean')
    
    ax3.set_xlabel('% Deviation from Mean')
    ax3.set_ylabel('Frequency')
    ax3.legend(loc='upper right', fontsize=4.5, framealpha=0.95)
    ax3.grid(False)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['bottom'].set_position(('outward', 5))
    ax3.spines['left'].set_position(('outward', 5))
    
    if all_deviations:
        min_dev = min(all_deviations)
        max_dev = max(all_deviations)
        padding = (max_dev - min_dev) * 0.05  # 5% padding
        ax3.set_xlim(min_dev - padding, max_dev + padding)
    
    # Save figure 
    if files:
        dir_path = os.path.dirname(files[0])
        output_path = os.path.join(dir_path, f'overlay_{file_type}{suffix}.svg')

        try:
            dir_path_check = os.path.dirname(output_path)
            if dir_path_check and not os.path.exists(dir_path_check):
                os.makedirs(dir_path_check)
            
            fig.savefig(output_path, bbox_inches='tight', pad_inches=0.1, format='svg')
            print(f"Figure saved successfully to: {output_path}")
        except Exception as e:
            print(f"Error saving figure: {e}")
        finally:
            plt.close(fig)

def analyze_power_vs_voltage(filename):
    """
    Analyze power vs voltage linearity from Excel file
    Handles multi-column format with laser names as headers and Voltage/Power sub-headers
    """
    # Color palette: Stable lasers = 3 distinct blue shades, Unstable (Chengchun) = 75% grey
    blue_shades = ['#08306B', '#2171B5', '#6BAED6']  # Dark, medium, light blue
    
    color_map = {
        'obis 473': blue_shades[0],     # Dark blue
        'obis_473': blue_shades[0],
        'obis 594': blue_shades[1],     # Medium blue
        'obis_594': blue_shades[1],
        'oxxius 450': blue_shades[2],   # Light blue
        'oxxius_450': blue_shades[2],
        'chengchun': '#404040',         # 75% grey for unstable
        'oxxius': blue_shades[2],       # Same as oxxius 450
    }
    
    def get_laser_color(laser_name):
        laser_lower = laser_name.lower()
        for key, color in color_map.items():
            if key in laser_lower:
                return color
        # Default to medium blue for any other stable lasers
        return blue_shades[1]
    
    def should_combine_lasers(laser_name):
        laser_lower = laser_name.lower()
        # Exclude Chengchun explicitly
        if 'chengchun' in laser_lower:
            return False
        # Include only stable lasers: Obis 594, Oxxius 450, Obis 473
        return ('594' in laser_lower or 
                '450' in laser_lower or
                ('obis' in laser_lower and '473' in laser_lower) )
    try:
        # Skip temporary Excel files (start with ~$)
        if os.path.basename(filename).startswith('~$'):
            print(f"Skipping temporary file: {filename}")
            return
            
        # Read the Excel file
        df = pd.read_excel(filename)
        
        # Extract laser names from column headers (non-Unnamed columns)
        laser_info = []
        for i in range(0, len(df.columns), 2):
            if i < len(df.columns):
                laser_col_name = df.columns[i]
                if not str(laser_col_name).startswith('Unnamed'):
                    laser_info.append({
                        'name': str(laser_col_name),
                        'voltage_col': df.columns[i],
                        'power_col': df.columns[i + 1] if i + 1 < len(df.columns) else None
                    })
        
        if not laser_info:
            print(f"Could not identify any laser columns in {filename}")
            return
            
        print(f"\nFound {len(laser_info)} lasers in file:")
        for laser in laser_info:
            print(f"  - {laser['name']}")
        
        # Separate lasers into combined and individual
        combined_lasers = []
        individual_lasers = []
        
        for laser in laser_info:
            if should_combine_lasers(laser['name']):
                combined_lasers.append(laser)
            else:
                individual_lasers.append(laser)
        
        # Store all laser data for combined plots
        all_laser_data = {}
        
        # Process each laser and store data
        for laser in laser_info:
            laser_name = laser['name']
            voltage_col = laser['voltage_col']
            power_col = laser['power_col']
            
            if power_col is None:
                print(f"\nSkipping {laser_name}: No power column found")
                continue
            
            # Get color for this laser
            laser_color = get_laser_color(laser_name)
            print(f"\n  Processing {laser_name} with color: {laser_color}")
            
            # Extract data (skip row 0 which contains 'Voltage'/'Power' labels)
            df_laser = df[[voltage_col, power_col]].iloc[1:].copy()
            
            # Rename columns for easier handling
            df_laser.columns = ['Voltage', 'Power']
            
            # Convert to numeric
            df_laser['Voltage'] = pd.to_numeric(df_laser['Voltage'], errors='coerce')
            df_laser['Power'] = pd.to_numeric(df_laser['Power'], errors='coerce')
            df_laser = df_laser.dropna()
            
            if df_laser.empty:
                print(f"  No valid data for {laser_name}")
                continue
            
            # Sort by voltage
            df_laser = df_laser.sort_values(by='Voltage')
            
            voltages = df_laser['Voltage'].values
            powers = df_laser['Power'].values
            
            print(f"  Data points: {len(voltages)}")
            print(f"  Voltage range: {voltages.min():.4f} - {voltages.max():.4f} V")
            print(f"  Power range: {powers.min():.2f} - {powers.max():.2f} mW")
            
            # Perform linear fit on ALL data
            coeffs = np.polyfit(voltages, powers, 1)
            poly = np.poly1d(coeffs)
            fit_powers = poly(voltages)
            
            # Calculate R² for full range
            ss_res = np.sum((powers - fit_powers) ** 2)
            ss_tot = np.sum((powers - np.mean(powers)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            print(f"  Linear fit: Power = {coeffs[0]:.3f} × Voltage + {coeffs[1]:.3f}")
            print(f"  R² (full range) = {r_squared:.6f}")
            
            # Store data for combined plots
            all_laser_data[laser_name] = {
                'voltages': voltages,
                'powers': powers,
                'coeffs': coeffs,
                'poly': poly,
                'fit_powers': fit_powers,
                'r_squared': r_squared,
                'color': laser_color
            }
            
            # Create individual plots only for non-combined lasers
            if not should_combine_lasers(laser_name):
                # Create single plot for FULL RANGE
                fig1, ax1 = plt.subplots(1, 1, figsize=(2.872, 2.306))

                plot_color = 'black' if ('obis' in laser_name.lower() and '473' in laser_name.lower()) else laser_color
                
                ax1.plot(voltages, powers, 'o', markersize=2, label='Measured', 
                        markerfacecolor=plot_color, markeredgecolor=plot_color)
                ax1.plot(voltages, fit_powers, '-', linewidth=0.8, 
                        label=f'Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR² = {r_squared:.4f}',
                        color=plot_color)
            
                ax1.set_xlabel('Voltage (V)')
                ax1.set_ylabel('Power (mW)')
                ax1.set_title(f'Power vs Voltage: {laser_name}')
                ax1.legend(loc='upper left')
                ax1.grid(False)
                # Minimal axis design
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
                # Add gap/break at origin by offsetting spines
                ax1.spines['bottom'].set_position(('outward', 5))
                ax1.spines['left'].set_position(('outward', 5))
                
                plt.tight_layout()
                
                # Save figure with laser name in filename
                dir_path = os.path.dirname(filename)
                safe_laser_name = laser_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
                output_path1 = os.path.join(dir_path, f'power_vs_voltage_{safe_laser_name}.svg')
                save_figure_safely(fig1, output_path1)
                
                # Create low-voltage zoom plot 
                low_voltage_threshold = 0.05  
                low_voltage_mask = voltages <= low_voltage_threshold
                n_low_voltage = np.sum(low_voltage_mask)
                
                print(f"  Low voltage data points (≤{low_voltage_threshold} V): {n_low_voltage}")
                
                if n_low_voltage > 3:
                    print(f"  Generating low-voltage zoom plot...")
                    
                    v_low = voltages[low_voltage_mask]
                    p_low = powers[low_voltage_mask]
                    fit_low = poly(v_low)  # Use same linear fit from full data
                    
                    # Calculate R² for low voltage range
                    ss_res_low = np.sum((p_low - fit_low) ** 2)
                    ss_tot_low = np.sum((p_low - np.mean(p_low)) ** 2)
                    r_squared_low = 1 - (ss_res_low / ss_tot_low)
                    
                    print(f"  R² (low voltage) = {r_squared_low:.6f}")
                    
                    # Use same dimensions as combined plots
                    axes_width = 102.935 / 96  # 1.430 inches
                    axes_height = 72.247 / 96  # 1.003 inches
                    
                    # Tight margins for 8pt font
                    left_margin = 0.35  # inches for y-axis label + ticks
                    bottom_margin = 0.25  # inches for x-axis label + ticks
                    right_margin = 0.05
                    top_margin = 0.15  # for title
                    
                    fig_width = left_margin + axes_width + right_margin
                    fig_height = bottom_margin + axes_height + top_margin
                    
                    fig2 = plt.figure(figsize=(fig_width, fig_height))
                    
                    # Position axes exactly
                    ax2 = fig2.add_axes([left_margin / fig_width, 
                                         bottom_margin / fig_height,
                                         axes_width / fig_width, 
                                         axes_height / fig_height])
                    
                    # Use black for Obis 473, otherwise use laser_color
                    plot_color = 'black' if ('obis' in laser_name.lower() and '473' in laser_name.lower()) else laser_color
                    
                    # Uniform solid markers
                    ax2.plot(v_low, p_low, 'o', markersize=2, label='Measured', 
                            markerfacecolor=plot_color, markeredgecolor=plot_color, zorder=3)
                    
                    # Connect measured points with dashed line (same color, lighter)
                    trend_color = lighten_color(plot_color, 0.3)
                    ax2.plot(v_low, p_low, '--', linewidth=0.6, label='Measured trend', 
                            color=trend_color, zorder=2)
                    
                    # Plot linear fit (same color)
                    ax2.plot(v_low, fit_low, '-', linewidth=0.8, 
                            label=f'Linear fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR² = {r_squared_low:.6f}', 
                            color=plot_color, zorder=1)
                    
                    ax2.set_xlabel('Voltage (V)')
                    ax2.set_ylabel('Power (mW)')
                    ax2.set_title(f'Power vs Voltage (Low Voltage): {laser_name}')
                    ax2.legend(loc='upper left')
                    ax2.grid(False)
                    # Minimal axis design
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    # Add gap/break at origin by offsetting spines
                    ax2.spines['bottom'].set_position(('outward', 5))
                    ax2.spines['left'].set_position(('outward', 5))
                    # Set y-ticks to min and max only
                    y_min, y_max = ax2.get_ylim()
                    ax2.set_yticks([y_min, y_max])
                    ax2.set_yticklabels([f'{y_min:.2f}', f'{y_max:.2f}'])
                    
                    output_path2 = os.path.join(dir_path, f'power_vs_voltage_{safe_laser_name}_lowvoltage.svg')
                    save_figure_safely(fig2, output_path2)
                else:
                    print(f"  Skipping low-voltage plot: insufficient data points (≤{low_voltage_threshold} V)")
        
        # Create combined plots for all stable lasers (Obis 473, Obis 594, Oxxius 450)
        if len(combined_lasers) >= 2:
            print("\n\nCreating combined plots for stable lasers (Obis 594, Oxxius 450)...")
            
            # COMBINED FULL RANGE PLOT - Stable Lasers
            fig_combined, ax_combined = plt.subplots(1, 1, figsize=(2.872, 2.306))
            
            for laser in combined_lasers:
                laser_name = laser['name']
                if laser_name not in all_laser_data:
                    continue
                    
                data = all_laser_data[laser_name]
                voltages = data['voltages']
                powers = data['powers']
                fit_powers = data['fit_powers']
                coeffs = data['coeffs']
                r_squared = data['r_squared']
                laser_color = data['color']
                
                # Plot measured points with smaller markers (NO LABEL for legend)
                ax_combined.plot(voltages, powers, 'o', markersize=2, 
                               color=laser_color, markeredgewidth=0)
                
                # Plot linear fit with thinner lines (ONLY fit lines in legend)
                ax_combined.plot(voltages, fit_powers, '-', linewidth=0.8, 
                               label=f'{laser_name}: y={coeffs[0]:.3f}x+{coeffs[1]:.3f}, R²={r_squared:.4f}',
                               color=laser_color)
            
            ax_combined.set_xlabel('Voltage (V)')
            ax_combined.set_ylabel('Power (mW)')
            ax_combined.set_title('Power vs Voltage: Stable Lasers')
            ax_combined.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
            ax_combined.grid(False)
            # Minimal axis design
            ax_combined.spines['top'].set_visible(False)
            ax_combined.spines['right'].set_visible(False)
            # Add gap/break at origin by offsetting spines
            ax_combined.spines['bottom'].set_position(('outward', 5))
            ax_combined.spines['left'].set_position(('outward', 5))
            
            plt.tight_layout()
            
            dir_path = os.path.dirname(filename)
            output_combined = os.path.join(dir_path, 'power_vs_voltage_stable_combined.svg')
            save_figure_safely(fig_combined, output_combined)
            
            # COMBINED LOW VOLTAGE PLOT
            print("  Creating combined low-voltage plot...")
            fig_combined_low = plt.figure(figsize=(3.5, 2.5))
            
            # Create axes with exact size in inches
            axes_width = 0.9157  # 23.259mm
            axes_height = 0.6434  # 16.344mm
            
            # Calculate position [left, bottom, width, height] in figure coordinates
            left_margin = 0.5 / 3.5  # ~0.5" left margin for y-axis label
            bottom_margin = 0.4 / 2.5  # ~0.4" bottom margin for x-axis label
            
            ax_combined_low = fig_combined_low.add_axes([left_margin, bottom_margin,
                                                         axes_width/3.5, axes_height/2.5])
            
            low_voltage_threshold = 0.05
            has_low_voltage_data = False
            
            for laser in combined_lasers:
                laser_name = laser['name']
                if laser_name not in all_laser_data:
                    continue
                    
                data = all_laser_data[laser_name]
                voltages = data['voltages']
                powers = data['powers']
                poly = data['poly']
                coeffs = data['coeffs']
                laser_color = data['color']
                
                # Filter low voltage data
                low_voltage_mask = voltages <= low_voltage_threshold
                n_low_voltage = np.sum(low_voltage_mask)
                
                if n_low_voltage > 3:
                    has_low_voltage_data = True
                    
                    v_low = voltages[low_voltage_mask]
                    p_low = powers[low_voltage_mask]
                    fit_low = poly(v_low)
                    
                    # Calculate R² for low voltage range
                    ss_res_low = np.sum((p_low - fit_low) ** 2)
                    ss_tot_low = np.sum((p_low - np.mean(p_low)) ** 2)
                    r_squared_low = 1 - (ss_res_low / ss_tot_low)
                    
                    # Plot measured points with smaller markers (NO LABEL)
                    ax_combined_low.plot(v_low, p_low, 'o', markersize=2, 
                                        color=laser_color, zorder=3, markeredgewidth=0)
                    
                    # Connect measured points with dashed line (thinner, lighter, NO LABEL)
                    trend_color = lighten_color(laser_color, 0.3)
                    ax_combined_low.plot(v_low, p_low, '--', linewidth=0.6, 
                                        color=trend_color, zorder=2)
                    
                    # Plot linear fit with thinner line (ONLY fit lines in legend)
                    ax_combined_low.plot(v_low, fit_low, '-', linewidth=0.8, 
                                        label=f'{laser_name}: y={coeffs[0]:.3f}x+{coeffs[1]:.3f}, R²={r_squared_low:.4f}',
                                        color=laser_color, zorder=1)
            
            if has_low_voltage_data:
                ax_combined_low.set_xlabel('Voltage (V)')
                ax_combined_low.set_ylabel('Power (mW)')
                ax_combined_low.set_title('Power vs Voltage (Low Voltage): Stable Lasers')
                ax_combined_low.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
                ax_combined_low.grid(False)
                # Minimal axis design
                ax_combined_low.spines['top'].set_visible(False)
                ax_combined_low.spines['right'].set_visible(False)
                # Add gap/break at origin by offsetting spines
                ax_combined_low.spines['bottom'].set_position(('outward', 5))
                ax_combined_low.spines['left'].set_position(('outward', 5))
                # Set y-ticks to min and max only
                y_min, y_max = ax_combined_low.get_ylim()
                ax_combined_low.set_yticks([y_min, y_max])
                ax_combined_low.set_yticklabels([f'{y_min:.2f}', f'{y_max:.2f}'])
                
                output_combined_low = os.path.join(dir_path, 'power_vs_voltage_stable_combined_lowvoltage.svg')
                save_figure_safely(fig_combined_low, output_combined_low)
            else:
                plt.close(fig_combined_low)
                print("  No sufficient low-voltage data for combined plot")
        
        # Create separate plot for unstable laser (Chengchun) if present
        unstable_lasers = [laser for laser in laser_info if 'chengchun' in laser['name'].lower()]
        
        if unstable_lasers:
            print("\n\nCreating plot for unstable laser (Chengchun)...")
            
            for laser in unstable_lasers:
                laser_name = laser['name']
                if laser_name not in all_laser_data:
                    continue
                
                data = all_laser_data[laser_name]
                voltages = data['voltages']
                powers = data['powers']
                fit_powers = data['fit_powers']
                coeffs = data['coeffs']
                r_squared = data['r_squared']
                laser_color = data['color']
                
                # FULL RANGE PLOT for unstable laser
                fig_unstable, ax_unstable = plt.subplots(1, 1, figsize=(2.872, 2.306))
                
                # Plot measured points with smaller markers (NO LABEL)
                ax_unstable.plot(voltages, powers, 'o', markersize=2, 
                               color=laser_color, markeredgewidth=0)
                
                # Plot linear fit with thinner line (ONLY fit line in legend)
                ax_unstable.plot(voltages, fit_powers, '-', linewidth=0.8, 
                               label=f'Linear fit: y={coeffs[0]:.3f}x+{coeffs[1]:.3f}\nR²={r_squared:.4f}',
                               color=laser_color)
                
                ax_unstable.set_xlabel('Voltage (V)')
                ax_unstable.set_ylabel('Power (mW)')
                ax_unstable.set_title(f'Power vs Voltage: {laser_name}')
                ax_unstable.legend(loc='upper left', fontsize=4.5, framealpha=0.95)
                ax_unstable.grid(False)
                # Minimal axis design
                ax_unstable.spines['top'].set_visible(False)
                ax_unstable.spines['right'].set_visible(False)
                # Add gap/break at origin
                ax_unstable.spines['bottom'].set_position(('outward', 5))
                ax_unstable.spines['left'].set_position(('outward', 5))
                
                plt.tight_layout()
                
                safe_laser_name = laser_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
                output_unstable = os.path.join(dir_path, f'power_vs_voltage_{safe_laser_name}_combined.svg')
                save_figure_safely(fig_unstable, output_unstable)
        
    except Exception as e:
        print(f"Error analyzing power vs voltage: {e}")
        import traceback
        traceback.print_exc()


# Main execution
if __name__ == "__main__":
    import glob
    
    # Set the working directory
    data_dir = r'C:\Users\ainia\Documents\University\PhD\Writing\Zapit_2025'
    
    # Change to the data directory
    if os.path.exists(data_dir):
        os.chdir(data_dir)
        print(f"Working directory: {data_dir}")
    else:
        print(f"Directory not found: {data_dir}")
        print("Please update the path or ensure the directory exists.")
        exit(1)
        
    # Search for files in the main directory only
    print(f"\nSearching for laser data files in main directory...")
    print(f"Search directory: {data_dir}")
    
    # Find all relevant files directly in the main directory
    all_ms_files = glob.glob(os.path.join(data_dir, '*ms.txt'))
    all_hr_files = glob.glob(os.path.join(data_dir, '*hr.txt'))
    
    power_voltage_files = glob.glob(os.path.join(data_dir, '*power*.xlsx'))
    
    print(f"\nFiles found:")
    print(f"  - Power stability (ms): {len(all_ms_files)} files")
    for f in all_ms_files:
        print(f"      {os.path.basename(f)}")
    print(f"  - Power stability (hr): {len(all_hr_files)} files")
    for f in all_hr_files:
        print(f"      {os.path.basename(f)}")
    print(f"  - Power vs Voltage: {len(power_voltage_files)} files")
    for f in power_voltage_files:
        print(f"      {os.path.basename(f)}")
    
    # Process power stability files (ms)
    if all_ms_files:
        for file in all_ms_files:
            print(f"\nProcessing: {os.path.basename(file)}")
            analyze_power_stability(file)
        
        # Create overlay plots for ms files
        create_stability_overlay_plots(all_ms_files, file_type='ms', exclude_lasers=['chengchun'])
        
        create_stability_overlay_plots(all_ms_files, file_type='ms', exclude_lasers=None)
    
    # Process power stability files (hr)
    if all_hr_files:
        for file in all_hr_files:
            analyze_power_stability(file)
        
        # Create overlay plots for hr files
        create_stability_overlay_plots(all_hr_files, file_type='hr', exclude_lasers=['chengchun'])
        create_stability_overlay_plots(all_hr_files, file_type='hr', exclude_lasers=None)
    
    # Process power vs voltage files
    if power_voltage_files:
        for file in power_voltage_files:
            analyze_power_vs_voltage(file)

    print(f"\nAll figures have been saved to: {data_dir}")
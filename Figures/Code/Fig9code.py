import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from nptdms import TdmsFile
import os
import glob

# Set up plotting style with Calibri font and editable SVG text
plt.rcParams['font.size'] = 8
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['svg.fonttype'] = 'none'

LASER_COLORS = {
    'obis473': '#1E3A8A',      # Darkest blue
    'obis_473': '#1E3A8A',
    'obis594': '#2563EB',      # Medium blue
    'obis_594': '#2563EB',
    'oxxius450': '#3B82F6',    # Lighter blue
    'oxxius_450': '#3B82F6',
    'oxxius': '#3B82F6',       # Default Oxxius to 450 color
    'chengchun': '#E74C3C',    # Red for unstable
}

def get_laser_color(laser_name):
    laser_lower = laser_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    
    # Check for specific matches
    for key, color in LASER_COLORS.items():
        if key.replace('_', '') in laser_lower:
            return color
    
    # Default to medium blue for unknown stable lasers
    return '#2563EB'

def load_tdms(filename):
    tdms_file = TdmsFile.read(filename)
    
    photodiode_segments = []
    laser_segments = []
    
    for group in tdms_file.groups():
        for channel in group.channels():
            if channel.name == 'Voltage_0':
                photodiode_segments.append(channel.data)
            elif channel.name == 'Voltage_1':
                laser_segments.append(channel.data)
    
    photodiode = np.concatenate(photodiode_segments)
    laser = np.concatenate(laser_segments)
    time_ms = np.arange(len(photodiode)) * 0.01
    
    print(f"\nTotal samples: {len(photodiode):,}")
    print(f"Duration: {time_ms[-1]/1000:.1f} seconds")
    print(f"Photodiode range: [{np.min(photodiode):.3f}, {np.max(photodiode):.3f}] V")
    print(f"Laser range: [{np.min(laser):.3f}, {np.max(laser):.3f}] V")
    
    return time_ms, photodiode, laser

def find_laser_pulses(laser, time_ms):
    laser_min = np.min(laser)
    laser_max = np.max(laser)
    
    print(f"Laser signal range: [{laser_min:.3f}, {laser_max:.3f}] V")
    
    # Calculate baseline and active levels
    sorted_laser = np.sort(laser)
    baseline = np.median(sorted_laser[:int(len(sorted_laser) * 0.4)])
    active = np.median(sorted_laser[-int(len(sorted_laser) * 0.4):])
    
    threshold = (baseline + active) / 2
    print(f"Baseline: {baseline:.3f} V, Active: {active:.3f} V, Threshold: {threshold:.3f} V")
    
    # Find rising edges
    is_on = laser > threshold
    transitions = np.diff(is_on.astype(int))
    pulse_starts = np.where(transitions == 1)[0] + 1
    
    print(f"Found {len(pulse_starts)} laser pulses")
    
    return pulse_starts, threshold

def find_epochs(laser, time_ms, pulse_starts):
    if len(pulse_starts) == 0:
        return []
    
    gaps = np.diff(pulse_starts) * 0.01
    gap_threshold_ms = 100
    large_gaps = gaps > gap_threshold_ms
    trial_boundaries = np.where(large_gaps)[0] + 1
    
    print(f"Found {len(trial_boundaries)} trial boundaries")
    
    epochs = []
    epoch_start_idx = 0
    
    for boundary_idx in trial_boundaries:
        epoch_pulses = pulse_starts[epoch_start_idx:boundary_idx].tolist()
        
        if len(epoch_pulses) > 0:
            epochs.append({
                'start_idx': epoch_pulses[0],
                'pulse_indices': epoch_pulses,
                'start_time_ms': time_ms[epoch_pulses[0]],
                'n_pulses': len(epoch_pulses)
            })
        
        epoch_start_idx = boundary_idx
    
    epoch_pulses = pulse_starts[epoch_start_idx:].tolist()
    if len(epoch_pulses) > 0:
        epochs.append({
            'start_idx': epoch_pulses[0],
            'pulse_indices': epoch_pulses,
            'start_time_ms': time_ms[epoch_pulses[0]],
            'n_pulses': len(epoch_pulses)
        })
    
    print(f"Grouped {len(pulse_starts)} pulses into {len(epochs)} trials")
    
    # Show trial info
    for i, epoch in enumerate(epochs):
        print(f"  Trial {i+1}: {epoch['n_pulses']} pulses starting at {epoch['start_time_ms']/1000:.2f}s")
    
    return epochs

def normalize_individually(signal):
    sig_min = np.min(signal)
    sig_max = np.max(signal)
    sig_range = sig_max - sig_min
    
    if sig_range < 1e-10:  # Avoid division by zero
        return signal - sig_min
    
    return (signal - sig_min) / sig_range

def extract_trials(time_ms, photodiode, laser, epochs, pre_ms=200, post_ms=1000):
    pre_samples = int(pre_ms / 0.01)
    post_samples = int(post_ms / 0.01)
    
    trials = []
    
    for i, epoch in enumerate(epochs):
        onset_idx = epoch['start_idx']
        
        start_idx = max(0, onset_idx - pre_samples)
        end_idx = min(len(photodiode), onset_idx + post_samples)
        
        actual_pre = onset_idx - start_idx
        actual_post = end_idx - onset_idx
        
        if actual_pre < pre_samples * 0.8 or actual_post < post_samples * 0.8:
            print(f"Skipping trial {i+1}: insufficient data")
            continue
        
        trial_photo = photodiode[start_idx:end_idx]
        trial_laser = laser[start_idx:end_idx]
        
        # Normalize each independently to same height
        photo_norm = normalize_individually(trial_photo)
        laser_norm = normalize_individually(trial_laser)
        
        trial_time = np.arange(len(trial_photo)) * 0.01 - (onset_idx - start_idx) * 0.01
        
        trials.append({
            'trial_num': i + 1,
            'time_ms': trial_time,
            'photodiode_raw': trial_photo,
            'laser_raw': trial_laser,
            'photodiode_norm': photo_norm,
            'laser_norm': laser_norm
        })
    
    print(f"Extracted {len(trials)} complete trials")
    return trials

def plot_trials_stacked(trials, laser_name, power, trials_to_show=[1, 10, 50], save_path=None):
    """
    Plot stacked individual trials with overlay inset
    Individual trials: 47.782mm x 62.367mm (1.881" x 2.455")
    Overlay inset: 22.433mm x 16.868mm (0.883" x 0.664")
    Font: Calibri 8pt, editable SVG text
    Colors: Match laser characterization color scheme
    FIXED: Removed alpha transparency from overlay to prevent gradient artifacts in SVG
    """
    
    # Get laser color
    laser_color = get_laser_color(laser_name)
    print(f"  Using color {laser_color} for {laser_name}")
    
    # Get trials to plot
    plot_trials = []
    for trial_num in trials_to_show:
        trial = next((t for t in trials if t['trial_num'] == trial_num), None)
        if trial:
            plot_trials.append(trial)
    
    if len(plot_trials) == 0:
        print("ERROR: No trials to plot!")
        return
    
    print(f"  Plotting {len(plot_trials)} trials stacked")
    
    fig_main = plt.figure(figsize=(2.455, 1.881))
    ax_main = fig_main.add_subplot(111)
    
    trial_spacing = 3.0  # Space between different trials
    trace_spacing = 1.2  # Space between photodiode and laser within a trial

    for idx, trial in enumerate(plot_trials):
        trial_offset = (len(plot_trials) - 1 - idx) * trial_spacing
        
        offset_photo = trial_offset + trace_spacing
        ax_main.plot(trial['time_ms'], 
                     trial['photodiode_norm'] + offset_photo, 
                     'black', linewidth=0.5, alpha=0.9)
        
        offset_laser = trial_offset
        ax_main.plot(trial['time_ms'], 
                     trial['laser_norm'] + offset_laser, 
                     color=laser_color, linewidth=0.5, alpha=0.7)
        
        # Add trial label on the left
        ax_main.text(-220, trial_offset + trace_spacing/2, f'Rep {trial["trial_num"]}', 
                     fontsize=8, va='center', fontweight='bold')
    
    # Add trace labels on the far left (only once)
    top_trial_offset = (len(plot_trials) - 1) * trial_spacing
    ax_main.text(-280, top_trial_offset + trace_spacing, 'Photodiode', 
                 fontsize=8, va='center', fontweight='bold', rotation=90)
    ax_main.text(-280, top_trial_offset, 'Laser', 
                 fontsize=8, va='center', color=laser_color, rotation=90)
    
    # Add reference lines
    ax_main.axvline(0, color='black', linestyle='--', alpha=1, linewidth=0.5)
    ax_main.axvline(800, color='black', linestyle='--', alpha=1, linewidth=0.5)
    ax_main.axvline(1000, color='black', linestyle='--', alpha=1, linewidth=0.5)
    ax_main.text(900, (len(plot_trials) - 1) * trial_spacing + trace_spacing + 1.3, 
                 'Rampdown', ha='center', fontsize=8, color='black')
    
    # Configure main plot
    ax_main.set_xlim(-200, 1000)
    ax_main.set_xticks([0, 200, 400, 600, 800, 1000])
    ax_main.set_ylim(-0.5, len(plot_trials) * trial_spacing + 0.5)
    ax_main.set_xlabel('Time from onset of analog signal (ms)', fontsize=8)
    ax_main.set_ylabel('Amplitude (normalized)', fontsize=8)
    ax_main.set_yticks([])
    ax_main.tick_params(labelsize=8)
    ax_main.grid(False)
    
    # Minimal axis design
    ax_main.spines['top'].set_visible(False)
    ax_main.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    if save_path:
        # Save main figure
        main_path = save_path.replace('.svg', '_individual.svg')
        fig_main.savefig(main_path, format='svg', bbox_inches='tight')
        print(f"Individual trials figure saved to: {main_path}")
        plt.close(fig_main)
    
    n_overlay = min(50, len(trials))
    print(f"  Creating overlay plot with {n_overlay} trials")
    
    # Convert mm to inches: 22.433mm = 0.883", 16.868mm = 0.664"
    fig_inset = plt.figure(figsize=(0.883, 0.664))
    ax_inset = fig_inset.add_subplot(111)
    
    # Define stacking offset for inset
    inset_spacing = 1.5
    
    from matplotlib.colors import to_rgba, to_hex
    
    # Create very light versions of colors for overlay
    def lighten_color(color, amount=0.85):
        """Lighten a color by mixing with white"""
        rgba = to_rgba(color)
        # Mix with white (1, 1, 1) by amount
        light_rgba = tuple(rgba[i] * (1 - amount) + amount for i in range(3)) + (1.0,)
        return light_rgba
    
    # Get lighter colors for overlay
    photo_light = lighten_color('black', 0.85)
    laser_light = lighten_color(laser_color, 0.85)
    
    # Plot all trials overlaid in the inset (zoomed to -1 to 3 ms)
    # FIXED: Using very thin lines with lighter colors instead of alpha transparency
    for i in range(n_overlay):
        trial = trials[i]
        # Mask to show only -1 to 3 ms
        mask = (trial['time_ms'] >= -1) & (trial['time_ms'] <= 3)
        time_zoom = trial['time_ms'][mask]
        photo_zoom = trial['photodiode_norm'][mask]
        laser_zoom = trial['laser_norm'][mask]
        
        # Plot photodiode (light gray, top) - NO ALPHA
        ax_inset.plot(time_zoom, photo_zoom + inset_spacing, 
                     color=photo_light, linewidth=0.2)
        
        # Plot laser (light laser color, bottom) - NO ALPHA
        ax_inset.plot(time_zoom, laser_zoom, 
                     color=laser_light, linewidth=0.2)
    
    # Add vertical line at onset (0 ms)
    ax_inset.axvline(0, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
    
    # Configure inset
    ax_inset.set_xlim(-1, 3)
    ax_inset.set_ylim(-0.2, inset_spacing + 1.2)
    ax_inset.set_xlabel('Time from onset of analog\nsignal (ms)', fontsize=8)
    ax_inset.set_title(f'Overlay of {n_overlay} trials', fontsize=8, fontweight='bold')
    ax_inset.tick_params(labelsize=8)
    ax_inset.set_yticks([])
    ax_inset.grid(False)
    
    # Minimal axis design
    ax_inset.spines['top'].set_visible(False)
    ax_inset.spines['right'].set_visible(False)
    
    # Add trace labels
    ax_inset.text(-1.15, inset_spacing + 0.5, 'Photodiode', 
                 fontsize=8, va='center', fontweight='bold')
    ax_inset.text(-1.15, 0.5, 'Laser', 
                 fontsize=8, va='center', color=laser_color)
    
    # Add legend to inset - use solid colors for legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='black', linewidth=1, label='Photodiode response'),
        Line2D([0], [0], color=laser_color, linewidth=1, label='Laser analog input')
    ]
    ax_inset.legend(handles=legend_elements, loc='best', fontsize=8, framealpha=0.9)
    
    plt.tight_layout()
    
    if save_path:
        # Save overlay figure
        overlay_path = save_path.replace('.svg', '_overlay.svg')
        fig_inset.savefig(overlay_path, format='svg', bbox_inches='tight')
        print(f"Overlay figure saved to: {overlay_path}")
        plt.close(fig_inset)

def extract_laser_and_power(filename):
    """Extract laser name and power from filename"""
    basename = os.path.basename(filename)
    name_parts = basename.replace('.tdms', '').replace('_filtered', '').split('_')
    
    laser_name = name_parts[0] if len(name_parts) > 0 else 'unknown'
    
    if len(name_parts) >= 2:
        try:
            power_str = name_parts[1]
            if len(name_parts) >= 3 and name_parts[2].replace('.', '').isdigit():
                power_str = f"{name_parts[1]}.{name_parts[2]}"
            power = float(power_str.replace('_', '.'))
        except:
            power = 0.0
    else:
        power = 0.0
    
    return laser_name, power

# MAIN SCRIPT
if __name__ == "__main__":
    data_dir = r'C:\Users\ainia\Documents\University\PhD\Writing\Zapit_2025'
    
    # Find only the two specific files
    target_files = [
        'obis594_50_filtered.tdms',
        'oxxius_30_filtered.tdms'
    ]
    
    tdms_files = []
    for target in target_files:
        full_path = os.path.join(data_dir, target)
        if os.path.exists(full_path):
            tdms_files.append(full_path)
        else:
            print(f"File not found: {target}")
    
    if len(tdms_files) == 0:
        print(f"None of the target files found in: {data_dir}")
    else:
        print(f"\nFound {len(tdms_files)} files to process:")
        for i, f in enumerate(tdms_files, 1):
            print(f"  {i}. {os.path.basename(f)}")
        
        # Process each file
        for file_num, tdms_file in enumerate(tdms_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing file {file_num}/{len(tdms_files)}: {os.path.basename(tdms_file)}")
            print('='*60)
            
            try:
                # Extract laser name and power
                laser_name, power = extract_laser_and_power(tdms_file)
                print(f"Detected: {laser_name} at {power} mW")
                
                # Load data
                time_ms, photodiode, laser = load_tdms(tdms_file)
                
                # Find pulses
                pulse_starts, threshold = find_laser_pulses(laser, time_ms)
                
                # Group into trials
                epochs = find_epochs(laser, time_ms, pulse_starts)
                
                if len(epochs) == 0:
                    print(f"No trials found")
                    continue
                
                # Extract trials
                trials = extract_trials(time_ms, photodiode, laser, epochs,
                                      pre_ms=200, post_ms=1000)
                
                if len(trials) == 0:
                    continue
                
                # Plot stacked trials
                output_dir = os.path.dirname(tdms_file)
                base_name = os.path.splitext(os.path.basename(tdms_file))[0]
                stacked_plot_path = os.path.join(output_dir, f'{base_name}_stacked.svg')
                
                plot_trials_stacked(trials, laser_name, power, 
                                  trials_to_show=[1, 10, 50], 
                                  save_path=stacked_plot_path)
                
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
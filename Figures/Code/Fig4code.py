import scipy.io
import numpy as np
import matplotlib.pyplot as plt
import os

def load_stimlocation_across_files(base_path, stimlocation_idx, num_files=5):
    all_waveforms = []
    
    for file_num in range(1, num_files + 1):
        filename = os.path.join(base_path, f"zapit_waveforms_site{file_num}.mat")
        
        if not os.path.exists(filename):
            continue
            
        try:
            mat_data = scipy.io.loadmat(filename)
            waveforms_array = mat_data['waveforms'].flatten()
            
            if stimlocation_idx >= len(waveforms_array):
                continue
                
            wf = waveforms_array[stimlocation_idx]
            x = wf[:, 0]
            y = wf[:, 1]
            all_waveforms.append((x, y))
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    if all_waveforms:
        x_all = np.concatenate([wf[0] for wf in all_waveforms])
        y_all = np.concatenate([wf[1] for wf in all_waveforms])
        return x_all, y_all, all_waveforms
    return None, None, []


def get_global_ranges(base_path, num_files=5, num_stimlocations=8):
    global_x_min, global_x_max = float('inf'), float('-inf')
    global_y_min, global_y_max = float('inf'), float('-inf')
    
    for stim_idx in range(num_stimlocations):
        x_data, y_data, _ = load_stimlocation_across_files(base_path, stim_idx, num_files)
        if x_data is not None:
            global_x_min = min(global_x_min, x_data.min())
            global_x_max = max(global_x_max, x_data.max())
            global_y_min = min(global_y_min, y_data.min())
            global_y_max = max(global_y_max, y_data.max())
    
    return (global_x_min, global_x_max), (global_y_min, global_y_max)


def detect_sites_in_order_1d(x, n_expected):
    x_range = np.max(x) - np.min(x)
    
    if x_range < 0.001:
        return [np.mean(x)], 0.01
    
    tolerance = x_range / (n_expected * 8)
    
    site_positions_ordered = []
    visited_positions = []
    
    i = 0
    while i < len(x) and len(site_positions_ordered) < n_expected:
        x_current = x[i]
        
        is_new = True
        for visited_x in visited_positions:
            if abs(x_current - visited_x) < tolerance:
                is_new = False
                break
        
        if is_new:
            stable_count = 0
            for j in range(i, min(i + 500, len(x))):
                if abs(x[j] - x_current) < tolerance:
                    stable_count += 1
            
            if stable_count > 80:
                visited_positions.append(x_current)
                matching = x[np.abs(x - x_current) < tolerance]
                mean_pos = np.mean(matching)
                site_positions_ordered.append(mean_pos)
                i += stable_count
                continue
        
        i += 1
    
    return site_positions_ordered, tolerance


def detect_sites_in_order_2d(x, y, n_expected):
    site_positions_ordered = []
    tolerance = 0.015
    
    i = 0
    while i < len(x) - 50 and len(site_positions_ordered) < n_expected:
        x_segment = x[i:i+50]
        y_segment = y[i:i+50]
        
        if np.std(x_segment) < 0.005 and np.std(y_segment) < 0.005:
            mean_x = np.mean(x_segment)
            mean_y = np.mean(y_segment)
            
            is_new = True
            for sx, sy in site_positions_ordered:
                if abs(mean_x - sx) < tolerance and abs(mean_y - sy) < tolerance:
                    is_new = False
                    break
            
            if is_new:
                site_positions_ordered.append((mean_x, mean_y))
            
            i += 50
        else:
            i += 1
    
    return site_positions_ordered, tolerance


def mark_site_visits_1d(x, site_positions_ordered, tolerance):
    visits = []
    
    for site_idx, x_site in enumerate(site_positions_ordered):
        at_site = np.abs(x - x_site) < tolerance
        
        changes = np.diff(np.concatenate([[False], at_site, [False]]).astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        for start, end in zip(starts, ends):
            if end - start > 40:
                visits.append((start, end, site_idx))
    
    return sorted(visits, key=lambda v: v[0])


def mark_site_visits_2d(x, y, site_positions_ordered, tolerance):
    """Find all visits to each site using both X and Y"""
    visits = []
    
    for site_idx, (x_site, y_site) in enumerate(site_positions_ordered):
        at_site = (np.abs(x - x_site) < tolerance) & (np.abs(y - y_site) < tolerance)
        
        changes = np.diff(np.concatenate([[False], at_site, [False]]).astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        for start, end in zip(starts, ends):
            if end - start > 40:
                visits.append((start, end, site_idx))
    
    return sorted(visits, key=lambda v: v[0])


def plot_all_stimlocations(base_path, num_files=5, save_path=None):
    
    if not os.path.exists(base_path):
        print(f"Error: Directory not found: {base_path}")
        return
    
    existing_files = [f for f in os.listdir(base_path) if f.startswith('zapit_waveforms_site') and f.endswith('.mat')]
    print(f"Found {len(existing_files)} waveform files in {base_path}")
    print()
    
    # Get global ranges for consistent scaling
    (global_x_min, global_x_max), (global_y_min, global_y_max) = get_global_ranges(base_path, num_files, 8)
    global_x_range = global_x_max - global_x_min
    global_y_range = global_y_max - global_y_min
    
    print(f"Global X range: [{global_x_min:.4f}, {global_x_max:.4f}] (span: {global_x_range:.4f})")
    print(f"Global Y range: [{global_y_min:.4f}, {global_y_max:.4f}] (span: {global_y_range:.4f})")
    print()
    
    fig, axes = plt.subplots(8, 1, figsize=(20, 26), sharex=True)
    
    # ML and AP coordinates from YAML
    stimlocation_info = [
        ('stimLocation01', 2, [2.3, -2.3], [-2.1, -2.1], False),
        ('stimLocation02', 2, [-2.7, 2.8], [-3.9, -3.95], False),
        ('stimLocation03', 2, [-1.99, 1.99], [2.99, 2.99], False),
        ('stimLocation04', 2, [-1.99, 1.99], [2.5, 2.5], False),
        ('stimLocation05', 2, [-1.75, 1.75], [2.45, 2.45], False),
        ('stimLocation06', 2, [-1.75, 1.75], [2.99, 2.99], False),
        ('stimLocation07', 1, [-3.7], [-1.2], False),
        ('stimLocation08', 5, [0, -0.5, -0.5, 0.5, 0.5], [-1, -1.5, -2.5, -1.5, -2.5], True),
    ]
    
    # Fixed offset between X and Y traces (in data units)
    trace_separation = global_x_range * 0.3
    
    for stim_idx in range(8):
        ax = axes[stim_idx]
        stim_name, n_sites, ml_coords, ap_coords, use_2d = stimlocation_info[stim_idx]
        
        x_data, y_data, all_waveforms = load_stimlocation_across_files(base_path, stim_idx, num_files)
        
        if x_data is None or len(x_data) == 0:
            ax.text(0.5, 0.5, f'No data for {stim_name}', transform=ax.transAxes,
                   ha='center', va='center', fontsize=12, color='red')
            ax.set_ylabel(stim_name, fontsize=11, fontweight='bold')
            continue
        
        time = np.arange(len(x_data))
        
        # Plot X trace (no modification - true amplitude)
        ax.plot(time, x_data, 'b-', linewidth=0.5, alpha=0.8)
        
        # Plot Y trace offset below X
        y_offset = global_x_min - global_y_max - trace_separation
        ax.plot(time, y_data + y_offset, 'r-', linewidth=0.5, alpha=0.8)
        
        # Set y-axis limits to be consistent across all panels (shared amplitude scale)
        y_axis_min = global_y_min + y_offset - 0.05
        y_axis_max = global_x_max + 0.15  # Extra space for site markers
        ax.set_ylim(y_axis_min, y_axis_max)
        
        # Axis labels
        ax.text(-800, np.mean(x_data), 'X', fontsize=10, fontweight='bold', 
               color='blue', va='center', ha='right')
        ax.text(-800, np.mean(y_data) + y_offset, 'Y', fontsize=10, fontweight='bold', 
               color='red', va='center', ha='right')
        
        # Mark repetition boundaries
        current_idx = 0
        for wf_num, (x_wf, _) in enumerate(all_waveforms):
            if wf_num > 0:
                ax.axvline(current_idx, color='black', linestyle=':', linewidth=1, alpha=0.4)
            current_idx += len(x_wf)
        
        # Detect sites
        if use_2d:
            site_positions, tolerance = detect_sites_in_order_2d(x_data, y_data, n_sites)
            visits = mark_site_visits_2d(x_data, y_data, site_positions, tolerance)
            print(f"{stim_name}: Detected {len(site_positions)} sites (2D)")
        else:
            site_positions, tolerance = detect_sites_in_order_1d(x_data, n_sites)
            visits = mark_site_visits_1d(x_data, site_positions, tolerance)
            print(f"{stim_name}: Detected {len(site_positions)} sites (1D) at X={[f'{x:.3f}' for x in site_positions]}")
        
        print(f"  Total visits: {len(visits)}, Expected: ~{n_sites * len(all_waveforms)}")
        
        # Mark sites
        colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C']
        
        # Legend
        legend_elements = []
        for site_num in range(n_sites):
            color = colors[site_num % len(colors)]
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                             markerfacecolor=color, markersize=10,
                                             label=f'Site {site_num+1}: ML={ml_coords[site_num]:.2f}, AP={ap_coords[site_num]:.2f}'))
        
        for start, end, site_idx_local in visits:
            mid = int((start + end) / 2)
            color = colors[site_idx_local % len(colors)]
            
            # Vertical line and label
            ax.plot([mid, mid], [x_data[mid], y_axis_max - 0.05], 
                   color=color, linewidth=1.5, alpha=0.7)
            ax.text(mid, y_axis_max - 0.02, str(site_idx_local + 1), 
                   ha='center', va='bottom', fontsize=9, 
                   color='white', fontweight='bold',
                   bbox=dict(boxstyle='circle,pad=0.2', facecolor=color, edgecolor='none'))
        
        ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.01, 0.5), 
                 fontsize=8, framealpha=0.95, edgecolor='gray')
        
        ax.set_ylabel(stim_name, fontsize=11, fontweight='bold')
        ax.set_yticks([])
        ax.grid(True, alpha=0.2, axis='x')
    
    axes[-1].set_xlabel('Time (samples)', fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=600, bbox_inches='tight')
        print(f"\nFigure saved to: {save_path}")
    
    plt.show()

def calculate_multisite_power_simple(power_range=(1, 10), max_sites=5, max_sites_heatmap=20):
    """
    Calculate theoretical total power requirements for multi-site stimulation
    """
    
    # Generate power values
    power_values = np.linspace(power_range[0], power_range[1], 50)
    
    # Calculate total power for each number of sites (for line plot)
    results = {}
    
    for n_sites in range(1, max_sites + 1):
        if n_sites <= 2:
            duty_cycle = 0.5
            scaling_factor = 2.0
        else:
            duty_cycle = 1.0 / n_sites
            scaling_factor = n_sites
        
        total_power = power_values * scaling_factor
        
        results[n_sites] = {
            'power_per_site': power_values,
            'total_power': total_power,
            'duty_cycle': duty_cycle,
            'scaling_factor': scaling_factor
        }
    
    # ========== HEATMAP ==========
    power_per_site_values = np.linspace(power_range[0], power_range[1], 100)
    n_sites_values = np.arange(1, max_sites_heatmap + 1)
    
    total_power_matrix = np.zeros((len(power_per_site_values), len(n_sites_values)))
    
    for i, power_per_site in enumerate(power_per_site_values):
        for j, n_sites in enumerate(n_sites_values):
            if n_sites <= 2:
                scaling_factor = 2.0
            else:
                scaling_factor = n_sites
            total_power_matrix[i, j] = power_per_site * scaling_factor
    
    # Mask values above 100 mW
    total_power_matrix_masked = np.ma.masked_where(total_power_matrix > 100, total_power_matrix)
    
    # Create custom colormap with white for masked values
    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color='white')
    
    # Create heatmap with optimized dimensions
    fig1, ax2 = plt.subplots(1, 1, figsize=(3.343, 2.347))
    
    # Temporarily set font to Arial for heatmap
    original_font = plt.rcParams['font.sans-serif'].copy()
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    
    # Plot with vmax=100
    im = ax2.imshow(total_power_matrix_masked, aspect='auto', origin='lower', 
                    cmap=cmap, interpolation='nearest', vmin=0, vmax=100)
    
    ax2.set_xlabel('Number of Sites', fontsize=8)
    ax2.set_ylabel('Target Power per Site (mW)', fontsize=8)
    
    # Set custom x-axis ticks: 1, 5, 10, 15, 20
    x_tick_positions = [0, 4, 9, 14, 19]
    x_tick_labels = [1, 5, 10, 15, 20]
    ax2.set_xticks(x_tick_positions)
    ax2.set_xticklabels(x_tick_labels, fontsize=8)
    
    # Set custom y-axis ticks: 1, 5, 10
    y_tick_powers = [1, 5, 10]
    y_tick_indices = [int((p - power_range[0]) / (power_range[1] - power_range[0]) * (len(power_per_site_values) - 1)) 
                     for p in y_tick_powers]
    ax2.set_yticks(y_tick_indices)
    ax2.set_yticklabels(y_tick_powers, fontsize=8)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label('Total Laser Power Required (mW)', fontsize=8)
    cbar.ax.tick_params(labelsize=8)
    
    # Add LABELED contour lines with manual label positioning
    contour_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    CS = ax2.contour(total_power_matrix_masked, levels=contour_levels, 
                     colors='white', alpha=1, linewidths=1.0)
    
    manual_positions = []
    x_pos = 10
    
    for level in contour_levels:
        power_per_site_needed = level / x_pos
        y_index = int((power_per_site_needed - power_range[0]) / (power_range[1] - power_range[0]) * (len(power_per_site_values) - 1))
        
        if 0 <= y_index < len(power_per_site_values):
            manual_positions.append((x_pos - 1, y_index))
    
    ax2.clabel(CS, inline=True, manual=manual_positions, fmt='%d mW', colors='white', fontsize=8)
    
    ax2.grid(False)
    
    plt.tight_layout()
    
    # Restore original font settings
    plt.rcParams['font.sans-serif'] = original_font
    
    print("\nMulti-site power scaling summary:")
    print("=" * 50)
    for n_sites in range(1, min(max_sites + 1, 11)):
        if n_sites <= 2:
            duty_cycle = 0.5
            scaling_factor = 2.0
        else:
            duty_cycle = 1.0 / n_sites
            scaling_factor = n_sites
        print(f"{n_sites:2d} site(s): {duty_cycle*100:5.1f}% duty cycle, "
              f"{scaling_factor:4.1f}× power scaling")
    
    if max_sites_heatmap > 10:
        print(f"... (up to {max_sites_heatmap} sites shown in heatmap)")
    return fig1, results

if __name__ == "__main__":
    base_path = r"C:\Users\ainia\Documents\University\PhD\Writing\Zapit_2025"
    save_path = r"C:\Users\ainia\Documents\University\PhD\Writing\Zapit_2025\galvo_waveforms_all_stimlocations.svg"
    
    plot_all_stimlocations(base_path, num_files=5, save_path=save_path)

    # Generate multi-site power calculations
    fig_heatmap, results = calculate_multisite_power_simple(power_range=(1, 10), max_sites=5, max_sites_heatmap=20)
    
    # Save heatmap
    output_path_heatmap = os.path.join(base_path, 'multisite_power_heatmap.svg')
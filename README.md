# overleaf-manuscript

Latex source and data for Zapit's [eLife manuscript](https://elifesciences.org/reviewed-preprints/111872). 


## Licence

- Manuscript text and figures (`*.tex`, `references.bib`, images under `Figures/`): [CC BY 4.0](LICENSE-CC-BY.txt)
- Figure data and code (`Figures/Code/`, `Figures/Supplementary_Figs/*/*code_data*`, `code_snippets/`): [MIT](LICENSE-MIT.txt)

See [LICENSE.md](LICENSE.md) for details. The Zapit software and CAD files are in separate [repositories](https://github.com/Zapit-Optostim) with their own licences.


## Data

Data and code needed to re-create the figures are in `Figures/Code/`, with one folder per figure (the supplementary Figure 2 data are under `Figures/Supplementary_Figs/`).
These match the "source data" and "source code" entries at the end of the figure legends.
Figures 1 to 5 and the other supplementary figures are schematics, screenshots and photographs, and have no source data.

| Figure | Data | Code |
|---|---|---|
| Fig 6: triggering and latency | `Figures/Code/fig_6_triggering/data/`: oscilloscope recordings (`.mat`) of hardware trigger and photodiode signals. `100kS_trigger` and `100kS_laser_input_output` were sampled at 100 kS/s. `5kS_delay` contains the recordings with a 1 s onset delay | `Figures/Code/fig_6_triggering/code/` |
| Fig 7: beam blanking and pointing | `Figures/Code/fig_7_galvo_position/raw_data/`: galvo waveforms for three sites (`zapit_waveforms_site*.mat`), photodiode feedback (`control_feedback_photodiode.bin`, described in `blanking_raw_data_readme.md`) and laser power vs command voltage (`PowervsVoltage_Obis473.xlsx`) | `Figures/Code/fig_7_galvo_position/code/` |
| Fig 7, supplement 1: laser comparisons | `Figures/Code/fig_7_supp_laser_comparisons/raw_data/`: laser power vs command voltage (`PowervsVoltage.xlsx`) | `Figures/Code/fig_7_supp_laser_comparisons/code/` |
| Fig 8: electrophysiology | `Figures/Code/fig_8_ephys/data/`: effect of photoinhibition across laser powers (`opto_cali_effect_alm_vs_v1.csv`, `opto_cali_ma.mat`) and firing-rate rebound (`rebound_vars.mat`). Reanalysed from Gauld et al. (2025) | `Figures/Code/fig_8_ephys/code/` |
| Fig 9A: whisker discrimination | `Figures/Code/fig_9_behaviour/data/`: trial tables and summary statistics for the photoinhibition mapping and power experiments | `Figures/Code/fig_9_behaviour/code/` |
| Fig 9B: visual change detection | `Figures/Code/Visual_Change_Detection_Behaviour_Zapit/OrganisedV1S1ConPlottingData.mat` | `Figures/Code/Visual_Change_Detection_Behaviour_Zapit/` (`.m` files) |
| Fig 2, supplement 1: beam resolution | `Figures/Supplementary_Figs/figS2_Optical_Design/Fig_2_code_data/`: measured and Zemax-simulated point spread functions | `Figures/Supplementary_Figs/figS2_Optical_Design/Fig_2_code_data/f150mm_Obis_Direct/plot_psf.py` |

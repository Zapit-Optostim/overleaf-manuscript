% This script loads in highly processed data to generate some ephys validation plots. 
% Access to the real data can be provided on request (the data-sets are
% very large in size).

clearvars

% point to fig_8_ephys/data directory

data_dir = uigetdir();%
cd(data_dir);
% Generate lateral photoinhibition curves for ALM and visual cortex

% load data
opto_cal = readtable('opto_cali_effect_alm_vs_v1.csv');

dist = 0:3; % distance bins

% Grab data for each area
alm_data = opto_cal(strcmp(opto_cal.area,"m2_1"),:); 
v1_data = opto_cal(strcmp(opto_cal.area,"v2mm"),:); 

DV_limit = -1000; % only include cells 0–1000 um deep

alm_data(alm_data.DV < DV_limit,:) = []; 
v1_data(v1_data.DV < DV_limit,:) = [];

alm_data(alm_data.power == 4,:) = []; % remove 4mW trials
v1_data(v1_data.power == 4,:) = [];

% Preallocate
mean_effect_alm = nan(1,numel(dist));
mean_effect_v1  = nan(1,numel(dist));
ci_effect_alm   = nan(1,numel(dist));
ci_effect_v1    = nan(1,numel(dist));

for i = 1:numel(dist)

    % Extract effects at this distance
    alm_vals = alm_data.effects(alm_data.AP_dist == dist(i));
    v1_vals  = v1_data.effects(v1_data.AP_dist == dist(i));

    % Mean effects
    mean_effect_alm(i) = nanmean(alm_vals);
    mean_effect_v1(i)  = nanmean(v1_vals);

    % Number of observations
    n_alm = sum(~isnan(alm_vals));
    n_v1  = sum(~isnan(v1_vals));

    % 95% confidence interval (t distribution)
    ci_effect_alm(i) = tinv(0.975,n_alm-1) * nanstd(alm_vals) / sqrt(n_alm);
    ci_effect_v1(i)  = tinv(0.975,n_v1-1)  * nanstd(v1_vals)  / sqrt(n_v1);

end

% Plot
figure

errorbar((1:numel(dist))+.025,mean_effect_alm,ci_effect_alm,...
    '-ok','Capsize',0,'MarkerFaceColor','k','LineWidth',2); 
hold on

errorbar((1:numel(dist))-0.025,mean_effect_v1,ci_effect_v1,...
    '-o','color','r','Capsize',0,'MarkerFaceColor','r','LineWidth',2); 

xlim([.5,4.5])
box off
axis square

xticks(1:4)
xticklabels({'0','1','2','3'})

xlabel('Lateral distance from laser site (mm)')
ylabel('Normalised FR')

ylim([0,1.2])

hold on
plot(xlim,[1,1],'--k')

text(3,.4,'Motor cortex','Color','k')
text(3,.3,'Visual cortex','Color','r')

%%

% % opto calibration
% % code written by Chaofei Bao, 2025.5.8
% 
% for i = 1:4
%     load(fullfile(data_root,sprintf("opto_cali_%d_fr_norm.mat",i)));
%     if i == 1
%         cali_struct = opto_cali_struct;
%     end
%     cali_struct(i,1) = opto_cali_struct(1);
% end
% 
% clusterinfo_sum1 = [cali_struct(1,1).this_clusterinfo;cali_struct(2,1).this_clusterinfo];
% cnd_psth_sum1 = cat(3,cali_struct(1).cnd_psth,cali_struct(2).cnd_psth);
% x_times = cali_struct(1,1).x_times;
% fr_cnd1_filter1 = (squeeze(mean(cnd_psth_sum1(8,x_times>0 & x_times<1,:),2, 'omitnan'))<1);
% select_cnd1 = [1,8,9,10,11,12,13];
% select_cnd2 = [14,21,22,23,24,25,26];
% select_cnd_plot_temp = 1:2:7;
% select_cnd_plot1 = [select_cnd_plot_temp,select_cnd_plot_temp+7];
% cnd_effects1 = squeeze(mean(cnd_psth_sum1(select_cnd_plot1,x_times>0.0 & x_times<1,fr_cnd1_filter1),2, 'omitnan'));
% distances = [0,1,2,3];
% AP_distance1 = [distances,distances];
% powers1 = repelem([1.5,4],1,4);
% cnd_effects_rsh1 = cnd_effects1;
% cnd_effects_mean1 = cnd_effects_rsh1;
% 
% 
% 
% clusterinfo_sum = [cali_struct(3,1).this_clusterinfo;cali_struct(4,1).this_clusterinfo];
% cnd_psth_sum = cat(3,cali_struct(3).cnd_psth,cali_struct(4).cnd_psth);
% 
% x_times = cali_struct(1,1).x_times;
% 
% fr_cnd1_filter = (squeeze(mean(cnd_psth_sum(9,x_times>0 & x_times<1,:),2, 'omitnan'))<1);
% 
% cnd_effects = squeeze(mean(cnd_psth_sum(:,x_times>0.0 & x_times<1,fr_cnd1_filter),2, 'omitnan'));
% distances = [0,1,2,3];
% cnd_effects_mean = cnd_effects(1:12,:);
% 
% AP_distance = [distances, distances, distances];
% powers = repelem([1,2,4],1,4);
% this_DV_inhib = clusterinfo_sum.real_dv;
% bin_edges = min(this_DV_inhib(:,1)):250:max(this_DV_inhib(:,1)) + 250;
% opto_cali_ma = nan(12,numel(bin_edges)-1);
% 
% for i_cnd = 1:size(cnd_effects_mean,1)
%     this_DV_inhib = [clusterinfo_sum.real_dv(fr_cnd1_filter), cnd_effects_mean(i_cnd,:)'];
%     this_power = powers(i_cnd);
%     this_distance = AP_distance(i_cnd);
%     idx_1st_sess = find((powers1 == this_power) & (AP_distance1 == this_distance));
%     if ~isempty(idx_1st_sess)
%         this_DV_inhib1 = [clusterinfo_sum1.real_dv(fr_cnd1_filter1), cnd_effects_mean1(idx_1st_sess,:)'];
%         this_DV_inhib = [this_DV_inhib;this_DV_inhib1];
%     end
%     [bin_idx, ~] = discretize(this_DV_inhib(:,1), bin_edges);
%     mean_values = accumarray(bin_idx, this_DV_inhib(:,2), [], @mean);
%     bin_centers = bin_edges(1:end-1) + diff(bin_edges)/2;
%     opto_cali_ma(i_cnd,:) = mean_values;
% 
%     save('opto_cali_ma.mat','opto_cali_ma','bin_centers')
% end
% 



%%
load('/opto_cali_ma.mat')
distances = 0:3;% mm
figure('Position',[0,0,600,250])
al = tiledlayout(1,3,"TileSpacing","compact");
nexttile
imagesc(distances,bin_centers/1000,opto_cali_ma(1:4,:)',[0,1])
axis xy
colormap(flipud(parula))
%clim([0 1])
title('1mW')
xlabel('distance (mm)')
ylabel('DV (mm)')
nexttile
imagesc(distances,bin_centers/1000,opto_cali_ma(5:8,:)',[0,1])
axis xy
%colorbar
%clim([0 1])
title('1.5mW')
yticklabels('')
nexttile
imagesc(distances,bin_centers/1000,opto_cali_ma(9:12,:)',[0,1])
axis xy
cl = colorbar;
cl.Label.String = 'normalized fr.';
%clim([0 1])
title('4mW')
yticklabels('')

cmap = makeColormap([ 0 0 0; 1 1 1], 255);
colormap(cmap)

set(findall(gcf,'-property','FontSize'),'FontSize',14);
set(findall(gcf,'-property','FontName'),'FontName','Arial');

%% inhibition and rebound distribution, combine two animals, combine 0-1mm, 2-3mm, remove 400ms ramp down
% 
% select_cnd1 = [1,9,11,13];
% select_cnd2 = [14,22,24,26];
% for i_idx = 1:2
%     opto_cali_struct1 = cali_struct(i_idx,1);
%     x_times1 = opto_cali_struct1(1,1).x_times;
%     this_clusterinfo1 = opto_cali_struct1(1,1).this_clusterinfo;
%     select_cnd_sum1 = [select_cnd1,select_cnd2];
%     cnd_psth1 = nan(numel(select_cnd_sum1),numel(x_times1),size(opto_cali_struct1.psth,3));
%     cnd_psth_org1 = nan(numel(select_cnd_sum1),numel(x_times1),size(opto_cali_struct1.psth,3));
%     opto_info_table1 = opto_cali_struct1(1,1).opto_table;
% 
% 
%     trial_cnd01 = opto_cali_struct1.psth(opto_cali_struct1.PD.isopto == 0,:,:);
%     trial_cnd0_mu1 = mean(trial_cnd01(:,:,:), 1, 'omitnan');
%     trial_cnd0_mu1_plot = mean(trial_cnd01(randsample(1:size(trial_cnd01,1),20,0),:,:), 1, 'omitnan');
%     trial_cnd0_std1 = std(trial_cnd01, 0, 1, 'omitnan');
% 
% 
%     for cnd_idx = 1:numel(select_cnd_sum1)
%         this_cnd_idx = select_cnd_sum1(cnd_idx);
%         this_cnd_psth = opto_cali_struct1.psth(opto_cali_struct1.PD.cond_number == this_cnd_idx,:,:);
%         control_mu = repmat(trial_cnd0_mu1,size(this_cnd_psth,1),1,1);
% 
%         this_cnd_psth_norm = this_cnd_psth./control_mu;
%         cnd_psth1(cnd_idx,:,:) = squeeze(mean(this_cnd_psth_norm,1, 'omitnan'));
%         cnd_psth_org1(cnd_idx,:,:) = squeeze(mean(this_cnd_psth,1, 'omitnan'));
%     end
%     if i_idx == 1
%         cnd_psth1_sum = cnd_psth1;
%         cnd_psth_org1_sum = cnd_psth_org1;
%         trial_cnd0_sum1 = trial_cnd0_mu1;
% 
%         trial_cnd0_sum1_plot = trial_cnd0_mu1_plot;
%     else
%         cnd_psth1_sum = cat(3, cnd_psth1_sum, cnd_psth1);
%         cnd_psth_org1_sum = cat(3, cnd_psth_org1_sum, cnd_psth_org1);
%         trial_cnd0_sum1 = cat(3, trial_cnd0_sum1, trial_cnd0_mu1);
% 
%         trial_cnd0_sum1_plot = cat(3, trial_cnd0_sum1_plot, trial_cnd0_mu1_plot);
%     end
% end
% 
% 
% select_cnd1 = [1:6:24,3:6:24,5:6:24];
% select_cnd2 = [2:6:24,4:6:24,6:6:24];
% for i_idx = 3:4
%     opto_cali_struct = cali_struct(i_idx,1);
%     x_times = opto_cali_struct(1,1).x_times;
%     this_clusterinfo = opto_cali_struct(1,1).this_clusterinfo;
%     select_cnd = [select_cnd1,select_cnd2];
%     cnd_psth = nan(numel(select_cnd),numel(x_times),size(opto_cali_struct.psth,3));
%     cnd_psth_org = nan(numel(select_cnd),numel(x_times),size(opto_cali_struct.psth,3));
%     opto_info_table = opto_cali_struct(1,1).opto_table;
% 
%     trial_cnd0 = opto_cali_struct.psth(opto_cali_struct.PD.isopto == 0,:,:);
%     trial_cnd0_mu = mean(trial_cnd0(:,:,:), 1, 'omitnan');
%     trial_cnd0_mu_plot = mean(trial_cnd0(randsample(1:size(trial_cnd0,1),20,0),:,:), 1, 'omitnan');
%     trial_cnd0_std = std(trial_cnd0, 0, 1, 'omitnan');
%     for cnd_idx = 1:numel(select_cnd)
%         this_cnd_idx = select_cnd(cnd_idx);
%         this_cnd_psth = opto_cali_struct.psth(opto_cali_struct.PD.cond_number == this_cnd_idx,:,:);
%         control_mu = repmat(trial_cnd0_mu,size(this_cnd_psth,1),1,1);
% 
%         this_cnd_psth_norm = this_cnd_psth./control_mu;
%         cnd_psth(cnd_idx,:,:) = squeeze(mean(this_cnd_psth_norm,1, 'omitnan'));
%         cnd_psth_org(cnd_idx,:,:) = squeeze(mean(this_cnd_psth,1, 'omitnan'));
%     end
%     if i_idx == 3
%         cnd_psth_sum = cnd_psth;
%         cnd_psth_org_sum = cnd_psth_org;
%         trial_cnd0_sum = trial_cnd0_mu;
% 
%         trial_cnd0_sum_plot = trial_cnd0_mu_plot;
%     end
%     if i_idx == 4
%         cnd_psth_sum_temp = cat(3, cnd_psth_sum, cnd_psth);
%         cnd_psth_sum = cnd_psth_sum_temp;
%         cnd_psth_org_sum_temp = cat(3, cnd_psth_org_sum, cnd_psth_org);
%         cnd_psth_org_sum = cnd_psth_org_sum_temp;
%         trial_cnd0_sum_temp = cat(3, trial_cnd0_sum, trial_cnd0_mu);
%         trial_cnd0_sum = trial_cnd0_sum_temp;
% 
%         trial_cnd0_sum_temp_plot = cat(3, trial_cnd0_sum_plot, trial_cnd0_mu_plot);
%         trial_cnd0_sum_plot = trial_cnd0_sum_temp_plot;
%     end
% 
% end
% 
% cnd_ma = [select_cnd1;select_cnd2];
% cnd_ma1 = [nan,nan,nan,nan,1,9,11,13,14,22,24,26;
%     nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan,nan];
% figure()
% set(gcf, 'Position', [0, 0, 500, 300]);
% t1 = tiledlayout(2, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
% xlabel(t1, 'rebound (a.u.)')
% ylabel(t1, 'pdf')
% rebound_ma = nan(6,2);
% combine_idx = 1:2:size(cnd_ma,2);
% AP_forplots = repmat({'0-1mm','2-3mm'},1,3);
% power_forplots = repelem([1,2,4],1,2);
% nexttile_position = reshape([1:3; 4:6], 1, []);
% 
% for jj = 1:numel(combine_idx)
%     nexttile(t1,nexttile_position(jj))
%     % combine the 200ms ramp down
%     this_idx = combine_idx(jj);
%     plot_this_cnd_psth_z = squeeze(cnd_psth_sum(this_idx,:,:))';
%     plot_this_cnd_psth = squeeze(cnd_psth_org_sum(this_idx,:,:))';
%     ext_idx = mean(plot_this_cnd_psth_z(:, x_times>0 & x_times<.5),2)>1;
%     plot_cells_psth = plot_this_cnd_psth(~ext_idx,:);
%     control_trial_psth = squeeze(trial_cnd0_sum)';
%     this_control = control_trial_psth(~ext_idx,:);
%     this_control_plot = squeeze(trial_cnd0_sum_plot)';
%     plot_tb1 = [mean(plot_cells_psth(:,x_times>-0.5 & x_times<0),2),...
%         mean(this_control(:,x_times>=-0.5 & x_times<0),2),mean(this_control(:,x_times>1 & x_times<=1.5),2),...
%         mean(plot_cells_psth(:,x_times>0 & x_times<=0.5),2),...
%         mean(plot_cells_psth(:,x_times>1 & x_times<=1.5),2), zeros(size(plot_cells_psth,1),1)];
%     plot_tb1 = array2table(plot_tb1,"VariableNames",{'baseline','baseline_inhib','baseline_rebound','inhib','rebound','group'});
% 
%     plot_tb1c = [
%         mean(this_control_plot(:,x_times>=-0.5 & x_times<0),2),mean(this_control_plot(:,x_times>1 & x_times<=1.5),2)];
%     plot_tb1c = array2table(plot_tb1c,"VariableNames",{'baseline','baseline_rebound'});
% 
%     if ~isnan(cnd_ma1(1,this_idx))
%         plot_this_cnd_psth_z3 = squeeze(cnd_psth1_sum(this_idx-4,:,:))';
%         plot_this_cnd_psth3 = squeeze(cnd_psth_org1_sum(this_idx-4,:,:))';
%         ext_idx3 = mean(plot_this_cnd_psth_z3(:, x_times>0 & x_times<.5),2)>1;
%         plot_cells_psth3 = plot_this_cnd_psth3(~ext_idx3,:);
%         control_trial_psth3 = squeeze(trial_cnd0_sum1)';
%         this_control3 = control_trial_psth3(~ext_idx3,:);
% 
%         this_control3_plot = squeeze(trial_cnd0_sum1_plot)';
%         plot_tb3 = [mean(plot_cells_psth3(:,x_times>-0.5 & x_times<0),2),...
%             mean(this_control3(:,x_times>=-0.5 & x_times<0),2),mean(this_control3(:,x_times>1.1 & x_times<=1.5),2),...
%             mean(plot_cells_psth3(:,x_times>0 & x_times<=0.5),2),...
%             mean(plot_cells_psth3(:,x_times>1 & x_times<=1.5),2), zeros(size(plot_cells_psth3,1),1)];
%         plot_tb3 = array2table(plot_tb3,"VariableNames",{'baseline','baseline_inhib','baseline_rebound','inhib','rebound','group'});
% 
%         plot_tb3c = [
%             mean(this_control3_plot(:,x_times>=-0.5 & x_times<0),2),mean(this_control3_plot(:,x_times>1 & x_times<=1.5),2)];
%         plot_tb3c = array2table(plot_tb3c,"VariableNames",{'baseline','baseline_rebound'});
% 
%         plot_tb1 = [plot_tb1;plot_tb3];
%         plot_tb1c = [plot_tb1c;plot_tb3c];
%     end
% 
%     plot_this_cnd_psth_z = squeeze(cnd_psth_sum(this_idx+1,:,:))';
%     plot_this_cnd_psth = squeeze(cnd_psth_org_sum(this_idx+1,:,:))';
%     ext_idx1 = mean(plot_this_cnd_psth_z(:, x_times>0 & x_times<.5),2)>1;
%     plot_cells_psth = plot_this_cnd_psth(~ext_idx1,:);
%     control_trial_psth = squeeze(trial_cnd0_sum)';
%     this_control = control_trial_psth(~ext_idx1,:);
% 
%     this_control_plot = squeeze(trial_cnd0_sum_plot)';
%     plot_tb11 = [mean(plot_cells_psth(:,x_times>-0.5 & x_times<0),2),...
%         mean(this_control(:,x_times>=-0.5 & x_times<0),2),mean(this_control(:,x_times>1 & x_times<=1.5),2),...
%         mean(plot_cells_psth(:,x_times>0 & x_times<=0.5),2),...
%         mean(plot_cells_psth(:,x_times>1 & x_times<=1.5),2), zeros(size(plot_cells_psth,1),1)];
%     plot_tb11 = array2table(plot_tb11,"VariableNames",{'baseline','baseline_inhib','baseline_rebound','inhib','rebound','group'});
% 
%     plot_tb11c = [
%         mean(this_control_plot(:,x_times>=-0.5 & x_times<0),2),mean(this_control_plot(:,x_times>1 & x_times<=1.5),2)];
%     plot_tb11c = array2table(plot_tb11c,"VariableNames",{'baseline','baseline_rebound'});
% 
%     if ~isnan(cnd_ma1(1,this_idx+1))
%         plot_this_cnd_psth_z3 = squeeze(cnd_psth1_sum(this_idx-3,:,:))';
%         plot_this_cnd_psth3 = squeeze(cnd_psth_org1_sum(this_idx-3,:,:))';
%         ext_idx3 = mean(plot_this_cnd_psth_z3(:, x_times>0 & x_times<.5),2)>1;
%         plot_cells_psth3 = plot_this_cnd_psth3(~ext_idx3,:);
%         control_trial_psth3 = squeeze(trial_cnd0_sum1)';
%         this_control3 = control_trial_psth3(~ext_idx3,:);
% 
%         this_control3_plot = squeeze(trial_cnd0_sum1_plot)';
%         plot_tb31 = [mean(plot_cells_psth3(:,x_times>=-0.5 & x_times<0),2),...
%             mean(this_control3(:,x_times>=-0.5 & x_times<0),2),mean(this_control3(:,x_times>1 & x_times<=1.5),2),...
%             mean(plot_cells_psth3(:,x_times>0 & x_times<=0.5),2),...
%             mean(plot_cells_psth3(:,x_times>1 & x_times<=1.5),2), zeros(size(plot_cells_psth3,1),1)];
%         plot_tb31 = array2table(plot_tb31,"VariableNames",{'baseline','baseline_inhib','baseline_rebound','inhib','rebound','group'});
% 
%         plot_tb31c = [
%             mean(this_control3_plot(:,x_times>=-0.5 & x_times<0),2),mean(this_control3_plot(:,x_times>1 & x_times<=1.5),2)];
%         plot_tb31c = array2table(plot_tb31c,"VariableNames",{'baseline','baseline_rebound'});
% 
%         plot_tb11 = [plot_tb11;plot_tb31];
%         plot_tb11c = [plot_tb11c;plot_tb31c];
%     end
%     plot_tb11_sum = [plot_tb1;plot_tb11];
%     plot_tb11c_sum = [plot_tb1c;plot_tb11c];
% 
%     plot_tb = [plot_tb11_sum];
% 
%     plot_tb_nrm = plot_tb;
%     plot_tb_nrm.inhib = (plot_tb_nrm.inhib - plot_tb_nrm.baseline)./plot_tb_nrm.baseline;
%     plot_tb_nrm.rebound = (plot_tb_nrm.rebound-plot_tb_nrm.baseline) ./ plot_tb_nrm.baseline;
%     plot_tb_nrm.control = (plot_tb_nrm.baseline_rebound-plot_tb_nrm.baseline_inhib) ./ plot_tb_nrm.baseline_inhib;
% 
%     plot_control = plot_tb11c_sum;
%     plot_control.control = (plot_control.baseline_rebound-plot_control.baseline) ./ plot_control.baseline;
%     hold on
%     plot_tb_nrm = plot_tb_nrm(plot_tb_nrm.rebound<10,:);
%     [x_pdf{jj},y_pdf{jj}] = ksdensity(plot_tb_nrm.rebound(plot_tb_nrm.group==0));
%     plot(y_pdf{jj},x_pdf{jj},'b-','LineWidth',2);
%     this_median{jj} = median(plot_tb_nrm.rebound(plot_tb_nrm.group==0));
%     xline(this_median{jj},'b:','LineWidth',2);
%     xlim([-1,1])
%     ylim([0 2.2])
%     yticks([])
%     xline(0,'LineWidth',1)
%     title({sprintf('dist. %s',AP_forplots{jj}), sprintf('power %.0f mW',power_forplots(jj))})
%     set(gca, 'LineWidth', 2);
% end
% set(findall(gcf,'-property','FontSize'),'FontSize',12);
% set(findall(gcf,'-property','FontName'),'FontName','Arial');
% 
% save('rebound_vars.mat','x_pdf','y_pdf','this_median')

load(['rebound_vars.mat'])

figure
plot_ind = [1,3,5];
powers = {'1 mW', '2 mW', '4 mW'};
for i = 1:3
subplot(1,3,i)
 plot(y_pdf{plot_ind(i)},x_pdf{plot_ind(i)},'k-','LineWidth',2);hold on
 plot([0,0],ylim,'k:')
    scatter(this_median{plot_ind(i)},0,'v','k','filled');
    xlim([-1,1])
    ylim([0 2.2])
    yticks([])
    xline(0,'LineWidth',1)
    axis square
    box off
    title(powers{i})
    xlabel('Rebound')
end



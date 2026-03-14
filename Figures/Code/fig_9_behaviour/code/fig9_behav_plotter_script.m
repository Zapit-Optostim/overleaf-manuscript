% this script loads in pre-processed data to generate behaviour validation
% figures in the manuscript. Raw data files can be provided if required.

clearvars

% point to ~/Code/fig9_behaviour directory;
data_dir = uigetdir();%

addpath(genpath(data_dir));

load_existing_data = 1;% load in the previous generated data table

if load_existing_data == 1
    dataTable = readtable([data_dir filesep 'data' filesep 'dataTable_whisker_opto_mapping.csv']);
    load([data_dir filesep 'data' filesep 'whisker_opto_mean_effect.mat'])
else
    performance_thr = .7;
    rolling_window=100;
    exp_mice = {'OLI-M-0116','OLI-M-0117','OLI-M-0118','OLI-M-0119'};

    all_mice = [exp_mice];
    z = 1;
    for x = 1:numel(all_mice)
        mouse_name = all_mice{x};
        data_path = ['/Volumes/ogma/headfixed/behaviour-data/' mouse_name '/Stage3_WhiskerDiscrim_delay_zapit/Session Data/'];% this is the uni only protocol with 500 ms resolution

        files = dir([data_path filesep '*.mat']);

        for f = 1:size(files,1)
            f
            if contains(files(f).name,'202')

                load([files(f).folder filesep files(f).name])


                if numel(SessionData.choice_data.correct_trial)-SessionData.params.num_warmup_trials > 100 % only analyse sessions with 100+ experiment trials
                    Seq{z} = SessionData.params.zapit_trial_type(1:numel(SessionData.choice_data.correct_trial));
                    delay{z} = SessionData.params.trial_zap_onset_delay(1:numel(SessionData.choice_data.correct_trial));
                    correct_choice{z} = SessionData.choice_data.correct_trial;
                    RT{z} = SessionData.choice_data.ReactionTime;
                    power{z} = SessionData.params.zap_power(1:numel(SessionData.choice_data.correct_trial));

                    power{z}(1:SessionData.params.num_warmup_trials)=[];
                    Seq{z}(1:SessionData.params.num_warmup_trials)=[];
                    delay{z}(1:SessionData.params.num_warmup_trials)=[];
                    correct_choice{z}(1:SessionData.params.num_warmup_trials)=[];
                    correct_choice_laser_off{z} = correct_choice{z};
                    correct_choice_laser_off{z}(~isnan(Seq{z}))=nan;
                    RT{z}(1:SessionData.params.num_warmup_trials)=[];

                    mouseid{z} = repmat(mouse_name,numel(RT{z}),1);
                    sessid{z} = repmat([SessionData.Info.SessionDate '_' mouse_name],numel(RT{z}),1);
                    include_trials{z} = zeros(1,numel(correct_choice_laser_off{z}));

                    clear roll_mean;
                    for i = 1:numel(correct_choice_laser_off{z})-99
                        roll_mean(i) = nanmean(correct_choice_laser_off{z}(i:i+99));
                    end

                    tmp = find(roll_mean>=performance_thr);

                    GOODTRIALS(1) = min(tmp);
                    GOODTRIALS(2) = max(tmp)+rolling_window-1;
                    include_trials{z}(GOODTRIALS(1):GOODTRIALS(2))=1;

                    z = z+1;
                end
            end

        end
    end

    mouseid_cat = vertcat(mouseid{:});
    sessid_cat = vertcat(sessid{:});

    power_cat = horzcat(power{:});
    include_trials_cat = horzcat(include_trials{:});
    Seq_cat = horzcat(Seq{:});
    delay_cat = horzcat(delay{:});
    correct_choice_cat = horzcat(correct_choice{:});
    RT_cat = horzcat(RT{:});
    RT_cat = RT_cat-2;

    RT_cat(include_trials_cat==0)=[];
    correct_choice_cat(include_trials_cat==0)=[];
    delay_cat(include_trials_cat==0)=[];
    Seq_cat(include_trials_cat==0)=[];
    power_cat(include_trials_cat==0)=[];
    mouseid_cat(include_trials_cat==0,:)=[];
    sessid_cat(include_trials_cat==0,:)=[];

    power_cat(isnan(correct_choice_cat))=[];
    Seq_cat(isnan(correct_choice_cat))=[];
    delay_cat(isnan(correct_choice_cat))=[];
    RT_cat(isnan(correct_choice_cat))=[];
    mouseid_cat(isnan(correct_choice_cat),:)=[];
    sessid_cat(isnan(correct_choice_cat),:)=[];
    correct_choice_cat(isnan(correct_choice_cat))=[];

    power_exclude = 4; % some sessions included 2 and 4 mW trials, for simplicity just lok at 2 mW

    RT_cat(power_cat==power_exclude)=[];
    correct_choice_cat(power_cat==power_exclude)=[];
    delay_cat(power_cat==power_exclude)=[];
    Seq_cat(power_cat==power_exclude)=[];
    mouseid_cat(power_cat==power_exclude,:)=[];
    sessid_cat(power_cat==power_exclude,:)=[];
    power_cat(power_cat==power_exclude)=[];
    opto = zeros(1,numel(Seq_cat));
    opto(~isnan(Seq_cat))=1;

    for d = 1:2
        for cond = 1:21
            mean_effect.p_corr_opto(d,cond) = nanmean(correct_choice_cat(Seq_cat == cond & (delay_cat == (d-1))));
            mean_effect.RT_opto(d,cond) = nanmedian(RT_cat(Seq_cat == cond & (delay_cat == (d-1))));
        end
    end

    dataTable = table(mouseid_cat, correct_choice_cat',delay_cat',Seq_cat',opto',RT_cat',sessid_cat);
    dataTable.Properties.VariableNames = {'mouse','choice','delay','location','opto','rt','sessid'};
    dataTable.sessid = cellstr(dataTable.sessid);

    dataTable.sessid = categorical(dataTable.sessid);

    % save the table
    writetable(dataTable, ['dataTable_whisker_opto_mapping.csv'], 'WriteVariableNames', true);
    save('whisker_opto_mean_effect.mat','mean_effect')

end

sess_ids = unique(dataTable.sessid);
dataTable.sessid = categorical(dataTable.sessid);

% calculate mean p(corr) and rt on control trials for each session, so can
% calculate overall control performance.
for z = 1:numel(sess_ids)
    p_corr_per_session(z)  = mean(dataTable.choice(dataTable.opto == 0 & dataTable.sessid == sess_ids(z)));
    RT_per_session(z)  = mean(dataTable.rt(dataTable.opto == 0 & dataTable.sessid == sess_ids(z)));
end

disp(['Average performance on control trials: ' num2str(mean(p_corr_per_session))])
%%
re_run_stats = 0; % 0 = load in the processed data, 1 = re-run the cross validation model comparison

if re_run_stats == 0
    load([data_dir filesep 'data' filesep 'p_values_bonfholm_corr.mat'])
else

    iterations=20;
    locations = 1:17;

    for rng_seed = 1:1
        %rng_seed = 1;
        rng(rng_seed)% for reproducibility

        for epoch = 1:2
            epoch
            for loc = 1:17
                tic
                loc
                zap_loc = (loc);
                % get data for epoch and location
                zapit_data_laser = dataTable(dataTable.location == zap_loc & dataTable.delay==epoch-1,:);
                zapit_data_control = dataTable(dataTable.opto == 0,:);
                zapit_data_control = zapit_data_control(ismember(zapit_data_control.sessid, unique(zapit_data_laser.sessid)), :); % filter out sessions without opto trials

                test_size_control = floor(size(zapit_data_control,1)/iterations);
                test_size_laser = floor(size(zapit_data_laser,1)/iterations);

                zapit_data_laser_sorted = zapit_data_laser(randperm(size(zapit_data_laser,1)),:);
                zapit_data_control_sorted = zapit_data_control(randperm(size(zapit_data_control,1)),:);

                parfor i=1:iterations
                    i
                    test_idx = false(size(zapit_data_laser,1),1);
                    test_idx((i-1)*test_size_laser+1:i*test_size_laser) = true;
                    zapit_data_laser_test_data = zapit_data_laser_sorted(test_idx,:);
                    zapit_data_laser_train_data = zapit_data_laser_sorted(~test_idx,:);

                    test_idx = false(size(zapit_data_control,1),1);
                    test_idx((i-1)*test_size_control+1:i*test_size_control) = true;
                    zapit_data_control_test_data = zapit_data_control_sorted(test_idx,:);
                    zapit_data_control_train_data = zapit_data_control_sorted(~test_idx,:);

                    train_data = [zapit_data_control_train_data ; zapit_data_laser_train_data];
                    test_data = [zapit_data_control_test_data ; zapit_data_laser_test_data];

                    % Assign a higher weight to opto (laser) trials to reduce imbalance influence
                    W = ones(height(train_data), 1);
                    W(train_data.opto == 1) = 20;  % give opto trials 20x the weight of control trials
                    % --------------------------------

                    test_data_size(epoch,loc,i) = size(test_data,1);

                    model1 = fitglme(train_data,'choice ~ 1 + (1|mouse)','Distribution','Binomial','Link','logit','FitMethod','Laplace','Weights',W);
                    model2 = fitglme(train_data,'choice ~ opto + (1|mouse)','Distribution','Binomial','Link','logit','FitMethod','Laplace','Weights',W);

                    predicted1 = predict(model1,test_data);
                    predicted2 = predict(model2,test_data);

                    % Calculate cross-validated likelihood
                    LLH1(epoch,loc,i) = -1*nansum(log(predicted1.*test_data.choice + (1-predicted1).*(1-test_data.choice)));
                    LLH2(epoch,loc,i) = -1*nansum(log(predicted2.*test_data.choice + (1-predicted2).*(1-test_data.choice)));
                end
                toc
            end
        end
    end

    for epoch = 1:2
        for loc = 1:17
            LLH = [squeeze(LLH1(epoch,loc,:))'; squeeze(LLH2(epoch,loc,:))'];
            test_size = squeeze(test_data_size(epoch,loc,:));
            LH{loc} = exp(-LLH./test_size'); % normalised liklihood

            [h,p]=ttest(LH{loc}(1,:),LH{loc}(2,:));
            pval(loc,epoch) = p;
        end
    end

    % requires bonf_holm from https://github.com/erlichlab/elutils
    pval_corr_opsin(:,1) = bonf_holm(pval(:,1),0.05)';
    pval_corr_opsin(:,2) = bonf_holm(pval(:,2),0.05)';
    pval_corr_opsin(pval_corr_opsin>1)=1;
    %

    for epoch = 1:2
        for cond = 1:17
            zapit_data_laser = dataTable(dataTable.location == cond & dataTable.delay==epoch-1,:);
            zapit_data_control = dataTable(dataTable.opto == 0,:);
            zapit_data_control = zapit_data_control(ismember(zapit_data_control.sessid, unique(zapit_data_laser.sessid)), :); % filter out sessions without opto trials
            [rt_p_val(cond,epoch),~]=ranksum(zapit_data_laser.rt, zapit_data_control.rt);
        end
    end

    % requires stats.bonf_holm from https://github.com/erlichlab/elutils
    rt_p_val_corr(:,1) = bonf_holm(rt_p_val(:,1),0.05)';
    rt_p_val_corr(:,2) = bonf_holm(rt_p_val(:,2),0.05)';
    rt_p_val_corr(rt_p_val_corr>1)=1;

    p_values_bonfholm_corr.rt_p_val_corr = rt_p_val_corr;
    p_values_bonfholm_corr.pval_corr_opsin = pval_corr_opsin;

    save('p_values_bonfholm_corr.mat','p_values_bonfholm_corr')
end
%%
cmap = makeColormap([ 0.7176    0.2745    1.0000; 1 1 1], 255);

stim_coords = ...
    [0.5,2.5;
    1.75,2.5;
    0.5,1.25;
    1.75,1.25;
    3,1.25;
    0.5,0;
    1.75,0;
    3,0;
    0.5,-1.45;
    1.75,-1.25;
    3.5,-1.25;
    0.5,-2.7;
    1.75,-2.5;
    3,-2.5;
    4.25,-2.5;
    1.75,-3.75;
    3,-3.75];

figure;

p_corr_opto = mean_effect.p_corr_opto;
RT_opto = mean_effect.RT_opto;
pval_corr_opsin = p_values_bonfholm_corr.pval_corr_opsin;
rt_p_val_corr = p_values_bonfholm_corr.rt_p_val_corr;


for epoch = 1:2

    subplot(3,2,epoch)

    for x = 1:17

        if (pval_corr_opsin(x,epoch)) > (0.05)
            scatter(stim_coords(x,1),stim_coords(x,2),15,'kx','linewidth',1); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),15,'kx','linewidth',1); hold on
        elseif (pval_corr_opsin(x,epoch)) < (0.0001)
            scatter(stim_coords(x,1),stim_coords(x,2),150,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),150,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (pval_corr_opsin(x,epoch)) < (0.001)
            scatter(stim_coords(x,1),stim_coords(x,2),100,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),100,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (pval_corr_opsin(x,epoch)) < (0.01)
            scatter(stim_coords(x,1),stim_coords(x,2),75,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),75,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (pval_corr_opsin(x,epoch)) < (0.05)
            scatter(stim_coords(x,1),stim_coords(x,2),25,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),25,p_corr_opto(epoch,x)-mean(dataTable.choice(dataTable.opto==0)),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on

        end

    end

    colormap(gca, cmap);
    c1 = colorbar;
    c1.Location = 'southoutside';
    c1.Label.String ='\DeltaP(Correct)';
    c1.Label.FontSize = 12;
    c1.Ticks = [-.15,0];

    caxis([-.15 0])
    box off
    axis off
    axis square
    title(['Epoch ' num2str(epoch)])

    try
    draw_top_down_ccf_outline
    end
    ylim([-5,6])
    xlim([-5.5,5.5])

end

cmap = makeColormap([1 1 1; 0.6353    0.0784    0.1843], 255);

for epoch = 1:2

    h = subplot(3,2,epoch+2);

    for x = 1:17
        hold on
        if (rt_p_val_corr(x,epoch)) > (0.05)
            scatter(stim_coords(x,1),stim_coords(x,2),15,'kx','linewidth',1); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),15,'kx','linewidth',1); hold on
        elseif (rt_p_val_corr(x,epoch)) < (0.0001)
            scatter(stim_coords(x,1),stim_coords(x,2),150,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),150,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (rt_p_val_corr(x,epoch)) < (0.001)
            scatter(stim_coords(x,1),stim_coords(x,2),100,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),100,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (rt_p_val_corr(x,epoch)) < (0.01)
            scatter(stim_coords(x,1),stim_coords(x,2),75,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),75,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        elseif (rt_p_val_corr(x,epoch)) < (0.05)
            scatter(stim_coords(x,1),stim_coords(x,2),25,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
            scatter(-stim_coords(x,1),stim_coords(x,2),25,1000*(RT_opto(epoch,x)-median(dataTable.rt(dataTable.opto==0))),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on

        end
    end

    box off
    axis off
    axis square
    title(['Epoch ' num2str(epoch)])

    try
    draw_top_down_ccf_outline
    end
    hold on
    ylim([-5,6])
    xlim([-5.5,5.5])
    axis square

    colormap(h,cmap)
    caxis([0,35])
    cb = colorbar;
    cb.Label.String = '\Delta RT (ms)';
    cb.Location = 'southoutside';
    cb.Label.FontSize = 12;
    cb.Ticks = [0,35];
end

% plot scale cirlces

h = subplot(3,2,5);

scatter(0,0,15,'kx','linewidth',1); hold on

scatter(0,4,150,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on

scatter(0,3,100,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on
scatter(0,2,75,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on
scatter(0,1,25,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on

ylim([-5,6])
xlim([-5.5,5.5])
axis square
%% choice biasing experiment
load_data=1;
if load_data == 1
    load([data_dir filesep 'data' filesep 'uni_choice_biasing_data.mat'])
else
    clear session
    session{1} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231022_161344.mat');
    session{2} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231023_114940.mat');
    session{3} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231023_120612.mat');
    session{4} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231023_121923.mat');
    session{5} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231024_151613.mat');
    session{6} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231025_165517.mat');
    session{7} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231026_154742.mat');

    session{8} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231022_133004.mat');
    session{9} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231023_104348.mat');
    session{10} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231024_115131.mat');
    session{11} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231025_153227.mat');
    session{12} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231026_141834.mat');

    session{13} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231022_145214.mat');
    session{14} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231022_152434.mat');
    session{15} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231023_134435.mat');
    session{16} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231024_132154.mat');
    session{17} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_delay_matrix_zapit/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_delay_matrix_zapit_20231026_165231.mat');


    clear whiskertrial left_choice whisker_trial zapit_location

    for i = 1:numel(session)
        left_choice{i} = session{i}.SessionData.choice_data.SpatialChoice;
        for x = 1:numel(left_choice{i})

            whisker_trial{i}(x) = session{i}.SessionData.trialvar(x);
            zapit_location{i}(x) = session{i}.SessionData.zapit_trialvar(x);

        end
    end

    data.zapit_location = zapit_location;
    data.whisker_trial = whisker_trial;
    data.left_choice = left_choice;

    save('uni_choice_biasing_data.mat','data')

end

zapit_loc = horzcat(data.zapit_location{:});
choice = horzcat(data.left_choice{:});
whiskertrial = horzcat(data.whisker_trial{:});


% the numbers here refer to position in a 3x3 stimulus matrix of 0,5 and
% 10Hz hz left and right combo whisker airpuffs
trial_pick{1}=7;% uni 10 Hz
trial_pick{2}=[4,8];%10:5
trial_pick{3} = [1,5,9];% equal stim (diagonal of matrix)
trial_pick{4} = [2,6];%10;5
trial_pick{5} = 3;%uni 10Hz

for i = 1:5
    clear tmp
    for z = 1:numel(trial_pick{i})

        tmp{z} = choice(whiskertrial==trial_pick{i}(z) & isnan(zapit_loc));
        tmp{z}(isnan(tmp{z}))=[];
    end
    plickleft(i) = mean(horzcat(tmp{:})==1);
    plickleft_bino(i,:) = binoci(horzcat(tmp{:})==1);

    clear tmp
    for z = 1:numel(trial_pick{i})
        tmp{z} = choice(whiskertrial==trial_pick{i}(z) & zapit_loc==1);
        tmp{z}(isnan(tmp{z}))=[];
    end
    plickleft_zap1(i) = mean(horzcat(tmp{:})==1);
    plickleft_zap1_bino(i,:) = binoci(horzcat(tmp{:})==1);

    clear tmp
    for z = 1:numel(trial_pick{i})
        tmp{z} = choice(whiskertrial==trial_pick{i}(z) & zapit_loc==2);
        tmp{z}(isnan(tmp{z}))=[];
    end
    plickleft_zap2(i) = mean(horzcat(tmp{:})==1);
    plickleft_zap2_bino(i,:) = binoci(horzcat(tmp{:})==1);
end

for t = 1:5
    errbar1(1,t) = plickleft(t) - plickleft_bino(t,1);
    errbar1(2,t) = plickleft(t) - plickleft_bino(t,2);
end

for t = 1:5
    errbar2(1,t) = plickleft_zap1(t) - plickleft_zap1_bino(t,1);
    errbar2(2,t) = plickleft_zap1(t) - plickleft_zap1_bino(t,2);
end

for t = 1:5
    errbar3(1,t) = plickleft_zap2(t) - plickleft_zap2_bino(t,1);
    errbar3(2,t) = plickleft_zap2(t) - plickleft_zap2_bino(t,2);
end

figure

% control trials
[param,stat]=sigm_fit_color(1:5,plickleft,[],[],1,'k');hold on
errorbar(1:5,plickleft, errbar1(1,:),errbar1(2,:),'ok','linewidth',2,'Capsize',0,'MarkerFaceColor','k','MarkerEdgeColor','none');

% left ALM
[param,stat]=sigm_fit_color(1:5,plickleft_zap1,[],[],1,'r');hold on
errorbar(1:5,plickleft_zap1, errbar2(1,:),errbar2(2,:),'or','linewidth',2,'Capsize',0,'MarkerFaceColor','r','MarkerEdgeColor','none');

% Right ALM
[param,stat]=sigm_fit_color(1:5,plickleft_zap2,[],[],1,'b');hold on
errorbar(1:5,plickleft_zap2, errbar3(1,:),errbar3(2,:),'ob','linewidth',2,'Capsize',0,'MarkerFaceColor','b','MarkerEdgeColor','none');

box off
axis square
ylim([0,1]); xlim([0,6])
ylabel('P(Left)')
xlabel('Stim difference (Hz)')
xticks(1:5)
xticklabels({'-10','-5','0','5','10'})
hold on
plot(xlim,[.5,.5],'--k')
plot([3,3],ylim,'--k')
%%

load_data=1;

if load_data == 1
    load([data_dir filesep 'data' filesep 'powersession_data.mat'])
else
    % for this experiment mice received unilateral whisker stimuli, and
    % contralateral uni ALM photoinhibition (i.e. to force errors) of varying
    % laser powers
    powersession{1} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_zapit_power_titration_20231027_112641.mat');
    powersession{2} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_zapit_power_titration_20231028_113352.mat');
    powersession{3} = load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_zapit_power_titration_20231031_134931.mat');
    powersession{4} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_zapit_power_titration_20231030_161737.mat');
    powersession{5} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0037/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0037_Stage3_WhiskerDiscrim_zapit_power_titration_20231030_154238.mat');
    powersession{6} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_zapit_power_titration_20231027_133044.mat');
    powersession{7} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_zapit_power_titration_20231028_144639.mat');
    powersession{8} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_zapit_power_titration_20231031_171648.mat');
    powersession{9} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0036/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0036_Stage3_WhiskerDiscrim_zapit_power_titration_20231030_170040.mat');
    powersession{10} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_zapit_power_titration_20231027_162844.mat');
    powersession{11} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_zapit_power_titration_20231028_132618.mat');
    powersession{12} =load('/Volumes/ogma/headfixed/behaviour-data/OLI-M-0039/Stage3_WhiskerDiscrim_zapit_power_titration/Session Data/OLI-M-0039_Stage3_WhiskerDiscrim_zapit_power_titration_20231031_123851.mat');

    clear data

    for i = 1:numel(powersession)
        data.left_choice{i} = powersession{i}.SessionData.choice_data.SpatialChoice;
        for x = 1:numel(left_choice{i})
            data.whisker_trial{i}(x) = powersession{i}.SessionData.trialvar(x);
            data.zapit_location{i}(x) = powersession{i}.SessionData.zapit_trialvar(x);
            data.zapit_power{i}(x) = powersession{i}.SessionData.params.zap_power(x);% note that for these experiments, power was recorded as peak power (i.e. it should be halved to get time-averaged power per site
        end
    end
    save('powersession_data.mat','data')
end
%
left_choice = data.left_choice;
whisker_trial = data.whisker_trial;
zapit_power = data.zapit_power;

for n = 1:numel(left_choice)
    for i = 0:5
        tmp = left_choice{n}(whisker_trial{n}==3 & zapit_power{n}==i);
        missrate_leftwhisker(n,i+1) = mean(isnan(tmp));
        tmp(isnan(tmp))=[];
        pcorrect_left_whisker(n,i+1) = mean(tmp==1);
        tmp = left_choice{n}(whisker_trial{n}==7 & zapit_power{n}==i);
        missrate_rightwhisker(n,i+1) = mean(isnan(tmp));
        tmp(isnan(tmp))=[];
        pcorrect_right_whisker(n,i+1) = mean(tmp==2);
    end
end

pcorr(:,:,1) = pcorrect_left_whisker;
pcorr(:,:,2) = pcorrect_right_whisker;

pcorr_mean = nanmean(pcorr,3);

figure;

hold on
errorbar(1:6,mean(pcorr_mean),1.96*(std(pcorr_mean)/sqrt(numel(data.left_choice))),'-ok','LineWidth',3);
box off
axis square
ylim([.25,1]); yticks([0,.5,1]); xticks([1,2,3,4,5,6])
xticklabels({'0','0.5','1','1.5','2','2.5'})
xlim([0.5,6.5])
xlabel('Time averaged power (mW)')
ylabel('P(Correct)')

%% IBL task data

% load data
ibl_zapit_data = readtable([data_dir filesep 'data' filesep 'zapit_RT_statistics.csv']);

% subtract mean RT on laser off trials
ibl_zapit_data.RTMean_s_= ibl_zapit_data.RTMean_s_ - ibl_zapit_data.RTMean_s_(1);

cmap = makeColormap([0.0745    0.6235    1.0000; 1 1 1; 0.6353    0.0784    0.1843], 255);

figure
h = subplot(1,2,1);

for x = 2:53
    hold on
    if ibl_zapit_data.P_value(x) > (0.05)
        scatter(ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),15,'kx','linewidth',1); hold on
        scatter(-ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),15,'kx','linewidth',1); hold on
    elseif ibl_zapit_data.P_value(x) < (0.0001)
        scatter(ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),150,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        scatter(-ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),150,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
    elseif ibl_zapit_data.P_value(x) < (0.001)
        scatter(ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),100,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        scatter(-ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),100,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
    elseif ibl_zapit_data.P_value(x) < (0.01)
        scatter(ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),75,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        scatter(-ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),75,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
    elseif ibl_zapit_data.P_value(x) < (0.05)
        scatter(ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),25,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on
        scatter(-ibl_zapit_data.ML_mm_(x),ibl_zapit_data.AP_mm_(x),25,ibl_zapit_data.RTMean_s_(x),'filled','o','linewidth',1,'MarkerEdgeColor','k'); hold on

    end
end

box off
axis off
axis square
try
draw_top_down_ccf_outline
end
hold on
ylim([-5,6])
xlim([-5.5,5.5])
axis square

colormap(h,cmap)
caxis([-.5,.5])
cb = colorbar;
cb.Label.String = '\DeltaRT (ms)';
cb.Location = 'southoutside';
cb.Label.FontSize = 12;
cb.Ticks = [-.5:.250:.5];

% plot scale circles for the legend

h = subplot(1,2,2);

scatter(0,0,15,'kx','linewidth',1); hold on
scatter(0,4,150,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on
scatter(0,3,100,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on
scatter(0,2,75,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on
scatter(0,1,25,'filled','wo','linewidth',1,'MarkerEdgeColor','k'); hold on

ylim([-5,6])
xlim([-5.5,5.5])
axis square


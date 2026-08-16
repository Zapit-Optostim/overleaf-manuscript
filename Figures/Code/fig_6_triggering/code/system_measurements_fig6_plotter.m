clearvars

% Select "fig6_triggering" directory
path_to_data = uigetdir();

addpath(genpath(path_to_data));% add fig6_triggering/code directory to path

filelist = dir(fullfile(path_to_data,'data','100kS_trigger','*.mat'));

n_reps_to_plot = 50;

pre_post_window = [.1,1.2];

srate = 100000; %kS/s
time_range_samples  = pre_post_window*srate;

for i = 1:size(filelist,1)
    
    xx = load([filelist(i).folder filesep filelist(i).name]);
    PhotoDiode1{i}=xx.A/max(xx.A);
    Trigger1{i}=xx.B/max(xx.B);

    ind = pt_continuousabove(Trigger1{i},0,.1,1,10000,1);
    n_samples = size(Trigger1{i},2);

    for z = 1:size(ind,1)
        try
            Trigger_trace1{i}(z,:)=Trigger1{i}(ind(z,1)-time_range_samples(1):ind(z,1)+time_range_samples(2));
            Photodiode_trace1{i}(z,:)=PhotoDiode1{i}(ind(z,1)-time_range_samples(1):ind(z,1)+time_range_samples(2));
        end
    end
end

z1 = vertcat(Photodiode_trace1{:});z1(sum(z1,2)==0,:)=[];
z2 = vertcat(Trigger_trace1{:});z2(sum(z2,2)==0,:)=[];

% get signal latency to TTL based on threshold crossing
for i = 1:n_reps_to_plot
    ind = pt_continuousabove(z1(i,:),0,.1,1,10000,1);
    latency(i) = ind(1,1)-10000;
end

mean_latency_in_samples = mean(latency);
mean_latency_in_ms = 1000*(mean_latency_in_samples/srate);

figure

subplot(3,2,1)

trace = [1,10,50];% repetitions to plot

jump = [0,3,6];

for i = 1:numel(trace)
    plot(z1(trace(i),:)+jump(i),'-k'); hold on
    plot(z2(trace(i),:)+jump(i)-1.2,'-r'); hold on
end

xticks([-10000:20000:120000])
xticklabels({'-200','0','200','400','600','800','1000'})
xlabel('Time from trigger (ms)')

hold on
box off
plot([10000,10000],ylim,'--b')% stim start
plot([90000,90000],ylim,'--k')% rampdown start
plot([110000,110000],ylim,'--k')% rampdown end

subplot(3,2,2)
plot(1.2+z1(1:n_reps_to_plot,:)','-k');
hold on
plot(z2(1:n_reps_to_plot,:)','-r');
xlim([9900,10200])
xlabel('Time from trigger (ms)')
xticks([9900:100:10200])
xticklabels({'-1','0','1','2'})
plot([10000+mean_latency_in_samples,10000+mean_latency_in_samples],ylim,'--b')
text(1005,0,['Latency = ' num2str(mean_latency_in_ms) ' (ms)'])
axis square
box off
title(['Latency = ' num2str(mean_latency_in_ms) ' ms'])

filelist = dir(fullfile(path_to_data,'data','5kS_delay','*.mat'));

srate = 5000; %kS/s - no need to super high temporal resolution for input/output compaison

for i = 1:size(filelist,1)-1
    xx = load([filelist(i).folder filesep filelist(i).name]);
    PhotoDiode2{i}=xx.A/max(xx.A);
    Trigger2{i}=xx.B/max(xx.B);
end

for i = 1:size(Trigger2,2)
    ind = pt_continuousabove(Trigger2{i},0,.2,1,10000,1);
    n_samples = size(Trigger2{i},2);
    try
        for z = 1:size(ind,1)
            Trigger_trace2{i}(z,:)=Trigger2{i}(ind(z,1)-1000:ind(z,1)+11000);
            Photodiode_trace2{i}(z,:)=PhotoDiode2{i}(ind(z,1)-1000:ind(z,1)+11000);
        end
    end
end

z1 = vertcat(Photodiode_trace2{:});
z2 = vertcat(Trigger_trace2{:});

%figure

subplot(3,2,3:4)

trace = [1,10,50];

jump = [0,3,6]*2;

for i = 1:3
    plot(z1(trace(i),:)+jump(i),'-k'); hold on
    plot(z2(trace(i),:)+jump(i)-1.2,'-r'); hold on
end

hold on
box off
plot([10000,10000],ylim,'--k')
plot([6000,6000],ylim,'--k')
plot([11000,11000],ylim,'--k')
plot([1000,1000],ylim,'--k')

xticks([1000:2500:12000])
xticklabels({'0','500','1000','1500','2000'})
xlabel('Time from trigger (ms)')

%%
filelist = dir(fullfile(path_to_data,'data','100kS_laser_input_output','*.mat'));

srate = 100000; %5kS/s

for i = 1:size(filelist,1)
    xx = load([filelist(i).folder filesep filelist(i).name]);
    PhotoDiode3{i}=xx.A/max(xx.A);
    Trigger3{i}=xx.B/max(xx.B);

    ind = pt_continuousabove(Trigger3{i},0,.2,1,100000,5000);
    n_samples = size(Trigger3{i},2);
    for z = 1:size(ind,1)
        try
            Trigger_trace3{i}(z,:)=Trigger3{i}(ind(z,1)-time_range_samples(1):ind(z,1)+time_range_samples(2));
            Photodiode_trace3{i}(z,:)=PhotoDiode3{i}(ind(z,1)-time_range_samples(1):ind(z,1)+time_range_samples(2));
        end
    end
end

z1 = vertcat(Photodiode_trace3{:});% concat traces for plotting
z2 = vertcat(Trigger_trace3{:});

z1(sum(z1')==0,:)=[]; 
z2(sum(z2')==0,:)=[];

for i = 1:50
    ind = pt_continuousabove(z1(i,:),0,.2,1,100000,5000);
    latency(i) = ind(1,1);
end

subplot(3,2,5)

trace = [1,10,50]; % rep number to plot

jump = [0,3,6];
for i = 1:3
    plot(z1(trace(i),:)+jump(i),'-k'); hold on
    plot(z2(trace(i),:)+jump(i)-1.2,'-m'); hold on
end

hold on
box off
xticks([-10000:20000:120000])
xticklabels({'-200','0','200','400','600','800','1000'})
xlabel('Time from trigger (ms)')

hold on
box off
plot([10000,10000],ylim,'--b')% stim start
plot([90000,90000],ylim,'--k')% rampdown start
plot([110000,110000],ylim,'--k')% rampdown end

subplot(3,2,6)

plot(1.2+z1','-k');
hold on
plot(z2','-m');
xlim([9900,10300]);xlabel('Time from trigger (ms)')
xlim([9900,10200])
xlabel('Time from stim onset (ms)')
xticks([9900:100:10200])
xticklabels({'-1','0','1','2'})
axis square
box off

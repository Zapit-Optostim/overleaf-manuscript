%% Plotting script for eLife paper 2026; contains table of trials and conditions for Zapit eLife paper 2026 plots and plotting code
% Michael Lohse 2026

clear all

try % if folder exist
    cd('eLifeDMDMZapitBehaviour')
end

Organised=1; % Organised data is aready saved

if Organised
    load('OrganisedV1S1ConPlottingData.mat')
else
    OrganiseScanDataForPlotting % first organise raw data to allow this plotting script to run
end

CS=[1 1.25 1.5 2]; % change sizes

clear Perf_Con Perf_S1_2mW Perf_S1_4mW Perf_V1_2mW Perf_V1_4mW Perf_CI_Con Perf_CI_S1_2mW Perf_CI_S1_4mW Perf_CI_V1_2mW Perf_CI_V1_4mW

for M=1:length(unique(ConS1andV1TrialsConcat(1,:))) % get performance of each mouse
    
    MouseTrials{M}=ConS1andV1TrialsConcat(:,ConS1andV1TrialsConcat(1,:)==M); % create mouse specific arrays
    
    for C=1:length(CS) % cycle through change sizes
        
        clear ConSelect S1Select_2mW S1Select_4mW V1Select_2mW V1Select_4mW
        ConSelect=MouseTrials{M}(9,:) == CS(C) & (MouseTrials{M}(3,:) | MouseTrials{M}(4,:)) & MouseTrials{M}(10,:) ==0; % control trials
        
        S1Select_2mW=MouseTrials{M}(9,:) == CS(C) & (MouseTrials{M}(3,:) | MouseTrials{M}(4,:)) & MouseTrials{M}(10,:) ==1 &  MouseTrials{M}(12,:) ==5 & MouseTrials{M}(11,:) ==1; % S1 inactivation 2mW
        S1Select_4mW=MouseTrials{M}(9,:) == CS(C) & (MouseTrials{M}(3,:) | MouseTrials{M}(4,:)) & MouseTrials{M}(10,:) ==1 &  MouseTrials{M}(12,:) ==5 & MouseTrials{M}(11,:) ==2; % S1 inactivation 4mW
        
        V1Select_2mW=MouseTrials{M}(9,:) == CS(C) & (MouseTrials{M}(3,:) | MouseTrials{M}(4,:)) & MouseTrials{M}(10,:) ==1 &  MouseTrials{M}(12,:) ==7 & MouseTrials{M}(11,:) ==1; % V1 inactivation 2mW
        V1Select_4mW=MouseTrials{M}(9,:) == CS(C) & (MouseTrials{M}(3,:) | MouseTrials{M}(4,:)) & MouseTrials{M}(10,:) ==1 &  MouseTrials{M}(12,:) ==7 & MouseTrials{M}(11,:) ==2; % V1 inactivation 4mW
        
        [Perf_Con(C,M) Perf_CI_Con(:,C,M)]=binofit(sum(MouseTrials{M}(3,ConSelect)),length(MouseTrials{M}(3,ConSelect)));
        [Perf_S1_2mW(C,M) Perf_CI_S1_2mW(:,C,M)]=binofit(sum(MouseTrials{M}(3,S1Select_2mW)),length(MouseTrials{M}(3,S1Select_2mW)));
        [Perf_S1_4mW(C,M) Perf_CI_S1_4mW(:,C,M)]=binofit(sum(MouseTrials{M}(3,S1Select_4mW)),length(MouseTrials{M}(3,S1Select_4mW)));
        [Perf_V1_2mW(C,M) Perf_CI_V1_2mW(:,C,M)]=binofit(sum(MouseTrials{M}(3,V1Select_2mW)),length(MouseTrials{M}(3,V1Select_2mW)));
        [Perf_V1_4mW(C,M) Perf_CI_V1_4mW(:,C,M)]=binofit(sum(MouseTrials{M}(3,V1Select_4mW)),length(MouseTrials{M}(3,V1Select_4mW)));
        
    end
end

figure
subplot(2,2,1)
errorbar(CS,mean(Perf_Con'),(std(Perf_Con')./sqrt(size(Perf_Con,1)))*1.96,'k','capSize',0,'linewidth',2) % 1.96*sem is 95% CI
hold on
errorbar(CS+0.01,mean(Perf_S1_2mW'),(std(Perf_S1_2mW')./sqrt(size(Perf_Con,1)))*1.96,'color',[0 130 200]/255,'capSize',0,'linewidth',2)
errorbar(CS+0.02,mean(Perf_S1_4mW'),(std(Perf_S1_4mW')./sqrt(size(Perf_Con,1)))*1.96,'color',[0 100 170]/255,'capSize',0,'linewidth',2)
scatter(CS,mean(Perf_Con'),[100 100 100 100],'k','filled')
scatter(CS+0.01,mean(Perf_S1_2mW'),[100 100 100 100],[0 130 200]/255,'filled')
scatter(CS+0.02,mean(Perf_S1_4mW'),[100 100 100 100],[0 100 170]/255,'filled')
box off
ylabel('Performance')
xlabel('Change Size (Hz)')
title('Avg Across Mice (S1)')
ylim([0 1])
xlim([0.9 2.1])
legend({'Con','2mW','4mW'})
 legend('Location','southeast')
legend boxoff

subplot(2,2,3)
errorbar(CS,mean(Perf_Con'),(std(Perf_Con')./sqrt(size(Perf_Con,1)))*1.96,'k','capSize',0,'linewidth',2) % 1.96*sem is 95% CI
hold on
errorbar(CS+0.03,mean(Perf_V1_2mW'),(std(Perf_V1_2mW')./sqrt(size(Perf_Con,1)))*1.96,'color',[0 114 178]/255,'capSize',0,'linewidth',2)
errorbar(CS+0.04,mean(Perf_V1_4mW'),(std(Perf_V1_4mW')./sqrt(size(Perf_Con,1)))*1.96,'color',[0 100 170]/255,'capSize',0,'linewidth',2)
scatter(CS,mean(Perf_Con'),[100 100 100 100],'k','filled')
scatter(CS+0.03,mean(Perf_V1_2mW'),[100 100 100 100],[0 130 200]/255,'filled')
scatter(CS+0.04,mean(Perf_V1_4mW'),[100 100 100 100],[0 100 170]/255,'filled')
box off
ylabel('Performance')
xlabel('Change Size (Hz)')
ylim([0 1])
xlim([0.9 2.1])
box off
set(findall(gcf,'-property','FontSize'),'FontSize',18)
title('Avg Across Mice (V1)')

ExMouse=2; % example mouse to use

subplot(2,2,2)
errorbar(CS,Perf_Con(:,ExMouse),Perf_CI_Con(1,:,ExMouse)'-Perf_Con(:,ExMouse),Perf_CI_Con(2,:,ExMouse)'-Perf_Con(:,ExMouse),'k','capSize',0,'linewidth',2) % 95% CI binomial
hold on
errorbar(CS+0.01,Perf_S1_2mW(:,ExMouse),Perf_CI_S1_2mW(1,:,ExMouse)'-Perf_S1_2mW(:,ExMouse),Perf_CI_S1_2mW(2,:,ExMouse)'-Perf_S1_2mW(:,ExMouse),'color',[0 130 200]/255,'capSize',0,'linewidth',2)
errorbar(CS+0.02,Perf_S1_4mW(:,ExMouse),Perf_CI_S1_4mW(1,:,ExMouse)'-Perf_S1_4mW(:,ExMouse),Perf_CI_S1_4mW(2,:,ExMouse)'-Perf_S1_4mW(:,ExMouse),'color',[0 100 170]/255,'capSize',0,'linewidth',2)
scatter(CS,Perf_Con(:,ExMouse),[100 100 100 100],'k','filled')
scatter(CS+0.01,Perf_S1_2mW(:,ExMouse),[100 100 100 100],[0 130 200]/255,'filled')
scatter(CS+0.02,Perf_S1_4mW(:,ExMouse),[100 100 100 100],[0 100 170]/255,'filled')
box off
ylabel('Performance')
xlabel('Change Size (Hz)')
title('Example Mouse (S1)')
ylim([0 1])
xlim([0.9 2.1])

subplot(2,2,4)
errorbar(CS,Perf_Con(:,ExMouse),Perf_CI_Con(1,:,ExMouse)'-Perf_Con(:,ExMouse),Perf_CI_Con(2,:,ExMouse)'-Perf_Con(:,ExMouse),'k','capSize',0,'linewidth',2) % 95% CI binomial 
hold on
errorbar(CS+0.03,Perf_V1_2mW(:,ExMouse),Perf_CI_V1_2mW(1,:,ExMouse)'-Perf_V1_2mW(:,ExMouse),Perf_CI_V1_2mW(2,:,ExMouse)'-Perf_V1_2mW(:,ExMouse),'color',[0 130 200]/255,'capSize',0,'linewidth',2)
errorbar(CS+0.04,Perf_V1_4mW(:,ExMouse),Perf_CI_V1_4mW(1,:,ExMouse)'-Perf_V1_4mW(:,ExMouse),Perf_CI_V1_4mW(2,:,ExMouse)'-Perf_V1_4mW(:,ExMouse),'color',[0 100 170]/255,'capSize',0,'linewidth',2)
scatter(CS,Perf_Con(:,ExMouse),[100 100 100 100],'k','filled')
scatter(CS+0.03,Perf_V1_2mW(:,ExMouse),[100 100 100 100],[0 130 200]/255,'filled')
scatter(CS+0.04,Perf_V1_4mW(:,ExMouse),[100 100 100 100],[0 100 170]/255,'filled')
title('Example Mouse (V1)')
ylabel('Performance')
xlabel('Change Size (Hz)')
ylim([0 1])
xlim([0.9 2.1])
box off
set(findall(gcf,'-property','FontSize'),'FontSize',18)
set(gcf,'Position',[300 300 800 700])
box off
[~,pV1_2mW]=ttest(Perf_V1_2mW',Perf_Con');
[~,pV1_4mW]=ttest(Perf_V1_4mW',Perf_Con');
[~,pS1_2mW]=ttest(Perf_S1_2mW',Perf_Con');
[~,pS1_4mW]=ttest(Perf_S1_4mW',Perf_Con');




function make_blanking_fig
% function make_blanking_fig
%
% Purpose
% Make the figure showing how Zapit performs blanking. In other words, this is how Zapit
% coordinates motion of the scanners with blanking the beam. The beam is off when the
% scanners are moving. A figure file called "blanking_figure" is saved to disk.
% Raw data and description of these are in the "raw_data" folder.
%
% Inputs
% none
%
% Outputs
% none
%
% Rob Campbell - SWC 2026



%% Preamble
% Data file name
rawDataDir = 'raw_data';
fname = 'control_feedback_photodiode.bin';

% Load the data from disk
data = readAndPlot(fullfile(rawDataDir,fname));


% Extract the relevant traces from the interleaved trace
feedback= data.waveforms(2:3:end);      % the feedback signal from the galvo
photodiode = data.waveforms(3:3:end);   % the photodiode signal




%% Data processing
% The blanking is very fast so we can differentiate the photodiode trace to determine the
% blanking times with a resolution 1E-5 seconds (which is the sample rate).

diffPeakThreshold = 1E4;
transitionInd = find(diff(photodiode)<-diffPeakThreshold);


% The feedback signal is a little noisier than the photodiode signal so we filter with a
% short boxcar. We do not filter the photodiode signal because it makes the light/dark
% transition significantly longer and this looks wrong.

filtLen = 3;
feedback = conv(feedback,ones(1,filtLen)/filtLen);


% Scale both traces so that they go between -5 and +5. This is to reflect the fact that
% the beam is moving over a 10 mm range, so the y axis will be in meaningful units for the
% the feedback signal.
feedback = feedback-min(feedback);
feedback = (feedback/max(feedback)*10)-5;

%photodiode = photodiode-min(photodiode);
%photodiode = (photodiode/max(photodiode)*10)-5;





%% -------------------------------------------------------------
%% Plot

clf

% Blanking screenshots
axSizeBS=0.47;
fSize=20;

bScreenShotA = imread('blanking_screenshot_A.png');
bScreenShotB = imread('blanking_screenshot_B.png');

axes('position',[0.025,0.53,axSizeBS,axSizeBS])
imshow(bScreenShotA)
text(20,30, 'A', 'FontSize',fSize+5,'FontWeight','bold','Color','w')

axes('position',[0.52,0.53,axSizeBS,axSizeBS])
imshow(bScreenShotB)
text(20,30, 'B', 'FontSize',fSize+5,'FontWeight','bold','Color','w')


% Data traces
axSizeTR=0.425;
% Bottom left plot
axes('position',[0.08,0.07,axSizeTR-0.02,axSizeTR])
hold on
preTicks = 78;
postTicks = 122;

timePoints = (-preTicks:postTicks)/1E2;
pdColor = [0.5,0.5,1];
fbColor = 'k';
photoDiodeLineStyle = {'-','color',pdColor,'lineWidth',1};
feedbackLineStyle = {'-','color',fbColor,'lineWidth',1};

yyaxis left
for ii=1:2:length(transitionInd)
    t=transitionInd(ii);
    plot(timePoints,feedback(t-preTicks:t+postTicks),feedbackLineStyle{:})
end
ylabel('beam position (mm)')
set(gca,'YColor',fbColor,'FontSize',fSize,'LineWidth',2)
set(gca,'YTick',-5:1:5)
ylim([-5.01,5.01])

% Label indicating sample size
text(-0.7,-4.75, sprintf('n=%d trials\n', length(1:2:length(transitionInd))), ...
    'FontSize',fSize-2)

% Label for the axes
text(-1.05,5, 'C', 'FontSize',fSize+5,'FontWeight','bold')

yyaxis right
for ii=1:2:length(transitionInd)
    t=transitionInd(ii);
    plot(timePoints,photodiode(t-preTicks:t+postTicks),photoDiodeLineStyle{:})
end
set(gca,'YColor',pdColor,'YTickLabel',[])

hold off
formatPlot




% Bottom right plot
axes('position',[0.56,0.07,axSizeTR-0.02,axSizeTR])
hold on
for ii=2:2:length(transitionInd)
    t=transitionInd(ii);
    plot(timePoints,feedback(t-preTicks:t+postTicks),feedbackLineStyle{:})
end
set(gca,'YColor',fbColor)
set(gca,'YTick',-5:1:5)
ylim([-5.01,5.01])

% Label indicating sample size
text(0.7,-4.75, sprintf('n=%d trials\n', length(2:2:length(transitionInd))),...
    'FontSize',fSize-2)

% Label for the axes
text(-0.97,5, 'D', 'FontSize',fSize+5,'FontWeight','bold')

set(gca,'YTickLabel',[],'LineWidth',2)

yyaxis right
for ii=2:2:length(transitionInd)
    t=transitionInd(ii);
    plot(timePoints,photodiode(t-preTicks:t+postTicks),photoDiodeLineStyle{:})
end
set(gca,'YColor',pdColor,'YTickLabel',[],'FontSize',fSize)
ylabel('Photodiode signal (arbitrary units)')
hold off
formatPlot



% Print to file
set(gcf,'PaperPosition',[0,0,15,12],'units','inches','Renderer','Painters')
print([mfilename,'.png'],'-dpng')
print([mfilename,'.eps'],'-depsc')

function formatPlot
    axis tight
    box on
    grid on
    xlabel('Time (ms)')
    xlim([-0.78,1.2])
    set(gca,'Xtick',-0.5:0.25:1)

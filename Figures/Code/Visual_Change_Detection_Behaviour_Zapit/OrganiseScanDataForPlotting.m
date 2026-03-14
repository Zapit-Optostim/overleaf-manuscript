% Organise Scan Data
% for Zapit eLife paper 2026
% Michael Lohse 2026

% loadRawData (in .../MiLo_20211201_DMDM_CausalCortex_fromwinstor/Behavioural_Inactivation_Sessions/Main/Cortex_Wide_Scanning_Grid/)

clear Trials TFStimuli
for M=1:5 % Mouse Counter

  % Session Info
   Trials{M}(1,:)=zeros(1,length(Full_Beh(M).Raw.Mouse))+M; % MouseId
   Trials{M}(2,:)=Full_Beh(M).Raw.Session; % SessionId
   
   %Outcomes
   Trials{M}(3,:)=Full_Beh(M).Raw.Corr; % Hits
   Trials{M}(4,:)=Full_Beh(M).Raw.Miss; % Miss
   Trials{M}(5,:)=Full_Beh(M).Raw.EarlyLick; % Lick before change
   Trials{M}(6,:)=Full_Beh(M).Raw.Abort; % Running Aborts
   Trials{M}(7,:)=Full_Beh(M).Raw.Ref; % Lick that happened within 150 ms after change onset, which is very unliknely to be change driven in our setup
   Trials{M}(8,:)=Full_Beh(M).Raw.RT; % % Reaction time (for hits this is from change point, for early licks or running aborts this is from trial onset)

   %Trial Conditions
   Trials{M}(9,:)=Full_Beh(M).Raw.Stim2TF; % Change Size (If mouse made it to change period (i.e., hit or miss trials))
   Trials{M}(10,:)=Full_Beh(M).Raw.LaserON; % % opto trials
   Trials{M}(11,:)=Full_Beh(M).Raw.powerOption; % laser power (1 is 2mW, 2 is 4 mW)
   Trials{M}(12,:)=Full_Beh(M).Raw.area; % which area was silenced (by number)

   % Trial specific stimulus fluctuations (the noise in the TF (updating every 50s) is randomly selected from a distribution of 0.25 std in log space on every trial)
   TFStimuli{M}=Full_Beh(M).Raw.TF;
    
end

AllTrialsConcat=[Trials{:}];
% on some trials the laser is pointed away formt he skull, make these control trials
AllTrialsConcat(10,AllTrialsConcat(12,:)==8)=0;

% For eLife paper I will only include V1 and S1 silecning (and control
% trials (no area silenced)) - the full silencing array is used for a
% different paper

ConS1andV1TrialsConcat=AllTrialsConcat(:,((AllTrialsConcat(12,:)==5 |AllTrialsConcat(12,:)==7) & AllTrialsConcat(10,:)==1) | AllTrialsConcat(10,:)==0 );

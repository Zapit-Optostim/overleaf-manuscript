function runThroughAllStimPoints
    % Present stimulus at each location for one second

    hZP = zapit.utils.getObject; % Get API object from base workspace

    if hZP.isReadyToStim == false
        return
    end

    for ii = 1:length(hZP.stimConfig.stimLocations)
        % Does not wait for a hardware trigger: starts right away
        hZP.sendSamples('conditionNum',ii,'hardwareTriggered',false) 
        pause(1) % Software timing only
        hZP.stopOptoStim
        pause(0.3) % To allow the ramp-down to happen
    end
end % runThroughAllStimPoints
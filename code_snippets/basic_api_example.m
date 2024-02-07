function runThroughAllStimPoints
    % Present stimulus at each location for one second

    % Get the API object from the base workspace
    hZP = zapit.utils.getObject;

    if hZP.isReadyToStim == false
        return
    end

    for ii = 1:length(hZP.stimConfig.stimLocations)
        % Does not wait for a hardware trigger: starts right away
        hZP.sendSamples('conditionNum',ii,'hardwareTriggered',false) 
        pause(1)
        hZP.stopOptoStim
        pause(0.3) % To allow the ramp-down to happen
    end

end % runThroughAllStimPoints
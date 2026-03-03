function varargout = readAndPlot(fname,sampleRate,nChans)

    % function varargout = readAndPlot(fname,sampleRate,nChans)
    %
    % Read and plot raw data from photoiode/blanking calibration
    %
    % Inputs
    % fname - file name to load
    % sampleRate - optional. 10,000 by default.
    % nChans - optional 3 by default.
    %
    % Outputs
    % optional. If no output argument is specified the function will plot the data to
    % screen. If an output is requested the plotting is skipped and the data read from
    % disk are returned as a structure.
    %
    %
    % Rob Campbell


    if nargin<3
        nChans=3;
    end

    if nargin<2
        sampleRate = 1E5;
    end
    fid = fopen(fname);

    data = fread(fid,'integer*2');
    timeAxis = linspace(0,(length(data)/nChans)/sampleRate,length(data)/nChans)*1E3; % ms

    if nargout>0
        out.waveforms = data;
        out.time = timeAxis;
        out.sampleRate = sampleRate;
        out.nChans = nChans;
        varargout{1} = out;
        return
    end



    % Plot
    figure
    cla
    hold on

    for ii=1:nChans
        plot(timeAxis,data(ii:nChans:end))
    end

    hold off

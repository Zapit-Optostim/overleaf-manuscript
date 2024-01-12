% Start the client, specifying the IP address of the Zapit server
client = zapit_tcp_bridge.TCPclient('ip','122.14.143.200');
client.connect;
 
% present the last stimulus condition for a short period
nCond = client.getNumConditions;
client.sendSamples('conditionNumber',nCond, 'hardwareTriggered', false);
pause(3)
client.stopOptoStim;
 
% Disconnect
delete(client)
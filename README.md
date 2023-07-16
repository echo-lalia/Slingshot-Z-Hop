# Slingshot-Z-Hop
A custom GCODE post processing script that adds a modified version of Z-Hop, which moves in a diagonal way instead of straight up and down.

# What the script does
At it's core, this is a python script that takes a GCODE file, and scans over it line-by-line. It looks for travel moves (any x/y move without extrusion), reads them, and replaces them with a modified version. The modified version moves the Z axis up at the same time as the X/Y axis, and then lowers the nozzle again when overhead of the target. The GCODE you give to it should not have ZHop enabled already. 

I'm a novice programmer, and I'd like my code to be easily readable by anyone who is starting out, so I have a comment on almost every line of the Python script, in case you'd like to look through it and see how it works, or modify it to your liking. 

# Running the Python script
The Python script can be run on it's own the same way you'd run any Python script. You'll need to already have Python installed and in your PATH. Open a terminal in the directory with slinghot_z_hop.py and config.ini, and run it. This is what the run command looks like on my PC running Windows 10: 
```
python slingshot_z_hop.py
```
By default, it will look for a file named "input.gcode" in the same folder. 

You can also specify a specific GCODE file, like this:
```
python slingshot_z_hop.py test.gcode
```
It will overwrite the file you pass to it, with the new ZHop behaviour. Each new line has a comment on it, in case you'd like to inspect the result.

# Running the executable on Windows
To run the executable on it's own, make sure both the slingshot_z_hop.exe and config.ini are in the same location. Place a file named 'input.gcode' into that folder, too, and simply double click the slingshot_z_hop.exe. It should edit your input.gcode file with the new ZHop feature. 

# Using with PrusaSlicer
These instrucitons are for Windows 10, and may need to be modified for other operating systems. 

Download the "slingshot_z_hop.exe" and the "config.ini", and place both into a directory on your computer where they can stay. Right click the slingshot_z_hop.exe, and hit 'Properties'. Copy the full Location of the file shown here. 

Go to PrusaSlicer, print settings, output options, and find the section for Post-processing scripts. (you may need to change to expert mode to see all the available print settings). Paste in the location of the slingshot_z_hop.exe, and make sure to type 'slingshot_z_hop.exe;" at the end of it. Like this: 
```
C:\Username\Documents\GCODEscripts\slingshot_z_hop.exe;
```
You may want to save to a new custom profile when you're done. 
Now, PrusaSlicer will try running the script when you export GCODE. If it works, youll see a terminal window briefly pop up, and get no error messages. 
Make sure you supervise the code when it runs on your printer! 

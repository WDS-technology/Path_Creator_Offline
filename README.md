# Path_CreatorV2

- What it does?

Creates a path/ route for the drone to fly. You build  a  route using special commands created by corvus.
The Script Provides Simple GUI to draw the route and select the commands you wish to use and put them in a JSON file.
Later this JSON file is sent to drone via SSH.

- How to use it ?

Go Inside The folder: `cd Path_CreatorV2`

Run The Script: `python path_script.py `
 
Result:



![Screenshot from 2023-09-19 08-58-44](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/feba5dd8-e056-401f-97ed-45b733dc0fe3)

### **Buttons**: They arw also used to write commands to json file.

Delay - set a delay command the drone will wait for specifdied seconds
Set XY speed - set a speed for drone (0.5/1.0/1.5)  [m/s]
Set new Yaw - will cause the drone to rotate - **default yaw is always 90 degrees!**
Take Picture
Start Recording

Export To json - used to export the path into json file and send it via SSH to the drone.
![Screenshot from 2023-09-19 09-11-17](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/3d35850d-bb8a-417b-8342-c601ca5cdfad)

----------


### **What  flying commands the drone uses?**



**SCHEDULE_MOVE_XYZ:** flying coordinate with speed and delay and yaw change

**SCHEDULE_FLY_TO_XY:**  just x, y coordinates to fly to

**SCHEDULE_FLY_TO_Z:** raise in the z axis  - gain altitude 

**SCHEDULE_FLY_TO_YAW:** - change how the drone rotated around itself - 90 is default

**SCHEDULE_SET_XY_SPEED** - change the speed the drone will fly

**SCHEDULE_SET_PAYLOAD_RECORDING:**   start recording using the tracking camera

**SCHEDULE_TAKE_PICTURE** 

**SCHEDULE_WAIT_FOR_PERIOD** - just a simple delay for drone- you put a number and the drones hovers inplace those number of seconds 

## Create A Path:


In order to give  the drone  flying commands just press with mouse on the grid map - a pop up of commands will be shown 

**Important!!** you select the the coordinates yourself  they are not based on where you select the point - just use the general axis convention 
for example: if you choose a point above the center make sure it has positive Y value according to cartesian XY axis - the grid map is here just to visualize the path  
so make sure that when you click a point to write coordinates that make sense.


![Image](https://i0.wp.com/statisticsbyjim.com/wp-content/uploads/2023/01/coordinate_plane.png?fit=499%2C499&ssl=1)
     
When you press any where on the grid you can select the command you want to use:

![Screenshot from 2023-09-19 09-17-01](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/a4249741-217d-4ee4-ad27-d408aedf25dd)





### So lets create s  short path:

* start always with giving a  height command - SCHEDULE_FLY_TO_Z
* Second send the drone to the  X=0, Y=0 with the SCHEDULE_FLY_TO_XY command 

**Note**: You always need to start with these two commands! i gave above

* Now just click on grid and enter new commands, you can change speed, yaw send the drone to new coordinate or just make it wait. some commands can  also be written to json file with the buttons on the right side of GUI.




You can also look at the height grid to get an idea of the altitude of drone / movement in the Z axis - look at the lower grid
![Screenshot from 2023-09-19 09-24-06](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/31a2b70a-7c8a-4546-a8e8-93651da8899b)



#### * When You finish


* export to json file - press the Export Button - give the path a name - **this name will be used later on the drone when selecting path**

![Screenshot from 2023-09-19 09-24-25](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/3c7bfc11-3953-407f-988a-3321025b48e3)


a window with address to ssh will open - enter the drone local IP address 

![Screenshot from 2023-09-19 09-24-38](https://github.com/jacob-CyberB/Path_CreatorV2/assets/134837950/b8b1cf8e-0916-442d-a4e7-000072737530)



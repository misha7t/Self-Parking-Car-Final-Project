Michael Tesis
5/9/26  

**Final Project Report**

**Introduction:**

The purpose of this project is to create a program that recognizes an object and controls a car to move to the object and park in front of it. To accomplish this, the project can be broken down into several parts responsible for different functions. Together they form the following pipeline: **Create Homography Matrix \-\> Object Recognition on Image \-\> Pixel to Real World Conversion \-\> Compute Time of Rotation and Movement \-\> Send Commands to Car**  
Each part of the pipeline is described below in its section.

**Technology Stack:**

* Laptop with camera and Python program  
* Micro:bit circuit board with JavaScript movement commands  
* Two FS90R servo motors with wheels attached  
* Breadboard connecting power source, micro:bit, and motors  
* Two AAA batteries  
* Car chassis and two additional wheels

**Part 1: Homography Matrix**

To create a homography matrix I used my laptop camera to take seven images shown below and measured the real world coordinates of the cone in each image with the camera position as the origin.

My Python program recognized the cone on each image, obtained the pixel coordinates of the cone, took the corresponding real world coordinates that I measured, and used the OpenCV function “findHomography” to create a resulting homography matrix. This matrix can then be used to find real world coordinates from the pixel coordinates of an object in an image taken with the same camera.

**Part 2: Object Recognition**

To find the position of the cone that the car must park in front of, I used my laptop camera to take an image of the cone. My Python program used color segmentation to recognize an orange colored object in the image, draw a bounding box around it, and find its pixel coordinates from the bounding box. Color segmentation used HSV parameters to determine the orange color under corresponding lighting conditions. The code for recognition is shown below:

**Part 3: Pixel to Real World Conversion**

I used the homography matrix obtained in Part 1 to calculate the real world coordinates of the cone in the image. The calculation is done by the function below. The H parameter in the function is the homography matrix, u and v are pixel coordinates obtained as described in Part 2\.

**Part 4: Compute Time of Rotation and Movement**

In order to know the time required to rotate the car by a certain angle and the time to move the car a certain distance, it was necessary to measure the angular velocity and linear velocity of my car. This measurement was done experimentally. I sent a command to the car motors through the micro:bit to rotate 180 degrees and measured the time it took. By dividing the 180 degree angle by the time, I found the angular velocity. Since the motors are not identical, I measured the angular velocity of the left and right rotations separately. To find the linear velocity, I measured how much time it took the car to travel one meter forward. Then I divided one meter by the measured time. The measured velocities are the parameters FORWARD\_SPEED,  TURN\_SPEED\_R, and TURN\_SPEED\_L in the code below. Knowing the world coordinates of the cone obtained in Part 3, I needed to calculate the angle and distance the car would have to move. The angle was calculated as arctan of the y-coordinate divided by the x-coordinate. The distance from the car to the cone was calculated by applying the Pythagorean theorem to the y and x coordinates. The Stopping distance from the cone was subtracted from the calculated distance to find the distance forward. Knowing the velocities, the angle to rotate left or right, and the distance forward, my program calculated the rotation time and movement time to send to the micro:bit. The function to compute the times is shown below:

**Part 5: Send Commands to Car**

My JavaScript program on the micro:bit defined the four basic commands that are sent to the motors. The right wheel motor was connected to pin 0 of the micro:bit and the left wheel motor was connected to pin 1 of the micro:bit. The four defined commands, “F” (move forward), “L” (rotate left), “R” (rotate right), and “S” (stop) are shown in the code below:

My Python function to send commands to micro:bit shown below took the command and time as parameters. It controlled how long the command was executed on the micro:bit by sending the Stop command after the time elapsed. The commands were sent from my Python program on the laptop to micro:bit via a USB cable.

**Demonstration:**

There are three videos showing the car parking at the Stopping distance in front of the cone attached with this report. The cone is located on the right, on the left, and in front relative to the car’s original position. The videos first show the recognition of the cone by the laptop camera and then the car moving according to that recognition.

**Sources of Error:**

The resulting parking position of the car in front of the cone is not always precise or consistent due to certain sources of error. One source is the angle of the laptop camera when taking an image of the cone. This angle can accidentally change when moving the laptop around since the screen is not firmly fixed in place. The homography matrix is extremely sensitive to the angle of the camera, so when an image is taken at a different angle, the calculated distance will be completely different. Another source of error is the varying speeds at which the wheels spin due to friction on different surfaces and the friction between the wheels and motors. If one wheel spins faster than the other, then instead of moving straight forward the car’s movement will be curved. Correspondingly, the calculated angle and distance will not match the actual ones, with the error increasing the longer the car moves. In addition, the movement of the car is sensitive to changes in the physical characteristics of the car itself, such as the total weight of the car with load, the distribution of the load between the wheels, the alignment of car parts, how firmly the parts are connected to each other, etc. The extensive testing during the project showed that recognition of the cone is consistently accurate and is not a source of error.

**Future Work:**

Due to the constraints of the micro:bit V1 that I used, I could not use wireless communication between the Python program and camera on the laptop and the micro:bit controlling the motors. From what I have researched, I know that micro:bit V2 is capable of wireless communication using bluetooth. Therefore, using micro:bit V2, and possibly a micro:bit driver (separate part), it will be possible to put my Python program on the phone and mount the phone on the car. Then the recognition of the cone can be done in real time using video streamed from the phone. Using this configuration I will no longer need to measure the angular and linear velocities of the car in advance. Instead, as the car moves, I would take a frame every small amount of time from the video, compute the angle and distance from the cone, and send the corresponding commands to micro:bit in real time. The commands would still be to move forward, rotate left, rotate right, or stop. Overall, this solves three current issues: eliminates wired connection between the laptop and car, video is taken dynamically from the car’s perspective instead of a static image taken from the laptop’s original fixed position, and calibration of angular and linear velocities are no longer needed.

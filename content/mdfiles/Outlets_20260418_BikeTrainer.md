### Bike Trainer Dashboard

A dynamic, single-page dashboard designed for **indoor cycling** using my **Minoura MAG-500** bike trainer. 

- Access the dashboard [**here**](tools/BikeTrainer.html)

Note: For **camera detection** to work, you have to open the `.html` file locally. 

This app utilizes a power model to estimate workout intensity based on environmental and mechanical factors:
- **Gravitational Power:** Calculates power required to overcome slope/grade.
- **Rolling Resistance:** Accounts for tire friction based on total mass.
- **Aerodynamic Drag:** Estimates wind resistance using rider height and shoulder width.

The settings include:
- **Trainer Config:** Eight magnetic resistance levels (L1–L8) mapped to specific slopes.
- **Drivetrain:** Selection for Front Ring (50T/34T) and Rear Cassette (11T–34T) gears.
- **Wheel Size:** Presets for various tire sizes (700x23C up to 700x32C) with manual circumference input.
- **Rider Profile:** Defaults are FTP 250W, Mass 85kg, Height 178cm, Shoulder Width 31cm.
- **Recording:** Can record a simulated workout and export a GPX file readable by other cycling apps such as Strava.

![Bike Trainer Dashboard](images/tool_BikeTrainer.png)
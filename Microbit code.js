//Microbit code:
serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
        let cmd = serial.readUntil(serial.delimiters(Delimiters.NewLine)).trim()
        if (cmd == "F") {
            pins.servoWritePin(AnalogPin.P0, 180)
            pins.servoWritePin(AnalogPin.P1, 0)
        } else if (cmd == "S") {
            pins.servoWritePin(AnalogPin.P0, 85)
            pins.servoWritePin(AnalogPin.P1, 90)
        } else if (cmd == "L") {
            pins.servoWritePin(AnalogPin.P0, 0)
            pins.servoWritePin(AnalogPin.P1, 0)
        } else if (cmd == "R") {
            pins.servoWritePin(AnalogPin.P0, 180)
            pins.servoWritePin(AnalogPin.P1, 180)
        }
    })
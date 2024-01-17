import navel

def main():
    with navel.Robot() as robot:
        robot.rotate_arms(180,180)
        robot.say("Hallo, welt!")
        robot.rotate_arms(0,0)

if __name__ == "__main__":
    main()


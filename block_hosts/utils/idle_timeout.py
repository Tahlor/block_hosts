import time
import threading

class IdleTimeoutHandler:
    def __init__(self, commands=None, run_once=False, timeout=60):
        self.commands = self.validate_commands(commands)
        self.run_once = run_once
        self.timeout = timeout
        self.last_interaction_time = time.time()
        self.running = False
        self.idle_thread = None
        self.active_commands = None

    def reset(self, commands):
        self.last_interaction_time = time.time()
        if self.idle_thread and self.idle_thread.is_alive():
            self.running = False
            self.idle_thread.join()
        self.active_commands = commands

        self.start_idle_timeout()

    def idle_timeout(self):
        while self.running:
            start_time = time.time()
            while self.running and time.time() - start_time < self.timeout:
                time.sleep(.4)
            if time.time() - self.last_interaction_time >= self.timeout:
                if self.active_commands:
                    for command in self.active_commands:
                        command()
                else:
                    print("Timeout")

                if self.run_once:
                    break

        #print("DONE WITH IDLE TIMEOUT")

    def start_idle_timeout(self):
        self.running = True
        self.idle_thread = threading.Thread(target=self.idle_timeout)
        self.idle_thread.start()

    def user_interaction(self):
        self.last_interaction_time = time.time()

    @staticmethod
    def validate_commands(commands):
        if commands and not isinstance(commands, (tuple,list)):
            commands=[commands]
        return commands

    def prompt(self, message, commands=None):
        commands = self.validate_commands(commands)
        if commands is None:
            commands = self.commands

        if not commands:
            user_input = input(message)
        else:
            self.reset(commands=commands)
            user_input = input(message)
            self.user_interaction()
            self.running = False

            if self.idle_thread and self.idle_thread.is_alive():
                self.idle_thread.join()

        return user_input


if __name__=="__main__":
    test_func = lambda : print("Default timeout func FTW")
    test_func2 = lambda : print("Timeout2 func FTW")
    test_func3 = lambda : print("Timeout3 func FTW")

    I = IdleTimeoutHandler(timeout = 15, commands=[test_func], run_once=False)
    I.prompt("1. This is a test prompt? ")
    I.prompt("2. This is a test prompt? ", commands=test_func2)
    I.prompt("3. This is a test prompt? ")
    I.prompt("4. This is a test prompt? ", commands=test_func3)
    input("DONE")

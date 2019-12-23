import socket

class Server(object):
    """
    An adventure game socket server

    An instance's methods share the following variables:

    * self.socket: a "bound" server socket, as produced by socket.bind()
    * self.client_connection: a "connection" socket as produced by socket.accept()
    * self.input_buffer: a string that has been read from the connected client and
      has yet to be acted upon.
    * self.output_buffer: a string that should be sent to the connected client; for
      testing purposes this string should NOT end in a newline character. When
      writing to the output_buffer, DON'T concatenate: just overwrite.
    * self.done: A boolean, False until the client is ready to disconnect
    * self.room: one of 0, 1, 2, 3. This signifies which "room" the client is in,
      according to the following map:

                                     3                      N
                                     |                      ^
                                 1 - 0 - 2                  |

    When a client connects, they are greeted with a welcome message. And then they can
    move through the connected rooms. For example, on connection:

    OK! Welcome to Realms of Venture! This room has brown wall paper!  (S)
    move north                                                         (C)
    OK! This room has white wallpaper.                                 (S)
    say Hello? Is anyone here?                                         (C)
    OK! You say, "Hello? Is anyone here?"                              (S)
    move south                                                         (C)
    OK! This room has brown wall paper!                                (S)
    move west                                                          (C)
    OK! This room has a green floor!                                   (S)
    quit                                                               (C)
    OK! Goodbye!                                                       (S)

    Note that we've annotated server and client messages with *(S)* and *(C)*, but
    these won't actually appear in server/client communication. Also, you'll be
    free to develop any room descriptions you like: the only requirement is that
    each room have a unique description.
    """

    game_name = "Realms of Venture"
    room_dict = {0: 'You are in the room with the white wallpaper',
                 1: 'You are in the room with the green wallpaper',
                 2: 'You are in the room with the brown wallpaper',
                 3: 'You are in the room with the mauve wallpaper'}
    BYTES = 16

    def __init__(self, port=50000):
        self.input_buffer = ""
        self.output_buffer = ""
        self.done = False
        self.socket = None
        self.client_connection = None
        self.port = port

        self.room = 0

    def connect(self):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP)

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        address = ('127.0.0.1', self.port)
        self.socket.bind(address)
        self.socket.listen(1)

        self.client_connection, address = self.socket.accept()

    def room_description(self, room_number):
        """
        For any room_number in 0, 1, 2, 3, return a string that "describes" that
        room.

        Ex: `self.room_number(1)` yields "Brown wallpaper covers the walls, bathing
        the room in warm light reflected from the half-drawn curtains."

        :param room_number: int
        :return: str
        """

        return self.room_dict[room_number]

    def greet(self):
        """
        Welcome a client to the game.

        Puts a welcome message and the description of the client's current room into
        the output buffer.

        :return: None
        """
        self.output_buffer = "Welcome to {}! {}".format(
            self.game_name,
            self.room_description(self.room)
        )

    def get_input(self):
        """
        Retrieve input from the client_connection. All messages from the client
        should end in a newline character: '\n'.

        This is a BLOCKING call. It should not return until there is some input from
        the client to receive.

        :return: None
        """

        received = ''
        while '\n' not in received:
            received += self.client_connection.recv(self.BYTES).decode('utf8')

        self.input_buffer = received.strip()

    def move(self, argument):
        """
        Moves the client from one room to another.

        Examines the argument, which should be one of:

        * "north"
        * "south"
        * "east"
        * "west"

        "Moves" the client into a new room by adjusting self.room to reflect the
        number of the room that the client has moved into.

        Puts the room description (see `self.room_description`) for the new room
        into "self.output_buffer".

        :param argument: str
        :return: None
        """

        # Only accept valid movements (north/east/west from room 0, east from
        # room 1, west from room 2, south from room 3)

        # Create dictionary of valid moves -> key = (current_room, direction)
        # value = new_room
        valid_moves = {(0,'north'):3, (0,'west'):1, (0,'east'):2,
                       (1,'east'):0, (2,'west'):0, (3,'south'):0}
       # Only accept valid moves
        if (self.room, argument) in valid_moves:
            self.room = valid_moves[(self.room, argument)]
            self.output_buffer = self.room_description(self.room)
        else:
            self.output_buffer = 'Not a valid move! Please try again.'

    def say(self, argument):
        """
        Lets the client speak by putting their utterance into the output buffer.

        For example:
        `self.say("Is there anybody here?")`
        would put
        `You say, "Is there anybody here?"`
        into the output buffer.

        :param argument: str
        :return: None
        """

        self.output_buffer = 'You say, \'{}\''.format(argument)

    def quit(self, argument):
        """
        Quits the client from the server.

        Turns `self.done` to True and puts "Goodbye!" onto the output buffer.

        Ignore the argument.

        :param argument: str
        :return: None
        """

        self.done = True
        self.output_buffer = 'Goodbye!'

    def route(self):
        """
        Examines `self.input_buffer` to perform the correct action (move, quit, or
        say) on behalf of the client.

        For example, if the input buffer contains "say Is anybody here?" then `route`
        should invoke `self.say("Is anybody here?")`. If the input buffer contains
        "move north", then `route` should invoke `self.move("north")`.

        :return: None
        """

        # Input buffer should start with either "move", "say", or "quit"
        received = self.input_buffer.split(' ')
        # Remove first word to help with routing
        command = received.pop(0)
        # Join rest of input back to a single string
        arguments = ' '.join(received)

        routing_dict = {'quit': self.quit,
                        'move': self.move,
                        'say': self.say}

        if command in routing_dict:
            routing_dict[command](arguments)
        else:
            self.output_buffer = 'Not a valid command.'

    def push_output(self):
        """
        Sends the contents of the output buffer to the client.

        This method should prepend "OK! " to the output and append "\n" before
        sending it.

        :return: None
        """

        output_string = 'OK! {}\n'.format(self.output_buffer).encode('utf8')
        self.client_connection.sendall(output_string)

    def serve(self):
        self.connect()
        self.greet()
        self.push_output()

        while not self.done:
            self.get_input()
            self.route()
            self.push_output()

        self.client_connection.close()
        self.socket.close()

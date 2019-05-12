package cruz.agents;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ConnectException;
import java.net.InetAddress;
import java.net.Socket;

class SocketClient {
    private static Socket socket;
    private int port;
    private DataOutputStream out;
    private DataInputStream in;

    SocketClient(int port) {
        this.port = port;
        this.createSocket();
    }

    private void createSocket() {
        try {
            InetAddress address = InetAddress.getByName("localhost");
            this.socket = new Socket(address, this.port);
            this.out = new DataOutputStream(this.socket.getOutputStream());
            this.in = new DataInputStream(this.socket.getInputStream());
        } catch (IOException e) {
            System.err.println("ATTENTION! Could not create the Java socket.");
            e.printStackTrace();
        }
    }

    /**
     * Writes the lenght of the message to send.
     * Sends a message to the server.
     * Receives the length to read.
     * Reads the message.
     */
    byte[] sendMessageAndReceiveResponse(byte[] messageToSend) {
        byte[] buffer = null;

        try {
            //Send the message to the server
            this.out.writeInt(messageToSend.length);
            this.out.flush();

            this.out.write(messageToSend);
            this.out.flush();

            int length = this.in.readInt();
            if (length >= 0) {
                buffer = new byte[length];
                this.in.readFully(buffer, 0, buffer.length);
            }
        } catch (ConnectException e) {
            System.err.println("ATTENTION! Could not connect to socket. No information was retrieved from the Python module.");
            e.printStackTrace();
            return null;
        } catch (Exception e) {
            System.err.println("ATTENTION! Something went wrong while communicating with the Python module.");
            e.printStackTrace();
            return null;
        }

        return buffer;
    }

    void close() {
        try {
            if (this.in != null) {
                this.in.close();
            }

            if (this.out != null) {
                this.out.close();
            }

            if (this.socket != null) {
                this.socket.close();
            }
        } catch(Exception e) {
            System.err.println("ATTENTION! Java socket not properly closed.");
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        SocketClient socketClient = new SocketClient(5000);
        byte[] response;

        response = socketClient.sendMessageAndReceiveResponse("a2345678".getBytes());
        System.out.println(new String(response));

        response = socketClient.sendMessageAndReceiveResponse("a234567812345".getBytes());
        System.out.println(new String(response));

        response = socketClient.sendMessageAndReceiveResponse("a12345678123456781".getBytes());
        System.out.println(new String(response));

        socketClient.close();
    }
}


package cruz.agents;

import ddejonge.bandana.tools.Logger;

import java.io.*;
import java.net.ConnectException;
import java.net.InetAddress;
import java.net.Socket;
import java.util.Arrays;

class SocketClient
{
    private static Socket socket;
    private String host;
    private int port;
    private Logger logger;

    SocketClient(String host, int port, Logger logger)
    {
        this.host = host;
        this.port = port;
        this.logger = logger;
    }

    byte[] sendMessageAndReceiveResponse(byte[] messageToSend){
        try {
            InetAddress address = InetAddress.getByName(host);
            socket = new Socket(address, port);

            //Send the message to the server
            OutputStream os = socket.getOutputStream();
            os.write(messageToSend);
            os.flush();

            //Get the return message from the server
            InputStream is = socket.getInputStream();
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024 * 20];

            while(true)
            {
                int n = is.read(buffer);
                if(n < 0) {
                    break;
                }
                baos.write(buffer, 0, n);
            }

            closeSocket();
            return baos.toByteArray();
        }
        catch (ConnectException exception) {
            System.out.println("ATTENTION! Could not connect to socket. No deal was retrieved from the Python module.");
            return null;
        }
        catch (Exception exception)
        {
            exception.printStackTrace();
            return null;
        }
    }

    private void closeSocket(){
        //Closing the socket
        try
        {
            socket.close();
        }
        catch(Exception e)
        {
            e.printStackTrace();
        }
    }
}
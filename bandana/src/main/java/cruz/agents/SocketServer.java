package cruz.agents;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.ServerSocket;
import java.net.Socket;

public class SocketServer {
    private ServerSocket serverSocket;
    private Socket clientSocket;

    SocketServer(int port) {
        try {
            this.serverSocket = new ServerSocket(port);
            this.clientSocket = serverSocket.accept();

            //Get the return message from the server
            InputStream is = this.clientSocket.getInputStream();
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
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    public static void main(String[] args) throws IOException {


    }
}

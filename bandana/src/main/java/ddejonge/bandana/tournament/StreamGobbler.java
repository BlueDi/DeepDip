package ddejonge.bandana.tournament;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintWriter;


class StreamGobbler extends Thread {
    InputStream inputStream;
    String type;
    OutputStream outputStream;
    boolean print;

    StreamGobbler(InputStream is, String type, boolean print) {
        this.inputStream = is;
        this.type = type;
        this.outputStream = null;
        this.print = print;
    }

    StreamGobbler(InputStream is, String type, OutputStream redirect) {
        this.inputStream = is;
        this.type = type;
        this.outputStream = redirect;
        this.print = false;
    }

    public void run() {
        PrintWriter pw = null;
        BufferedReader br = null;
        String line = null;

        try {
            if (this.outputStream != null) {
                pw = new PrintWriter(this.outputStream);
            }

            br = new BufferedReader(new InputStreamReader(this.inputStream));

            while ((line = br.readLine()) != null) {
                if (pw != null) {
                    pw.println(this.type + ": " + line);
                }

                if (this.print) {
                    System.out.println(this.type + ": " + line);
                }
            }
        } catch (IOException e) {
            System.err.println("Failed to read from " + this.type);
            e.printStackTrace();
        } finally {
            try {
                if (br != null) {
                    br.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }

            if (pw != null) {
                pw.flush();
                pw.close();
            }
        }
    }
}


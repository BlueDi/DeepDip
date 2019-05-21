package ddejonge.bandana.tournament;


public class ProcessRunner {
    public ProcessRunner() {}

    public static Process exec(String[] cmdArray, String name) {
        Process process = null;

        try {
            process = Runtime.getRuntime().exec(cmdArray);
        } catch (Throwable e) {
            e.printStackTrace();
        }

        return process;
    }
}

